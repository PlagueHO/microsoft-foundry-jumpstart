# .NET 10 Upgrade Report

## Project target framework modifications

| Project name                                                                      | Old Target Framework | New Target Framework | Commits                          |
|:----------------------------------------------------------------------------------|:--------------------:|:--------------------:|:---------------------------------|
| semantic-kernel\home-loan-agent\HomeLoanAgent.csproj                              | net8.0               | net10.0              | c05dba67                         |
| agent-framework\AzureArchitect\AzureArchitect_Step07_Workflows\AzureArchitect_Step07_WorkflowConcurrent.csproj | net9.0 | net10.0 | c778ac44                         |
| agent-framework\AzureArchitect\AzureArchitect_Step06_UsingImages\AzureArchitect_Step06_UsingImages.csproj | net9.0 | net10.0 | d5ea62a1                         |
| agent-framework\AzureArchitect\AzureArchitect_Step05_MCPServer\AzureArchitect_Step05_MCPServer.csproj | net9.0 | net10.0 | 289f5ffb                         |
| agent-framework\AzureArchitect\AzureArchitect_Step04_UsingFunctionToolsWithApprovals\AzureArchitect_Step04_UsingFunctionToolsWithApprovals.csproj | net9.0 | net10.0 | b2dce1e0 |
| agent-framework\AzureArchitect\AzureArchitect_Step03_UsingFunctionTools\AzureArchitect_Step03_UsingFunctionTools.csproj | net9.0 | net10.0 | fc5f153a |
| agent-framework\AzureArchitect\AzureArchitect_Step02_Foundry_AgentService\AzureArchitect_Step02_Foundry_AgentService.csproj | net9.0 | net10.0 | d4de3483 |
| agent-framework\AzureArchitect\AzureArchitect_Step01_Simple\AzureArchitect_Step01_Simple.csproj | net9.0 | net10.0 | 7ba2b8e6 |

## NuGet Packages

| Package Name                                          | Old Version | New Version | Commit IDs                                                       |
|:------------------------------------------------------|:-----------:|:-----------:|:-----------------------------------------------------------------|
| Azure.Identity                                        | 1.16.0      | 1.17.1      | c6302fe3, 013606da, cc881f77, 4a99229a, b3365f86, 8eb5501c, 1ac7e89c, 14c1f6e5 |
| Azure.Identity                                        | 1.17.0      | 1.17.1      | 013606da, cc881f77, 4a99229a, b3365f86, 8eb5501c, 1ac7e89c, 14c1f6e5 |
| Microsoft.Extensions.Configuration                    | 9.0.9       | 10.0.0      | c6302fe3                                                         |
| Microsoft.Extensions.Configuration.EnvironmentVariables | 9.0.9     | 10.0.0      | c6302fe3                                                         |
| Microsoft.Extensions.Configuration.UserSecrets        | 9.0.9       | 10.0.0      | c6302fe3                                                         |
| Microsoft.Extensions.DependencyInjection              | 9.0.9       | 10.0.0      | c6302fe3                                                         |
| Microsoft.Extensions.Hosting                          | 9.0.9       | 10.0.0      | c6302fe3                                                         |
| Microsoft.Extensions.Logging.Console                  | 9.0.9       | 10.0.0      | c6302fe3                                                         |

## Other Changes

### Removed packages

- Removed `System.Net.ServerSentEvents` (version 10.0.0) from three projects (AzureArchitect_Step07_WorkflowConcurrent, AzureArchitect_Step06_UsingImages, and AzureArchitect_Step05_MCPServer) as it was flagged as unnecessary by NU1510.

## All commits

| Commit ID | Description                                                                          |
|:----------|:-------------------------------------------------------------------------------------|
| 700c82fb  | Commit upgrade plan                                                                  |
| c05dba67  | Update HomeLoanAgent.csproj to target .NET 10.0                                      |
| c6302fe3  | Update package versions in HomeLoanAgent.csproj                                      |
| c778ac44  | Update target framework to net10.0 in WorkflowConcurrent.csproj                      |
| 013606da  | Update Azure.Identity to v1.17.1 in WorkflowConcurrent.csproj                        |
| 45f4a016  | Remove System.Net.ServerSentEvents from WorkflowConcurrent.csproj                    |
| 0eb54fbb  | Remove System.Net.ServerSentEvents from .csproj                                      |
| d5ea62a1  | Update target framework to net10.0 in AzureArchitect_Step06_UsingImages.csproj       |
| cc881f77  | Update Azure.Identity version in AzureArchitect_Step06_UsingImages.csproj            |
| 4a99229a  | Update Azure.Identity to v1.17.1 in AzureArchitect_Step05_MCPServer.csproj           |
| 289f5ffb  | Update target framework to net10.0 in AzureArchitect_Step05_MCPServer.csproj         |
| a0050907  | Remove System.Net.ServerSentEvents from .csproj dependencies                         |
| b2dce1e0  | Update target framework to net10.0 in AzureArchitect_Step04                          |
| b3365f86  | Update Azure.Identity to version 1.17.1 in csproj file                               |
| fc5f153a  | Update target framework in AzureArchitect_Step03_UsingFunctionTools.csproj           |
| 8eb5501c  | Update Azure.Identity to v1.17.1 in AzureArchitect_Step03_UsingFunctionTools.csproj  |
| d4de3483  | Update target framework to net10.0 in AzureArchitect_Step02_Foundry_AgentService.csproj |
| 1ac7e89c  | Update Azure.Identity to v1.17.1 in AzureArchitect_Step02                            |
| 7ba2b8e6  | Update target framework to net10.0 in AzureArchitect_Step01_Simple.csproj            |
| 14c1f6e5  | Update Azure.Identity version in AzureArchitect_Step01_Simple.csproj                 |

## Summary

Successfully upgraded all 8 projects in the solution to .NET 10.0 (Long Term Support):

- 1 project upgraded from .NET 8.0
- 7 projects upgraded from .NET 9.0

Key changes made:

- Updated target framework to `net10.0` for all projects
- Upgraded `Azure.Identity` package to version 1.17.1 (addresses deprecated MSAL .NET dependency)
- Upgraded Microsoft.Extensions packages (Configuration, DependencyInjection, Hosting, Logging.Console) from 9.0.9 to 10.0.0 in HomeLoanAgent project
- Removed unnecessary `System.Net.ServerSentEvents` package from three projects

All projects built and validated successfully after the upgrade.

## Next steps

- Test your applications thoroughly with .NET 10.0 to ensure all functionality works as expected
- Review and test any Azure Identity authentication flows with the updated package version
- Consider reviewing the .NET 10.0 release notes for any new features or improvements you could leverage
- Update your CI/CD pipelines to use .NET 10.0 SDK if needed
