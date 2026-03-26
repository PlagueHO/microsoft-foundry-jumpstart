targetScope = 'subscription'

// ============================================================================
// Cross-Region Web App with Foundry Agent Service
// ============================================================================
// Deploys a cross-region architecture:
//   - Foundry V2 (AI Services) in East US 2 with Agent Service
//   - VNet in Australia East with cross-region private endpoints to all
//     Foundry-region resources
//   - Azure Web App (.NET 10) in Australia East integrated into the VNet
//   - BYO resources (Cosmos DB, Storage, AI Search) co-located with Foundry
//
// Demonstrates cross-region private endpoint connectivity where the VNet and
// consuming application reside in a different region to the Foundry resource.
// ============================================================================

import { deploymentType } from '../../../infra/cognitive-services/accounts/main.bicep'
import { capabilityHostType } from '../../../infra/cognitive-services/accounts/capabilityHost/main.bicep'

// ---------- GLOBAL PARAMETERS ----------

@sys.description('Name of the environment which is used to generate a short unique hash used in all resources.')
@minLength(1)
@maxLength(40)
param environmentName string

@sys.description('Region for the Foundry resource and BYO resources (Cosmos DB, Storage, AI Search).')
@minLength(1)
param foundryLocation string = 'eastus2'

@sys.description('Region for the VNet, Web App, and private endpoints.')
@minLength(1)
param vnetLocation string = 'australiaeast'

@sys.description('The Azure resource group where Foundry and BYO resources are deployed.')
param foundryResourceGroupName string = 'rg-${environmentName}-foundry'

@sys.description('The Azure resource group where VNet and Web App are deployed.')
param vnetResourceGroupName string = 'rg-${environmentName}-webapp'

@sys.description('Id of the user or app to assign application roles.')
param principalId string

@sys.description('Type of the principal referenced by principalId.')
@allowed([
  'User'
  'ServicePrincipal'
])
param principalIdType string = 'User'

@sys.description('Disable API key authentication for all Cognitive Services resources.')
param disableApiKeys bool = false

// ---------- FOUNDRY PARAMETERS ----------

@sys.description('Deploy model deployments to the Foundry account.')
param deployModels bool = true

@sys.description('Model deployments for the Foundry account.')
param modelDeployments deploymentType[] = [
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

// ---------- PROJECT PARAMETERS ----------

@sys.description('Deploy a Foundry project.')
param foundryProjectDeploy bool = true

@sys.description('The name of the Foundry project.')
param foundryProjectName string = 'agent-project'

@sys.description('The display name of the Foundry project.')
param foundryProjectFriendlyName string = 'Cross-Region Agent Project'

@sys.description('The description of the Foundry project.')
param foundryProjectDescription string = 'Foundry project accessed by a cross-region Web App via private endpoint'

// ---------- WEB APP PARAMETERS ----------

@sys.description('The SKU for the App Service Plan. P1v3 or higher required for VNet integration.')
param appServicePlanSku string = 'P1v3'

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
var aiSearchServiceName = '${abbrs.aiSearchSearchServices}${environmentName}'
var storageAccountName = take(toLower(replace('${abbrs.storageStorageAccounts}${environmentName}agent', '-', '')), 24)
var cosmosDbAccountName = '${abbrs.cosmosDBAccounts}${replace(environmentName, '-', '')}agent'
var appServicePlanName = '${abbrs.webServerFarms}${environmentName}'
var webAppName = '${abbrs.webSitesAppService}${environmentName}'

// ---------- RESOURCE GROUPS ----------

module foundryResourceGroup 'br/public:avm/res/resources/resource-group:0.4.3' = {
  name: 'rg-foundry-deployment'
  params: {
    name: foundryResourceGroupName
    location: foundryLocation
    tags: tags
  }
}

module vnetResourceGroup 'br/public:avm/res/resources/resource-group:0.4.3' = {
  name: 'rg-vnet-deployment'
  params: {
    name: vnetResourceGroupName
    location: vnetLocation
    tags: tags
  }
}

// ---------- MONITORING ----------

module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.15.0' = {
  name: 'log-analytics-deployment'
  scope: az.resourceGroup(foundryResourceGroupName)
  dependsOn: [foundryResourceGroup]
  params: {
    name: logAnalyticsName
    location: foundryLocation
    tags: tags
  }
}

// ---------- VIRTUAL NETWORK (AUSTRALIA EAST) ----------

var subnets = [
  {
    // Subnet for cross-region private endpoints to Foundry and BYO resources
    name: 'PrivateEndpoints'
    addressPrefix: '10.0.1.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Subnet delegated to Web App for VNet integration (outbound)
    name: 'WebAppIntegration'
    addressPrefix: '10.0.2.0/24'
    delegation: 'Microsoft.Web/serverFarms'
  }
]

