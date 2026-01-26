# .NET Samples

This directory contains .NET sample projects demonstrating various Azure AI Foundry capabilities.

## Structure

```
dotnet/
├── src/                    # Sample source code
│   ├── agent-framework/    # Microsoft Agent Framework samples
│   └── semantic-kernel/    # Semantic Kernel samples
├── tests/                  # Tests for samples
└── microsoft-foundry-jumpstart-samples.slnx  # Solution file
```

## Prerequisites

- .NET 8.0 SDK or later
- Azure subscription with AI Foundry resources

## Getting Started

1. Open the solution in Visual Studio or VS Code:
   ```bash
   cd samples/dotnet
   dotnet restore
   ```

2. Configure environment variables (see individual sample READMEs)

3. Build and run samples:
   ```bash
   dotnet build
   dotnet run --project src/<sample-path>
   ```

## Available Samples

### Agent Framework
- **AzureArchitect** - Multi-step samples showing agent capabilities
  - Step 01: Simple agent
  - Step 02: Foundry agents (single-turn, multi-turn, prebuilt)
  - Step 03-07: Advanced features (tools, approvals, MCP, images, workflows)
- **AgentPersistence** - Managing agent state and persistence

### Semantic Kernel
- **HomeLoanAgent** - Loan processing agent with eligibility checking

## Running Tests

```bash
dotnet test
```

## Learn More

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/en-us/semantic-kernel/agents/)
- [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
