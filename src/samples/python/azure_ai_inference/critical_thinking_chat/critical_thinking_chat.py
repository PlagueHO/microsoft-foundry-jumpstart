"""
Critical Thinking Chat Assistant with Tool Calling and User Permission.

The assistant uses the Azure AI Projects SDK to connect to Microsoft Foundry and
implements function tool calling with the evaluate_syllogism tool for logical analysis.

Features:
- Requests user permission before executing any tool calls
- Displays tool name and parameters to the user before execution
- Provides option for users to decline tool execution
- Handles user permission responses gracefully
- Configurable logging levels for debugging and monitoring
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

from tools.fallacy_detector import detect_fallacies
from tools.syllogism import evaluate_syllogism

# Configure logging for debugging and monitoring (default configuration)
# This will be updated by configure_logging() function based on verbose setting
logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single conversation exchange."""

    user_input: str
    assistant_response: str
    timestamp: str
    thinking_techniques_used: List[str]


def configure_logging(verbose_level: str = 'ERROR') -> None:
    """
    Configure application logging based on verbosity level.

    Args:
        verbose_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Raises:
        ValueError: If invalid logging level provided
    """
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if verbose_level.upper() not in valid_levels:
        raise ValueError(f"Invalid logging level '{verbose_level}'. Valid options: {', '.join(valid_levels)}")

    log_level = getattr(logging, verbose_level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True  # Override any existing configuration
    )

    # Set Azure SDK logging to WARNING to reduce noise unless DEBUG is selected
    if verbose_level.upper() != 'DEBUG':
        logging.getLogger('azure').setLevel(logging.WARNING)
        logging.getLogger('openai').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the critical thinking assistant."""
    parser = argparse.ArgumentParser(
        description="Critical Thinking Chat Assistant - Challenge assumptions, promote critical thinking, and facilitate deeper analysis",
        epilog="Example: python critical_thinking_chat.py --question 'I think social media is bad for society' --interactive",
    )
    parser.add_argument(
        "--question", "-q", type=str, help="Initial question/statement to analyze"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Enable interactive mode for extended conversations",
    )
    parser.add_argument(
        "--endpoint", type=str, help="Override PROJECT_ENDPOINT environment variable"
    )
    parser.add_argument(
        "--model", type=str, help="Override MODEL_DEPLOYMENT_NAME environment variable"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=None,
        help="Set logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: ERROR"
    )
    return parser.parse_args()


def load_environment() -> None:
    """Load environment variables from .env file if available."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.info("python-dotenv not available, using system environment variables")


def initialize_client(endpoint: Optional[str] = None) -> AzureOpenAI:
    """
    Initialize and test the Azure AI Projects client and get Azure OpenAI client.

    Args:
        endpoint: Optional override for PROJECT_ENDPOINT

    Returns:
        Azure OpenAI client from AI Projects SDK

    Raises:
        SystemExit: If connection fails or required environment variables are missing
    """
    load_environment()

    # Get project endpoint from argument or environment
    project_endpoint = endpoint or os.environ.get("PROJECT_ENDPOINT")
    if not project_endpoint:
        logger.error(
            "PROJECT_ENDPOINT environment variable is required or must be provided via --endpoint argument"
        )
        print(
            "Error: PROJECT_ENDPOINT environment variable is required or must be provided via --endpoint argument"
        )
        sys.exit(1)

    # Configure authentication using DefaultAzureCredential
    credential = DefaultAzureCredential()

    try:
        # Create the Azure AI Projects client
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=credential
        )

        # Get Azure OpenAI client for inference operations (handle dynamic attribute for type checkers)
        inference_attr = getattr(project_client, "inference", None)
        if inference_attr is None:
            raise RuntimeError(
                "AIProjectClient does not expose 'inference' operations. Ensure the 'azure-ai-projects' package version supports inference."
            )
        client = inference_attr.get_azure_openai_client(api_version="2024-10-21")

        logger.info("Created Azure OpenAI client via AIProjectClient for endpoint: %s", project_endpoint)
        print(f"Connected to Microsoft Foundry project: {project_endpoint}")

        return client

    except Exception as e:
        logger.error("Failed to initialize client: %s", e)
        print(f"Connection failed: {e}")
        print("Please check your PROJECT_ENDPOINT and authentication.")
        sys.exit(1)


