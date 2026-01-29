"""
Unpublished Agent Sample - Development Mode with Microsoft Agent Framework.

This sample demonstrates using Microsoft Agent Framework with an unpublished
(development) agent in Microsoft Foundry Agent Service. In development mode,
you have full access to the Responses API including:
- Server-managed threads (conversations)
- File uploads and file search
- Vector stores
- Code interpreter
- Function calling (tools)

The project endpoint provides the complete API surface for development,
testing, and debugging your agents before publishing to production.

Prerequisites:
- Microsoft Foundry project with an agent created
- Azure CLI authenticated (az login)
- Environment variables: PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME

Usage:
    python unpublished_agent.py
    python unpublished_agent.py --interactive
    python unpublished_agent.py --question "What is the capital of France?"
"""
# pylint: disable=duplicate-code,too-many-statements
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

import argparse
import asyncio
import os
from typing import Annotated, Any, Dict

from azure.identity import DefaultAzureCredential


def load_environment() -> None:
    """Load environment variables from .env file if available."""
    # pylint: disable=import-outside-toplevel
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed, use system env vars


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Microsoft Agent Framework - Unpublished Agent Sample",
        epilog="Example: python unpublished_agent.py --question 'Tell me a joke'"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default="What are the key differences between development and "
                "production modes in Microsoft Foundry Agent Service?",
        help="The question to ask the agent"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode for multiple questions"
    )
    return parser.parse_args()


# ============================================================================
# Tool Functions - These work the same in both unpublished and published modes
# ============================================================================

def get_current_weather(
    location: Annotated[str, "The city and state, e.g., San Francisco, CA"],
    unit: Annotated[str, "Temperature unit: celsius or fahrenheit"] = "celsius"
) -> str:
    """
    Get the current weather for a location.

    This is a mock implementation demonstrating function calling capability.
    In a real application, this would call a weather API.

    Args:
        location: The location to get weather for.
        unit: The temperature unit.

    Returns:
        A string describing the current weather.
    """
    # Mock weather data - replace with actual API call in production
    weather_data: Dict[str, Dict[str, Any]] = {
        "New York, NY": {"temp": 22, "condition": "Partly cloudy"},
        "San Francisco, CA": {"temp": 18, "condition": "Foggy"},
        "Seattle, WA": {"temp": 15, "condition": "Rainy"},
        "Miami, FL": {"temp": 30, "condition": "Sunny"},
    }

    # Default weather for unknown locations
    data = weather_data.get(location, {"temp": 20, "condition": "Clear"})

    if unit.lower() == "fahrenheit":
        temp = data["temp"] * 9 / 5 + 32
        return f"The weather in {location} is {data['condition']} with a " \
               f"temperature of {temp:.1f}°F."
    return f"The weather in {location} is {data['condition']} with a " \
           f"temperature of {data['temp']}°C."


