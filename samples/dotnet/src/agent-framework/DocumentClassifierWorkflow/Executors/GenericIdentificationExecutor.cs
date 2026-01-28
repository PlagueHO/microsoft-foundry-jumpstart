// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using Microsoft.Extensions.AI;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// GenericIdentification LLM executor that uses an AI model to identify
/// document type with schema-enforced output.
/// </summary>
internal sealed class GenericIdentificationExecutor : ReflectingExecutor<GenericIdentificationExecutor>,
    IMessageHandler<RoutingDecision>
{
    private readonly IChatClient? _chatClient;

    private const string SystemPrompt = """
        You are a document identification and schema extraction expert. Analyze the provided document and identify its type and structure.
        Respond with a JSON object containing:
        - "identifiedType": The document type (e.g., "Contract", "Report", "Email", "Memo", "Form", "Article", "Manual")
        - "schema": A brief description of the document's structure/schema
        - "metadata": An object with key-value pairs of extracted metadata (e.g., {"author": "...", "date": "...", "version": "..."})

        Only respond with valid JSON, no additional text. Ensure the response conforms to this schema.
        """;

    /// <summary>
    /// Initializes a new instance of the <see cref="GenericIdentificationExecutor"/> class.
    /// </summary>
    /// <param name="chatClient">Optional chat client for LLM calls.</param>
    public GenericIdentificationExecutor(IChatClient? chatClient = null) : base("GenericIdentificationExecutor")
    {
        _chatClient = chatClient;
    }

    /// <summary>
    /// Identifies the document type and extracts schema information using LLM.
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
        GenericIdentificationResult result;

        if (_chatClient is not null)
        {
            result = await GetLLMIdentificationAsync(input, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            // Fallback to heuristic-based identification
            result = GetHeuristicIdentification(input);
        }

        await context.SendMessageAsync(result, cancellationToken).ConfigureAwait(false);
    }

    private async Task<GenericIdentificationResult> GetLLMIdentificationAsync(
        WorkflowInput input,
        CancellationToken cancellationToken)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, SystemPrompt),
            new(ChatRole.User, $"Identify and analyze this document:\n\n{input.Document}")
        };

        var response = await _chatClient!.GetResponseAsync(messages, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        var responseText = response.Text ?? "{}";

        try
        {
            using var jsonDoc = JsonDocument.Parse(responseText);
            var root = jsonDoc.RootElement;

            var metadata = new Dictionary<string, string>();
            if (root.TryGetProperty("metadata", out var metadataElement))
            {
                foreach (var property in metadataElement.EnumerateObject())
                {
                    metadata[property.Name] = property.Value.GetString() ?? "";
                }
            }

            return new GenericIdentificationResult(
                Input: input,
                IdentifiedType: root.GetProperty("identifiedType").GetString() ?? "Unknown",
                Schema: root.GetProperty("schema").GetString() ?? "Unstructured",
                Metadata: metadata);
        }
        catch (JsonException)
        {
            return new GenericIdentificationResult(
                Input: input,
                IdentifiedType: "Unknown",
                Schema: "Unstructured",
                Metadata: new Dictionary<string, string>());
        }
    }

    private static GenericIdentificationResult GetHeuristicIdentification(WorkflowInput input)
    {
        var content = input.Document.ToLowerInvariant();
        var metadata = new Dictionary<string, string>();

        // Extract any dates found
        var dateMatch = System.Text.RegularExpressions.Regex.Match(content, @"\d{1,2}/\d{1,2}/\d{2,4}");
        if (dateMatch.Success)
        {
            metadata["date"] = dateMatch.Value;
        }

        var (identifiedType, schema) = content switch
        {
            var c when c.Contains("dear", StringComparison.OrdinalIgnoreCase) &&
                       c.Contains("sincerely", StringComparison.OrdinalIgnoreCase) =>
                ("Letter", "Header, Salutation, Body, Closing, Signature"),
            var c when c.Contains("subject:", StringComparison.OrdinalIgnoreCase) &&
                       c.Contains("from:", StringComparison.OrdinalIgnoreCase) =>
                ("Email", "Headers (From, To, Subject), Body, Attachments"),
            var c when c.Contains("table of contents", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("chapter", StringComparison.OrdinalIgnoreCase) =>
                ("Manual", "Title, TOC, Chapters, Sections, Index"),
            var c when c.Contains("whereas", StringComparison.OrdinalIgnoreCase) ||
                       c.Contains("party", StringComparison.OrdinalIgnoreCase) =>
                ("Contract", "Parties, Recitals, Terms, Signatures"),
            var c when c.Contains("summary", StringComparison.OrdinalIgnoreCase) &&
                       c.Contains("conclusion", StringComparison.OrdinalIgnoreCase) =>
                ("Report", "Executive Summary, Body, Analysis, Conclusion"),
            _ => ("Document", "Unstructured text content")
        };

        return new GenericIdentificationResult(
            Input: input,
            IdentifiedType: identifiedType,
            Schema: schema,
            Metadata: metadata);
    }
}
