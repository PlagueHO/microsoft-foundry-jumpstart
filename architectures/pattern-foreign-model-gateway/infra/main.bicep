targetScope = 'subscription'

// ============================================================================
// Foundry with Foreign Models - Architecture Pattern
// ============================================================================
// Deploys a hybrid architecture with:
//   - Primary region (e.g. Australia East): Foundry account + Agent Service
//     capability hosts with BYO resources (Cosmos DB, Storage, AI Search) for
//     data sovereignty
//   - Foreign model region (e.g. Sweden Central): Azure OpenAI resource
//     hosting models not available in the primary region
//   - Cross-region private endpoint so clients in the primary region can call
//     foreign-region models over the Microsoft backbone
//
// The Agent Service capability hosts use only primary-region models.
// External applications call foreign-region models directly via cross-region
// private endpoint without internet exposure.
// ============================================================================

import { deploymentType } from '../../../infra/cognitive-services/accounts/main.bicep'
import { capabilityHostType } from '../../../infra/cognitive-services/accounts/capabilityHost/main.bicep'

// ---------- GLOBAL PARAMETERS ----------

@sys.description('Name of the environment which is used to generate a short unique hash used in all resources.')
@minLength(1)
@maxLength(40)
param environmentName string

@sys.description('Primary region for all data-sovereign resources (Foundry, Agent Service, BYO resources, VNet).')
@minLength(1)
param primaryLocation string = 'australiaeast'

@sys.description('Foreign region where additional model deployments are hosted.')
@minLength(1)
param foreignModelLocation string = 'eastus2'

@sys.description('The Azure resource group where primary-region resources will be deployed.')
param resourceGroupName string = 'rg-${environmentName}'

@sys.description('The Azure resource group where foreign-model-region resources will be deployed. Defaults to a separate resource group.')
param foreignResourceGroupName string = 'rg-${environmentName}-models'

@sys.description('Id of the user or app to assign application roles.')
param principalId string

@sys.description('Type of the principal referenced by principalId.')
@allowed([
  'User'
  'ServicePrincipal'
])
param principalIdType string = 'User'

@sys.description('Disable API key authentication for all Cognitive Services resources. Defaults to false.')
param disableApiKeys bool = false

// ---------- PRIMARY FOUNDRY PARAMETERS ----------

@sys.description('Deploy model deployments to the primary Foundry account. Defaults to true.')
param deployPrimaryModels bool = true

@sys.description('Model deployments for the primary-region Foundry account. Only models available in the primary region should be listed.')
param primaryModelDeployments deploymentType[] = [
  {
    name: 'gpt-4o'
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
    sku: {
      name: 'Standard'
      capacity: 30
    }
  }
]

// ---------- FOREIGN MODEL PARAMETERS ----------

@sys.description('Deploy model deployments to the foreign-region resource. Defaults to true.')
param deployForeignModels bool = true

@sys.description('Model deployments for the foreign-region resource. These are models not available in the primary region.')
param foreignModelDeployments deploymentType[] = [
  {
    name: 'gpt-5'
    model: {
      format: 'OpenAI'
      name: 'gpt-5'
      version: '2025-06-18'
    }
    sku: {
      name: 'Standard'
      capacity: 50
    }
  }
  {
    name: 'gpt-4-1'
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1'
      version: '2025-04-14'
    }
    sku: {
      name: 'Standard'
      capacity: 50
    }
  }
  {
    name: 'gpt-4-1-mini'
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1-mini'
      version: '2025-04-14'
    }
    sku: {
      name: 'Standard'
      capacity: 50
    }
  }
]

// ---------- FOUNDRY PROJECT PARAMETERS ----------

@sys.description('Deploy a Foundry project in the primary-region Foundry account. Defaults to true.')
param foundryProjectDeploy bool = true

@sys.description('The name of the Foundry project to create.')
param foundryProjectName string = 'agent-project'

@sys.description('The display name of the Foundry project.')
param foundryProjectFriendlyName string = 'Agent Project'

@sys.description('The description of the Foundry project.')
param foundryProjectDescription string = 'Foundry project for Agent Framework orchestrator with foreign model access'

// ---------- NAMING ----------

var abbrs = loadJsonContent('../../../infra/abbreviations.json')

var tags = {
  'azd-env-name': environmentName
}

