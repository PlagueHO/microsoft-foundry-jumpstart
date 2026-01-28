// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using Microsoft.Extensions.AI;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// SuggestContentType LLM executor that uses an AI model to suggest
/// the content type of a document. Returns a single-candidate JSON response.
/// </summary>
internal sealed class SuggestContentTypeExecutor : ReflectingExecutor<SuggestContentTypeExecutor>,
    IMessageHandler<RoutingDecision>
{
    private readonly IChatClient? _chatClient;

    private const string SystemPrompt = """
        You are a document content type classifier. Analyze the provided document and suggest the most appropriate content type.
        Respond with a JSON object containing:
        - "suggestedContentType": The primary content type (e.g., "Legal Contract", "Financial Report", "Technical Documentation", "Marketing Material", "Medical Record", "Invoice", "Resume", "Policy Document")
        - "confidence": A confidence score between 0.0 and 1.0

        Only respond with valid JSON, no additional text.
        """;

    /// <summary>
    /// Initializes a new instance of the <see cref="SuggestContentTypeExecutor"/> class.
    /// </summary>
    /// <param name="chatClient">Optional chat client for LLM calls.</param>
    public SuggestContentTypeExecutor(IChatClient? chatClient = null) : base("SuggestContentTypeExecutor")
    {
        _chatClient = chatClient;
    }

    /// <summary>
    /// Analyzes the document and suggests a content type using LLM.
    /// </summary>
    /// <param name="decision">The routing decision containing the input.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        RoutingDecision decision,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        var input = decision.Input;
        ContentTypeSuggestion result;

        if (_chatClient is not null)
        {
            result = await GetLLMSuggestionAsync(input, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            // Fallback to heuristic-based classification
            result = GetHeuristicSuggestion(input);
        }

        await context.SendMessageAsync(result, cancellationToken).ConfigureAwait(false);
    }

    private async Task<ContentTypeSuggestion> GetLLMSuggestionAsync(
        WorkflowInput input,
        CancellationToken cancellationToken)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, SystemPrompt),
            new(ChatRole.User, $"Analyze this document and suggest its content type:\n\n{input.Document}")
        };

        var response = await _chatClient!.GetResponseAsync(messages, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        var responseText = response.Text ?? "{}";

        try
        {
            using var jsonDoc = JsonDocument.Parse(responseText);
            var root = jsonDoc.RootElement;

            return new ContentTypeSuggestion(
                Input: input,
                SuggestedContentType: root.GetProperty("suggestedContentType").GetString() ?? "Unknown",
                Confidence: root.GetProperty("confidence").GetDouble());
        }
        catch (JsonException)
        {
            return new ContentTypeSuggestion(
                Input: input,
                SuggestedContentType: "Unknown",
                Confidence: 0.0);
        }
    }

    private static ContentTypeSuggestion GetHeuristicSuggestion(WorkflowInput input)
    {
        var content = input.Document.ToLowerInvariant();
        var (contentType, confidence) = content switch
        {
            var c when c.Contains("hereby agree", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("terms and conditions", StringComparison.OrdinalIgnoreCase) => ("Legal Contract", 0.85),
            var c when c.Contains("revenue", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("quarterly", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("fiscal", StringComparison.OrdinalIgnoreCase) => ("Financial Report", 0.80),
            var c when c.Contains("api", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("implementation", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("architecture", StringComparison.OrdinalIgnoreCase) => ("Technical Documentation", 0.75),
            var c when c.Contains("invoice", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("amount due", StringComparison.OrdinalIgnoreCase) => ("Invoice", 0.90),
            var c when c.Contains("patient", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("diagnosis", StringComparison.OrdinalIgnoreCase) => ("Medical Record", 0.85),
            var c when c.Contains("experience", StringComparison.OrdinalIgnoreCase) &&
                       c.Contains("skills", StringComparison.OrdinalIgnoreCase) => ("Resume", 0.80),
            _ => ("General Document", 0.50)
        };

        return new ContentTypeSuggestion(
            Input: input,
            SuggestedContentType: contentType,
            Confidence: confidence);
    }
}
