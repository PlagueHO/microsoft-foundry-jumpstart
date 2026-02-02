"""
Common utilities for Microsoft Foundry Agent Service samples.

This module contains shared code used by both published and unpublished
agent samples, reducing code duplication and providing consistent behavior.

Key components:
- Azure Architect agent configuration and instructions
- Local Python tools for architecture analysis
- Environment loading and argument parsing
- MCP configuration constants
- ClientSideThread for published agent thread management
- CosmosDBChatMessageStore for persistent thread storage
- Approval flow handling for MCP tools
"""
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

import argparse
import json
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4


# ============================================================================
# MCP Configuration - Same for all samples
# ============================================================================

MCP_SERVER_URL = "https://learn.microsoft.com/api/mcp"
MCP_SERVER_NAME = "Microsoft Learn MCP"


# ============================================================================
# Azure Architect Agent Configuration
# ============================================================================

AZURE_ARCHITECT_INSTRUCTIONS = """You are an Azure Solutions Architect assistant.

Your role is to help users design, plan, and implement Azure cloud solutions following
Microsoft's Well-Architected Framework pillars:
- Reliability: Design for failure, use redundancy, implement disaster recovery
- Security: Zero-trust, defense in depth, identity-based security
- Cost Optimization: Right-sizing, reserved instances, cost monitoring
- Operational Excellence: Infrastructure as code, monitoring, automation
- Performance Efficiency: Scaling, caching, content delivery

You have access to these tools:
1. **Microsoft Learn MCP**: Search official Azure documentation for best practices,
   tutorials, and reference architectures
2. **estimate_azure_costs**: Calculate estimated monthly costs for Azure resources
3. **validate_architecture**: Check architecture designs against Well-Architected principles
4. **generate_bicep_snippet**: Generate Infrastructure as Code snippets for Azure resources

When helping users:
- Always cite official Microsoft documentation using the MCP tool
- Provide cost estimates when discussing resource choices
- Validate architectural decisions against the Well-Architected Framework
- Suggest IaC patterns using Bicep or Azure Verified Modules
- Consider network security, identity, and compliance requirements
"""

AZURE_ARCHITECT_NAME = "azure-architect-assistant"


# ============================================================================
# Local Python Tools for Azure Architect
# ============================================================================

def estimate_azure_costs(
    resource_type: str,
    sku: str = "Standard",
    region: str = "eastus",
    quantity: int = 1
) -> Dict[str, Any]:
    """
    Estimate monthly Azure costs for a resource.

    This is a simplified cost estimation tool. In production, integrate with
    Azure Pricing API or Azure Cost Management API for accurate pricing.

    Args:
        resource_type: Type of Azure resource (e.g., 'vm', 'storage', 'sql').
        sku: SKU/tier of the resource (e.g., 'Standard_D2s_v3', 'Standard_LRS').
        region: Azure region for pricing (e.g., 'eastus', 'westeurope').
        quantity: Number of resources.

    Returns:
        Dictionary with cost estimate details.
    """
    # Simplified pricing data (in production, use Azure Pricing API)
    base_prices = {
        "vm": {"Basic": 15.0, "Standard": 75.0, "Premium": 200.0},
        "storage": {"Standard_LRS": 0.02, "Standard_GRS": 0.04, "Premium_LRS": 0.15},
        "sql": {"Basic": 5.0, "Standard": 25.0, "Premium": 125.0},
        "appservice": {"Free": 0.0, "Basic": 55.0, "Standard": 75.0, "Premium": 150.0},
        "aks": {"Standard": 73.0, "Premium": 146.0},
        "cosmosdb": {"Serverless": 0.25, "Provisioned": 25.0},
        "redis": {"Basic": 16.0, "Standard": 50.0, "Premium": 225.0},
        "keyvault": {"Standard": 3.0, "Premium": 5.0},
    }

    resource_lower = resource_type.lower()
    if resource_lower not in base_prices:
        return {
            "resource_type": resource_type,
            "error": f"Unknown resource type. Supported: {list(base_prices.keys())}",
            "estimated_monthly_cost_usd": None,
        }

    sku_prices = base_prices[resource_lower]
    sku_key = sku.split("_")[0] if "_" in sku else sku

    if sku_key not in sku_prices:
        sku_key = list(sku_prices.keys())[1]  # Default to middle tier

    unit_price = sku_prices.get(sku_key, 50.0)
    total_cost = unit_price * quantity

    return {
        "resource_type": resource_type,
        "sku": sku,
        "region": region,
        "quantity": quantity,
        "unit_price_usd": unit_price,
        "estimated_monthly_cost_usd": total_cost,
        "note": "Estimate only. Use Azure Pricing Calculator for accurate pricing.",
        "pricing_url": "https://azure.microsoft.com/pricing/calculator/",
    }


