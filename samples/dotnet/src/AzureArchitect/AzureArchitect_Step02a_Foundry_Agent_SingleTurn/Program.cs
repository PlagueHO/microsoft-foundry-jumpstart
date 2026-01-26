// Copyright (c) Microsoft. All rights reserved.

// This sample shows how to create and use a simple AI agent with Azure Foundry Agents as the backend.

using Azure.AI.Projects;
using Azure.AI.Projects.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;

string endpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT") ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
string deploymentName = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME") ?? "gpt-4o-mini";

// Create a unique agent name using a timestamp to avoid naming conflicts
string iso9660Timestamp = DateTime.UtcNow.ToString("yyyyMMdd'T'HHmmss'Z'");
string ArchitectName = $"azure-architect-{iso9660Timestamp}";

// Define the instructions for the Azure Architect agent
const string ArchitectInstructions = """
You are an expert in Azure architecture. You provide direct guidance to help Azure Architects make the best decisions about cloud solutions.
You always review the latest Azure best practices and patterns to ensure your recommendations are:
- up to date
- use the principles of the Azure Well Architected Framework
- keep responses concise and to the point
""";

// Get a client to create/retrieve/delete server side agents with Azure Foundry Agents.
AIProjectClient aiProjectClient = new(new Uri(endpoint), new AzureCliCredential());

// Define the agent you want to create. (Prompt Agent in this case)
AgentVersionCreationOptions options = new(new PromptAgentDefinition(model: deploymentName) {
    Instructions = ArchitectInstructions
    });

// Azure.AI.Agents SDK creates and manages agent by name and versions.
// You can create a server side agent version with the Azure.AI.Agents SDK client below.
AgentVersion agentVersion = aiProjectClient.Agents.CreateAgentVersion(agentName: ArchitectName, options);

// You can retrieve an AIAgent for a already created server side agent version.
AIAgent architectAgent = aiProjectClient.GetAIAgent(agentVersion);

// Invoke the agent with streaming support.
Console.WriteLine("Question: I am building an AI agent in Azure using Microsoft Agent Framework. What Azure services can I use to host it and get 3 9's availability?\n");
await foreach (AgentRunResponseUpdate update in architectAgent.RunStreamingAsync("I am building an AI agent in Azure using Microsoft Agent Framework. What Azure services can I use to host it and get 3 9's availability?"))
{
    Console.Write(update);
}

Console.WriteLine("\n\n-------------------\n");

Console.WriteLine("Question: I want to use Azure App Service, how do I ensure it is secure?\n");
await foreach (AgentRunResponseUpdate update in architectAgent.RunStreamingAsync("I want to use Azure App Service, how do I ensure it is secure?"))
{
    Console.Write(update);
}

Console.WriteLine("\n");

// Cleanup by agent name removes the agent version created.
// await aiProjectClient.Agents.DeleteAgentAsync(architectAgent.Name);
