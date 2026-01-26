"""
Home Loan Agent - A conversational AI agent to assist with mortgage loan inquiries.

This module provides a home loan guide agent that can answer questions about mortgage
loans, documentation requirements, and loan processes using Azure AI Project Client
and agent services.
"""

import argparse
import os
from pathlib import Path

from azure.ai.agents.models import (
    CodeInterpreterTool,
    FilePurpose,
    FileSearchTool,
    MessageAttachment,
)
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


# Parse command-line arguments
def parse_arguments():
    """
    Parse command-line arguments for the home loan agent.

    Returns:
        argparse.Namespace: Parsed command-line arguments containing question and interactive mode settings.
    """
    parser = argparse.ArgumentParser(
        description="Home Loan Guide Agent - Ask questions about mortgage loans and documentation",
        epilog="Example: python home_loan_agent.py --question 'What documents do I need for a conventional loan?'"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default="What documents do I need for a Contoso Bank loan?",
        help="The question to ask the agent (default: 'What documents do I need for a Contoso Bank loan?')"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode to ask multiple questions"
    )
    return parser.parse_args()

# Function to initialize and test the project client
def initialize_client():
    """
    Initialize and test the Azure AI Project client.

    Returns:
        AIProjectClient: Initialized Azure AI Project client ready for use.

    Raises:
        SystemExit: If connection fails or required environment variables are missing.
    """
    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not available, use system environment variables

    # Create project client using connection string, copied from your Microsoft Foundry project
    credential = DefaultAzureCredential()

    # Create project client following the official documentation pattern
    project_client = AIProjectClient(
        credential=credential,
        endpoint=os.environ["PROJECT_ENDPOINT"],
    )

    print(f"Created project client for endpoint: {os.environ['PROJECT_ENDPOINT']}")
    print("Testing connection...")

    # Test the connection first
    try:
        # Try to access the agents client to test the connection
        _ = project_client.agents
        print("Connection successful! Agent client created.")
    except Exception as e:
        print(f"Connection test failed: {e}")
        print("Please check your PROJECT_ENDPOINT and authentication.")
        exit(1)

    return project_client

# Function to create and setup the agent with files
def create_agent(project_client):
    """
    Create and setup the home loan agent with required files and tools.

    Args:
        project_client: Azure AI Project client instance.

    Returns:
        The created agent instance with file search and code interpreter tools.
    """
    # Get the model deployment name from environment
    model_deployment_name = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")

    # Get absolute paths for the files
    current_dir = Path(__file__).parent
    checklist_file_path = current_dir / 'Contoso_Loan_Documentation_Checklist.md'
    dataset_file_path = current_dir / 'loan_product_eligibility_dataset.csv'

    print(f"Uploading checklist file from: {checklist_file_path}")
    print(f"File exists: {checklist_file_path.exists()}")

    # Upload the loan checklist file
    checklist_file = project_client.agents.files.upload_and_poll(file_path=str(checklist_file_path), purpose=FilePurpose.AGENTS)
    print(f"Uploaded file, file ID: {checklist_file.id}")

    # Upload a file for use with Code Interpreter
    code_interpreter_file = project_client.agents.files.upload_and_poll(
        file_path=str(dataset_file_path), purpose=FilePurpose.AGENTS
    )
    print(f"Uploaded file, file ID: {code_interpreter_file.id}")

    # create a vector store with the file you uploaded
    vector_store = project_client.agents.vector_stores.create_and_poll(file_ids=[checklist_file.id], name="my_vectorstore")
    print(f"Created vector store, vector store ID: {vector_store.id}")

    # create a file search tool
    file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])
    # create a code interpreter tool
    code_interpreter = CodeInterpreterTool(file_ids=[code_interpreter_file.id])

    # Create an agent following the documentation pattern
    agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="home-loan-guide",
        instructions="""Home Loan Guide is your expert assistant with over 10 years of experience in mortgage lending and loan processing. I am here to simplify the mortgage application process and support borrowers in making informed decisions about their home financing.

My primary responsibilities include:

1. Guiding users through the mortgage application process step-by-step.
2. Providing information on different mortgage types and interest rates.
3. Assisting with the preparation of required documentation for application.
4. Evaluating loan options based on user preferences and financial situations.
5. Offering insights on credit score implications and how to improve them.
6. Answering questions regarding loan approvals and denials.
7. Explaining mortgage terms and payment structures in simple language.
8. Assisting clients in understanding the closing process and associated fees.

I combine financial logic and document awareness to provide smart, supportive advice through every phase of the mortgage journey.

# Form Details
To effectively assist you, please provide answers to the following:

What type of mortgage are you interested in? (e.g., conventional, FHA, VA)

What is the purchase price of the property you are considering?

What is your estimated down payment amount?

Do you have a pre-approval letter or any existing mortgage offers?

What is your current credit score range, if known?

Are there specific concerns or questions you have about the mortgage process or options?

# Manager Feedback
To enhance my capabilities as a Mortgage Loan Assistant, I follow these feedback insights:

Provide real-time updates on application statuses to keep users informed.

Use clear, jargon-free language to simplify complex mortgage concepts.

Be proactive in offering mortgage rate comparisons and product suggestions.

Maintain a supportive and patient demeanor throughout the application process.

Follow up after application submissions to assist with documentation or next steps.""",
        tools=file_search_tool.definitions + code_interpreter.definitions,
        tool_resources=file_search_tool.resources,
    )
    print(f"Created agent, agent ID: {agent.id}")

    # Return agent and resources for cleanup later
    return agent, {
        'checklist_file': checklist_file,
        'code_interpreter_file': code_interpreter_file,
        'vector_store': vector_store
    }

