// Copyright (c) Microsoft. All rights reserved.

// This sample demonstrates how to use a ChatClientAgent with function tools.
// It shows both non-streaming and streaming agent interactions using menu-related tools.

using System.ComponentModel;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
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
- you will use SLO calculator tool whenever asked about reliability or availability
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

// Create the chat client and agent, and provide the function tool to the agent.
AIAgent agent = new AzureOpenAIClient(
    new Uri(endpoint),
    new AzureCliCredential())
     .GetChatClient(deploymentName)
     .CreateAIAgent(
        instructions: ArchitectInstructions,
        name: ArchitectName,
        tools: [AIFunctionFactory.Create(CalculateCompositeSlo)]);

AgentThread thread = agent.GetNewThread();

// Non-streaming agent interaction with function tools.
Console.WriteLine(await agent.RunAsync("""
    I have service dependencies with availability 0.999, 0.995, and 0.998.
    What is the composite SLO and how can I improve it to reach three nines?
    """, thread));

Console.WriteLine("-------------------");

// Streaming agent interaction with function tools.
await foreach (var update in agent.RunStreamingAsync("""
    I plan to add Azure Front Door in front of App Service, what should I consider for availability and latency trade-offs?
    """, thread))
{
    Console.Write(update);
}
