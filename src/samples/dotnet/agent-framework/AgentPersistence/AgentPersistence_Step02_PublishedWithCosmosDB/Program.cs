// Copyright (c) Microsoft. All rights reserved.

// This sample demonstrates the client-side persistence pattern required for published Agent Applications.
// Published applications only have access to the stateless /responses endpoint, so conversation
// history must be managed by the client.
//
// This sample uses CosmosChatMessageStore from Microsoft.Agents.AI.CosmosNoSql for persistence.
// It demonstrates hierarchical partitioning for multi-tenant SaaS scenarios.

using System.Text.Json;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;

namespace AgentPersistence.PublishedWithCosmosDB;

/// <summary>
/// Demonstrates published Agent Application usage with Cosmos DB persistence.
/// </summary>
/// <remarks>
/// <para>
/// Published Agent Applications have LIMITED API access:
/// - ❌ POST /conversations - INACCESSIBLE
/// - ❌ GET /conversations/{id}/messages - INACCESSIBLE
/// - ❌ POST /files - INACCESSIBLE
/// - ❌ POST /vector_stores - INACCESSIBLE
/// - ✅ POST /responses (store=false) - Only available endpoint
/// </para>
/// <para>
/// This design is intentional for user data isolation. The client must manage:
/// - Conversation history storage
/// - Message retrieval for context
/// - User/tenant data separation
/// </para>
/// <para>
/// This sample uses CosmosChatMessageStore with hierarchical partitioning:
/// - Partition key: /tenantId, /userId, /sessionId
/// - Enables efficient multi-tenant data isolation
/// - Supports session resumption across application restarts
/// </para>
/// </remarks>
internal static class Program
{
    private const string AgentName = "PersistentAssistant";
    private const string AgentInstructions = """
        You are a helpful AI assistant that demonstrates conversation persistence.
        You remember all previous messages in the conversation and can reference them.
        Keep your responses concise and helpful.
        When asked about previous topics, summarize what was discussed.
        """;

