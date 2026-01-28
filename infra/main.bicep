targetScope = 'subscription'
extension microsoftGraphV1

import { deploymentType } from './cognitive-services/accounts/main.bicep'
import { capabilityHostType } from './cognitive-services/accounts/capabilityHost/main.bicep'

@sys.description('Name of the the environment which is used to generate a short unique hash used in all resources.')
@minLength(1)
@maxLength(40)
param environmentName string

@sys.description('Location for all resources')
@minLength(1)
@metadata({
  azd: {
    type: 'location'
  }
})
param location string

@sys.description('The Azure resource group where new resources will be deployed.')
@metadata({
  azd: {
    type: 'resourceGroup'
  }
})
param resourceGroupName string = 'rg-${environmentName}'

@sys.description('Array of public IPv4 addresses or CIDR ranges that will be added to the Microsoft Foundry allow-list when azureNetworkIsolation is true.')
param foundryIpAllowList array = []

@sys.description('SKU for the Azure AI Search service. Defaults to standard.')
@allowed([
  'standard'
  'standard2'
  'standard3'
  'storage_optimized_l1'
  'storage_optimized_l2'
])
param azureAiSearchSku string = 'standard'

@sys.description('Number of replicas in the Azure AI Search service. Must be between 1 and 12. Defaults to 1.')
@minValue(1)
@maxValue(12)
param azureAiSearchReplicaCount int = 1

@sys.description('Number of partitions in the Azure AI Search service. Must be 1, 2, 3, 4, 6, or 12. Defaults to 1.')
@allowed([1, 2, 3, 4, 6, 12])
param azureAiSearchPartitionCount int = 1

@sys.description('Id of the user or app to assign application roles.')
param principalId string

@sys.description('Type of the principal referenced by principalId.')
@allowed([
  'User'
  'ServicePrincipal'
])
param principalIdType string = 'User'

@sys.description('Enable network isolation. When false no virtual network, private endpoint or private DNS resources are created and all services expose public endpoints')
param azureNetworkIsolation bool = true

@sys.description('Deploy an Azure Bastion Host to the virtual network. This is required for private endpoint access to the AI Services. Defaults to false.')
param bastionHostDeploy bool = false

@sys.description('Disable API key authentication for AI Services and AI Search. Defaults to false.')
param disableApiKeys bool = false

@sys.description('Deploy the sample model deployments listed in ./sample-model-deployments.json. Defaults to false')
param deploySampleModels bool = false

@sys.description('Override the sample model deployments. When empty, loads from ./sample-model-deployments.json. When provided, uses the custom array instead.')
param deploySampleModelsList deploymentType[] = []

@sys.description('Deploy sample data containers into the Azure Storage Account. Defaults to false.')
param deploySampleData bool = false

@sys.description('Deploy Foundry projects to the Foundry resource. Set to false to skip creation of Microsoft Foundry projects to the Foundry resource. Defaults to false.')
param foundryProjectDeploy bool = false

@sys.description('The name of the Foundry project to create.')
param foundryProjectName string

@sys.description('The description of the Microsoft Foundry project to create.') 
param foundryProjectDescription string

@sys.description('The friendly name of the Microsoft Foundry project to create.')
param foundryProjectFriendlyName string

@sys.description('Use projects defined in sample-foundry-projects.json file instead of the single project parameters. When true, the foundryProject* parameters are ignored. Defaults to false.')
param foundryProjectsFromJson bool = false

@sys.description('Deploy Azure AI Search and all dependent configuration. Set to false to skip its deployment.')
param azureAiSearchDeploy bool = true

@sys.description('Use Azure AI Search as a vector store capability host for AI agents. Requires azureAiSearchDeploy to be true.')
param azureAiSearchCapabilityHost bool = false

@sys.description('Deploy Azure Cosmos DB for thread storage. Set to false to skip its deployment.')
param cosmosDbDeploy bool = false

@sys.description('Use Azure Cosmos DB as a thread storage capability host for AI agents. Requires cosmosDbDeploy to be true.')
param cosmosDbCapabilityHost bool = false

@sys.description('Use Azure Storage Account as a file storage capability host for AI agents. Requires deploySampleData to be true.')
param azureStorageAccountCapabilityHost bool = false

