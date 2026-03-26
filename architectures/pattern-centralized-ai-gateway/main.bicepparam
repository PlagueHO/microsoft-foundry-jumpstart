using './main.bicep'

param environmentName = 'aigw'
param primaryLocation = 'australiaeast'
param modelsLocation = 'eastus2'
param resourceGroupName = 'rg-aigw'
param modelsResourceGroupName = 'rg-aigw-models'
param principalId = ''
param principalIdType = 'User'
param disableApiKeys = false
param deployPrimaryModels = true
param deployModelsRegionModels = true
param foundryProjectDeploy = true
param department1Name = 'dept-1'
param department1DisplayName = 'Department 1'
param department2Name = 'dept-2'
param department2DisplayName = 'Department 2'
param apimPublisherEmail = 'apimgmt-noreply@mail.windowsazure.com'
param apimPublisherName = 'AI Gateway Admin'
param apimSku = 'Developer'
param apimSkuCapacity = 1
