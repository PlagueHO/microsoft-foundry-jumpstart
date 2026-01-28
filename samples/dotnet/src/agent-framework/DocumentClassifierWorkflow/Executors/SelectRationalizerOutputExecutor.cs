// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// SelectRationalizerOutput executor that chooses between the Generic
/// and ContentType rationalizer outputs based on decision quality.
/// </summary>
internal sealed class SelectRationalizerOutputExecutor() :
    ReflectingExecutor<SelectRationalizerOutputExecutor>("SelectRationalizerOutputExecutor"),
    IMessageHandler<CombinedRationalizerOutput>
{
    /// <summary>
    /// Selection result containing the chosen output and selection rationale.
    /// </summary>
    /// <param name="SelectedOutput">The selected rationalizer output.</param>
    /// <param name="SelectionRationale">Why this output was selected.</param>
    public sealed record SelectionResult(
        RationalizerOutput SelectedOutput,
        string SelectionRationale);

    /// <summary>
    /// Selects the more appropriate rationalizer output based on decision criteria.
    /// </summary>
    /// <param name="combined">The combined outputs from both rationalizers.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        CombinedRationalizerOutput combined,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        var (selectedOutput, rationale) = SelectBestOutput(
            combined.GenericOutput,
            combined.ContentTypeOutput);

        var result = new SelectionResult(selectedOutput, rationale);
        await context.SendMessageAsync(result, cancellationToken).ConfigureAwait(false);
    }

    private static (RationalizerOutput Output, string Rationale) SelectBestOutput(
        RationalizerOutput genericOutput,
        RationalizerOutput contentTypeOutput)
    {
        // Priority 1: If one has MAP and the other has CREATE_NEW, prefer MAP
        // (existing categories are usually more reliable)
        if (contentTypeOutput.Decision == RationalizerDecision.MAP &&
            genericOutput.Decision == RationalizerDecision.CREATE_NEW)
        {
            return (contentTypeOutput, "ContentType rationalizer found a direct mapping while Generic suggested new type");
        }

        if (genericOutput.Decision == RationalizerDecision.MAP &&
            contentTypeOutput.Decision == RationalizerDecision.CREATE_NEW)
        {
            return (genericOutput, "Generic rationalizer found a direct mapping while ContentType suggested new type");
        }

        // Priority 2: If both agree on the decision, prefer ContentType for its specialization
        if (genericOutput.Decision == contentTypeOutput.Decision)
        {
            return (contentTypeOutput, $"Both rationalizers agree on {contentTypeOutput.Decision}; preferring ContentType specialization");
        }

        // Priority 3: Prefer MAP_AS_VARIANT over CREATE_NEW (more conservative)
        if (contentTypeOutput.Decision == RationalizerDecision.MAP_AS_VARIANT)
        {
            return (contentTypeOutput, "ContentType suggests mapping as variant (conservative approach)");
        }

        if (genericOutput.Decision == RationalizerDecision.MAP_AS_VARIANT)
        {
            return (genericOutput, "Generic suggests mapping as variant (conservative approach)");
        }

        // Priority 4: If ContentType suggests CREATE_NEW with specific reasoning, prefer it
        if (contentTypeOutput.Decision == RationalizerDecision.CREATE_NEW &&
            !string.IsNullOrWhiteSpace(contentTypeOutput.NewTypeName) &&
            !contentTypeOutput.NewTypeName.Equals("Unknown", StringComparison.OrdinalIgnoreCase))
        {
            return (contentTypeOutput, $"ContentType proposes new type '{contentTypeOutput.NewTypeName}' with specific classification");
        }

        // Default: Prefer ContentType rationalizer as the specialized classifier
        return (contentTypeOutput, "Defaulting to ContentType rationalizer as the specialized classifier");
    }
}