@sys.description('Capability hosts to deploy in the Foundry account. These enable AI agent functionality with thread, vector, and file storage.')
param foundryCapabilityHosts capabilityHostType[] = []

@sys.description('Override the default storage account name. Use the magic string `default` to fall back to the generated name.')
@minLength(3)
@maxLength(24)
param azureStorageAccountName string = 'default'

var abbrs = loadJsonContent('./abbreviations.json')

// tags that should be applied to all resources.
var tags = {
  // Tag all resources with the environment name.
  'azd-env-name': environmentName
}

// Generate a unique token to be used in naming resources.
// Remove linter suppression after using.
#disable-next-line no-unused-vars
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

var effectiveResourceGroupName = !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
var logAnalyticsName = '${abbrs.operationalInsightsWorkspaces}${environmentName}'
var sendTologAnalyticsCustomSettingName = 'send-to-${logAnalyticsName}'
var applicationInsightsName = '${abbrs.insightsComponents}${environmentName}'
var virtualNetworkName = '${abbrs.networkVirtualNetworks}${environmentName}'
// Sample data storage account name - ensure it's ≤ 24 characters as required by Azure
var sampleDataStorageAccountName = azureStorageAccountName == 'default'
  ? take(toLower(replace('${abbrs.storageStorageAccounts}${environmentName}sample', '-', '')), 24)
  : take(toLower(replace('${azureStorageAccountName}sample', '-', '')), 24)
var aiSearchServiceName = '${abbrs.aiSearchSearchServices}${environmentName}'
var foundryServiceName = '${abbrs.foundryAccounts}${environmentName}'
var foundryCustomSubDomainName = toLower(replace(environmentName, '-', ''))
var bastionHostName = '${abbrs.networkBastionHosts}${environmentName}'
var cosmosDbAccountName = '${abbrs.cosmosDBAccounts}${replace(environmentName, '-', '')}'
var networkDefaultAction = azureNetworkIsolation ? 'Deny' : 'Allow'

// Assemble list of sample data containers
var sampleDataContainersArray = loadJsonContent('./sample-data-containers.json')
var sampleDataContainers = [for name in sampleDataContainersArray: {
  name: name
  publicAccess: 'None'
}]

// Load sample OpenAI models from JSON file or use override parameter
var sampleModelDeploymentsFromFile = loadJsonContent('./sample-model-deployments.json')
var sampleModelDeployments deploymentType[] = empty(deploySampleModelsList) ? sampleModelDeploymentsFromFile : deploySampleModelsList

// Transform IP allow list for networkAcls
var foundryIpRules = [for ip in foundryIpAllowList: {
  value: ip
}]

// ---------- PROJECT DEPLOYMENT LOGIC ----------
// Load projects from JSON file for reference
var projectsFromJson = loadJsonContent('./sample-foundry-projects.json')

// Create the effective list of projects to deploy to AI Services
var effectiveProjectList = foundryProjectDeploy 
  ? (foundryProjectsFromJson 
      ? projectsFromJson
      : [
          {
            Name: foundryProjectName
            FriendlyName: foundryProjectFriendlyName
            Description: foundryProjectDescription
          }
        ])
  : []

// Transform the effective project list for AI Services deployment
var foundryServiceProjects = [for project in effectiveProjectList: {
  name: replace(project.Name, ' ', '-')
  location: location
  properties: {
    displayName: project.FriendlyName
    description: project.Description
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
}]

// ---------- RESOURCE GROUP ----------
module resourceGroup 'br/public:avm/res/resources/resource-group:0.4.3' = {
  name: 'resource-group-deployment-${location}'
  params: {
    name: effectiveResourceGroupName
    location: location
    tags: tags
  }
}

// ---------- MONITORING RESOURCES ----------
module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.15.0' = {
  name: 'logAnalytics-workspace-deployment'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
  }
}

module applicationInsights 'br/public:avm/res/insights/component:0.7.1' = {
  name: 'application-insights-deployment'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    name: applicationInsightsName
    location: location
    tags: tags
    workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
  }
}

// ---------- VIRTUAL NETWORK (REQUIRED FOR NETWORK ISOLATION) ----------
// Update subnet definitions to match architecture doc
var subnets = [
  {
    // Default subnet (generally not used)
    name: 'Default'
    addressPrefix: '10.0.0.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // AiServices Subnet (AI Services private endpoints)
    name: 'AiServices'
    addressPrefix: '10.0.1.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Capability Hosts Subnet (Conversation History, Agent Definitions, File Storage, Vector Search)
    name: 'CapabilityHosts'
    addressPrefix: '10.0.2.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Data Subnet (Sample Data Storage Account private endpoint)
    name: 'Data'
    addressPrefix: '10.0.3.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Management Subnet (Log Analytics, Application Insights) - Not used yet
    name: 'Management'
    addressPrefix: '10.0.4.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
  {
    // Bastion Gateway Subnet
    name: 'AzureBastionSubnet'
    addressPrefix: '10.0.255.0/27'
    privateEndpointNetworkPolicies: 'Disabled'
    privateLinkServiceNetworkPolicies: 'Disabled'
  }
]

module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.2' = if (azureNetworkIsolation) {
  name: 'virtualNetwork'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    name: virtualNetworkName
    location: location
    addressPrefixes: [
      '10.0.0.0/16'
    ]
    subnets: subnets
    tags: tags
    ddosProtectionPlanResourceId: null // Corrected parameter name
  }
}

// ---------- PRIVATE DNS ZONES (REQUIRED FOR NETWORK ISOLATION) ----------
module storageBlobPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = if (deploySampleData && azureNetworkIsolation) {
  name: 'storage-blobservice-private-dns-zone'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
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

// Private DNS zones for AI Search
module aiSearchPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = if (azureNetworkIsolation && azureAiSearchDeploy) {
  name: 'ai-search-private-dns-zone'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
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

// Private DNS zones for AI Services
module aiServicesPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = if (azureNetworkIsolation) {
  name: 'ai-services-private-dns-zone'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
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

module aiServicesOpenAiDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = if (azureNetworkIsolation) {
  name: 'ai-services-openai-dns-zone'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
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

module aiServicesAiDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = if (azureNetworkIsolation) {
  name: 'ai-services-ai-dns-zone'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
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

// Private DNS zones for Cosmos DB (for thread storage)
module cosmosDbPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.8.0' = if (azureNetworkIsolation && cosmosDbDeploy) {
  name: 'cosmos-db-private-dns-zone'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
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

// ---------- STORAGE ACCOUNT SAMPLE DATA (OPTIONAL) ----------
module sampleDataStorageAccount 'br/public:avm/res/storage/storage-account:0.31.0' = if (deploySampleData) {
  name: 'sample-data-storage-account-deployment'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    name: sampleDataStorageAccountName
    allowBlobPublicAccess: false
    blobServices: {
      automaticSnapshotPolicyEnabled: false
      containerDeleteRetentionPolicyEnabled: false
      deleteRetentionPolicyEnabled: false
      lastAccessTimeTrackingPolicyEnabled: true
      containers: sampleDataContainers
    }
    diagnosticSettings: [
      {
        metricCategories: [
          {
            category: 'AllMetrics'
          }
        ]
        name: sendTologAnalyticsCustomSettingName
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
      }
    ]
    enableHierarchicalNamespace: false // not supported for AI Foundry
    enableNfsV3: false
    enableSftp: false
    largeFileSharesState: 'Enabled'
    location: location
    managedIdentities: {
      systemAssigned: true
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: networkDefaultAction
    }
    privateEndpoints: azureNetworkIsolation ? [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: storageBlobPrivateDnsZone.outputs.resourceId
            }
          ]
        }
        service: 'blob'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[3] // Data subnet
        tags: tags
      }
    ] : []
    sasExpirationPeriod: '180.00:00:00'
    skuName: 'Standard_LRS'
    tags: tags
  }
}

