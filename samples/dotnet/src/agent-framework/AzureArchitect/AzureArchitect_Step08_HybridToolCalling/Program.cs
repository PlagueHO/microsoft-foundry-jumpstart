// Copyright (c) Microsoft. All rights reserved.

// This sample validates the hybrid tool calling scenario: combining a remote MCP server
// (Microsoft Learn) with local function tools in a single agent using client-side
// orchestration via AzureOpenAIResponsesClient (OpenAI Responses API).
//
// WHY THIS MATTERS:
// When using agent_reference with the Foundry Agent Service, tools cannot be passed at
// call time — they must be baked into the agent definition via create_version. This sample
// proves that client-side orchestration via the Responses API allows both remote MCP tools
// and local function tools to coexist in a single request, with full flexibility to change
// tool schemas per-request without recreating an agent version.
//
// PREREQUISITES:
// - Azure OpenAI endpoint with a deployed model (e.g., gpt-4.1-mini)
// - az login (for AzureCliCredential)
// - Environment variable: AZURE_OPENAI_ENDPOINT
// - Optional: AZURE_OPENAI_DEPLOYMENT_NAME (defaults to gpt-4.1-mini)
//
// NO other Azure service dependencies are required — the MCP server is the public
// Microsoft Learn endpoint.

using System.ComponentModel;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using ModelContextProtocol.Client;
using OpenAI;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT")
    ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4.1-mini";

const string AgentName = "HybridToolCallingAgent";
const string AgentInstructions = """
    You are an Azure reliability assistant that combines documentation search with availability calculations.
    Use the Microsoft Learn MCP tools to find official Azure documentation.
    Use the SLO calculator tool to compute composite availability from individual service SLAs.
    Always cite sources from Microsoft Learn when providing guidance.
    """;

// --- Local function tool: SLO composite availability calculator ---
[Description("Calculate the composite availability SLO given individual service availabilities (0-1 range).")]
static string CalculateCompositeSlo(
    [Description("Availability values for each dependent service expressed as decimals between 0 and 1.")]
    double[] availabilities)
{
    if (availabilities is null || availabilities.Length == 0)
    {
        throw new ArgumentException("At least one availability value is required.", nameof(availabilities));
    }

    double composite = availabilities.Aggregate(1.0, (current, a) => current * a);
    return $"Composite availability: {composite:P4} ({composite * 100:F4}%)";
}

// --- Remote MCP tool: Microsoft Learn documentation search ---
using var httpClient = new HttpClient();

var transport = new HttpClientTransport(new()
{
    Endpoint = new Uri("https://learn.microsoft.com/api/mcp"),
    Name = "MicrosoftLearn",
}, httpClient);

await using var mcpClient = await McpClient.CreateAsync(transport);

// Combine both tool types into a single list
var tools = new List<AITool>(await mcpClient.ListToolsAsync().ConfigureAwait(false))
{
    AIFunctionFactory.Create(CalculateCompositeSlo)
};

Console.WriteLine("=== Hybrid Tool Calling Sample ===");
Console.WriteLine($"Endpoint: {endpoint}");
Console.WriteLine($"Model: {deploymentName}");
Console.WriteLine($"Tools: {tools.Count} total (MCP from Microsoft Learn + local SLO calculator)");
Console.WriteLine();

// Create agent using AzureOpenAIClient — this uses the Responses API directly (client-side orchestration).
// Tools are passed per-request, NOT baked into an agent definition.
AIAgent agent = new AzureOpenAIClient(
    new Uri(endpoint),
    new AzureCliCredential())
     .GetChatClient(deploymentName)
     .CreateAIAgent(
        instructions: AgentInstructions,
        name: AgentName,
        tools: tools);

AgentThread thread = agent.GetNewThread();

// --- Test 1: Force both tool types to be used in a single conversation ---
Console.WriteLine("--- Test 1: Hybrid tool call (MCP + local function) ---");
Console.WriteLine("Question: What is the SLA for Azure App Service and Azure SQL Database?");
Console.WriteLine("          Then calculate the composite availability for 0.999 and 0.9995.\n");

Console.WriteLine(await agent.RunAsync("""
    First, search Microsoft Learn for the SLA guarantees of Azure App Service and Azure SQL Database.
    Then use the SLO calculator to compute the composite availability assuming
    App Service has 0.999 availability and Azure SQL Database has 0.9995.
    """, thread));

Console.WriteLine("\n\n--- Test 2: Streaming with hybrid tools ---");
Console.WriteLine("Question: What Azure patterns improve reliability beyond three nines?\n");

await foreach (var update in agent.RunStreamingAsync("""
    Search Microsoft Learn for Azure reliability patterns that can help improve
    availability beyond three nines (99.9%). Include specific patterns like
    deployment stamps, health endpoint monitoring, or queue-based load leveling.
    Then calculate the composite availability if I add a caching layer at 0.9999
    to the previous App Service (0.999) and SQL Database (0.9995) design.
    """, thread))
{
    Console.Write(update);
}

Console.WriteLine("\n\nDone.");
