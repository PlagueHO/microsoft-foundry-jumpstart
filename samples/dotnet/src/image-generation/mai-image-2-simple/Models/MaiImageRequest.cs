namespace MaiImage2Simple.Models;

/// <summary>
/// Represents a MAI image generation request from the UI.
/// </summary>
public sealed class MaiImageRequest
{
    /// <summary>
    /// Gets or sets the prompt used for image generation.
    /// </summary>
    public string Prompt { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the output width in pixels.
    /// </summary>
    public int Width { get; set; }

    /// <summary>
    /// Gets or sets the output height in pixels.
    /// </summary>
    public int Height { get; set; }

    /// <summary>
    /// Gets or sets the deployment name to use, overriding the configured default.
    /// When null or empty, the value from <c>MicrosoftFoundry:ImageDeployment</c> is used.
    /// </summary>
    public string? Deployment { get; set; }
}