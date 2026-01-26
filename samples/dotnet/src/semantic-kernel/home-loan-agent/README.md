# 🏠 Home Loan Guide (.NET)

This is a .NET implementation of the Home Loan Guide agent using Microsoft Semantic Kernel. This agent provides users with helpful information about mortgage applications at the fictitious Contoso Bank, streamlining the customer's mortgage application journey and empowering them to make informed decisions about their home loan options.

**IMPORTANT NOTE:** This is a sample application designed to demonstrate the capabilities of Semantic Kernel for building AI agents. The loan information and calculations provided are for demonstration purposes only and should not be used for actual financial decisions.

## 💼 Use Cases

- **Consumer Loan Advisory**: Help individuals evaluate loan options, understand documentation requirements, and compare payment terms
- **Pre-Approval & Application Readiness**: Guide users through the loan readiness process with tailored documentation and eligibility support
- **Mortgage Calculations**: Perform mortgage payment calculations, affordability analysis, and loan amount estimations

## 🧩 Features

This agent leverages **Microsoft Semantic Kernel** with the following capabilities:

- **Document Analysis**: Access to loan documentation checklists and product eligibility data
- **Mortgage Calculations**: Built-in functions for payment calculations, affordability analysis, and loan amount estimation
- **Interactive Chat**: Support for both single-question and interactive conversation modes
- **Azure OpenAI Integration**: Uses Azure OpenAI for natural language understanding and generation

## 🚀 Prerequisites

1. [.NET 8.0 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) or later
2. Azure OpenAI service with a deployed model (e.g., GPT-4, GPT-3.5-turbo)
3. Azure subscription with appropriate permissions

## ⚙️ Configuration

### Environment Variables

Set the following environment variables or configure them in `appsettings.json`:

```bash
# Required
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Optional (if not using DefaultAzureCredential)
AZURE_OPENAI_API_KEY=your-api-key
```

### Authentication

The application supports multiple authentication methods:

1. **DefaultAzureCredential** (Recommended): Uses managed identity, service principal, or user credentials
2. **API Key**: Direct API key authentication (less secure, not recommended for production)

### appsettings.json

```json
{
  "AzureOpenAI": {
    "Endpoint": "https://your-openai-resource.openai.azure.com/",
    "ApiKey": "", // Optional, leave empty to use DefaultAzureCredential
    "DeploymentName": "gpt-4o-mini"
  }
}
```

## 🔧 Building and Running

### Build the application

```bash
cd samples/dotnet/src/semantic-kernel/home-loan-agent
dotnet build
```

### Run with a single question

```bash
dotnet run -- --question "What documents do I need for a conventional loan?"
```

### Run in interactive mode

```bash
dotnet run -- --interactive
```

### Command Line Options

- `--question` or `-q`: Ask a single question (default: "What documents do I need for a Contoso Bank loan?")
- `--interactive` or `-i`: Run in interactive mode for multiple questions
- `--help`: Show help information

## 💬 Example Interactions

### Mortgage Calculation

**User**: Can you calculate my monthly payment if I take a 30-year fixed mortgage on a $450,000 home with a $90,000 down payment at a 6.5% interest rate?

**Agent Response**: The agent will use the built-in mortgage calculator to provide:
- Loan amount calculation ($360,000)
- Monthly payment calculation
- Total interest over the life of the loan
- Payment breakdown

### Documentation Requirements

**User**: What documents do I need for an FHA loan application?

**Agent Response**: The agent will reference the loan documentation checklist and provide specific requirements for FHA loans.

### Affordability Analysis

**User**: I make $8,000 per month and have $1,200 in existing debt. What can I afford?

**Agent Response**: The agent will calculate debt-to-income ratios and determine the maximum housing payment you can afford.

## 🏗️ Architecture

The application is built using:

- **Microsoft Semantic Kernel**: AI orchestration framework
- **Azure OpenAI**: Large language model for natural language processing
- **Dependency Injection**: For configuration and service management
- **Plugins**: Custom functions for mortgage calculations
- **Streaming**: Real-time response generation in interactive mode

## 📁 Project Structure

```
home_loan_agent/
├── Program.cs                              # Main application entry point
├── HomeLoanAgent.csproj                    # Project file with dependencies
├── appsettings.json                        # Configuration file
├── Contoso_Loan_Documentation_Checklist.md # Loan documentation requirements
├── loan_product_eligibility_dataset.csv    # Loan product data
└── README.md                               # This file
```

## 🔍 Key Components

### MortgageCalculatorPlugin

Provides mathematical functions for:
- Monthly payment calculations
- Affordability analysis based on income and DTI ratios
- Loan amount calculations based on purchase price and down payment

### ChatCompletionAgent

Configured with domain-specific instructions for:
- Mortgage lending expertise
- Document guidance
- Customer service best practices
- Integration with calculation functions

## 🛠️ Development

### Adding New Functions

To add new mortgage-related functions, extend the `MortgageCalculatorPlugin` class:

```csharp
[KernelFunction]
[Description("Your function description")]
public string YourNewFunction(
    [Description("Parameter description")] double parameter)
{
    // Your implementation
    return "Result";
}
```

### Customizing Agent Instructions

Modify the `instructions` constant in the `CreateHomeLoanAgent` method to customize the agent's behavior and personality.

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure your Azure OpenAI credentials are correctly configured
2. **Model Not Found**: Verify the deployment name matches your Azure OpenAI deployment
3. **Missing Files**: Ensure the documentation and CSV files are copied to the output directory

### Debugging

Enable detailed logging by setting the log level in `appsettings.json`:

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Debug",
      "Microsoft.SemanticKernel": "Debug"
    }
  }
}
```

## 📚 Resources

- [Semantic Kernel Documentation](https://learn.microsoft.com/semantic-kernel/overview/)
- [Semantic Kernel .NET Samples](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples)
- [Azure OpenAI Service Documentation](https://docs.microsoft.com/azure/cognitive-services/openai/)

## ⚖️ Legal Notice

This sample application is for demonstration purposes only. The loan information, calculations, and advice provided should not be used for actual financial decisions. Always consult with qualified financial professionals for real mortgage and lending advice.

## 🤝 Contributing

This is part of the Microsoft Foundry Jumpstart project. Contributions are welcome following the project's contribution guidelines.