// ---------- SAMPLE DATA STORAGE ACCOUNT ROLE ASSIGNMENTS (OPTIONAL) ----------
module sampleDataStorageAccountRoles './core/security/role_storageaccount.bicep' = if (deploySampleData) {
  name: 'sample-data-storage-account-role-assignments'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    azureStorageAccountName: sampleDataStorageAccountName
    roleAssignments: [
      // Foundry role assignments
      {
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
        principalType: 'ServicePrincipal'
        principalId: foundryService.outputs.?systemAssignedMIPrincipalId ?? ''
      }
      // AI Search role assignments
      ...(azureAiSearchDeploy ? [
        {
          roleDefinitionIdOrName: 'Storage Blob Data Contributor'
          principalType: 'ServicePrincipal'
          principalId: aiSearchService.outputs.?systemAssignedMIPrincipalId ?? ''
        }
      ] : [])
      // Developer role assignments
      ...(!empty(principalId) ? [
        {
          roleDefinitionIdOrName: 'Storage Blob Data Contributor'
          principalType: principalIdType
          principalId: principalId
        }
        {
          roleDefinitionIdOrName: 'Storage Blob Data Reader'
          principalType: principalIdType
          principalId: principalId
        }
        {
          roleDefinitionIdOrName: 'Storage Account Contributor'
          principalType: principalIdType
          principalId: principalId
        }
      ] : [])
    ]
  }
}

// ---------- AI SEARCH (OPTIONAL) ----------
module aiSearchService 'br/public:avm/res/search/search-service:0.12.0' = if (azureAiSearchDeploy) {
  name: 'ai-search-service-deployment'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    name: aiSearchServiceName
    location: location
    sku: azureAiSearchSku
    replicaCount: azureAiSearchReplicaCount
    partitionCount: azureAiSearchPartitionCount
    diagnosticSettings: [
      {
        metricCategories: [
          { 
            category: 'AllMetrics'
          }
        ]
        name: sendTologAnalyticsCustomSettingName
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
    privateEndpoints: azureNetworkIsolation ? [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: aiSearchPrivateDnsZone.outputs.resourceId
            }
          ]
        }
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[2] // Capability Hosts
        tags: tags
      }
    ] : []
    publicNetworkAccess: azureNetworkIsolation ? 'Disabled' : 'Enabled'
    semanticSearch: 'standard'
    tags: tags
  }
}

// Role assignments (only when Search exists)
var aiSearchRoleAssignmentsArray = azureAiSearchDeploy ? [
  {
    roleDefinitionIdOrName: 'Search Index Data Contributor'
    principalType: 'ServicePrincipal'
    principalId: foundryService.outputs.?systemAssignedMIPrincipalId
  }
  {
    roleDefinitionIdOrName: 'Search Index Data Reader'
    principalType: 'ServicePrincipal'
    principalId: foundryService.outputs.?systemAssignedMIPrincipalId
  }
  {
    roleDefinitionIdOrName: 'Search Service Contributor'
    principalType: 'ServicePrincipal'
    principalId: foundryService.outputs.?systemAssignedMIPrincipalId
  }
  // Developer role assignments
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
] : []

module aiSearchRoleAssignments './core/security/role_aisearch.bicep' = if (azureAiSearchDeploy) {
  name: 'ai-search-role-assignments'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    azureAiSearchName: aiSearchServiceName
    roleAssignments: aiSearchRoleAssignmentsArray
  }
}

// ---------- COSMOS DB (OPTIONAL - FOR THREAD STORAGE) ----------
module cosmosDbAccount 'br/public:avm/res/document-db/database-account:0.18.0' = if (cosmosDbDeploy) {
  name: 'cosmos-db-account-deployment'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    name: cosmosDbAccountName
    location: location
    capabilitiesToAdd: [
      'EnableServerless'
    ]
    diagnosticSettings: [
      {
        metricCategories: [
          {
            category: 'AllMetrics'
          }
        ]
        name: sendTologAnalyticsCustomSettingName
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
      }
    ]
    disableLocalAuthentication: disableApiKeys
    managedIdentities: {
      systemAssigned: true
    }
    networkRestrictions: {
      publicNetworkAccess: azureNetworkIsolation ? 'Disabled' : 'Enabled'
      networkAclBypass: 'AzureServices'
      ipRules: []
      virtualNetworkRules: []
    }
    privateEndpoints: azureNetworkIsolation ? [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: cosmosDbPrivateDnsZone.outputs.resourceId
            }
          ]
        }
        service: 'Sql'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[2] // Capability Hosts subnet
        tags: tags
      }
    ] : []
    sqlDatabases: [
      {
        name: 'AgentThreads'
        containers: [
          {
            name: 'threads'
            paths: [
              '/threadId'
            ]
          }
        ]
      }
    ]
    tags: tags
  }
}

