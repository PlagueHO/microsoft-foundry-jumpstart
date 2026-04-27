using ImageGenerationExplorer.Models;

namespace ImageGenerationExplorer.Services;

/// <summary>
/// Generates an image using a specific API surface.
/// </summary>
public interface IImageGenerationProvider
{
    /// <summary>
    /// Gets the API type this provider handles.
    /// </summary>
    ImageApiType ApiType { get; }

    /// <summary>
    /// Generates an image for the given prompt and model configuration.
    /// </summary>
    /// <param name="prompt">The text prompt.</param>
    /// <param name="width">Output width in pixels.</param>
    /// <param name="height">Output height in pixels.</param>
    /// <param name="model">Model configuration including deployment name.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The generation result.</returns>
    Task<ImageGenerationResult> GenerateAsync(
        string prompt,
        int width,
        int height,
        ImageModelConfig model,
        CancellationToken cancellationToken = default);
}
