"""
Azure Architect Agent - Production Mode with Microsoft Agent Framework.

This sample demonstrates an Azure Solutions Architect agent using Microsoft
Agent Framework with a published (production) agent in Microsoft Foundry
Agent Service. The agent combines:

1. MCP Tools (Microsoft Learn) - For searching Azure documentation
2. Local Python Tools - For cost estimation, architecture validation, and IaC generation
3. Client-Side Thread Management - Required for published agents

The Azure Architect agent helps users:
- Design cloud solutions following the Well-Architected Framework
- Estimate Azure resource costs
- Validate architectures against best practices
- Generate Bicep infrastructure-as-code snippets

Key differences from unpublished (development) mode:
- Only POST /responses is available
- /conversations, /files, /vector_stores are INACCESSIBLE
- Conversation history must be stored client-side
- Each user's data is isolated
- Authentication requires Azure AI User role on the Application resource

Prerequisites:
- Published agent application in Microsoft Foundry
- Azure CLI authenticated (az login)
- Azure AI User role on the Agent Application resource
- Environment variables: AZURE_AI_APPLICATION_ENDPOINT

Usage:
    python published_agent.py                     # Default demo
    python published_agent.py --hosted-mcp        # Server-side MCP + local tools
    python published_agent.py --local-mcp         # Client-side MCP + local tools
    python published_agent.py --interactive       # Interactive chat mode

Reference:
- https://learn.microsoft.com/azure/well-architected/
- https://learn.microsoft.com/agent-framework/
"""
# pylint: disable=duplicate-code,too-many-statements,too-many-locals
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

import argparse
import asyncio
from typing import Any, List

from azure.identity.aio import AzureCliCredential

