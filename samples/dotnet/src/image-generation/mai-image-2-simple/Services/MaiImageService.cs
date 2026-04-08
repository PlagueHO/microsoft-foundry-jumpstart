using MaiImage2Simple.Models;
using Microsoft.Extensions.Options;
using OpenAI;
using OpenAI.Images;
using System.ClientModel;

namespace MaiImage2Simple.Services;

#pragma warning disable OPENAI001

/// <summary>
/// Calls MAI image generation over the OpenAI Images client.
/// </summary>
public sealed class MaiImageService : IMaiImageService
{
    private const int MinimumDimension = 768;
    private const int MaximumArea = 1_048_576;

    private readonly MicrosoftFoundryOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="MaiImageService"/> class.
    /// </summary>
    /// <param name="options">Foundry configuration values.</param>
    public MaiImageService(IOptions<MicrosoftFoundryOptions> options)
    {
        ArgumentNullException.ThrowIfNull(options);

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

        if (string.IsNullOrWhiteSpace(_options.ApiKey))
        {
            return MaiImageResult.Failure("Set MicrosoftFoundry:ApiKey before generating images.");
        }

        var size = request.Width switch
        {
            1024 when request.Height == 1024 => GeneratedImageSize.W1024xH1024,
            1024 when request.Height == 1536 => GeneratedImageSize.W1024xH1536,
            1536 when request.Height == 1024 => GeneratedImageSize.W1536xH1024,
            _ => GeneratedImageSize.W1024xH1024,
        };

        ImageClient client = new(
            credential: new ApiKeyCredential(_options.ApiKey),
            model: _options.ImageDeployment,
            options: new OpenAIClientOptions
            {
                Endpoint = resourceUri,
            });

        try
        {
            var result = await client.GenerateImageAsync(
                request.Prompt,
                new ImageGenerationOptions { Size = size },
                cancellationToken: cancellationToken).ConfigureAwait(false);

            var bytes = result.Value.ImageBytes;
            if (bytes is null || bytes.ToArray().Length == 0)
            {
                return MaiImageResult.Failure("The service did not return an image payload.");
            }

            var base64 = Convert.ToBase64String(bytes.ToArray());
            return MaiImageResult.Success(base64);
        }
        catch (Exception ex)
        {
            return MaiImageResult.Failure($"Image generation failed: {ex.Message}");
        }
    }
}