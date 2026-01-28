# Quick Configurations

The following configurations are quick setups for deploying Microsoft Foundry with project support. These configurations can be used to set up the environment variables required for deployment.

## Without Network Isolation

```bash
azd env set AZURE_NETWORK_ISOLATION false
azd env set DEPLOY_SAMPLE_MODELS true
azd env set DEPLOY_SAMPLE_DATA true
azd env set AZURE_AI_SEARCH_DEPLOY true
azd env set MICROSOFT_FOUNDRY_PROJECTS_FROM_JSON true
azd env set MICROSOFT_FOUNDRY_PROJECT_DEPLOY true
```

## With Network Isolation

```bash
azd env set AZURE_NETWORK_ISOLATION true
azd env set DEPLOY_SAMPLE_MODELS true
azd env set DEPLOY_SAMPLE_DATA true
azd env set AZURE_AI_SEARCH_DEPLOY true
azd env set MICROSOFT_FOUNDRY_PROJECTS_FROM_JSON true
azd env set MICROSOFT_FOUNDRY_PROJECT_DEPLOY true
```

## With Capability Hosts (AI Agents Support)

This configuration deploys all resources needed for AI agent functionality, including thread storage (Cosmos DB), vector store (AI Search), and file storage.

### Without Network Isolation

```bash
azd env set AZURE_NETWORK_ISOLATION false
azd env set DEPLOY_SAMPLE_MODELS true
azd env set DEPLOY_SAMPLE_DATA true
azd env set AZURE_AI_SEARCH_DEPLOY true
azd env set AZURE_AI_SEARCH_CAPABILITY_HOST true
azd env set COSMOS_DB_DEPLOY true
azd env set COSMOS_DB_CAPABILITY_HOST true
azd env set AZURE_STORAGE_ACCOUNT_CAPABILITY_HOST true
azd env set MICROSOFT_FOUNDRY_PROJECTS_FROM_JSON true
azd env set MICROSOFT_FOUNDRY_PROJECT_DEPLOY true
```

### With Network Isolation

```bash
azd env set AZURE_NETWORK_ISOLATION true
azd env set DEPLOY_SAMPLE_MODELS true
azd env set DEPLOY_SAMPLE_DATA true
azd env set AZURE_AI_SEARCH_DEPLOY true
azd env set AZURE_AI_SEARCH_CAPABILITY_HOST true
azd env set COSMOS_DB_DEPLOY true
azd env set COSMOS_DB_CAPABILITY_HOST true
azd env set AZURE_STORAGE_ACCOUNT_CAPABILITY_HOST true
azd env set MICROSOFT_FOUNDRY_PROJECTS_FROM_JSON true
azd env set MICROSOFT_FOUNDRY_PROJECT_DEPLOY true
```