def get_critical_thinking_system_prompt() -> str:
    """
    Get the system prompt that defines the critical thinking assistant behavior.

    Returns:
        str: System prompt for the critical thinking assistant
    """
    return """You are a Critical Thinking Assistant, designed to help users develop deeper analytical skills and examine their assumptions through thoughtful questioning. Your role is to:

**Core Principles:**
1. Challenge assumptions by asking clarifying questions
2. Provide alternative perspectives without taking sides
3. Guide users through evidence-based reasoning
4. Encourage examination of biases and preconceptions
5. Use Socratic questioning to stimulate deeper inquiry

**Tool Usage:**
- When users present logical arguments or reasoning structures, you can use the evaluate_syllogism tool to analyze their logical validity
- Use tool results to enhance your critical thinking guidance and identify logical fallacies
- Integrate tool analysis into your questioning and discussion to promote deeper understanding

**Questioning Techniques:**
- Ask "What evidence supports this view?"
- Explore "What might someone who disagrees say?"
- Inquire "How did you arrive at this conclusion?"
- Challenge with "What assumptions are you making?"
- Probe with "What are the implications of this belief?"
- Investigate "Have you considered alternative explanations?"

**Conversation Approach:**
- Build upon previous exchanges to maintain context
- Use structured frameworks like "5 Whys" when appropriate
- Encourage users to think through problems systematically
- Present counterarguments respectfully and constructively
- Help users identify logical fallacies in their reasoning

**Response Style:**
- Be respectful but intellectually challenging
- Ask follow-up questions that deepen analysis
- Avoid simply providing answers; instead, guide users to discover insights
- Use examples and analogies to illustrate different perspectives
- Maintain a supportive tone while promoting rigorous thinking

Remember: Your goal is not to convince users of any particular viewpoint, but to help them think more critically and thoroughly about complex topics."""




def create_syllogism_tool() -> Dict[str, Any]:
    """
    Create the syllogism evaluation tool definition for the AI model.

    Returns:
        dict: Tool definition for syllogism evaluation in OpenAI format
    """
    return {
        "type": "function",
        "function": {
            "name": "evaluate_syllogism",
            "description": "Evaluates the logical validity of a syllogism consisting of major premise, minor premise, and conclusion. Returns detailed analysis including validity, logical form, and identification of any logical fallacies or errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "major_premise": {
                        "type": "string",
                        "description": "The major premise of the syllogism (universal statement)"
                    },
                    "minor_premise": {
                        "type": "string",
                        "description": "The minor premise of the syllogism (specific statement)"
                    },
                    "conclusion": {
                        "type": "string",
                        "description": "The conclusion of the syllogism (derived statement)"
                    }
                },
                "required": ["major_premise", "minor_premise", "conclusion"]
            }
        }
    }


def create_fallacy_detector_tool() -> Dict[str, Any]:
    """
    Create the fallacy detection tool definition for the AI model.

    Returns:
        dict: Tool definition for fallacy detection in OpenAI format
    """
    return {
        "type": "function",
        "function": {
            "name": "detect_fallacies",
            "description": "Identifies logical fallacies in argumentative text. Returns detailed analysis including detected fallacies, confidence scores, and suggestions for improvement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text containing argument to analyze for logical fallacies"
                    }
                },
                "required": ["text"]
            }
        }
    }


def create_conversation_memory() -> List[Dict[str, Any]]:
    """
    Create initial conversation memory with system prompt.

    Returns:
        List[Dict[str, Any]]: Initial conversation history with system message
    """
    system_prompt = get_critical_thinking_system_prompt()
    return [{"role": "system", "content": system_prompt}]


def _request_tool_permission(
    tool_name: str, tool_purpose: str, tool_parameters: Dict[str, Any]
) -> bool:
    """
    Request user permission before executing a tool call.

    Args:
        tool_name: The name of the tool to be executed
        tool_purpose: A human-readable description of what the tool does
        tool_parameters: The parameters that will be passed to the tool

    Returns:
        bool: True if user grants permission, False if declined
    """
    print("\n🔧 Tool Call Request:")
    print(f"Tool: {tool_name}")
    print(f"Purpose: {tool_purpose}")
    print("Parameters:")

    # Display parameters in a user-friendly format
    for key, value in tool_parameters.items():
        # Convert parameter names to more readable format
        display_key = key.replace('_', ' ').title()
        print(f"  - {display_key}: {value}")

    while True:
        try:
            permission = input("\nExecute this tool? (y/n): ").strip().lower()

            if permission in ['y', 'yes']:
                return True
            elif permission in ['n', 'no']:
                print("Tool execution declined. Continuing without tool analysis.")
                return False
            else:
                print("Please respond with 'y' (yes) or 'n' (no)")

        except KeyboardInterrupt:
            print("\nTool execution cancelled by user.")
            return False


