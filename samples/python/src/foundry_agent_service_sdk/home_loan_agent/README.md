# 🏠 Home Loan Guide

This code sample enables agent creation to provide users with helpful information about mortgage applications at a fictitious company, Cortoso Bank.
It helps streamlines a customer's mortgage application journey, empowering them to make informed decisions about their home loan options while simplifying the documentation and application process.

**IMPORTANT NOTE:** Starter templates, instructions, code samples and resources in this msft-agent-samples file (“samples”) are designed to assist in accelerating development of agents for specific scenarios. It is important that you review all provided resources and carefully test Agent behavior in the context of your use case: ([Learn More](https://learn.microsoft.com/en-us/legal/cognitive-services/agents/transparency-note?context=%2Fazure%2Fai-services%2Fagents%2Fcontext%2Fcontext)).

Certain Agent offerings may be subject to legal and regulatory requirements, may require licenses, or may not be suitable for all industries, scenarios, or use cases. By using any sample, you are acknowledging that Agents or other output created using that sample are solely your responsibility, and that you will comply with all applicable laws, regulations, and relevant safety standards, terms of service, and codes of conduct.  

**WARNING:**  The Home Loan Guide code sample is intended to help you create an agent that will be used for informational purposes only. Any information produced by an agent you create using the Home Loan Guide agent code sample is not intended to be used to assess an end-user consumer’s eligibility for any form of credit or insurance, employment purposes, or otherwise be used in connection with a credit transaction or business transaction of the end-user consumer. Any information developed by such an agent should only be shared with the relevant end-user consumer strictly for the end-user consumer’s informational purposes.
By using the Home Loan Guide agent code sample, you are agreeing not to furnish to, or otherwise share with, third parties any consumer information accessed or acquired using an agent created with the Home Loan Guide code sample. Customer also agrees not to use or collect any information through an agent created with Home Loan Guide code sample to determine an end-user consumer’s eligibility for any form of credit or insurance, employment purposes, or otherwise use the information in connection with an end-user consumer credit transaction or business transaction.  

## 💼 Use Cases

- **Consumer Loan Advisory**: Help individuals evaluate loan options, understand documentation requirements, and compare payment terms.
- **Pre-Approval & Application Readiness**: Guide users through the loan readiness process with tailored documentation and eligibility support.

## 🧩 Tools

This agent leverages **Azure AI Agent Service**, using the following tools:

- **File Search** to retrieve mortgage forms, FAQs, and templates.
- **Code Interpreter** to calculate mortgage payments, compare scenarios, and validate input.

The agent is configured via a `template.py` file and deployable with Bicep for enterprise use.

---

## Setup Instructions

### Prerequisites

1. Azure subscription with the following permissions
   - Contributor or Cognitive Services Contributor role (for resource deployment)
   - Azure AI Developer and Cognitive Services user role (for agent creation)
2. Agent setup: deploy the latest agent setup using this ([custom deployment](https://www.aka.ms/basic-agent-deployment)).
   - The above creates:
      - AI Services resource
      - AI Project
      - Model deployment
3. Python 3.8+
4. Azure CLI

---

## 💬 Example Agent Interactions

**User**: Can you calculate my monthly payment if I take a 30-year fixed mortgage on a $450,000 home with a $90,000 down payment at a 6.5% interest rate?  
**🔧 Agent Response**: Code Interpreter performs mortgage payment calculation.

---

**User**: What documents do I need for a Contoso Bank loan?  
**🔍 Agent Response**: File Search Tool retrieves the Contoso Bank loan documentation checklist.

---

**User**: Can you compare the estimated closing costs for FHA and Conventional loans at Contoso Bank?  
**🔍 Agent Response**: File Search Tool retrieves rows from the dataset for side-by-side cost comparison.

---

**User**: I’m comparing a 15-year and 30-year mortgage—can you show the difference in total interest paid?  
**🔧 Agent Response**: Code Interpreter compares amortization scenarios.

---

**User**: I have a condo in Florida—what loan products allow condos, and what are their DTI limits?  
**🔍 Agent Response**: File Search Tool returns products where `Allowed Property Types = Condo`, with associated DTI caps.

## 🛠 Customization Tips

- **Integrate with Loan Origination Systems (LOS)**  
  Add a custom tool or connector (e.g., via Azure Logic Apps) to allow users to submit pre-approval applications, upload documents, or retrieve loan status from internal LOS platforms.

- **Personalize Based on User Profile**  
  Modify the `system_message` to adjust tone and guidance for first-time buyers, military veterans, or investment property seekers.

- **Enable Secure Document Submission**  
  Extend the agent to support Azure Blob or SharePoint uploads for income verification, ID, or bank statements, and validate them using metadata or form templates.

- **Visualize Loan Comparisons**  
  Generate charts comparing monthly payments, total interest, and amortization curves across loan products.

- **Add Multi-language Support**  
  Integrate Translator or prompt-based language switching to support users in multiple languages.

## 🚀 Quick Start

### Prerequisites

1. **Microsoft Foundry Project**: Set up an Microsoft Foundry project
2. **Authentication**: Login via Azure CLI: `az login`
3. **Python Environment**: Python 3.8+ with required packages

### Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Setup

Set your project endpoint and optionally the model deployment:

```bash
# PowerShell
$env:PROJECT_ENDPOINT = "https://yourproject.region.api.azureml.ms"
$env:MODEL_DEPLOYMENT_NAME = "gpt-4o-mini"  # Optional, defaults to gpt-4o-mini

# Command Prompt  
set PROJECT_ENDPOINT=https://yourproject.region.api.azureml.ms
set MODEL_DEPLOYMENT_NAME=gpt-4o-mini
```

### Run the Sample

#### Basic Usage (Default Question)

```bash
python home_loan_agent.py
```

#### Custom Question

```bash
python home_loan_agent.py --question "Can you calculate my monthly payment for a $400,000 home with 20% down at 6.5% interest?"
```

#### Interactive Mode

```bash
python home_loan_agent.py --interactive
```

#### Command-Line Options

- `--question`, `-q`: Specify a custom question to ask the agent
- `--interactive`, `-i`: Run in interactive mode for multiple questions
- `--help`, `-h`: Show help message with all available options

## 📋 What the Sample Does

The `home_loan_agent.py` script demonstrates a complete agent lifecycle with modular resource management and the following process:

### 1. **Connection & Authentication**

- Establishes connection to Microsoft Foundry using `DefaultAzureCredential`
- Tests the connection before proceeding
- Uses environment variables for configuration

### 2. **File Upload & Preparation**

- Uploads `Contoso_Loan_Documentation_Checklist.md` for document search capabilities
- Uploads `loan_product_eligibility_dataset.csv` for code interpreter analysis
- Creates a vector store with the checklist file for enhanced search

### 3. **Agent Creation**

- Creates a "home-loan-guide" agent with comprehensive mortgage expertise
- Configures the agent with detailed instructions covering:
  - Mortgage application guidance
  - Document preparation assistance
  - Loan option evaluation
  - Credit score insights
  - Payment structure explanations

### 4. **Tool Configuration**

- **File Search Tool**: Configured with the vector store for document retrieval
- **Code Interpreter Tool**: Set up with the loan dataset for calculations and analysis

### 5. **Thread Management**

- **Single Question Mode**: Creates a dedicated thread for each question session
- **Interactive Mode**: Creates a persistent thread that maintains conversation context
- Dedicated `create_thread()` and `delete_thread()` functions for proper lifecycle management

### 6. **Conversation Execution**

- Accepts questions via command-line parameters or interactive input
- Default question: "What documents do I need for a Contoso Bank loan?"
- Processes the agent's response using both tools
- Displays the complete conversation history with proper message ordering

### 7. **Resource Cleanup**

- **Thread Cleanup**: Properly deletes conversation threads when sessions end
- **Agent Cleanup**: Removes the agent and associated resources
- **File Cleanup**: Deletes uploaded files and vector stores
- Ensures no resources are left behind with proper error handling

### 📊 Sample Output

When you run the script, you'll see:

- Connection status and agent creation confirmations
- File upload progress with generated IDs
- Vector store creation details
- **Thread creation and management**: Clear indication of thread lifecycle
- The question being asked (custom or default)
- The complete conversation between user and agent
- Step-by-step resource cleanup including thread deletion

### 💡 Architecture Highlights

The script follows a clean separation of concerns:

- **Agent Management**: `create_agent()` and `cleanup_agent()` handle agent lifecycle
- **Thread Management**: `create_thread()` and `delete_thread()` manage conversation contexts
- **Question Processing**: `ask_question()` handles individual interactions
- **Session Management**: `process_question()` and `interactive_mode()` orchestrate complete workflows

### 🔄 Architecture Overview

#### Modular Resource Management

```text
1. Create agent + resources
2. Create dedicated thread
3. Process question
4. Delete thread
5. Cleanup agent + resources
```

#### Interactive Session Architecture

```text
1. Create agent + resources
2. Create persistent thread
3. Process multiple questions (same thread)
4. Delete thread on exit
5. Cleanup agent + resources
```

### 💬 Usage Examples

#### Single Question Mode

```bash
# Use the default question
python home_loan_agent.py

# Ask a specific question
python home_loan_agent.py -q "What are the interest rates for FHA loans?"

# Ask about calculations
python home_loan_agent.py --question "Calculate monthly payment for $350,000 loan at 6.2% for 10, 20 and 30 years."
```

Each single question creates its own isolated session with dedicated thread management.

#### Interactive Session Mode

```bash
python home_loan_agent.py --interactive
```

In interactive mode, you can:

- Ask multiple questions in sequence within the **same conversation thread**
- The agent maintains conversation context between questions
- Reference previous questions and build upon earlier responses
- Type 'quit', 'exit', or 'q' to stop
- The agent and conversation thread persist throughout the entire session

**Example Interactive Session:**

```text
Your question: What documents do I need for a conventional loan?
[Agent provides document checklist...]

Your question: Can you calculate payments for a $400,000 loan with those requirements?
[Agent references previous context and performs calculations...]

Your question: What if I put down 25% instead of 20%?
[Agent builds on previous calculation context...]
```

### 📁 Required Files

Ensure these files exist in the same directory:

- `Contoso_Loan_Documentation_Checklist.md`
- `loan_product_eligibility_dataset.csv`

---

## 🔧 Customization & Extension Ideas

### 🏗️ Modular Architecture Benefits

The refactored code structure provides several advantages for customization:

- **Thread Management**: Separate `create_thread()` and `delete_thread()` functions make it easy to implement custom session handling
- **Resource Isolation**: Clean separation between agent lifecycle and thread lifecycle enables better resource management
- **Session Flexibility**: Easy to extend for different conversation patterns (e.g., multi-user sessions, conversation branching)
- **Error Handling**: Modular cleanup ensures proper resource disposal even when errors occur
- **Testing**: Individual components can be tested independently

### 🚀 Financial Planner Agent Extension

Transform the Home Loan Agent into a specialized tool within a comprehensive Financial Planner agent architecture:

#### 💰 Financial Planner Agent Configuration

**Agent Name**: `financial_planner`

**Instructions**:

```text
You are a financial planner that helps people perform financial planning and save for things. You are financially responsible and give responsible financial advice. You are for demonstration purposes only.
```

**Available Tools**:

- **Home Loan Agent Tool**
  - **Name**: `home_loan_agent`
  - **Activation Criteria**: "Activate when information about home loans and home loan requirements or application requirements are needed"
  - **Detailed Steps to Activate the Agent**:
    1. User asks questions related to mortgage loans, home buying, or loan documentation
    2. User requests calculations for mortgage payments, interest rates, or loan comparisons
    3. User needs guidance on loan application processes or eligibility requirements
    4. User inquires about specific loan products or documentation checklists

#### 🏗️ Implementation Architecture

```text
Financial Planner Agent (Main)
├── General financial planning and advice
├── Savings strategies and budgeting
├── Investment guidance
└── Home Loan Agent Tool (Specialized)
    ├── Mortgage calculations
    ├── Loan documentation guidance
    ├── Application requirements
    └── Loan product comparisons
```

#### 💡 Usage Examples

##### Scenario 1: Home Purchase Planning

- **User**: "I want to buy a house in 2 years. How should I prepare financially?"
- **Financial Planner**: Provides savings strategy, credit improvement tips
- **Activates Home Loan Agent**: When user asks "What documents will I need for the mortgage application?"

##### Scenario 2: Comprehensive Financial Review

- **User**: "I'm 30 years old, make $80k, and want to plan for homeownership and retirement"
- **Financial Planner**: Creates holistic financial plan
- **Activates Home Loan Agent**: When discussing mortgage affordability and loan options

##### Scenario 3: Refinancing Decision

- **User**: "Should I refinance my mortgage given current rates?"
- **Financial Planner**: Analyzes overall financial impact
- **Activates Home Loan Agent**: For detailed refinancing calculations and documentation requirements

#### 🔧 Technical Implementation

The modular architecture of the Home Loan Agent makes it ideal for integration as a specialized tool:

- **Clean Resource Management**: Each tool activation creates isolated agent and thread resources
- **Context Preservation**: Financial Planner maintains overall conversation context while delegating specialized tasks
- **Error Isolation**: Home Loan Agent tool failures don't affect the main Financial Planner session
- **Scalable Design**: Additional specialized agents (investment advisor, tax planner) can be added following the same pattern
