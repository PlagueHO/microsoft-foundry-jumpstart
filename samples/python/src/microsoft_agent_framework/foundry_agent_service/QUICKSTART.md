# Quick Start Guide

Get the Azure Architect Agent samples running in 5 minutes.

## Prerequisites

- Python 3.8 or later
- Azure CLI (`az login` already authenticated)
- Microsoft Foundry project created

## 1. Install Dependencies

```bash
pip install agent-framework --pre
pip install azure-identity azure-ai-projects azure-cosmos redis
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

## 2. Configure Environment

Create a `.env` file in this directory:

```bash
# For Development (Unpublished Agent)
PROJECT_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<project-name>

# For Production (Published Agent) - Optional
AZURE_AI_APPLICATION_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<project-name>/applications/<app-name>/protocols

# Model deployment - Optional (defaults to gpt-5-mini)
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5-mini

# Persistent storage - Optional
COSMOS_DB_CONNECTION_STRING=AccountEndpoint=https://...
REDIS_URL=redis://localhost:6379
```

**Finding your endpoints:**

- **Project Endpoint**: In Azure AI Foundry portal, go to your project → Settings → copy the Project endpoint
- **Application Endpoint**: After publishing an agent, go to Applications → your app → copy the endpoint

## 3. Run the Samples

### Development Mode (Unpublished Agent)

Quick demo with hosted MCP:

```bash
python unpublished_agent.py --hosted-mcp
```

Interactive chat:

```bash
python unpublished_agent.py --hosted-mcp --interactive
```

Ask specific questions:

```bash
python unpublished_agent.py --hosted-mcp -q "Design a web app with Azure App Service and SQL Database"
```

With persistent chat (Cosmos DB):

```bash
python unpublished_agent.py --hosted-mcp --cosmos
```

### Production Mode (Published Agent)

> **Note**: Requires a published Agent Application in Foundry

Quick demo:

```bash
python published_agent.py --hosted-mcp
```

Interactive mode:

```bash
python published_agent.py --local-mcp --interactive
```

## 4. Understanding the Options

| Option | Description |
|--------|-------------|
| `--hosted-mcp` | Server-side MCP execution (production-ready) |
| `--local-mcp` | Client-side MCP execution (development/debugging) |
| `--cosmos` | Enable Cosmos DB persistent chat (unpublished only) |
| `--interactive` | Multi-turn conversation mode |
| `-q "question"` | Ask a specific question |

## Common Questions

**Q: Which sample should I start with?**  
A: Start with `unpublished_agent.py --hosted-mcp` for development.

**Q: What's the difference between unpublished and published?**  
A: Unpublished = development mode with full API access. Published = production mode with stable endpoint and limited API.

**Q: Do I need Cosmos DB or Redis?**  
A: No, these are optional for persistent chat across sessions. The samples work without them.

**Q: What if I don't have a published agent?**  
A: Just use `unpublished_agent.py` - you don't need a published agent for development.

**Q: Where do I create an agent in Foundry?**  
A: For unpublished mode, the agent is created programmatically - you don't need to create it manually. For published mode, you must create and publish an Agent Application in the Azure AI Foundry portal first.

## Troubleshooting

**Error: "PROJECT_ENDPOINT environment variable is required"**  
→ Set `PROJECT_ENDPOINT` in your `.env` file or environment.

**Error: "Required packages not installed"**  
→ Run `pip install agent-framework --pre azure-identity azure-ai-projects`

**Error: Authentication failed**  
→ Run `az login` to authenticate with Azure CLI.

**Error: "AZURE_AI_APPLICATION_ENDPOINT environment variable required"**  
→ You're running `published_agent.py` but haven't set the application endpoint. Either:

- Set the variable for published agents, OR
- Use `unpublished_agent.py` instead for development

**Error: "Model deployment name is required"**  
→ Set `AZURE_AI_MODEL_DEPLOYMENT_NAME` in your `.env` file to match a model deployment in your Azure AI Foundry project (e.g., `gpt-5-mini`, `gpt-5.2-chat`, `gpt-4o-mini`).

**Error: "Timed out waiting for Azure CLI" or "CredentialUnavailableError"**  
→ Authentication issues. Try these steps:

  1. Run `az login` again to refresh your credentials
  2. Run `az account show` to verify you're logged in
  3. If the issue persists, set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, and `AZURE_CLIENT_SECRET` environment variables for service principal authentication

## Next Steps

- Read [README.md](README.md) for comprehensive documentation
- Explore MCP vs local tool execution differences
- Learn about persistent chat with Cosmos DB or Redis
- Understand the SDLC workflow for production deployment

## Example Session

```bash
$ python unpublished_agent.py --hosted-mcp --interactive

=== AZURE ARCHITECT - INTERACTIVE MODE ===
Ask about Azure architecture, costs, or IaC generation.
Type 'quit' to exit.

You: I need a web app with SQL database

[Processing with MCP + local tools...]

Architect: I'll help you design this solution. Based on Azure 
best practices, I recommend:

1. Azure App Service (Web App)
   - Supports .NET, Python, Node.js, Java, PHP
   - Auto-scaling capabilities
   - Built-in CI/CD

2. Azure SQL Database
   - Managed service with high availability
   - Point-in-time restore
   - Automatic backups

Let me estimate the costs and validate the architecture...

[Calls estimate_azure_costs and validate_architecture tools]

Estimated monthly cost: $150-$300
Architecture validation: ✓ Security, ✓ Reliability...

You: Generate Bicep for the App Service

[Calls generate_bicep_snippet tool]

Architect: Here's the Bicep template for Azure App Service:

resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: 'my-web-app'
  location: location
  ...
}

You: quit
```

## Support

For detailed documentation, architecture patterns, and DevOps workflows, see:

- [README.md](README.md) - Full documentation
- [Microsoft Agent Framework Docs](https://learn.microsoft.com/agent-framework/)
- [Azure AI Foundry Agents](https://learn.microsoft.com/azure/ai-foundry/agents/)
