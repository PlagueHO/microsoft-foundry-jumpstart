metadata name = 'Cognitive Services Application'
metadata description = '''
This module creates an application within a Cognitive Services project.
Applications are agentic application instances that can contain agent deployments.
See: https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects/applications
'''

// ================ //
// Parameters       //
// ================ //

@sys.description('Required. The name of the parent Cognitive Services account.')
param accountName string

@sys.description('Required. The name of the parent project.')
param projectName string

@sys.description('Required. The name of the application.')
param name string

@sys.description('Optional. The display name of the application.')
param displayName string?

@sys.description('Optional. A description of the application.')
param description string?

@sys.description('Optional. The authorization policy for the application.')
param authorizationPolicy applicationAuthorizationPolicyType?

@sys.description('Optional. The Entra ID agentic blueprint of the application.')
param agentIdentityBlueprint assignedIdentityType?

@sys.description('Optional. The default agent instance identity of the application.')
param defaultInstanceIdentity assignedIdentityType?

@sys.description('Optional. The application\'s dedicated invocation endpoint.')
param baseUrl string?

@sys.description('Optional. The traffic routing policy for the application\'s deployments.')
param trafficRoutingPolicy applicationTrafficRoutingPolicyType?

@sys.description('Optional. The list of agent references in this application.')
param agents agentReferenceType[]?

@sys.description('Optional. Tags for the application properties.')
param tags object?

import { agentDeploymentType } from 'agentDeployment/main.bicep'
@sys.description('Optional. Agent deployments to create within this application.')
param agentDeployments agentDeploymentType[] = []

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

resource application 'Microsoft.CognitiveServices/accounts/projects/applications@2025-10-01-preview' = {
  parent: parentProject
  name: name
  properties: {
    displayName: displayName
    description: description
    #disable-next-line BCP225 BCP078 // authorizationPolicy uses authorizationScheme discriminator; ARM schema still references 'type' (RP schema mismatch)
    authorizationPolicy: authorizationPolicy
    agentIdentityBlueprint: agentIdentityBlueprint
    defaultInstanceIdentity: defaultInstanceIdentity
    baseUrl: baseUrl
    trafficRoutingPolicy: trafficRoutingPolicy
    agents: agents
    tags: tags
  }
}

@batchSize(1)
resource application_agentDeployments 'Microsoft.CognitiveServices/accounts/projects/applications/agentDeployments@2025-10-01-preview' = [
  for (agentDeployment, index) in (agentDeployments ?? []): {
    parent: application
    name: agentDeployment.name
    properties: union(
      {
        deploymentType: agentDeployment.deploymentType
        displayName: agentDeployment.?displayName
        description: agentDeployment.?description
        deploymentId: agentDeployment.?deploymentId
        agents: agentDeployment.?agents
        protocols: agentDeployment.?protocols
        tags: agentDeployment.?tags
      },
      agentDeployment.deploymentType == 'Hosted'
        ? {
            minReplicas: agentDeployment.?minReplicas
            maxReplicas: agentDeployment.?maxReplicas
          }
        : {}
    )
  }
]

// ============ //
// Outputs      //
// ============ //

@sys.description('The resource ID of the application.')
output resourceId string = application.id

@sys.description('The name of the application.')
output name string = application.name

@sys.description('The name of the resource group the application was created in.')
output resourceGroupName string = resourceGroup().name

// ================ //
// Definitions      //
// ================ //

@export()
@sys.description('The type for a reference to an agent within an application.')
type agentReferenceType = {
  @sys.description('Optional. The agent\'s unique identifier within the organization.')
  agentId: string?

  @sys.description('Optional. The agent\'s name (unique within the project/app).')
  agentName: string?
}

@export()
@sys.description('The type for the authorization policy of an application.')
type applicationAuthorizationPolicyType = {
  @sys.description('Required. The authorization scheme type.')
  authorizationScheme: 'Channels' | 'Default' | 'OrganizationScope'
}

@export()
@sys.description('The type for an assigned identity.')
type assignedIdentityType = {
  @sys.description('Required. The client ID of the identity.')
  clientId: string

  @sys.description('Required. Specifies the kind of Entra identity.')
  kind: 'AgentBlueprint' | 'AgenticUser' | 'AgentInstance' | 'Managed' | 'None'

  @sys.description('Required. The principal ID of the identity.')
  principalId: string

  @sys.description('Optional. The subject of this identity assignment.')
  subject: string?

  @sys.description('Required. The tenant ID of the identity.')
  tenantId: string

  @sys.description('Required. The identity type from a management perspective.')
  type: 'None' | 'System' | 'User'
}

@export()
@sys.description('The type for the traffic routing policy.')
type applicationTrafficRoutingPolicyType = {
  @sys.description('Optional. Methodology used to route traffic to deployments.')
  protocol: 'FixedRatio'?

  @sys.description('Optional. Collection of traffic routing rules.')
  rules: trafficRoutingRuleType[]?
}

@export()
@sys.description('The type for a traffic routing rule.')
type trafficRoutingRuleType = {
  @sys.description('Optional. The unique identifier of the deployment to route traffic to.')
  deploymentId: string?

  @sys.description('Optional. A description for this traffic routing rule.')
  description: string?

  @sys.description('Optional. The identifier of this traffic routing rule.')
  ruleId: string?

  @sys.description('Optional. The percentage of traffic allocated to this instance.')
  trafficPercentage: int?
}

@export()
@sys.description('The type for an application configuration, used when defining applications for a project.')
type applicationType = {
  @sys.description('Required. The name of the application.')
  name: string

  @sys.description('Optional. The display name of the application.')
  displayName: string?

  @sys.description('Optional. A description of the application.')
  description: string?

  @sys.description('Optional. The authorization policy for the application.')
  authorizationPolicy: applicationAuthorizationPolicyType?

  @sys.description('Optional. The Entra ID agentic blueprint of the application.')
  agentIdentityBlueprint: assignedIdentityType?

  @sys.description('Optional. The default agent instance identity.')
  defaultInstanceIdentity: assignedIdentityType?

  @sys.description('Optional. The application\'s dedicated invocation endpoint.')
  baseUrl: string?

  @sys.description('Optional. The traffic routing policy for the application\'s deployments.')
  trafficRoutingPolicy: applicationTrafficRoutingPolicyType?

  @sys.description('Optional. The list of agent references in this application.')
  agents: agentReferenceType[]?

  @sys.description('Optional. Tags for the application properties.')
  tags: object?

  @sys.description('Optional. Agent deployments to create within this application.')
  agentDeployments: agentDeploymentType[]?
}

@export()
@sys.description('The type for the application output.')
type applicationOutputType = {
  @sys.description('The name of the application.')
  name: string

  @sys.description('The resource ID of the application.')
  resourceId: string
}
