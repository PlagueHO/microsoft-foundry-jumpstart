# Azure AI Foundry Architecture Patterns

This library contains reusable, battle-tested Bicep + AVM architecture patterns for Azure AI Foundry deployments. Each pattern represents a distinct architectural approach optimized for specific scenarios and compliance requirements.

All patterns leverage shared modules from the [core infra](../infra/) directory, ensuring consistency, maintainability, and rapid iteration.

## Pattern Catalog

| Pattern | Scenario | Network Model | Regions | Complexity | Cost Band |
|---------|----------|---------------|---------|-----------| ----------|
| [Foundry with Foreign Models](#foundry-with-foreign-models) | Multi-region model portfolio with data sovereignty | Private endpoints + cross-region PE | 2+ | Medium | $$ |
| [Cross-Region Web App](#cross-region-web-app) | Web App in one region consuming Foundry in another | Cross-region PE + VNet integration | 2 | Medium | $$ |

---

## Foundry with Foreign Models

**Pattern:** `pattern-foreign-model-gateway/`

**Quick Start:**

```bash
cd architectures/pattern-foreign-model-gateway/
az deployment sub create \
  --location australiaeast \
  --template-file main.bicep \
  --parameters main.bicepparam environmentName=fgn principalId=<your-id>
```

**When to use:**

- Sovereign data residency in primary region (e.g., APAC, EU)
- Access to models only available in distant regions (e.g., latest GPT in US)
- Zero-trust networking with private endpoints
- Agent Framework orchestrators accessing multi-region model portfolio

**Key characteristics:**

- ✅ Full stack in primary region (Foundry, Agent Service, BYO resources)
- ✅ Foreign models in geo-distant region
- ✅ Cross-region private endpoint for secure model access
- ✅ No public internet exposure
- ✅ Managed identity RBAC (no API keys required)

**Resources deployed:**

- AI Foundry Account (primary + foreign regions)
- Agent Service Capability Host
- Cosmos DB (serverless, threads)
- AI Search (standard, semantic search)
- Storage Blob (primary data)
- Virtual Network (primary region) with private endpoints
- Private DNS Zones
- Log Analytics Workspace

**Cost estimate:** ~$3K–$5K/month (depends on Foundry API throughput and model capacity)

See [pattern README](./pattern-foreign-model-gateway/README.md) for full details.

---

## Cross-Region Web App

**Pattern:** `pattern-cross-region-webapp/`

**Quick Start:**

```bash
cd architectures/pattern-cross-region-webapp/
az deployment sub create \
  --location australiaeast \
  --template-file main.bicep \
  --parameters main.bicepparam environmentName=crw principalId=<your-id>
```

**When to use:**

- Application infrastructure must reside in a different region to Foundry
- Cross-region private endpoint connectivity to AI services
- Web App front-end calling Foundry Agent Service securely
- Zero-trust networking with no public internet exposure

**Key characteristics:**

- ✅ Foundry + BYO resources in East US 2
- ✅ VNet + Web App in Australia East
- ✅ Cross-region private endpoints (Azure backbone, no internet)
- ✅ .NET 10 Razor Pages app using Agent Service SDK
- ✅ Managed identity RBAC (no API keys required)

**Resources deployed:**

- AI Foundry Account (East US 2)
- Cosmos DB, Storage, AI Search (East US 2)
- Virtual Network with private endpoints (Australia East)
- App Service Plan + Web App (Australia East)
- Private DNS Zones (7 zones)
- Log Analytics Workspace

**Cost estimate:** ~$500–$800/month (depends on model throughput and search volume)

See [pattern README](./pattern-cross-region-webapp/README.md) for full details.

---

## Shared Assets

All patterns build on:

- **[infra/cognitive-services/accounts/main.bicep](../infra/cognitive-services/accounts/main.bicep)** – Custom Foundry module (projects, connections, capability hosts)
- **[infra/core/security/role_*.bicep](../infra/core/security/)** – RBAC role assignment modules
- **[infra/abbreviations.json](../infra/abbreviations.json)** – Corporate naming conventions

### Module Reuse

Each pattern imports shared modules via relative paths:

```bicep
import { deploymentType } from '../../infra/cognitive-services/accounts/main.bicep'
module foundry '../../infra/cognitive-services/accounts/main.bicep' = { ... }
```

This ensures:

- ✅ No code duplication
- ✅ Bug fixes propagate automatically to all patterns
- ✅ Consistent resource naming, tagging, RBAC across deployments
- ✅ Single source of truth for Foundry configuration

---

## Getting Started

### Prerequisites

- Azure CLI with Bicep (`az bicep build` works)
- Azure subscription with appropriate quotas
- Sufficient RBAC permissions (Contributor or resource group owner)

### Deploy a Pattern

1. **Choose a pattern** (e.g., `pattern-foreign-model-gateway/`)
2. **Review the README** to understand scenario and customization options
3. **Edit `main.bicepparam`** with your environment values:

   ```bicep
   param environmentName = 'prod'
   param primaryLocation = 'eastus'
   param principalId = '<your-user-or-app-id>'
   ```

4. **Deploy:**

   ```bash
   cd architectures/pattern-name/
   az deployment sub create \
     --location <location> \
     --template-file main.bicep \
     --parameters main.bicepparam
   ```

5. **Validate:** Check outputs and test connectivity to your Foundry projects

### Customize a Pattern

Each pattern is fully parameterized. Common customizations:

```bash
# Override default locations
az deployment sub create --template-file main.bicep \
  --parameters main.bicepparam \
  --parameters primaryLocation=westeurope foreignModelLocation=northeurope

# Customize model deployments
# Edit main.bicepparam and update primaryModelDeployments / foreignModelDeployments

# Disable API keys (require Azure AD)
--parameters disableApiKeys=true

# Skip foreign model deployment (primary region only)
--parameters deployForeignModels=false
```

---

## Architecture Decision Records (ADRs)

- **Why separate from core infra?** Patterns are *alternatives* to the Jumpstart architecture, not replacement. Core infra remains the reference deployment.
- **Why shared modules in `infra/`?** Single source of truth for Foundry resource provisioning; no drift or duplication.
- **Why private endpoints everywhere?** Zero-trust compliance; models/data never exposed to public internet.
- **Why cross-region private endpoints instead of peering?** Private endpoints are simpler, more secure, and work across subscriptions.

---

## Contributing New Patterns

To add a new architecture pattern:

1. **Create folder:** `architectures/pattern-<name>/`
2. **Scaffold files:**

   ```bash
   mkdir -p architectures/pattern-<name>/docs
   touch architectures/pattern-<name>/main.bicep
   touch architectures/pattern-<name>/main.bicepparam
   touch architectures/pattern-<name>/README.md
   touch architectures/pattern-<name>/architecture.drawio
   ```

3. **Reference shared modules:** Always import from `../../infra/cognitive-services/` and `../../infra/core/security/`
4. **Document:**
   - Problem solved
   - When to use / not use
   - Network diagram (drawio)
   - Deployment steps
   - Cost estimates
5. **Validate:** `az bicep build --file main.bicep`
6. **Add to catalog:** Update this README with pattern table and description
7. **Test deployment:** Full end-to-end validation

---

## Bicep Validation

Validate all patterns before committing:

```bash
# Validate a single pattern
az bicep build --file architectures/pattern-foreign-model-gateway/main.bicep

# Validate all patterns (PowerShell)
Get-ChildItem -Path architectures -Filter main.bicep -Recurse | ForEach-Object {
  az bicep build --file $_.FullName
}
```

---

## Support & Issues

- **Bicep/AVM questions?** See [Azure Verified Modules docs](https://github.com/Azure/bicep-registry-modules)
- **Foundry-specific?** Check [Azure AI Foundry docs](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- **Pattern request?** Open an issue with scenario details
