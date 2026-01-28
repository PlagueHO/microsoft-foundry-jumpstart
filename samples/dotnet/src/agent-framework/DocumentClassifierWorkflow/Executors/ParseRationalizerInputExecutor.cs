// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// ParseRationalizerInput executor that shapes the payload for the rationalizer LLMs.
/// Part of the STANDALONERATIONLISER flow.
/// </summary>
internal sealed class ParseRationalizerInputExecutor() :
    ReflectingExecutor<ParseRationalizerInputExecutor>("ParseRationalizerInputExecutor"),
    IMessageHandler<RationalizerInput>
{
    /// <summary>
    /// Shapes the rationalizer input and forwards to both rationalizer LLMs.
    /// </summary>
    /// <param name="input">The rationalizer input from MatchDecision.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        RationalizerInput input,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        // Forward the input to both rationalizer LLMs in parallel
        // The workflow's fan-out edge will handle the distribution
        await context.SendMessageAsync(input, cancellationToken).ConfigureAwait(false);
    }
}
