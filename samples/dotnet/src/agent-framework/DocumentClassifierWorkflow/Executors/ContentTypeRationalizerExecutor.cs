// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using Microsoft.Extensions.AI;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// Content Type Rationalizer LLM executor that decides whether to CREATE_NEW, MAP, or MAP_AS_VARIANT.
/// Specializes in content type-specific classification logic.
/// </summary>
internal sealed class ContentTypeRationalizerExecutor : ReflectingExecutor<ContentTypeRationalizerExecutor>,
    IMessageHandler<RationalizerInput>
{
    private readonly IChatClient? _chatClient;

    private const string SystemPrompt = """
        You are a content type classification specialist. Based on the document content type analysis, decide the best classification action.
        Focus specifically on content type categorization (e.g., Legal, Financial, Technical, Medical, etc.).

        Choose one of three actions:
        - CREATE_NEW: Create a new content type category if this is a genuinely new type
        - MAP: Map to an existing content type if there's a clear match
        - MAP_AS_VARIANT: Create as a variant if it's a sub-type of an existing category

        Known content types to consider: Legal Contract, Financial Report, Technical Documentation, Invoice, Medical Record, Resume, Policy Document, Marketing Material, Email, Memo, Manual, Article.

        Respond with a JSON object containing:
        - "decision": One of "CREATE_NEW", "MAP", or "MAP_AS_VARIANT"
        - "mappingTarget": The target category name (if MAP or MAP_AS_VARIANT, otherwise null)
        - "newTypeName": The new type name (if CREATE_NEW, otherwise null)
        - "reasoning": Brief explanation focusing on content type characteristics

        Only respond with valid JSON, no additional text.
        """;

    /// <summary>
    /// Known content type categories for classification.
    /// </summary>
    private static readonly HashSet<string> KnownContentTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        "Legal Contract",
        "Financial Report",
        "Technical Documentation",
        "Invoice",
        "Medical Record",
        "Resume",
        "Policy Document",
        "Marketing Material",
        "Email",
        "Memo",
        "Manual",
        "Article"
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="ContentTypeRationalizerExecutor"/> class.
    /// </summary>
    /// <param name="chatClient">Optional chat client for LLM calls.</param>
    public ContentTypeRationalizerExecutor(IChatClient? chatClient = null) : base("ContentTypeRationalizerExecutor")
    {
        _chatClient = chatClient;
    }

    /// <summary>
    /// Analyzes the payload with content type focus and determines the rationalization decision.
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
            new(ChatRole.User, $"Analyze and rationalize this content type classification:\n\n{contextInfo}")
        };

        var response = await _chatClient!.GetResponseAsync(messages, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        return ParseLLMResponse(response.Text ?? "{}", "ContentType");
    }

    private RationalizerOutput GetHeuristicDecision(RationalizerInput input)
    {
        var suggestion = input.Payload.SuggestionOutput;
        if (suggestion is null)
        {
            return new RationalizerOutput(
                Decision: RationalizerDecision.CREATE_NEW,
                MappingTarget: null,
                NewTypeName: "Unclassified Content",
                Reasoning: "No content type suggestion available",
                Source: "ContentType");
        }

        var suggestedType = suggestion.SuggestedContentType;

        // Check for exact match in known types
        if (KnownContentTypes.Contains(suggestedType))
        {
            return new RationalizerOutput(
                Decision: RationalizerDecision.MAP,
                MappingTarget: suggestedType,
                NewTypeName: null,
                Reasoning: $"'{suggestedType}' is a recognized content type",
                Source: "ContentType");
        }

        // Check for partial matches
        var partialMatch = KnownContentTypes.FirstOrDefault(kt =>
            kt.Contains(suggestedType, StringComparison.OrdinalIgnoreCase) ||
            suggestedType.Contains(kt, StringComparison.OrdinalIgnoreCase));

        if (partialMatch is not null && suggestion.Confidence >= 0.6)
        {
            return new RationalizerOutput(
                Decision: RationalizerDecision.MAP_AS_VARIANT,
                MappingTarget: partialMatch,
                NewTypeName: null,
                Reasoning: $"'{suggestedType}' appears to be a variant of '{partialMatch}'",
                Source: "ContentType");
        }

        // Check if we should create based on confidence
        if (suggestion.Confidence >= 0.7)
        {
            return new RationalizerOutput(
                Decision: RationalizerDecision.CREATE_NEW,
                MappingTarget: null,
                NewTypeName: suggestedType,
                Reasoning: $"'{suggestedType}' is a distinct content type not matching known categories (confidence: {suggestion.Confidence:P0})",
                Source: "ContentType");
        }

        // Low confidence - try to map to closest known type
        var closestType = FindClosestContentType(suggestedType);
        return new RationalizerOutput(
            Decision: RationalizerDecision.MAP_AS_VARIANT,
            MappingTarget: closestType,
            NewTypeName: null,
            Reasoning: $"Low confidence ({suggestion.Confidence:P0}), mapping to closest known type '{closestType}'",
            Source: "ContentType");
    }

    private static string FindClosestContentType(string suggestedType)
    {
        var lower = suggestedType.ToLowerInvariant();

        return lower switch
        {
            var s when s.Contains("legal") || s.Contains("contract") || s.Contains("agreement") => "Legal Contract",
            var s when s.Contains("financial") || s.Contains("report") || s.Contains("quarterly") => "Financial Report",
            var s when s.Contains("technical") || s.Contains("doc") || s.Contains("api") => "Technical Documentation",
            var s when s.Contains("invoice") || s.Contains("bill") => "Invoice",
            var s when s.Contains("medical") || s.Contains("health") || s.Contains("patient") => "Medical Record",
            var s when s.Contains("resume") || s.Contains("cv") => "Resume",
            var s when s.Contains("policy") || s.Contains("procedure") => "Policy Document",
            var s when s.Contains("market") || s.Contains("promo") => "Marketing Material",
            _ => "Technical Documentation" // Default fallback
        };
    }

    private static string BuildContextInfo(RationalizerInput input)
    {
        var lines = new List<string>
        {
            $"Document excerpt: {input.Payload.Input.Document[..Math.Min(500, input.Payload.Input.Document.Length)]}..."
        };

        if (input.Payload.SuggestionOutput is not null)
        {
            lines.Add($"Suggested content type: {input.Payload.SuggestionOutput.SuggestedContentType} (confidence: {input.Payload.SuggestionOutput.Confidence:P0})");
        }

        lines.Add($"Search result: Match={input.SearchResult.MatchFound}, Term={input.SearchResult.MatchedTerm ?? "N/A"}");
        lines.Add($"Known content types: {string.Join(", ", KnownContentTypes)}");

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
