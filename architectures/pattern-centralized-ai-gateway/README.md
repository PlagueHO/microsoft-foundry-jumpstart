# Centralized AI Gateway Architecture Pattern

## Overview

This pattern deploys a **centralized AI gateway architecture** with multiple Foundry accounts (departments) sharing BYO resources and a single API Management instance acting as an AI Gateway for model routing, governance, and cross-region model access.

### Problem Solved

- **Multi-department isolation**: Each department gets its own Foundry account and project while sharing underlying data infrastructure
- **Centralized AI governance**: API Management acts as a single point of control for all model access, enabling rate limiting, logging, and policy enforcement
- **Data sovereignty**: All BYO resources (Cosmos DB, AI Search, Storage) remain in the primary region
- **Model availability**: Models not available in the primary region are accessed via APIM routing to a models-region Foundry resource
- **Zero-trust networking**: All resources communicate over private endpoints within a VNet

### Capability Host Sharing Research

**Key finding**: Multiple Foundry accounts **cannot share a single Capability Host**. Each Foundry account requires its own capability host (one active capability host per scope). However, multiple Foundry accounts **can share the same underlying Azure resources** (Cosmos DB, AI Search, Storage Account). Each Foundry account creates its own connections pointing to the shared resources, and its own capability host referencing those connections.

This means:

- Foundry Account 1 has: connections -> shared Cosmos DB/Search/Storage -> capability host referencing those connections
- Foundry Account 2 has: connections -> **same** shared Cosmos DB/Search/Storage -> capability host referencing those connections

The capability hosts are separate sub-resources, but they point to the same physical data stores.

## Architecture Components

### Primary Region (Australia East)

#### Shared Infrastructure

- **Virtual Network** (10.0.0.0/16) with dedicated subnets:
  - `AiServices` (10.0.1.0/24) - Private endpoints for Foundry accounts
  - `CapabilityHosts` (10.0.2.0/24) - Private endpoints for Cosmos DB, Search, Storage
  - `ModelsRegion` (10.0.3.0/24) - Cross-region private endpoint to models region
  - `AgentSubnet1` (10.0.4.0/24) - Delegated for Department 1 Agent Service
  - `AgentSubnet2` (10.0.5.0/24) - Delegated for Department 2 Agent Service
  - `ApimSubnet` (10.0.6.0/24) - APIM VNet injection
- **Log Analytics Workspace** for centralized monitoring

#### Shared BYO Resources

- **Cosmos DB** (serverless) - Thread storage for both departments' agents
- **Storage Account** (blob) - File storage for both departments' agents
- **AI Search** (standard with semantic search) - Vector store for both departments

#### Department 1 Foundry

- **AI Foundry Account** with Agent Service capability host
- Connections to shared Cosmos DB, Storage, AI Search
- Own delegated agent subnet
- Project with Azure AI Developer role assignment

#### Department 2 Foundry

- **AI Foundry Account** with Agent Service capability host
- Connections to **same** shared Cosmos DB, Storage, AI Search
- Own delegated agent subnet
- Project with Azure AI Developer role assignment

#### API Management (AI Gateway)

- **Internal VNet mode** - deployed into ApimSubnet
- System-assigned managed identity with Cognitive Services OpenAI User on all Foundry accounts
- Backends configured for:
  - Department 1 Foundry models
  - Department 2 Foundry models
  - Models-region Foundry models
- Managed identity authentication to backends

### Models Region (East US 2)

- **Foundry Resource** hosting models not available in the primary region (e.g., GPT-5, GPT-4.1)
- **No Agent Service or capability hosts** (models-only resource)
- **Locked-down networking**: public access disabled; reachable via cross-region private endpoint
- Cross-region private endpoint in the primary VNet connects to this resource

## When to Use This Pattern

### Use this pattern if you need

- Multiple departments/teams sharing AI infrastructure with isolation at the Foundry level
- Centralized model governance, rate limiting, and observability via APIM
- Data residency in a specific region with shared BYO resources
- Access to models only available in different Azure regions
- Zero-trust networking with no public internet exposure
- Token usage tracking and cost attribution per department

### Don't use this pattern if

- You only have a single department or team (use the foreign-model-gateway pattern instead)
- You don't need centralized AI governance
- All required models are available in your primary region and you don't need APIM
- Your departments need completely separate data stores (no sharing)