def calculate_loan_payment(
    principal: Annotated[float, "The loan principal amount in dollars"],
    annual_rate: Annotated[float, "Annual interest rate as a percentage"],
    years: Annotated[int, "Loan term in years"]
) -> str:
    """
    Calculate monthly loan payment using standard amortization formula.

    This demonstrates a more complex tool that the agent can use.

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

    total_payment = monthly_payment * num_payments
    total_interest = total_payment - principal

    return (
        f"For a ${principal:,.2f} loan at {annual_rate}% APR over {years} years:\n"
        f"- Monthly Payment: ${monthly_payment:,.2f}\n"
        f"- Total Interest: ${total_interest:,.2f}\n"
        f"- Total Cost: ${total_payment:,.2f}"
    )


async def run_with_agent_framework() -> None:
    """
    Run the sample using Microsoft Agent Framework with azure-ai-projects V2.

    This demonstrates the recommended approach for unpublished agents using
    the Agent Framework's AzureAIProjectAgentProvider.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework.azure import AzureAIProjectAgentProvider  # type: ignore[import-untyped]
        from azure.ai.projects import AIProjectClient
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install agent-framework azure-ai-projects")
        return

    args = parse_arguments()
    load_environment()

    # Get configuration from environment
    project_endpoint = os.environ.get("PROJECT_ENDPOINT")
    model_deployment = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")

    if not project_endpoint:
        print("Error: PROJECT_ENDPOINT environment variable is required.")
        print("Set it to your Microsoft Foundry project endpoint:")
        print("  https://<resource>.services.ai.azure.com/api/projects/<project>")
        return

    print(f"Connecting to project: {project_endpoint}")
    print(f"Using model: {model_deployment}")
    print("-" * 60)

    # Create Azure AI Project client
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential
    )

    # Create agent provider from the project client
    provider = AzureAIProjectAgentProvider(project_client)

    # Create an agent with tools
    # Note: In development mode (unpublished), we can dynamically create agents
    agent = await provider.create_agent(
        name="development-assistant",
        model=model_deployment,
        instructions="""You are a helpful assistant demonstrating capabilities
        of the Microsoft Agent Framework with Microsoft Foundry Agent Service.

        You have access to tools for:
        1. Getting weather information (get_current_weather)
        2. Calculating loan payments (calculate_loan_payment)
        
        When answering questions:
        - Use the appropriate tools when relevant
        - Be concise but informative
        - Explain what you're doing when using tools
        """,
        tools=[get_current_weather, calculate_loan_payment]
    )

    print(f"Created agent: {agent.name} (ID: {agent.id})")

    # Create a thread for the conversation
    # In development mode, threads are server-managed and persistent
    thread = await agent.get_new_thread()
    print(f"Created thread: {thread.id}")
    print("-" * 60)

    async def ask_question(question: str) -> None:
        """Send a question and display the response."""
        print(f"\nUser: {question}")
        print("\nAssistant: ", end="", flush=True)

        # Run the agent with the question and thread
        response = await agent.run(question, thread=thread)

        # Display the response
        print(response.text)
        print()

    if args.interactive:
        print("\n=== INTERACTIVE MODE ===")
        print("Type 'quit', 'exit', or 'q' to stop.")
        print("Ask questions about weather, loan calculations, or anything else.\n")

        while True:
            try:
                question = input("Your question: ").strip()
                if question.lower() in ["quit", "exit", "q", ""]:
                    print("Goodbye!")
                    break
                await ask_question(question)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except (OSError, RuntimeError) as e:
                print(f"Error: {e}")
                continue
    else:
        # Ask a single question demonstrating the capabilities
        await ask_question(args.question)

        # Ask a follow-up to demonstrate thread/conversation state
        await ask_question(
            "Can you also tell me the weather in Seattle and "
            "calculate a monthly payment for a $300,000 loan at 6.5% "
            "over 30 years?"
        )

    # Clean up resources
    print("-" * 60)
    print("Cleaning up resources...")

    # Delete thread (in development mode, threads persist until deleted)
    await thread.delete()
    print(f"Deleted thread: {thread.id}")

    # Delete the agent (optional - you might want to keep it for reuse)
    await agent.delete()
    print(f"Deleted agent: {agent.id}")


async def run_with_azure_responses_client() -> None:
    """
    Alternative approach using Azure OpenAI Responses Client directly.

    This demonstrates using the lower-level Azure OpenAI Responses Client
    which provides more control but requires more manual management.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import Agent, AgentThread  # type: ignore[import-untyped]
        from agent_framework.azure import AzureOpenAIResponsesClient  # type: ignore[import-untyped]
    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install agent-framework")
        return

    args = parse_arguments()
    load_environment()

    # Get configuration
    project_endpoint = os.environ.get("PROJECT_ENDPOINT")
    model_deployment = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")

    if not project_endpoint:
        print("Error: PROJECT_ENDPOINT environment variable is required.")
        return

    credential = DefaultAzureCredential()

    # Create Azure OpenAI Responses client
    # This is a lower-level client that uses the Responses API directly
    client = AzureOpenAIResponsesClient(
        azure_endpoint=project_endpoint,
        credential=credential,
        deployment_name=model_deployment
    )

    # Create an agent using the chat client
    agent = Agent(
        name="responses-client-assistant",
        model_client=client,
        instructions="You are a helpful assistant with weather and loan tools.",
        tools=[get_current_weather, calculate_loan_payment]
    )

    # Create a local thread (client-managed, not server-managed)
    thread = AgentThread()

    print(f"Using Responses Client with model: {model_deployment}")
    print("-" * 60)

    print(f"\nUser: {args.question}")
    response = await agent.run(args.question, thread=thread)
    print(f"Assistant: {response.text}")


async def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("Microsoft Agent Framework - Unpublished Agent Sample")
    print("Development Mode with Full API Access")
    print("=" * 60)
    print()

    # Run the primary sample with Agent Framework
    await run_with_agent_framework()


if __name__ == "__main__":
    asyncio.run(main())
