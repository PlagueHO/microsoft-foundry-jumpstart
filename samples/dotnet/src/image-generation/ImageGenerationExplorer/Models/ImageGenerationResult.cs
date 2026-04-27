namespace ImageGenerationExplorer.Models;

/// <summary>
/// Result of an image generation attempt for a single model.
/// </summary>
public sealed class ImageGenerationResult
{
    /// <summary>
    /// Gets the deployment name that produced this result.
    /// </summary>
    public required string DeploymentName { get; init; }

    /// <summary>
    /// Gets the display name of the model.
    /// </summary>
    public required string DisplayName { get; init; }

    /// <summary>
    /// Gets a value indicating whether the request succeeded.
    /// </summary>
    public bool IsSuccess { get; init; }

    /// <summary>
    /// Gets the base64 image payload when generation succeeds.
    /// </summary>
    public string? Base64Image { get; init; }

    /// <summary>
    /// Gets a friendly error message when generation fails.
    /// </summary>
    public string? ErrorMessage { get; init; }

    /// <summary>
    /// Gets the HTTP status code when available.
    /// </summary>
    public int? StatusCode { get; init; }

    /// <summary>
    /// Gets the elapsed generation time in milliseconds.
    /// </summary>
    public long ElapsedMs { get; init; }

    /// <summary>
    /// Gets the width of the generated image.
    /// </summary>
    public int Width { get; init; }

    /// <summary>
    /// Gets the height of the generated image.
    /// </summary>
    public int Height { get; init; }

    /// <summary>
    /// Creates a successful result.
    /// </summary>
    public static ImageGenerationResult Success(
        string deploymentName,
        string displayName,
        string base64Image,
        int width,
        int height,
        long elapsedMs) => new()
    {
        DeploymentName = deploymentName,
        DisplayName = displayName,
        IsSuccess = true,
        Base64Image = base64Image,
        Width = width,
        Height = height,
        ElapsedMs = elapsedMs,
    };

    /// <summary>
    /// Creates a failed result.
    /// </summary>
    public static ImageGenerationResult Failure(
        string deploymentName,
        string displayName,
        string errorMessage,
        long elapsedMs,
        int? statusCode = null) => new()
    {
        DeploymentName = deploymentName,
        DisplayName = displayName,
        IsSuccess = false,
        ErrorMessage = errorMessage,
        ElapsedMs = elapsedMs,
        StatusCode = statusCode,
    };
}
