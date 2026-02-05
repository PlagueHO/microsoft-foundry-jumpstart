"""
Azure Architect Agent - Published Agent Sample using OpenAI Responses API.

**SDK APPROACH**: This sample uses the OpenAI Python SDK's Responses API to communicate
with published agent applications. This provides a cleaner interface than raw REST calls
while we wait for full Microsoft Agent Framework support for published agents.

**Current Status (GitHub Issues)**:
- Agent Framework: https://github.com/microsoft/agent-framework/issues/2722
- Azure SDK: https://github.com/Azure/azure-sdk-for-net/issues/54426

**Why OpenAI SDK Instead of Agent Framework?**
The Microsoft Agent Framework SDK does not yet support published Agent Applications.
The OpenAI Responses API provides a standardized interface that works with both:
- Standard Azure OpenAI endpoints
- Published Agent Application endpoints

**Published Agent Constraints**:
1. Only POST /responses is available (no /conversations, /files, /vector_stores)
2. Conversation history must be stored client-side
3. Each user's data is automatically isolated
4. Model and tools are pre-configured in the published agent, you don't specify a model

**Future Migration Path**:
When Microsoft Agent Framework adds published agent support, this code can be
migrated to use the framework's abstractions. The structure is designed to make
this transition straightforward:
- `ClientSideThread` -> Framework's `AgentThread` with `ChatMessageStore`
- `OpenAI.responses.create()` -> Framework's agent.run()
- Manual response parsing -> Framework's response handling

Prerequisites:
- Published agent application in Microsoft Foundry
- Azure CLI authenticated (az login)
- Azure AI User role on the Agent Application resource
- Environment variables: AZURE_AI_APPLICATION_ENDPOINT
- Required packages: pip install openai azure-identity

Reference:
- https://learn.microsoft.com/azure/ai-foundry/agents/how-to/publish-agent
- https://learn.microsoft.com/azure/ai-foundry/openai/how-to/responses
- https://learn.microsoft.com/agent-framework/
"""
# pylint: disable=duplicate-code,too-many-statements,too-many-locals
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

import argparse
import asyncio
from typing import Any

from common import (  # pylint: disable=import-error
    AZURE_ARCHITECT_INSTRUCTIONS,
    AZURE_ARCHITECT_NAME,
    AZURE_ARCHITECT_TOOLS,
    MCP_SERVER_NAME,
    MCP_SERVER_URL,
    ClientSideThread,
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


def create_openai_client_for_published_agent(
    application_endpoint: str,
) -> tuple[Any, str, str]:
    """
    Create an HTTP client configured for a published agent application.
    
    Published agents use the OpenAI Responses API format but at a non-standard
    endpoint. The standard OpenAI SDK doesn't properly handle Azure's api-version
    query parameter for these endpoints, so we use httpx directly.
    
    Args:
        application_endpoint: The full application endpoint URL from
            AZURE_AI_APPLICATION_ENDPOINT environment variable.
    
    Returns:
        A tuple of (token_provider callable, responses_endpoint, api_version).
    
    Future Migration:
        When Agent Framework supports published agents, this function will be
        replaced with framework's built-in client initialization.
    """
    # pylint: disable=import-outside-toplevel
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    
    # Extract api-version from query string if present
    api_version = "2025-11-15-preview"  # Default
    if "?" in application_endpoint:
        base_part, query_part = application_endpoint.split("?", 1)
        for param in query_part.split("&"):
            if param.startswith("api-version="):
                api_version = param.split("=", 1)[1]
                break
    else:
        base_part = application_endpoint
    
    # Ensure endpoint ends with /responses
    if not base_part.endswith('/responses'):
        base_part = f"{base_part}/responses"
    
    # Build full endpoint with api-version
    responses_endpoint = f"{base_part}?api-version={api_version}"
    
    # Setup Azure credential and token provider
    # Published agents use ai.azure.com scope
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential,
        "https://ai.azure.com/.default"
    )
    
    return token_provider, responses_endpoint, api_version


