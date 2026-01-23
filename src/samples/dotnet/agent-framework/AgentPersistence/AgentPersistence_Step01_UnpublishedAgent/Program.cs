// Copyright (c) Microsoft. All rights reserved.

// This sample demonstrates using an unpublished (project-level) agent with full API access
// to /conversations, /files, and /vector_stores endpoints. The server manages persistence.

using Azure.AI.Projects;
using Azure.AI.Projects.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;

namespace AgentPersistence.UnpublishedAgent;

/// <summary>
/// Demonstrates unpublished agent usage with server-side persistence.
/// </summary>
/// <remarks>
/// Unpublished agents have full access to:
/// - POST /conversations - Create conversation threads
/// - GET /conversations/{id}/messages - Retrieve message history
/// - POST /files - Upload files for processing
/// - POST /vector_stores - Create and manage vector stores
/// - POST /responses - Generate responses
///
/// This is the simpler approach when user data isolation is not required.
/// </remarks>
internal static class Program
{
    private const string AgentInstructions = """
        You are a helpful AI assistant that demonstrates conversation persistence.
        You remember all previous messages in the conversation and can reference them.
        Keep your responses concise and helpful.
        When asked about previous topics, summarize what was discussed.
        """;

    public static async Task Main(string[] args)
    {
        Console.WriteLine("=== Unpublished Agent with Server-Side Persistence ===\n");

        // Get configuration from environment
        string endpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT")
            ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
        string deploymentName = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME")
            ?? "gpt-4.1";

        // Create a unique agent name using a timestamp to avoid naming conflicts
        string timestamp = DateTime.UtcNow.ToString("yyyyMMdd'T'HHmmss'Z'");
        string agentName = $"persistence-demo-{timestamp}";

        Console.WriteLine($"Agent Name: {agentName}");
        Console.WriteLine($"Endpoint: {endpoint}");
        Console.WriteLine($"Model: {deploymentName}\n");

        // Create the AI Project Client using Azure CLI credentials
        AIProjectClient aiProjectClient = new(new Uri(endpoint), new AzureCliCredential());

        // Define the agent with instructions
        var options = new AgentVersionCreationOptions(new PromptAgentDefinition(model: deploymentName)
        {
            Instructions = AgentInstructions
        });

        // Create the server-side agent version
        Console.WriteLine("Creating server-side agent...");
        AgentVersion agentVersion = await aiProjectClient.Agents.CreateAgentVersionAsync(agentName: agentName, options);
        Console.WriteLine($"Agent created with version: {agentVersion.Name}\n");

        // Get an AIAgent instance for the created agent
        AIAgent agent = aiProjectClient.GetAIAgent(agentVersion);

        // Create a new thread - this is stored SERVER-SIDE
        // The thread can be used to continue the conversation later
        AgentThread thread = agent.GetNewThread();
        Console.WriteLine("Created server-side thread for conversation persistence.\n");

        // Simulate a multi-turn conversation
        await RunConversationAsync(agent, thread);

        // Demonstrate retrieving the same thread later (simulating app restart)
        Console.WriteLine("\n--- Simulating Application Restart ---\n");
        Console.WriteLine("In a real application, you would store the thread reference and reuse it.");
        Console.WriteLine("The thread maintains conversation state across multiple interactions.\n");

        // Continue the conversation on the same thread
        await ContinueConversationAsync(agent, thread);

        // Cleanup
        Console.WriteLine("\n--- Cleanup ---");
        Console.WriteLine("Deleting agent...");
        await aiProjectClient.Agents.DeleteAgentAsync(agentName);
        Console.WriteLine("Agent deleted successfully.");
    }

    private static async Task RunConversationAsync(AIAgent agent, AgentThread thread)
    {
        Console.WriteLine("=== Starting Multi-Turn Conversation ===\n");

        // First turn
        await AskQuestionAsync(agent, thread, "Hello! My name is Alex and I'm interested in learning about Azure architecture.");

        // Second turn - agent should remember the name
        await AskQuestionAsync(agent, thread, "What are the key pillars of the Azure Well-Architected Framework?");

        // Third turn - agent should remember both previous turns
        await AskQuestionAsync(agent, thread, "Which pillar do you think is most important for my learning journey?");
    }

    private static async Task ContinueConversationAsync(AIAgent agent, AgentThread thread)
    {
        Console.WriteLine("=== Continuing Conversation (Same Thread) ===\n");

        // Fourth turn - should remember Alex's name and previous discussion
        await AskQuestionAsync(agent, thread, "Can you remind me what my name is and summarize what we discussed?");
    }

    private static async Task AskQuestionAsync(AIAgent agent, AgentThread thread, string question)
    {
        Console.WriteLine($"User: {question}\n");
        Console.Write("Assistant: ");

        await foreach (AgentRunResponseUpdate update in agent.RunStreamingAsync(question, thread))
        {
            Console.Write(update);
        }

        Console.WriteLine("\n");
        Console.WriteLine(new string('-', 60));
        Console.WriteLine();
    }
}
