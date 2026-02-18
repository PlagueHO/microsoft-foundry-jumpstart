metadata name = 'Cognitive Services Project Capability Host'
metadata description = '''
This module creates a capability host in a Cognitive Services project.
Project-level capability hosts configure per-project storage backends for threads, vectors, and files,
allowing different projects to use different storage connections.
See: https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects/capabilityhosts
'''

// ================ //
// Parameters       //
// ================ //

@sys.description('Required. Name of the capability host to create.')
param name string

@sys.description('Required. The name of the parent Cognitive Services account.')
param accountName string

@sys.description('Required. The name of the parent Foundry Project.')
param projectName string

@sys.description('Optional. Array of AI services connection resource IDs. These connections reference AI services available to the project.')
param aiServicesConnections string[]?

@sys.description('Optional. Array of connection resource IDs for thread storage. These connections store conversation thread data for agents.')
param threadStorageConnections string[]?

@sys.description('Optional. Array of connection resource IDs for vector stores. These connections store vector embeddings for semantic search.')
param vectorStoreConnections string[]?

@sys.description('Optional. Array of connection resource IDs for file storage. These connections store files uploaded to agents.')
param storageConnections string[]?

// ============================= //
// Existing resources references //
// ============================= //

resource parentAccount 'Microsoft.CognitiveServices/accounts@2025-10-01-preview' existing = {
  name: accountName
}

resource parentProject 'Microsoft.CognitiveServices/accounts/projects@2025-10-01-preview' existing = {
  parent: parentAccount
  name: projectName
}

// ============== //
// Resources      //
// ============== //

resource capabilityHost 'Microsoft.CognitiveServices/accounts/projects/capabilityHosts@2025-10-01-preview' = {
  name: name
  parent: parentProject
  properties: {
    aiServicesConnections: aiServicesConnections
    threadStorageConnections: threadStorageConnections
    vectorStoreConnections: vectorStoreConnections
    storageConnections: storageConnections
  }
}

// ============ //
// Outputs      //
// ============ //

@sys.description('The resource ID of the project capability host.')
output resourceId string = capabilityHost.id

@sys.description('The name of the project capability host.')
output name string = capabilityHost.name

@sys.description('The name of the resource group the project capability host was created in.')
output resourceGroupName string = resourceGroup().name

// ================ //
// Definitions      //
// ================ //

@export()
@sys.description('The type for a project-level capability host configuration.')
type projectCapabilityHostType = {
  @sys.description('Required. Name of the capability host to create.')
  name: string

  @sys.description('Optional. Array of AI services connection names. These must match connection names defined in the account or project connections.')
  aiServicesConnectionNames: string[]?

  @sys.description('Optional. Array of connection names for thread storage. These must match connection names defined in the account or project connections.')
  threadStorageConnectionNames: string[]?

  @sys.description('Optional. Array of connection names for vector stores. These must match connection names defined in the account or project connections.')
  vectorStoreConnectionNames: string[]?

  @sys.description('Optional. Array of connection names for file storage. These must match connection names defined in the account or project connections.')
  storageConnectionNames: string[]?
}

@export()
@sys.description('The output type for a project-level capability host.')
type projectCapabilityHostOutputType = {
  @sys.description('The name of the project capability host.')
  name: string

  @sys.description('The resource ID of the project capability host.')
  resourceId: string
}
