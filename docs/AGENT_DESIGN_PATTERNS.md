# Microsoft Foundry Agent Design Patterns

This document defines the distinct architectural patterns for building AI agent solutions with Microsoft Foundry. Each pattern represents a different combination of where the orchestration loop runs, where tools execute, and what Foundry services are involved.

> [!NOTE]
> This document covers only patterns using the **Responses API** surface area (Foundry Agent Service v2). It does not cover the deprecated Assistants API (v1 threads/runs model). For a deep comparison of server-side vs client-side tool calling mechanics, see [RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md](RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md).

## Pattern Overview

| Pattern | Orchestration | Agent Registered on Foundry | Tools Execute | Compute |
|---------|---------------|----------------------------|---------------|---------|
| [1. Prompt Agent — Fully Server-Side](#pattern-1-prompt-agent--fully-server-side) | Foundry Agent Service | Yes (`PromptAgentDefinition`) | Server-side | Foundry-managed |
| [2. Prompt Agent — Hybrid](#pattern-2-prompt-agent--hybrid-server--client-function-calling) | Foundry + Client | Yes (`PromptAgentDefinition`) | Server-side + Client-side | Foundry + Your app |
| [3. Workflow Agent](#pattern-3-workflow-agent) | Foundry Agent Service | Yes (Declarative YAML) | Server-side | Foundry-managed |
| [4. Hosted Agent](#pattern-4-hosted-agent) | Your code on Foundry | Yes (`HostedAgentDefinition`) | Your code | Foundry-managed containers |
| [5. Client-Side Orchestration via Responses API](#pattern-5-client-side-orchestration-via-responses-api) | Your code | No | Client-side | Your compute |
| [6. Client-Side Orchestration via Stateless Models](#pattern-6-client-side-orchestration-via-stateless-models) | Your code | No | Client-side | Your compute |

> See [agent-design-patterns.drawio](diagrams/agent-design-patterns.drawio) for interactive diagrams (open in draw.io or VS Code Draw.io Integration extension). The file contains tabs for each pattern.

---

## Pattern 1: Prompt Agent — Fully Server-Side

### Description

A named, versioned agent is registered in Foundry Agent Service v2 with a `PromptAgentDefinition`. All configured tools (Web Search, Code Interpreter, File Search, MCP, OpenAPI, Azure AI Search, etc.) execute server-side within the Agent Service. The client sends a single `POST /responses` with an `agent_reference` and receives the final answer. The entire ReAct loop (reason → tool call → observe → repeat) runs inside Foundry.

### Architecture

![Pattern 1 prompt agent architecture](diagrams/pattern-1-prompt-agent-architecture.svg)

> **Diagram**: See [pattern-1-prompt-agent-architecture.drawio](diagrams/pattern-1-prompt-agent-architecture.drawio) — open in draw.io or the VS Code Draw.io Integration extension.

### When to Use

- Rapid prototyping and internal tools
- Agents that only need Foundry's built-in tools (web search, code interpreter, file search, MCP servers, OpenAPI)
- You want to publish to Teams/M365 Copilot
- Zero-trust networking with private endpoints (supported for prompt agents)
- You don't need custom server-side logic

### Key Characteristics

- **1 network round-trip** (or 2 with MCP approval)
- **No client-side loop** — fire and forget
- **Agent identity** manages tool credentials server-side
- **Conversation state** managed by Foundry (conversations, memory)
- **Full observability** — Application Insights, tracing, continuous evaluation
- **Private networking** — fully supported
- **Tools are fixed at creation time** — all tools must be defined in `create_version`; you cannot pass additional `tools` in the `POST /responses` request when using `agent_reference` (see [Known limitation](#known-limitation-tools-cannot-be-added-at-invocation-time) below)

### Code Example

```python
# Create agent (once)
agent = project.agents.create_version(
    agent_name="support-agent",
    definition=PromptAgentDefinition(
        model="gpt-4o",
        instructions="You are a helpful support assistant.",
        tools=[WebSearchTool(), FileSearchTool(vector_store_ids=["vs_123"])],
    ),
)

# Invoke agent (per request) — single round-trip, Foundry handles everything
response = openai.responses.create(
    input="How do I reset my password?",
    extra_body={"agent_reference": {"name": "support-agent", "type": "agent_reference"}},
)
print(response.output_text)
```

### References

- [What is Microsoft Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/overview)
- [Build with agents, conversations, and responses](https://learn.microsoft.com/azure/foundry/agents/concepts/runtime-components)
- [Agent tools overview](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-catalog)
- [Publish and share agents](https://learn.microsoft.com/azure/foundry/agents/how-to/publish-agent)

---

## Pattern 2: Prompt Agent — Hybrid (Server + Client Function Calling)

### Description

A prompt agent is registered on Foundry with **both** server-side tools (MCP, Code Interpreter, etc.) **and** function calling tools. The Agent Service runs server-side tools internally but **pauses and returns control to the client** when the model requests a function call. The client executes the function, submits `function_call_output` via `POST /responses` with `previous_response_id`, and Foundry resumes — potentially calling more server-side tools before returning the final answer.

This is the most common pattern for production applications that need to extend Foundry's built-in capabilities with custom business logic.

### Architecture

![Pattern 2 prompt agent hybrid architecture](diagrams/pattern-2-prompt-agent-hybrid-architecture.svg)

> **Diagram**: See [pattern-2-prompt-agent-hybrid-architecture.drawio](diagrams/pattern-2-prompt-agent-hybrid-architecture.drawio) — open in draw.io or the VS Code Draw.io Integration extension.

### When to Use

- You need Foundry's built-in tools (search, code interpreter, MCP) **and** custom business logic that only your app can perform
- Internal APIs not exposed via MCP or OpenAPI
- Proprietary data enrichment, validation, or transformation
- Progressive migration: start fully server-side, add function tools as custom requirements emerge
- Human-in-the-loop approval for sensitive server-side MCP calls (via `mcp_approval_request`)

### Key Characteristics

- **2N+1 round-trips** where N = number of function calls (server-side tools add zero additional round-trips)
- **Server-side tool credentials** stay isolated in Foundry
- **Client must handle** the function call loop (or use Agent Framework which abstracts it)
- **Agent identity** handles server-side tool auth; **your app's identity** handles function tool auth
- **Conversation state** managed by Foundry
- **Tools are fixed at creation time** — both server-side and function calling tools must be defined in `create_version`; you cannot pass additional `tools` alongside `agent_reference` at invocation time (see [Known limitation](#known-limitation-tools-cannot-be-added-at-invocation-time) below)

### Code Example

```python
# Agent with both server-side (web_search) and client-side (function) tools
func_tool = FunctionTool(
    name="get_crm_record",
    parameters={
        "type": "object",
        "properties": {"customer_id": {"type": "string"}},
        "required": ["customer_id"],
    },
    description="Look up customer details from the CRM system.",
    strict=True,
)

agent = project.agents.create_version(
    agent_name="support-hybrid",
    definition=PromptAgentDefinition(
        model="gpt-4o",
        instructions="Search the web for general info. Use get_crm_record for customer details.",
        tools=[WebSearchTool(), func_tool],
    ),
)

# Invoke — the response may contain function_call items
response = openai.responses.create(
    input="What's the status of customer CUST-1234's latest order?",
    extra_body={"agent_reference": {"name": "support-hybrid", "type": "agent_reference"}},
)

# Handle function calls
input_list = []
for item in response.output:
    if item.type == "function_call" and item.name == "get_crm_record":
        result = call_crm_api(**json.loads(item.arguments))  # YOUR CODE
        input_list.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(result),
        })

# Feed results back — Foundry resumes the loop
final = openai.responses.create(
    input=input_list,
    previous_response_id=response.id,
    extra_body={"agent_reference": {"name": "support-hybrid", "type": "agent_reference"}},
)
print(final.output_text)
```

### References

- [Function calling with Foundry agents](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/function-calling)
- [Tool best practices](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-best-practice)
- [MCP tool approval](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol)
- [RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md](RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md) — detailed hybrid flow analysis

---

## Known Limitation: Tools Cannot Be Added at Invocation Time

> [!IMPORTANT]
> **Applies to Patterns 1 and 2** (any pattern using `agent_reference` in `POST /responses`).

When invoking a stored agent via `POST /responses` with `agent_reference`, the Responses API **rejects** the `tools` parameter:

```text
openai.BadRequestError: 400 - 'Not allowed when agent is specified'
```

**All tools — both server-side (MCP, Code Interpreter, File Search, etc.) and client-side (function calling) — must be defined at agent creation time** via `create_version`. You cannot dynamically add, remove, or override tools at invocation time.

### Impact

| Scenario | Supported? | Workaround |
|----------|-----------|------------|
| Agent with fixed tools across all requests | ✅ Yes | N/A — Patterns 1 and 2 work as designed |
| Different tool sets per request or per user | ❌ No | Create separate agent versions per tool set, or use [Pattern 5](#pattern-5-client-side-orchestration-via-responses-api) (client-side orchestration) |
| Adding a client-discovered MCP server at invocation time | ❌ No | Use [Pattern 5](#pattern-5-client-side-orchestration-via-responses-api) where all tools are passed per-request |
| Parameterizing existing tool configs at invocation time | ⚠️ Partial | `structured_inputs` can inject values (e.g., vector store IDs) into tools defined at creation, but cannot add new tool schemas |

### Microsoft Agent Framework behavior

The [Agent Framework](https://learn.microsoft.com/agent-framework/overview/) SDKs enforce this constraint:

- **Python**: `AzureAIAgentClient._remove_agent_level_run_options()` explicitly strips runtime tool overrides with a warning: _"AzureAIClient does not support runtime tools overrides after agent creation. Use AzureOpenAIResponsesClient instead."_ `FoundryAgentChatClient._prepare_options()` raises `TypeError` for non-`FunctionTool` types at runtime.
- **.NET**: The `PersistentAgentsClient` silently ignores tools passed at invocation time when using a stored agent.

### Recommended workaround

Use **[Pattern 5: Client-Side Orchestration via Responses API](#pattern-5-client-side-orchestration-via-responses-api)** with `AzureOpenAIResponsesClient` (Python) or `AzureOpenAIClient.GetChatClient()` (.NET). In client-side orchestration, tools are defined per-request — there is no `agent_reference` and no creation-time constraint. This enables combining any tool types (MCP, function calling, etc.) dynamically at invocation time.

See the [hybrid tool calling samples](../samples/README.md) for working examples and [RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md](RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md#known-limitation-all-tools-must-be-defined-at-agent-creation-time) for the full technical analysis.

---

## Pattern 3: Workflow Agent

### Description

Workflow agents orchestrate a sequence of actions or coordinate multiple agents using declarative definitions. Build workflows visually in the Foundry portal or define them in YAML through Visual Studio Code. Workflows support branching logic, human-in-the-loop steps, and sequential or group-chat multi-agent patterns — all without writing custom code.

### Architecture

![Pattern 3 workflow agent architecture](diagrams/pattern-3-workflow-agent-architecture.svg)

> **Diagram**: See [pattern-3-workflow-agent-architecture.drawio](diagrams/pattern-3-workflow-agent-architecture.drawio) — open in draw.io or the VS Code Draw.io Integration extension.

### When to Use

- Multi-step orchestration (e.g., research → classify → act)
- Agent-to-agent coordination without custom code
- Approval workflows with human-in-the-loop
- Repeatable automation pipelines
- Teams that prefer visual or declarative development over code

### Key Characteristics

- **No code required** (YAML optional via VS Code)
- **Fully managed** — Foundry runs the workflow
- **Multi-agent** — coordinate prompt agents, hosted agents, or external agents
- **Branching logic** — conditional routing based on agent outputs
- **Private networking** — supported
- **Preview** — currently in public preview

### References

- [What are workflow agents](https://learn.microsoft.com/azure/foundry/agents/concepts/workflow)
- [Agent types overview](https://learn.microsoft.com/azure/foundry/agents/overview#agent-types)

---

## Pattern 4: Hosted Agent

### Description

You write the orchestration logic in code — using Microsoft Agent Framework, LangGraph, or custom code — containerize it, push to Azure Container Registry, and register it with Foundry Agent Service. Foundry runs your container on managed pay-as-you-go infrastructure and handles scaling, identity, conversation state, versioning, and publishing. Callers invoke it via the same Responses API surface as prompt agents.

The key differentiator: **your code controls the orchestration**, but Foundry manages everything else (compute, networking, identity, state, observability).

### Architecture

![Pattern 4 hosted agent architecture](diagrams/pattern-4-hosted-agent-architecture.svg)

> **Diagram**: See [pattern-4-hosted-agent-architecture.drawio](diagrams/pattern-4-hosted-agent-architecture.drawio) — open in draw.io or the VS Code Draw.io Integration extension.

### When to Use

- Complex multi-agent orchestration with custom logic
- Tools that need to run in your process (local computation, proprietary ML models, direct database access)
- Agent-to-agent coordination with custom routing
- You want managed compute without managing infrastructure
- You want to publish to Teams/M365 Copilot with a code-based agent

### Key Characteristics

- **Your code, Foundry's compute** — you control behavior, Foundry manages infra
- **Hosting adapter** abstracts Responses API ↔ your framework
- **Managed identity** — project MI for unpublished, dedicated MI for published
- **Versioning** — container image changes create new versions
- **Observability** — OpenTelemetry export to Application Insights
- **Private networking** — **NOT supported** during preview
- **Preview** — currently in public preview

### Code Example

```python
from agent_framework import ai_function, ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.ai.agentserver.agentframework import from_agent_framework
from azure.identity import DefaultAzureCredential

@ai_function
def query_inventory(product_id: str) -> str:
    """Check real-time inventory — runs in YOUR container."""
    return db.query("SELECT stock FROM inventory WHERE id = %s", (product_id,))

agent = ChatAgent(
    chat_client=AzureAIAgentClient(
        project_endpoint=PROJECT_ENDPOINT,
        model_deployment_name="gpt-4o",
        credential=DefaultAzureCredential(),
    ),
    instructions="You help customers check product availability.",
    tools=[query_inventory],
)

# Hosting adapter exposes this as the Responses API
if __name__ == "__main__":
    from_agent_framework(agent).run()  # Starts HTTP server on :8088
```

### References

- [What are hosted agents](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
- [Deploy your first hosted agent](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)
- [Hosted agent samples (Python)](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents)
- [Hosted agent samples (C#)](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/csharp/hosted-agents)

---

## Pattern 5: Client-Side Orchestration via Responses API

### Description

Your application calls the Responses API **directly** (without an `agent_reference`) with tools defined per-request. The Responses API handles built-in tool execution (code interpreter, MCP, web search) server-side but returns `function_call` items for custom functions. Your code manages the ReAct loop: detect tool calls → execute → feed results back → repeat until no more tool calls.

No agent is registered on Foundry. There is no agent name, no versioning, no publishing. The Responses API is used as a stateful model endpoint with tool-calling capabilities.

Frameworks like **Microsoft Agent Framework** or **Semantic Kernel** can fully abstract this loop — you write `agent.Run()` and the framework handles the detect-execute-feed cycle automatically.

### Architecture

![Pattern 5 client-side responses architecture](diagrams/pattern-5-client-side-responses-architecture.svg)

> **Diagram**: See [pattern-5-client-side-responses-architecture.drawio](diagrams/pattern-5-client-side-responses-architecture.drawio) — open in draw.io or the VS Code Draw.io Integration extension.

### When to Use

- You want Responses API features (stateful chaining, truncation, compaction, built-in tools) without managing agent definitions
- Ad-hoc or ephemeral agent behavior — tools change per request
- You're using Agent Framework or Semantic Kernel and want client-side orchestration with the Responses API backend
- You don't need publishing, versioning, or Foundry-managed conversations
- Private networking is required (and hosted agents don't support it yet)
- **You need per-request tool flexibility** — tools vary by request or are discovered dynamically at runtime (this is the workaround for the [agent_reference + tools limitation](#known-limitation-tools-cannot-be-added-at-invocation-time))

### Key Characteristics

- **No agent registered** on Foundry
- **Responses API features** still available (`previous_response_id`, `store`, `compact`, `truncation`)
- **Built-in tools** (code_interpreter, MCP, web_search) still execute server-side
- **Function tools** execute client-side
- **Your code manages** the ReAct loop (frameworks abstract this)
- **No publishing** — no Teams/M365 Copilot distribution
- **No agent-level observability** — you instrument yourself
- **Private networking** — fully supported (it's just an API call)

### Code Example (with Agent Framework)

```python
from agent_framework import ai_function, ChatAgent
from agent_framework.azure import AzureOpenAIResponsesClient

@ai_function
def check_order(order_id: str) -> str:
    """Check order status in your system."""
    return orders_db.get_status(order_id)

# Agent Framework manages the ReAct loop client-side
agent = ChatAgent(
    chat_client=AzureOpenAIResponsesClient(endpoint=ENDPOINT, credential=cred),
    instructions="You help customers track orders.",
    tools=[check_order],
)
result = await agent.run("Where is order ORD-5678?")
```

### Code Example (manual loop)

```python
# No agent_reference — tools defined per request
response = openai.responses.create(
    model="gpt-4o",
    tools=[{"type": "function", "name": "check_order", ...}],
    input="Where is order ORD-5678?",
)

# Client manages the loop
while any(item.type == "function_call" for item in response.output):
    outputs = []
    for item in response.output:
        if item.type == "function_call":
            result = execute_function(item.name, item.arguments)
            outputs.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result,
            })

    response = openai.responses.create(
        input=outputs,
        previous_response_id=response.id,
        model="gpt-4o",
        tools=[{"type": "function", "name": "check_order", ...}],
    )

print(response.output_text)
```

### References

- [Use the Azure OpenAI Responses API](https://learn.microsoft.com/azure/foundry/openai/how-to/responses)
- [Function calling in Responses API](https://learn.microsoft.com/azure/foundry/openai/how-to/responses#function-calling)
- [Microsoft Agent Framework providers](https://learn.microsoft.com/agent-framework/agents/providers/)

---

## Pattern 6: Client-Side Orchestration via Stateless Models

### Description

Your application calls Foundry model endpoints directly (Chat Completions API or Responses API **without** tool definitions) and manages **all** orchestration in your own code. Foundry is used purely as an LLM inference endpoint — no Agent Service, no built-in tools, no server-side state. Frameworks like **Semantic Kernel**, **Microsoft Agent Framework** (with ChatClient), or **LangChain** manage the agent loop, tool execution, context window, and conversation state entirely client-side.

This is the most flexible pattern and the only one that works with non-Foundry model endpoints (Ollama, Anthropic, etc.) via Agent Framework's provider abstraction.

### Architecture

![Pattern 6 client-side stateless architecture](diagrams/pattern-6-client-side-stateless-architecture.svg)

> **Diagram**: See [pattern-6-client-side-stateless-architecture.drawio](diagrams/pattern-6-client-side-stateless-architecture.drawio) — open in draw.io or the VS Code Draw.io Integration extension.

### When to Use

- Full control over every aspect of agent behavior
- Strict data residency — nothing leaves your compute except model inference
- Private networking with zero-trust (VNet + private endpoints)
- You need to integrate with non-Foundry model providers
- Existing investment in Semantic Kernel or LangChain
- Complex custom orchestration (state machines, conditional logic, parallel tool execution, caching)
- Foundry is just one of multiple LLM backends

### Key Characteristics

- **No Foundry Agent Service involvement** — model inference only
- **All state is client-managed** — conversation history, tool results, context
- **All tools execute client-side** — no server-side built-in tools
- **No Responses API features** if using Chat Completions — no `previous_response_id`, no compaction, no truncation (you manage the context window yourself)
- **Full private networking** — just needs a PE to the model endpoint
- **No publishing** — no Teams/M365 Copilot (would need custom Bot Framework integration)
- **Provider-portable** — same code works with Ollama, Anthropic, etc.
- **You build observability** — no built-in dashboards

### Code Example (Semantic Kernel — C#)

```csharp
var kernel = Kernel.CreateBuilder()
    .AddAzureOpenAIChatCompletion("gpt-4o", endpoint, credential)
    .Build();

kernel.Plugins.AddFromType<OrderPlugin>();

var agent = new ChatCompletionAgent
{
    Name = "OrderAssistant",
    Instructions = "You help customers track orders.",
    Kernel = kernel,
};

var history = new ChatHistory();
history.AddUserMessage("Where is order ORD-5678?");
await foreach (var msg in agent.InvokeStreamingAsync(history))
{
    Console.Write(msg.Content);
}
```

### Code Example (Agent Framework — Python)

```python
from agent_framework import ai_function, ChatAgent
from agent_framework.azure import AzureOpenAIChatClient

@ai_function
def check_order(order_id: str) -> str:
    """Check order status."""
    return orders_db.get_status(order_id)

agent = ChatAgent(
    chat_client=AzureOpenAIChatClient(endpoint=ENDPOINT, credential=cred),
    instructions="You help customers track orders.",
    tools=[check_order],
)
result = await agent.run("Where is order ORD-5678?")
```

### References

- [Semantic Kernel overview](https://learn.microsoft.com/semantic-kernel/overview/)
- [Microsoft Agent Framework providers](https://learn.microsoft.com/agent-framework/agents/providers/)
- [Azure OpenAI Chat Completions](https://learn.microsoft.com/azure/foundry/openai/how-to/chatgpt)
- [Deployment types](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/deployment-types)

---

## Decision Guide

```text
                       Do you need Foundry Agent Service?
                                    │
                    ┌───── YES ──────┴────── NO ──────┐
                    │                                  │
              Do you need                    Do you want Responses
              custom code for                API features?
              orchestration?                 (state, compaction,
                    │                        built-in tools)
           ┌── YES ─┴── NO ──┐                   │
           │                  │            ┌─ YES ─┴── NO ──┐
     Must Foundry       Do you need        │                │
     manage compute?    multi-agent        Pattern 5        Pattern 6
           │            workflows?         Client-side      Stateless
     ┌─ YES┴─ NO ─┐         │             + Responses API  models
     │             │    ┌─YES┴─ NO ─┐
  Pattern 4     Pattern 2  │        │
  Hosted Agent  Hybrid   Pattern 3  Pattern 1
  (your code,  (server + Workflow   Prompt Agent
   Foundry      client   Agent      (fully
   compute)     tools)              server-side)
```

### Quick Decision Criteria

| If you need... | Use Pattern |
|----------------|-------------|
| Fastest time to working agent, no code | **1 (Prompt Agent)** or **3 (Workflow Agent)** |
| Built-in tools + custom business logic | **2 (Hybrid)** |
| Multi-agent orchestration without code | **3 (Workflow Agent)** |
| Full code control but managed compute | **4 (Hosted Agent)** |
| Responses API features without agent definitions | **5 (Client-Side + Responses API)** |
| Maximum control, provider portability, VNet isolation | **6 (Client-Side + Stateless Models)** |
| Publishing to Teams / M365 Copilot | **1, 2, 3, or 4** |
| Private networking (today) | **1, 2, 3, 5, or 6** (not 4 during preview) |

---

## Cross-Cutting Concerns

### Microsoft Agent Framework Across Patterns

[Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/overview/) provides a unified `AIAgent` interface that works across Patterns 1, 2, 4, 5, and 6. The same `agent.Run()` call works regardless of backend — only the provider configuration changes:

| Pattern | Agent Framework Provider | ReAct Loop |
|---------|------------------------|------------|
| 1 & 2 | `AzureAIProjectAgentProvider` / `PersistentAgentsClient` | Server-side (Framework delegates to Agent Service) |
| 4 | Hosting adapter (`from_agent_framework`) | Your code (Framework runs locally in container) |
| 5 | `AzureOpenAIResponsesClient` / `OpenAIResponsesClient` | Client-side (Framework manages loop) |
| 6 | `AzureOpenAIChatClient` / `OpenAIChatClient` | Client-side (Framework manages loop) |

This means you can **develop locally against Pattern 6** (stateless models, fast iteration) and **deploy in production as Pattern 1 or 4** (managed infrastructure, observability) with the same agent code.

### Private Networking Support

| Pattern | Private Networking | Notes |
|---------|-------------------|-------|
| 1 (Prompt Agent) | Supported | VNet + private endpoints |
| 2 (Hybrid) | Supported | Same as Pattern 1 |
| 3 (Workflow Agent) | Supported | Same as Pattern 1 |
| 4 (Hosted Agent) | **Not during preview** | Limitation of hosted agent preview |
| 5 (Client-Side + Responses API) | Supported | PE to Foundry endpoint |
| 6 (Client-Side + Stateless) | Supported | PE to model endpoint |

### Observability

| Pattern | Built-in Observability | Custom Required |
|---------|----------------------|-----------------|
| 1, 2, 3 | Full (App Insights, tracing, evaluation, red team) | Minimal |
| 4 | OpenTelemetry export to App Insights | Some (your container logs) |
| 5, 6 | None | Full (instrument yourself) |

---

## Related Documents

- [RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md](RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md) — detailed comparison of server-side vs client-side tool calling mechanics, including security, performance, observability, and data residency
- [ARCHITECTURE.md](ARCHITECTURE.md) — this repository's infrastructure architecture
- [TECHNOLOGY.md](TECHNOLOGY.md) — technology choices and rationale

## External References

- [What is Microsoft Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/overview)
- [Agent types comparison](https://learn.microsoft.com/azure/foundry/agents/overview#compare-agent-types)
- [Build with agents, conversations, and responses](https://learn.microsoft.com/azure/foundry/agents/concepts/runtime-components)
- [What are hosted agents](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
- [Agent tools overview](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-catalog)
- [Function calling with Foundry agents](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/function-calling)
- [Use the Azure OpenAI Responses API](https://learn.microsoft.com/azure/foundry/openai/how-to/responses)
- [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/overview/)
- [Semantic Kernel overview](https://learn.microsoft.com/semantic-kernel/overview/)
- [Agent development lifecycle](https://learn.microsoft.com/azure/foundry/agents/concepts/development-lifecycle)
