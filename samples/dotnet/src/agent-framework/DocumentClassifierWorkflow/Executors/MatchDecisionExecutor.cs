// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// MatchDecision executor that routes based on whether a match was found.
/// If match found → emit CandidateResponse and stop.
/// If no match → continue to StandaloneRationaliser path.
/// </summary>
internal sealed class MatchDecisionExecutor() :
    ReflectingExecutor<MatchDecisionExecutor>("MatchDecisionExecutor"),
    IMessageHandler<SearchResult>
{
    /// <summary>
    /// Evaluates the search result and routes accordingly.
    /// Emits MatchDecisionOutput with isMatch flag for conditional routing.
    /// </summary>
    /// <param name="result">The search result from Encompass5Search.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        SearchResult result,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        if (result.MatchFound && result.MatchedTerm is not null)
        {
            // Match found - emit candidate response as output
            var finalResponses = new List<CandidateResponse>(result.Payload.CandidateResponses)
            {
                new CandidateResponse(
                    Type: result.MatchedTerm,
                    Confidence: 0.95,
                    Source: $"Encompass5Search ({result.MatchType})")
            };

            var output = new WorkflowOutput(
                CandidateResponses: finalResponses,
                SelectedRationalizer: null,
                FinalDecision: null);

            await context.YieldOutputAsync(output, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            // No match - continue to rationalizer path
            var rationalizerInput = new RationalizerInput(
                Payload: result.Payload,
                SearchResult: result);

            await context.SendMessageAsync(rationalizerInput, cancellationToken).ConfigureAwait(false);
        }
    }
}
