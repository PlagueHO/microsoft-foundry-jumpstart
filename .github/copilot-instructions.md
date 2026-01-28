This is an Azure Developer CLI (azd) solution accelerator for deploying Microsoft Foundry environments with zero-trust networking and enterprise security patterns.

## Architecture Overview

**Core Concept**: Deploy AI Services-based projects (not legacy Hub mode) using Azure Verified Modules with optional network isolation.

- **AI Foundry** = AI Services resource (`Microsoft.CognitiveServices/accounts`) managing projects, connections, and deployments
- **Projects** = deployed directly to AI Services (`/accounts/projects`), not to separate Hub resources
- **Network Isolation** = all resources use private endpoints (10.0.0.0/16 VNet with dedicated subnets: AiServices 10.0.1.0/24, Data 10.0.2.0/24)
- **Hub Mode Deprecated** (Dec 2025) = no longer supports `Microsoft.MachineLearningServices/workspaces`

Key architectural files: [infra/main.bicep](infra/main.bicep), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Infrastructure as Code Patterns

### Azure Verified Modules (AVM)

All infrastructure uses AVM modules from `br/public:avm/res/*`. **Never** create raw resource declarations:

```bicep
// ✅ Correct - use AVM
module aiSearch 'br/public:avm/res/search/search-service:0.11.1' = {
  name: 'ai-search-deployment'
  params: { name: aiSearchName, sku: 'standard' }
}

// ❌ Wrong - raw resource
resource aiSearch 'Microsoft.Search/searchServices@2024-03-01' = { }
```

### Custom Cognitive Services Module

AI Foundry requires a custom module at `infra/cognitive-services/accounts/main.bicep` because AVM doesn't yet support AI Foundry V2 projects/connections ([tracked issue](https://github.com/Azure/bicep-registry-modules/issues/5390)). This module:

- Deploys projects as child resources via `infra/cognitive-services/accounts/project/main.bicep`
- Creates connections via `infra/cognitive-services/accounts/connection/main.bicep`
- Uses AVM common types for consistency (`diagnosticSettingFullType`, `privateEndpointSingleServiceType`)

### Role Assignment Pattern

Role assignments use dedicated modules in `infra/core/security/role_*.bicep` to avoid circular dependencies:

```bicep
// Deploy resource first
module aiFoundry './cognitive-services/accounts/main.bicep' = { }

// Then assign roles in separate module
module roles './core/security/role_aifoundry.bicep' = {
  dependsOn: [aiFoundry]
  params: {
    azureAiFoundryName: aiFoundryName
    roleAssignments: [/* assignments */]
  }
}
```

### Conditional Deployment

Use `if` conditions and ternary operators for optional resources:

```bicep
module aiSearch 'br/public:avm/res/search/search-service:0.11.1' = if (azureAiSearchDeploy) { }

var connections = concat(
  azureAiSearchDeploy ? [{ /* search connection */ }] : [],
  deploySampleData ? [{ /* storage connection */ }] : []
)
```

## Developer Workflows

### Deployment Commands

```bash
# Standard deployment
azd up

# Configure before deployment
azd env set AZURE_NETWORK_ISOLATION false  # public endpoints
azd env set DEPLOY_SAMPLE_MODELS true
azd env set AZURE_AI_FOUNDRY_PROJECT_DEPLOY true

# Teardown
azd down --force --purge
```

### Post-Provision Hooks

`azure.yaml` defines hooks that run after `azd provision`:

- **Windows**: `scripts/Upload-SampleData.ps1` (requires `RemoteSigned` execution policy)
- **POSIX**: `scripts/Upload-SampleData.sh`

These scripts:

1. Check `DEPLOY_SAMPLE_DATA` env var
2. Add temporary IP rules to storage if network isolated
3. Upload sample data from `sample-data/` to containers
4. Clean up temporary firewall rules

### Bicep Validation

```bash
# Lint and build
az bicep build --file infra/main.bicep

# Validate deployment (what-if)
az deployment sub what-if --location eastus --template-file infra/main.bicep
```

