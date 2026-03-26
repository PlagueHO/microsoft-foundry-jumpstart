"""
Hybrid Tool Calling Sample — Client-Side Orchestration with MCP + Local Functions.

This sample validates the hybrid tool calling scenario: combining a remote MCP
server (Microsoft Learn) with local function tools in a single agent using
client-side orchestration via AzureOpenAIResponsesClient (OpenAI Responses API).

WHY THIS MATTERS:
When using agent_reference with the Foundry Agent Service, tools cannot be
passed at call time — they must be baked into the agent definition via
create_version. This sample proves that client-side orchestration via the
Responses API allows both remote MCP tools and local function tools to coexist
in a single request, with full flexibility to change tool schemas per-request
without recreating an agent version.

PREREQUISITES:
- Azure OpenAI endpoint with a deployed model (e.g., gpt-4.1-mini)
- az login (for DefaultAzureCredential)
- Environment variable: AZURE_OPENAI_ENDPOINT
- Optional: AZURE_OPENAI_DEPLOYMENT_NAME (defaults to gpt-4.1-mini)

NO other Azure service dependencies are required — the MCP server is the
public Microsoft Learn endpoint.

Usage:
    python hybrid_tool_calling.py
"""
# pylint: disable=duplicate-code
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

import asyncio
import os
from functools import reduce

from azure.identity.aio import DefaultAzureCredential

AGENT_NAME = "HybridToolCallingAgent"

AGENT_INSTRUCTIONS = """You are an Azure reliability assistant that combines \
documentation search with availability calculations.
Use the Microsoft Learn MCP tools to find official Azure documentation.
Use the SLO calculator tool to compute composite availability from individual \
service SLAs.
Always cite sources from Microsoft Learn when providing guidance."""

MCP_SERVER_URL = "https://learn.microsoft.com/api/mcp"


def calculate_composite_slo(availabilities: list[float]) -> str:
    """Calculate composite availability SLO from individual service values.

    Args:
        availabilities: Availability values for each dependent service
            expressed as decimals between 0 and 1.

    Returns:
        A string describing the composite availability.

    Raises:
        ValueError: If the list is empty.
    """
    if not availabilities:
        raise ValueError("At least one availability value is required.")
    composite = reduce(lambda a, b: a * b, availabilities)
    return f"Composite availability: {composite:.4%} ({composite * 100:.4f}%)"


async def main() -> None:
    """Run the hybrid tool calling sample."""
    try:
        from agent_framework import (  # type: ignore[import-untyped]
            AgentThread,
            FunctionTool,
            MCPStreamableHTTPTool,
        )
        from agent_framework.openai import (  # type: ignore[import-untyped]
            AzureOpenAIResponsesClient,
        )
    except ImportError as exc:
        print(f"Error: Required packages not installed. {exc}")
        print("Install with: pip install agent-framework agent-framework-openai --pre")
        return

    # Load environment
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        print("Error: AZURE_OPENAI_ENDPOINT environment variable is required.")
        return

    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini")

    # --- Local function tool: SLO calculator ---
    slo_tool = FunctionTool(
        name="calculate_composite_slo",
        description=(
            "Calculate the composite availability SLO given individual "
            "service availabilities (0-1 range)."
        ),
        function=calculate_composite_slo,
    )

    # --- Remote MCP tool: Microsoft Learn documentation ---
    mcp_tool = MCPStreamableHTTPTool(
        name="Microsoft Learn",
        url=MCP_SERVER_URL,
    )

    print("=== Hybrid Tool Calling Sample ===")
    print(f"Endpoint: {endpoint}")
    print(f"Model: {deployment}")
    print("Tools: MCP (Microsoft Learn) + local SLO calculator")
    print()

    # Create agent using AzureOpenAIResponsesClient — client-side orchestration.
    # Tools are passed per-request, NOT baked into an agent definition.
    async with DefaultAzureCredential() as credential:
        client = AzureOpenAIResponsesClient(
            azure_endpoint=endpoint,
            azure_credential=credential,
            model=deployment,
        )

        agent = client.as_agent(
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            tools=[mcp_tool, slo_tool],
        )

        thread = AgentThread()

        # --- Test 1: Force both tool types in a single conversation ---
        print("--- Test 1: Hybrid tool call (MCP + local function) ---")
        print(
            "Question: What is the SLA for Azure App Service and Azure SQL "
            "Database? Then calculate composite availability for 0.999 and "
            "0.9995.\n"
        )

        result = await agent.run(
            """First, search Microsoft Learn for the SLA guarantees of \
Azure App Service and Azure SQL Database.
Then use the SLO calculator to compute the composite availability assuming \
App Service has 0.999 availability and Azure SQL Database has 0.9995.""",
            thread=thread,
        )
        print(result)

        # --- Test 2: Streaming with hybrid tools ---
        print("\n\n--- Test 2: Streaming with hybrid tools ---")
        print("Question: What Azure patterns improve reliability beyond three nines?\n")

        async for update in agent.run_streaming(
            """Search Microsoft Learn for Azure reliability patterns that \
can help improve availability beyond three nines (99.9%). Include specific \
patterns like deployment stamps, health endpoint monitoring, or queue-based \
load leveling.
Then calculate the composite availability if I add a caching layer at 0.9999 \
to the previous App Service (0.999) and SQL Database (0.9995) design.""",
            thread=thread,
        ):
            print(update, end="", flush=True)

        print("\n\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
