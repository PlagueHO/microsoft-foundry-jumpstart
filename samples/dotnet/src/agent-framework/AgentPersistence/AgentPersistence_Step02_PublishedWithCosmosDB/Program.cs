// Copyright (c) Microsoft. All rights reserved.

// This sample demonstrates the client-side persistence pattern required for published Agent Applications.
// Published applications only have access to the stateless /responses endpoint, so conversation
// history must be managed by the client.
//
// This sample uses CosmosChatMessageStore from Microsoft.Agents.AI.CosmosNoSql for persistence.
// It demonstrates hierarchical partitioning for multi-tenant SaaS scenarios.
//
// When run via Aspire AppHost, Cosmos DB connection is automatically injected.
// When run standalone, configure via environment variables.

using System.Text.Json;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace AgentPersistence.PublishedWithCosmosDB;

/// <summary>
/// Demonstrates published Agent Application usage with Cosmos DB persistence.
/// </summary>
/// <remarks>
/// <para>
/// Published Agent Applications have LIMITED API access:
/// - POST /conversations - INACCESSIBLE
/// - GET /conversations/{id}/messages - INACCESSIBLE
/// - POST /files - INACCESSIBLE
/// - POST /vector_stores - INACCESSIBLE
/// - POST /responses (store=false) - Only available endpoint
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

        // Build the host with Aspire service defaults
        var builder = Host.CreateApplicationBuilder(args);

        // Add Aspire service defaults (OpenTelemetry, health checks, service discovery)
        builder.AddServiceDefaults();

        // Add Azure Cosmos DB client - Aspire will inject the connection string
        // from the AppHost when running under orchestration, or falls back to
        // ConnectionStrings:cosmos configuration or AZURE_COSMOS_ENDPOINT env var
        builder.AddAzureCosmosClient("cosmos");

        // Build the host
        using var host = builder.Build();

        // Get configuration
        var configuration = host.Services.GetRequiredService<IConfiguration>();

        // Get Cosmos client from DI (injected by Aspire or configured manually)
        var cosmosClient = host.Services.GetRequiredService<CosmosClient>();

        // Get configuration values (Aspire-injected or environment variables)
        string openAiEndpoint = configuration["AZURE_OPENAI_ENDPOINT"]
            ?? Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT")
            ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
        string deploymentName = configuration["AZURE_OPENAI_DEPLOYMENT_NAME"]
            ?? Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME")
            ?? "gpt-4.1";
        string cosmosDatabaseId = configuration["AZURE_COSMOS_DATABASE_ID"]
            ?? Environment.GetEnvironmentVariable("AZURE_COSMOS_DATABASE_ID")
            ?? "AgentPersistence";
        string cosmosContainerId = configuration["AZURE_COSMOS_CONTAINER_ID"]
            ?? Environment.GetEnvironmentVariable("AZURE_COSMOS_CONTAINER_ID")
            ?? "ChatMessages";

        Console.WriteLine($"OpenAI Endpoint: {openAiEndpoint}");
        Console.WriteLine($"Model: {deploymentName}");
        Console.WriteLine($"Cosmos DB Endpoint: {cosmosClient.Endpoint}");
        Console.WriteLine($"Database: {cosmosDatabaseId}, Container: {cosmosContainerId}\n");

        // Create Azure credential (uses DefaultAzureCredential for flexibility)
        var credential = new DefaultAzureCredential();

        // Multi-tenant identifiers - in production, these come from your auth/session system
        string tenantId = configuration["TENANT_ID"]
            ?? Environment.GetEnvironmentVariable("TENANT_ID")
            ?? "contoso";
        string userId = configuration["USER_ID"]
            ?? Environment.GetEnvironmentVariable("USER_ID")
            ?? "user-123";
        string sessionId = configuration["SESSION_ID"]
            ?? Environment.GetEnvironmentVariable("SESSION_ID")
            ?? Guid.NewGuid().ToString("N");

        Console.WriteLine($"Tenant: {tenantId}");
        Console.WriteLine($"User: {userId}");
        Console.WriteLine($"Session: {sessionId}\n");

        // Ensure database and container exist (for emulator scenarios)
        await EnsureDatabaseAndContainerAsync(cosmosClient, cosmosDatabaseId, cosmosContainerId);

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
                // Using the CosmosClient from DI (Aspire-provided or manually configured)
                // This enables efficient multi-tenant data isolation:
                // - Partition key: /tenantId/userId/sessionId
                // - Each tenant's data is isolated at the storage level
                // - Queries are scoped to the specific tenant/user/session
                var store = new CosmosChatMessageStore(
                    cosmosClient,
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
        Console.WriteLine("Serialized thread state (for session resume):");
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

        Console.WriteLine("\n=== Aspire Integration ===\n");
        Console.WriteLine("""
            This sample integrates with .NET Aspire for:

            - Automatic Cosmos DB Linux Preview Emulator provisioning
            - Connection string injection via IConfiguration
            - OpenTelemetry tracing and metrics
            - Health check endpoints
            - Service discovery

            Run via AppHost:
              cd samples/dotnet/src/orchestrator/AppHost
              dotnet run

            Or run standalone with environment variables:
              export AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
              export ConnectionStrings__cosmos=AccountEndpoint=https://your-cosmos.documents.azure.com:443/;AccountKey=...
              dotnet run
            """);
    }

    /// <summary>
    /// Ensures the database and container exist in Cosmos DB.
    /// This is useful for emulator scenarios where the resources may not exist.
    /// </summary>
    private static async Task EnsureDatabaseAndContainerAsync(
        CosmosClient cosmosClient,
        string databaseId,
        string containerId)
    {
        Console.WriteLine("Ensuring Cosmos DB database and container exist...");

        // Create database if it doesn't exist
        var databaseResponse = await cosmosClient.CreateDatabaseIfNotExistsAsync(databaseId);
        Console.WriteLine($"Database '{databaseId}' ready (Status: {databaseResponse.StatusCode})");

        // Create container with partition key
        // Note: The emulator may have limitations with hierarchical partition keys
        // For production, ensure your container is created with the proper partition key paths
        var containerProperties = new ContainerProperties(containerId, "/tenantId")
        {
            DefaultTimeToLive = 604800 // 7 days TTL
        };

        var containerResponse = await databaseResponse.Database.CreateContainerIfNotExistsAsync(containerProperties);
        Console.WriteLine($"Container '{containerId}' ready (Status: {containerResponse.StatusCode})\n");
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
