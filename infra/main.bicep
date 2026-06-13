targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment — used in resource naming')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Location for Azure OpenAI (gpt-4o availability varies by region)')
param openAiLocation string = 'eastus'

@description('Object ID of the deploying user for local dev role assignments')
param principalId string = ''

var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: 'log-${resourceToken}'
    applicationInsightsName: 'appi-${resourceToken}'
  }
}

module openai './modules/openai.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    location: openAiLocation
    tags: tags
    name: 'cog-${resourceToken}'
    deploymentName: 'gpt-4o'
    principalId: principalId
  }
}

module search './modules/search.bicep' = {
  name: 'search'
  scope: rg
  params: {
    location: location
    tags: tags
    name: 'srch-${resourceToken}'
    principalId: principalId
  }
}

module aiHub './modules/ai-hub.bicep' = {
  name: 'ai-hub'
  scope: rg
  params: {
    location: location
    tags: tags
    hubName: 'hub-${resourceToken}'
    projectName: 'proj-${resourceToken}'
    storageAccountName: 'st${resourceToken}'
    keyVaultName: 'kv-${resourceToken}'
    applicationInsightsId: monitoring.outputs.applicationInsightsId
    openAiId: openai.outputs.openAiId
    openAiEndpoint: openai.outputs.openAiEndpoint
    searchId: search.outputs.searchServiceId
    searchEndpoint: search.outputs.searchEndpoint
    principalId: principalId
  }
}

module registry './modules/registry.bicep' = {
  name: 'registry'
  scope: rg
  params: {
    location: location
    tags: tags
    name: 'cr${resourceToken}'
  }
}

module containerApps './modules/container-apps.bicep' = {
  name: 'container-apps'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppsEnvironmentName: 'cae-${resourceToken}'
    containerAppName: 'ca-ascent'
    containerRegistryLoginServer: registry.outputs.registryLoginServer
    acrPullIdentityId: registry.outputs.acrPullIdentityId
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    aiProjectEndpoint: aiHub.outputs.projectEndpoint
    openAiDeploymentName: 'gpt-4o'
    searchEndpoint: search.outputs.searchEndpoint
    searchIndexName: 'ascent-kb'
    openAiResourceName: openai.outputs.openAiName
    searchResourceName: search.outputs.searchName
  }
}

// azd reads these outputs and injects them as environment variables after provision
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = subscription().tenantId
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.registryLoginServer
output AZURE_CONTAINER_REGISTRY_NAME string = registry.outputs.registryName
output AZURE_AI_PROJECT_ENDPOINT string = aiHub.outputs.projectEndpoint
output AZURE_AI_MODEL_DEPLOYMENT string = 'gpt-4o'
output AZURE_SEARCH_ENDPOINT string = search.outputs.searchEndpoint
output AZURE_SEARCH_KNOWLEDGE_BASE string = 'ascent-kb'
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString
output SERVICE_ASCENT_AGENT_IMAGE_NAME string = 'ascent'