def validate_architecture(
    components: List[str],
    requirements: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate an architecture design against Azure Well-Architected Framework.

    Args:
        components: List of Azure components in the architecture.
        requirements: Optional list of specific requirements to validate.

    Returns:
        Dictionary with validation results and recommendations.
    """
    findings: List[Dict[str, str]] = []
    score = 100

    components_lower = [c.lower() for c in components]

    # Reliability checks
    if not any(x in components_lower for x in ["availability zone", "zone", "multi-region"]):
        findings.append({
            "pillar": "Reliability",
            "severity": "Warning",
            "finding": "No zone or region redundancy detected",
            "recommendation": "Consider availability zones or multi-region deployment",
        })
        score -= 10

    if not any(x in components_lower for x in ["backup", "recovery", "geo-replication"]):
        findings.append({
            "pillar": "Reliability",
            "severity": "Warning",
            "finding": "No backup or disaster recovery components",
            "recommendation": "Add Azure Backup, Site Recovery, or geo-replication",
        })
        score -= 10

    # Security checks
    if not any(x in components_lower for x in ["key vault", "keyvault", "managed identity"]):
        findings.append({
            "pillar": "Security",
            "severity": "Critical",
            "finding": "No secrets management detected",
            "recommendation": "Use Azure Key Vault for secrets and Managed Identity for auth",
        })
        score -= 15

    if not any(x in components_lower for x in ["nsg", "firewall", "private endpoint", "vnet"]):
        findings.append({
            "pillar": "Security",
            "severity": "Critical",
            "finding": "No network security components",
            "recommendation": "Add NSGs, Azure Firewall, or Private Endpoints",
        })
        score -= 15

    # Operational Excellence checks
    if not any(x in components_lower for x in ["monitor", "log analytics", "app insights"]):
        findings.append({
            "pillar": "Operational Excellence",
            "severity": "Warning",
            "finding": "No monitoring components",
            "recommendation": "Add Azure Monitor, Log Analytics, and Application Insights",
        })
        score -= 10

    # Cost checks
    if requirements and "cost" in str(requirements).lower():
        findings.append({
            "pillar": "Cost Optimization",
            "severity": "Info",
            "finding": "Cost optimization requirement noted",
            "recommendation": "Consider Reserved Instances, Spot VMs, and auto-scaling",
        })

    return {
        "components_analyzed": components,
        "well_architected_score": max(0, score),
        "findings_count": len(findings),
        "findings": findings,
        "reference": "https://learn.microsoft.com/azure/well-architected/",
    }


def generate_bicep_snippet(
    resource_type: str,
    name: str = "myResource",
    location: str = "eastus",
    use_avm: bool = True
) -> Dict[str, Any]:
    """
    Generate a Bicep infrastructure-as-code snippet for an Azure resource.

    Args:
        resource_type: Type of Azure resource to generate.
        name: Name for the resource.
        location: Azure region.
        use_avm: If True, use Azure Verified Modules pattern.

    Returns:
        Dictionary with Bicep code and documentation links.
    """
    snippets = {
        "storage": {
            "avm": f"""module storage 'br/public:avm/res/storage/storage-account:0.14.0' = {{
  name: 'storage-deployment'
  params: {{
    name: '{name}'
    location: '{location}'
    skuName: 'Standard_LRS'
    kind: 'StorageV2'
    allowBlobPublicAccess: false
    networkAcls: {{
      defaultAction: 'Deny'
    }}
  }}
}}""",
            "raw": f"""resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {{
  name: '{name}'
  location: '{location}'
  sku: {{ name: 'Standard_LRS' }}
  kind: 'StorageV2'
  properties: {{
    allowBlobPublicAccess: false
  }}
}}""",
        },
        "keyvault": {
            "avm": f"""module keyVault 'br/public:avm/res/key-vault/vault:0.9.0' = {{
  name: 'keyvault-deployment'
  params: {{
    name: '{name}'
    location: '{location}'
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
  }}
}}""",
            "raw": f"""resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {{
  name: '{name}'
  location: '{location}'
  properties: {{
    sku: {{ family: 'A', name: 'standard' }}
    tenantId: tenant().tenantId
    enableRbacAuthorization: true
  }}
}}""",
        },
        "vm": {
            "avm": f"""module virtualMachine 'br/public:avm/res/compute/virtual-machine:0.5.0' = {{
  name: 'vm-deployment'
  params: {{
    name: '{name}'
    location: '{location}'
    vmSize: 'Standard_D2s_v3'
    osType: 'Linux'
    zone: 1
  }}
}}""",
            "raw": f"""resource vm 'Microsoft.Compute/virtualMachines@2024-03-01' = {{
  name: '{name}'
  location: '{location}'
  properties: {{
    hardwareProfile: {{ vmSize: 'Standard_D2s_v3' }}
    // Additional configuration required
  }}
}}""",
        },
    }

    resource_lower = resource_type.lower()
    if resource_lower not in snippets:
        return {
            "resource_type": resource_type,
            "error": f"Unknown resource. Supported: {list(snippets.keys())}",
            "bicep": None,
        }

    snippet_set = snippets[resource_lower]
    bicep_code = snippet_set["avm"] if use_avm else snippet_set["raw"]

    return {
        "resource_type": resource_type,
        "name": name,
        "location": location,
        "uses_avm": use_avm,
        "bicep": bicep_code,
        "avm_registry": "https://github.com/Azure/bicep-registry-modules",
        "documentation": f"https://learn.microsoft.com/azure/{resource_lower}/",
    }


# Tool definitions for Agent Framework
AZURE_ARCHITECT_TOOLS = [
    {
        "name": "estimate_azure_costs",
        "description": (
            "Estimate monthly Azure costs for a resource. "
            "Provide resource_type (vm, storage, sql, appservice, aks, cosmosdb, redis, keyvault), "
            "sku (tier/size), region, and quantity."
        ),
        "function": estimate_azure_costs,
        "parameters": {
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "Azure resource type",
                },
                "sku": {
                    "type": "string",
                    "description": "SKU or tier",
                    "default": "Standard",
                },
                "region": {
                    "type": "string",
                    "description": "Azure region",
                    "default": "eastus",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of resources",
                    "default": 1,
                },
            },
            "required": ["resource_type"],
        },
    },
    {
        "name": "validate_architecture",
        "description": (
            "Validate an architecture design against Azure Well-Architected Framework. "
            "Provide a list of Azure components in the architecture."
        ),
        "function": validate_architecture,
        "parameters": {
            "type": "object",
            "properties": {
                "components": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of Azure components in the architecture",
                },
                "requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional specific requirements to validate",
                },
            },
            "required": ["components"],
        },
    },
    {
        "name": "generate_bicep_snippet",
        "description": (
            "Generate Bicep infrastructure-as-code for an Azure resource. "
            "Supports: storage, keyvault, vm. Can use Azure Verified Modules pattern."
        ),
        "function": generate_bicep_snippet,
        "parameters": {
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "Type of Azure resource",
                },
                "name": {
                    "type": "string",
                    "description": "Resource name",
                    "default": "myResource",
                },
                "location": {
                    "type": "string",
                    "description": "Azure region",
                    "default": "eastus",
                },
                "use_avm": {
                    "type": "boolean",
                    "description": "Use Azure Verified Modules",
                    "default": True,
                },
            },
            "required": ["resource_type"],
        },
    },
]


# ============================================================================
# Environment and Configuration
# ============================================================================

def load_environment() -> None:
    """Load environment variables from .env file if available."""
    # pylint: disable=import-outside-toplevel
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed, use system env vars


def create_argument_parser(
    description: str,
    example: str = "python sample.py --hosted-mcp"
) -> argparse.ArgumentParser:
    """
    Create a common argument parser for agent samples.

    Args:
        description: Description for the help text.
        example: Example usage for the epilog.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        description=description,
        epilog=f"Example: {example}"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default="Design a secure web application architecture on Azure with high availability",
        help="The question to ask the agent"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode for multiple questions"
    )
    parser.add_argument(
        "--hosted-mcp",
        action="store_true",
        help="Use Hosted MCP (server-side execution)"
    )
    parser.add_argument(
        "--local-mcp",
        action="store_true",
        help="Use Local MCP (client-side execution)"
    )
    return parser