var logAnalyticsName = '${abbrs.operationalInsightsWorkspaces}${environmentName}'
var sendToLogAnalyticsCustomSettingName = 'send-to-${logAnalyticsName}'
var virtualNetworkName = '${abbrs.networkVirtualNetworks}${environmentName}'
var foundryServiceName = '${abbrs.foundryAccounts}${environmentName}'
var foundryCustomSubDomainName = foundryServiceName
var foreignFoundryName = '${abbrs.foundryAccounts}${environmentName}-fgn'
var foreignFoundrySubDomainName = foreignFoundryName
var aiSearchServiceName = '${abbrs.aiSearchSearchServices}${environmentName}'
var storageAccountName = take(toLower(replace('${abbrs.storageStorageAccounts}${environmentName}agent', '-', '')), 24)
var cosmosDbAccountName = '${abbrs.cosmosDBAccounts}${replace(environmentName, '-', '')}agent'
var keyVaultName = '${abbrs.keyVaultVaults}${replace(environmentName, '-', '')}-agent'

// ---------- RESOURCE GROUPS ----------

module primaryResourceGroup 'br/public:avm/res/resources/resource-group:0.4.3' = {
  name: 'rg-primary-deployment'
  params: {
    name: resourceGroupName
    location: primaryLocation
    tags: tags
  }
}

module foreignResourceGroup 'br/public:avm/res/resources/resource-group:0.4.3' = {
  name: 'rg-foreign-deployment'
  params: {
    name: foreignResourceGroupName
    location: foreignModelLocation
    tags: tags
  }
}

// ---------- MONITORING ----------

module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.15.0' = {
  name: 'log-analytics-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: logAnalyticsName
    location: primaryLocation
    tags: tags
  }
}

// ---------- VIRTUAL NETWORK ----------
// Primary-region VNet with subnets for private endpoints, agent compute, and AKS

var subnets = [
  {
    name: 'AiServices'
    addressPrefix: '10.0.1.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    name: 'CapabilityHosts'
    addressPrefix: '10.0.2.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Subnet for cross-region private endpoints (foreign models)
    name: 'ForeignModels'
    addressPrefix: '10.0.3.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Delegated to Microsoft.App/environments for Agent Service compute
    name: 'AgentSubnet'
    addressPrefix: '10.0.4.0/24'
    delegation: 'Microsoft.App/environments'
  }
]

module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.2' = {
  name: 'vnet-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: virtualNetworkName
    location: primaryLocation
    addressPrefixes: [
      '10.0.0.0/16'
    ]
    subnets: subnets
    tags: tags
  }
}

// ---------- PRIVATE DNS ZONES ----------

module cognitiveServicesDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-cognitiveservices'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'privatelink.cognitiveservices.azure.com'
    location: 'global'
    tags: tags
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
        registrationEnabled: false
      }
    ]
  }
}

module openAiDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-openai'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'privatelink.openai.azure.com'
    location: 'global'
    tags: tags
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
        registrationEnabled: false
      }
    ]
  }
}

module aiServicesDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-aiservices'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'privatelink.services.ai.azure.com'
    location: 'global'
    tags: tags
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
        registrationEnabled: false
      }
    ]
  }
}

module searchDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-search'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'privatelink.search.windows.net'
    location: 'global'
    tags: tags
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
        registrationEnabled: false
      }
    ]
  }
}

module cosmosDbDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-cosmosdb'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'privatelink.documents.azure.com'
    location: 'global'
    tags: tags
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
        registrationEnabled: false
      }
    ]
  }
}

module storageBlobDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-blob'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'privatelink.blob.${environment().suffixes.storage}'
    location: 'global'
    tags: tags
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
        registrationEnabled: false
      }
    ]
  }
}

module keyVaultDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-keyvault'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'privatelink.vaultcore.azure.net'
    location: 'global'
    tags: tags
    virtualNetworkLinks: [
      {
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
        registrationEnabled: false
      }
    ]
  }
}

// ---------- BYO RESOURCES (PRIMARY REGION) ----------
// Cosmos DB for thread storage, Storage Account for file storage, AI Search for vector store

module cosmosDbAccount 'br/public:avm/res/document-db/database-account:0.18.0' = {
  name: 'cosmos-db-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: cosmosDbAccountName
    location: primaryLocation
    capabilitiesToAdd: [
      'EnableServerless'
    ]
    diagnosticSettings: [
      {
        metricCategories: [{ category: 'AllMetrics' }]
        name: sendToLogAnalyticsCustomSettingName
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
      }
    ]
    disableLocalAuthentication: disableApiKeys
    managedIdentities: {
      systemAssigned: true
    }
    networkRestrictions: {
      publicNetworkAccess: 'Disabled'
      networkAclBypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: []
    }
    privateEndpoints: [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: cosmosDbDnsZone.outputs.resourceId }
          ]
        }
        service: 'Sql'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[1] // CapabilityHosts
        tags: tags
      }
    ]
    sqlDatabases: [
      {
        name: 'AgentThreads'
        containers: [
          {
            name: 'threads'
            paths: ['/threadId']
          }
        ]
      }
    ]
    tags: tags
  }
}

module storageAccount 'br/public:avm/res/storage/storage-account:0.31.0' = {
  name: 'storage-account-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: storageAccountName
    allowBlobPublicAccess: false
    blobServices: {
      automaticSnapshotPolicyEnabled: false
      containerDeleteRetentionPolicyEnabled: false
      deleteRetentionPolicyEnabled: false
    }
    diagnosticSettings: [
      {
        metricCategories: [{ category: 'AllMetrics' }]
        name: sendToLogAnalyticsCustomSettingName
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
      }
    ]
    enableHierarchicalNamespace: false
    enableNfsV3: false
    enableSftp: false
    location: primaryLocation
    managedIdentities: {
      systemAssigned: true
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }
    privateEndpoints: [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: storageBlobDnsZone.outputs.resourceId }
          ]
        }
        service: 'blob'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[1] // CapabilityHosts
        tags: tags
      }
    ]
    skuName: 'Standard_LRS'
    tags: tags
  }
}

module aiSearchService 'br/public:avm/res/search/search-service:0.12.0' = {
  name: 'ai-search-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: aiSearchServiceName
    location: primaryLocation
    sku: 'standard'
    diagnosticSettings: [
      {
        metricCategories: [{ category: 'AllMetrics' }]
        name: sendToLogAnalyticsCustomSettingName
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
      }
    ]
    disableLocalAuth: disableApiKeys
    managedIdentities: {
      systemAssigned: true
    }
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    privateEndpoints: [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: searchDnsZone.outputs.resourceId }
          ]
        }
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[1] // CapabilityHosts
        tags: tags
      }
    ]
    publicNetworkAccess: 'Disabled'
    semanticSearch: 'standard'
    tags: tags
  }
}

module keyVault 'br/public:avm/res/key-vault/vault:0.6.1' = {
  name: 'keyvault-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: keyVaultName
    location: primaryLocation
    enablePurgeProtection: false
    enableRbacAuthorization: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }
    privateEndpoints: [
      {
        privateDnsZoneResourceIds: [
          keyVaultDnsZone.outputs.resourceId
        ]
        service: 'vault'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[1] // CapabilityHosts
        tags: tags
      }
    ]
    publicNetworkAccess: 'Disabled'
    tags: tags
  }
}

// ---------- PRIMARY FOUNDRY ACCOUNT (PRIMARY REGION) ----------
// Hosts Agent Service, projects, connections, and capability hosts

var cosmosDbConnectionName = replace(cosmosDbAccountName, '-', '')
var storageConnectionName = replace(storageAccountName, '-', '')
var aiSearchConnectionName = replace(aiSearchServiceName, '-', '')

