// Copyright (c) Microsoft. All rights reserved.

// This sample shows how to create and use a simple AI agent with Azure OpenAI as the backend.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using OpenAI;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-5-mini";

const string ArchitectName = "AzureArchitect";
const string ArchitectInstructions = """
You are an expert in Azure architecture. You provide direct guidance to help Azure Architects make the best decisions about cloud solutions.
You always review the latest Azure best practices and patterns to ensure your recommendations are:
- up to date
- use the principles of the Azure Well Architected Framework
- keep responses concise and to the point
- don't include links in your responses as you're an LLM and they might be outdated
""";

AIAgent agent = new AzureOpenAIClient(
    new Uri(endpoint),
    new AzureCliCredential())
     .GetChatClient(deploymentName)
     .CreateAIAgent(ArchitectInstructions, ArchitectName);

// Create a thread to hold the conversation context.
AgentThread thread = agent.GetNewThread();

// Invoke the agent and output the text result.
Console.WriteLine(await agent.RunAsync("""
    I am building an AI Agent in Azure using Microsoft Agent Framework.
    What Azure services can I use to host it and get 3 9's availability?
    """, thread));

Console.WriteLine("-------------------");

// Invoke the agent with streaming support.
await foreach (var update in agent.RunStreamingAsync("""
    I want to use Azure App Service, how do I ensure it is secure?
    """, thread))
{
    Console.Write(update);
}