# Function to create a conversation thread
def create_thread(project_client):
    """
    Create a new conversation thread for agent interactions.

    Args:
        project_client: Azure AI Project client instance.

    Returns:
        The created thread instance.
    """
    thread = project_client.agents.threads.create()
    print(f"Created thread, thread ID: {thread.id}")
    return thread

# Function to delete a conversation thread
def delete_thread(project_client, thread):
    """
    Delete a conversation thread and clean up resources.

    Args:
        project_client: Azure AI Project client instance.
        thread: The thread instance to delete.
    """
    if thread:
        try:
            project_client.agents.threads.delete(thread.id)
            print(f"Deleted thread, thread ID: {thread.id}")
        except Exception as e:
            print(f"Warning: Could not delete thread {thread.id}: {e}")

# Function to cleanup agent and resources
def cleanup_agent(project_client, agent, resources):
    """
    Clean up agent and associated resources like vector stores and files.

    Args:
        project_client: Azure AI Project client instance.
        agent: The agent instance to delete.
        resources: Dictionary containing resources to clean up (vector_store, files, etc.).
    """
    print("\nCleaning up resources...")

    # Cleanup resources
    project_client.agents.vector_stores.delete(resources['vector_store'].id)
    print("Deleted vector store")

    project_client.agents.files.delete(resources['checklist_file'].id)
    print("Deleted checklist file")

    project_client.agents.files.delete(resources['code_interpreter_file'].id)
    print("Deleted code interpreter file")

    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

