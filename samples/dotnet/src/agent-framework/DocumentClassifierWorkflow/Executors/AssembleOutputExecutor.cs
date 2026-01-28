// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using static DocumentClassifierWorkflow.Executors.SelectRationalizerOutputExecutor;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// AssembleOutput executor that produces the final workflow output
/// containing candidate responses from the rationalization process.
/// </summary>
internal sealed class AssembleOutputExecutor() :
    ReflectingExecutor<AssembleOutputExecutor>("AssembleOutputExecutor"),
    IMessageHandler<SelectionResult>
{
    /// <summary>
    /// Assembles the final output from the selected rationalizer result.
    /// </summary>
    /// <param name="result">The selection result from SelectRationalizerOutput.</param>
    /// <param name="context">Workflow context for yielding output.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        SelectionResult result,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        var selectedOutput = result.SelectedOutput;

        // Build final candidate responses based on the rationalization decision
        var candidateResponses = BuildFinalCandidateResponses(selectedOutput);

        var workflowOutput = new WorkflowOutput(
            CandidateResponses: candidateResponses,
            SelectedRationalizer: selectedOutput.Source,
            FinalDecision: selectedOutput.Decision);

        // Yield the final output as the workflow result
        await context.YieldOutputAsync(workflowOutput, cancellationToken).ConfigureAwait(false);
    }

    private static List<CandidateResponse> BuildFinalCandidateResponses(RationalizerOutput output)
    {
        var responses = new List<CandidateResponse>();

        switch (output.Decision)
        {
            case RationalizerDecision.MAP:
                if (!string.IsNullOrWhiteSpace(output.MappingTarget))
                {
                    responses.Add(new CandidateResponse(
                        Type: output.MappingTarget,
                        Confidence: 0.90,
                        Source: $"Rationalizer ({output.Source}) - Mapped"));
                }
                break;

            case RationalizerDecision.MAP_AS_VARIANT:
                if (!string.IsNullOrWhiteSpace(output.MappingTarget))
                {
                    // Add both the parent type and the variant
                    responses.Add(new CandidateResponse(
                        Type: $"{output.MappingTarget} (Variant)",
                        Confidence: 0.85,
                        Source: $"Rationalizer ({output.Source}) - Variant"));

                    responses.Add(new CandidateResponse(
                        Type: output.MappingTarget,
                        Confidence: 0.70,
                        Source: $"Rationalizer ({output.Source}) - Parent Type"));
                }
                break;

            case RationalizerDecision.CREATE_NEW:
                var newTypeName = output.NewTypeName ?? "New Document Type";
                responses.Add(new CandidateResponse(
                    Type: newTypeName,
                    Confidence: 0.75,
                    Source: $"Rationalizer ({output.Source}) - New Type"));
                break;
        }

        // Add reasoning as a metadata response if no other responses
        if (responses.Count == 0)
        {
            responses.Add(new CandidateResponse(
                Type: "Unclassified",
                Confidence: 0.50,
                Source: $"Rationalizer ({output.Source}) - Fallback"));
        }

        return responses;
    }
}
