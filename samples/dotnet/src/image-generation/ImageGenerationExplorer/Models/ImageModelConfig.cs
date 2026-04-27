using System.ComponentModel.DataAnnotations;

namespace ImageGenerationExplorer.Models;

/// <summary>
/// Configuration for a single image generation model deployment.
/// </summary>
public sealed class ImageModelConfig
{
    /// <summary>
    /// Gets or sets the deployment name used in API calls.
    /// </summary>
    [Required]
    [MinLength(1)]
    public string DeploymentName { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the friendly display name shown in the UI.
    /// </summary>
    [Required]
    [MinLength(1)]
    public string DisplayName { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the API type that determines which provider handles this model.
    /// </summary>
    public ImageApiType ApiType { get; set; } = ImageApiType.Mai;

    /// <summary>
    /// Gets or sets the resource endpoint for this model.
    /// </summary>
    [Required]
    [Url]
    public string Endpoint { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the default output width in pixels.
    /// </summary>
    [Range(256, 8192)]
    public int DefaultWidth { get; set; } = 1024;

    /// <summary>
    /// Gets or sets the default output height in pixels.
    /// </summary>
    [Range(256, 8192)]
    public int DefaultHeight { get; set; } = 1024;

    /// <summary>
    /// Gets or sets the maximum output width in pixels supported by this model.
    /// </summary>
    [Range(256, 8192)]
    public int MaxWidth { get; set; } = 1024;

    /// <summary>
    /// Gets or sets the maximum output height in pixels supported by this model.
    /// </summary>
    [Range(256, 8192)]
    public int MaxHeight { get; set; } = 1024;

    /// <summary>
    /// Gets or sets a value indicating whether this model is enabled by default.
    /// </summary>
    public bool Enabled { get; set; } = true;
}