def get_project_endpoint() -> Optional[str]:
    """Get the project endpoint from environment variables."""
    return os.environ.get("PROJECT_ENDPOINT")


def get_application_endpoint() -> Optional[str]:
    """Get the application endpoint from environment variables."""
    return os.environ.get("AZURE_AI_APPLICATION_ENDPOINT")


def get_cosmos_connection_string() -> Optional[str]:
    """Get the Cosmos DB connection string from environment variables."""
    return os.environ.get("COSMOS_DB_CONNECTION_STRING")


def get_redis_url() -> Optional[str]:
    """Get the Redis URL from environment variables."""
    return os.environ.get("REDIS_URL")


def get_model_deployment_name() -> str:
    """Get the model deployment name from environment variables.
    
    Checks AZURE_AI_MODEL_DEPLOYMENT_NAME first (preferred),
    then falls back to MODEL_DEPLOYMENT_NAME for backward compatibility.
    Returns a default if neither is set.
    """
    return (
        os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or
        os.environ.get("MODEL_DEPLOYMENT_NAME") or
        "gpt-5-mini"
    )


# ============================================================================
# Client-Side Thread Management
# ============================================================================

class ClientSideThread:
    """
    Client-side thread implementation for agents.

    Published agent endpoints don't support server-managed threads
    (/conversations API), so conversation state must be managed locally.
    This class provides a simple implementation that can be extended
    with persistence (Redis, Cosmos DB, etc.) for production use.
    """

    def __init__(self, thread_id: Optional[str] = None):
        """Initialize a client-side thread."""
        self.id = thread_id or str(uuid4())
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the thread."""
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages in the thread."""
        return self.messages.copy()

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()

    def to_json(self) -> str:
        """Serialize thread to JSON for persistence."""
        return json.dumps({"id": self.id, "messages": self.messages})

    @classmethod
    def from_json(cls, json_str: str) -> "ClientSideThread":
        """Deserialize thread from JSON."""
        data = json.loads(json_str)
        thread = cls(thread_id=data["id"])
        thread.messages = data["messages"]
        return thread

    def __len__(self) -> int:
        """Return the number of messages."""
        return len(self.messages)