from common import (  # pylint: disable=import-error
    AZURE_ARCHITECT_INSTRUCTIONS,
    AZURE_ARCHITECT_NAME,
    AZURE_ARCHITECT_TOOLS,
    ClientSideThread,
    MCP_SERVER_NAME,
    MCP_SERVER_URL,
    create_argument_parser,
    estimate_azure_costs,
    generate_bicep_snippet,
    get_application_endpoint,
    load_environment,
    print_header,
    validate_architecture,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for published agent sample."""
    parser = create_argument_parser(
        description="Azure Architect Agent - Published (Production) Mode",
        example="python published_agent.py --hosted-mcp --interactive"
    )
    return parser.parse_args()


async def run_with_hosted_mcp() -> None:
    """
    Run Azure Architect with HOSTED MCP + local Python tools (published agent).

    Combines server-side MCP (for Microsoft Learn docs) with local Python
    tools for cost estimation, architecture validation, and Bicep generation.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import (  # type: ignore[import-untyped]
            AgentProtocol,
            AgentResponse,
            ChatAgent,
            ChatMessage,
            FunctionTool,
            HostedMCPTool,
        )
        from agent_framework.azure import AzureAIClient  # type: ignore[import-untyped]
        from azure.ai.projects.aio import AIProjectClient
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install agent-framework azure-ai-projects --pre")
        return

    args = parse_arguments()
    load_environment()

    application_endpoint = get_application_endpoint()
    if not application_endpoint:
        print("Error: AZURE_AI_APPLICATION_ENDPOINT environment variable required.")
        print("Set it to your Agent Application endpoint:")
        print("  https://<resource>.services.ai.azure.com/api/projects/"
              "<project>/applications/<app>/protocols")
        return

    print_header(
        "Azure Architect Agent (Published - Hosted MCP)",
        "Production mode with server-side MCP + local tools"
    )
    print(f"Endpoint: {application_endpoint}")
    print()

    # Create local Python tools
    local_tools = [
        FunctionTool(
            name="estimate_azure_costs",
            description=AZURE_ARCHITECT_TOOLS[0]["description"],
            function=estimate_azure_costs,
        ),
        FunctionTool(
            name="validate_architecture",
            description=AZURE_ARCHITECT_TOOLS[1]["description"],
            function=validate_architecture,
        ),
        FunctionTool(
            name="generate_bicep_snippet",
            description=AZURE_ARCHITECT_TOOLS[2]["description"],
            function=generate_bicep_snippet,
        ),
    ]

    # MCP tool for Microsoft Learn documentation
    mcp_tool = HostedMCPTool(
        name=MCP_SERVER_NAME,
        url=MCP_SERVER_URL,
        approval_mode="never_require",
    )

    async def handle_approval_flow(
        query: str,
        agent: "AgentProtocol",
        thread: ClientSideThread
    ) -> "AgentResponse":
        """Handle MCP approval requests."""
        messages: List[Any] = []
        for msg in thread.get_messages():
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        result = await agent.run(messages, store=False)  # type: ignore[arg-type]
        thread.add_message("user", query)

        while len(result.user_input_requests) > 0:
            new_input: List[Any] = list(messages)
            for request in result.user_input_requests:
                func_call = request.function_call
                if func_call is not None:
                    print(f"\n[APPROVAL REQUEST] Tool: {func_call.name}")
                    print(f"  Arguments: {func_call.arguments}")
                else:
                    print("\n[APPROVAL REQUEST] (unknown tool)")
                approval = input("  Approve? (y/n): ")
                new_input.append(
                    ChatMessage(
                        role="assistant",
                        contents=[request]
                    )
                )
                new_input.append(
                    ChatMessage(
                        role="user",
                        contents=[request.to_function_approval_response(
                            approval.lower() == "y"
                        )]
                    )
                )
            result = await agent.run(new_input, store=False)

        thread.add_message("assistant", str(result))
        return result

    async with (
        AzureCliCredential() as credential,
        AIProjectClient(
            endpoint=application_endpoint,
            credential=credential
        ) as project_client,
    ):
        chat_client = AzureAIClient(project_client=project_client)

        async with ChatAgent(
            chat_client=chat_client,
            name=AZURE_ARCHITECT_NAME,
            instructions=AZURE_ARCHITECT_INSTRUCTIONS,
            tools=[mcp_tool] + local_tools,
        ) as agent:
            print(f"Agent: {agent.name}")
            print("Tools: MCP (Microsoft Learn) + 3 local Python tools")
            thread = ClientSideThread()

            if args.interactive:
                print("\n=== INTERACTIVE MODE (Hosted MCP - Published) ===")
                print("Type 'quit' to exit. Type 'clear' to reset history.\n")
                while True:
                    try:
                        question = input("Your question: ").strip()
                        if question.lower() in ["quit", "exit", "q", ""]:
                            break
                        if question.lower() == "clear":
                            thread.clear()
                            print("Conversation cleared.")
                            continue
                        print("\n[Server is making MCP call...]")
                        result = await handle_approval_flow(question, agent, thread)
                        print(f"\nAssistant: {result}\n")
                    except KeyboardInterrupt:
                        break
            else:
                print(f"\nUser: {args.question}")
                print("\n[Server is making MCP call...]")
                result = await handle_approval_flow(args.question, agent, thread)
                print(f"\nAssistant: {result}")

            print(f"\nConversation managed client-side: {len(thread.messages)} msgs")


async def run_with_local_mcp() -> None:
    """
    Run Azure Architect with LOCAL MCP + local Python tools (published agent).

    Combines client-side MCP (for Microsoft Learn docs) with local Python
    tools for cost estimation, architecture validation, and Bicep generation.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import (  # type: ignore[import-untyped]
            ChatAgent,
            FunctionTool,
            MCPStreamableHTTPTool,
        )
        from agent_framework.azure import AzureAIClient  # type: ignore[import-untyped]
        from azure.ai.projects.aio import AIProjectClient
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install agent-framework azure-ai-projects --pre")
        return

    args = parse_arguments()
    load_environment()

    application_endpoint = get_application_endpoint()
    if not application_endpoint:
        print("Error: AZURE_AI_APPLICATION_ENDPOINT environment variable required.")
        return

    print_header(
        "Azure Architect Agent (Published - Local MCP)",
        "Production mode with client-side MCP + local tools"
    )
    print(f"Endpoint: {application_endpoint}")
    print()

    # Create local Python tools
    local_tools = [
        FunctionTool(
            name="estimate_azure_costs",
            description=AZURE_ARCHITECT_TOOLS[0]["description"],
            function=estimate_azure_costs,
        ),
        FunctionTool(
            name="validate_architecture",
            description=AZURE_ARCHITECT_TOOLS[1]["description"],
            function=validate_architecture,
        ),
        FunctionTool(
            name="generate_bicep_snippet",
            description=AZURE_ARCHITECT_TOOLS[2]["description"],
            function=generate_bicep_snippet,
        ),
    ]

    # MCP tool for Microsoft Learn documentation (client-side)
    mcp_tool = MCPStreamableHTTPTool(
        name=MCP_SERVER_NAME,
        url=MCP_SERVER_URL,
    )

    async with (
        AzureCliCredential() as credential,
        AIProjectClient(
            endpoint=application_endpoint,
            credential=credential
        ) as project_client,
    ):
        chat_client = AzureAIClient(project_client=project_client)

        async with ChatAgent(
            chat_client=chat_client,
            name=AZURE_ARCHITECT_NAME,
            instructions=AZURE_ARCHITECT_INSTRUCTIONS,
            tools=[mcp_tool] + local_tools,
        ) as agent:
            print(f"Agent: {agent.name}")
            print("Tools: MCP (Microsoft Learn) + 3 local Python tools")
            thread = ClientSideThread()

            if args.interactive:
                print("\n=== INTERACTIVE MODE (Local MCP - Published) ===")
                print("Type 'quit' to exit. Type 'clear' to reset history.\n")
                while True:
                    try:
                        question = input("Your question: ").strip()
                        if question.lower() in ["quit", "exit", "q", ""]:
                            break
                        if question.lower() == "clear":
                            thread.clear()
                            print("Conversation cleared.")
                            continue
                        messages = thread.get_messages() + [
                            {"role": "user", "content": question}
                        ]
                        print("\n[Client is making MCP call...]")
                        result = await agent.run(messages)  # type: ignore[arg-type]
                        thread.add_message("user", question)
                        thread.add_message("assistant", str(result))
                        print(f"\nAssistant: {result}\n")
                    except KeyboardInterrupt:
                        break
            else:
                print(f"\nUser: {args.question}")
                print("\n[Client is making MCP call...]")
                result = await agent.run(args.question)
                print(f"\nAssistant: {result}")

            print(f"\nConversation managed client-side: {len(thread.messages)} msgs")


async def main() -> None:
    """Main entry point for Azure Architect published agent."""
    args = parse_arguments()
    load_environment()

    print()
    print("=" * 70)
    print("  AZURE ARCHITECT AGENT - Production (Published) Mode")
    print("=" * 70)
    print()
    print("This agent helps you design Azure solutions with:")
    print("  - Microsoft Learn MCP tool for documentation search")
    print("  - Cost estimation for Azure services")
    print("  - Architecture validation against Well-Architected Framework")
    print("  - Bicep infrastructure-as-code generation")
    print()
    print("Published agents require client-side thread management.")
    print("This sample demonstrates production deployment patterns.")
    print()

    if args.hosted_mcp:
        await run_with_hosted_mcp()
    elif args.local_mcp:
        await run_with_local_mcp()
    else:
        print("Available modes:")
        print()
        print("  --hosted-mcp   Server-side MCP + local tools")
        print("                 Foundry Agent Service makes MCP calls")
        print()
        print("  --local-mcp    Client-side MCP + local tools")
        print("                 Agent Framework makes MCP calls directly")
        print()
        print("-" * 60)
        print("\nRunning default demo (Hosted MCP):\n")
        await run_with_hosted_mcp()


if __name__ == "__main__":
    asyncio.run(main())
