# Driver Safety Agent - Vehicle Telematics

This sample demonstrates a **vehicle telematics driver safety recommendations agent** using [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/) with a **Responses Agent** backed by an LLM in Microsoft Foundry.

The agent analyzes driving telemetry data (speed, braking, acceleration, cornering, phone usage) and provides actionable safety recommendations, driver safety scores, fleet comparisons, and long-term risk projections.

## Architecture

This sample uses the **Responses Agent** pattern (direct inference):

- `AIProjectClient.AsAIAgent(...)` creates a code-first agent with a model and instructions
- No server-managed agent resource is created in Foundry
- Multi-turn conversation is maintained via `AgentSession`
- Streaming responses are used for real-time output

## Prerequisites

1. A [Microsoft Foundry project](https://learn.microsoft.com/azure/foundry/how-to/create-projects) with a deployed model (for example, `gpt-4o-mini`)
1. [.NET 10 SDK](https://dotnet.microsoft.com/download)
1. Azure CLI authenticated (`az login`)

## Configuration

Set the following environment variables before running:

| Variable | Description | Default |
| --- | --- | --- |
| `AZURE_FOUNDRY_PROJECT_ENDPOINT` | Your Foundry project endpoint URL | *(required)* |
| `AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME` | Model deployment name | `gpt-4o-mini` |

## Running the sample

```bash
# From the samples/dotnet directory
dotnet run --project src/agent-framework/DriverSafetyAgent
```

Or use the VS Code task **dotnet: run: AgentFramework: DriverSafetyAgent**.

## What the sample demonstrates

1. **Trip telemetry analysis** - The agent receives raw telematics data and produces a structured safety assessment with a driver safety score
1. **Fleet comparison** - Multi-turn conversation allows follow-up questions, with the agent retaining context from the previous analysis
1. **Long-term risk projection** - The agent projects safety and cost implications if the driving pattern continues
