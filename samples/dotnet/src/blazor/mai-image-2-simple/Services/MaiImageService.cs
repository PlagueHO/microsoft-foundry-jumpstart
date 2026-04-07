using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Azure.Core;
using Azure.Identity;
using MaiImage2Simple.Models;
using Microsoft.Extensions.Options;

namespace MaiImage2Simple.Services;

/// <summary>
/// Calls MAI image generation over REST with Entra authentication.
/// </summary>
public sealed class MaiImageService : IMaiImageService
{
    private static readonly string[] CognitiveServicesScope =
        ["https://cognitiveservices.azure.com/.default"];

    private const int MinimumDimension = 768;
    private const int MaximumArea = 1_048_576;

    private readonly HttpClient _httpClient;
    private readonly MicrosoftFoundryOptions _options;
    private readonly TokenCredential _credential;

    /// <summary>
    /// Initializes a new instance of the <see cref="MaiImageService"/> class.
    /// </summary>
    /// <param name="httpClient">HTTP client used for MAI requests.</param>
    /// <param name="options">Foundry configuration values.</param>
    /// <param name="credential">Credential used to get Entra access tokens.</param>
    public MaiImageService(
        HttpClient httpClient,
        IOptions<MicrosoftFoundryOptions> options,
        TokenCredential? credential = null)
    {
        ArgumentNullException.ThrowIfNull(httpClient);
        ArgumentNullException.ThrowIfNull(options);

        _httpClient = httpClient;
        _options = options.Value;
        _credential = credential ?? new DefaultAzureCredential();
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

        AccessToken accessToken;
        try
        {
            accessToken = await _credential.GetTokenAsync(
                new TokenRequestContext(CognitiveServicesScope),
                cancellationToken).ConfigureAwait(false);
        }
        catch (AuthenticationFailedException)
        {
            return MaiImageResult.Failure(
                "Unable to authenticate. Sign in with Azure CLI or use a managed identity.");
        }

        var payload = new MaiImageGenerationRequestDto
        {
            Model = _options.ImageDeployment,
            Prompt = request.Prompt,
            Width = request.Width,
            Height = request.Height,
        };

        using var requestMessage = new HttpRequestMessage(
            HttpMethod.Post,
            new Uri(resourceUri, "/mai/v1/images/generations"));

        requestMessage.Headers.Authorization =
            new AuthenticationHeaderValue("Bearer", accessToken.Token);
        requestMessage.Content = JsonContent.Create(payload);

        HttpResponseMessage response;
        try
        {
            response = await _httpClient.SendAsync(requestMessage, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (HttpRequestException)
        {
            return MaiImageResult.Failure(
                "Unable to reach the Foundry endpoint. Verify network and endpoint settings.");
        }

        using (response)
        {
            var responseText = await response.Content.ReadAsStringAsync(cancellationToken)
                .ConfigureAwait(false);

            if (!response.IsSuccessStatusCode)
            {
                var statusCode = (int)response.StatusCode;
                var apiMessage = TryReadApiErrorMessage(responseText);
                var friendlyMessage = apiMessage ?? "The MAI request failed. Try again in a moment.";

                return MaiImageResult.Failure(friendlyMessage, statusCode);
            }

            MaiImageGenerationResponseDto? responseDto;
            try
            {
                responseDto = JsonSerializer.Deserialize<MaiImageGenerationResponseDto>(responseText);
            }
            catch (JsonException)
            {
                return MaiImageResult.Failure(
                    "The service returned an unexpected response format.");
            }

            var base64 = responseDto?.Data.FirstOrDefault()?.Base64Json;
            if (string.IsNullOrWhiteSpace(base64))
            {
                return MaiImageResult.Failure("The service did not return an image payload.");
            }

            return MaiImageResult.Success(base64);
        }
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