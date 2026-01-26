// Copyright (c) Microsoft. All rights reserved.

// This sample shows how to create and use an Azure Well-Architected reliability agent
// with tools from the Microsoft Learn MCP Server.

using System.ComponentModel;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using ModelContextProtocol.Client;
using OpenAI;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-5-mini";

const string ReliabilityAgentName = "AzureReliabilityAgent";
const string ReliabilityInstructions = """
You are the reliability agent for an Azure architecture engagement.
You focus exclusively on Azure Well-Architected reliability guidance, using Microsoft Learn content to support recommendations.
You keep responses concise, call the Microsoft Learn MCP tools to cite guidance, and invoke the SLO calculator tool whenever availability math is required.
Always highlight trade-offs that impact resiliency objectives.
""";

[Description("Calculate the composite availability SLO given individual service availabilities (0-1 range).")]
static string CalculateCompositeSlo([Description("Availability values for each dependent service expressed as decimals between 0 and 1.")] double[] availabilities)
{
    if (availabilities is null || availabilities.Length == 0)
    {
        throw new ArgumentException("At least one availability value is required.", nameof(availabilities));
    }

    double composite = availabilities.Aggregate(1.0, (current, availability) => current * availability);
    return $"Composite availability: {composite:P3}";
}

using var httpClient = new HttpClient();

var transport = new HttpClientTransport(new()
{
    Endpoint = new Uri("https://learn.microsoft.com/api/mcp"),
    Name = "MicrosoftLearnReliabilityClient",
}, httpClient);

await using var mcpClient = await McpClient.CreateAsync(transport);

var tools = new List<AITool>(await mcpClient.ListToolsAsync().ConfigureAwait(false))
{
    AIFunctionFactory.Create(CalculateCompositeSlo)
};

AIAgent agent = new AzureOpenAIClient(
    new Uri(endpoint),
    new AzureCliCredential())
     .GetChatClient(deploymentName)
     .CreateAIAgent(
        instructions: ReliabilityInstructions,
        name: ReliabilityAgentName,
        tools: tools);

AgentThread thread = agent.GetNewThread();

// Invoke the agent and output the text result.
Console.WriteLine(await agent.RunAsync("""
    We must guarantee at least 99.9% availability for an Azure App Service workload that depends on Azure SQL Database and Azure Storage.
    How resilient is this design and what Azure services or patterns should we add to reach 99.95%?
    """, thread));

Console.WriteLine("-------------------");

await foreach (var update in agent.RunStreamingAsync("""
    Provide reliability safeguards for deploying a new region pair and describe how to handle failover testing cadence.
    """, thread))
{
    Console.Write(update);
}
