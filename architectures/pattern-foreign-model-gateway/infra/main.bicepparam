using './main.bicep'

param environmentName = 'fgn'
param primaryLocation = 'australiaeast'
param foreignModelLocation = 'eastus2'
param resourceGroupName = 'rg-fgn'
param foreignResourceGroupName = 'rg-fgn-models'
param principalId = ''
param principalIdType = 'User'
param disableApiKeys = false
param deployPrimaryModels = true
param deployForeignModels = true
param foundryProjectDeploy = true
param foundryProjectName = 'agent-project'
param foundryProjectFriendlyName = 'Agent Project'
param foundryProjectDescription = 'Foundry project for Agent Framework orchestrator with foreign model access'
