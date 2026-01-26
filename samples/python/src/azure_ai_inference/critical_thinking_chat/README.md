# Critical Thinking Chat Assistant

A Python application that provides an interactive conversational assistant designed to challenge user assumptions, promote critical thinking, and facilitate deeper analysis of topics through structured questioning techniques with function tool calling capabilities for logical analysis.

## Overview

This sample demonstrates how to use the Azure AI Projects SDK to create an intelligent conversational agent that:

- Challenges user assumptions through Socratic questioning
- Promotes critical thinking by asking probing questions  
- Facilitates deeper analysis of complex topics
- Provides alternative perspectives on user statements
- Guides users through structured problem-solving approaches
- Uses function tool calling for logical analysis (syllogism evaluation and fallacy detection) with user permission requests
- Employs modular tools architecture for easy extensibility

## Prerequisites

- Python 3.8 or later
- Microsoft Foundry project with a deployed language model (e.g., GPT-4, GPT-4o-mini)
- Access to Azure with appropriate authentication configured

## Installation

1. Navigate to the critical thinking chat directory:

   ```bash
   cd samples/python/src/azure_ai_inference/critical_thinking_chat
   ```

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set the following environment variables:

- `PROJECT_ENDPOINT` (required): Your Microsoft Foundry project endpoint URL in the format `https://<project-name>.<region>.api.azureml.ms`
- `MODEL_DEPLOYMENT_NAME` (optional): Name of your deployed language model (defaults to "gpt-4o")
- `VERBOSE_LOGGING` (optional): Logging verbosity level (defaults to "ERROR")

You can also create a `.env` file in this directory:

```env
PROJECT_ENDPOINT=https://your-project.eastus.api.azureml.ms
MODEL_DEPLOYMENT_NAME=gpt-4o
VERBOSE_LOGGING=ERROR
```

## Authentication

This application uses `DefaultAzureCredential` for Azure authentication, which automatically selects the most appropriate credential source:

- Azure CLI login (`az login`)
- Managed Identity (when running on Azure)
- Visual Studio Code Azure Account extension
- Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)

## Usage

### Interactive Mode

Start a conversation that maintains context across multiple exchanges:

```bash
python critical_thinking_chat.py --interactive
```

### Single Question Mode

Analyze a single statement or question:

```bash
python critical_thinking_chat.py --question "I think social media is bad for society"
```

### Interactive Mode with Initial Question

Start with a question and continue the conversation:

```bash
python critical_thinking_chat.py --question "Remote work is always better" --interactive
```

### Verbose Logging

Enable debug logging for troubleshooting:

```bash
python critical_thinking_chat.py --interactive --verbose DEBUG
```

### Command Line Options

- `--question, -q`: Initial question/statement to analyze
- `--interactive, -i`: Enable interactive mode for extended conversations
- `--endpoint`: Override PROJECT_ENDPOINT environment variable
- `--model`: Override MODEL_DEPLOYMENT_NAME environment variable
- `--verbose, -v`: Set logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: ERROR
- `--help`: Show help message

## Example Conversations

### Single Question Analysis

```text
> python critical_thinking_chat.py --question "All politicians are corrupt"

=== CRITICAL THINKING ANALYSIS ===
Your statement: All politicians are corrupt
==================================================

Critical Thinking Assistant:
That's a strong generalization. Let's examine this more deeply. What specific evidence led you to conclude that ALL politicians are corrupt? Are there any politicians, either currently serving or historically, that you would consider honest? What would you say to someone who argues that corruption varies significantly across different political systems and cultures?

Also, how are you defining "corrupt" in this context? Sometimes people use this term broadly, but it can mean different things - from financial misconduct to simply making decisions we disagree with.
```

### Interactive Conversation

```text
> python critical_thinking_chat.py --interactive

============================================================
           CRITICAL THINKING CHAT ASSISTANT
============================================================
I'm here to help you think more deeply about complex topics.
I'll challenge your assumptions and guide you through critical analysis.

Type 'quit', 'exit', or 'q' to end our conversation.
Press Ctrl+C at any time to exit cleanly.
============================================================

--------------------------------------------------

Your response or new statement: I think AI will replace all human jobs

Critical Thinking Assistant:
That's a significant prediction about the future of work. Let's break this down systematically. When you say "all human jobs," are you including every type of work - from caregivers and therapists to artists and leaders? What evidence are you basing this prediction on?

Consider this: What unique human capabilities might be difficult for AI to replicate? And what new types of jobs might emerge as AI develops, just as previous technological revolutions created jobs we couldn't imagine before?

What timeframe are you thinking about for this complete replacement?
```

### Tool Calling Examples

The assistant can use function tools for logical analysis with user permission:

#### Syllogism Evaluation

```text
Your response or new statement: All mammals are warm-blooded. Whales are mammals. Therefore whales are warm-blooded.

🔧 Tool Call Request:
Tool: evaluate_syllogism
Purpose: Evaluate logical validity of syllogism
Parameters:
  - Major Premise: All mammals are warm-blooded
  - Minor Premise: Whales are mammals
  - Conclusion: Therefore whales are warm-blooded

Execute this tool? (y/n): y

Critical Thinking Assistant:
I've analyzed the logical structure of your argument. This is a valid categorical syllogism with proper logical structure. The premises support the conclusion effectively, and there are no logical fallacies present.

This is a good example of sound deductive reasoning. What made you choose this particular example?
```

