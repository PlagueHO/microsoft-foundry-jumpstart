"""
Published Agent Sample - Production Mode with Microsoft Agent Framework.

This sample demonstrates using Microsoft Agent Framework with a published
(production) agent in Microsoft Foundry Agent Service. In production mode,
the agent runs through an Agent Application with a stable endpoint.

Key differences from unpublished (development) mode:
- Only POST /responses is available
- /conversations, /files, /vector_stores, /containers are INACCESSIBLE
- Conversation history must be stored client-side
- Each user's data is isolated
- Authentication requires Azure AI User role on the Application resource

The Microsoft Agent Framework handles these differences by providing:
- Client-side thread management via AgentThread and ChatMessageStore
- Same tool calling interface that works in both modes
- Consistent API regardless of backend capabilities

Prerequisites:
- Published agent application in Microsoft Foundry
- Azure CLI authenticated (az login)
- Azure AI User role on the Agent Application resource
- Environment variables: AZURE_AI_APPLICATION_ENDPOINT

Usage:
    python published_agent.py
    python published_agent.py --interactive
    python published_agent.py --question "Calculate a loan payment"
"""
# pylint: disable=duplicate-code,too-many-statements

import argparse
import asyncio
import json
import os
import uuid
from typing import Annotated, Any, Dict, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider


def load_environment() -> None:
    """Load environment variables from .env file if available."""
    # pylint: disable=import-outside-toplevel
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Microsoft Agent Framework - Published Agent Sample",
        epilog="Example: python published_agent.py --question 'Tell me a joke'"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default="What are the benefits of using a published agent endpoint?",
        help="The question to ask the agent"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode for multiple questions"
    )
    return parser.parse_args()


# ============================================================================
# Tool Functions - These work identically in both unpublished and published modes
# ============================================================================

def get_current_weather(
    location: Annotated[str, "The city and state, e.g., San Francisco, CA"],
    unit: Annotated[str, "Temperature unit: celsius or fahrenheit"] = "celsius"
) -> str:
    """
    Get the current weather for a location.

    Args:
        location: The location to get weather for.
        unit: The temperature unit.

    Returns:
        A string describing the current weather.
    """
    weather_data: Dict[str, Dict[str, Any]] = {
        "New York, NY": {"temp": 22, "condition": "Partly cloudy"},
        "San Francisco, CA": {"temp": 18, "condition": "Foggy"},
        "Seattle, WA": {"temp": 15, "condition": "Rainy"},
        "Miami, FL": {"temp": 30, "condition": "Sunny"},
    }

    data = weather_data.get(location, {"temp": 20, "condition": "Clear"})

    if unit.lower() == "fahrenheit":
        temp = data["temp"] * 9 / 5 + 32
        return f"Weather in {location}: {data['condition']}, {temp:.1f}°F"
    return f"Weather in {location}: {data['condition']}, {data['temp']}°C"


def calculate_loan_payment(
    principal: Annotated[float, "The loan principal amount in dollars"],
    annual_rate: Annotated[float, "Annual interest rate as a percentage"],
    years: Annotated[int, "Loan term in years"]
) -> str:
    """
    Calculate monthly loan payment.

    Args:
        principal: The loan amount.
        annual_rate: Annual interest rate percentage.
        years: Loan term in years.

    Returns:
        A string describing the monthly payment.
    """
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12

    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = principal * (
            monthly_rate * (1 + monthly_rate) ** num_payments
        ) / ((1 + monthly_rate) ** num_payments - 1)

    return (
        f"Loan: ${principal:,.0f} at {annual_rate}% for {years} years\n"
        f"Monthly Payment: ${monthly_payment:,.2f}"
    )