var foundryConnections = [
  {
    category: 'CosmosDb'
    connectionProperties: { authType: 'AAD' }
    metadata: {
      Type: 'azure_cosmos_db'
      ApiType: 'Azure'
      ApiVersion: '2024-05-15'
      DeploymentApiVersion: '2024-05-15'
      Location: primaryLocation
      ResourceId: cosmosDbAccount.outputs.resourceId
      AccountName: cosmosDbAccountName
      DatabaseName: 'AgentThreads'
    }
    name: cosmosDbConnectionName
    target: cosmosDbAccount.outputs.endpoint
    isSharedToAll: true
  }
  {
    category: 'AzureBlob'
    connectionProperties: { authType: 'AAD' }
    metadata: {
      Type: 'azure_storage_account'
      ApiType: 'Azure'
      ApiVersion: '2023-10-01'
      DeploymentApiVersion: '2023-10-01'
      Location: primaryLocation
      ResourceId: storageAccount.outputs.resourceId
      AccountName: storageAccountName
      ContainerName: 'default'
    }
    name: storageConnectionName
    target: storageAccount.outputs.primaryBlobEndpoint
    isSharedToAll: true
  }
  {
    category: 'CognitiveSearch'
    connectionProperties: { authType: 'AAD' }
    metadata: {
      Type: 'azure_ai_search'
      ApiType: 'Azure'
      ApiVersion: '2024-05-01-preview'
      DeploymentApiVersion: '2023-11-01'
      Location: primaryLocation
      ResourceId: aiSearchService.outputs.resourceId
    }
    name: aiSearchConnectionName
    target: aiSearchService.outputs.endpoint
    isSharedToAll: true
  }
]

var foundryCapabilityHosts capabilityHostType[] = [
  {
    name: 'default'
    capabilityHostKind: 'Agents'
    threadStorageConnectionNames: [cosmosDbConnectionName]
    vectorStoreConnectionNames: [aiSearchConnectionName]
    storageConnectionNames: [storageConnectionName]
    // NOTE: aiServicesConnections is NOT set here because private networking
    // requires all referenced resources to be in the same region as the VNet.
    // Foreign-region models are accessed directly via cross-region private endpoints.
  }
]

var foundryProjects = foundryProjectDeploy ? [
  {
    name: replace(foundryProjectName, ' ', '-')
    location: primaryLocation
    properties: {
      displayName: foundryProjectFriendlyName
      description: foundryProjectDescription
    }
    identity: {
      systemAssigned: true
    }
    roleAssignments: !empty(principalId) ? [
      {
        roleDefinitionIdOrName: 'Azure AI Developer'
        principalType: principalIdType
        principalId: principalId
      }
    ] : []
  }
] : []

module foundryService '../../../infra/cognitive-services/accounts/main.bicep' = {
  name: 'foundry-primary-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: foundryServiceName
    kind: 'AIServices'
    location: primaryLocation
    customSubDomainName: foundryCustomSubDomainName
    disableLocalAuth: disableApiKeys
    allowProjectManagement: true
    diagnosticSettings: [
      {
        name: 'send-to-log-analytics'
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
        logCategoriesAndGroups: [
          { categoryGroup: 'allLogs', enabled: true }
        ]
        metricCategories: [
          { category: 'AllMetrics', enabled: true }
        ]
      }
    ]
    managedIdentities: {
      systemAssigned: true
    }
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
    networkInjections: {
      scenario: 'agent'
      subnetResourceId: virtualNetwork.outputs.subnetResourceIds[3] // AgentSubnet
    }
    privateEndpoints: [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: cognitiveServicesDnsZone.outputs.resourceId }
            { privateDnsZoneResourceId: openAiDnsZone.outputs.resourceId }
            { privateDnsZoneResourceId: aiServicesDnsZone.outputs.resourceId }
          ]
        }
        service: 'account'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[0] // AiServices
      }
    ]
    restrictOutboundNetworkAccess: true
    publicNetworkAccess: 'Disabled'
    sku: 'S0'
    deployments: deployPrimaryModels ? primaryModelDeployments : []
    connections: foundryConnections
    capabilityHosts: foundryCapabilityHosts
    projects: foundryProjects
    tags: tags
  }
}

// ---------- PRIMARY FOUNDRY ROLE ASSIGNMENTS ----------

module foundryRoleAssignments '../../../infra/core/security/role_foundry.bicep' = {
  name: 'foundry-primary-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup, foundryService]
  params: {
    foundryName: foundryServiceName
    roleAssignments: [
      {
        roleDefinitionIdOrName: 'Cognitive Services Contributor'
        principalType: 'ServicePrincipal'
        principalId: aiSearchService.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
        principalType: 'ServicePrincipal'
        principalId: aiSearchService.outputs.systemAssignedMIPrincipalId!
      }
      ...(!empty(principalId) ? [
        {
          roleDefinitionIdOrName: 'Contributor'
          principalType: principalIdType
          principalId: principalId
        }
        {
          roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
          principalType: principalIdType
          principalId: principalId
        }
      ] : [])
    ]
  }
}

