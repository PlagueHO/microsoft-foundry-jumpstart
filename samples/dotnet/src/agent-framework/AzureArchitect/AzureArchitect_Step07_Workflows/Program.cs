// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using Microsoft.Extensions.AI;
using ModelContextProtocol.Client;

namespace WorkflowConcurrentSample;

/// <summary>
/// This sample demonstrates a concurrent Azure architecture review workflow.
///
/// The start executor fans a customer scenario out to five Azure Well-Architected
/// pillar specialists. Each architect uses the Microsoft Learn docs MCP server as
/// a shared tool source so every recommendation is grounded in current guidance.
/// The aggregation executor then performs a fan-in to consolidate pillar-specific
/// findings into a single response for the lead architect.
/// </summary>
/// <remarks>
/// Pre-requisites:
/// - Foundational samples should be completed first.
/// - An Azure OpenAI chat completion deployment must be configured.
/// </remarks>
public static class Program
{
    private static async Task Main()
    {
        // Set up the Azure OpenAI client that each architect will invoke.
        var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
        var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4-1";
        var chatClient = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential()).GetChatClient(deploymentName).AsIChatClient();

        // Discover tools from the Microsoft Learn docs MCP server once and share with every pillar architect.
        using var httpClient = new HttpClient();
        var transport = new HttpClientTransport(new()
        {
            Endpoint = new Uri("https://learn.microsoft.com/api/mcp"),
            Name = "MicrosoftLearnDocsClient",
        }, httpClient);

        await using var mcpClient = await McpClient.CreateAsync(transport).ConfigureAwait(false);
        var docsTools = (await mcpClient.ListToolsAsync().ConfigureAwait(false)).ToList();

        const string SharedArchitectInstructions = """
You are part of an Azure architecture review board applying the Azure Well-Architected Framework.
Ground every recommendation in Microsoft Learn guidance by calling the docs MCP tools before finalizing your answer.
Respond with focused Azure platform guidance, cite the Microsoft Learn titles you relied on, and explain trade-offs.
Avoid using or referencing the SLO calculator.
""";

        var architectProfiles = new (string AgentName, string DisplayName, string Pillar, string Focus)[]
        {
            ("ReliabilityArchitect", "Reliability Architect", "Reliability", "Design for resiliency, failover, redundancy, and recovery readiness."),
            ("SecurityArchitect", "Security Architect", "Security", "Protect identities, data, and infrastructure while meeting zero-trust expectations."),
            ("CostOptimizationArchitect", "Cost Optimization Architect", "Cost Optimization", "Manage spending, governance, and pricing efficiency without degrading outcomes."),
            ("OperationalExcellenceArchitect", "Operational Excellence Architect", "Operational Excellence", "Ensure deployments, automation, observability, and process maturity support operations."),
            ("PerformanceEfficiencyArchitect", "Performance Efficiency Architect", "Performance Efficiency", "Right-size services, plan scale, and optimize performance for workload variability."),
        };

        ChatClientAgent[] azureArchitects = architectProfiles
            .Select(profile => CreateArchitectAgent(profile))
            .ToArray();

        var startExecutor = new ConcurrentStartExecutor();
        var aggregationExecutor = new ConcurrentAggregationExecutor(
            architectProfiles.Select(profile => (profile.AgentName, profile.DisplayName)).ToArray());

        var workflow = new WorkflowBuilder(startExecutor)
            .AddFanOutEdge(startExecutor, targets: [.. azureArchitects])
            .AddFanInEdge(aggregationExecutor, sources: [.. azureArchitects])
            .WithOutputFrom(aggregationExecutor)
            .Build();

        StreamingRun run = await InProcessExecution.StreamAsync(workflow, "We are launching a new global e-commerce platform on Azure. Assess the current design and highlight gaps across the pillars.").ConfigureAwait(false);
        await foreach (WorkflowEvent evt in run.WatchStreamAsync().ConfigureAwait(false))
        {
            if (evt is WorkflowOutputEvent output)
            {
                Console.WriteLine($"Workflow completed with results:\n{output.Data}");
            }
        }

