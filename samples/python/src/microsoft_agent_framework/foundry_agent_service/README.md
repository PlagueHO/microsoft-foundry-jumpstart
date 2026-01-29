# Microsoft Agent Framework with Microsoft Foundry Agent Service

This directory contains samples demonstrating how to use the
[Microsoft Agent Framework](https://github.com/microsoft/agent-framework) with
[Microsoft Foundry Agent Service](https://learn.microsoft.com/azure/ai-foundry/agents) for
both **development** (unpublished agents) and **production** (published agents) scenarios.

## Overview

Microsoft Foundry Agent Service supports two modes of operation:

| Mode | Endpoint | Use Case | API Availability |
|------|----------|----------|------------------|
| **Unpublished (Development)** | Project endpoint | Development, testing, debugging | Full Responses API (threads, files, vector stores, containers) |
| **Published (Production)** | Agent Application endpoint | Production, customer-facing | Limited API (only POST /responses, no server-side state storage) |

### Key Differences

When you **publish an agent** to become an Agent Application:

1. **Stable Endpoint**: The application gets a dedicated, stable URL that doesn't change across updates
2. **User Data Isolation**: Each user's interactions are isolated (not shared like in projects)
3. **Limited API**: Only `POST /responses` is available; `/conversations`, `/files`,
   `/vector_stores`, and `/containers` are **inaccessible**
4. **Client-Side State**: Conversation history must be stored on the client side
5. **RBAC Authentication**: Callers need Azure AI User role on the Agent Application resource

### Microsoft Agent Framework Advantages

The Microsoft Agent Framework abstracts these differences, allowing you to write code that
works in **both** environments with minimal changes:

- **Threads**: Framework provides client-side thread management via `AgentThread` and
  `ChatMessageStore` that work regardless of backend support
- **Tools**: Function calling works the same in both modes
- **Files**: For published agents, file content can be passed in-context rather than uploaded

## Samples

| Sample | Description |
|--------|-------------|
| [unpublished_agent.py](unpublished_agent.py) | Development mode using project endpoint with full API access |
| [published_agent.py](published_agent.py) | Production mode using application endpoint with client-side state |

## Prerequisites

- Python 3.8 or later
- Azure CLI installed and authenticated (`az login`)
- Microsoft Foundry project with an agent created
- Required Python packages (see [requirements.txt](requirements.txt))

## Environment Variables

Create a `.env` file or set these environment variables:

```bash
# For unpublished (development) agent
PROJECT_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<project-name>

# For published (production) agent
AZURE_AI_APPLICATION_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<project-name>/applications/<app-name>/protocols

# Model deployment name
MODEL_DEPLOYMENT_NAME=gpt-5.2-chat
```

## Installation

```bash
# Install Microsoft Agent Framework (preview)
pip install agent-framework --pre

# Install Azure dependencies
pip install azure-identity azure-ai-projects

# Or use requirements.txt
pip install -r requirements.txt
```

## Running the Samples

### Unpublished Agent (Development Mode)

```bash
# Basic usage
python unpublished_agent.py

# Interactive mode
python unpublished_agent.py --interactive
```

### Published Agent (Production Mode)

```bash
# Basic usage
python published_agent.py

# Interactive mode
python published_agent.py --interactive
```

## Architecture Notes

### Unpublished Agent Flow

```text
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client    │────▶│  Project Endpoint │────▶│  Agent Service  │
│ Application │◀────│  (Full API)       │◀────│  (Server State) │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │
                           ▼
                    ┌───────────────┐
                    │ Threads,      │
                    │ Files,        │
                    │ Vector Stores │
                    └───────────────┘
```

### Published Agent Flow

```text
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client    │────▶│  Application     │────▶│  Agent Service  │
│ Application │◀────│  Endpoint        │◀────│  (Stateless)    │
└─────────────┘     │  (POST /responses│     └─────────────────┘
       │            │   only)          │
       ▼            └──────────────────┘
┌──────────────┐
│ Local State  │
│ (Threads,    │
│ Files, etc.) │
└──────────────┘
```

## SDLC and DevOps Considerations

### The Environment Parity Challenge

A core DevOps principle is that **dev/test should mirror production** to catch issues early.
The Agent Service publish model creates a challenge: unpublished agents (dev/test) have
fundamentally different API capabilities than published agents (production):

| Capability | Dev/Test (Unpublished) | Production (Published) |
|------------|------------------------|------------------------|
| Thread management | Server-managed | Client-managed |
| File storage | Server `/files` API | In-context only |
| Vector stores | Dynamic creation | Pre-configured only |
| State persistence | Server handles it | Your responsibility |

**Without mitigation**, this means different code paths in dev vs production—an anti-pattern
that can lead to production-only bugs.

### How Microsoft Agent Framework Mitigates This

The framework's abstraction layer is the solution. By using framework components consistently,
your code follows the **same logical path** regardless of backend capabilities:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Your Application Code                        │
│  (Same code for dev and prod using Agent Framework abstractions)│
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│  Dev/Test Environment   │     │  Production Environment │
│  (Project Endpoint)     │     │  (Application Endpoint) │
│                         │     │                         │
│  Framework uses:        │     │  Framework uses:        │
│  • Server threads       │     │  • Client threads       │
│  • Server file storage  │     │  • In-context files     │
│  • Full API access      │     │  • POST /responses only │
└─────────────────────────┘     └─────────────────────────┘
```

**Key principle**: Write to the framework's abstractions, not directly to the underlying APIs.

### Recommended SDLC Workflow

```text
┌───────────┐     ┌───────────┐    ┌──────────┐    ┌──────────┐
│  Dev      │───▶│  Test     │───▶│  Staging │───▶│   Prod   │
│           │     │           │    │          │    │          │
│Unpublished│     │Unpublished│    │ Published│    │ Published│
│  Agent    │     │  Agent    │    │  Agent   │    │  Agent   │
└───────────┘     └───────────┘    └──────────┘    └──────────┘
     │               │               │               │
     └───────────────┴───────────────┴───────────────┘
                     Use Agent Framework
                     throughout all stages
```

**Stage-by-stage guidance:**

1. **Development**: Use unpublished agent with project endpoint for rapid iteration.
   Full API access enables debugging threads, inspecting file uploads, examining vector stores.

2. **Testing**: Continue with unpublished agent. Write integration tests using framework
   abstractions. Tests validate your application logic, not Agent Service internals.

3. **Staging**: **Publish the agent**. This is your first environment using the application
   endpoint. Verify client-side state management works correctly. This catches any
   accidental dependencies on server-side features.

4. **Production**: Deploy the same published agent configuration. Same endpoint pattern,
   same client-side state handling as staging.

### Enterprise Multi-Resource Pattern

> ⚠️ **Important**: The simple workflow above assumes a single AI Services resource.
> Most enterprises require **separate resources per environment**, often in different
> Azure subscriptions. This changes how the "publish" concept works.

**The Reality of Publishing**:

- Publishing creates an Agent Application *within the same AI Services resource*
- There is **no native mechanism** to promote a published agent to another resource
- Publishing is **not like deploying a container image** through environments

**Implication**: Your agent definition must be recreated in each environment's AI Services
resource. The **agent definition becomes your deployable artifact**, not the published agent.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        Source Control (Git)                             │
│         agent-definition.json / Bicep / Terraform / Pulumi              │
│                                                                         │
│  Contains: instructions, model config, tools, vector store refs, files  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
           CI/CD Pipeline applies agent definition to each environment
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Dev Subscription│     │ Staging Sub     │      │  Prod Sub       │
│  ───────────────│      │ ───────────────│      │  ───────────────│
│  AI Services    │      │  AI Services    │      │  AI Services    │
│  Resource       │      │  Resource       │      │  Resource       │
│                 │      │                 │      │                 │
│  Agent created  │      │  Agent created  │      │  Agent created  │
│  (unpublished)  │      │  + Published    │      │  + Published    │
│                 │      │  to App         │      │  to App         │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │                        │
    Full API for dev         Published API            Published API
```

**Agent-as-Code Pattern** (recommended for enterprise):

```jsonc
// agent-definition.json - checked into source control
{
  "name": "customer-support-agent",
  "model": "gpt-4o",
  "instructions": "You are a helpful customer support agent...",
  "tools": [
    { "type": "function", "function": { "name": "lookup_order", ... } },
    { "type": "file_search" }
  ],
  "tool_resources": {
    "file_search": {
      "vector_store_ids": ["${VECTOR_STORE_ID}"]  // Injected per environment
    }
  }
}
```

**CI/CD Pipeline Steps**:

1. **Build**: Validate agent definition schema, lint instructions
2. **Deploy to Dev**: Create/update agent in Dev AI Services (unpublished)
3. **Test in Dev**: Run integration tests against project endpoint
4. **Deploy to Staging**: Create/update agent in Staging AI Services, then **publish**
5. **Test in Staging**: Validate against application endpoint (published API surface)
6. **Deploy to Prod**: Create/update agent in Prod AI Services, then **publish**

**What Must Be Environment-Specific**:

| Component | Same Across Envs | Per-Environment |
|-----------|------------------|-----------------|
| Agent instructions | ✅ | |
| Tool definitions | ✅ | |
| Model selection | ✅ (usually) | Sometimes different for cost |
| Vector store IDs | | ✅ Created per resource |
| File IDs | | ✅ Uploaded per resource |
| Connection strings | | ✅ Point to env-specific backends |
| AI Services endpoint | | ✅ Different resources |

**Vector Store and File Handling**:

Since vector stores and files are resource-scoped, your pipeline must:

1. Upload source documents to each environment's AI Services
2. Create vector stores in each environment
3. Capture the resulting IDs and inject them into agent definition
4. Create the agent with environment-specific resource references

```yaml
# Example Azure DevOps / GitHub Actions step
- name: Create vector store and deploy agent
  run: |
    # Upload files and create vector store in target environment
    VECTOR_STORE_ID=$(az ai foundry vector-store create --files ./knowledge-base/*.pdf)
    
    # Substitute into agent definition
    envsubst < agent-definition.template.json > agent-definition.json
    
    # Create/update agent
    az ai foundry agent create --definition agent-definition.json
    
    # Publish (staging/prod only)
    if [[ "$ENVIRONMENT" != "dev" ]]; then
      az ai foundry agent publish --name customer-support-agent
    fi
```

### Trade-offs and Limitations of This Model

This enterprise pattern works, but it's important to acknowledge the friction points:

| Concern | Traditional DevOps | Agent Service Reality |
|---------|-------------------|----------------------|
| Artifact promotion | Build once, deploy everywhere | Recreate in each environment |
| Environment drift | Identical artifacts prevent it | Agent definitions could diverge |
| Rollback | Redeploy previous artifact | Republish previous definition |
| Audit trail | Artifact registry has history | Must rely on source control |

**Mitigations**:

- **Treat source control as your artifact registry** for agent definitions
- **Use infrastructure-as-code** (Bicep/Terraform) to ensure consistent resource setup
- **Automate everything**—manual agent creation invites environment drift
- **Tag releases** in Git; correlate deployments to commits
- **Consider GitOps** patterns where environments sync from source control

**Why Microsoft Agent Framework Still Helps**:

Even with the multi-resource complexity, the framework provides value:

1. **Your application code stays the same** across all environments
2. **Endpoint type becomes configuration**, not code branches
3. **Client-side thread handling** works regardless of publish state
4. **Testing your integration code** is valid even if agent definitions differ slightly

The framework doesn't solve the agent definition promotion problem, but it ensures your
*application code* follows DevOps best practices even when the *agent infrastructure*
requires per-environment recreation.

### Best Practices for Environment Parity

1. **Always use Agent Framework abstractions**
   - Use `ChatAgent` and `AgentThread`, not raw API calls
   - Let the framework handle thread storage differences
   - Pass files as content, don't rely on `/files` API in core logic

2. **Configure, don't code, the differences**
   - Endpoint URL is configuration, not code
   - Use environment variables: `PROJECT_ENDPOINT` vs `AZURE_AI_APPLICATION_ENDPOINT`
   - Same codebase, different `.env` files per environment

3. **Test with published agents in staging**
   - Don't wait until production to discover published agent limitations
   - Staging should match production's API surface exactly

4. **Pre-configure resources before publishing**
   - Vector stores needed in production must be created at agent definition time
   - Files referenced by the agent must be attached before publishing
   - Knowledge bases should be fully indexed before publish

5. **Design for statelessness from the start**
   - Even in dev, treat each request as potentially stateless
   - Store conversation history in your own data store
   - Don't assume server-side thread persistence

### What the Framework Handles vs What You Handle

| Concern | Framework Handles | You Handle |
|---------|-------------------|------------|
| Thread creation | ✅ Automatic | |
| Message history | ✅ `ChatMessageStore` | |
| Tool invocation | ✅ Same pattern both modes | |
| Credential flow | ✅ `AzureAIClient` | |
| Endpoint selection | | ✅ Configuration |
| Conversation persistence | | ✅ External storage |
| File content delivery | | ✅ In-context for published |
| Pre-publish resource setup | | ✅ Vector stores, files |

## Known Gaps in Microsoft Agent Framework (Preview)

As Microsoft Agent Framework is currently in **preview**, the following limitations exist:

1. **No direct Microsoft Foundry Application endpoint support in agent-framework.azure module**:
   As of the preview, direct integration with published Agent Applications requires using
   the OpenAI-compatible endpoint directly. The framework's `AzureAIProjectAgentProvider`
   works with project endpoints but not application endpoints.

2. **File upload during published agent runs**: Published agents cannot access `/files` API,
   so files must be passed as context in the message content.

3. **Vector store creation**: Published agents cannot create vector stores dynamically;
   these should be configured at the agent definition level before publishing.

4. **Server-side thread management**: The `azure-ai-projects` V2 SDK thread APIs are not
   available through published agent endpoints; use client-side `ChatMessageStore` instead.

## References

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/agent-framework/)
- [Microsoft Foundry Agents](https://learn.microsoft.com/azure/ai-foundry/agents/)
- [Publishing Agents](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/publish-agent)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
