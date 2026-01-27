// Copyright (c) Microsoft. All rights reserved.

// This sample shows how to use an existing prebuilt AI agent from Azure Foundry Agents
// that already has MCP tools connected. It demonstrates using a prebuilt "azure-security-architect"
// agent with multiturn conversation threads to maintain context across interactions.

using Azure.AI.Projects;
using Azure.AI.Projects.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;

string endpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT") ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");

// Name of the existing agent in Azure Foundry (this agent already exists with MCP tools connected)
const string ExistingAgentName = "azure-security-architect";

// Get a client to retrieve/interact with server side agents in Azure Foundry Agents.
AIProjectClient aiProjectClient = new(new Uri(endpoint), new AzureCliCredential());

// Retrieve the existing agent by name - this agent already has MCP tools configured
// Get the list of versions and use the first one (most recent)
var agentVersions = aiProjectClient.Agents.GetAgentVersionsAsync(ExistingAgentName, limit: 1, order: AgentListOrder.Descending);
AgentVersion? agentVersion = null;

await foreach (var version in agentVersions)
{
    agentVersion = version;
    break;
}

if (agentVersion == null)
{
    throw new InvalidOperationException($"Agent '{ExistingAgentName}' not found. Please ensure the agent exists in Azure Foundry.");
}

// Get the AIAgent instance for the prebuilt agent
AIAgent architectAgent = aiProjectClient.GetAIAgent(agentVersion);

Console.WriteLine($"Successfully retrieved existing agent: {ExistingAgentName}");
Console.WriteLine($"Agent ID: {agentVersion.Id}");
Console.WriteLine($"Agent version: {agentVersion.Version}\n");
Console.WriteLine("-------------------\n");

// Create a new thread to maintain conversation context across multiple interactions
AgentThread thread = architectAgent.GetNewThread();

// First question in the conversation - leveraging the prebuilt agent with MCP tools
Console.WriteLine("Question 1: What are the best practices for securing an Azure App Service deployment with network isolation?\n");
await foreach (AgentRunResponseUpdate update in architectAgent.RunStreamingAsync("What are the best practices for securing an Azure App Service deployment with network isolation?", thread))
{
    Console.Write(update);
}

Console.WriteLine("\n\n-------------------\n");

// Second question - this will have context from the first question because we're using the same thread
Console.WriteLine("Question 2: How do I implement private endpoints for this setup?\n");
await foreach (AgentRunResponseUpdate update in architectAgent.RunStreamingAsync("How do I implement private endpoints for this setup?", thread))
{
    Console.Write(update);
}

Console.WriteLine("\n\n-------------------\n");

// Third question - demonstrating continued context and leveraging MCP tools
Console.WriteLine("Question 3: Can you help me understand the compliance requirements for healthcare data in Azure?\n");
await foreach (AgentRunResponseUpdate update in architectAgent.RunStreamingAsync("Can you help me understand the compliance requirements for healthcare data in Azure?", thread))
{
    Console.Write(update);
}

Console.WriteLine("\n");

// Note: We don't delete the agent since it's a prebuilt/shared agent
// Only delete agents that you created specifically for this session