#### Fallacy Detection

```text
Your response or new statement: Politicians are all corrupt because they take money from lobbyists.

🔧 Tool Call Request:
Tool: detect_fallacies
Purpose: Identify logical fallacies in argumentative text
Parameters:
  - Text: Politicians are all corrupt because they take money from lobbyists.

Execute this tool? (y/n): y

Critical Thinking Assistant:
I've analyzed your statement for logical fallacies. The analysis identified a hasty generalization fallacy - you're making a sweeping claim about ALL politicians without sufficient evidence or qualifying language.

What specific evidence do you have that ALL politicians are corrupt? Are there any politicians who might be exceptions? How do you define "corrupt" in this context? Consider using more precise language like "many" or "some" rather than absolute terms.
```

## Critical Thinking Techniques

The assistant employs various techniques to promote deeper analysis:

1. **Socratic Questioning**: Asking probing questions to examine assumptions
2. **Evidence-Based Reasoning**: Requesting supporting evidence for claims
3. **Alternative Perspectives**: Presenting different viewpoints on topics
4. **Assumption Challenging**: Identifying and questioning underlying beliefs
5. **5 Whys Approach**: Drilling down to root causes and reasoning
6. **Devil's Advocate**: Respectfully challenging positions to strengthen arguments

## Features

- **Modular Tools Architecture**: Extensible tools structure with separate modules for different analytical functions
- **Syllogism Evaluation**: Function tool calling for logical validity analysis of formal arguments
- **Fallacy Detection**: Comprehensive identification of logical fallacies in argumentative text with confidence scoring
- **User Permission System**: All tool calls require explicit user consent before execution
- **Context Maintenance**: Conversation memory across multiple exchanges
- **Graceful Exit**: Support for 'quit', 'exit', 'q', or Ctrl+C
- **Error Handling**: Robust error handling with informative messages
- **Configurable Logging**: Structured logging with verbosity control (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Type Safety**: Comprehensive type hints and validation
- **Authentication**: Secure Azure authentication using best practices

## Tools Architecture

The application uses a modular tools architecture for extensibility:

```text
tools/
├── __init__.py              # Python package initialization
├── syllogism.py             # Syllogism evaluation logic
└── fallacy_detector.py      # Fallacy detection logic
```

### Syllogism Tool

Analyzes the logical validity of syllogisms with three components:

- **Major Premise**: Universal statement
- **Minor Premise**: Specific statement  
- **Conclusion**: Derived statement

Returns detailed analysis including validity, logical form (categorical/conditional/disjunctive), and identified errors.

### Fallacy Detector Tool

Identifies common logical fallacies in argumentative text:

- Ad Hominem, Straw Man, False Dichotomy
- Hasty Generalization, Appeal to Authority
- Slippery Slope, Circular Reasoning
- Red Herring, Bandwagon, Appeal to Emotion

Returns detected fallacies, confidence scores, detailed analysis, and improvement suggestions.

## Code Quality

This implementation follows Python best practices and passes ruff linting checks:

```bash
# Run linting
python -m ruff check critical_thinking_chat.py

# Apply automatic fixes
python -m ruff check --fix critical_thinking_chat.py

# Format code
python -m ruff format critical_thinking_chat.py
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Ensure you're logged into Azure CLI (`az login`) or have appropriate credentials configured
2. **Endpoint Not Found**: Verify your PROJECT_ENDPOINT is correct and the project exists
3. **Model Not Available**: Check that your MODEL_DEPLOYMENT_NAME matches a deployed model in your project
4. **Network Issues**: Ensure you have internet connectivity and can reach Azure endpoints

### Debug Logging

To enable debug logging, use the `--verbose` command-line option or set the `VERBOSE_LOGGING` environment variable:

```bash
# Command line option
python critical_thinking_chat.py --interactive --verbose DEBUG

# Environment variable
export VERBOSE_LOGGING=DEBUG  # Linux/Mac
$env:VERBOSE_LOGGING="DEBUG"  # Windows PowerShell
```

Valid logging levels: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: ERROR)

## Dependencies

This implementation requires the following key dependencies:

- **Python 3.8+**
- **azure-ai-projects v1.0.0b12+** - Core Microsoft Foundry SDK
- **azure-identity** - DefaultAzureCredential authentication
- **openai** - Chat completions via Azure OpenAI client
- **argparse** - Command line argument parsing
- **json** - Tool response handling
- **logging** - Configurable verbosity control

## Implementation Notes

- Uses Azure AI Projects SDK with AIProjectClient.inference.get_azure_openai_client()
- Implements modular tools architecture with separate modules for logical analysis functions
- Implements function tool calling for syllogism evaluation and fallacy detection with user permission system
- Implements conversation memory with token overflow protection
- Follows Azure SDK security best practices
- Compatible with tool-capable AI models (GPT-4, GPT-4o, etc.)
- Supports Microsoft Foundry project deployments
- Quiet-by-default logging (ERROR level) with configurable verbosity
- Extensible design allows easy addition of new analytical tools
