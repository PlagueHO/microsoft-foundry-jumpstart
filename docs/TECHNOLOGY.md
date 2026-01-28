# Technology Overview

This solution accelerator leverages a range of Azure services and technologies to deliver a secure, scalable, and well-architected Microsoft Foundry environment.

## Core Azure Services Deployed

- **Microsoft Foundry Service (Formerly known as Azure AI Services)**
  Provides access to Azure AI Services and Foundry based projects.

- **Azure AI Search** *(Optional, but recommended)*
  Enterprise-grade search service for AI-powered indexing and retrieval. Can be used as a capability host for vector stores in AI agents.

- **Azure Cosmos DB** *(Optional - when AI Agents are deployed)*
  NoSQL database for storing agent conversation threads. Configured as a capability host for thread storage in AI agents.

- **Azure Storage Account for Samples** *(Optional - when Samples are deployed)*
  Secure storage for sample datasets. Can be used as a capability host for file storage in AI agents.

- **Azure Virtual Network (VNet) & Subnets** *(Optional - when Network Isolation is enabled)*
  Provides network isolation and secure communication between resources.

- **Private Endpoints & Private DNS Zones** *(Optional - when Network Isolation is enabled)*
  Ensures all services communicate privately within the VNet, supporting zero-trust architecture.

- **Azure Bastion (Optional)** *(Optional - when Network Isolation is enabled)*
  Secure RDP/SSH access to resources without exposing public IPs.

- **Azure Log Analytics Workspace**
  Centralized logging and monitoring for all deployed resources.

- **Azure Application Insights**
  Application performance monitoring and diagnostics.

## Infrastructure as Code

- **Bicep with Azure Verified Modules (AVM)**
  All resources are provisioned using Bicep and AVM for modular, secure, and repeatable deployments.

## Security & Identity

- **Managed Identities**
  Used for secure, passwordless authentication between Azure resources.

- **Role-Based Access Control (RBAC)**
  Fine-grained access management for users and service principals.

## Capability Hosts (AI Agents)

- **Thread Storage (Cosmos DB)**
  Stores agent conversation threads and state for multi-turn interactions.

- **Vector Stores (AI Search)**
  Provides vector search capabilities for agent knowledge bases and retrieval-augmented generation (RAG).

- **File Storage (Storage Account)**
  Stores agent files, attachments, and artifacts.

---

This technology stack ensures the accelerator is secure, operationally excellent, and ready for enterprise AI workloads.
