# Azure Architect Agent Framework Demo

This demo showcases the progression of building an Azure architecture consultant AI agent using the Microsoft Agent Framework. The demo consists of seven progressive steps that demonstrate increasingly sophisticated agent capabilities, from simple chat interactions to complex concurrent workflows with external tool integration.

## Prerequisites

Before you begin, ensure you have the following prerequisites:

- .NET 9.0 SDK or later
- Microsoft Foundry service endpoint, project and GPT 4.1 deployment configured
- Azure CLI installed and authenticated (for Azure credential authentication)

**Note**: These demos use Azure CLI credentials for authentication. Make sure you're logged in with `az login` and have access to the Azure Foundry resource. For more information, see the [Azure CLI documentation](https://learn.microsoft.com/cli/azure/authenticate-azure-cli-interactively).

Set the following environment variables:

```powershell
$env:AZURE_OPENAI_ENDPOINT="<Your Azure OpenAI Endpoint - provided within Microsoft Foundry>"
$env:AZURE_OPENAI_DEPLOYMENT_NAME="<GPT 4.1 model deployed to Microsoft Foundry Project>"
$env:MICROSOFT_FOUNDRY_PROJECT_ENDPOINT="<Your Microsoft Foundry Project Endpoint>"
$env:MICROSOFT_FOUNDRY_PROJECT_DEPLOYMENT_NAME="<GPT 4.1 model deployed to Microsoft Foundry Project>"
```

## Purpose

The Azure Architect demo serves as a comprehensive learning path for developers who want to understand how to build production-ready AI agents that can provide expert Azure architecture guidance. Each step builds upon the previous one, introducing new concepts and capabilities while maintaining a consistent Azure Well-Architected Framework focus.

## Demo Flow

The demo follows a structured progression from basic agent creation to advanced workflow orchestration:

<!-- markdownlint-disable MD033 -->
| Title | Highlights |
| --- | --- |
| [Step 1: Simple Agent](./AzureArchitect_Step01_Simple/) | <ul><li>Builds a baseline Azure architecture advisor using Azure OpenAI chat completions.</li><li>Demonstrates both standard and streaming conversations that share a thread.</li><li>Establishes the Well-Architected focused agent persona and guidance style.</li></ul> |
| [Step 2: Microsoft Foundry Agent Service](./AzureArchitect_Step02_Foundry_AgentService/) | <ul><li>Creates and retrieves persistent server-side agents with Microsoft Foundry.</li><li>Manages multiple agent instances and their lifecycle from a single client.</li><li>Shows how Azure CLI credentials flow to hosted agent services.</li></ul> |
| [Step 3: Using Function Tools](./AzureArchitect_Step03_UsingFunctionTools/) | <ul><li>Registers a custom SLO calculator function tool with the agent.</li><li>Invokes tools during both non-streaming and streaming interactions.</li><li>Explains availability trade-offs through tool-augmented reasoning.</li></ul> |
| [Step 4: Function Tools with Approvals](./AzureArchitect_Step04_UsingFunctionToolsWithApprovals/) | <ul><li>Wraps the SLO calculator with approval requirements for human oversight.</li><li>Processes user approval responses to govern tool execution at runtime.</li><li>Illustrates repeatable human-in-the-loop compliance patterns.</li></ul> |
| [Step 5: MCP Server Integration](./AzureArchitect_Step05_MCPServer/) | <ul><li>Discovers Microsoft Learn tools via the Model Context Protocol server.</li><li>Combines official guidance tools with the reliability agent persona.</li><li>Grounds availability recommendations with cited Learn content.</li></ul> |
| [Step 6: Using Images](./AzureArchitect_Step06_UsingImages/) | <ul><li>Analyzes Azure reference architecture diagrams through image inputs.</li><li>Blends vision understanding with Microsoft Learn MCP tool citations.</li><li>Reuses conversation context for follow-up reliability questions.</li></ul> |
| [Step 7: Concurrent Workflows](./AzureArchitect_Step07_Workflows/) | <ul><li>Fans a scenario out to five pillar-specific architects via workflows.</li><li>Shares a discovered MCP toolset across agents without state conflicts.</li><li>Aggregates pillar findings into a consolidated lead architect report.</li></ul> |
<!-- markdownlint-enable MD033 -->

## Running the Demo

Each step can be run independently, but it's recommended to progress through them sequentially to understand the evolution of capabilities:

```powershell
# Navigate to any step directory
cd AzureArchitect_Step01_Simple
dotnet run
```

## Key Concepts Demonstrated

- **Agent Framework Basics**: Core concepts of agent creation and management
- **Authentication Patterns**: Azure CLI credential usage for secure access
- **Tool Integration**: Custom functions and external service integration
- **Approval Workflows**: Human-in-the-loop patterns for governance
- **Multi-Modal Processing**: Handling text and image inputs
- **Concurrent Processing**: Workflow orchestration and parallel execution
- **Knowledge Integration**: Real-time access to current documentation and guidance

## Architecture Patterns

The demo showcases several important architectural patterns:

- **Progressive Enhancement**: Each step builds upon previous capabilities
- **Separation of Concerns**: Different agents specialize in specific domains
- **Tool Composition**: Combining multiple tools and services
- **Workflow Orchestration**: Coordinating multiple agents for complex tasks
- **Human Oversight**: Implementing appropriate governance mechanisms