# Function to ask a single question using a provided thread
def ask_question(project_client, agent, question, thread):
    """
    Ask a question to the agent using a specific thread.

    Args:
        project_client: Azure AI Project client instance.
        agent: The agent instance to query.
        question: The question string to ask.
        thread: The thread instance to use for the conversation.
    """
    # Get absolute paths for the files
    current_dir = Path(__file__).parent
    checklist_file_path = current_dir / 'Contoso_Loan_Documentation_Checklist.md'

    print(f"Using thread, thread ID: {thread.id}")

    # Upload the user provided file as a message attachment
    message_file = project_client.agents.files.upload_and_poll(file_path=str(checklist_file_path), purpose=FilePurpose.AGENTS)
    print(f"Uploaded file, file ID: {message_file.id}")

    # Create a message with the file search attachment
    # Notice that vector store is created temporarily when using attachments with a default expiration policy of seven days.
    attachment = MessageAttachment(file_id=message_file.id, tools=FileSearchTool().definitions)

    print(f"\nAsking question: {question}")
    message = project_client.agents.messages.create(
        thread_id=thread.id, role="user", content=question, attachments=[attachment]
    )
    print(f"Created message, message ID: {message.id}")

    run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    print(f"Created run, run ID: {run.id}")
    print(f"Run status: {run.status}")

    # Get the conversation messages after the run is processed
    print("\n=== CONVERSATION MESSAGES ===")
    messages = project_client.agents.messages.list(thread_id=thread.id)

    # Display messages in chronological order (reverse the list since they come newest first)
    message_list = list(messages)
    message_list.reverse()

    for i, message in enumerate(message_list, 1):
        role = message.role.upper()
        content = ""
        # Extract text content from the message
        if hasattr(message, 'content') and message.content:
            for content_part in message.content:
                if hasattr(content_part, 'text'):
                    text_obj = content_part.text
                    if hasattr(text_obj, 'value'):
                        content += text_obj.value
                    else:
                        content += str(text_obj)
                else:
                    content += str(content_part)

        print(f"\n--- Message {i} ({role}) ---")
        print(f"ID: {message.id}")
        print(f"Content: {content}")

        # Show any file attachments
        if hasattr(message, 'attachments') and message.attachments:
            print(f"Attachments: {len(message.attachments)} file(s)")
            for attachment in message.attachments:
                if hasattr(attachment, 'file_id'):
                    print(f"  - File ID: {attachment.file_id}")

    print("\n=== END CONVERSATION ===\n")

    # Clean up only the message file for this question
    project_client.agents.files.delete(message_file.id)
    print("Deleted message file")

# Function to process a single question with complete lifecycle management
def process_question(project_client, question):
    """
    Process a single question with complete agent lifecycle management.

    Args:
        project_client: Azure AI Project client instance.
        question: The question string to process.
    """
    # Create agent and resources
    agent, resources = create_agent(project_client)
    thread = None

    try:
        # Create thread for this question
        thread = create_thread(project_client)

        # Ask the question using the created thread
        ask_question(project_client, agent, question, thread)
    finally:
        # Clean up thread first, then agent and resources
        if thread:
            delete_thread(project_client, thread)
        cleanup_agent(project_client, agent, resources)

# Interactive mode function
def interactive_mode(project_client):
    """
    Run the agent in interactive mode for multiple questions.

    Args:
        project_client: Azure AI Project client instance.
    """
    print("\n=== INTERACTIVE MODE ===")
    print("Type 'quit', 'exit', or 'q' to stop.")
    print("Ask questions about home loans and mortgage documentation.\n")

    # Create the agent once for the entire interactive session
    agent, resources = create_agent(project_client)
    thread = None

    try:
        # Create a persistent thread for the interactive session
        thread = create_thread(project_client)

        while True:
            try:
                question = input("Your question: ").strip()
                if question.lower() in ['quit', 'exit', 'q', '']:
                    print("Goodbye!")
                    break

                # Use the persistent thread for all questions in interactive mode
                ask_question(project_client, agent, question, thread)
                print("\n" + "="*50 + "\n")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error processing question: {e}")
                continue
    finally:
        # Clean up thread first, then agent and resources when exiting interactive mode
        if thread:
            delete_thread(project_client, thread)
        cleanup_agent(project_client, agent, resources)

# Main execution
def main():
    """
    Main entry point for the home loan agent application.

    Parses command-line arguments and runs either interactive mode or processes a single question.
    """
    args = parse_arguments()

    # Initialize the client
    project_client = initialize_client()

    if args.interactive:
        interactive_mode(project_client)
    else:
        process_question(project_client, args.question)

if __name__ == "__main__":
    main()