// ---------- FOUNDRY/AI SERVICES ----------
// Deploy Foundry (Cognitive Services) resource with projects (Stage 2)
// Projects are deployed directly into the AI Services resource
// Prepare connections for the Foundry Account
var foundryServiceConnections = concat(azureAiSearchDeploy ? [
  {
    // CognitiveSearch connection
    category: 'CognitiveSearch'
    connectionProperties: {
      authType: 'AAD'
    }
    metadata: {
      Type: 'azure_ai_search'
      ApiType: 'Azure'
      ApiVersion: '2024-05-01-preview'
      DeploymentApiVersion: '2023-11-01'
      Location: location
      ResourceId: aiSearchService.outputs.resourceId
    }
    // Full aiSearchServiceName can't be used because may cause deployment name to be too long
    name: replace(aiSearchServiceName,'-','')
    target: aiSearchService.outputs.endpoint
    isSharedToAll: true
  }
] : [], (deploySampleData) ? [
  {
    // SampleDataStorageAccount connection
    category: 'AzureBlob'
    connectionProperties: {
      authType: 'AAD'
    }
    metadata: {
      Type: 'azure_storage_account'
      ApiType: 'Azure'
      ApiVersion: '2023-10-01'
      DeploymentApiVersion: '2023-10-01'
      Location: location
      ResourceId: sampleDataStorageAccount.outputs.resourceId
      AccountName: sampleDataStorageAccountName
      ContainerName: 'default'
    }
    name: replace(sampleDataStorageAccountName,'-','')
    target: sampleDataStorageAccount.outputs.primaryBlobEndpoint
    isSharedToAll: true
  }
] : [], cosmosDbDeploy ? [
  {
    // CosmosDB connection for thread storage
    category: 'CosmosDb'
    connectionProperties: {
      authType: 'AAD'
    }
    metadata: {
      Type: 'azure_cosmos_db'
      ApiType: 'Azure'
      ApiVersion: '2024-05-15'
      DeploymentApiVersion: '2024-05-15'
      Location: location
      ResourceId: cosmosDbAccount.outputs.resourceId
      AccountName: cosmosDbAccountName
      DatabaseName: 'AgentThreads'
    }
    name: replace(cosmosDbAccountName,'-','')
    target: cosmosDbAccount.outputs.endpoint
    isSharedToAll: true
  }
] : [])

// ---------- CAPABILITY HOSTS CONFIGURATION ----------
// Build the capability host connection names based on the boolean flags
var aiSearchConnectionName = replace(aiSearchServiceName,'-','')
var storageConnectionName = replace(sampleDataStorageAccountName,'-','')
var cosmosDbConnectionName = replace(cosmosDbAccountName,'-','')

// Compute effective capability hosts by combining explicit foundryCapabilityHosts param with auto-configured ones
var autoCapabilityHost capabilityHostType = {
  name: 'default'
  capabilityHostKind: 'Agents'
  threadStorageConnectionNames: cosmosDbDeploy && cosmosDbCapabilityHost ? [cosmosDbConnectionName] : null
  vectorStoreConnectionNames: azureAiSearchDeploy && azureAiSearchCapabilityHost ? [aiSearchConnectionName] : null
  storageConnectionNames: deploySampleData && azureStorageAccountCapabilityHost ? [storageConnectionName] : null
}

// Determine if we should add the auto-configured capability host
var hasAutoCapabilityHost = (cosmosDbDeploy && cosmosDbCapabilityHost) || (azureAiSearchDeploy && azureAiSearchCapabilityHost) || (deploySampleData && azureStorageAccountCapabilityHost)

// Combine explicit and auto-configured capability hosts
var effectiveCapabilityHosts = concat(foundryCapabilityHosts, hasAutoCapabilityHost ? [autoCapabilityHost] : [])

