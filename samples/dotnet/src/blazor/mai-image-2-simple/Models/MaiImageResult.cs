namespace MaiImage2Simple.Models;

/// <summary>
/// Represents the result of a MAI image generation attempt.
/// </summary>
public sealed class MaiImageResult
{
    /// <summary>
    /// Gets a value indicating whether the request succeeded.
    /// </summary>
    public bool IsSuccess { get; init; }

    /// <summary>
    /// Gets the base64 PNG payload when generation succeeds.
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
    /// Creates a successful image generation result.
    /// </summary>
    /// <param name="base64Image">Generated base64 image payload.</param>
    /// <returns>A successful result.</returns>
    public static MaiImageResult Success(string base64Image)
    {
        return new MaiImageResult
        {
            IsSuccess = true,
            Base64Image = base64Image,
        };
    }

    /// <summary>
    /// Creates a failed image generation result.
    /// </summary>
    /// <param name="errorMessage">Friendly error message.</param>
    /// <param name="statusCode">Optional HTTP status code.</param>
    /// <returns>A failed result.</returns>
    public static MaiImageResult Failure(string errorMessage, int? statusCode = null)
    {
        return new MaiImageResult
        {
            IsSuccess = false,
            ErrorMessage = errorMessage,
            StatusCode = statusCode,
        };
    }
}