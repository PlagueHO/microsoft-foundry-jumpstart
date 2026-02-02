"""
Azure Architect Agent - Development Mode with Microsoft Agent Framework.

This sample demonstrates an Azure Solutions Architect agent using Microsoft
Agent Framework with an unpublished (development) agent in Microsoft Foundry
Agent Service. The agent combines:

1. MCP Tools (Microsoft Learn) - For searching Azure documentation
2. Local Python Tools - For cost estimation, architecture validation, and IaC generation
3. Persistent Chat (Cosmos DB) - For conversation history across sessions

The Azure Architect agent helps users:
- Design cloud solutions following the Well-Architected Framework
- Estimate Azure resource costs
- Validate architectures against best practices
- Generate Bicep infrastructure-as-code snippets

KEY CONCEPT: Tool Execution Locations
=====================================
- MCP Tools: Execute on server (HostedMCPTool) or client (MCPStreamableHTTPTool)
- Local Python Tools: Always execute on the client
- Both tool types work together seamlessly in the same agent

Prerequisites:
- Microsoft Foundry project with an agent created
- Azure CLI authenticated (az login)
- Environment variables: PROJECT_ENDPOINT
- Optional: COSMOS_DB_CONNECTION_STRING for persistent thread storage

Usage:
    python unpublished_agent.py                     # Default demo
    python unpublished_agent.py --hosted-mcp        # Server-side MCP + local tools
    python unpublished_agent.py --local-mcp         # Client-side MCP + local tools
    python unpublished_agent.py --cosmos            # With Cosmos DB persistence
    python unpublished_agent.py --interactive       # Interactive chat mode

Reference:
- https://learn.microsoft.com/azure/well-architected/
- https://learn.microsoft.com/agent-framework/
"""
# pylint: disable=duplicate-code,too-many-statements,too-many-locals,too-many-branches
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

import asyncio

from azure.identity.aio import AzureCliCredential

from common import (  # pylint: disable=import-error
    AZURE_ARCHITECT_INSTRUCTIONS,
    AZURE_ARCHITECT_NAME,
    AZURE_ARCHITECT_TOOLS,
    CosmosDBChatMessageStore,
    MCP_SERVER_NAME,
    MCP_SERVER_URL,
    create_argument_parser,
    estimate_azure_costs,
    generate_bicep_snippet,
    get_cosmos_connection_string,
    get_project_endpoint,
    handle_approval_flow_with_thread,
    load_environment,
    print_header,
    validate_architecture,
)


def parse_arguments():
    """Parse command-line arguments with unpublished-specific options."""
    parser = create_argument_parser(
        description="Microsoft Agent Framework - Unpublished Agent Sample",
        example="python unpublished_agent.py --hosted-mcp"
    )
    parser.add_argument(
        "--cosmos",
        action="store_true",
        help="Use Cosmos DB for persistent thread storage"
    )
    return parser.parse_args()


