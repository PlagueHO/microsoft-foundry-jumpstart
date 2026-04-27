using System.ComponentModel.DataAnnotations;

namespace ImageGenerationExplorer.Models;

/// <summary>
/// Top-level configuration for the Image Generation Explorer application.
/// </summary>
public sealed class ImageGenerationExplorerOptions
{
    /// <summary>
    /// The configuration section name.
    /// </summary>
    public const string SectionName = "ImageGenerationExplorer";

    /// <summary>
    /// Gets or sets the API key. Leave empty to use DefaultAzureCredential.
    /// </summary>
    public string ApiKey { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the configured image model deployments.
    /// </summary>
    [Required]
    [MinLength(1)]
    public IList<ImageModelConfig> Models { get; set; } = [];
}
