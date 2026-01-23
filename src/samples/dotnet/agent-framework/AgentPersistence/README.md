# Agent Persistence Patterns Demo

This demo showcases two different approaches to implementing persistent AI agents with Microsoft Foundry, addressing the key architectural differences between unpublished (project-level) agents and published Agent Applications.

## Background

When working with Microsoft Foundry agents, there's a critical distinction between:

1. **Unpublished Agents (Project-Level)**: Access to full OpenAI-compatible API including `/conversations`, `/files`, `/vector_stores` endpoints with server-side persistence
2. **Published Agent Applications**: Limited to stateless `/responses` endpoint only, requiring **client-side persistence**

This limitation in published applications is by design for **user data isolation** - ensuring published applications don't mix user data in shared server-side storage.

## Prerequisites

Before you begin, ensure you have the following:

- .NET 9.0 SDK or later
- Microsoft Foundry service endpoint, project, and GPT 4.1 deployment configured
- Azure CLI installed and authenticated (`az login`)
- Azure Cosmos DB account (for the published agent sample)

## Environment Variables

Set the following environment variables:

```powershell
# Required for both samples
$env:AZURE_FOUNDRY_PROJECT_ENDPOINT = "<Your Microsoft Foundry Project Endpoint>"
$env:AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME = "<GPT 4.1 model deployed to Microsoft Foundry Project>"

# Required for Published Agent sample (Step 2)
$env:AZURE_COSMOSDB_ENDPOINT = "<Your Cosmos DB Account Endpoint>"
$env:AZURE_COSMOSDB_DATABASE_ID = "agent-persistence"
$env:AZURE_COSMOSDB_CONTAINER_ID = "conversations"

# Optional - for Published Agent Application endpoint
$env:AZURE_FOUNDRY_APPLICATION_ENDPOINT = "<Your Published Agent Application Endpoint>"
```

## Demo Structure

| Sample | Description |
|--------|-------------|
| [Step 1: Unpublished Agent with Server-Side Persistence](./AgentPersistence_Step01_UnpublishedAgent/) | Uses project-level APIs with full `/conversations`, `/files`, `/vector_stores` access. Messages are stored server-side automatically. |
| [Step 2: Published Agent with Cosmos DB Persistence](./AgentPersistence_Step02_PublishedWithCosmosDB/) | Uses `CosmosChatMessageStore` from Agent Framework SDK for client-side persistence. Works with stateless `/responses` endpoint. |

## Key Concepts

### Unpublished Agent (Step 1)

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│           ┌─────────────────────────────────────────────────┐│
│           │         AIProjectClient                          ││
│           │  - CreateAgentVersion()                          ││
│           │  - GetAIAgent()                                  ││
│           │  - GetNewThread() ← Thread stored server-side    ││
│           └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         Microsoft Foundry Project (Full API Access)          │
│  ✅ POST /conversations                                      │
│  ✅ GET /conversations/{id}/messages                         │
│  ✅ POST /files                                              │
│  ✅ POST /vector_stores                                      │
│  ✅ POST /responses                                          │
└─────────────────────────────────────────────────────────────┘
```

### Published Agent (Step 2)

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         CosmosChatMessageStore                        │   │
│  │  - Stores messages in Cosmos DB                       │   │
│  │  - Retrieves history on each request                  │   │
│  │  - Supports hierarchical partitioning                 │   │
│  └───────────────────────────┬──────────────────────────┘   │
│                              │                               │
│  ┌───────────────────────────▼──────────────────────────┐   │
│  │           Azure OpenAI Client with                    │   │
│  │           ChatMessageStoreFactory                     │   │
│  └───────────────────────────┬──────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│     Published Agent Application (Limited API Access)        │
│  ❌ /conversations - INACCESSIBLE                           │
│  ❌ /files - INACCESSIBLE                                   │
│  ❌ /vector_stores - INACCESSIBLE                           │
│  ✅ POST /responses (store=false, stateless)                │
└─────────────────────────────────────────────────────────────┘
```

## Cosmos DB Setup

For Step 2, you need to create a Cosmos DB container with the following configuration:

```bash
# Create database and container using Azure CLI
az cosmosdb sql database create \
  --account-name <your-cosmos-account> \
  --resource-group <your-resource-group> \
  --name agent-persistence

az cosmosdb sql container create \
  --account-name <your-cosmos-account> \
  --resource-group <your-resource-group> \
  --database-name agent-persistence \
  --name conversations \
  --partition-key-path /conversationId \
  --default-ttl 86400
```

For hierarchical partitioning (multi-tenant scenarios):

```bash
az cosmosdb sql container create \
  --account-name <your-cosmos-account> \
  --resource-group <your-resource-group> \
  --database-name agent-persistence \
  --name conversations \
  --partition-key-path "/tenantId,/userId,/conversationId" \
  --hierarchical-partition-keys true \
  --default-ttl 86400
```

## Running the Samples

```powershell
# Run Step 1 - Unpublished Agent
cd AgentPersistence_Step01_UnpublishedAgent
dotnet run

# Run Step 2 - Published Agent with Cosmos DB
cd AgentPersistence_Step02_PublishedWithCosmosDB
dotnet run
```

## When to Use Each Approach

| Scenario | Recommended Approach |
|----------|---------------------|
| Development/Testing | Unpublished Agent (simpler setup) |
| Single-tenant production | Either (based on security requirements) |
| Multi-tenant production | Published Agent + Cosmos DB |
| Strict user data isolation | Published Agent + Cosmos DB |
| Serverless/stateless APIs | Published Agent + Cosmos DB |
| Rapid prototyping | Unpublished Agent |

## Additional Resources

- [Microsoft Foundry Agent Applications Documentation](https://learn.microsoft.com/azure/ai-services/agents/concepts/agent-applications)
- [Agent Framework SDK GitHub](https://github.com/microsoft/agent-framework)
- [CosmosChatMessageStore Reference](https://github.com/microsoft/agent-framework/tree/main/dotnet/src/Microsoft.Agents.AI.CosmosNoSql)
