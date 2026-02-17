metadata name = 'Cognitive Services Application Agent Deployment'
metadata description = '''
This module creates an agent deployment within an application in a Cognitive Services project.
Agent deployments define how agents within an application are deployed and scaled.
See: https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects/applications/agentdeployments
'''

// ================ //
// Parameters       //
// ================ //

@sys.description('Required. The name of the parent Cognitive Services account.')
param accountName string

@sys.description('Required. The name of the parent project.')
param projectName string

@sys.description('Required. The name of the parent application.')
param applicationName string

@sys.description('Required. The name of the agent deployment.')
param name string

@sys.description('Required. The type of deployment. Use "Hosted" for hosted deployments with scaling or "Managed" for managed deployments.')
@allowed([
  'Hosted'
  'Managed'
])
param deploymentType string

@sys.description('Optional. The display name of the deployment.')
param displayName string?

@sys.description('Optional. The description of the deployment.')
param description string?

@sys.description('Optional. The unique identifier of the deployment.')
param deploymentId string?

@sys.description('Optional. List of agent:version pairs deployed in this deployment.')
param agents versionedAgentReferenceType[]?

@sys.description('Optional. Protocol types and versions exposed by this deployment.')
param protocols agentProtocolVersionType[]?

@sys.description('Optional. The minimum number of replicas for hosted deployments. Only applicable when deploymentType is "Hosted".')
@minValue(0)
param minReplicas int?

@sys.description('Optional. The maximum number of replicas for hosted deployments. Only applicable when deploymentType is "Hosted".')
@minValue(0)
param maxReplicas int?

@sys.description('Optional. Tags for the deployment.')
param tags object?

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

resource parentApplication 'Microsoft.CognitiveServices/accounts/projects/applications@2025-10-01-preview' existing = {
  parent: parentProject
  name: applicationName
}

// ============== //
// Resources      //
// ============== //

resource agentDeployment 'Microsoft.CognitiveServices/accounts/projects/applications/agentDeployments@2025-10-01-preview' = {
  parent: parentApplication
  name: name
  properties: union(
    {
      deploymentType: deploymentType
      displayName: displayName
      description: description
      deploymentId: deploymentId
      agents: agents
      protocols: protocols
      tags: tags
    },
    deploymentType == 'Hosted'
      ? {
          minReplicas: minReplicas
          maxReplicas: maxReplicas
        }
      : {}
  )
}

// ============ //
// Outputs      //
// ============ //

@sys.description('The resource ID of the agent deployment.')
output resourceId string = agentDeployment.id

@sys.description('The name of the agent deployment.')
output name string = agentDeployment.name

@sys.description('The name of the resource group the agent deployment was created in.')
output resourceGroupName string = resourceGroup().name

// ================ //
// Definitions      //
// ================ //

@export()
@sys.description('The type for a versioned agent reference.')
type versionedAgentReferenceType = {
  @sys.description('Optional. The agent\'s unique identifier within the organization.')
  agentId: string?

  @sys.description('Optional. The agent\'s name (unique within the project/app).')
  agentName: string?

  @sys.description('Optional. The agent\'s version (unique for each agent lineage).')
  agentVersion: string?
}

@export()
@sys.description('The type for an agent protocol version.')
type agentProtocolVersionType = {
  @sys.description('Optional. The protocol used by the agent.')
  protocol: ('A2A' | 'Agent' | 'Responses')?

  @sys.description('Optional. The version of the protocol.')
  version: string?
}

@export()
@sys.description('The type for an agent deployment configuration.')
type agentDeploymentType = {
  @sys.description('Required. The name of the agent deployment.')
  name: string

  @sys.description('Required. The type of deployment.')
  deploymentType: 'Hosted' | 'Managed'

  @sys.description('Optional. The display name of the deployment.')
  displayName: string?

  @sys.description('Optional. The description of the deployment.')
  description: string?

  @sys.description('Optional. The unique identifier of the deployment.')
  deploymentId: string?

  @sys.description('Optional. List of agent:version pairs deployed in this deployment.')
  agents: versionedAgentReferenceType[]?

  @sys.description('Optional. Protocol types and versions exposed by this deployment.')
  protocols: agentProtocolVersionType[]?

  @sys.description('Optional. The minimum number of replicas. Only applicable when deploymentType is "Hosted".')
  @minValue(0)
  minReplicas: int?

  @sys.description('Optional. The maximum number of replicas. Only applicable when deploymentType is "Hosted".')
  @minValue(0)
  maxReplicas: int?

  @sys.description('Optional. Tags for the deployment.')
  tags: object?
}