    public static async Task Main(string[] args)
    {
        Console.WriteLine("=== Published Agent with Cosmos DB Persistence ===\n");

        // Get configuration from environment
        string openAiEndpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT")
            ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
        string deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME")
            ?? "gpt-4.1";
        string cosmosEndpoint = Environment.GetEnvironmentVariable("AZURE_COSMOS_ENDPOINT")
            ?? throw new InvalidOperationException("AZURE_COSMOS_ENDPOINT is not set.");
        string cosmosDatabaseId = Environment.GetEnvironmentVariable("AZURE_COSMOS_DATABASE_ID")
            ?? "AgentPersistence";
        string cosmosContainerId = Environment.GetEnvironmentVariable("AZURE_COSMOS_CONTAINER_ID")
            ?? "ChatMessages";

        Console.WriteLine($"OpenAI Endpoint: {openAiEndpoint}");
        Console.WriteLine($"Model: {deploymentName}");
        Console.WriteLine($"Cosmos DB: {cosmosEndpoint}");
        Console.WriteLine($"Database: {cosmosDatabaseId}, Container: {cosmosContainerId}\n");

        // Create Azure credential (uses DefaultAzureCredential for flexibility)
        var credential = new DefaultAzureCredential();

        // Multi-tenant identifiers - in production, these come from your auth/session system
        string tenantId = Environment.GetEnvironmentVariable("TENANT_ID") ?? "contoso";
        string userId = Environment.GetEnvironmentVariable("USER_ID") ?? "user-123";
        string sessionId = Environment.GetEnvironmentVariable("SESSION_ID") ?? Guid.NewGuid().ToString("N");

        Console.WriteLine($"Tenant: {tenantId}");
        Console.WriteLine($"User: {userId}");
        Console.WriteLine($"Session: {sessionId}\n");

        // Create the Azure OpenAI client and convert to IChatClient
        var chatClient = new AzureOpenAIClient(new Uri(openAiEndpoint), credential)
            .GetChatClient(deploymentName)
            .AsIChatClient();

        // Create the AI Agent with Cosmos DB persistence using hierarchical partitioning
        // The ChatMessageStoreFactory creates a new CosmosChatMessageStore for each thread
        AIAgent agent = chatClient.AsAIAgent(new ChatClientAgentOptions
        {
            Name = AgentName,
            ChatOptions = new() { Instructions = AgentInstructions },
            ChatMessageStoreFactory = (context, cancellationToken) =>
            {
                // Create Cosmos DB message store with hierarchical partitioning
                // This enables efficient multi-tenant data isolation:
                // - Partition key: /tenantId/userId/sessionId
                // - Each tenant's data is isolated at the storage level
                // - Queries are scoped to the specific tenant/user/session
                var store = new CosmosChatMessageStore(
                    cosmosEndpoint,
                    credential,
                    cosmosDatabaseId,
                    cosmosContainerId,
                    tenantId,
                    userId,
                    sessionId)
                {
                    // Configure optional settings
                    MessageTtlSeconds = 86400 * 7, // 7 days TTL for messages
                    MaxMessagesToRetrieve = 50     // Limit context window
                };

                return new ValueTask<ChatMessageStore>(store);
            }
        });

        // Create a thread for this conversation
        AgentThread thread = await agent.GetNewThreadAsync();

        Console.WriteLine("=== Conversation Demo ===\n");
        Console.WriteLine("Messages are persisted to Cosmos DB with hierarchical partitioning.\n");

        await AskQuestionAsync(agent, thread, "Hello! My name is Jordan and I'm building a chat application.");
        await AskQuestionAsync(agent, thread, "What are some best practices for conversation persistence?");
        await AskQuestionAsync(agent, thread, "Can you remind me what my name is and what I'm building?");

        // The third question demonstrates context retention - the agent retrieves
        // conversation history from Cosmos DB to maintain context

        // Demonstrate session serialization for resume capability
        Console.WriteLine("\n=== Session Serialization Demo ===\n");
        JsonElement serializedThread = thread.Serialize();
        Console.WriteLine($"Serialized thread state (for session resume):");
        Console.WriteLine($"{serializedThread}\n");

        Console.WriteLine("To resume this session later, deserialize the thread:");
        Console.WriteLine("  AgentThread resumed = await agent.DeserializeThreadAsync(serializedState);\n");

        Console.WriteLine("=== Architecture Benefits ===\n");
        Console.WriteLine("""
            Hierarchical Partitioning Benefits:

            1. Data Isolation:
               - Partition key: /tenantId/userId/sessionId
               - Tenant data is physically isolated at storage level
               - No cross-tenant data leakage possible

            2. Query Efficiency:
               - Queries scoped to partition are fast and cheap
               - No cross-partition fan-out for normal operations

            3. GDPR Compliance:
               - Delete all user data with single partition delete
               - TTL auto-expires old messages

            4. Scalability:
               - Each partition scales independently
               - Hot tenants don't affect others

            5. Session Resume:
               - Serialize thread state for client storage
               - Deserialize to resume with full history from Cosmos DB
            """);

        Console.WriteLine("\n=== Cosmos DB Container Setup ===\n");
        Console.WriteLine("""
            To create the container with hierarchical partition key:

            az cosmosdb sql container create \
              --account-name <cosmos-account> \
              --database-name AgentPersistence \
              --name ChatMessages \
              --partition-key-path "/tenantId" "/userId" "/sessionId" \
              --default-ttl 604800

            Or via Bicep/ARM with ContainerProperties:
              partitionKeyPaths: ['/tenantId', '/userId', '/sessionId']
              defaultTtl: 604800
            """);
    }

    private static async Task AskQuestionAsync(AIAgent agent, AgentThread thread, string question)
    {
        Console.WriteLine($"User: {question}\n");
        Console.Write("Assistant: ");

        await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(question, thread))
        {
            Console.Write(update);
        }

        Console.WriteLine("\n");
        Console.WriteLine(new string('-', 60));
        Console.WriteLine();
    }
}