def add_to_conversation(
    conversation: List[Dict[str, Any]], role: str, content: str
) -> None:
    """
    Add a message to the conversation history.

    Args:
        conversation: The conversation history list
        role: The role of the message sender ('user' or 'assistant')
        content: The message content
    """
    if role in ("user", "assistant"):
        conversation.append({"role": role, "content": content})
    else:
        raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'.")

    logger.debug("Added %s message to conversation: %s...", role, content[:50])


def get_ai_response(
    client: AzureOpenAI, conversation: List[Dict[str, Any]], model_name: str
) -> str:
    """
    Get a response from the AI model using the conversation history.
    Handles tool calling for syllogism evaluation with user permission requests.

    This function implements tool permission functionality:
    - Requests user permission before executing any tool calls
    - Displays tool name and parameters to the user
    - Provides option to decline tool execution
    - Handles user permission responses gracefully
    - Continues conversation when tools are declined

    Args:
        client: The OpenAI client instance
        conversation: The conversation history
        model_name: The model deployment name

    Returns:
        str: The AI assistant's response

    Raises:
        RuntimeError: If the API call fails
    """
    try:
        # Create the logical analysis tools
        syllogism_tool = create_syllogism_tool()
        fallacy_detector_tool = create_fallacy_detector_tool()

        # Make the API call with standard parameters and tool support
        response = client.chat.completions.create(
            messages=conversation,  # type: ignore[arg-type]
            model=model_name,
            tools=[syllogism_tool, fallacy_detector_tool],  # type: ignore[list-item]
            max_tokens=800,
            temperature=1.0,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        # Check if the model wants to use tools
        if response.choices[0].finish_reason == "tool_calls":
            logger.info("Model requested tool calls, requesting user permission")

            # Add the assistant's tool call message to conversation
            if response.choices[0].message.tool_calls:
                assistant_message: Dict[str, Any] = {
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name if hasattr(tc, 'function') else "",
                                "arguments": tc.function.arguments if hasattr(tc, 'function') else ""
                            }
                        }
                        for tc in response.choices[0].message.tool_calls
                        if hasattr(tc, 'function')
                    ]
                }
                conversation.append(assistant_message)

                # Process each tool call with user permission
                for tool_call in response.choices[0].message.tool_calls:
                    if not hasattr(tool_call, 'function'):
                        continue
                    if tool_call.function.name == "evaluate_syllogism":
                        logger.info("Processing syllogism evaluation tool call permission")

                        try:
                            # Parse tool arguments for display
                            function_args = json.loads(tool_call.function.arguments)
                            logger.debug("Tool arguments: %s", function_args)

                            # Request user permission
                            permission_granted = _request_tool_permission(
                                tool_call.function.name,
                                "Evaluate logical validity of syllogism",
                                function_args
                            )

                            if permission_granted:
                                logger.info("User granted permission, executing syllogism evaluation tool")

                                # Execute the syllogism evaluation function
                                tool_result = evaluate_syllogism(**function_args)
                                logger.debug("Tool result: %s", tool_result[:200] + "..." if len(tool_result) > 200 else tool_result)

                                # Add tool response to conversation
                                tool_message = {
                                    "role": "tool",
                                    "content": tool_result,
                                    "tool_call_id": tool_call.id
                                }
                                conversation.append(tool_message)
                            else:
                                logger.info("User declined tool execution, continuing without tool analysis")

                                # Add declined tool response to conversation
                                declined_result = json.dumps({
                                    "declined": True,
                                    "message": "User declined tool execution",
                                    "alternative": "Continuing analysis without formal logical validation"
                                })
                                tool_message = {
                                    "role": "tool",
                                    "content": declined_result,
                                    "tool_call_id": tool_call.id
                                }
                                conversation.append(tool_message)

                        except json.JSONDecodeError as e:
                            logger.error("Failed to parse tool arguments: %s", e)
                            error_result = json.dumps({
                                "error": "Invalid tool arguments provided",
                                "details": str(e)
                            })
                            tool_message = {
                                "role": "tool",
                                "content": error_result,
                                "tool_call_id": tool_call.id
                            }
                            conversation.append(tool_message)

                        except Exception as e:
                            logger.error("Tool execution failed: %s", e)
                            error_result = json.dumps({
                                "error": f"Tool execution failed: {str(e)}"
                            })
                            tool_message = {
                                "role": "tool",
                                "content": error_result,
                                "tool_call_id": tool_call.id
                            }
                            conversation.append(tool_message)

                    elif hasattr(tool_call, 'function') and tool_call.function.name == "detect_fallacies":
                        logger.info("Processing fallacy detection tool call permission")

                        try:
                            # Parse tool arguments for display
                            function_args = json.loads(tool_call.function.arguments)
                            logger.debug("Tool arguments: %s", function_args)

                            # Request user permission
                            permission_granted = _request_tool_permission(
                                tool_call.function.name,
                                "Identify logical fallacies in argumentative text",
                                function_args
                            )

                            if permission_granted:
                                logger.info("User granted permission, executing fallacy detection tool")

                                # Execute the fallacy detection function
                                tool_result = detect_fallacies(**function_args)
                                logger.debug("Tool result: %s", tool_result[:200] + "..." if len(tool_result) > 200 else tool_result)

                                # Add tool response to conversation
                                tool_message = {
                                    "role": "tool",
                                    "content": tool_result,
                                    "tool_call_id": tool_call.id
                                }
                                conversation.append(tool_message)
                            else:
                                logger.info("User declined fallacy detection, continuing without fallacy analysis")

                                # Add declined tool response to conversation
                                declined_result = json.dumps({
                                    "declined": True,
                                    "message": "User declined fallacy detection",
                                    "alternative": "Continuing analysis without formal fallacy identification"
                                })
                                tool_message = {
                                    "role": "tool",
                                    "content": declined_result,
                                    "tool_call_id": tool_call.id
                                }
                                conversation.append(tool_message)

                        except json.JSONDecodeError as e:
                            logger.error("Failed to parse fallacy detection arguments: %s", e)
                            error_result = json.dumps({
                                "error": "Invalid tool arguments provided",
                                "details": str(e)
                            })
                            tool_message = {
                                "role": "tool",
                                "content": error_result,
                                "tool_call_id": tool_call.id
                            }
                            conversation.append(tool_message)

                        except Exception as e:
                            logger.error("Fallacy detection tool execution failed: %s", e)
                            error_result = json.dumps({
                                "error": f"Tool execution failed: {str(e)}"
                            })
                            tool_message = {
                                "role": "tool",
                                "content": error_result,
                                "tool_call_id": tool_call.id
                            }
                            conversation.append(tool_message)

            # Get the final response with tool results incorporated
            final_response = client.chat.completions.create(
                messages=conversation,  # type: ignore[arg-type]
                model=model_name,
                tools=[syllogism_tool, fallacy_detector_tool],  # type: ignore[list-item]
                max_tokens=800,
                temperature=1.0,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )

            # Extract and return final response content
            if (
                final_response.choices
                and len(final_response.choices) > 0
                and final_response.choices[0].message.content
            ):
                return final_response.choices[0].message.content
        else:
            # Standard response without tool calls
            if (
                response.choices
                and len(response.choices) > 0
                and response.choices[0].message.content
            ):
                return response.choices[0].message.content

        raise RuntimeError("No response received from the model")

    except Exception as e:
        logger.error("Failed to get AI response: %s", e)
        raise RuntimeError(f"Unable to get response from AI: {e}") from e


