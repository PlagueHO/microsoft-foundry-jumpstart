// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// ProcessOutput / Merge executor that combines results from the parallel
/// LLM and PI service executions into a unified payload.
/// Aggregates: PI result + Content Type suggestion + Generic identification
/// into candidateResponses and suggestion_output.
/// </summary>
internal sealed class ProcessOutputExecutor() :
    ReflectingExecutor<ProcessOutputExecutor>("ProcessOutputExecutor"),
    IMessageHandler<PIServiceResult>,
    IMessageHandler<ContentTypeSuggestion>,
    IMessageHandler<GenericIdentificationResult>
{
    private readonly object _lock = new();
    private WorkflowInput? _input;
    private PIServiceResult? _piResult;
    private ContentTypeSuggestion? _contentTypeSuggestion;
    private GenericIdentificationResult? _genericResult;
    private int _expectedResults = 3;
    private int _receivedResults;

    /// <summary>
    /// Handles incoming PI service results.
    /// </summary>
    /// <param name="result">The PI service result.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        PIServiceResult result,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        lock (_lock)
        {
            _piResult = result;
            _input ??= result.Input;
            _receivedResults++;
        }

        await TryEmitUnifiedPayloadAsync(context, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Handles incoming content type suggestions.
    /// </summary>
    /// <param name="result">The content type suggestion.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        ContentTypeSuggestion result,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        lock (_lock)
        {
            _contentTypeSuggestion = result;
            _input ??= result.Input;
            _receivedResults++;
        }

        await TryEmitUnifiedPayloadAsync(context, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Handles incoming generic identification results.
    /// </summary>
    /// <param name="result">The generic identification result.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        GenericIdentificationResult result,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        lock (_lock)
        {
            _genericResult = result;
            _input ??= result.Input;
            _receivedResults++;
        }

        await TryEmitUnifiedPayloadAsync(context, cancellationToken).ConfigureAwait(false);
    }

    private async ValueTask TryEmitUnifiedPayloadAsync(
        IWorkflowContext context,
        CancellationToken cancellationToken)
    {
        UnifiedPayload? payload = null;

        lock (_lock)
        {
            if (_receivedResults >= _expectedResults && _input is not null)
            {
                var candidateResponses = BuildCandidateResponses();
                payload = new UnifiedPayload(
                    Input: _input,
                    CandidateResponses: candidateResponses,
                    SuggestionOutput: _contentTypeSuggestion,
                    PIResult: _piResult,
                    GenericResult: _genericResult);

                // Reset state for potential reuse
                ResetState();
            }
        }

        if (payload is not null)
        {
            await context.SendMessageAsync(payload, cancellationToken).ConfigureAwait(false);
        }
    }

    private List<CandidateResponse> BuildCandidateResponses()
    {
        var responses = new List<CandidateResponse>();

        if (_contentTypeSuggestion is not null)
        {
            responses.Add(new CandidateResponse(
                Type: _contentTypeSuggestion.SuggestedContentType,
                Confidence: _contentTypeSuggestion.Confidence,
                Source: "ContentTypeLLM"));
        }

        if (_genericResult is not null)
        {
            responses.Add(new CandidateResponse(
                Type: _genericResult.IdentifiedType,
                Confidence: 0.75, // Default confidence for generic identification
                Source: "GenericIdentificationLLM"));
        }

        if (_piResult is not null && _piResult.PIDetected)
        {
            responses.Add(new CandidateResponse(
                Type: "PI-Sensitive Document",
                Confidence: 0.95,
                Source: "AzurePIService"));
        }

        return responses;
    }

    private void ResetState()
    {
        _input = null;
        _piResult = null;
        _contentTypeSuggestion = null;
        _genericResult = null;
        _receivedResults = 0;
    }
}
