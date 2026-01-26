# Python Samples

This directory contains Python sample projects demonstrating various Azure AI Foundry capabilities.

## Structure

```
python/
├── src/                                  # Sample source code
│   ├── azure_ai_inference/              # Azure AI Inference SDK samples
│   ├── foundry_agent_service_sdk/       # Foundry Agent Service samples
│   └── semantic_kernel/                 # Semantic Kernel samples
├── tests/                                # Tests for samples
└── pyproject.toml                        # Python configuration
```

## Prerequisites

- Python 3.8 or later
- Azure subscription with AI Foundry resources

## Getting Started

1. Navigate to a specific sample:
   ```bash
   cd samples/python/src/<sample-category>/<sample-name>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables (create `.env` file based on `.env.template` if provided)

4. Run the sample:
   ```bash
   python <sample-script>.py
   ```

## Available Samples

### Azure AI Inference
- **critical_thinking_chat** - Chat with fallacy detection and syllogism evaluation
- **initiative_analyzer** - Analyze project initiatives and backlog items

### Foundry Agent Service SDK
- **home_loan_agent** - Loan processing agent with eligibility checking

### Semantic Kernel
- **tech_support_agent** - Technical support agent with multiturn conversation

## Running Tests

From the `python/` directory:
```bash
pytest tests/
```

## Development

Lint code:
```bash
ruff check src/
```

Type checking:
```bash
mypy src/
```

## Learn More

- [Azure AI Inference Documentation](https://learn.microsoft.com/en-us/azure/ai-services/inference/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Semantic Kernel for Python](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-python)