module foundryService './cognitive-services/accounts/main.bicep' = {
  name: 'foundry-service-deployment'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    name: foundryServiceName
    kind: 'AIServices'
    location: location
    customSubDomainName: foundryCustomSubDomainName
    disableLocalAuth: disableApiKeys
    allowProjectManagement: true
    diagnosticSettings: [
      {
        name: 'send-to-log-analytics'
        workspaceResourceId: logAnalyticsWorkspace.outputs.resourceId
        logCategoriesAndGroups: [
          {
            categoryGroup: 'allLogs'
            enabled: true
          }
        ]
        metricCategories: [
          {
            category: 'AllMetrics'
            enabled: true
          }
        ]
      }
    ]
    managedIdentities: {
      systemAssigned: true
    }
    networkAcls: azureNetworkIsolation ? {
      defaultAction: 'Deny'
      ipRules: foundryIpRules
      virtualNetworkRules: []
    } : {
      defaultAction: 'Allow'
      ipRules: []
      virtualNetworkRules: []
    }
    privateEndpoints: azureNetworkIsolation ? [
      {
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: aiServicesPrivateDnsZone.outputs.resourceId
            }
            {
              privateDnsZoneResourceId: aiServicesOpenAiDnsZone.outputs.resourceId
            }
            {
              privateDnsZoneResourceId: aiServicesAiDnsZone.outputs.resourceId
            }
          ]
        }
        service: 'account'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[1] // AiServices Subnet
      }
    ] : []
    restrictOutboundNetworkAccess: azureNetworkIsolation
    publicNetworkAccess: azureNetworkIsolation ? 'Disabled' : 'Enabled'
    sku: 'S0'
    deployments: deploySampleModels ? sampleModelDeployments : []
    connections: foundryServiceConnections
    capabilityHosts: effectiveCapabilityHosts
    projects: foundryServiceProjects
    tags: tags
  }
}

// Add role assignments for AI Services using the role_foundry.bicep module
// This needs to be done after the AI Services account is created to avoid circular dependencies
// between the AI Services account and the AI Search service.
var foundryRoleAssignmentsArray = [
  // search–specific roles only when search is present
  ...(azureAiSearchDeploy ? [
    {
      roleDefinitionIdOrName: 'Cognitive Services Contributor'
      principalType: 'ServicePrincipal'
      principalId: aiSearchService.outputs.?systemAssignedMIPrincipalId
    }
    {
      roleDefinitionIdOrName: 'Cognitive Services OpenAI Contributor'
      principalType: 'ServicePrincipal'
      principalId: aiSearchService.outputs.?systemAssignedMIPrincipalId
    }
  ] : [])
  // Developer role assignments
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

module foundryRoleAssignments './core/security/role_foundry.bicep' = {
  name: 'foundry-role-assignments'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [
    resourceGroup
    foundryService
  ]
  params: {
    foundryName: foundryServiceName
    roleAssignments: foundryRoleAssignmentsArray
  }
}

// ---------- FOUNDRY PROJECT ROLE ASSIGNMENTS TO AI SEARCH ----------
// Add any Search Index Reader and Search Service Contributor roles for each Foundry project
// to the AI Search Account. This ensures Agents created within a project can access indexes in
// the AI Search account.
@batchSize(1)
module foundryProjectToAiSearchRoleAssignments './core/security/role_aisearch.bicep' = [
  for (project,index) in foundryServiceProjects : if (foundryProjectDeploy && azureAiSearchDeploy) {
    name: take('fp-aisch-ra-${project.name}',64)
    scope: az.resourceGroup(effectiveResourceGroupName)
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

module bastionHost 'br/public:avm/res/network/bastion-host:0.8.2' = if (bastionHostDeploy && azureNetworkIsolation) {
  name: 'bastion-host-deployment'
  scope: az.resourceGroup(effectiveResourceGroupName)
  dependsOn: [resourceGroup]
  params: {
    name: bastionHostName
    location: location
    virtualNetworkResourceId: virtualNetwork.outputs.resourceId
    skuName: 'Developer'
    tags: tags
  }
}

output AZURE_RESOURCE_GROUP string = resourceGroup.outputs.name
output AZURE_PRINCIPAL_ID string = principalId
output AZURE_PRINCIPAL_ID_TYPE string = principalIdType

// Output the monitoring resources
output LOG_ANALYTICS_WORKSPACE_NAME string = logAnalyticsWorkspace.outputs.name
output LOG_ANALYTICS_RESOURCE_ID string = logAnalyticsWorkspace.outputs.resourceId
output LOG_ANALYTICS_WORKSPACE_ID string = logAnalyticsWorkspace.outputs.logAnalyticsWorkspaceId
output APPLICATION_INSIGHTS_NAME string = applicationInsights.outputs.name
output APPLICATION_INSIGHTS_RESOURCE_ID string = applicationInsights.outputs.resourceId
output APPLICATION_INSIGHTS_INSTRUMENTATION_KEY string = applicationInsights.outputs.instrumentationKey

// Output the network isolation resources
output AZURE_NETWORK_ISOLATION bool = azureNetworkIsolation
output AZURE_VIRTUAL_NETWORK_NAME string = azureNetworkIsolation ? virtualNetwork.outputs.name : ''
output AZURE_VIRTUAL_NETWORK_RESOURCE_ID string = azureNetworkIsolation ? virtualNetwork.outputs.resourceId : ''

// Output the supporting resources
output AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_NAME string = deploySampleData ? sampleDataStorageAccount.outputs.name : ''
output AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_RESOURCE_ID string = deploySampleData ? sampleDataStorageAccount.outputs.resourceId : ''
output AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_BLOB_ENDPOINT string = deploySampleData ? sampleDataStorageAccount.outputs.primaryBlobEndpoint : ''

// Output the AI resources
output AZURE_DISABLE_API_KEYS bool = disableApiKeys
output AZURE_AI_SEARCH_NAME string = azureAiSearchDeploy ? aiSearchService.outputs.name : ''
output AZURE_AI_SEARCH_ID   string = azureAiSearchDeploy ? aiSearchService.outputs.resourceId : ''
output MICROSOFT_FOUNDRY_NAME string = foundryService.outputs.name
output MICROSOFT_FOUNDRY_ID string = foundryService.outputs.resourceId
output MICROSOFT_FOUNDRY_ENDPOINT string = foundryService.outputs.endpoint
output MICROSOFT_FOUNDRY_RESOURCE_ID string = foundryService.outputs.resourceId

// Output the Foundry project
output MICROSOFT_FOUNDRY_PROJECT_DEPLOY bool = foundryProjectDeploy
output MICROSOFT_FOUNDRY_PROJECTS_FROM_JSON bool = foundryProjectsFromJson
output MICROSOFT_FOUNDRY_PROJECT_NAME string = foundryProjectDeploy ? foundryProjectName : ''
output MICROSOFT_FOUNDRY_PROJECT_DESCRIPTION string = foundryProjectDeploy ? foundryProjectDescription : ''
output MICROSOFT_FOUNDRY_PROJECT_FRIENDLY_NAME string = foundryProjectDeploy ? foundryProjectFriendlyName : ''
output MICROSOFT_FOUNDRY_CAPABILITY_HOSTS array = foundryService.outputs.capabilityHostsOutput

// Output the Cosmos DB resources
output COSMOS_DB_DEPLOY bool = cosmosDbDeploy
output COSMOS_DB_CAPABILITY_HOST bool = cosmosDbCapabilityHost
output COSMOS_DB_NAME string = cosmosDbDeploy ? cosmosDbAccount.outputs.name : ''
output COSMOS_DB_ID string = cosmosDbDeploy ? cosmosDbAccount.outputs.resourceId : ''
output COSMOS_DB_ENDPOINT string = cosmosDbDeploy ? cosmosDbAccount.outputs.endpoint : ''

// Output the capability host configuration
output AZURE_AI_SEARCH_CAPABILITY_HOST bool = azureAiSearchCapabilityHost
output AZURE_STORAGE_ACCOUNT_CAPABILITY_HOST bool = azureStorageAccountCapabilityHost

// Output the Bastion Host resources
output AZURE_BASTION_HOST_DEPLOY bool = bastionHostDeploy
output AZURE_BASTION_HOST_NAME string = bastionHostDeploy && azureNetworkIsolation ? bastionHost.outputs.name : ''
output AZURE_BASTION_HOST_RESOURCE_ID string = bastionHostDeploy && azureNetworkIsolation ? bastionHost.outputs.resourceId : ''
