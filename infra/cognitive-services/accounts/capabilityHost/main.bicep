metadata name = 'Cognitive Services Capability Hosts'
metadata description = '''
This module creates a capability host in a Cognitive Services account.
Capability hosts enable AI agent functionality by configuring storage for threads, vectors, and files.
See: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/capability-hosts
'''

// ================ //
// Parameters       //
// ================ //

@sys.description('Required. Name of the capability host to create.')
param name string

@sys.description('Required. The name of the parent Cognitive Services account. Required if the template is used in a standalone deployment.')
param accountName string

@sys.description('Required. The kind of capability host. Currently only "Agents" is supported.')
@allowed([
  'Agents'
])
param capabilityHostKind string = 'Agents'

@sys.description('Optional. Array of connection resource IDs for thread storage. These connections store conversation thread data for agents.')
param threadStorageConnections string[]?

@sys.description('Optional. Array of connection resource IDs for vector stores. These connections store vector embeddings for semantic search.')
param vectorStoreConnections string[]?

@sys.description('Optional. Array of connection resource IDs for file storage. These connections store files uploaded to agents.')
param storageConnections string[]?

// ============================= //
// Existing resources references //
// ============================= //

resource cognitiveServicesAccount 'Microsoft.CognitiveServices/accounts@2025-10-01-preview' existing = {
  name: accountName
}

// ============== //
// Resources      //
// ============== //

resource capabilityHost 'Microsoft.CognitiveServices/accounts/capabilityHosts@2025-10-01-preview' = {
  name: name
  parent: cognitiveServicesAccount
  properties: {
    capabilityHostKind: capabilityHostKind
    threadStorageConnections: threadStorageConnections
    vectorStoreConnections: vectorStoreConnections
    storageConnections: storageConnections
  }
}

// ============ //
// Outputs      //
// ============ //

@sys.description('The resource ID of the capability host.')
output resourceId string = capabilityHost.id

@sys.description('The name of the capability host.')
output name string = capabilityHost.name

@sys.description('The name of the resource group the capability host was created in.')
output resourceGroupName string = resourceGroup().name

// ================ //
// Definitions      //
// ================ //

@export()
@sys.description('The type for a capability host configuration.')
type capabilityHostType = {
  @sys.description('Required. Name of the capability host to create.')
  name: string

  @sys.description('Required. The kind of capability host. Currently only "Agents" is supported.')
  capabilityHostKind: 'Agents'

  @sys.description('Optional. Array of connection names for thread storage. These must match connection names defined in the connections parameter.')
  threadStorageConnectionNames: string[]?

  @sys.description('Optional. Array of connection names for vector stores. These must match connection names defined in the connections parameter.')
  vectorStoreConnectionNames: string[]?

  @sys.description('Optional. Array of connection names for file storage. These must match connection names defined in the connections parameter.')
  storageConnectionNames: string[]?
}
