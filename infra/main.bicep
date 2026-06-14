targetScope = 'subscription'

// Supporting infrastructure for the ASCENT Hosted Agent.
// The agent itself is NOT defined here — it is registered in Foundry Agent
// Service via scripts/deploy_hosted_agent.py, which references the container
// image in the ACR provisioned below. This template just provisions the ACR
// (holds the agent image) and Application Insights (telemetry).

@minLength(1)
@maxLength(64)
param environmentName string

@minLength(1)
param location string

@description('Existing AI Foundry project endpoint (informational output only)')
param existingProjectEndpoint string = ''

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

module registry './modules/registry.bicep' = {
  name: 'registry'
  scope: rg
  params: {
    location: location
    tags: tags
    name: 'cr${resourceToken}'
  }
}

output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_LOCATION string = location
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.registryLoginServer
output AZURE_CONTAINER_REGISTRY_NAME string = registry.outputs.registryName
output AZURE_AI_PROJECT_ENDPOINT string = existingProjectEndpoint
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString
