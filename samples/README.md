# Samples

This directory contains sample applications demonstrating various Azure AI Foundry capabilities using different frameworks and SDKs.

## Directory Structure

```
samples/
├── dotnet/                                        # .NET samples
│   ├── src/                                      # Sample source code
│   │   ├── agent-framework/                      # Microsoft Agent Framework samples
│   │   │   ├── AzureArchitect/                  # Progressive agent samples
│   │   │   └── AgentPersistence/                # Agent persistence samples
│   │   └── semantic-kernel/                     # Semantic Kernel samples
│   │       └── home-loan-agent/                 # Home loan processing agent
│   ├── tests/                                    # Tests for .NET samples
│   ├── microsoft-foundry-jumpstart-samples.slnx  # Solution file
│   └── README.md                                 # .NET samples documentation
│
└── python/                                        # Python samples
    ├── src/                                      # Sample source code
    │   ├── azure_ai_inference/                  # Azure AI Inference SDK samples
    │   │   ├── critical_thinking_chat/          # Critical thinking chat
    │   │   └── initiative_analyzer/             # Initiative analysis tool
    │   ├── foundry_agent_service_sdk/           # Foundry Agent Service samples
    │   │   └── home_loan_agent/                # Home loan agent
    │   └── semantic_kernel/                     # Semantic Kernel samples
    │       └── tech_support_agent/             # Technical support agent
    ├── tests/                                    # Tests for Python samples
    ├── pyproject.toml                            # Python configuration
    └── README.md                                 # Python samples documentation
```

## Getting Started

### .NET Samples

For .NET samples, see [dotnet/README.md](dotnet/README.md).

Quick start:
```bash
cd samples/dotnet
dotnet restore
dotnet build
dotnet run --project src/<sample-path>
```

### Python Samples

For Python samples, see [python/README.md](python/README.md).

Quick start:
```bash
cd samples/python/src/<sample-category>/<sample-name>
pip install -r requirements.txt
python <sample-script>.py
```

## Sample Categories

### Agent Framework (.NET)
Progressive samples showing the Microsoft Agent Framework capabilities from simple agents to complex workflows with tools, approvals, and multi-modal inputs.

### Semantic Kernel (.NET & Python)
Samples demonstrating the Semantic Kernel SDK for building AI applications with both .NET and Python.

### Azure AI Inference (Python)
Samples using the Azure AI Inference SDK for building intelligent applications with critical thinking and analysis capabilities.

### Foundry Agent Service SDK (Python)
Samples using the Foundry Agent Service SDK for building and deploying agents on Azure AI Foundry.

## Prerequisites

- **For .NET samples**: .NET 8.0 SDK or later
- **For Python samples**: Python 3.8 or later
- Azure subscription with AI Foundry resources deployed
- Environment variables configured (see individual sample READMEs)

## Contributing

When adding new samples:
1. Place them in the appropriate language and framework directory under `src/`
2. Include a `README.md` with setup and usage instructions
3. Add corresponding tests in the `tests/` directory
4. Update this README with a brief description
5. Follow the coding standards for the respective language

## Learn More

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/en-us/semantic-kernel/agents/)
- [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
- [Azure AI Inference Documentation](https://learn.microsoft.com/en-us/azure/ai-services/inference/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
