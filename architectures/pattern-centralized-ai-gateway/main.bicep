targetScope = 'subscription'

// ============================================================================
// Centralized AI Gateway Architecture Pattern
// ============================================================================
// Deploys a centralized AI gateway architecture with:
//   - Primary region (e.g. Australia East): Two Foundry accounts (departments)
//     sharing BYO resources (Cosmos DB, Storage, AI Search) via separate
//     capability hosts, all connected through a centralized API Management
//     (AI Gateway) deployed in the same VNet
//   - Models region (e.g. East US 2): A separate Foundry resource hosting
//     models not available in the primary region, accessed via APIM routing
//
// Key points:
//   - Each Foundry account has its OWN capability host but points to the SAME
//     shared Cosmos DB, Storage, and AI Search resources
//   - APIM acts as a centralized AI Gateway for model routing + governance
//   - Cross-region model access via APIM backend routing to models region
// ============================================================================

import { deploymentType } from '../../infra/cognitive-services/accounts/main.bicep'
import { capabilityHostType } from '../../infra/cognitive-services/accounts/capabilityHost/main.bicep'

// ---------- GLOBAL PARAMETERS ----------

@sys.description('Name of the environment which is used to generate a short unique hash used in all resources.')
@minLength(1)
@maxLength(40)
param environmentName string

@sys.description('Primary region for all data-sovereign resources (Foundry, Agent Service, BYO resources, VNet).')
@minLength(1)
param primaryLocation string = 'australiaeast'

@sys.description('Region where additional model deployments are hosted and accessed via AI Gateway.')
@minLength(1)
param modelsLocation string = 'eastus2'

@sys.description('The Azure resource group where primary-region resources will be deployed.')
param resourceGroupName string = 'rg-${environmentName}'

@sys.description('The Azure resource group where model-region resources will be deployed.')
param modelsResourceGroupName string = 'rg-${environmentName}-models'

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

@sys.description('Deploy model deployments to the primary Foundry accounts. Defaults to true.')
param deployPrimaryModels bool = true

@sys.description('Model deployments for the primary-region Foundry accounts. Only models available in the primary region should be listed.')
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

// ---------- MODELS REGION PARAMETERS ----------

@sys.description('Deploy model deployments to the models-region resource. Defaults to true.')
param deployModelsRegionModels bool = true

