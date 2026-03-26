# Cross-Region Web App with Foundry Agent Service

## Overview

This pattern deploys a **cross-region architecture** that demonstrates how a VNet
and consuming application can reside in a different Azure region from the
Microsoft Foundry resource, connected securely via cross-region private endpoints.

### Problem Solved

- **Foundry region availability**: Foundry (East US 2) may have models or capacity
  not available in your application's region (Australia East).
- **Compliance**: Application and networking infrastructure must reside in a
  specific region (e.g., APAC) while consuming AI services from another.
- **Secure connectivity**: All traffic flows over the Microsoft backbone via
  private endpoints — no public internet exposure.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│ EAST US 2 (Foundry Region)                              │
│                                                         │
│  AI Foundry Account (AIServices)                        │
│   ├─ Models: gpt-4o                                     │
│   ├─ Project: agent-project                             │
│   ├─ Capability Host: Agent Service                     │
│   └─ Connections: Cosmos DB, Storage, AI Search         │
│                                                         │
│  BYO Resources                                          │
│   ├─ Cosmos DB (serverless, agent threads)              │
│   ├─ Storage Account (blob, agent files)                │
│   └─ AI Search (semantic search, vectors)               │
│                                                         │
│  All resources: public network access = Disabled        │
└────────────────────────┬────────────────────────────────┘
                         │ Cross-region private endpoints
                         │ (Azure backbone, no internet)
                         ▼
┌─────────────────────────────────────────────────────────┐
│ AUSTRALIA EAST (Application Region)                     │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │ Virtual Network (10.0.0.0/16)                │       │
│  │  ├─ PrivateEndpoints (10.0.1.0/24)           │       │
│  │  │  ├─ PE: AI Foundry (cross-region)         │       │
│  │  │  ├─ PE: Cosmos DB (cross-region)          │       │
│  │  │  ├─ PE: Storage (cross-region)            │       │
│  │  │  ├─ PE: AI Search (cross-region)          │       │
│  │  │  └─ PE: Web App (inbound)                 │       │
│  │  └─ WebAppIntegration (10.0.2.0/24)          │       │
│  │     └─ Web App VNet integration (outbound)   │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  App Service Plan (P1v3, Linux)                         │
│   └─ Web App (.NET 10 Razor Pages)                      │
│      ├─ Uses managed identity (DefaultAzureCredential)  │
│      ├─ Calls Foundry Agent Service via PE              │
│      └─ Public access disabled                          │
│                                                         │
│  Private DNS Zones (linked to VNet)                     │
│   ├─ privatelink.cognitiveservices.azure.com            │
│   ├─ privatelink.openai.azure.com                       │
│   ├─ privatelink.services.ai.azure.com                  │
│   ├─ privatelink.search.windows.net                     │
│   ├─ privatelink.documents.azure.com                    │
│   ├─ privatelink.blob.core.windows.net                  │
│   └─ privatelink.azurewebsites.net                      │
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Cross-region private endpoints are supported by Azure Private Link** — the
   private endpoint must be in the same region as the VNet, but the target
   resource (Foundry, Storage, etc.) can be in any region.
2. **All private DNS zones are in the VNet resource group** (Australia East) and
   linked to the VNet so the Web App resolves Foundry endpoints to private IPs.
3. **Web App uses VNet integration** for outbound traffic so all calls to Foundry
   route through the VNet and hit the private endpoints.
4. **Web App uses a private endpoint** for inbound traffic — it is not publicly
   accessible.
5. **Managed identity** is used for authentication — no API keys or secrets.

## When to Use This Pattern

✅ **Use this pattern if you need:**

- Application infrastructure in a region different from your Foundry resource
- Cross-region private endpoint connectivity to AI services
- A Web App front-end that calls Foundry Agent Service securely
- Zero-trust networking with no public internet exposure

❌ **Don't use this pattern if:**

- Foundry and your application can be co-located in the same region
- You don't require network isolation
- Low latency is critical (cross-region adds ~150-200ms RTT)

## Deployment

### Prerequisites

- Azure CLI with Bicep support
- Azure subscription with quota in East US 2 and Australia East
- Appropriate RBAC roles (Contributor)
- .NET 10 SDK (for building the Web App)

### Deploy Infrastructure

```bash
cd architectures/pattern-cross-region-webapp/
az deployment sub create \
  --location australiaeast \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --parameters environmentName=crw principalId=<your-principal-id>
```

### Build and Deploy the Web App

```bash
cd app/
dotnet publish -c Release -o ./publish
az webapp deploy \
  --resource-group rg-crw-webapp \
  --name app-crw \
  --src-path ./publish \
  --type zip
```

### Customization

```bash
# Use different regions
--parameters foundryLocation=swedencentral vnetLocation=eastasia

# Use a smaller App Service Plan (note: P1v3+ required for VNet integration)
--parameters appServicePlanSku=P1v3

# Disable model deployment
--parameters deployModels=false
```

## .NET 10 Web App

The `app/` directory contains a simple .NET 10 Razor Pages application that:

1. Uses `Azure.AI.Projects` SDK to connect to the Foundry project endpoint
2. Creates a Prompt Agent via the Microsoft Agent Framework
3. Streams the agent's response back to the user
4. Authenticates using `DefaultAzureCredential` (managed identity in Azure)

### Local Development

Set the `AZURE_FOUNDRY_PROJECT_ENDPOINT` environment variable in
`Properties/launchSettings.json` to your Foundry project endpoint, then:

```bash
cd app/
dotnet run
```

## Cost Considerations

- **Cross-region data transfer**: Calls from Australia East to East US 2 incur
  cross-region egress charges (but stay on the Microsoft backbone).
- **Latency**: ~150-200ms round trip between Australia East and East US 2.
  Acceptable for agent interactions but not ideal for high-throughput scenarios.
- **App Service Plan**: P1v3 required for VNet integration (~$140/month).
- **AI Search, Cosmos DB, Storage**: Standard pricing applies in East US 2.

## Limitations

- Cross-region latency affects agent response time.
- Agent Service VNet injection (outbound) is **not** cross-region — this pattern
  uses cross-region private endpoints for inbound connectivity only.
- The Web App must be accessed via the private endpoint or a VPN/ExpressRoute
  connection to the Australia East VNet.
- BYO resources (Cosmos DB, Storage, AI Search) are co-located with Foundry in
  East US 2 to avoid additional cross-region hops for Agent Service.

## Resources Deployed

| Resource | Region | Purpose |
|----------|--------|---------|
| AI Foundry Account (AIServices) | East US 2 | Models, Agent Service, projects |
| Cosmos DB (serverless) | East US 2 | Agent thread storage |
| Storage Account (blob) | East US 2 | Agent file storage |
| AI Search (standard) | East US 2 | Vector store, semantic search |
| Virtual Network | Australia East | Network backbone |
| Private DNS Zones (7) | Global | DNS resolution for private endpoints |
| App Service Plan (P1v3) | Australia East | Web App hosting |
| Web App (.NET 10) | Australia East | Razor Pages calling Agent Service |
| Log Analytics Workspace | East US 2 | Centralized monitoring |

**Estimated cost**: ~$500-$800/month (depends on model throughput and search volume).
