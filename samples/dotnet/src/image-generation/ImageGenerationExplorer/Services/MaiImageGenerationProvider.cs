using System.Diagnostics;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Azure.Core;
using ImageGenerationExplorer.Models;
using Microsoft.Extensions.Options;

namespace ImageGenerationExplorer.Services;

/// <summary>
/// Generates images via the MAI REST API at /mai/v1/images/generations.
/// </summary>
public sealed class MaiImageGenerationProvider : IImageGenerationProvider
{
    private readonly HttpClient _httpClient;
    private readonly ImageGenerationExplorerOptions _options;
    private readonly TokenCredential _credential;

    /// <summary>
    /// Initializes a new instance of the <see cref="MaiImageGenerationProvider"/> class.
    /// </summary>
    public MaiImageGenerationProvider(
        HttpClient httpClient,
        IOptions<ImageGenerationExplorerOptions> options,
        TokenCredential credential)
    {
        ArgumentNullException.ThrowIfNull(httpClient);
        ArgumentNullException.ThrowIfNull(options);
        ArgumentNullException.ThrowIfNull(credential);

        _httpClient = httpClient;
        _options = options.Value;
        _credential = credential;
    }

    /// <inheritdoc/>
    public ImageApiType ApiType => ImageApiType.Mai;

    /// <inheritdoc/>
    public async Task<ImageGenerationResult> GenerateAsync(
        string prompt,
        int width,
        int height,
        ImageModelConfig model,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(model);
        var sw = Stopwatch.StartNew();

        if (string.IsNullOrWhiteSpace(prompt))
        {
            return ImageGenerationResult.Failure(
                model.DeploymentName, model.DisplayName,
                "Enter a prompt before generating an image.", sw.ElapsedMilliseconds);
        }

        if (!Uri.TryCreate(model.Endpoint, UriKind.Absolute, out var resourceUri))
        {
            return ImageGenerationResult.Failure(
                model.DeploymentName, model.DisplayName,
                "The configured Foundry resource endpoint is invalid.", sw.ElapsedMilliseconds);
        }

        var endpointUri = NormalizeMaiEndpoint(resourceUri);

        var payloadBytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(
            new MaiImageGenerationRequestDto
            {
                Model = model.DeploymentName,
                Prompt = prompt,
                Width = width,
                Height = height,
            }));
        using var content = new ByteArrayContent(payloadBytes);
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");

        using var requestMessage = new HttpRequestMessage(HttpMethod.Post, endpointUri);
        requestMessage.Content = content;

        if (!string.IsNullOrWhiteSpace(_options.ApiKey))
        {
            requestMessage.Headers.Add("api-key", _options.ApiKey);
        }
        else
        {
            var tokenContext = new TokenRequestContext(["https://cognitiveservices.azure.com/.default"]);
            var token = await _credential.GetTokenAsync(tokenContext, cancellationToken).ConfigureAwait(false);
            requestMessage.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token.Token);
        }

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
                    return ImageGenerationResult.Failure(
                        model.DeploymentName, model.DisplayName,
                        "Unknown model or deployment. Use the exact deployment name from Foundry Deployments.",
                        sw.ElapsedMilliseconds, statusCode);
                }

                return ImageGenerationResult.Failure(
                    model.DeploymentName, model.DisplayName,
                    apiMessage ?? "Image generation request failed.",
                    sw.ElapsedMilliseconds, statusCode);
            }

            MaiImageGenerationResponseDto? responseDto;
            try
            {
                responseDto = JsonSerializer.Deserialize<MaiImageGenerationResponseDto>(responseText);
            }
            catch (JsonException)
            {
                return ImageGenerationResult.Failure(
                    model.DeploymentName, model.DisplayName,
                    "The service returned an unexpected response format.",
                    sw.ElapsedMilliseconds);
            }

            var base64 = responseDto?.Data.FirstOrDefault()?.Base64Json;
            if (string.IsNullOrWhiteSpace(base64))
            {
                return ImageGenerationResult.Failure(
                    model.DeploymentName, model.DisplayName,
                    "The service did not return an image payload.",
                    sw.ElapsedMilliseconds);
            }

            return ImageGenerationResult.Success(
                model.DeploymentName, model.DisplayName, base64, width, height, sw.ElapsedMilliseconds);
        }
        catch (Exception ex)
        {
            return ImageGenerationResult.Failure(
                model.DeploymentName, model.DisplayName,
                $"Image generation failed: {ex.Message}",
                sw.ElapsedMilliseconds);
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
