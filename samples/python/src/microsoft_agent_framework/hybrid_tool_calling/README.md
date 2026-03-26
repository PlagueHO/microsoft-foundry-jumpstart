# Hybrid Tool Calling — Client-Side Orchestration with MCP + Local Functions

This sample validates the **hybrid tool calling** scenario: combining a remote MCP
server (Microsoft Learn) with local function tools in a single agent, using
**client-side orchestration** via the Azure OpenAI Responses API.

## Why This Sample Exists

When using `agent_reference` with the Foundry Agent Service (server-side orchestration),
tools **cannot** be passed at call time — they must be defined in the agent version via
`create_version`. If your application needs to dynamically change local function tool
schemas without re-creating agent versions, this is a limitation.

This sample proves that **client-side orchestration** via the Responses API works as an
alternative: both remote MCP tools and local function tools coexist in a single request,
with full flexibility to change tool schemas per-request.

See [Responses API: Server-Side vs Client-Side Tool Calling](../../../../../docs/RESPONSES_API_SERVER_VS_CLIENT_TOOL_CALLING.md)
for the full comparison.

## What It Does

1. **Remote MCP tool** — Connects to the public [Microsoft Learn MCP server](https://learn.microsoft.com/api/mcp)
   to search Azure documentation
2. **Local function tool** — A composite SLO calculator that computes availability
   from individual service SLAs
3. **Hybrid query** — Asks the agent to both search docs AND calculate availability
   in a single conversation turn, forcing both tool types to execute

## Prerequisites

- Azure OpenAI endpoint with a deployed model (e.g., `gpt-4.1-mini`)
- `az login` (for `DefaultAzureCredential` / `AzureCliCredential`)
- Environment variable: `AZURE_OPENAI_ENDPOINT`
- Optional: `AZURE_OPENAI_DEPLOYMENT_NAME` (defaults to `gpt-4.1-mini`)

No other Azure service dependencies are required.

## Running

### Python

```bash
cd samples/python/src/microsoft_agent_framework/hybrid_tool_calling
pip install -r requirements.txt
python hybrid_tool_calling.py
```

### .NET

```bash
cd samples/dotnet
dotnet run --project src/agent-framework/AzureArchitect/AzureArchitect_Step08_HybridToolCalling
```

## Key Observations

| Aspect | Server-Side (agent_reference) | Client-Side (this sample) |
|--------|------------------------------|---------------------------|
| Tools passed per-request | No — must use `create_version` | **Yes** — tools in every request |
| Schema changes | Require new agent version | Immediate, no version needed |
| MCP credential isolation | Server-side (secure) | Client-side (you hold credentials) |
| Platform observability | Built-in App Insights | Must implement yourself |
| Network round-trips | 1 (server handles ReAct loop) | 2N+1 (N = tool calls) |
