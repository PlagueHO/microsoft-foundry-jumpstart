namespace ImageGenerationExplorer.Models;

/// <summary>
/// Represents a single comparison run — one prompt evaluated across multiple models.
/// </summary>
public sealed class ComparisonRun
{
    /// <summary>
    /// Gets the prompt used for this comparison.
    /// </summary>
    public required string Prompt { get; init; }

    /// <summary>
    /// Gets the timestamp when this comparison was started.
    /// </summary>
    public DateTimeOffset Timestamp { get; init; } = DateTimeOffset.UtcNow;

    /// <summary>
    /// Gets the results from each model in this comparison.
    /// </summary>
    public required IReadOnlyList<ImageGenerationResult> Results { get; set; }

    /// <summary>
    /// Gets the deployment names of models that were enabled for this run.
    /// </summary>
    public IReadOnlySet<string> EnabledDeployments { get; init; } = new HashSet<string>();
}
