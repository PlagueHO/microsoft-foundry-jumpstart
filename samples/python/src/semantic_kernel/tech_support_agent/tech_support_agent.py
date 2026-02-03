
"""
Sample: Multiturn conversation with Azure AI Agents in Azure Agent Service using Semantic Kernel (latest SDK pattern).

Prerequisites:
- pip install -r requirements.txt
- Configure a .env file in this folder with the following content (replace values as needed):

    AZURE_AI_AGENT_PROJECT_CONNECTION_STRING="eastus2.api.azureml.ms;78700012-09f8-4425-b47f-7e98d215cfeb;rg-techsupport;techsupport-project"
    AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME="gpt-4o"
    AZURE_AI_AGENT_ID="your-agent-id" (from Microsoft Foundry or Azure Agent Service)

  - The connection string format is: <endpoint>;<subscription_id>;<resource_group>;<project_name>
  - The model deployment name should match your Azure OpenAI deployment.

This script demonstrates a multiturn conversation loop using the recommended AzureAIAgent approach.
"""


import asyncio
import os

from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment variables
load_dotenv()

def get_env_var(name: str) -> str:
    """
    Get an environment variable value with validation.

    Args:
        name: The name of the environment variable to retrieve.

    Returns:
        The value of the environment variable.

    Raises:
        OSError: If the environment variable is not set.
    """
    value = os.getenv(name)
    if not value:
        raise OSError(f"Please set {name} in your environment.")
    return value


# Use the new recommended environment variable names
PROJECT_CONN_STR = get_env_var("AZURE_AI_AGENT_PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = get_env_var("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")

# Agent ID for using an existing agent
AGENT_ID = get_env_var("AZURE_AI_AGENT_ID")


async def main():
    """
    Main function to run the tech support agent with interactive chat.

    Creates an Azure AI Agent client, retrieves an existing agent, and runs
    an interactive chat loop for tech support conversations.
    """

    ai_agent_settings = AzureAIAgentSettings(
        project_connection_string=PROJECT_CONN_STR,
        model_deployment_name=MODEL_DEPLOYMENT_NAME,
    )

    creds = DefaultAzureCredential()
    async with creds, AzureAIAgent.create_client(
        credential=creds,
        conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
    ) as client:
        # Retrieve an existing agent by ID from the environment variable
        agent_definition = await client.agents.get_agent(AGENT_ID)
        agent = AzureAIAgent(client=client, definition=agent_definition)

        print("Azure AI Agent Tech Support Chat (using existing agent). Type 'exit' to quit.")
        thread = None
        while True:
            user_input = input("You: ")
            if user_input.lower() in ("exit", "quit"):
                break
            # Send user input and get agent response
            async for response in agent.invoke(messages=user_input, thread=thread):
                thread = response.thread
                print(f"Agent: {response.content}")
        # Clean up thread if created
        if thread:
            await thread.delete()

if __name__ == "__main__":
    asyncio.run(main())