def search_knowledge_base(
    query: Annotated[str, "The search query for the knowledge base"]
) -> str:
    """
    Search an internal knowledge base.

    Note: In published mode, server-side vector stores are not accessible.
    This demonstrates a client-side alternative using local search or
    external APIs.

    Args:
        query: The search query.

    Returns:
        Search results as a string.
    """
    # Simulated knowledge base - in a real app, call your own search service
    knowledge = {
        "published agents": (
            "Published agents provide a stable production endpoint with "
            "user data isolation, RBAC authentication, and governance "
            "capabilities through Azure Policy."
        ),
        "agent applications": (
            "Agent Applications are Azure resources that project agents "
            "as services with durable interfaces, dedicated identities, "
            "and lifecycle management."
        ),
        "threads": (
            "In published mode, threads are managed client-side using "
            "ChatMessageStore. The server-side /conversations API is not "
            "available through application endpoints."
        ),
    }

    query_lower = query.lower()
    for key, value in knowledge.items():
        if key in query_lower or any(word in query_lower for word in key.split()):
            return f"Knowledge Base Result:\n{value}"

    return "No matching results found in the knowledge base."


# ============================================================================
# Client-Side Thread Management
# ============================================================================

class ClientSideThread:
    """
    Client-side thread implementation for published agents.

    Published agent endpoints don't support server-managed threads
    (/conversations API), so conversation state must be managed locally.
    This class provides a simple implementation that can be extended
    with persistence (Redis, database, etc.) for production use.

    The Microsoft Agent Framework provides AgentThread and ChatMessageStore
    that achieve this automatically, but this implementation shows
    how it works under the hood.
    """

    def __init__(self, thread_id: Optional[str] = None):
        """Initialize a client-side thread."""
        self.id = thread_id or str(uuid.uuid4())
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the thread."""
        self.messages.append({
            "role": role,
            "content": content
        })

    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages in the thread."""
        return self.messages.copy()

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()

    def to_json(self) -> str:
        """Serialize thread to JSON for persistence."""
        return json.dumps({
            "id": self.id,
            "messages": self.messages
        })

    @classmethod
    def from_json(cls, json_str: str) -> "ClientSideThread":
        """Deserialize thread from JSON."""
        data = json.loads(json_str)
        thread = cls(thread_id=data["id"])
        thread.messages = data["messages"]
        return thread


