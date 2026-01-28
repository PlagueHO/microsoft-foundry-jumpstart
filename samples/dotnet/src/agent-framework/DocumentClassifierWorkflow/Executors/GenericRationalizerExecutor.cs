// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using Microsoft.Extensions.AI;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// Generic Rationalizer LLM executor that decides whether to CREATE_NEW, MAP, or MAP_AS_VARIANT.
/// Uses general document classification heuristics.
/// </summary>
internal sealed class GenericRationalizerExecutor : ReflectingExecutor<GenericRationalizerExecutor>,
    IMessageHandler<RationalizerInput>
{
    private readonly IChatClient? _chatClient;

    private const string SystemPrompt = """
        You are a document classification rationalizer. Based on the document analysis results, decide the best classification action.
        Choose one of three actions:
        - CREATE_NEW: Create a new classification category if this document type is truly novel
        - MAP: Map to an existing well-known category if there's a clear match
        - MAP_AS_VARIANT: Create as a variant of an existing category if it's similar but distinct

        Respond with a JSON object containing:
        - "decision": One of "CREATE_NEW", "MAP", or "MAP_AS_VARIANT"
        - "mappingTarget": The target category name (if MAP or MAP_AS_VARIANT, otherwise null)
        - "newTypeName": The new type name (if CREATE_NEW, otherwise null)
        - "reasoning": Brief explanation of your decision

        Only respond with valid JSON, no additional text.
        """;

    /// <summary>
    /// Initializes a new instance of the <see cref="GenericRationalizerExecutor"/> class.
    /// </summary>
    /// <param name="chatClient">Optional chat client for LLM calls.</param>
    public GenericRationalizerExecutor(IChatClient? chatClient = null) : base("GenericRationalizerExecutor")
    {
        _chatClient = chatClient;
    }

    /// <summary>
    /// Analyzes the payload and determines the rationalization decision.
    /// </summary>
    /// <param name="input">The rationalizer input.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        RationalizerInput input,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        RationalizerOutput result;

        if (_chatClient is not null)
        {
            result = await GetLLMDecisionAsync(input, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            // Fallback to heuristic-based decision
            result = GetHeuristicDecision(input);
        }

        await context.SendMessageAsync(result, cancellationToken).ConfigureAwait(false);
    }

    private async Task<RationalizerOutput> GetLLMDecisionAsync(
        RationalizerInput input,
        CancellationToken cancellationToken)
    {
        var contextInfo = BuildContextInfo(input);
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, SystemPrompt),
            new(ChatRole.User, $"Rationalize this document classification:\n\n{contextInfo}")
        };

        var response = await _chatClient!.GetResponseAsync(messages, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        return ParseLLMResponse(response.Text ?? "{}", "Generic");
    }

    private static RationalizerOutput GetHeuristicDecision(RationalizerInput input)
    {
        var candidates = input.Payload.CandidateResponses;
        var genericResult = input.Payload.GenericResult;

        // If we have high-confidence candidates, MAP to them
        var highConfidenceCandidate = candidates.FirstOrDefault(c => c.Confidence >= 0.85);
        if (highConfidenceCandidate is not null)
        {
            return new RationalizerOutput(
                Decision: RationalizerDecision.MAP,
                MappingTarget: highConfidenceCandidate.Type,
                NewTypeName: null,
                Reasoning: $"High confidence ({highConfidenceCandidate.Confidence:P0}) match found from {highConfidenceCandidate.Source}",
                Source: "Generic");
        }

        // If we have moderate confidence candidates, MAP_AS_VARIANT
        var moderateConfidenceCandidate = candidates.FirstOrDefault(c => c.Confidence >= 0.6);
        if (moderateConfidenceCandidate is not null)
        {
            return new RationalizerOutput(
                Decision: RationalizerDecision.MAP_AS_VARIANT,
                MappingTarget: moderateConfidenceCandidate.Type,
                NewTypeName: null,
                Reasoning: $"Moderate confidence ({moderateConfidenceCandidate.Confidence:P0}) suggests variant of {moderateConfidenceCandidate.Type}",
                Source: "Generic");
        }

        // Otherwise CREATE_NEW
        var newTypeName = genericResult?.IdentifiedType ?? "Unknown Document Type";
        return new RationalizerOutput(
            Decision: RationalizerDecision.CREATE_NEW,
            MappingTarget: null,
            NewTypeName: newTypeName,
            Reasoning: "No existing category matches with sufficient confidence",
            Source: "Generic");
    }

    private static string BuildContextInfo(RationalizerInput input)
    {
        var lines = new List<string>
        {
            $"Document excerpt: {input.Payload.Input.Document[..Math.Min(500, input.Payload.Input.Document.Length)]}...",
            $"Search result: Match={input.SearchResult.MatchFound}, Term={input.SearchResult.MatchedTerm ?? "N/A"}, Type={input.SearchResult.MatchType ?? "N/A"}",
            "Candidate responses:"
        };

        foreach (var candidate in input.Payload.CandidateResponses)
        {
            lines.Add($"  - {candidate.Type} (confidence: {candidate.Confidence:P0}, source: {candidate.Source})");
        }

        if (input.Payload.GenericResult is not null)
        {
            lines.Add($"Generic identification: {input.Payload.GenericResult.IdentifiedType}, Schema: {input.Payload.GenericResult.Schema}");
        }

        return string.Join(Environment.NewLine, lines);
    }

    private static RationalizerOutput ParseLLMResponse(string responseText, string source)
    {
        try
        {
            using var jsonDoc = JsonDocument.Parse(responseText);
            var root = jsonDoc.RootElement;

            var decisionStr = root.GetProperty("decision").GetString() ?? "CREATE_NEW";
            var decision = Enum.TryParse<RationalizerDecision>(decisionStr, true, out var d)
                ? d
                : RationalizerDecision.CREATE_NEW;

            return new RationalizerOutput(
                Decision: decision,
                MappingTarget: root.TryGetProperty("mappingTarget", out var mt) ? mt.GetString() : null,
                NewTypeName: root.TryGetProperty("newTypeName", out var nt) ? nt.GetString() : null,
                Reasoning: root.GetProperty("reasoning").GetString() ?? "No reasoning provided",
                Source: source);
        }
        catch (JsonException)
        {
            return new RationalizerOutput(
                Decision: RationalizerDecision.CREATE_NEW,
                MappingTarget: null,
                NewTypeName: "Unknown",
                Reasoning: "Failed to parse LLM response",
                Source: source);
        }
    }
}
