# Microsoft Foundry Jumpstart Solution Accelerator – Overview

The Microsoft Foundry Jumpstart Solution Accelerator provides a secure, well-architected, and automated way to deploy an Microsoft Foundry environment and its supporting resources. It is designed to help organizations quickly explore and experiment with Microsoft Foundry capabilities while adhering to Microsoft’s Zero Trust security model and Azure Well-Architected Framework best practices.

## Key Features

- **Zero-Trust Security**: Deploys resources into a virtual network with private endpoints, disables public access, and enforces managed identities for secure service-to-service authentication.
- **Azure Verified Modules**: Uses AVM Bicep modules for all supported resources, ensuring reliability and compliance.
- **Flexible Network Isolation**: Supports both network-isolated (private) and public endpoint deployments.
- **Managed Identities**: Eliminates the need for API keys by leveraging Azure-managed identities and optional Entra ID-only authentication.
- **Comprehensive Logging**: Configures diagnostic settings for all resources, sending logs to Log Analytics for monitoring and compliance.
- **Optional Bastion Host**: Enables secure RDP/SSH access via Azure Bastion when required.
- **Extensible Model and Data Deployment**: Optionally deploys sample OpenAI models and uploads sample data to accelerate onboarding.
- **AI Agent Capability Hosts**: Configures Cosmos DB, AI Search, and Storage Account as capability hosts for AI agent thread storage, vector stores, and file storage.
- **Customizable Resource Attachments**: Supports attaching existing Azure Container Registries and configuring Azure AI Search service deployment.
- **Role-Based Access Control**: Grants access to specified users or service principals.

## Configurable Capabilities

Deployment behavior can be tailored using environment variables, including:

- **Sample Data and Model Deployment**: Toggle deployment of sample OpenAI models and sample data containers.
- **Network Isolation**: Enable or disable VNet isolation and configure IP allow lists.
- **API Key Management**: Optionally disable API keys for Azure AI services.
- **Resource Sizing and Selection**: Choose SKUs for Azure AI Search and control deployment of optional infrastructure like Bastion.
- **Access Control**: Specify principal IDs and types for Microsoft Foundry access.
- **Capability Hosts**: Configure Cosmos DB, AI Search, and Storage Account as capability hosts for AI agents.

For a full list of configuration options, see [CONFIGURATION_OPTIONS.md](../CONFIGURATION_OPTIONS.md).

## Sample Data Sets

The accelerator includes sample data sets to facilitate testing, demonstrating and learning of Microsoft Foundry capabilities. All data is synthetic and can be generated using the data_generator tool in the [../tools/python/src/data_generator](../tools/python/src/data_generator) directory.

| Data Set                       | Description                                                                                      | Data Generator Tool                                                                 |
|--------------------------------|--------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| Technical Support Cases        | Synthetic support tickets, resolutions, and customer feedback for various products.              | [tools/tech_support.py](../tools/python/src/data_generator/tools/tech_support.py)                         |
| Retail Products                | Synthetic retail product descriptions and attributes.                                            | [tools/retail_product.py](../tools/python/src/data_generator/tools/retail_product.py)                     |
| Healthcare Patient Records     | Synthetic anonymized patient visit summaries, diagnoses, treatment plans, and other medical notes. | [tools/healthcare_record.py](../tools/python/src/data_generator/tools/healthcare_record.py)       |
| Financial Transactions         | Simulated bank transactions, account statements, and fraud detection cases.                      | [tools/financial_transaction.py](../tools/python/src/data_generator/tools/financial_transaction.py) |
| Insurance Claims               | Example auto, health, or property insurance claim forms and adjuster notes.                      | [tools/insurance_claim.py](../tools/python/src/data_generator/tools/insurance_claim.py)       |
| Legal Contracts                | Sample NDAs, service agreements, and contract negotiation histories.                             | [tools/legal_contract.py](../tools/python/src/data_generator/tools/legal_contract.py) |
| Customer Support Chat Logs     | Multi-turn chat transcripts for various industries (e.g., telecom, utilities).                   | [tools/customer_support_chat_log.py](../tools/python/src/data_generator/tools/customer_support_chat_log.py) |
| IT Service Desk Tickets        | Incident, change, and request tickets with resolution notes.                                     | [tools/it_service_desk_ticket.py](../tools/python/src/data_generator/tools/it_service_desk_ticket.py) |
| HR Employee Records            | Onboarding documents, performance reviews, and leave requests.                                   | [tools/hr_employee_record.py](../tools/python/src/data_generator/tools/hr_employee_record.py) |
| Manufacturing Maintenance Logs | Equipment maintenance records, sensor readings, and failure reports.                             | [tools/manufacturing_maintenance_log.py](../tools/python/src/data_generator/tools/manufacturing_maintenance_log.py) |
| Travel Bookings                | Itineraries, booking confirmations, and customer feedback for flights/hotels.                    | [tools/travel_booking.py](../tools/python/src/data_generator/tools/travel_booking.py) |
| E-commerce Order Histories     | Orders, returns, product reviews, and customer service interactions.                             | [tools/ecommerce_order_history.py](../tools/python/src/data_generator/tools/ecommerce_order_history.py) |

These data sets enable comprehensive evaluation of LLM and agent capabilities across document understanding, summarization, Q&A, classification, and workflow automation tasks.

---
This accelerator is ideal for secure, rapid prototyping and evaluation of Microsoft Foundry in enterprise environments.
