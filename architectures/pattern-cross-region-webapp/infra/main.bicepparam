using './main.bicep'

param environmentName = 'crw'
param foundryLocation = 'eastus2'
param vnetLocation = 'australiaeast'
param foundryResourceGroupName = 'rg-crw-foundry'
param vnetResourceGroupName = 'rg-crw-webapp'
param principalId = ''
param principalIdType = 'User'
param disableApiKeys = false
param deployModels = true
param foundryProjectDeploy = true
param foundryProjectName = 'agent-project'
param foundryProjectFriendlyName = 'Cross-Region Agent Project'
param foundryProjectDescription = 'Foundry project accessed by a cross-region Web App via private endpoint'
param appServicePlanSku = 'P1v3'
