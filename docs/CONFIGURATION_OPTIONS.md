# Configuration Options

The following environment variables control the deployment behaviour of the Azure AI Foundry Jumpstart Solution accelerator.

The configuration options are grouped into the following categories:

- [Create Sample Data](#create-sample-data)
- [Networking & Isolation](#networking--isolation)
- [Microsoft Foundry Project](#microsoft-foundry-project)
- [Azure AI Search Service](#azure-ai-search-service)
- [Azure Cosmos DB](#azure-cosmos-db)
- [Capability Hosts](#capability-hosts)
- [Identity & Access](#identity--access)
- [Optional Infrastructure](#optional-infrastructure)
- [Security](#security)

## Create Sample Data

These options control the creation of sample data and configuration in the Azure AI Foundry hub.

### DEPLOY_SAMPLE_MODELS

Deploy sample base models into the Microsoft Foundry Project.
Default: `true`.

This will deploy the following models into the Azure OpenAI Service. If the models aren't available in the selected region, or the quota is exceeded, the deployment will fail:

| Model Name             | Version    | Deployment Type | TPM  |
| ---------------------- | ---------- | --------------- | ---- |
| model-router           | 2025-05-19 | Global Standard | 150K |
| gpt-5-mini             | 2025-08-07 | Global Standard | 20K  |
| gpt-5-nano             | 2025-08-07 | Global Standard | 50K  |
| gpt-5-chat             | 2025-08-07 | Global Standard | 50K  |
| gpt-4.1                | 2025-04-14 | Global Standard | 50K  |
| gpt-4.1-mini           | 2025-04-14 | Global Standard | 100K |
| gpt-4.1-nano           | 2025-04-14 | Global Standard | 200K |
| gpt-4o                 | 2024-11-20 | Global Standard | 50K  |
| gpt-4o-transcribe      | 2025-03-20 | Global Standard | 100K |
| gpt-4o-mini            | 2024-07-18 | Global Standard | 100K |
| gpt-4o-mini-transcribe | 2025-03-20 | Global Standard | 100K |
| o4-mini                | 2025-04-16 | Global Standard | 20K  |
| gpt-realtime           | 2025-08-28 | Global Standard | 100K |
| gpt-realtime-mini      | 2025-08-28 | Global Standard | 100K |
| text-embedding-3-large | 1          | Global Standard | 150K |

The list of models, versions, quota and TPM are defined in the [infra/sample-model-deployments.json](../infra/sample-model-deployments.json) file. If you wish to define alternate models, you can edit this file.

```powershell
azd env set DEPLOY_SAMPLE_MODELS false
```

### DEPLOY_SAMPLE_MODELS_LIST

Override the sample model deployments with a custom array. When empty, the deployment uses models defined in [infra/sample-model-deployments.json](../infra/sample-model-deployments.json). When provided, uses the custom array instead.

This parameter is useful when you want to:

- Deploy a different set of models than the defaults
- Test with specific model versions
- Use a custom JSON file with model definitions

Default: `[]` (empty array - uses sample-model-deployments.json).

**Note**: This parameter must be set in a `.bicepparam` file rather than as an environment variable, as it requires a strongly-typed array matching the `deploymentType` schema.

Example in `main.bicepparam`:

```bicep
param deploySampleModelsList = [
  {
    name: 'my-custom-gpt-4'
    model: {
      format: 'OpenAI'
      name: 'gpt-4'
      version: '0613'
    }
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
]
```

Alternatively, you can load from a custom JSON file:

```bicep
param deploySampleModelsList = loadJsonContent('./my-custom-models.json')
```

### DEPLOY_SAMPLE_DATA

Create a dedicated Azure Storage Account for sample data to use with Microsoft Foundry, Foundry IQ and Azure AI Search.
When enabled, sample data containers will be created in the dedicated storage account and datastores will be created in the Microsoft Foundry projects to connect to each container.

> [!IMPORTANT]
> When being deployed from a Windows machine, a PowerShell script is used to upload the sample data to the containers. This script will require the [PowerShell script execution policy](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_execution_policies) to be set to `RemoteSigned` or `Unrestricted`, otherwise an execution error will occur.

Default: `false`.

When set to `true`:

- A dedicated sample data storage account will be deployed (named with 'sample' postfix)
- The following containers will be created in the sample data storage account:

- `tech-support`
- `retail-products`
- `healthcare-records`
- `financial-transactions`
- `insurance-claims`

```powershell
azd env set DEPLOY_SAMPLE_DATA true
```

## Networking & Isolation

### AZURE_NETWORK_ISOLATION

Deploy resources into a virtual network (`true`) or expose public endpoints (`false`).  
Default: `true`.

```powershell
azd env set AZURE_NETWORK_ISOLATION false
```

### AZURE_DISABLE_API_KEYS

Disable API keys on Azure AI services (`true`) and enforce Entra ID authentication only.  
Default: `false`.

```powershell
azd env set AZURE_DISABLE_API_KEYS true
```

## Microsoft Foundry Project

The Microsoft Foundry Jumpstart supports multiple project deployment scenarios based on your architecture preferences:

### Project Deployment Scenarios

1. **No Projects**: Set `MICROSOFT_FOUNDRY_PROJECT_DEPLOY=false` to deploy only the AI Foundry/AI Services without any projects
2. **Projects to AI Foundry/AI Services**: Set `MICROSOFT_FOUNDRY_PROJECT_DEPLOY=true` to deploy projects directly to the AI Foundry/AI Services resource.

### Foundry Project Experience Differences

**Important**: Azure AI Foundry supports two different project experiences that behave differently when working with multiple projects:

- **Foundry (Classic)**: In the Classic experience, the Default Project and **all other projects** deployed to the AI Services resource are visible and usable in the UI. This allows you to work with multiple projects from the same AI Foundry resource.
  - [Learn more about Foundry Classic](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/create-projects?view=foundry-classic&tabs=foundry)

- **Foundry (New)**: In the New experience, **only the Default Project** is accessible through the UI. While additional projects can still be deployed as child resources to the AI Services account, they will not appear in the Foundry portal UI.
  - [Learn more about Foundry New experience](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/create-projects?view=foundry&tabs=foundry)

> [!NOTE]
> If you plan to use the Foundry (New) experience and need to work with multiple projects through the UI, you will need to deploy separate AI Services resources, each with its own Default Project. Alternatively, use the Foundry (Classic) experience to access all projects from a single resource.

### Project Sources

The projects that will be deployed can be defined in two ways:

- **Single Project**: Use the `MICROSOFT_FOUNDRY_PROJECT_*` parameters to define a single project
- **Multiple Projects**: Set `MICROSOFT_FOUNDRY_PROJECTS_FROM_JSON=true` to load project definitions from the `infra/sample-ai-foundry-projects.json` file

### MICROSOFT_FOUNDRY_PROJECT_DEPLOY

Enable deployment of Projects into the Microsoft Foundry/AI Services resource.
When set to `false`, no project resources are created in the Microsoft Foundry/AI Services resource.

Default: `true`.

```powershell
azd env set MICROSOFT_FOUNDRY_PROJECT_DEPLOY false
```

### MICROSOFT_FOUNDRY_PROJECT_NAME

The name of the sample Microsoft Foundry Project. This is used in the resource name, so can not contain spaces or special characters.
Default: `sample-project`.

```powershell
azd env set MICROSOFT_FOUNDRY_PROJECT_NAME "my-ai-project"
```

### MICROSOFT_FOUNDRY_PROJECT_FRIENDLY_NAME

Friendly display name for the sample Microsoft Foundry Project.
Default: `Sample Project`.

```powershell
azd env set MICROSOFT_FOUNDRY_PROJECT_FRIENDLY_NAME "My AI Project"
```

### MICROSOFT_FOUNDRY_PROJECT_DESCRIPTION

Optional description for the sample Microsoft Foundry Project shown in the Azure portal.
Default: `A sample project for Microsoft Foundry`.

```powershell
azd env set MICROSOFT_FOUNDRY_PROJECT_DESCRIPTION "This is my first AI project."
```

### MICROSOFT_FOUNDRY_PROJECTS_FROM_JSON

Use projects defined in infra/sample-ai-foundry-projects.json file instead of the single project parameters.
When set to `true`, the `MICROSOFT_FOUNDRY_PROJECT_NAME`, `MICROSOFT_FOUNDRY_PROJECT_FRIENDLY_NAME`, and `MICROSOFT_FOUNDRY_PROJECT_DESCRIPTION` parameters are ignored.
Default: `false`.

```powershell
azd env set MICROSOFT_FOUNDRY_PROJECTS_FROM_JSON true
```

The `infra/sample-ai-foundry-projects.json` file contains an array of project definitions. Each project definition includes the following properties:

| Property     | Description                                               |
| ------------ | --------------------------------------------------------- |
| Name         | The name of the AI Foundry project (used in resource name)|
| FriendlyName | Display name shown in the Azure portal                    |
| Description  | Optional description shown in the Azure portal            |

Example JSON structure:

```json
[
  {
    "Name": "contoso-retail-analytics",
    "FriendlyName": "Contoso Retail Analytics",
    "Description": "Sample project demonstrating AI-driven product recommendations."
  },
  {
    "Name": "fabrikam-health-insights",
    "FriendlyName": "Fabrikam Health Insights",
    "Description": "Sample healthcare project showcasing patient-note summarisation."
  }
]
```

You can modify this file to define your own set of projects to be created during deployment.

## Azure AI Search Service

### AZURE_AI_SEARCH_SKU

SKU tier for the Azure AI Search service.  
Allowed: `standard` | `standard2` | `standard3` | `storage_optimized_l1` | `storage_optimized_l2`.
Default: `standard`.

```powershell
azd env set AZURE_AI_SEARCH_SKU standard2
```

### AZURE_AI_SEARCH_DEPLOY

Deploy the Azure AI Search service **and** all related role assignments / connections (`true`).  
When set to `false`, no Search resources or privileges are created.

Default: `true`.

```powershell
azd env set AZURE_AI_SEARCH_DEPLOY false
```

### AZURE_AI_SEARCH_REPLICA_COUNT

Number of replicas in the Azure AI Search service. Replicas provide high availability and increase query throughput.  
Must be between 1 and 12.
Default: `1`.

```powershell
azd env set AZURE_AI_SEARCH_REPLICA_COUNT 2
```

### AZURE_AI_SEARCH_PARTITION_COUNT

Number of partitions in the Azure AI Search service. Partitions divide the search index to enable scaling and parallel processing.  
Allowed: `1` | `2` | `3` | `4` | `6` | `12`.
Default: `1`.

```powershell
azd env set AZURE_AI_SEARCH_PARTITION_COUNT 2
```

## Azure Cosmos DB

Azure Cosmos DB can be deployed to provide thread storage for AI agents. This is used by capability hosts to persist conversation threads.

### COSMOS_DB_DEPLOY

Deploy an Azure Cosmos DB account for thread storage (`true`).
When enabled, a serverless Cosmos DB account with a SQL API database named `AgentThreads` is created.

Default: `false`.

```powershell
azd env set COSMOS_DB_DEPLOY true
```

### COSMOS_DB_CAPABILITY_HOST

Use the deployed Cosmos DB account as a thread storage capability host for AI agents (`true`).
Requires `COSMOS_DB_DEPLOY` to be set to `true`.

When enabled, a connection to the Cosmos DB account is created in the Foundry resource and configured as the thread storage for the default capability host.

Default: `false`.

```powershell
azd env set COSMOS_DB_CAPABILITY_HOST true
```

## Capability Hosts

Capability hosts enable AI agent functionality by configuring storage backends for threads, vectors, and files. These settings control which deployed resources are automatically configured as capability hosts.

For more information about capability hosts, see [Azure AI Foundry Capability Hosts](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/capability-hosts).

### AZURE_AI_SEARCH_CAPABILITY_HOST

Use Azure AI Search as a vector store capability host for AI agents (`true`).
Requires `AZURE_AI_SEARCH_DEPLOY` to be set to `true`.

When enabled, a connection to the AI Search service is configured as the vector store for the default capability host.

Default: `false`.

```powershell
azd env set AZURE_AI_SEARCH_CAPABILITY_HOST true
```

### AZURE_STORAGE_ACCOUNT_CAPABILITY_HOST

Use the sample data Azure Storage Account as a file storage capability host for AI agents (`true`).
Requires `DEPLOY_SAMPLE_DATA` to be set to `true`.

When enabled, a connection to the storage account is configured as the file storage for the default capability host.

Default: `false`.

```powershell
azd env set AZURE_STORAGE_ACCOUNT_CAPABILITY_HOST true
```

## Identity & Access

### AZURE_PRINCIPAL_ID

Object ID (GUID) of the user or service principal to grant access to the AI Foundry hub.
Default: current Azure CLI principal.

```powershell
azd env set AZURE_PRINCIPAL_ID "00000000-0000-0000-0000-000000000000"
```

### AZURE_PRINCIPAL_ID_TYPE

The type of identity in `AZURE_PRINCIPAL_ID`.
Allowed: `user` | `serviceprincipal`.
Default: `user`.

```powershell
azd env set AZURE_PRINCIPAL_ID_TYPE serviceprincipal
```

## Optional Infrastructure

### AZURE_BASTION_HOST_DEPLOY

Deploy an Azure Bastion host for secure RDP/SSH access (`true`).  

Default: `false`.

```powershell
azd env set AZURE_BASTION_HOST_DEPLOY true
```

### AZURE_CONTAINER_REGISTRY_RESOURCE_ID

Provide the full resource-id of an existing Azure Container Registry to associate with the deployment.  
When set, the accelerator **does not** create a new registry.
If `AZURE_NETWORK_ISOLATION` is `true`, ensure the registry already has the required private endpoints and DNS zones.
If `AZURE_CONTAINER_REGISTRY_DEPLOY` is set to `true`, this setting is ignored.

```powershell
azd env set AZURE_CONTAINER_REGISTRY_RESOURCE_ID "/subscriptions/<subId>/resourceGroups/rg-xyz/providers/Microsoft.ContainerRegistry/registries/acrExisting"
```

### AZURE_CONTAINER_REGISTRY_DEPLOY

Deploy a new Azure Container Registry **or** attach an existing one (`true`).  
When set to `true`, `AZURE_CONTAINER_REGISTRY_RESOURCE_ID` is ignored and the AI Foundry Hub is created without an attached registry.

Default: `false`.

```powershell
azd env set AZURE_CONTAINER_REGISTRY_DEPLOY true
```

### AZURE_STORAGE_ACCOUNT_NAME

Override the default storage account name, which is automatically generated from the environment name.
Default: `environment-name`.

```powershell
azd env set AZURE_STORAGE_ACCOUNT_NAME mycustomstorage
```

## Security

### AZURE_KEYVAULT_ENABLE_PURGE_PROTECTION

Enable purge protection on the Key Vault (`true`). When enabled, the vault cannot be permanently deleted until purge protection is disabled.  
Default: `false`.

```powershell
azd env set AZURE_KEYVAULT_ENABLE_PURGE_PROTECTION true
```
