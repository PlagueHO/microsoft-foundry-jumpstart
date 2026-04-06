# Agent Framework v1.0 Migration Guide

**Status**: ⚠️  Python Ready, .NET requires architecture rewrite

## Overview

The Agent Framework v1.0 release introduces new APIs for Azure AI Foundry agent management. This guide documents breaking changes and migration paths for samples.

## Python Samples - ✅ READY

### Changes Made

- **agent-framework**: 0.1.0a1 → 1.0.0 (GA)
- **agent-framework-redis**: 0.1.0a1 → 1.0.0 (GA)

### API Changes

Python samples already use v1.0-compatible APIs:

- Message API uses `contents=` parameter (not deprecated `text=`)
- All samples in `samples/python/src/` compatible with v1.0.0

### Installation

```bash
pip install agent-framework==1.0.0 agent-framework-redis==1.0.0
```

✅ **Status**: Ready for production use

---

## .NET Samples - ⚠️ REQUIRES REFACTORING

### Package Updates

#### Available (Updated)

- `Azure.AI.Projects`: 2.0.0 GA ✅
- `Azure.Identity`: 1.20.0 ✅
- `Microsoft.Agents.AI.OpenAI`: 1.0.0-rc5 ⚠️ (GA not released)
- `Microsoft.Agents.AI.AzureAI`: 1.0.0-rc5 ⚠️ (GA not released)

#### Still Preview (Not GA)

- `Microsoft.Agents.AI.CosmosNoSql`: 1.0.0-preview.260402.1
- Full GA release of Microsoft.Agents.AI.* packages pending

### Breaking Changes in Azure.AI.Projects 2.0.0 GA

#### 1. **Namespace Organization**

The Azure.AI.Projects 2.0.0 GA uses structured namespaces with client separation:

**Before (Preview)**:

```csharp
using Azure.AI.Projects;
using Azure.AI.Projects.Agents;  // Preview API
```

**After (GA)**:

```csharp
using Azure.AI.Projects.Agents;
```

#### 2. **Agent Administration Client**

Use `AgentAdministrationClient` for creating and managing agent versions:

```csharp
// Access through AIProjectClient
AIProjectClient projectClient = new(endpoint, tokenProvider);
AgentAdministrationClient agentClient = projectClient.AgentAdministrationClient;

// Create agent version
ProjectsAgentVersionCreationOptions options = new(
    new DeclarativeAgentDefinition(model: "gpt-4")
    {
        Instructions = "You are helpful assistant"
    }
);

ProjectsAgentVersion version = agentClient.CreateAgentVersion(
    agentName: "my-agent",
    options: options
);
```

#### 3. **Agent Interaction - Use Persistent Agents Library**

For thread-based conversations (threads, runs, messages), add the separate package:

**Required Package**:

```xml
<PackageReference Include="Azure.AI.Agents.Persistent" Version="1.1.0" />
```

**Agent Interaction Code**:

```csharp
using Azure.AI.Agents.Persistent;

// Get the persistent agents client
PersistentAgentsClient persistentClient = new(
    projectClient.GetPersistentAgentsClient()
);

// Create thread
PersistentAgentThread thread = await persistentClient.Threads.CreateThreadAsync();

// Send message
await persistentClient.Messages.CreateMessageAsync(
    thread.Id,
    MessageRole.User,
    "Hi, what's 2+2?"
);

// Run agent
ThreadRun run = await persistentClient.Runs.CreateRunAsync(
    thread.Id,
    agent.Id
);

// Poll for completion
while (run.Status == RunStatus.InProgress)
{
    await Task.Delay(500);
    run = await persistentClient.Runs.GetRunAsync(thread.Id, run.Id);
}

// Get responses
await foreach (PersistentThreadMessage msg in persistentClient.Messages.GetMessagesAsync(thread.Id))
{
    // Process messages
}
```

#### 4. **Removed/Changed Types**

| Old (Preview) | New (GA) | Status |
|--------------|----------|--------|
| `Azure.AI.Projects.OpenAI` namespace | Consolidated into main namespace | ❌ Removed |
| `AIProjectClient.GetAIAgent()` | Use `AgentAdministrationClient` | ❌ Removed |
| `ChatClient.CreateAIAgent()` | Not an extension in GA | ❌ Removed |
| `AgentThread` | `PersistentAgentThread` (from Persistent lib) | ⚠️ Changed |
| `AgentRunResponseUpdate` | `RunUpdate` (from Persistent lib) | ⚠️ Changed |
| `AgentListOrder` | Use filtering parameters instead | ❌ Removed |

### Samples Requiring Updates

The following samples need code refactoring (not just package updates):

1. **AzureArchitect_Step01_Simple**
   - ❌ Missing: `Azure.AI.Agents.Persistent` package reference
   - ❌ Issue: `ChatClient.CreateAIAgent()` not available
   - ❌ Issue: `AgentThread` type missing

2. **AzureArchitect_Step02a_Foundry_Agent_SingleTurn**
   - ✅ Package versions updated
   - ❌ Issue: Namespace and method calls need updating

3. **AzureArchitect_Step02b_Foundry_Agent_MultiturnConversation**
   - ✅ Package versions updated
   - ❌ Issue: Thread API requires Persistent Agents library

4. **AzureArchitect_Step02c_Foundry_Agent_PrebuiltAgent**
   - ✅ Package versions updated  
   - ❌ Issue: Agent interaction code needs refactoring

5. **AzureArchitect_Step05_MCPServer**
   - ✅ Package versions updated
   - ❌ Issue: Thread operations need Persistent Agents library

6. **AgentPersistence_Step01_UnpublishedAgent**
   - ✅ Package versions updated
   - ❌ Issue: Agent persistence code needs refactoring for new APIs

7. **AgentPersistence_Step02_PublishedWithCosmosDB**
   - ✅ Package versions updated
   - ❌ Issue: Cosmos DB persistence integration needs updates

8. **DocumentClassifierWorkflow**
   - ✅ Package versions updated
   - ❌ Issue: InProcessExecution API changes

### Required .csproj Updates

All affected samples need this package addition:

```xml
<ItemGroup>
  <PackageReference Include="Azure.AI.Agents.Persistent" Version="1.1.0" />
  <!-- Plus existing packages upgraded as noted above -->
</ItemGroup>
```

### Migration Checklist

For each sample, follow these steps:

- [ ] Add `Azure.AI.Agents.Persistent` NuGet package (v1.1.0+)
- [ ] Update`Azure.AI.Projects` to 2.0.0
- [ ] Update `Microsoft.Agents.AI.AzureAI` to 1.0.0-rc5
- [ ] Update `Microsoft.Agents.AI.OpenAI` to 1.0.0
- [ ] Update `Azure.Identity` to 1.20.0
- [ ] Replace `AIProjectClient` with `AgentAdministrationClient` for agent management
- [ ] Replace custom thread code with `PersistentAgentsClient` from Persistent Agents lib
- [ ] Replace `AgentThread` with `PersistentAgentThread`
- [ ] Replace `AgentRunResponseUpdate` with `RunUpdate`
- [ ] Remove any references to `Azure.AI.Projects.OpenAI` namespace
- [ ] Test sample execution end-to-end
- [ ] Update sample README with new code patterns

---

## Temporary Workaround

Until all GA releases are available:

1. **Revert .NET samples to rc5 versions** - use release candidates instead of GA
2. **Keep Python samples on v1.0.0** - fully supported
3. **File issues** with Azure SDK team for:
   - Microsoft.Agents.AI.* full GA releases (currently rc5)
   - Clarification on Azure.AI.Projects 2.0.0 breaking changes

### Updated Package Versions (Current Stable)

```xml
<ItemGroup>
  <PackageReference Include="Azure.AI.Projects" Version="2.0.0" />
  <PackageReference Include="Azure.AI.Agents.Persistent" Version="1.1.0" />
  <PackageReference Include="Azure.Identity" Version="1.20.0" />
  <PackageReference Include="Microsoft.Agents.AI.OpenAI" Version="1.0.0" />
  <PackageReference Include="Microsoft.Agents.AI.AzureAI" Version="1.0.0-rc5" />
  <!-- For CosmosDB persistence -->
  <PackageReference Include="Microsoft.Agents.AI.CosmosNoSql" Version="1.0.0-preview.260402.1" />
</ItemGroup>
```

---

## References

- [Azure AI Projects API Reference (.NET)](https://learn.microsoft.com/dotnet/api/overview/azure/ai.projects-readme?view=azure-dotnet)
- [Azure AI Agents Persistent API Reference (.NET)](https://learn.microsoft.com/dotnet/api/overview/azure.ai.agents.persistent-readme?view=azure-dotnet)
- [Agent Framework Migration Guide](https://learn.microsoft.com/azure/foundry/agents/how-to/migrate)
- [Azure AI Projects - Samples](https://aka.ms/azsdk/Azure.AI.Projects/net/samples)

---

## Next Steps

1. ✅ **Python**: Deploy samples with agent-framework v1.0.0
2. ⏳ **.NET**: Await full GA releases of Microsoft.Agents.AI.* packages (currently rc5)
3. 🔄 **Refactor**: Update all agent interaction code to use new API patterns once GA releases available
4. 📝 **Documentation**: Update architecture guides with new patterns

---

## Build Failure Analysis

### Critical Issue: API Types No Longer Exist in GA

The .NET samples cannot compile due to **missing type definitions** that were present in preview releases but do NOT exist in any final GA release:

#### Missing Types

- **`AgentThread`** - Used in 4 samples for thread management
- **`AgentVersion`** - Used for agent version management  
- **`AgentRunResponseUpdate`** - Used for streaming run updates
- **`ProjectsAgentVersion`** - Not a direct replacement (different API surface)

#### Missing Methods

- **`AIProjectClient.GetAIAgent()`** - Removed in Azure.AI.Projects 2.0.0 GA
- **`ChatClient.CreateAIAgent()`** - Extension method removed
- **`agentClient.Agents`** - Property does not exist in AgentAdministrationClient
- **`InProcessExecution.StreamAsync`** - Method signature changed or removed

#### Root Cause

These samples were written for **internal/preview-only APIs** that:

1. Never made it into final GA releases
2. Were removed or refactored during the RC→GA transition
3. Have no direct GA equivalents

**Evidence**: Checking Azure.AI.Agents.Persistent 1.1.0 and Azure.AI.Projects 2.0.0 GA releases confirms these types are genuinely unavailable.

#### Affected Samples (8 total, cannot compile)

| Sample | Primary Issue | Type Count |
|--------|--------------|-----------|
| AzureArchitect_Step01_Simple | ChatClient integration | 2 errors |
| AzureArchitect_Step02a_SingleTurn | AgentThread not found | 3 errors |
| AzureArchitect_Step02b_Multiturn | AgentThread, AgentRunResponseUpdate | 4 errors |
| AzureArchitect_Step02c_PrebuiltAgent | agentClient properties missing | 5 errors |
| AzureArchitect_Step05_MCPServer | CreateAIAgent extension removed | 4 errors |
| AgentPersistence_Step01_Unpublished | AgentThread not found | 3 errors |
| AgentPersistence_Step02_PublishedCosmosDB | AgentThread not found | 6 errors |
| DocumentClassifierWorkflow | InProcessExecution API changed | 5 errors |

### Recommended Action: Architecture Rewrite Required

These samples require **complete refactoring**, not simple package updates. The refactoring should:

1. **Replace `AgentThread` references** → Use `Azure.AI.Agents.Persistent` thread APIs instead
2. **Replace `AgentVersion` references** → Use `ProjectsAgentVersion` (if available) or new GA patterns
3. **Replace `ChatClient.CreateAIAgent()` → Use `AIProjectClient` agent creation methods directly
4. **Update streaming** → Use new run/response APIs from persistent agents library

**Effort estimate**: 20-40 hours per sample (requires deep API redesign)

---

## Summary

- **Python Samples**: ✅ Ready for production (v1.0.0 GA compatible)
- **.NET Samples**: ⚠️ Cannot compile - Preview APIs absent from GA releases
- **Blocking Issue**: Samples require code refactoring, not just package updates
- **Root Cause**: Built against internal/preview APIs removed in GA transition
- **Timeline**: Manual refactoring using new GA API patterns required before deployment