async def run_with_hosted_mcp(use_cosmos: bool = False) -> None:
    """
    Run Azure Architect agent with HOSTED MCP + local Python tools.

    Combines server-side MCP (for Microsoft Learn docs) with local Python
    tools for cost estimation, architecture validation, and Bicep generation.

    Args:
        use_cosmos: If True, use Cosmos DB for thread storage.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import (  # type: ignore[import-untyped]
            AgentThread,
            FunctionTool,
            HostedMCPTool,
        )
        from agent_framework.azure import (  # type: ignore[import-untyped]
            AzureAIProjectAgentProvider,
        )
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install agent-framework --pre")
        return

    args = parse_arguments()
    load_environment()

    project_endpoint = get_project_endpoint()
    if not project_endpoint:
        print("Error: PROJECT_ENDPOINT environment variable is required.")
        return

    print_header(
        "Azure Architect Agent (Hosted MCP + Local Tools)",
        "Server-side MCP for docs, Local Python tools for architecture"
    )
    print(f"Endpoint: {project_endpoint}")
    print()

    # Set up Cosmos DB thread storage if requested
    cosmos_store = None
    if use_cosmos:
        cosmos_conn = get_cosmos_connection_string()
        if not cosmos_conn:
            print("Warning: COSMOS_DB_CONNECTION_STRING not set.")
            print("Using in-memory thread storage instead.\n")
        else:
            cosmos_store = CosmosDBChatMessageStore(
                connection_string=cosmos_conn,
                thread_id="azure_architect_hosted",
                max_messages=100
            )
            print(f"Persistent chat enabled: {cosmos_store}")
            print()

    # Create local Python tools using FunctionTool
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

    async with (
        AzureCliCredential() as credential,
        AzureAIProjectAgentProvider(credential=credential) as provider,
    ):
        # Create agent with both MCP and local tools
        agent = await provider.create_agent(
            name=AZURE_ARCHITECT_NAME,
            instructions=AZURE_ARCHITECT_INSTRUCTIONS,
            tools=[mcp_tool] + local_tools,
        )

        print(f"Created agent: {agent.name}")
        print("Tools: MCP (Microsoft Learn) + 3 local Python tools")

        # Create thread - with Cosmos DB or server-managed
        if cosmos_store:
            thread = AgentThread(message_store=cosmos_store)
            print(f"Using persistent thread: {cosmos_store.thread_id}")
        else:
            thread = agent.get_new_thread()
            print("Using server-managed thread")

        if args.interactive:
            print("\n=== AZURE ARCHITECT - INTERACTIVE MODE ===")
            print("Ask about Azure architecture, costs, or IaC generation.")
            print("Type 'quit' to exit.\n")
            while True:
                try:
                    question = input("You: ").strip()
                    if question.lower() in ["quit", "exit", "q", ""]:
                        break
                    print("\n[Processing with MCP + local tools...]")
                    result = await handle_approval_flow_with_thread(
                        question, agent, thread
                    )
                    print(f"\nArchitect: {result}\n")
                except KeyboardInterrupt:
                    break
        else:
            print(f"\nUser: {args.question}")
            print("\n[Server is making MCP call...]")
            result = await handle_approval_flow_with_thread(
                args.question, agent, thread
            )
            print(f"\nAssistant: {result}")

        # Show Cosmos DB persistence info
        if cosmos_store:
            messages = await cosmos_store.list_messages()
            print(f"\nMessages stored in Cosmos DB: {len(messages)}")
            await cosmos_store.aclose()


async def run_with_local_mcp(use_cosmos: bool = False) -> None:
    """
    Run Azure Architect agent with LOCAL MCP + local Python tools.

    Combines client-side MCP (for Microsoft Learn docs) with local Python
    tools for cost estimation, architecture validation, and Bicep generation.

    Args:
        use_cosmos: If True, use Cosmos DB for thread storage.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import (  # type: ignore[import-untyped]
            AgentThread,
            FunctionTool,
            MCPStreamableHTTPTool,
        )
        from agent_framework.azure import (  # type: ignore[import-untyped]
            AzureAIProjectAgentProvider,
        )
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install agent-framework --pre")
        return

    args = parse_arguments()
    load_environment()

    project_endpoint = get_project_endpoint()
    if not project_endpoint:
        print("Error: PROJECT_ENDPOINT environment variable is required.")
        return

    print_header(
        "Azure Architect Agent (Local MCP + Local Tools)",
        "Client-side MCP for docs, Local Python tools for architecture"
    )
    print(f"Endpoint: {project_endpoint}")
    print()

    # Set up Cosmos DB thread storage if requested
    cosmos_store = None
    if use_cosmos:
        cosmos_conn = get_cosmos_connection_string()
        if cosmos_conn:
            cosmos_store = CosmosDBChatMessageStore(
                connection_string=cosmos_conn,
                thread_id="azure_architect_local",
                max_messages=100
            )
            print(f"Persistent chat enabled: {cosmos_store}")
            print()

    # Create local Python tools using FunctionTool
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
        AzureAIProjectAgentProvider(credential=credential) as provider,
    ):
        # Create agent with both MCP and local tools
        agent = await provider.create_agent(
            name=AZURE_ARCHITECT_NAME,
            instructions=AZURE_ARCHITECT_INSTRUCTIONS,
            tools=[mcp_tool] + local_tools,
        )

        print(f"Created agent: {agent.name}")
        print("Tools: MCP (Microsoft Learn) + 3 local Python tools")

        async with agent:
            # Create thread - with Cosmos DB or default
            if cosmos_store:
                thread = AgentThread(message_store=cosmos_store)
                print(f"Using persistent thread: {cosmos_store.thread_id}")
            else:
                thread = agent.get_new_thread()
                print("Using default thread")

            if args.interactive:
                print("\n=== AZURE ARCHITECT - INTERACTIVE MODE ===")
                print("Ask about Azure architecture, costs, or IaC generation.")
                print("Type 'quit' to exit.\n")
                while True:
                    try:
                        question = input("You: ").strip()
                        if question.lower() in ["quit", "exit", "q", ""]:
                            break
                        print("\n[Processing with MCP + local tools...]")
                        result = await agent.run(question, thread=thread)
                        print(f"\nArchitect: {result}\n")
                    except KeyboardInterrupt:
                        break
            else:
                print(f"\nYou: {args.question}")
                print("\n[Processing with MCP + local tools...]")
                result = await agent.run(args.question, thread=thread)
                print(f"\nArchitect: {result}")

            if cosmos_store:
                messages = await cosmos_store.list_messages()
                print(f"\nMessages stored in Cosmos DB: {len(messages)}")
                await cosmos_store.aclose()