        ChatClientAgent CreateArchitectAgent((string AgentName, string DisplayName, string Pillar, string Focus) profile)
        {
            string instructions = $"""
{SharedArchitectInstructions}

Pillar focus: {profile.Pillar}
Key responsibilities: {profile.Focus}

Deliver concise guidance tailored to the {profile.Pillar} pillar while coordinating with the broader architecture team.
Identify yourself as {profile.DisplayName} in your response headers.
""";

            // Provide each architect with its own tool collection instance to avoid shared state issues.
            return new ChatClientAgent(
                chatClient,
                name: profile.AgentName,
                instructions: instructions,
                tools: new List<AITool>(docsTools));
        }
    }
}

/// <summary>
/// Executor that starts the concurrent processing by sending messages to the agents.
/// </summary>
internal sealed class ConcurrentStartExecutor() :
    ReflectingExecutor<ConcurrentStartExecutor>("ConcurrentStartExecutor"),
    IMessageHandler<string>
{
    /// <summary>
    /// Starts the concurrent processing by sending messages to the agents.
    /// </summary>
    /// <param name="message">The user message to process</param>
    /// <param name="context">Workflow context for accessing workflow services and adding events</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>A task representing the asynchronous operation</returns>
    public async ValueTask HandleAsync(string message, IWorkflowContext context, CancellationToken cancellationToken = default)
    {
        // Broadcast the message to all connected agents. Receiving agents will queue
        // the message but will not start processing until they receive a turn token.
        await context.SendMessageAsync(new ChatMessage(ChatRole.User, message), cancellationToken);
        // Broadcast the turn token to kick off the agents.
        await context.SendMessageAsync(new TurnToken(emitEvents: true), cancellationToken);
    }
}

/// <summary>
/// Executor that aggregates the results from the concurrent agents.
/// </summary>
internal sealed class ConcurrentAggregationExecutor(IReadOnlyList<(string AgentName, string DisplayName)> architects) :
    ReflectingExecutor<ConcurrentAggregationExecutor>("ConcurrentAggregationExecutor"),
    IMessageHandler<ChatMessage>
{
    private readonly IReadOnlyList<(string AgentName, string DisplayName)> _architects = architects;
    private readonly HashSet<string> _expectedArchitects = new(architects.Select(architect => architect.AgentName), StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, string> _responses = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Handles incoming messages from the agents and aggregates their responses.
    /// </summary>
    /// <param name="message">The message from the agent</param>
    /// <param name="context">Workflow context for accessing workflow services and adding events</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>A task representing the asynchronous operation</returns>
    public async ValueTask HandleAsync(ChatMessage message, IWorkflowContext context, CancellationToken cancellationToken = default)
    {
        if (message.Role != ChatRole.Assistant)
        {
            return;
        }

        var author = message.AuthorName;
        if (author is null || !this._expectedArchitects.Contains(author))
        {
            return;
        }

        if (!TryGetResponseText(message, out string responseText))
        {
            return;
        }

        this._responses[author] = responseText;

        if (this._responses.Count == this._expectedArchitects.Count)
        {
            var formattedMessages = string.Join(
                $"{Environment.NewLine}{Environment.NewLine}",
                this._architects.Select(architect =>
                    this._responses.TryGetValue(architect.AgentName, out string? architectResponse)
                        ? $"{architect.DisplayName}:{Environment.NewLine}{architectResponse}"
                        : $"{architect.DisplayName}:{Environment.NewLine}No response received."));

            await context.YieldOutputAsync(formattedMessages, cancellationToken).ConfigureAwait(false);
            this._responses.Clear();
        }
    }

    private static bool TryGetResponseText(ChatMessage message, out string response)
    {
        if (!string.IsNullOrWhiteSpace(message.Text))
        {
            response = message.Text;
            return true;
        }

        if (message.Contents.Count > 0)
        {
            var segments = message.Contents
                .OfType<TextContent>()
                .Select(static content => content.Text)
                .Where(static text => !string.IsNullOrWhiteSpace(text))
                .ToList();

            if (segments.Count > 0)
            {
                response = string.Join(Environment.NewLine, segments);
                return true;
            }
        }

        response = string.Empty;
        return false;
    }
}
