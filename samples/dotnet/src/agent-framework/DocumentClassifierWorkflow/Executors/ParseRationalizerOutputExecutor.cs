// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// ParseRationalizerOutput executor that collects and normalizes outputs
/// from both Generic and ContentType rationalizers.
/// </summary>
internal sealed class ParseRationalizerOutputExecutor() :
    ReflectingExecutor<ParseRationalizerOutputExecutor>("ParseRationalizerOutputExecutor"),
    IMessageHandler<RationalizerOutput>
{
    private readonly object _lock = new();
    private RationalizerOutput? _genericOutput;
    private RationalizerOutput? _contentTypeOutput;
    private int _receivedCount;

    /// <summary>
    /// Collects rationalizer outputs and combines them when both are received.
    /// </summary>
    /// <param name="output">A rationalizer output from either Generic or ContentType.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        RationalizerOutput output,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        CombinedRationalizerOutput? combinedOutput = null;

        lock (_lock)
        {
            if (output.Source.Equals("Generic", StringComparison.OrdinalIgnoreCase))
            {
                _genericOutput = output;
            }
            else if (output.Source.Equals("ContentType", StringComparison.OrdinalIgnoreCase))
            {
                _contentTypeOutput = output;
            }

            _receivedCount++;

            // When we have both outputs, combine and forward
            if (_receivedCount >= 2 && _genericOutput is not null && _contentTypeOutput is not null)
            {
                combinedOutput = new CombinedRationalizerOutput(
                    GenericOutput: _genericOutput,
                    ContentTypeOutput: _contentTypeOutput);

                // Reset for potential reuse
                ResetState();
            }
        }

        if (combinedOutput is not null)
        {
            await context.SendMessageAsync(combinedOutput, cancellationToken).ConfigureAwait(false);
        }
    }

    private void ResetState()
    {
        _genericOutput = null;
        _contentTypeOutput = null;
        _receivedCount = 0;
    }
}