module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.2' = {
  name: 'vnet-deployment'
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
  params: {
    name: virtualNetworkName
    location: vnetLocation
    addressPrefixes: [
      '10.0.0.0/16'
    ]
    subnets: subnets
    tags: tags
  }
}

// ---------- PRIVATE DNS ZONES (LINKED TO AUSTRALIA EAST VNET) ----------
// DNS zones are created in the VNet resource group so the Web App resolves
// Foundry-region endpoints to private IP addresses via the cross-region PEs.

module cognitiveServicesDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-cognitiveservices'
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
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
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
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
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
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
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
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
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
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
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
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

module webAppDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = {
  name: 'dns-webapp'
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
  params: {
    name: 'privatelink.azurewebsites.net'
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

// ---------- BYO RESOURCES (EAST US 2) ----------
// Cosmos DB for thread storage, Storage Account for file storage, AI Search
// for vector store. All co-located with Foundry in East US 2 but accessed
// via cross-region private endpoints in the Australia East VNet.

module cosmosDbAccount 'br/public:avm/res/document-db/database-account:0.18.0' = {
  name: 'cosmos-db-deployment'
  scope: az.resourceGroup(foundryResourceGroupName)
  dependsOn: [foundryResourceGroup]
  params: {
    name: cosmosDbAccountName
    location: foundryLocation
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
    // Cross-region PE: resource in East US 2, PE in Australia East VNet
    privateEndpoints: [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: cosmosDbDnsZone.outputs.resourceId }
          ]
        }
        service: 'Sql'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[0] // PrivateEndpoints
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
  scope: az.resourceGroup(foundryResourceGroupName)
  dependsOn: [foundryResourceGroup]
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
    location: foundryLocation
    managedIdentities: {
      systemAssigned: true
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }
    // Cross-region PE: resource in East US 2, PE in Australia East VNet
    privateEndpoints: [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: storageBlobDnsZone.outputs.resourceId }
          ]
        }
        service: 'blob'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[0] // PrivateEndpoints
        tags: tags
      }
    ]
    skuName: 'Standard_LRS'
    tags: tags
  }
}

module aiSearchService 'br/public:avm/res/search/search-service:0.12.0' = {
  name: 'ai-search-deployment'
  scope: az.resourceGroup(foundryResourceGroupName)
  dependsOn: [foundryResourceGroup]
  params: {
    name: aiSearchServiceName
    location: foundryLocation
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
    // Cross-region PE: resource in East US 2, PE in Australia East VNet
    privateEndpoints: [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: searchDnsZone.outputs.resourceId }
          ]
        }
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[0] // PrivateEndpoints
        tags: tags
      }
    ]
    publicNetworkAccess: 'Disabled'
    semanticSearch: 'standard'
    tags: tags
  }
}

// ---------- FOUNDRY ACCOUNT (EAST US 2) ----------

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
      Location: foundryLocation
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
      Location: foundryLocation
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
      Location: foundryLocation
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
  }
]