@sys.description('Model deployments for the models-region resource. These are models not available in the primary region.')
param modelsRegionDeployments deploymentType[] = [
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

@sys.description('Deploy a Foundry project in each department Foundry account. Defaults to true.')
param foundryProjectDeploy bool = true

@sys.description('Configuration for the first department Foundry account.')
param department1Name string = 'dept-1'

@sys.description('Display name for the first department.')
param department1DisplayName string = 'Department 1'

@sys.description('Configuration for the second department Foundry account.')
param department2Name string = 'dept-2'

@sys.description('Display name for the second department.')
param department2DisplayName string = 'Department 2'

// ---------- APIM PARAMETERS ----------

@sys.description('APIM publisher email address.')
param apimPublisherEmail string = 'apimgmt-noreply@mail.windowsazure.com'

@sys.description('APIM publisher name.')
param apimPublisherName string = 'AI Gateway Admin'

@sys.description('APIM SKU. Must be Developer or Premium for VNet injection. Use Developer for non-production.')
@allowed([
  'Developer'
  'Premium'
])
param apimSku string = 'Developer'

@sys.description('APIM SKU capacity. Defaults to 1.')
param apimSkuCapacity int = 1

// ---------- NAMING ----------

var abbrs = loadJsonContent('../../infra/abbreviations.json')

var tags = {
  'azd-env-name': environmentName
}

var logAnalyticsName = '${abbrs.operationalInsightsWorkspaces}${environmentName}'
var sendToLogAnalyticsCustomSettingName = 'send-to-${logAnalyticsName}'
var virtualNetworkName = '${abbrs.networkVirtualNetworks}${environmentName}'
var foundry1Name = '${abbrs.foundryAccounts}${environmentName}-d1'
var foundry1SubDomain = foundry1Name
var foundry2Name = '${abbrs.foundryAccounts}${environmentName}-d2'
var foundry2SubDomain = foundry2Name
var modelsFoundryName = '${abbrs.foundryAccounts}${environmentName}-mdl'
var modelsFoundrySubDomain = modelsFoundryName
var aiSearchServiceName = '${abbrs.aiSearchSearchServices}${environmentName}'
var storageAccountName = take(toLower(replace('${abbrs.storageStorageAccounts}${environmentName}agent', '-', '')), 24)
var cosmosDbAccountName = '${abbrs.cosmosDBAccounts}${replace(environmentName, '-', '')}agent'
var apimName = '${abbrs.apiManagementService}${environmentName}'

// ---------- RESOURCE GROUPS ----------

module primaryResourceGroup 'br/public:avm/res/resources/resource-group:0.4.3' = {
  name: 'rg-primary-deployment'
  params: {
    name: resourceGroupName
    location: primaryLocation
    tags: tags
  }
}

module modelsResourceGroup 'br/public:avm/res/resources/resource-group:0.4.3' = {
  name: 'rg-models-deployment'
  params: {
    name: modelsResourceGroupName
    location: modelsLocation
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
// Primary-region VNet with subnets for private endpoints, agent compute, APIM,
// capability host resources, and cross-region model access

var subnets = [
  {
    // Subnet 0: Private endpoints for AI Services (Foundry accounts)
    name: 'AiServices'
    addressPrefix: '10.0.1.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Subnet 1: Private endpoints for capability host resources (Cosmos DB, Search, Storage)
    name: 'CapabilityHosts'
    addressPrefix: '10.0.2.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Subnet 2: Cross-region private endpoints (models region)
    name: 'ModelsRegion'
    addressPrefix: '10.0.3.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Subnet 3: Delegated to Microsoft.App/environments for Agent Service (Foundry 1)
    name: 'AgentSubnet1'
    addressPrefix: '10.0.4.0/24'
    delegation: 'Microsoft.App/environments'
  }
  {
    // Subnet 4: Delegated to Microsoft.App/environments for Agent Service (Foundry 2)
    name: 'AgentSubnet2'
    addressPrefix: '10.0.5.0/24'
    delegation: 'Microsoft.App/environments'
  }
  {
    // Subnet 5: APIM VNet injection
    name: 'ApimSubnet'
    addressPrefix: '10.0.6.0/24'
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

module apimDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-apim'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'privatelink.azure-api.net'
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

// ---------- SHARED BYO RESOURCES (PRIMARY REGION) ----------
// These resources are shared across BOTH department Foundry accounts.
// Each Foundry account creates its own connections and capability host
// pointing to these same underlying resources.

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

// ---------- SHARED CONNECTION DEFINITIONS ----------
// Both Foundry accounts use the same connection definitions pointing to shared resources.

var cosmosDbConnectionName = replace(cosmosDbAccountName, '-', '')
var storageConnectionName = replace(storageAccountName, '-', '')
var aiSearchConnectionName = replace(aiSearchServiceName, '-', '')

var sharedConnections = [
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

var sharedCapabilityHosts capabilityHostType[] = [
  {
    name: 'default'
    capabilityHostKind: 'Agents'
    threadStorageConnectionNames: [cosmosDbConnectionName]
    vectorStoreConnectionNames: [aiSearchConnectionName]
    storageConnectionNames: [storageConnectionName]
  }
]

// ---------- DEPARTMENT 1 FOUNDRY ACCOUNT ----------

var dept1Projects = foundryProjectDeploy
  ? [
      {
        name: '${department1Name}-project'
        location: primaryLocation
        properties: {
          displayName: '${department1DisplayName} Project'
          description: 'Foundry project for ${department1DisplayName}'
        }
        identity: {
          systemAssigned: true
        }
        roleAssignments: !empty(principalId)
          ? [
              {
                roleDefinitionIdOrName: 'Azure AI Developer'
                principalType: principalIdType
                principalId: principalId
              }
            ]
          : []
      }
    ]
  : []

module foundry1 '../../infra/cognitive-services/accounts/main.bicep' = {
  name: 'foundry-dept1-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: foundry1Name
    kind: 'AIServices'
    location: primaryLocation
    customSubDomainName: foundry1SubDomain
    disableLocalAuth: disableApiKeys
    allowProjectManagement: true
    diagnosticSettings: [
      {
        name: 'send-to-log-analytics'
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
        logCategoriesAndGroups: [{ categoryGroup: 'allLogs', enabled: true }]
        metricCategories: [{ category: 'AllMetrics', enabled: true }]
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
      subnetResourceId: virtualNetwork.outputs.subnetResourceIds[3] // AgentSubnet1
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
    connections: sharedConnections
    capabilityHosts: sharedCapabilityHosts
    projects: dept1Projects
    tags: tags
  }
}

// ---------- DEPARTMENT 2 FOUNDRY ACCOUNT ----------

var dept2Projects = foundryProjectDeploy
  ? [
      {
        name: '${department2Name}-project'
        location: primaryLocation
        properties: {
          displayName: '${department2DisplayName} Project'
          description: 'Foundry project for ${department2DisplayName}'
        }
        identity: {
          systemAssigned: true
        }
        roleAssignments: !empty(principalId)
          ? [
              {
                roleDefinitionIdOrName: 'Azure AI Developer'
                principalType: principalIdType
                principalId: principalId
              }
            ]
          : []
      }
    ]
  : []

module foundry2 '../../infra/cognitive-services/accounts/main.bicep' = {
  name: 'foundry-dept2-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: foundry2Name
    kind: 'AIServices'
    location: primaryLocation
    customSubDomainName: foundry2SubDomain
    disableLocalAuth: disableApiKeys
    allowProjectManagement: true
    diagnosticSettings: [
      {
        name: 'send-to-log-analytics'
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
        logCategoriesAndGroups: [{ categoryGroup: 'allLogs', enabled: true }]
        metricCategories: [{ category: 'AllMetrics', enabled: true }]
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
      subnetResourceId: virtualNetwork.outputs.subnetResourceIds[4] // AgentSubnet2
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
    connections: sharedConnections
    capabilityHosts: sharedCapabilityHosts
    projects: dept2Projects
    tags: tags
  }
}

// ---------- FOUNDRY 1 ROLE ASSIGNMENTS ----------

module foundry1RoleAssignments '../../infra/core/security/role_foundry.bicep' = {
  name: 'foundry-dept1-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup, foundry1]
  params: {
    foundryName: foundry1Name
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
      ...(!empty(principalId)
        ? [
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
          ]
        : [])
    ]
  }
}

// ---------- FOUNDRY 2 ROLE ASSIGNMENTS ----------

module foundry2RoleAssignments '../../infra/core/security/role_foundry.bicep' = {
  name: 'foundry-dept2-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup, foundry2]
  params: {
    foundryName: foundry2Name
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
      ...(!empty(principalId)
        ? [
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
          ]
        : [])
    ]
  }
}

// ---------- AI SEARCH ROLE ASSIGNMENTS ----------
// Both Foundry managed identities need access to AI Search

module aiSearchRoleAssignments '../../infra/core/security/role_aisearch.bicep' = {
  name: 'ai-search-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    azureAiSearchName: aiSearchServiceName
    roleAssignments: [
      // Foundry 1 identity
      {
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundry1.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Search Index Data Reader'
        principalType: 'ServicePrincipal'
        principalId: foundry1.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Search Service Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundry1.outputs.systemAssignedMIPrincipalId!
      }
      // Foundry 2 identity
      {
        roleDefinitionIdOrName: 'Search Index Data Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundry2.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Search Index Data Reader'
        principalType: 'ServicePrincipal'
        principalId: foundry2.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Search Service Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundry2.outputs.systemAssignedMIPrincipalId!
      }
      ...(!empty(principalId)
        ? [
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
          ]
        : [])
    ]
  }
}

// ---------- STORAGE ACCOUNT ROLE ASSIGNMENTS ----------
// Both Foundry managed identities need access to Storage

module storageAccountRoles '../../infra/core/security/role_storageaccount.bicep' = {
  name: 'storage-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    azureStorageAccountName: storageAccountName
    roleAssignments: [
      {
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundry1.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundry2.outputs.systemAssignedMIPrincipalId!
      }
      ...(!empty(principalId)
        ? [
            {
              roleDefinitionIdOrName: 'Storage Blob Data Contributor'
              principalType: principalIdType
              principalId: principalId
            }
          ]
        : [])
    ]
  }
}

// ---------- API MANAGEMENT (AI GATEWAY) ----------
// Centralized APIM deployed into the VNet with Internal mode.
// Routes requests to both primary-region Foundry models and models-region Foundry.

module apiManagement 'br/public:avm/res/api-management/service:0.14.1' = {
  name: 'apim-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: apimName
    location: primaryLocation
    publisherEmail: apimPublisherEmail
    publisherName: apimPublisherName
    sku: apimSku
    skuCapacity: apimSkuCapacity
    virtualNetworkType: 'Internal'
    subnetResourceId: virtualNetwork.outputs.subnetResourceIds[5] // ApimSubnet
    managedIdentities: {
      systemAssigned: true
    }
    diagnosticSettings: [
      {
        metricCategories: [{ category: 'AllMetrics' }]
        name: sendToLogAnalyticsCustomSettingName
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
      }
    ]
    backends: [
      // Backend for Department 1 Foundry models
      {
        name: 'foundry-dept1-backend'
        url: '${foundry1.outputs.endpoint}openai'
        type: 'Single'
        tls: {
          validateCertificateChain: true
          validateCertificateName: true
        }
      }
      // Backend for Department 2 Foundry models
      {
        name: 'foundry-dept2-backend'
        url: '${foundry2.outputs.endpoint}openai'
        type: 'Single'
        tls: {
          validateCertificateChain: true
          validateCertificateName: true
        }
      }
      // Backend for models-region Foundry
      {
        name: 'models-region-backend'
        url: '${modelsFoundry.outputs.endpoint}openai'
        type: 'Single'
        tls: {
          validateCertificateChain: true
          validateCertificateName: true
        }
      }
    ]
    apis: [
      {
        displayName: 'AI Gateway - OpenAI'
        name: 'ai-gateway-openai'
        path: 'openai'
        protocols: [
          'https'
        ]
        serviceUrl: '${foundry1.outputs.endpoint}openai'
        subscriptionRequired: false
      }
    ]
    policies: [
      {
        format: 'xml'
        value: '<policies><inbound><base /><authentication-managed-identity resource="https://cognitiveservices.azure.com" /></inbound><backend><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>'
      }
    ]
    tags: tags
  }
}

// ---------- APIM ROLE ASSIGNMENTS ----------
// APIM managed identity needs Cognitive Services User on both primary Foundry accounts
// and the models-region Foundry to invoke models.

module apimFoundry1Roles '../../infra/core/security/role_foundry.bicep' = {
  name: 'apim-foundry1-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    foundryName: foundry1Name
    roleAssignments: [
      {
        roleDefinitionIdOrName: 'Cognitive Services OpenAI User'
        principalType: 'ServicePrincipal'
        principalId: apiManagement.outputs.systemAssignedMIPrincipalId!
      }
    ]
  }
}

module apimFoundry2Roles '../../infra/core/security/role_foundry.bicep' = {
  name: 'apim-foundry2-role-assignments'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    foundryName: foundry2Name
    roleAssignments: [
      {
        roleDefinitionIdOrName: 'Cognitive Services OpenAI User'
        principalType: 'ServicePrincipal'
        principalId: apiManagement.outputs.systemAssignedMIPrincipalId!
      }
    ]
  }
}

// ---------- MODELS REGION FOUNDRY ----------
// A separate Foundry resource in the models region hosts models not available
// in the primary region. APIM routes to this via cross-region private endpoint.

module modelsFoundry '../../infra/cognitive-services/accounts/main.bicep' = {
  name: 'foundry-models-deployment'
  scope: az.resourceGroup(modelsResourceGroupName)
  dependsOn: [modelsResourceGroup]
  params: {
    name: modelsFoundryName
    kind: 'AIServices'
    location: modelsLocation
    customSubDomainName: modelsFoundrySubDomain
    disableLocalAuth: disableApiKeys
    allowProjectManagement: false
    diagnosticSettings: [
      {
        name: 'send-to-log-analytics'
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
        logCategoriesAndGroups: [{ categoryGroup: 'allLogs', enabled: true }]
        metricCategories: [{ category: 'AllMetrics', enabled: true }]
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
    privateEndpoints: []
    restrictOutboundNetworkAccess: true
    publicNetworkAccess: 'Disabled'
    sku: 'S0'
    deployments: deployModelsRegionModels ? modelsRegionDeployments : []
    tags: tags
  }
}

// ---------- CROSS-REGION PRIVATE ENDPOINT ----------
// Creates a private endpoint in the primary-region VNet that connects to the
// models-region Foundry resource. APIM reaches models-region via this PE.

module modelsPrivateEndpoint 'br/public:avm/res/network/private-endpoint:0.11.1' = {
  name: 'models-region-pe-deployment'
  scope: az.resourceGroup(resourceGroupName)
  dependsOn: [primaryResourceGroup]
  params: {
    name: 'pep-${modelsFoundryName}-account'
    location: primaryLocation
    privateLinkServiceConnections: [
      {
        name: '${modelsFoundryName}-account'
        properties: {
          privateLinkServiceId: modelsFoundry.outputs.resourceId
          groupIds: [
            'account'
          ]
        }
      }
    ]
    subnetResourceId: virtualNetwork.outputs.subnetResourceIds[2] // ModelsRegion subnet
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

// ---------- MODELS REGION ROLE ASSIGNMENTS ----------
// APIM and both primary Foundry identities need access to models-region

module modelsFoundryRoleAssignments '../../infra/core/security/role_foundry.bicep' = {
  name: 'foundry-models-role-assignments'
  scope: az.resourceGroup(modelsResourceGroupName)
  dependsOn: [modelsResourceGroup]
  params: {
    foundryName: modelsFoundryName
    roleAssignments: [
      // APIM can invoke models in the models region
      {
        roleDefinitionIdOrName: 'Cognitive Services OpenAI User'
        principalType: 'ServicePrincipal'
        principalId: apiManagement.outputs.systemAssignedMIPrincipalId!
      }
      // Foundry 1 identity can also invoke models
      {
        roleDefinitionIdOrName: 'Cognitive Services OpenAI User'
        principalType: 'ServicePrincipal'
        principalId: foundry1.outputs.systemAssignedMIPrincipalId!
      }
      // Foundry 2 identity can also invoke models
      {
        roleDefinitionIdOrName: 'Cognitive Services OpenAI User'
        principalType: 'ServicePrincipal'
        principalId: foundry2.outputs.systemAssignedMIPrincipalId!
      }
      // Developer access
      ...(!empty(principalId)
        ? [
            {
              roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
              principalType: principalIdType
              principalId: principalId
            }
          ]
        : [])
    ]
  }
}

// ---------- PROJECT-LEVEL ROLE ASSIGNMENTS TO AI SEARCH ----------

@batchSize(1)
module foundry1ProjectAiSearchRoles '../../infra/core/security/role_aisearch.bicep' = [
  for (project, index) in dept1Projects: if (foundryProjectDeploy) {
    name: take('f1p-aisch-ra-${project.name}', 64)
    scope: az.resourceGroup(resourceGroupName)
    params: {
      azureAiSearchName: aiSearchServiceName
      roleAssignments: [
        {
          roleDefinitionIdOrName: 'Search Index Data Reader'
          principalType: 'ServicePrincipal'
          principalId: foundry1.outputs.projects[index].?systemAssignedMIPrincipalId ?? ''
        }
        {
          roleDefinitionIdOrName: 'Search Service Contributor'
          principalType: 'ServicePrincipal'
          principalId: foundry1.outputs.projects[index].?systemAssignedMIPrincipalId ?? ''
        }
      ]
    }
  }
]

@batchSize(1)
module foundry2ProjectAiSearchRoles '../../infra/core/security/role_aisearch.bicep' = [
  for (project, index) in dept2Projects: if (foundryProjectDeploy) {
    name: take('f2p-aisch-ra-${project.name}', 64)
    scope: az.resourceGroup(resourceGroupName)
    params: {
      azureAiSearchName: aiSearchServiceName
      roleAssignments: [
        {
          roleDefinitionIdOrName: 'Search Index Data Reader'
          principalType: 'ServicePrincipal'
          principalId: foundry2.outputs.projects[index].?systemAssignedMIPrincipalId ?? ''
        }
        {
          roleDefinitionIdOrName: 'Search Service Contributor'
          principalType: 'ServicePrincipal'
          principalId: foundry2.outputs.projects[index].?systemAssignedMIPrincipalId ?? ''
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

// Department 1 Foundry
output FOUNDRY_DEPT1_NAME string = foundry1.outputs.name
output FOUNDRY_DEPT1_RESOURCE_ID string = foundry1.outputs.resourceId
output FOUNDRY_DEPT1_ENDPOINT string = foundry1.outputs.endpoint
output FOUNDRY_DEPT1_CAPABILITY_HOSTS array = foundry1.outputs.capabilityHostsOutput

// Department 2 Foundry
output FOUNDRY_DEPT2_NAME string = foundry2.outputs.name
output FOUNDRY_DEPT2_RESOURCE_ID string = foundry2.outputs.resourceId
output FOUNDRY_DEPT2_ENDPOINT string = foundry2.outputs.endpoint
output FOUNDRY_DEPT2_CAPABILITY_HOSTS array = foundry2.outputs.capabilityHostsOutput

// Shared BYO resources
output COSMOS_DB_NAME string = cosmosDbAccount.outputs.name
output COSMOS_DB_ENDPOINT string = cosmosDbAccount.outputs.endpoint
output STORAGE_ACCOUNT_NAME string = storageAccount.outputs.name
output AI_SEARCH_NAME string = aiSearchService.outputs.name

// API Management (AI Gateway)
output APIM_NAME string = apiManagement.outputs.name
output APIM_RESOURCE_ID string = apiManagement.outputs.resourceId

// Models region
output MODELS_RESOURCE_GROUP string = modelsResourceGroup.outputs.name
output MODELS_FOUNDRY_NAME string = modelsFoundry.outputs.name
output MODELS_FOUNDRY_RESOURCE_ID string = modelsFoundry.outputs.resourceId
output MODELS_FOUNDRY_ENDPOINT string = modelsFoundry.outputs.endpoint
output MODELS_LOCATION string = modelsLocation

// Projects
output FOUNDRY_PROJECT_DEPLOY bool = foundryProjectDeploy
