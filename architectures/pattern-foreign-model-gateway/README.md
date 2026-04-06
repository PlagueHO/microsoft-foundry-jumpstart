# Foundry with Foreign Models Architecture Pattern

## Overview

This pattern deploys a **hybrid multi-region Foundry architecture** that enables sovereign data residency in a primary region while accessing models hosted in distant regions via secure cross-region private endpoints.

### Problem Solved

- **Data sovereignty**: Foundry, Agent Service capability hosts, and BYO resources live in the primary region (e.g., Australia East).
- **Model availability**: Models not available in the primary region are deployed to an Azure OpenAI resource in a foreign region (e.g., Sweden Central).
- **Secure cross-region access**: Applications reach foreign models over Azure's private backbone—no public internet exposure.
- **No network isolation compromise**: Private endpoints and network policies ensure both regions remain locked down.

## Architecture Components

### Primary Region

- **AI Foundry Account** with Agent Service capability host
- **Agent Service Connections**: Cosmos DB (threads), AI Search (vectors), Storage (files)
- **Virtual Network** with dedicated subnets for:
  - Private endpoints (AI Services, search, storage, Cosmos DB, Key Vault)
  - Agent Service capability host compute
  - Cross-region private endpoint access to foreign models
- **Bring-Your-Own (BYO) Resources**:
  - Cosmos DB (serverless, threads)
  - Storage Account (blob)
  - AI Search (standard with semantic search)
  - Key Vault (secrets & certificate management)

### Foreign Region

- **Azure OpenAI Account** hosting foreign models
- **No Agent Service or capability hosts** (models accessed directly via private endpoint)
- **Locked-down networking**: Public access disabled; only reachable via cross-region private endpoint

### Cross-Region Connectivity

- **Private Endpoint** in primary VNet connects to foreign Azure OpenAI resource
- **Private DNS Zones** resolve foreign region endpoints to private IPs
- **Applications** call foreign models via Azure OpenAI SDK through the private endpoint (not via Agent Service)

## When to Use This Pattern

✅ **Use this pattern if you need:**

- Data residency in a specific region (e.g., APAC, EU) with Agent Service
- Access to models only available in geographically distant regions
- Zero-trust networking with no public internet exposure
- Multi-region model portfolio for applications
- Sovereign capability hosts with global model access

❌ **Don't use this pattern if:**

- All required models are available in your primary region
- You don't need cross-region private endpoint overhead
- Your compliance doesn't mandate data residency
- Single-region deployment is sufficient
- You require orchestration across resource groups (use Agent Framework)

## Deployment

### Prerequisites

- Azure CLI (`az`) with Bicep support
- Azure subscription with quota in both primary and foreign regions
- Appropriate RBAC roles (Contributor)

### Quick Deploy (minimal parameters)

```bash
cd architectures/pattern-foreign-model-gateway/
az deployment sub create \
  --location australiaeast \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --parameters environmentName=fgn principalId=<your-principal-id>
```

### Customization

Edit `main.bicepparam` or override on the command line:

```bash
# Use different regions (primary in APAC, foreign models in Europe)
--parameters primaryLocation=eastasia foreignModelLocation=swedencentral

# Disable API keys (require Azure AD auth)
--parameters disableApiKeys=true

# Custom model deployments
# Edit main.bicepparam and update primaryModelDeployments / foreignModelDeployments arrays

# Deploy only primary models (no foreign models)
--parameters deployForeignModels=false
```

## Networking Topology