async def run_with_openai_client() -> None:
    """
    Run the sample using OpenAI client with Agent Application endpoint.

    Published agents expose an OpenAI-compatible endpoint, so we can use
    the standard OpenAI client with Azure authentication. This is the
    current recommended approach for published agents.

    Note: The Microsoft Agent Framework's direct support for published
    agent endpoints is still in development. This sample shows the
    OpenAI-compatible approach that works today.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai package not installed.")
        print("Install with: pip install openai")
        return

    args = parse_arguments()
    load_environment()

    application_endpoint = os.environ.get("AZURE_AI_APPLICATION_ENDPOINT")

    if not application_endpoint:
        print("Error: AZURE_AI_APPLICATION_ENDPOINT environment variable is required.")
        print("Set it to your Agent Application endpoint:")
        print("  https://<resource>.services.ai.azure.com/api/projects/"
              "<project>/applications/<app>/protocols")
        return

    print(f"Connecting to Application: {application_endpoint}")
    print("-" * 60)

    # Create credential and token provider
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://ai.azure.com/.default"
    )

    # Create OpenAI client pointing to the application endpoint
    # Published agents use OpenAI-compatible Responses API
    client = OpenAI(
        api_key=token_provider(),  # Use Azure AD token as API key
        base_url=application_endpoint,
        default_query={"api-version": "2025-11-15-preview"}
    )

    # Create client-side thread for conversation management
    # (Server-side threads are NOT available through application endpoints)
    thread = ClientSideThread()

    async def ask_question(question: str) -> str:
        """
        Send a question to the published agent.

        Note: In published mode, we must include conversation history
        in each request since the server doesn't maintain state.
        """
        # Add user message to local thread
        thread.add_message("user", question)

        print(f"\nUser: {question}")
        print("\nAssistant: ", end="", flush=True)

        # Published endpoints only support POST /responses
        # We pass the full conversation history since there's no server state
        response = client.responses.create(
            input=thread.get_messages()  # Send full history
        )

        # Extract the response text
        response_text = response.output_text if hasattr(response, 'output_text') else str(response)

        # Add assistant response to local thread for future context
        thread.add_message("assistant", response_text)

        print(response_text)
        return response_text

    if args.interactive:
        print("\n=== INTERACTIVE MODE ===")
        print("Type 'quit', 'exit', or 'q' to stop.")
        print("Type 'clear' to reset conversation history.\n")

        while True:
            try:
                question = input("Your question: ").strip()
                if question.lower() in ["quit", "exit", "q", ""]:
                    print("Goodbye!")
                    break
                if question.lower() == "clear":
                    thread.clear()
                    print("Conversation history cleared.")
                    continue
                await ask_question(question)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except (OSError, RuntimeError) as e:
                print(f"Error: {e}")
                continue
    else:
        await ask_question(args.question)

        # Demonstrate multi-turn conversation with client-side state
        await ask_question("Can you elaborate on that?")

    print("\n" + "-" * 60)
    print("Conversation history (client-managed):")
    print(f"  Thread ID: {thread.id}")
    print(f"  Messages: {len(thread.get_messages())}")


async def run_with_agent_framework() -> None:
    """
    Run using Microsoft Agent Framework with application endpoint.

    This demonstrates how to use the Agent Framework with a published
    Agent Application using the official pattern from the framework.

    Uses the pattern from the official sample:
    - AIProjectClient with application endpoint
    - AzureAIClient wrapping the project client
    - ChatAgent for conversation management
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import ChatAgent  # type: ignore[import-untyped]
        from agent_framework.azure import AzureAIClient  # type: ignore[import-untyped]
        from azure.ai.projects.aio import AIProjectClient
    except ImportError as e:
        print(f"Note: Some Agent Framework components not available: {e}")
        print("Falling back to OpenAI client approach.")
        await run_with_openai_client()
        return

    args = parse_arguments()
    load_environment()

    application_endpoint = os.environ.get("AZURE_AI_APPLICATION_ENDPOINT")

    if not application_endpoint:
        print("Error: AZURE_AI_APPLICATION_ENDPOINT environment variable is required.")
        print("Set it to your Agent Application endpoint:")
        print("  https://<resource>.services.ai.azure.com/api/projects/"
              "<project>/applications/<app>/protocols")
        return

    print(f"Connecting to Application: {application_endpoint}")
    print("-" * 60)

    # Use async context managers for proper resource management
    # This follows the official sample pattern from agent-framework
    try:
        # pylint: disable=import-outside-toplevel
        from azure.identity.aio import AzureCliCredential

        async with (
            AzureCliCredential() as credential,
            AIProjectClient(
                endpoint=application_endpoint,
                credential=credential
            ) as project_client,
            ChatAgent(
                chat_client=AzureAIClient(project_client=project_client)
            ) as agent,
        ):
            print("\nUsing Agent Framework with application endpoint")
            print("-" * 60)

            if args.interactive:
                print("\n=== INTERACTIVE MODE ===")
                print("Type 'quit', 'exit', or 'q' to stop.\n")

                while True:
                    try:
                        question = input("Your question: ").strip()
                        if question.lower() in ["quit", "exit", "q", ""]:
                            print("Goodbye!")
                            break

                        print(f"\nUser: {question}")
                        response = await agent.run(question)
                        print(f"Assistant: {response}")
                    except KeyboardInterrupt:
                        print("\nGoodbye!")
                        break
                    except (OSError, RuntimeError) as e:
                        print(f"Error: {e}")
                        continue
            else:
                print(f"\nUser: {args.question}")
                response = await agent.run(args.question)
                print(f"Assistant: {response}")

                # Demonstrate follow-up question
                follow_up = "Can you elaborate on that?"
                print(f"\nUser: {follow_up}")
                response = await agent.run(follow_up)
                print(f"Assistant: {response}")

    except (ImportError, OSError, RuntimeError) as e:
        print(f"Error connecting with Agent Framework: {e}")
        print("Falling back to OpenAI client approach.")
        await run_with_openai_client()


async def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("Microsoft Agent Framework - Published Agent Sample")
    print("Production Mode with Client-Side State Management")
    print("=" * 60)
    print()
    print("IMPORTANT NOTES:")
    print("- Published agents use Agent Application stable endpoints")
    print("- Only POST /responses API is available")
    print("- /conversations, /files, /vector_stores are NOT accessible")
    print("- Conversation state is managed client-side")
    print("- Tool calling works the same as development mode")
    print()

    # Try Agent Framework approach first, fall back to OpenAI client
    await run_with_agent_framework()


if __name__ == "__main__":
    asyncio.run(main())
