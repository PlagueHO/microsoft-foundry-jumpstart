# .NET 10 Upgrade Plan

## Execution Steps

Execute steps below sequentially one by one in the order they are listed.

1. Validate that a .NET 10.0 SDK required for this upgrade is installed on the machine and if not, help to get it installed.
2. Ensure that the SDK version specified in global.json files is compatible with the .NET 10.0 upgrade.
3. Upgrade semantic-kernel\home-loan-agent\HomeLoanAgent.csproj
4. Upgrade agent-framework\AzureArchitect\AzureArchitect_Step07_Workflows\AzureArchitect_Step07_WorkflowConcurrent.csproj
5. Upgrade agent-framework\AzureArchitect\AzureArchitect_Step06_UsingImages\AzureArchitect_Step06_UsingImages.csproj
6. Upgrade agent-framework\AzureArchitect\AzureArchitect_Step05_MCPServer\AzureArchitect_Step05_MCPServer.csproj
7. Upgrade agent-framework\AzureArchitect\AzureArchitect_Step04_UsingFunctionToolsWithApprovals\AzureArchitect_Step04_UsingFunctionToolsWithApprovals.csproj
8. Upgrade agent-framework\AzureArchitect\AzureArchitect_Step03_UsingFunctionTools\AzureArchitect_Step03_UsingFunctionTools.csproj
9. Upgrade agent-framework\AzureArchitect\AzureArchitect_Step02_Foundry_AgentService\AzureArchitect_Step02_Foundry_AgentService.csproj
10. Upgrade agent-framework\AzureArchitect\AzureArchitect_Step01_Simple\AzureArchitect_Step01_Simple.csproj

## Settings

This section contains settings and data used by execution steps.

### Aggregate NuGet packages modifications across all projects

NuGet packages used across all selected projects or their dependencies that need version update in projects that reference them.

| Package Name                                          | Current Version | New Version | Description                                                     |
|:------------------------------------------------------|:---------------:|:-----------:|:----------------------------------------------------------------|
| Azure.Identity                                        | 1.16.0;1.17.0   | 1.17.1      | Deprecated - depends on deprecated version of MSAL .NET         |
| Microsoft.Extensions.Configuration                    | 9.0.9           | 10.0.0      | Recommended for .NET 10.0                                       |
| Microsoft.Extensions.Configuration.EnvironmentVariables | 9.0.9         | 10.0.0      | Recommended for .NET 10.0                                       |
| Microsoft.Extensions.Configuration.UserSecrets        | 9.0.9           | 10.0.0      | Recommended for .NET 10.0                                       |
| Microsoft.Extensions.DependencyInjection              | 9.0.9           | 10.0.0      | Recommended for .NET 10.0                                       |
| Microsoft.Extensions.Hosting                          | 9.0.9           | 10.0.0      | Recommended for .NET 10.0                                       |
| Microsoft.Extensions.Logging.Console                  | 9.0.9           | 10.0.0      | Recommended for .NET 10.0                                       |

### Project upgrade details

This section contains details about each project upgrade and modifications that need to be done in the project.

#### semantic-kernel\home-loan-agent\HomeLoanAgent.csproj modifications

Project properties changes:

- Target framework should be changed from `net8.0` to `net10.0`

NuGet packages changes:

- Azure.Identity should be updated from `1.16.0` to `1.17.1` (*deprecated - depends on deprecated version of MSAL .NET*)
- Microsoft.Extensions.Configuration should be updated from `9.0.9` to `10.0.0` (*recommended for .NET 10.0*)
- Microsoft.Extensions.Configuration.EnvironmentVariables should be updated from `9.0.9` to `10.0.0` (*recommended for .NET 10.0*)
- Microsoft.Extensions.Configuration.UserSecrets should be updated from `9.0.9` to `10.0.0` (*recommended for .NET 10.0*)
- Microsoft.Extensions.DependencyInjection should be updated from `9.0.9` to `10.0.0` (*recommended for .NET 10.0*)
- Microsoft.Extensions.Hosting should be updated from `9.0.9` to `10.0.0` (*recommended for .NET 10.0*)
- Microsoft.Extensions.Logging.Console should be updated from `9.0.9` to `10.0.0` (*recommended for .NET 10.0*)

#### agent-framework\AzureArchitect\AzureArchitect_Step07_Workflows\AzureArchitect_Step07_WorkflowConcurrent.csproj modifications

Project properties changes:

- Target framework should be changed from `net9.0` to `net10.0`

NuGet packages changes:

- Azure.Identity should be updated from `1.17.0` to `1.17.1` (*deprecated - depends on deprecated version of MSAL .NET*)

#### agent-framework\AzureArchitect\AzureArchitect_Step06_UsingImages\AzureArchitect_Step06_UsingImages.csproj modifications

Project properties changes:

- Target framework should be changed from `net9.0` to `net10.0`

NuGet packages changes:

- Azure.Identity should be updated from `1.17.0` to `1.17.1` (*deprecated - depends on deprecated version of MSAL .NET*)

#### agent-framework\AzureArchitect\AzureArchitect_Step05_MCPServer\AzureArchitect_Step05_MCPServer.csproj modifications

Project properties changes:

- Target framework should be changed from `net9.0` to `net10.0`

NuGet packages changes:

- Azure.Identity should be updated from `1.17.0` to `1.17.1` (*deprecated - depends on deprecated version of MSAL .NET*)

#### agent-framework\AzureArchitect\AzureArchitect_Step04_UsingFunctionToolsWithApprovals\AzureArchitect_Step04_UsingFunctionToolsWithApprovals.csproj modifications

Project properties changes:

- Target framework should be changed from `net9.0` to `net10.0`

NuGet packages changes:

- Azure.Identity should be updated from `1.17.0` to `1.17.1` (*deprecated - depends on deprecated version of MSAL .NET*)

#### agent-framework\AzureArchitect\AzureArchitect_Step03_UsingFunctionTools\AzureArchitect_Step03_UsingFunctionTools.csproj modifications

Project properties changes:

- Target framework should be changed from `net9.0` to `net10.0`

NuGet packages changes:

- Azure.Identity should be updated from `1.17.0` to `1.17.1` (*deprecated - depends on deprecated version of MSAL .NET*)

#### agent-framework\AzureArchitect\AzureArchitect_Step02_Foundry_AgentService\AzureArchitect_Step02_Foundry_AgentService.csproj modifications

Project properties changes:

- Target framework should be changed from `net9.0` to `net10.0`

NuGet packages changes:

- Azure.Identity should be updated from `1.17.0` to `1.17.1` (*deprecated - depends on deprecated version of MSAL .NET*)

#### agent-framework\AzureArchitect\AzureArchitect_Step01_Simple\AzureArchitect_Step01_Simple.csproj modifications

Project properties changes:

- Target framework should be changed from `net9.0` to `net10.0`

NuGet packages changes:

- Azure.Identity should be updated from `1.17.0` to `1.17.1` (*deprecated - depends on deprecated version of MSAL .NET*)
