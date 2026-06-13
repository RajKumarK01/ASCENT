param location string
param tags object
param hubName string
param projectName string
param storageAccountName string
param keyVaultName string
param applicationInsightsId string
param openAiId string
param openAiEndpoint string
param searchId string
param searchEndpoint string
param principalId string

// Storage and Key Vault are required dependencies of an AI Hub
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    accessPolicies: []
  }
}

resource hub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: hubName
  location: location
  tags: tags
  kind: 'Hub'
  identity: { type: 'SystemAssigned' }
  properties: {
    storageAccount: storage.id
    keyVault: keyVault.id
    applicationInsights: applicationInsightsId
    publicNetworkAccess: 'Enabled'
  }
}

// Wire OpenAI into the hub so agents can reach it via the project connection
resource aoaiConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = {
  parent: hub
  name: 'aoai-connection'
  properties: {
    category: 'AzureOpenAI'
    target: openAiEndpoint
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: listKeys(openAiId, '2023-05-01').key1
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: openAiId
      ApiVersion: '2024-05-01-preview'
      DeploymentApiVersion: '2023-10-01-preview'
    }
  }
}

// Wire AI Search into the hub for the Foundry IQ knowledge base
resource searchConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = {
  parent: hub
  name: 'search-connection'
  properties: {
    category: 'CognitiveSearch'
    target: searchEndpoint
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: listAdminKeys(searchId, '2023-11-01').primaryKey
    }
    metadata: {
      ResourceId: searchId
      ApiVersion: '2024-05-01-preview'
    }
  }
}

resource project 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: projectName
  location: location
  tags: tags
  kind: 'Project'
  identity: { type: 'SystemAssigned' }
  properties: {
    hubResourceId: hub.id
    publicNetworkAccess: 'Enabled'
  }
}

// Allow the deploying user to use the project from VS Code / local dev
var azureAIDeveloperRoleId = '64702f94-c441-49e6-a78b-ef80e0188fee'
resource projectDeveloperRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: project
  name: guid(project.id, principalId, azureAIDeveloperRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAIDeveloperRoleId)
    principalId: principalId
    principalType: 'User'
  }
}

// Standard format: https://<project>.<region>.api.azureml.ms
// Verify against the portal after provision if the SDK returns a 404.
output projectEndpoint string = 'https://${project.name}.${location}.api.azureml.ms'
output hubName string = hub.name
output projectName string = project.name
output projectId string = project.id