# ============================================================================
# Chat Message Store Providers (re-exported from separate modules)
# ============================================================================

# Re-export the chat message store implementations for convenience
# These are in separate files so they can be used independently
# pylint: disable=wrong-import-position,import-error
from cosmosdb_chat_message_store import CosmosDBChatMessageStore  # noqa: E402
from redis_chat_message_store import RedisChatMessageStore  # noqa: E402

__all__ = [
    # Chat message stores
    "CosmosDBChatMessageStore",
    "RedisChatMessageStore",
    # Configuration
    "MCP_SERVER_URL",
    "MCP_SERVER_NAME",
    "AZURE_ARCHITECT_INSTRUCTIONS",
    "AZURE_ARCHITECT_NAME",
    "AZURE_ARCHITECT_TOOLS",
    # Tools
    "estimate_azure_costs",
    "validate_architecture",
    "generate_bicep_snippet",
    # Utilities
    "load_environment",
    "get_project_endpoint",
    "get_application_endpoint",
    "get_cosmos_connection_string",
    "get_redis_url",
    "get_model_deployment_name",
    "create_argument_parser",
    "ClientSideThread",
    "handle_approval_flow_with_thread",
    "handle_approval_flow_stateless",
    "print_header",
    "print_mcp_mode_info",
]


# ============================================================================
# MCP Approval Flow Handling
# ============================================================================

async def handle_approval_flow_with_thread(
    query: str,
    agent: Any,
    thread: Any,
) -> Any:
    """
    Handle MCP approval requests when using hosted MCP with server-managed threads.

    Args:
        query: The user's question.
        agent: The agent instance (AgentProtocol).
        thread: The server-managed thread (AgentThread).

    Returns:
        The final AgentResponse after all approvals are handled.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import ChatMessage
    except ImportError:
        print("Error: agent_framework not installed")
        return None

    result = await agent.run(query, thread=thread)
    while len(result.user_input_requests) > 0:
        new_input: List[Any] = []
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
                    role="user",
                    contents=[request.to_function_approval_response(
                        approval.lower() == "y"
                    )]
                )
            )
        result = await agent.run(new_input, thread=thread)
    return result


async def handle_approval_flow_stateless(
    query: str,
    agent: Any,
    thread: ClientSideThread,
) -> Any:
    """
    Handle MCP approval requests for stateless/published agents.

    Args:
        query: The user's question.
        agent: The agent instance.
        thread: The client-side thread for state management.

    Returns:
        The final AgentResponse after all approvals are handled.
    """
    # pylint: disable=import-outside-toplevel
    try:
        from agent_framework import ChatMessage
    except ImportError:
        print("Error: agent_framework not installed")
        return None

    # Build input with conversation history
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
                ChatMessage(role="assistant", contents=[request])
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


def print_header(title: str, subtitle: str = "") -> None:
    """Print a formatted header."""
    print("=" * 60)
    print(title)
    if subtitle:
        print(subtitle)
    print("=" * 60)


def print_mcp_mode_info(
    mode: str,
    endpoint: str,
    is_server_side: bool,
    is_published: bool = False
) -> None:
    """Print information about the MCP mode being used."""
    agent_type = "PUBLISHED AGENT" if is_published else ""
    print("=" * 60)
    print(f"{mode} MODE ({agent_type})" if agent_type else f"{mode} MODE")
    print("=" * 60)
    print(f"Endpoint: {endpoint}")
    print(f"MCP Server: {MCP_SERVER_URL}")
    print()
    if is_server_side:
        print("In this mode, the FOUNDRY AGENT SERVICE (server)")
        print("makes the MCP tool calls.")
    else:
        print("In this mode, the AGENT FRAMEWORK (client)")
        print("makes the MCP tool calls directly.")
    print("-" * 60)
