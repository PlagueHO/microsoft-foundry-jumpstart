using MaiImage2Simple.Models;

namespace MaiImage2Simple.Services;

/// <summary>
/// Provides MAI image generation operations.
/// </summary>
public interface IMaiImageService
{
    /// <summary>
    /// Generates an image using the MAI endpoint.
    /// </summary>
    /// <param name="request">Image request parameters.</param>
    /// <param name="cancellationToken">A cancellation token.</param>
    /// <returns>The generation result with either image payload or error.</returns>
    Task<MaiImageResult> GenerateImageAsync(
        MaiImageRequest request,
        CancellationToken cancellationToken = default);
}