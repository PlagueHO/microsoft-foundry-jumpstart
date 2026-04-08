using MaiImage2Simple.Models;
using Microsoft.Extensions.Options;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace MaiImage2Simple.Services;

/// <summary>
/// Calls MAI image generation over the MAI REST API.
/// </summary>
public sealed class MaiImageService : IMaiImageService
{
    private const int MinimumDimension = 768;
    private const int MaximumArea = 1_048_576;

    private readonly HttpClient _httpClient;
    private readonly MicrosoftFoundryOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="MaiImageService"/> class.
    /// </summary>
    /// <param name="httpClient">HTTP client used for MAI requests.</param>
    /// <param name="options">Foundry configuration values.</param>
    public MaiImageService(HttpClient httpClient, IOptions<MicrosoftFoundryOptions> options)
    {
        ArgumentNullException.ThrowIfNull(httpClient);
        ArgumentNullException.ThrowIfNull(options);

        _httpClient = httpClient;
        _options = options.Value;
    }

    /// <inheritdoc/>
    public async Task<MaiImageResult> GenerateImageAsync(
        MaiImageRequest request,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(request);

        if (string.IsNullOrWhiteSpace(request.Prompt))
        {
            return MaiImageResult.Failure("Enter a prompt before generating an image.");
        }

        if (request.Width < MinimumDimension || request.Height < MinimumDimension)
        {
            return MaiImageResult.Failure(
                $"Width and height must be at least {MinimumDimension} pixels.");
        }

        if (request.Width * request.Height > MaximumArea)
        {
            return MaiImageResult.Failure(
                "Width x height must be less than or equal to 1048576.");
        }

        if (!Uri.TryCreate(_options.ResourceEndpoint, UriKind.Absolute, out var resourceUri))
        {
            return MaiImageResult.Failure("The configured Foundry resource endpoint is invalid.");
        }

        var endpointUri = NormalizeMaiEndpoint(resourceUri);

        if (string.IsNullOrWhiteSpace(_options.ApiKey))
        {
            return MaiImageResult.Failure("Set MicrosoftFoundry:ApiKey before generating images.");
        }

        var payload = new MaiImageGenerationRequestDto
        {
            Model = _options.ImageDeployment,
            Prompt = request.Prompt,
            Width = request.Width,
            Height = request.Height,
        };

        var payloadJson = JsonSerializer.Serialize(payload);
        var payloadBytes = Encoding.UTF8.GetBytes(payloadJson);
        using var content = new ByteArrayContent(payloadBytes);
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");

        using var requestMessage = new HttpRequestMessage(HttpMethod.Post, endpointUri);
        requestMessage.Headers.Add("api-key", _options.ApiKey);
        requestMessage.Content = content;

        try
        {
            using var response = await _httpClient.SendAsync(requestMessage, cancellationToken)
                .ConfigureAwait(false);

            var responseText = await response.Content.ReadAsStringAsync(cancellationToken)
                .ConfigureAwait(false);

            if (!response.IsSuccessStatusCode)
            {
                var apiMessage = TryReadApiErrorMessage(responseText);
                var statusCode = (int)response.StatusCode;

                if (statusCode == 404 ||
                    (apiMessage?.Contains("unknown_model", StringComparison.OrdinalIgnoreCase) ?? false))
                {
                    return MaiImageResult.Failure(
                        "Unknown model or deployment. Use the exact deployment name from Foundry Deployments.",
                        statusCode);
                }

                return MaiImageResult.Failure(
                    apiMessage ?? "Image generation request failed.",
                    statusCode);
            }

            MaiImageGenerationResponseDto? responseDto;
            try
            {
                responseDto = JsonSerializer.Deserialize<MaiImageGenerationResponseDto>(responseText);
            }
            catch (JsonException)
            {
                return MaiImageResult.Failure("The service returned an unexpected response format.");
            }

            var base64 = responseDto?.Data.FirstOrDefault()?.Base64Json;
            if (string.IsNullOrWhiteSpace(base64))
            {
                return MaiImageResult.Failure("The service did not return an image payload.");
            }

            return MaiImageResult.Success(base64);
        }
        catch (Exception ex)
        {
            return MaiImageResult.Failure($"Image generation failed: {ex.Message}");
        }
    }

    private static Uri NormalizeMaiEndpoint(Uri resourceUri)
    {
        var uriBuilder = new UriBuilder(resourceUri);

        if (uriBuilder.Host.EndsWith(".openai.azure.com", StringComparison.OrdinalIgnoreCase))
        {
            uriBuilder.Host = uriBuilder.Host.Replace(
                ".openai.azure.com",
                ".services.ai.azure.com",
                StringComparison.OrdinalIgnoreCase);
        }

        return new Uri(uriBuilder.Uri, "/mai/v1/images/generations");
    }

    private static string? TryReadApiErrorMessage(string responseText)
    {
        if (string.IsNullOrWhiteSpace(responseText))
        {
            return null;
        }

        try
        {
            var error = JsonSerializer.Deserialize<MaiErrorEnvelopeDto>(responseText);
            if (string.IsNullOrWhiteSpace(error?.Error?.Message))
            {
                return null;
            }

            if (string.IsNullOrWhiteSpace(error.Error.Code))
            {
                return error.Error.Message;
            }

            return $"{error.Error.Message} ({error.Error.Code})";
        }
        catch (JsonException)
        {
            return null;
        }
    }
}