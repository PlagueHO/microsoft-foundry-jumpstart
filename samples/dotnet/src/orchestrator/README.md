# Microsoft Foundry Jumpstart - Aspire Orchestration

This folder contains .NET Aspire orchestration projects for running the sample applications with shared infrastructure resources.

## Projects

- **AppHost**: The Aspire application host that orchestrates all sample projects and provides shared resources like Azure Cosmos DB
- **ServiceDefaults**: Shared service configuration including OpenTelemetry, health checks, resilience, and service discovery

## Running the Samples

### Prerequisites

1. [.NET 10 SDK](https://dot.net) or later
2. [Docker Desktop](https://www.docker.com/products/docker-desktop) or [Podman](https://podman.io/) for container support
3. Azure OpenAI endpoint configured (for samples that use Azure OpenAI)

### Using Aspire AppHost

The AppHost project provides:

- **Azure Cosmos DB Linux Preview Emulator**: Automatically provisioned for local development
- **OpenTelemetry**: Distributed tracing and metrics collection
- **Health Checks**: Application health monitoring
- **Service Discovery**: Automatic service registration and discovery
- **Aspire Dashboard**: Visual monitoring of all running services

To run all samples with Aspire orchestration:

```bash
cd samples/dotnet/src/orchestrator/AppHost
dotnet run
```

The Aspire Dashboard will open in your browser, showing all running sample projects and the Cosmos DB emulator.

### Environment Variables

When running via Aspire, connection strings are automatically injected. For standalone execution, configure:

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes (for AI samples) |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment name | No (defaults to `gpt-4.1`) |
| `ConnectionStrings__cosmos` | Cosmos DB connection string | Yes (for Cosmos samples when standalone) |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Aspire Dashboard                         │
│                    (Monitoring & Observability)                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                           AppHost                               │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐   │
│  │ Azure Cosmos DB     │  │ Sample Projects                 │   │
│  │ Preview Emulator    │  │ - AzureArchitect_Step01-07     │   │
│  │ (Linux Container)   │  │ - AgentPersistence_Step01-02    │   │
│  │                     │  │ - DocumentClassifierWorkflow    │   │
│  │ Database:           │  │ - HomeLoanAgent                 │   │
│  │ - AgentPersistence  │  │                                 │   │
│  └─────────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                      ServiceDefaults                            │
│  - OpenTelemetry (Tracing + Metrics)                           │
│  - Health Checks (/health, /alive)                              │
│  - HTTP Resilience (retry, circuit breaker)                     │
│  - Service Discovery                                            │
└─────────────────────────────────────────────────────────────────┘
```

## Cosmos DB Emulator

The AppHost uses the **Azure Cosmos DB Linux Preview Emulator**, which provides:

- Full Cosmos DB NoSQL API compatibility
- Data Explorer UI at port 8081
- No Azure subscription required for local development

### Accessing Data Explorer

When running via AppHost, open the Aspire Dashboard and click on the Cosmos DB resource to access the Data Explorer.

### Container Setup

For scenarios requiring hierarchical partition keys:

```csharp
var containerProperties = new ContainerProperties(containerId, "/tenantId")
{
    DefaultTimeToLive = 604800 // 7 days TTL
};
```

## Troubleshooting

### Docker Not Running

Ensure Docker Desktop or Podman is running before starting the AppHost.

### Port Conflicts

If port 8081 is already in use, the emulator will use an alternative port. Check the Aspire Dashboard for the actual endpoint.

### Connection Issues

For Cosmos DB connection issues, verify the emulator container is healthy in the Aspire Dashboard or Docker Desktop.