def extract_response_text(response_json: dict[str, Any]) -> str:
    """
    Extract the text content from an OpenAI Responses API response.
    
    The Responses API returns a different structure than Chat Completions:
    - output_text: Direct text output (convenience field)
    - output: Array of output items (messages, tool calls, approval requests, etc.)
    
    For published agents with MCP tools requiring approval, the response may
    contain tool approval requests instead of a final answer.
    
    Args:
        response_json: The JSON response dict from the Responses API.
    
    Returns:
        The extracted text content or status message.
    
    Future Migration:
        When Agent Framework supports published agents, response parsing
        will be handled by the framework automatically.
    """
    # Check for output_text convenience field first
    if response_json.get("output_text"):
        return response_json["output_text"]
    
    # Otherwise parse the output array
    output = response_json.get("output", [])
    texts: list[str] = []
    tool_requests: list[str] = []
    
    for output_item in output:
        item_type = output_item.get("type", "")
        
        # Handle message output with text content
        if item_type == "message":
            for content_item in output_item.get("content", []):
                if content_item.get("type") == "output_text":
                    text = content_item.get("text", "")
                    if text:
                        texts.append(text)
        
        # Handle MCP tool approval requests (tools with require_approval: 'always')
        elif item_type == "mcp_approval_request":
            server = output_item.get("server_label", "unknown")
            tool_name = output_item.get("name", "unknown")
            tool_requests.append(f"{server}/{tool_name}")
    
    # If we have text responses, return them
    if texts:
        return "\n\n".join(texts)
    
    # If there are pending tool approval requests, explain what's happening
    if tool_requests:
        return (
            f"[Agent is requesting approval to use tools: {', '.join(tool_requests)}]\n"
            f"Note: This published agent has MCP tools configured with 'require_approval: always'. "
            f"For automated responses, reconfigure the agent with 'require_approval: never' "
            f"or implement a tool approval handler."
        )
    
    # Check status for any errors
    status = response_json.get("status", "unknown")
    if status == "completed":
        return "[Agent completed but produced no text output]"
    elif status == "failed":
        error = response_json.get("error", {})
        return f"[Agent failed: {error.get('message', 'Unknown error')}]"
    
    # Fallback - return string representation
    return str(response_json)