```
┌─────────────────────────────────────────────────────────┐
│ PRIMARY REGION (e.g., Australia East)                   │
│                                                           │
│  ┌──────────────────────────────────────────────┐       │
│  │ Virtual Network (10.0.0.0/16)                │       │
│  │  ├─ AiServices Subnet     (10.0.1.0/24)     │       │
│  │  │  └─ PE: Primary Foundry Account          │       │
│  │  ├─ CapabilityHosts Subnet (10.0.2.0/24)    │       │
│  │  │  ├─ PE: Cosmos DB                        │       │
│  │  │  ├─ PE: Storage Blob                     │       │
│  │  │  ├─ PE: AI Search                        │       │
│  │  │  └─ PE: Key Vault                        │       │
│  │  ├─ ForeignModels Subnet  (10.0.3.0/24)     │       │
│  │  │  └─ PE: Foreign Azure OpenAI (cross-rg)  │       │
│  │  └─ AgentSubnet (10.0.4.0/24)               │       │
│  │     └─ Agent Service Capability Hosts       │       │
│  └──────────────────────────────────────────────┘       │
│                                                           │
│  Primary Foundry Account (AIServices)                    │
│   ├─ Models: gpt-4o (primary region only)               │
│   ├─ Project: agent-project                             │
│   └─ Connections:                                       │
│      ├─ Cosmos DB (AgentThreads)                        │
│      ├─ Storage (default container)                     │
│      └─ AI Search (vector store)                        │
│                                                           │
│  BYO Resources (CapabilityHosts Subnet)                  │
│   ├─ Cosmos DB (serverless, threads)                    │
│   ├─ Storage Account (blob, agent files)                │
│   ├─ AI Search (semantic search, vectors)               │
│   └─ Key Vault (secrets, certificates, API keys)        │
└─────────────────────────────────────────────────────────┘
                        │
                        ### Post-Deployment Key Vault RBAC Setup
                        │ Cross-region private endpoint
                        After deployment completes, grant Foundry and developer access to Key Vault:

                        ```bash
                        # Get resource IDs
                        KEYVAULT_ID=$(az keyvault show --name <key-vault-name> --query id -o tsv)
                        FOUNDRY_PRINCIPAL=$(az deployment sub show --name <deployment-name> --query outputs.FOUNDRY_NAME -o tsv | xargs -I {} az cognitiveservices account show --name {} --resource-group <rg-name> --query identity.principalId -o tsv)

                        # Grant Foundry managed identity access to secrets
                        az role assignment create --role "Key Vault Secrets Officer" --assignee $FOUNDRY_PRINCIPAL --scope $KEYVAULT_ID

                        # Grant developer full access
                        az role assignment create --role "Key Vault Administrator" --assignee <your-principal-id> --scope $KEYVAULT_ID
                        ```

                        │ (via private DNS zones)
                        ▼
┌─────────────────────────────────────────────────────────┐
│ FOREIGN REGION (e.g., Sweden Central)                   │
│                                                           │
│  Azure OpenAI Account                                    │
│   └─ Models: gpt-4, gpt-4o, custom models               │
│      (accessed by primary region apps via private PE)    │
└─────────────────────────────────────────────────────────┘
```

## Cost & Performance Considerations

### Cost

- **Primary region**: Full stack (Foundry, Agent Service, storage, networking)
- **Foreign region**: Minimal (Azure OpenAI resource + models only; no compute/storage overhead)
- **Cross-region data transfer**: Negligible for metadata; model inference calls incur egress

### Performance

- **Latency**: ~50–150ms round-trip to foreign models (via private backbone)
- **Throughput**: Depends on Azure OpenAI deployment quota
- **DNS resolution**: Instant (private DNS zones cache answers)

### Reliability

- Primary region resources: ZRS (Zone Redundant) where available
- Foreign region: Fault-isolated (separate subscription/resource group)
- No single point of failure for model access

## Security & Compliance

✅ **Zero-Trust Principles:**

- All resources use private endpoints; public access disabled
- Network policies prevent unsanctioned endpoint egress
- Managed identities for RBAC (no API keys by default)
- Microsoft-only routing (Azure backbone)

✅ **Compliance Friendliness:**

- Data residency: All primary data in primary region
- Model access: Private endpoints only (no internet)
- Audit logs: Log Analytics workspace captures all activity

✅ **Secrets Management:**

- Disabled API key auth recommended (`disableApiKeys=true`)
- Use Azure AD with managed identities
- Consider Key Vault integration for certificate/key rotation

## Troubleshooting

### Deployment Fails on Foreign Resource Group

- Check quota in foreign region: `az quota view --resource-name subscriptionQuota/compute-cores --region <location>`
- Verify region support for Foundry accounts

### Agent Cannot Reach Foreign Models

- Verify private endpoint DNS records: `nslookup <foreign-foundry>.cognitiveservices.azure.com`
- Check NSG rules: subnets should allow outbound HTTPS (443)
- Verify RBAC: Primary Foundry identity should have `Cognitive Services OpenAI User` on foreign Foundry

### High Cross-Region Latency

- Expected latency: 50–150ms
- If higher, check VNet peering / routing config
- Consider co-locating orchestrator closer to foreign models if latency-critical

## Architecture Decision Records (ADRs)

- **Why no AKS?** Agent Service capability hosts provide serverless agent compute; no need for Kubernetes.
- **Why separate resource groups?** Isolates blast radius; foreign models can fail independently.
- **Why both VNets are private?** Zero-trust compliance; no models/data exposed to public internet.
- **Why cross-region private endpoint instead of global peering?** Simpler setup, works across subscriptions, no additional routing overhead.

## Related Patterns

- **[Foundry Single Region](../../infra/)**: Baseline Jumpstart pattern (primary architecture); use if multi-region not needed