// ---------- AI SEARCH ROLE ASSIGNMENTS ----------

module aiSearchRoleAssignments '../../../infra/core/security/role_aisearch.bicep' = {
  name: 'ai-search-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    azureAiSearchName: aiSearchServiceName
    roleAssignments: [
      {
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundryService.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Search Index Data Reader'
        principalType: 'ServicePrincipal'
        principalId: foundryService.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Search Service Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundryService.outputs.systemAssignedMIPrincipalId!
      }
      ...(!empty(principalId) ? [
        {
          roleDefinitionIdOrName: 'Search Service Contributor'
          principalType: principalIdType
          principalId: principalId
        }
        {
          roleDefinitionIdOrName: 'Search Index Data Contributor'
          principalType: principalIdType
          principalId: principalId
        }
      ] : [])
    ]
  }
}

// ---------- STORAGE ACCOUNT ROLE ASSIGNMENTS ----------

module storageAccountRoles '../../../infra/core/security/role_storageaccount.bicep' = {
  name: 'storage-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    azureStorageAccountName: storageAccountName
    roleAssignments: [
      {
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundryService.outputs.systemAssignedMIPrincipalId!
      }
      ...(!empty(principalId) ? [
        {
          roleDefinitionIdOrName: 'Storage Blob Data Contributor'
          principalType: principalIdType
          principalId: principalId
        }
      ] : [])
    ]
  }
}

// ---------- KEY VAULT ROLE ASSIGNMENTS ----------
// Note: RBAC assignments can be configured post-deployment via Azure Portal or CLI:
// az role assignment create --role "Key Vault Secrets Officer" --assignee <foundry-principal-id> --scope <keyvault-resource-id>
// az role assignment create --role "Key Vault Administrator" --assignee <user-principal-id> --scope <keyvault-resource-id>

// ---------- FOREIGN MODEL RESOURCE (FOREIGN REGION) ----------
// A separate Foundry/OpenAI resource in the foreign region hosts models not
// available in the primary region. Public network access is disabled; the AKS
// orchestrator reaches it via a cross-region private endpoint in the primary VNet.

module foreignFoundryService '../../../infra/cognitive-services/accounts/main.bicep' = {
  name: 'foundry-foreign-deployment'
  scope: az.resourceGroup(foreignResourceGroupName)
  dependsOn: [foreignResourceGroup]
  params: {
    name: foreignFoundryName
    kind: 'AIServices'
    location: foreignModelLocation
    customSubDomainName: foreignFoundrySubDomainName
    disableLocalAuth: disableApiKeys
    allowProjectManagement: false
    diagnosticSettings: [
      {
        name: 'send-to-log-analytics'
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
        logCategoriesAndGroups: [
          { categoryGroup: 'allLogs', enabled: true }
        ]
        metricCategories: [
          { category: 'AllMetrics', enabled: true }
        ]
      }
    ]
    managedIdentities: {
      systemAssigned: true
    }
    networkAcls: {
      defaultAction: 'Deny'
      ipRules: []
      virtualNetworkRules: []
    }
    // Cross-region private endpoint is created in the PRIMARY VNet below
    privateEndpoints: []
    restrictOutboundNetworkAccess: true
    publicNetworkAccess: 'Disabled'
    sku: 'S0'
    deployments: deployForeignModels ? foreignModelDeployments : []
    tags: tags
  }
}

// ---------- CROSS-REGION PRIVATE ENDPOINT ----------
// Creates a private endpoint in the primary-region VNet that connects to the
// foreign-region Foundry resource. This enables the AKS orchestrator to call
// foreign models over the Microsoft backbone without public internet exposure.

module foreignModelPrivateEndpoint 'br/public:avm/res/network/private-endpoint:0.11.1' = {
  name: 'foreign-model-pe-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'pep-${foreignFoundryName}-account'
    location: primaryLocation
    privateLinkServiceConnections: [
      {
        name: '${foreignFoundryName}-account'
        properties: {
          privateLinkServiceId: foreignFoundryService.outputs.resourceId
          groupIds: [
            'account'
          ]
        }
      }
    ]
    subnetResourceId: virtualNetwork.outputs.subnetResourceIds[2] // ForeignModels subnet
    privateDnsZoneGroup: {
      privateDnsZoneGroupConfigs: [
        { privateDnsZoneResourceId: cognitiveServicesDnsZone.outputs.resourceId }
        { privateDnsZoneResourceId: openAiDnsZone.outputs.resourceId }
        { privateDnsZoneResourceId: aiServicesDnsZone.outputs.resourceId }
      ]
    }
    tags: tags
  }
}