def process_single_question(
    client: AzureOpenAI, question: str, model_name: str
) -> None:
    """
    Process a single question in non-interactive mode.

    Args:
        client: The AzureOpenAI instance
        question: The user's question or statement
        model_name: The model deployment name
    """
    print("\n=== CRITICAL THINKING ANALYSIS ===")
    print(f"Your statement: {question}")
    print("=" * 50)

    try:
        # Create conversation memory
        conversation = create_conversation_memory()
        add_to_conversation(conversation, "user", question)

        # Get AI response (with tool permission handling)
        response = get_ai_response(client, conversation, model_name)

        print("\nCritical Thinking Assistant:")
        print(response)
        print("\n" + "=" * 50)

    except Exception as e:
        print(f"Error processing question: {e}")
        logger.error("Error in process_single_question: %s", e)


def interactive_mode(
    client: AzureOpenAI,
    model_name: str,
    initial_question: Optional[str] = None,
) -> None:
    """
    Run the assistant in interactive mode for extended conversations.

    Args:
        client: The AzureOpenAI instance
        model_name: The model deployment name
        initial_question: Optional initial question to start the conversation
    """
    print("\n" + "=" * 60)
    print("           CRITICAL THINKING CHAT ASSISTANT")
    print("=" * 60)
    print("I'm here to help you think more deeply about complex topics.")
    print("I'll challenge your assumptions and guide you through critical analysis.")
    print("\nWhen analyzing logical arguments, I may request permission to use")
    print("analytical tools. You'll be asked to approve each tool before execution.")
    print("\nType 'quit', 'exit', or 'q' to end our conversation.")
    print("Press Ctrl+C at any time to exit cleanly.")
    print("=" * 60)

    # Create conversation memory
    conversation = create_conversation_memory()
    conversation_turns: List[ConversationTurn] = []

    try:
        # Handle initial question if provided
        if initial_question:
            print(f"\nStarting with your statement: {initial_question}")
            add_to_conversation(conversation, "user", initial_question)

            try:
                response = get_ai_response(client, conversation, model_name)
                add_to_conversation(conversation, "assistant", response)

                print("\nCritical Thinking Assistant:")
                print(response)

                # Record the turn
                turn = ConversationTurn(
                    user_input=initial_question,
                    assistant_response=response,
                    timestamp=datetime.now().isoformat(),
                    thinking_techniques_used=[
                        "Socratic questioning",
                        "Assumption challenging",
                    ],
                )
                conversation_turns.append(turn)

            except Exception as e:
                print(f"Error processing initial question: {e}")

        # Main interactive loop
        while True:
            try:
                print("\n" + "-" * 50)
                user_input = input("\nYour response or new statement: ").strip()

                # Check for exit commands
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\nThank you for engaging in critical thinking!")
                    print("Remember to question assumptions and examine evidence.")
                    break

                # Skip empty input
                if not user_input:
                    print("Please provide a statement or question to analyze.")
                    continue

                # Add user input to conversation
                add_to_conversation(conversation, "user", user_input)

                # Get AI response
                response = get_ai_response(client, conversation, model_name)
                add_to_conversation(conversation, "assistant", response)

                print("\nCritical Thinking Assistant:")
                print(response)

                # Record the turn
                turn = ConversationTurn(
                    user_input=user_input,
                    assistant_response=response,
                    timestamp=datetime.now().isoformat(),
                    thinking_techniques_used=[
                        "Evidence-based reasoning",
                        "Alternative perspectives",
                    ],
                )
                conversation_turns.append(turn)

                # Limit conversation length to prevent token overflow
                if (
                    len(conversation) > 20
                ):  # Keep last 18 messages + system prompt + current
                    conversation = [conversation[0]] + conversation[-17:]
                    logger.info(
                        "Trimmed conversation history to prevent token overflow"
                    )

            except KeyboardInterrupt:
                print("\n\nThank you for the thoughtful discussion!")
                break
            except Exception as e:
                print(f"Error processing your input: {e}")
                logger.error("Error in interactive mode: %s", e)
                continue

    except KeyboardInterrupt:
        print("\n\nGoodbye!")

    # Display conversation summary
    if conversation_turns:
        print(f"\nConversation Summary: {len(conversation_turns)} exchanges completed")
        logger.info(
            "Interactive session completed with %d turns", len(conversation_turns)
        )


def main() -> None:
    """
    Main entry point for the Critical Thinking Chat Assistant.
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Configure logging based on verbose flag and environment variable
        # Priority: command-line argument > environment variable > default (ERROR)
        verbose_level = args.verbose
        if verbose_level is None:
            verbose_level = os.environ.get('VERBOSE_LOGGING', 'ERROR').upper()

        try:
            configure_logging(verbose_level)
            logger.info("Logging configured at %s level", verbose_level)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Get model deployment name from environment or command line
        model_deployment_name = args.model or os.environ.get(
            "MODEL_DEPLOYMENT_NAME", "gpt-4o"
        )

        # Initialize the client
        client = initialize_client(endpoint=args.endpoint)

        # Determine execution mode
        if args.interactive:
            # Interactive mode with optional initial question
            interactive_mode(client, model_deployment_name, args.question)
        elif args.question:
            # Single question mode
            process_single_question(client, args.question, model_deployment_name)
        else:
            # No question provided, start interactive mode
            print("No question provided. Starting interactive mode...")
            interactive_mode(client, model_deployment_name)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error in main: %s", e)
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