var foundryProjects = foundryProjectDeploy
  ? [
      {
        name: replace(foundryProjectName, ' ', '-')
        location: foundryLocation
        properties: {
          displayName: foundryProjectFriendlyName
          description: foundryProjectDescription
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

module foundryService '../../../infra/cognitive-services/accounts/main.bicep' = {
  name: 'foundry-deployment'
  scope: az.resourceGroup(foundryResourceGroupName)
  dependsOn: [foundryResourceGroup]
  params: {
    name: foundryServiceName
    kind: 'AIServices'
    location: foundryLocation
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
    // Cross-region PE: Foundry in East US 2, PE in Australia East VNet
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
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[0] // PrivateEndpoints in Australia East
      }
    ]
    restrictOutboundNetworkAccess: true
    publicNetworkAccess: 'Disabled'
    sku: 'S0'
    deployments: deployModels ? modelDeployments : []
    connections: foundryConnections
    capabilityHosts: foundryCapabilityHosts
    projects: foundryProjects
    tags: tags
  }
}

// ---------- WEB APP (AUSTRALIA EAST) ----------
// App Service Plan and Web App are created BEFORE Foundry role assignments
// so the Web App managed identity can be referenced in the RBAC assignments.

module appServicePlan 'br/public:avm/res/web/serverfarm:0.7.0' = {
  name: 'app-service-plan-deployment'
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
  params: {
    name: appServicePlanName
    location: vnetLocation
    kind: 'Linux'
    reserved: true
    skuName: appServicePlanSku
    tags: tags
  }
}

module webApp 'br/public:avm/res/web/site:0.22.0' = {
  name: 'web-app-deployment'
  scope: az.resourceGroup(vnetResourceGroupName)
  dependsOn: [vnetResourceGroup]
  params: {
    name: webAppName
    location: vnetLocation
    kind: 'app,linux'
    serverFarmResourceId: appServicePlan.outputs.resourceId
    managedIdentities: {
      systemAssigned: true
    }
    siteConfig: {
      linuxFxVersion: 'DOTNETCORE|10.0'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'AZURE_FOUNDRY_PROJECT_ENDPOINT'
          value: foundryService.outputs.endpoint
        }
        {
          name: 'AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME'
          value: 'gpt-4o'
        }
      ]
    }
    httpsOnly: true
    publicNetworkAccess: 'Disabled'
    // VNet integration for outbound traffic through Australia East VNet
    virtualNetworkSubnetResourceId: virtualNetwork.outputs.subnetResourceIds[1] // WebAppIntegration
    // Private endpoint for inbound traffic
    privateEndpoints: [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            { privateDnsZoneResourceId: webAppDnsZone.outputs.resourceId }
          ]
        }
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[0] // PrivateEndpoints
        tags: tags
      }
    ]
    diagnosticSettings: [
      {
        name: sendToLogAnalyticsCustomSettingName
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
        metricCategories: [
          { category: 'AllMetrics', enabled: true }
        ]
      }
    ]
    tags: tags
  }
}

// ---------- FOUNDRY ROLE ASSIGNMENTS ----------

module foundryRoleAssignments '../../../infra/core/security/role_foundry.bicep' = {
  name: 'foundry-role-assignments'
  scope: az.resourceGroup(foundryResourceGroupName)
  dependsOn: [foundryResourceGroup]
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
      // Web App managed identity gets access to invoke agents
      {
        roleDefinitionIdOrName: 'Cognitive Services OpenAI User'
        principalType: 'ServicePrincipal'
        principalId: webApp.outputs.systemAssignedMIPrincipalId!
      }
      {
        roleDefinitionIdOrName: 'Azure AI Developer'
        principalType: 'ServicePrincipal'
        principalId: webApp.outputs.systemAssignedMIPrincipalId!
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

module aiSearchRoleAssignments '../../../infra/core/security/role_aisearch.bicep' = {
  name: 'ai-search-role-assignments'
  scope: az.resourceGroup(foundryResourceGroupName)
  dependsOn: [foundryResourceGroup]
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

module storageAccountRoles '../../../infra/core/security/role_storageaccount.bicep' = {
  name: 'storage-role-assignments'
  scope: az.resourceGroup(foundryResourceGroupName)
  dependsOn: [foundryResourceGroup]
  params: {
    azureStorageAccountName: storageAccountName
    roleAssignments: [
      {
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundryService.outputs.systemAssignedMIPrincipalId!
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

// ---------- FOUNDRY PROJECT ROLE ASSIGNMENTS ----------

@batchSize(1)
module foundryProjectAiSearchRoles '../../../infra/core/security/role_aisearch.bicep' = [
  for (project, index) in foundryProjects: if (foundryProjectDeploy) {
    name: take('fp-aisch-ra-${project.name}', 64)
    scope: az.resourceGroup(foundryResourceGroupName)
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

// Foundry
output FOUNDRY_RESOURCE_GROUP string = foundryResourceGroup.outputs.name
output FOUNDRY_LOCATION string = foundryLocation
output FOUNDRY_NAME string = foundryService.outputs.name
output FOUNDRY_RESOURCE_ID string = foundryService.outputs.resourceId
output FOUNDRY_ENDPOINT string = foundryService.outputs.endpoint

// VNet & Web App
output VNET_RESOURCE_GROUP string = vnetResourceGroup.outputs.name
output VNET_LOCATION string = vnetLocation
output VIRTUAL_NETWORK_NAME string = virtualNetwork.outputs.name
output WEB_APP_NAME string = webApp.outputs.name
output WEB_APP_DEFAULT_HOSTNAME string = webApp.outputs.defaultHostname
output WEB_APP_RESOURCE_ID string = webApp.outputs.resourceId

// BYO resources
output COSMOS_DB_NAME string = cosmosDbAccount.outputs.name
output STORAGE_ACCOUNT_NAME string = storageAccount.outputs.name
output AI_SEARCH_NAME string = aiSearchService.outputs.name

// Monitoring
output LOG_ANALYTICS_WORKSPACE_NAME string = logAnalyticsWorkspace.outputs.name