async def run_cosmos_demo() -> None:
    """
    Demonstrate Azure Architect with Cosmos DB persistent chat.

    Shows how conversation history persists across agent "restarts",
    enabling multi-session architecture consulting.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import (  # type: ignore[import-untyped]
            AgentThread,
            FunctionTool,
        )
        from agent_framework.azure import (  # type: ignore[import-untyped]
            AzureAIProjectAgentProvider,
        )
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        return

    load_environment()

    cosmos_conn = get_cosmos_connection_string()
    if not cosmos_conn:
        print("Error: COSMOS_DB_CONNECTION_STRING environment variable required.")
        print("Set it to your Cosmos DB connection string for thread persistence.")
        return

    project_endpoint = get_project_endpoint()
    if not project_endpoint:
        print("Error: PROJECT_ENDPOINT environment variable is required.")
        return

    print_header(
        "Azure Architect - Persistent Chat Demo",
        "Conversation history persists across sessions"
    )
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

    # Create Cosmos DB store for persistent thread
    conversation_id = "azure_architect_persistent"

    print("--- Session 1: Starting architecture consultation ---")
    store1 = CosmosDBChatMessageStore(
        connection_string=cosmos_conn,
        thread_id=conversation_id,
        max_messages=50,
    )

    async with (
        AzureCliCredential() as credential,
        AzureAIProjectAgentProvider(credential=credential) as provider,
    ):
        agent = await provider.create_agent(
            name=AZURE_ARCHITECT_NAME,
            instructions=AZURE_ARCHITECT_INSTRUCTIONS,
            tools=local_tools,
        )

        # Session 1: Start architecture consultation
        thread1 = AgentThread(message_store=store1)

        query1 = "I need to design a web application on Azure for an e-commerce site."
        print(f"You: {query1}")
        response1 = await agent.run(query1, thread=thread1)
        print(f"Architect: {response1}")

        query2 = "What would be the estimated monthly cost for App Service and SQL?"
        print(f"\nYou: {query2}")
        response2 = await agent.run(query2, thread=thread1)
        print(f"Architect: {response2}")

        messages = await store1.list_messages()
        print(f"\n[Stored {len(messages)} messages in Cosmos DB]")
        await store1.aclose()

        # Session 2: Resume conversation (simulating app restart)
        print("\n" + "=" * 60)
        print("--- Session 2: Resuming consultation (after 'restart') ---")
        print("=" * 60)
        store2 = CosmosDBChatMessageStore(
            connection_string=cosmos_conn,
            thread_id=conversation_id,  # Same thread ID
        )

        thread2 = AgentThread(message_store=store2)

        query3 = "Can you validate the architecture we discussed? Include Key Vault and VNet."
        print(f"You: {query3}")
        response3 = await agent.run(query3, thread=thread2)
        print(f"Architect: {response3}")

        messages_after = await store2.list_messages()
        print(f"\n[Total messages after resuming: {len(messages_after)}]")

        # Cleanup (optional - remove for true persistence demo)
        print("\nCleaning up demo data...")
        await store2.clear()
        await store2.aclose()
        print("Done!")


async def main() -> None:
    """Main entry point for Azure Architect agent."""
    args = parse_arguments()
    load_environment()

    print_header(
        "Azure Architect Agent",
        "MCP + Local Tools with Persistent Chat"
    )
    print()

    if args.cosmos and not args.hosted_mcp and not args.local_mcp:
        # Run Cosmos DB persistence demo
        await run_cosmos_demo()
    elif args.hosted_mcp:
        await run_with_hosted_mcp(use_cosmos=args.cosmos)
    elif args.local_mcp:
        await run_with_local_mcp(use_cosmos=args.cosmos)
    else:
        # Default: show usage info
        print("This Azure Architect agent demonstrates:\n")
        print("TOOLS:")
        print("  - Microsoft Learn MCP: Search Azure documentation")
        print("  - estimate_azure_costs: Calculate resource costs")
        print("  - validate_architecture: Check Well-Architected compliance")
        print("  - generate_bicep_snippet: Create Infrastructure as Code\n")
        print("MODES:")
        print("  --hosted-mcp: Server-side MCP + local Python tools")
        print("  --local-mcp:  Client-side MCP + local Python tools")
        print("  --cosmos:     Enable persistent chat with Cosmos DB")
        print("  --interactive: Multi-turn conversation mode\n")
        print("EXAMPLES:")
        print("  python unpublished_agent.py --hosted-mcp --interactive")
        print("  python unpublished_agent.py --local-mcp --cosmos")
        print("  python unpublished_agent.py --cosmos  # Persistence demo\n")
        print("-" * 60)
        print("\nRunning default demo with hosted MCP:\n")
        await run_with_hosted_mcp()


if __name__ == "__main__":
    asyncio.run(main())
