# Microsoft Foundry Jumpstart Solution Accelerator

[![CI][ci-shield]][ci-url]
[![CD][cd-shield]][cd-url]
[![License][license-shield]][license-url]
[![Azure][azure-shield]][azure-url]
[![IaC][iac-shield]][iac-url]

## What is the Microsoft Foundry Jumpstart Solution Accelerator

The Microsoft Foundry Jumpstart Solution Accelerator deploys a [Microsoft Foundry environment](https://learn.microsoft.com/azure/ai-foundry/how-to/create-secure-ai-hub) and supporting services into your Azure subscription. This accelerator is designed to be used as a secure environment for exploring and experimenting with Microsoft Foundry capabilities.

This solution accelerator is intended to help getting started with Microsoft Foundry quickly and easily, while meeting security and well-architected framework best practices.

If you just want to get started, jump to the [Deploying](#deploying) section.

## A Zero-trust Foundry Environment

By default, this solution accelerator deploys Microsoft Foundry and most of the supporting resources into a *virtual network* using *private endpoints*, *disables public access* and configures *managed identities for services to authenticate* to each other. This aligns to [Microsoft's Secure Future Initiative](https://www.microsoft.com/trust-center/security/secure-future-initiative) and the [Zero Trust security model](https://learn.microsoft.com/security/zero-trust/).

It automates the deployment of the Microsoft Foundry services and capabilities, optionally into a virtual network using Private Link as described in the [How to configure a private link for Microsoft Foundry (Foundry projects)](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/configure-private-link?view=foundry) page.

> [!IMPORTANT]
> Zero-trust with network isolation is the default configuration for this solution accelerator. But you can choose to deploy the resources without a virtual network and public endpoints if you prefer. See the [Configuration Options](#configuration-options) section for more details.
> When deployed with zero-trust, the Microsoft Foundry environment is not accessible from the public internet. You will need to use a VPN or Azure Bastion to access it.

## Requirements

Before you begin, ensure you have the following prerequisites in place:

1. An active Azure subscription - [Create a free account](https://azure.microsoft.com/free/) if you don't have one.
1. [Azure Developer CLI (azd)](https://aka.ms/install-azd) Install or update to the latest version. Instructions can be found on the linked page.
1. **Windows Only** [PowerShell](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows) of the latest version, needed only for local application development on Windows operation system. Please make sure that PowerShell executable `pwsh.exe` is added to the `PATH` variable.
1. **Recommended for using sample tools** [Python 3.10+](https://www.python.org/downloads/)

## Key Features

There are several features of the solution accelerator that are worth highlighting:

- **Zero-trust**: Support for deploying a zero-trust environment (network isolation).
- **Managed identities**: Use of managed identities for Azure resources to authenticate to each other. API keys are not used and can optionally be disabled.
- **Azure Verified Modules**: Use of Bicep [Azure verified modules](https://aka.ms/avm) to deploy the resources where possible.
- **Project deployment**: Optional deployment of [Microsoft Foundry projects]([https://learn.microsoft.com/azure/ai-foundry/concepts/ai-resources#organize-work-in-projects-for-customization](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/create-projects?view=foundry&tabs=foundry)) to the Foundry resource.
- **Diagnostic settings**: Diagnostic settings are configured for all resources to send logs to a Log Analytics workspace.
- **Model deployment**: Optionally deploy a selection of current AI models, speeding up getting started.
- **Sample data deployment**: Optionally upload sample data to an additional sample data storage account help you get started with Microsoft Foundry.
- **Sample data creation**: Data generation tool to create custom synthetic data for using with Microsoft Foundry.

> [!WARNING]
> **Hub Mode Deprecated** - As of December 2025, Microsoft Foundry Hub mode support has been removed from this solution accelerator. The solution now deploys only AI Services-based projects (Microsoft.CognitiveServices/accounts), which is the recommended approach. The Hub mode (Microsoft.MachineLearningServices/workspaces) required additional supporting resources (Key Vault, Storage Account, Container Registry) and is no longer necessary for Microsoft Foundry deployments. If you need Hub mode support, please use a previous version of this repository.

## Deploying

You can deploy the application using one of the following methods:

- [Azure Developer CLI](azure-developer-cli)
- [Azure Portal Deployment](azure-portal-deployment)

### Azure Developer CLI

This section will create Azure resources and deploy the solution from your local environment using the [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/overview). You do not need to clone this repository to complete these steps, but if you have already, just use the instructions under [If you have already cloned this repo](#if-you-have-already-cloned-this-repo). If you'd like to customize the deployment, see the [Customize the solution accelerator settings](#customize-the-solution-accelerator-settings) section.

#### If you have not cloned this repo

1. Download the [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/overview)
1. If you have not cloned this repo, you can use the `azd init -t PlagueHO/microsoft-foundry-jumpstart` command to clone the repo and initialize it.

   ```powershell
   azd init -t PlagueHO/microsoft-foundry-jumpstart
   ```

1. Authenticate the Azure Developer CLI  by running `azd auth login`.

   ```powershell
   azd auth login
   ```

1. (Optional) If you want to deploy the solution accelerator without network isolation, set the `AZURE_NETWORK_ISOLATION` environment variable to `false`:

   ```powershell
   azd env set AZURE_NETWORK_ISOLATION false
   ```

> [!NOTE]
> This will deploy the Microsoft Foundry service with public endpoints. You can access the Microsoft Foundry service from the public internet. This is recommended for demonstration and testing purposes or when there is no requirement for network isolation.

1. Run `azd up` to provision and deploy the application

   ```powershell
   azd up

#### If you have already cloned this repo

1. Download the [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/overview)
1. If you have already cloned this repo, change directory to the repo root directory.

   ```powershell
   cd microsoft-foundry-jumpstart
   ```

1. Authenticate the Azure Developer CLI  by running `azd auth login`.

   ```powershell
   azd auth login
   ```

1. (Optional) If you want to deploy the solution accelerator without network isolation, set the `AZURE_NETWORK_ISOLATION` environment variable to `false`:

   ```powershell
   azd env set AZURE_NETWORK_ISOLATION false
   ```

> [!NOTE]
> This will deploy the Microsoft Foundry service with public endpoints. You can access the Microsoft Foundry service from the public internet. This is recommended for demonstration and testing purposes or when there is no requirement for network isolation.

1. Run `azd up` to provision and deploy the application

   ```powershell
   azd up
   ```

#### Customize the solution accelerator settings

You can control many aspects of the AI Foundry environment during deployment by setting the environment values using the `azd env set` command before running the `azd up` command. For example:

```powershell
azd env set AZURE_NETWORK_ISOLATION false
azd env set DEPLOY_SAMPLE_MODELS true
azd env set DEPLOY_SAMPLE_DATA true
azd env set AZURE_CONTAINER_REGISTRY_DEPLOY false
azd env set AZURE_AI_SEARCH_DEPLOY false
azd env set MICROSOFT_FOUNDRY_PROJECT_DEPLOY true # Deploy projects (sample or single)
azd env set MICROSOFT_FOUNDRY_PROJECT_NAME "my-ai-project"
azd env set MICROSOFT_FOUNDRY_PROJECT_DESCRIPTION "This is my first AI project."
azd env set MICROSOFT_FOUNDRY_PROJECT_FRIENDLY_NAME "My AI Project"
```

A complete list of environment variables can be found in the [Configuration Options](docs/CONFIGURATION_OPTIONS.md) document.

### Azure Portal Deployment

Click on the Deploy to Azure button to deploy the Azure resources for this solution accelerator.

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FPlagueHO%2Fazure-ai-foundry-jumpstart%2Fmain%2Finfra%2Fmain.json)

> [!NOTE]
> This button will only create Azure resources. It will not deploy any sample data.

## Next Steps

After the deployment is complete, you can access the Microsoft Foundry service using the URL provided in the output of the deployment or going to [https://ai.azure.com/](https://ai.azure.com/). You can also access the Microsoft Foundry service using the Azure portal by navigating to the resource group created during the deployment.

> [!IMPORTANT]
> If you deployed the solution accelerator with network isolation, you will need to use a VPN or Azure Bastion to access the Microsoft Foundry service and project. The Microsoft Foundry service and project are not accessible from the public internet.

## Deleting the Deployment

If you created the deployment as a test or demonstration environment, you can easily delete the environment using the Azure Developer CLI if you used this method to deploy it.To delete all the resources created during the deployment, run the following command:

```powershell
azd down
```

You can force the deletion and purge the Key Vault and Azure AI Services by using the `--force` and `--purge` options:

```powershell
azd down --force --purge
```

> [!WARNING]
> This will delete all the resources created during the deployment, including any data or changes made since the deployment was created. So, before doing this, ensure you have backed up any important data or changes.

## Configuration Options

You can configure the deployment by setting environment variables when using the Azure Developer CLI. The environment variables are set in the Azure Developer CLI using the `azd env set` command. For example:

```powershell
azd env set AZURE_NETWORK_ISOLATION false
```

A complete list of environment variables can be found in the [Configuration Options](docs/CONFIGURATION_OPTIONS.md) document.

## Architecture

The following diagrams illustrate the architecture of the solution accelerator. For a detailed overview of the architecture of the solution accelerator, see the [Architecture](docs/design/ARCHITECTURE.md) document.

### With Network Isolation

The following diagram illustrates the architecture of the solution accelerator with network isolation when deploying a Microsoft Foundry project environment.

[![Microsoft Foundry Jumpstart Solution Accelerator with Network Isolation](docs/images/microsoft-foundry-jumpstart-zero-trust.svg)](docs/images/microsoft-foundry-jumpstart-zero-trust.svg)

### Without Network Isolation

The following diagram illustrates the architecture of the solution accelerator without network isolation when deploying a Microsoft Foundry project environment.

[![Microsoft Foundry Jumpstart Solution Accelerator without network isolation](docs/images/microsoft-foundry-jumpstart-public.svg)](docs/images/microsoft-foundry-jumpstart-public.svg)

## Contributing

TBC

## Contributors

Thanks to the following people who have contributed to this project:

- [Tim Shaw](https://github.com/Ancient13) - Partner Solution Architect, Data & AI, Microsoft

<!-- Badge reference links -->
[ci-shield]: https://img.shields.io/github/actions/workflow/status/PlagueHO/azure-ai-foundry-jumpstart/continuous-integration.yml?branch=main&label=CI
[ci-url]: https://github.com/PlagueHO/azure-ai-foundry-jumpstart/actions/workflows/continuous-integration.yml

[cd-shield]: https://img.shields.io/github/actions/workflow/status/PlagueHO/azure-ai-foundry-jumpstart/continuous-delivery.yml?branch=main&label=CD
[cd-url]: https://github.com/PlagueHO/azure-ai-foundry-jumpstart/actions/workflows/continuous-delivery.yml

[license-shield]: https://img.shields.io/github/license/PlagueHO/azure-ai-foundry-jumpstart
[license-url]: https://github.com/PlagueHO/azure-ai-foundry-jumpstart/blob/main/LICENSE

[azure-shield]: https://img.shields.io/badge/Azure-Solution%20Accelerator-0078D4?logo=microsoftazure&logoColor=white
[azure-url]: https://azure.microsoft.com/

[iac-shield]: https://img.shields.io/badge/Infrastructure%20as%20Code-Bicep-5C2D91?logo=azurepipelines&logoColor=white
[iac-url]: https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview
