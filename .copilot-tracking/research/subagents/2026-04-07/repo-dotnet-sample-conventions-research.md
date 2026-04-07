---
title: Repo Dotnet Sample Conventions Research
description: Research notes on repository-specific conventions for adding a new sample under samples/dotnet
ms.date: 2026-04-07
ms.topic: reference
---

## Research Scope

* Repository-specific conventions for adding a new sample under samples/dotnet

## Investigate

1. Existing folder/layout conventions under samples/dotnet/src and samples/dotnet/tests
2. csproj/package/version patterns, target framework choices, nullable/implicit usings, analyzers
3. Established patterns for Azure SDK credential usage and configuration classes
4. README and sample documentation conventions for new samples
5. Build/test tasks a new sample must satisfy

## Findings In Progress

### 1) Folder and layout conventions under samples/dotnet/src and samples/dotnet/tests

* The .NET samples root documents a two-root layout under src and tests, with solution-level inclusion via microsoft-foundry-jumpstart-samples.slnx:
  * samples/dotnet/README.md:9
  * samples/dotnet/README.md:12
  * samples/dotnet/README.md:13
* Existing source grouping under src is by framework/domain (agent-framework, semantic-kernel, orchestrator):
  * samples/dotnet/microsoft-foundry-jumpstart-samples.slnx:8
  * samples/dotnet/microsoft-foundry-jumpstart-samples.slnx:11
  * samples/dotnet/microsoft-foundry-jumpstart-samples.slnx:38
* Tests are grouped under tests/unit with mirrored framework/sample hierarchy and paired project entries in the solution:
  * samples/dotnet/microsoft-foundry-jumpstart-samples.slnx:25
  * samples/dotnet/microsoft-foundry-jumpstart-samples.slnx:36
  * samples/dotnet/microsoft-foundry-jumpstart-samples.slnx:40
* Repository docs also reflect this structure at a high level:
  * docs/FOLDERS.md:34
  * docs/FOLDERS.md:39
  * docs/FOLDERS.md:40

### 2) csproj/package/version patterns, target framework, nullable/implicit usings, analyzers

* SDK and test runner are pinned in samples/dotnet/global.json:
  * samples/dotnet/global.json:3
  * samples/dotnet/global.json:7
  * samples/dotnet/global.json:10
* Current sample and test projects consistently target net10.0 and enable nullable/implicit usings (with LangVersion set in test projects):
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/AzureArchitect_Step01_Simple.csproj:5
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/AzureArchitect_Step01_Simple.csproj:7
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/AzureArchitect_Step01_Simple.csproj:8
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/HomeLoanAgent.Tests.csproj:4
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/HomeLoanAgent.Tests.csproj:5
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/HomeLoanAgent.Tests.csproj:6
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/HomeLoanAgent.Tests.csproj:7
* Package versions are declared directly in individual csproj files (no Directory.Packages.props found under samples/dotnet):
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/AzureArchitect_Step01_Simple.csproj:12
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/AzureArchitect_Step01_Simple.csproj:15
  * samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step02_PublishedWithCosmosDB/AgentPersistence_Step02_PublishedWithCosmosDB.csproj:12
  * samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step02_PublishedWithCosmosDB/AgentPersistence_Step02_PublishedWithCosmosDB.csproj:18
* Test projects use MSTest.Sdk and FluentAssertions with direct ProjectReference to the sample project:
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/HomeLoanAgent.Tests.csproj:1
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/HomeLoanAgent.Tests.csproj:11
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/HomeLoanAgent.Tests.csproj:15
* Analyzer and code-analysis settings are currently scoped in AgentPersistence via Directory.Build.props, not globally across all dotnet samples:
  * samples/dotnet/src/agent-framework/AgentPersistence/Directory.Build.props:4
  * samples/dotnet/src/agent-framework/AgentPersistence/Directory.Build.props:6
  * samples/dotnet/src/agent-framework/AgentPersistence/Directory.Build.props:7
  * samples/dotnet/src/agent-framework/AgentPersistence/Directory.Build.props:8
  * samples/dotnet/src/agent-framework/AgentPersistence/Directory.Build.props:13

### 3) Azure SDK credential usage and configuration class patterns

* Most Agent Framework samples use environment variables for endpoint/deployment and AzureCliCredential for auth:
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/Program.cs:10
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/Program.cs:11
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/Program.cs:25
  * samples/dotnet/src/agent-framework/DocumentClassifierWorkflow/Program.cs:179
  * samples/dotnet/src/agent-framework/DocumentClassifierWorkflow/Program.cs:180
  * samples/dotnet/src/agent-framework/DocumentClassifierWorkflow/Program.cs:190
* AgentPersistence published sample mixes IConfiguration + environment fallback and uses DefaultAzureCredential:
  * samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step02_PublishedWithCosmosDB/Program.cs:85
  * samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step02_PublishedWithCosmosDB/Program.cs:86
  * samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step02_PublishedWithCosmosDB/Program.cs:103
  * samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step02_PublishedWithCosmosDB/Program.cs:104
* Semantic Kernel sample uses host configuration pipeline (appsettings.json + env vars + user secrets) and supports API key or DefaultAzureCredential:
  * samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:90
  * samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:91
  * samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:92
  * samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:108
  * samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:120
  * samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:125
* No dedicated shared *Config/*Options class library pattern was found under samples/dotnet/src; configuration patterns are implemented inline per sample program.

### 4) README and sample documentation conventions

* Cross-sample contribution guidance explicitly requires: place source under src, add README, add tests, update samples/README:
  * samples/README.md:82
  * samples/README.md:83
  * samples/README.md:84
  * samples/README.md:85
  * samples/README.md:86
* .NET samples README emphasizes restore/build/run flow and test execution from samples/dotnet:
  * samples/dotnet/README.md:27
  * samples/dotnet/README.md:35
  * samples/dotnet/README.md:50
* Existing per-sample READMEs commonly include prerequisites, required env vars, and run commands:
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step07_Workflows/README.md:10
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step07_Workflows/README.md:11
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step07_Workflows/README.md:14
  * samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step07_Workflows/README.md:18
  * samples/dotnet/src/semantic-kernel/home-loan-agent/README.md:30
  * samples/dotnet/src/semantic-kernel/home-loan-agent/README.md:32
  * samples/dotnet/src/semantic-kernel/home-loan-agent/README.md:62
  * samples/dotnet/src/semantic-kernel/home-loan-agent/README.md:68
  * samples/dotnet/src/semantic-kernel/home-loan-agent/README.md:74

### 5) Build/test tasks and CI checks a new sample must satisfy

* Local task wiring expects sample projects to be in microsoft-foundry-jumpstart-samples.slnx, because build/test/format tasks run against that solution file:
  * .vscode/tasks.json:130
  * .vscode/tasks.json:133
  * .vscode/tasks.json:148
  * .vscode/tasks.json:151
  * .vscode/tasks.json:211
  * .vscode/tasks.json:214
  * .vscode/tasks.json:225
  * .vscode/tasks.json:228
* Unit test task and CI both filter by TestCategory=Unit and generate coverage artifacts:
  * .vscode/tasks.json:240
  * .vscode/tasks.json:248
  * .vscode/tasks.json:254
  * .github/workflows/lint-and-test-dotnet-apps.yml:46
  * .github/workflows/lint-and-test-dotnet-apps.yml:52
  * .github/workflows/lint-and-test-dotnet-apps.yml:62
* PRs touching samples/dotnet trigger the .NET lint/test workflow with restore, release build, format verify, and unit tests:
  * .github/workflows/lint-and-test-dotnet-apps.yml:9
  * .github/workflows/lint-and-test-dotnet-apps.yml:34
  * .github/workflows/lint-and-test-dotnet-apps.yml:37
  * .github/workflows/lint-and-test-dotnet-apps.yml:40
  * .github/workflows/lint-and-test-dotnet-apps.yml:44
* Test tagging convention is evidenced by [TestCategory("Unit")] in current unit tests:
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/ProgramTests.cs:11
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/ProgramTests.cs:22
  * samples/dotnet/tests/unit/semantic-kernel/home-loan-agent/ProgramTests.cs:33

## Open Follow-on Questions

* Confirm whether CI will be updated to .NET 10 to align with samples/dotnet/global.json currently pinned to SDK 10.0.100:
  * samples/dotnet/global.json:3
  * .github/workflows/lint-and-test-dotnet-apps.yml:28
* Confirm whether project-level package version centralization (Directory.Packages.props) is desired for future consistency, since current pattern is per-csproj versions.

## Clarifying Questions

* Should new samples follow the dominant Agent Framework auth pattern (AzureCliCredential + environment variables) or the HomeLoan style that supports API key plus DefaultAzureCredential fallback?
* Do you want new sample READMEs to include a standard required section set (Prerequisites, Environment Variables, Running, Troubleshooting), or continue with flexible per-sample formatting?