### Python Development

Tool projects in `tools/python/src/` follow this structure:

- `__main__.py` - entry point enabling `python -m <tool>`
- `cli.py` - Click-based CLI interface
- `engine.py` - core business logic
- `pyproject.toml` - dependencies and tool config

Example tools: `create_ai_search_index`, `data_generator`

Run linting/tests (from `tools/python/` directory):

```bash
python -m ruff check src/ --fix
python -m mypy src/
python -m pytest tests/
```

## Configuration System

All config via `azd env set <KEY> <VALUE>` (stored in `.azure/<env>/.env`):

| Key | Default | Impact |
|-----|---------|--------|
| `AZURE_NETWORK_ISOLATION` | `true` | Creates VNet, private endpoints, DNS zones |
| `AZURE_AI_SEARCH_DEPLOY` | `true` | Deploys AI Search + role assignments |
| `DEPLOY_SAMPLE_DATA` | `false` | Creates storage account, uploads sample data |
| `AZURE_AI_FOUNDRY_PROJECT_DEPLOY` | `true` | Creates projects in AI Services |
| `AZURE_AI_FOUNDRY_PROJECTS_FROM_JSON` | `false` | Uses `infra/sample-ai-foundry-projects.json` instead of single project params |

See [docs/CONFIGURATION_OPTIONS.md](docs/CONFIGURATION_OPTIONS.md) for complete reference.

## CI/CD Pipeline

GitHub Actions workflows in `.github/workflows/`:

- **continuous-integration.yml**: PR validation (lint Bicep)
- **continuous-delivery.yml**: Main branch deployment orchestration
- **e2e-test.yml**: Full deploy → test → teardown cycle
- **validate-infrastructure.yml**: ARM `what-if` validation
- **provision-infrastructure.yml**: `azd up` deployment

Uses workload identity federation (no service principal secrets).

## Project-Specific Conventions

1. **Naming**: Use `abbrs` from `infra/abbreviations.json` + `${environmentName}` pattern (e.g., `st${environmentName}sample`)
2. **Tagging**: All resources get `azd-env-name: ${environmentName}` tag
3. **Diagnostic Settings**: All resources send metrics/logs to Log Analytics with setting name `send-to-${logAnalyticsName}`
4. **Storage account names**: ≤ 24 chars, lowercase, no hyphens (use `toLower(replace(...))`)
5. **Module names**: Max 64 chars due to Azure limits (use `take()` for project-based deployments)

## Language-Specific Instructions

**Bicep**: See above patterns + always include `@sys.description()` on parameters

**Python**: Follow PEP 8, use type hints, docstrings with Google style, 79-char line limit. See `.github/instructions/python.instructions.md`.

**PowerShell**: Follow Microsoft guidelines in `.github/instructions/powershell-best-practices.instructions.md`.

**C#**: Follow C# 14 conventions in `.github/instructions/csharp-14-best-practices.instructions.md`.

## Common Pitfalls

❌ **Don't** create AI Foundry Hub mode resources (deprecated)  
❌ **Don't** use raw `resource` declarations - use AVM modules  
❌ **Don't** deploy role assignments in same module as resource (causes circular deps)  
❌ **Don't** forget network isolation impacts sample data upload scripts  
❌ **Don't** exceed 64-char deployment names (esp. with project loops)

✅ **Do** use conditional deployments with `if` expressions  
✅ **Do** use dedicated role assignment modules after resource creation  
✅ **Do** test with both `AZURE_NETWORK_ISOLATION=true` and `false`  
✅ **Do** validate Bicep with `az bicep build` before committing

## Azure-Specific Rules

When creating infrastructure as code, follow Azure Well-Architected Framework best practices prioritizing: Security, Operational Excellence, Performance Efficiency, Reliability, and Cost Optimization.

- @azure Rule - Use Azure Best Practices: When generating code for Azure, running terminal commands for Azure, or performing operations related to Azure, invoke your `get_azure_best_practices` tool if available.