async def run_with_hosted_mcp() -> None:
    """
    Run Azure Architect with HOSTED MCP (published agent using Responses API).

    This function uses the OpenAI Responses API format to communicate with
    the published agent via direct HTTP calls. The agent's MCP tools and local
    tools are pre-configured server-side.
    
    **Why httpx instead of OpenAI SDK?**
    The standard OpenAI Python SDK doesn't properly handle Azure's api-version
    query parameter for published agent endpoints. We use httpx directly with
    the Responses API request/response format.

    **Future Migration Path**:
    When Microsoft Agent Framework adds published agent support:
    1. Replace httpx calls with AzureAIProjectAgentProvider or equivalent
    2. Replace manual response parsing with framework's response handling
    3. Replace ClientSideThread with framework's AgentThread
    """
    # pylint: disable=import-outside-toplevel
    try:
        import httpx
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install httpx azure-identity")
        return

    args = parse_arguments()
    load_environment()

    application_endpoint = get_application_endpoint()
    if not application_endpoint:
        print("Error: AZURE_AI_APPLICATION_ENDPOINT environment variable required.")
        print("Set it to your Agent Application endpoint:")
        print("  https://<resource>.services.ai.azure.com/api/projects/"
              "<project>/applications/<app>/protocols/openai/responses")
        return

    print_header(
        "Azure Architect Agent (Published - Responses API)",
        "Production mode using OpenAI Responses API format"
    )
    print(f"Endpoint: {application_endpoint}")
    print()
    print("📦 HTTP Client: httpx with Responses API format")
    print("   Tools: Pre-configured in published agent (MCP + local)")
    print("   Conversation: Client-side management via ClientSideThread")
    print()
    print("Note: When Agent Framework adds published agent support,")
    print("      this code can be migrated to use framework abstractions.")
    print()

    try:
        token_provider, responses_endpoint, api_version = (
            create_openai_client_for_published_agent(application_endpoint)
        )
    except Exception as ex:
        print(f"Error setting up authentication: {ex}")
        return

    # ClientSideThread manages conversation history
    # Future: Will be replaced by AgentThread with ChatMessageStore
    thread = ClientSideThread()

    async with httpx.AsyncClient(timeout=120.0) as client:
        if args.interactive:
            print("\n=== INTERACTIVE MODE (Published Agent - Responses API) ===")
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
                    
                    # Build input for Responses API
                    # Format: array of message objects with type, role, content
                    inputs: list[dict[str, Any]] = [
                        {"type": "message", "role": msg["role"], "content": msg["content"]}
                        for msg in thread.get_messages()
                    ]
                    inputs.append({"type": "message", "role": "user", "content": question})
                    
                    print("\n[Calling published agent via Responses API...]")
                    
                    # Make Responses API call
                    response = await client.post(
                        responses_endpoint,
                        headers={
                            "Authorization": f"Bearer {token_provider()}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "input": inputs,
                            # Published agents have model pre-configured, but API may require it
                            # Using a placeholder that the service should override
                        },
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        assistant_message = extract_response_text(result)
                        
                        # Update conversation history
                        thread.add_message("user", question)
                        thread.add_message("assistant", assistant_message)
                        
                        print(f"\nAssistant: {assistant_message}\n")
                    else:
                        print(f"\nError: HTTP {response.status_code}")
                        print(f"Response: {response.text}\n")
                    
                except KeyboardInterrupt:
                    break
                except Exception as ex:
                    print(f"\nError: {ex}\n")
        else:
            # Single question mode
            print(f"\nUser: {args.question}")
            print("\n[Calling published agent via Responses API...]")
            
            try:
                # Single message input using Responses API format
                inputs = [{"type": "message", "role": "user", "content": args.question}]
                
                response = await client.post(
                    responses_endpoint,
                    headers={
                        "Authorization": f"Bearer {token_provider()}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "input": inputs,
                    },
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_message = extract_response_text(result)
                    
                    thread.add_message("user", args.question)
                    thread.add_message("assistant", assistant_message)
                    
                    print(f"\nAssistant: {assistant_message}")
                else:
                    print(f"\nError: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                
            except Exception as ex:
                print(f"\nError: {ex}")

    print(f"\nConversation managed client-side: {len(thread.messages)} msgs")


async def run_with_local_mcp() -> None:
    """
    Run Azure Architect with LOCAL MCP (published agent using Responses API).

    This mode demonstrates client-side MCP execution, but with published agents
    the MCP tools are pre-configured server-side. This function provides the
    same interface for consistency, but the actual MCP execution location
    depends on how the agent was configured during publishing.

    **Note**: For true client-side MCP with published agents, you would need
    to implement a full agent runtime loop that:
    1. Calls the Responses API
    2. Parses tool_calls from responses
    3. Executes MCP tools locally
    4. Returns tool results to the API
    
    This is complex and outside the scope of this sample. The current
    implementation uses the same approach as hosted MCP - relying on
    server-side tool execution.

    **Future Migration Path**:
    When Microsoft Agent Framework adds published agent support:
    1. Use framework's MCPStreamableHTTPTool for true client-side MCP
    2. Framework handles the tool execution loop automatically
    """
    # pylint: disable=import-outside-toplevel
    try:
        import httpx
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install httpx azure-identity")
        return

    args = parse_arguments()
    load_environment()

    application_endpoint = get_application_endpoint()
    if not application_endpoint:
        print("Error: AZURE_AI_APPLICATION_ENDPOINT environment variable required.")
        return

    print_header(
        "Azure Architect Agent (Published - Responses API)",
        "Production mode using OpenAI Responses API format (Local MCP mode)"
    )
    print(f"Endpoint: {application_endpoint}")
    print()
    print("📦 HTTP Client: httpx with Responses API format")
    print("   Note: True client-side MCP requires agent runtime implementation")
    print("   This demo uses server-side tool execution")
    print()

    try:
        token_provider, responses_endpoint, api_version = (
            create_openai_client_for_published_agent(application_endpoint)
        )
    except Exception as ex:
        print(f"Error setting up authentication: {ex}")
        return

    thread = ClientSideThread()

    async with httpx.AsyncClient(timeout=120.0) as client:
        if args.interactive:
            print("\n=== INTERACTIVE MODE (Published Agent - Responses API) ===")
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
                    
                    inputs: list[dict[str, Any]] = [
                        {"type": "message", "role": msg["role"], "content": msg["content"]}
                        for msg in thread.get_messages()
                    ]
                    inputs.append({"type": "message", "role": "user", "content": question})
                    
                    print("\n[Calling published agent via Responses API...]")
                    
                    response = await client.post(
                        responses_endpoint,
                        headers={
                            "Authorization": f"Bearer {token_provider()}",
                            "Content-Type": "application/json",
                        },
                        json={"input": inputs},
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        assistant_message = extract_response_text(result)
                        
                        thread.add_message("user", question)
                        thread.add_message("assistant", assistant_message)
                        
                        print(f"\nAssistant: {assistant_message}\n")
                    else:
                        print(f"\nError: HTTP {response.status_code}")
                        print(f"Response: {response.text}\n")
                    
                except KeyboardInterrupt:
                    break
                except Exception as ex:
                    print(f"\nError: {ex}\n")
        else:
            print(f"\nUser: {args.question}")
            print("\n[Calling published agent via Responses API...]")
            
            try:
                inputs = [{"type": "message", "role": "user", "content": args.question}]
                
                response = await client.post(
                    responses_endpoint,
                    headers={
                        "Authorization": f"Bearer {token_provider()}",
                        "Content-Type": "application/json",
                    },
                    json={"input": inputs},
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_message = extract_response_text(result)
                    
                    thread.add_message("user", args.question)
                    thread.add_message("assistant", assistant_message)
                    
                    print(f"\nAssistant: {assistant_message}")
                else:
                    print(f"\nError: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                
            except Exception as ex:
                print(f"\nError: {ex}")

    print(f"\nConversation managed client-side: {len(thread.messages)} msgs")

async def main() -> None:
    """Main entry point for Azure Architect published agent."""
    args = parse_arguments()
    load_environment()

    print()
    print("=" * 70)
    print("  AZURE ARCHITECT AGENT - Production (Published) Mode")
    print("  Using OpenAI Responses API format via httpx")
    print("=" * 70)
    print()
    print("This agent helps you design Azure solutions with:")
    print("  - Microsoft Learn MCP tool for documentation search")
    print("  - Cost estimation for Azure services")
    print("  - Architecture validation against Well-Architected Framework")
    print("  - Bicep infrastructure-as-code generation")
    print()
    print("Published agents require client-side thread management.")
    print("Tools and model are pre-configured in the published agent.")
    print()
    print("HTTP Note: Using httpx with Responses API format until Agent")
    print("           Framework adds native support for published agents.")
    print()

    if args.hosted_mcp:
        await run_with_hosted_mcp()
    elif args.local_mcp:
        await run_with_local_mcp()
    else:
        print("Available modes:")
        print()
        print("  --hosted-mcp   Server-side tool execution")
        print("                 Published agent handles MCP calls")
        print()
        print("  --local-mcp    Same as hosted (see docstring for details)")
        print("                 True client-side MCP requires agent runtime")
        print()
        print("-" * 60)
        print("\nRunning default demo (Hosted MCP):\n")
        await run_with_hosted_mcp()


if __name__ == "__main__":
    asyncio.run(main())
