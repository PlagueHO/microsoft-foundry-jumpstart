namespace ImageGenerationExplorer.Models;

/// <summary>
/// Discriminates which API surface to use for image generation.
/// </summary>
public enum ImageApiType
{
    /// <summary>
    /// MAI REST API at /mai/v1/images/generations.
    /// </summary>
    Mai,

    /// <summary>
    /// OpenAI-compatible API via Azure.AI.OpenAI SDK.
    /// </summary>
    OpenAi,
}
