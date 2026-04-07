using System.ComponentModel.DataAnnotations;

namespace MaiImage2Simple.Models;

/// <summary>
/// Configuration values for Microsoft Foundry image generation.
/// </summary>
public sealed class MicrosoftFoundryOptions
{
    /// <summary>
    /// The configuration section name for the Microsoft Foundry settings.
    /// </summary>
    public const string SectionName = "MicrosoftFoundry";

    /// <summary>
    /// Gets or sets the Foundry resource endpoint used for MAI requests.
    /// </summary>
    [Required]
    [Url]
    public string ResourceEndpoint { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the deployment name for the MAI image model.
    /// </summary>
    [Required]
    [MinLength(1)]
    public string ImageDeployment { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the default output width in pixels.
    /// </summary>
    [Range(768, 8192)]
    public int DefaultWidth { get; set; } = 1024;

    /// <summary>
    /// Gets or sets the default output height in pixels.
    /// </summary>
    [Range(768, 8192)]
    public int DefaultHeight { get; set; } = 1024;
}