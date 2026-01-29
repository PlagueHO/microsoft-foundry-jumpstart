// Copyright (c) Microsoft. All rights reserved.

// Microsoft Foundry Jumpstart - Aspire AppHost
// This AppHost orchestrates all sample projects and provides shared infrastructure resources
// including Azure Cosmos DB (using the Linux Preview Emulator for local development).

var builder = DistributedApplication.CreateBuilder(args);

// Azure Cosmos DB with Linux Preview Emulator for local development
// The preview emulator runs as a Linux container and supports hierarchical partition keys
var cosmos = builder.AddAzureCosmosDB("cosmos")
    .RunAsPreviewEmulator(configureEmulator => configureEmulator
        .WithGatewayPort(8081)
        .WithDataExplorer());

// Add the AgentPersistence database with ChatMessages container
var cosmosDb = cosmos.AddCosmosDatabase("AgentPersistence");

// Agent Framework - Azure Architect Samples (do not require Cosmos DB)
builder.AddProject<Projects.AzureArchitect_Step01_Simple>("azurearchitect-step01-simple");

builder.AddProject<Projects.AzureArchitect_Step02a_Foundry_Agent_SingleTurn>("azurearchitect-step02a-singleturn");

builder.AddProject<Projects.AzureArchitect_Step02b_Foundry_Agent_MultiturnConversation>("azurearchitect-step02b-multiturn");

builder.AddProject<Projects.AzureArchitect_Step02c_Foundry_Agent_PrebuiltAgent>("azurearchitect-step02c-prebuilt");

builder.AddProject<Projects.AzureArchitect_Step03_UsingFunctionTools>("azurearchitect-step03-functiontools");

builder.AddProject<Projects.AzureArchitect_Step04_UsingFunctionToolsWithApprovals>("azurearchitect-step04-approvals");

builder.AddProject<Projects.AzureArchitect_Step05_MCPServer>("azurearchitect-step05-mcpserver");

builder.AddProject<Projects.AzureArchitect_Step06_UsingImages>("azurearchitect-step06-images");

builder.AddProject<Projects.AzureArchitect_Step07_WorkflowConcurrent>("azurearchitect-step07-workflows");

// Agent Framework - Agent Persistence Samples
builder.AddProject<Projects.AgentPersistence_Step01_UnpublishedAgent>("agentpersistence-step01-unpublished");

// Agent Persistence with Cosmos DB - requires the emulator
builder.AddProject<Projects.AgentPersistence_Step02_PublishedWithCosmosDB>("agentpersistence-step02-cosmosdb")
    .WithReference(cosmos)
    .WaitFor(cosmos);

// Agent Framework - Document Classifier Workflow
builder.AddProject<Projects.DocumentClassifierWorkflow>("document-classifier-workflow");

// Semantic Kernel Samples
builder.AddProject<Projects.HomeLoanAgent>("home-loan-agent");

builder.Build().Run();