// ---------- FOREIGN FOUNDRY ROLE ASSIGNMENTS ----------
// Grant the primary Foundry managed identity and the developer access to the
// foreign model resource so the AKS orchestrator can call models.

module foreignFoundryRoleAssignments '../../../infra/core/security/role_foundry.bicep' = {
  name: 'foundry-foreign-role-assignments'
  scope: az.resourceGroup(foreignResourceGroupName)
  dependsOn: [foreignResourceGroup]
  params: {
    foundryName: foreignFoundryName
    roleAssignments: [
      // Primary Foundry identity can invoke foreign models
      {
        roleDefinitionIdOrName: 'Cognitive Services OpenAI User'
        principalType: 'ServicePrincipal'
        principalId: foundryService.outputs.systemAssignedMIPrincipalId!
      }
      // Developer access
      ...(!empty(principalId) ? [
        {
          roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
          principalType: principalIdType
          principalId: principalId
        }
      ] : [])
    ]
  }
}

// ---------- FOUNDRY PROJECT ROLE ASSIGNMENTS TO AI SEARCH ----------

@batchSize(1)
module foundryProjectAiSearchRoles '../../../infra/core/security/role_aisearch.bicep' = [
  for (project, index) in foundryProjects: if (foundryProjectDeploy) {
    name: take('fp-aisch-ra-${project.name}', 64)
    scope: az.resourceGroup(resourceGroupName)
    params: {
      azureAiSearchName: aiSearchServiceName
      roleAssignments: [
        {
          roleDefinitionIdOrName: 'Search Index Data Reader'
          principalType: 'ServicePrincipal'
          principalId: foundryService.outputs.projects[index].?systemAssignedMIPrincipalId ?? ''
        }
        {
          roleDefinitionIdOrName: 'Search Service Contributor'
          principalType: 'ServicePrincipal'
          principalId: foundryService.outputs.projects[index].?systemAssignedMIPrincipalId ?? ''
        }
      ]
    }
  }
]

// ---------- OUTPUTS ----------

// Primary region
output PRIMARY_RESOURCE_GROUP string = primaryResourceGroup.outputs.name
output PRIMARY_LOCATION string = primaryLocation
output VIRTUAL_NETWORK_NAME string = virtualNetwork.outputs.name
output VIRTUAL_NETWORK_RESOURCE_ID string = virtualNetwork.outputs.resourceId
output LOG_ANALYTICS_WORKSPACE_NAME string = logAnalyticsWorkspace.outputs.name

// Primary Foundry
output FOUNDRY_NAME string = foundryService.outputs.name
output FOUNDRY_RESOURCE_ID string = foundryService.outputs.resourceId
output FOUNDRY_ENDPOINT string = foundryService.outputs.endpoint
output FOUNDRY_CAPABILITY_HOSTS array = foundryService.outputs.capabilityHostsOutput

// BYO resources
output COSMOS_DB_NAME string = cosmosDbAccount.outputs.name
output COSMOS_DB_ENDPOINT string = cosmosDbAccount.outputs.endpoint
output STORAGE_ACCOUNT_NAME string = storageAccount.outputs.name
output AI_SEARCH_NAME string = aiSearchService.outputs.name
output KEY_VAULT_NAME string = keyVault.outputs.name
output KEY_VAULT_URI string = keyVault.outputs.uri

// Foreign models
output FOREIGN_RESOURCE_GROUP string = foreignResourceGroup.outputs.name
output FOREIGN_FOUNDRY_NAME string = foreignFoundryService.outputs.name
output FOREIGN_FOUNDRY_RESOURCE_ID string = foreignFoundryService.outputs.resourceId
output FOREIGN_FOUNDRY_ENDPOINT string = foreignFoundryService.outputs.endpoint
output FOREIGN_MODEL_LOCATION string = foreignModelLocation

// Project
output FOUNDRY_PROJECT_DEPLOY bool = foundryProjectDeploy