## Deployment

### Prerequisites

- Azure CLI (`az`) with Bicep support
- Azure subscription with quota in both primary and models regions
- Appropriate RBAC roles (Contributor)
- APIM requires Developer or Premium SKU for VNet injection

### Quick Deploy (minimal parameters)

```bash
cd architectures/pattern-centralized-ai-gateway/
az deployment sub create \
  --location australiaeast \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --parameters environmentName=aigw principalId=<your-principal-id>
```

### Customization

Edit `main.bicepparam` or override on the command line:

```bash
# Use different regions
--parameters primaryLocation=eastasia modelsLocation=swedencentral

# Disable API keys (require Azure AD auth)
--parameters disableApiKeys=true

# Use Premium APIM SKU for production
--parameters apimSku=Premium apimSkuCapacity=1

# Custom department names
--parameters department1Name=engineering department1DisplayName='Engineering Team'
--parameters department2Name=research department2DisplayName='Research Team'
```

## Networking Topology

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    Primary Region (Australia East)                    │
│  VNet: 10.0.0.0/16                                                   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ AiServices Subnet (10.0.1.0/24)                               │   │
│  │  [PE: Foundry Dept 1]  [PE: Foundry Dept 2]                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ CapabilityHosts Subnet (10.0.2.0/24)                          │   │
│  │  [PE: Cosmos DB]  [PE: AI Search]  [PE: Storage]              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ ModelsRegion Subnet (10.0.3.0/24)                             │   │
│  │  [PE: Models-Region Foundry] ──────────────────────────┐      │   │
│  └──────────────────────────────────────────────────────┘  │      │   │
│                                                             │      │   │
│  ┌──────────────────────┐  ┌──────────────────────┐        │      │   │
│  │ AgentSubnet1          │  │ AgentSubnet2          │        │      │   │
│  │ (10.0.4.0/24)        │  │ (10.0.5.0/24)        │        │      │   │
│  │ Dept 1 Agent Service │  │ Dept 2 Agent Service │        │      │   │
│  └──────────────────────┘  └──────────────────────┘        │      │   │
│                                                             │      │   │
│  ┌──────────────────────────────────────────────┐          │      │   │
│  │ ApimSubnet (10.0.6.0/24)                      │          │      │   │
│  │  ┌──────────────────────────────────┐         │          │      │   │
│  │  │  API Management (AI Gateway)      │─────────┼──────────┘      │   │
│  │  │  Internal VNet Mode               │         │                  │   │
│  │  └──────────────────────────────────┘         │                  │   │
│  └──────────────────────────────────────────────┘                  │   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Cross-region PE
                                    ▼
┌─────────────────────────────────────────────┐
│         Models Region (East US 2)            │
│                                               │
│  ┌─────────────────────────────────────┐     │
│  │  Foundry Resource (models-only)      │     │
│  │  - GPT-5                             │     │
│  │  - GPT-4.1                           │     │
│  │  - GPT-4.1-mini                      │     │
│  │  Public access: Disabled             │     │
│  └─────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

## AVM Modules Used

| Module | Version | Purpose |
|--------|---------|---------|
| `avm/res/resources/resource-group` | 0.4.3 | Resource groups |
| `avm/res/operational-insights/workspace` | 0.15.0 | Log Analytics |
| `avm/res/network/virtual-network` | 0.7.2 | VNet with subnets |
| `avm/res/network/private-dns-zone` | 0.8.0 | Private DNS zones |
| `avm/res/document-db/database-account` | 0.18.0 | Cosmos DB (serverless) |
| `avm/res/storage/storage-account` | 0.31.0 | Storage Account |
| `avm/res/search/search-service` | 0.12.0 | AI Search |
| `avm/res/api-management/service` | 0.14.1 | API Management |
| `avm/res/network/private-endpoint` | 0.11.1 | Cross-region PE |

Custom modules from this repo:

| Module | Purpose |
|--------|---------|
| `infra/cognitive-services/accounts/main.bicep` | Foundry accounts with projects, connections, capability hosts |
| `infra/core/security/role_foundry.bicep` | Foundry role assignments |
| `infra/core/security/role_aisearch.bicep` | AI Search role assignments |
| `infra/core/security/role_storageaccount.bicep` | Storage role assignments |
