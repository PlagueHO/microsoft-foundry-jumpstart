# Document Classifier Workflow

A Microsoft Agent Framework workflow sample demonstrating a complex document classification pipeline with parallel execution, conditional routing, and AI-powered rationalization.

## Overview

This workflow implements a document classification system based on the MAML (Microsoft Agent Markup Language) workflow pattern:

```text
┌─────────────────┐
│      Start      │
│ Receive input   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PreparePrompt   │  Routes based on classifier type
│    Routing      │  (PI / ContentType / Standard)
└────────┬────────┘
         │
         ▼ ─────────────────────────────────────────
         │           PARALLEL EXECUTION            │
    ┌────┴────┬────────────┬────────────┐          │
    ▼         ▼            ▼            │          │
┌───────┐ ┌────────┐ ┌───────────────┐  │          │
│Azure  │ │Suggest │ │   Generic     │  │          │
│  PI   │ │Content │ │Identification │  │          │
│Service│ │Type LLM│ │     LLM       │  │          │
└───┬───┘ └────┬───┘ └──────┬────────┘  │          │
    │          │            │           │          │
    └──────────┴────────────┘           │          │
               │                        ─────────────
               ▼
┌─────────────────┐
│  ProcessOutput  │  Merge into unified payload
│     Merge       │  → candidateResponses
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Encompass5Search│  Heart/variant/synonym
│                 │  matching
└────────┬────────┘
         │
         ▼
      ┌──┴──┐
      │Match│───Yes──▶ Emit CandidateResponse ──▶ END
      │  ?  │
      └──┬──┘
         │ No
         ▼
┌─────────────────────────────────────────────────┐
│           STANDALONERATIONLISER                 │
│                                                 │
│  ┌─────────────────┐                            │
│  │ParseRationalizer│  Shape payload for LLM     │
│  │     Input       │                            │
│  └────────┬────────┘                            │
│           │                                     │
│      ┌────┴────┐                                │
│      ▼         ▼                                │
│  ┌───────┐ ┌────────────┐                       │
│  │Generic│ │ContentType │  Both decide:         │
│  │Ration-│ │Rationalizer│ CREATE_NEW/MAP/       │
│  │alizer │ │    LLM     │ MAP_AS_VARIANT        │
│  └───┬───┘ └─────┬──────┘                       │
│      │           │                              │
│      └─────┬─────┘                              │
│            ▼                                    │
│  ┌─────────────────┐                            │
│  │ParseRationalizer│  Normalize decision JSON   │
│  │    Output       │                            │
│  └────────┬────────┘                            │
│           ▼                                     │
│  ┌──────────────────┐                           │
│  │SelectRationalizer│  Choose best output       │
│  │     Output       │  (ContentType or Generic) │
│  └────────┬─────────┘                           │
│           ▼                                     │
│  ┌─────────────────┐                            │
│  │ AssembleOutput  │  Emit final candidates     │
│  └────────┬────────┘                            │
│           │                                     │
└───────────┼─────────────────────────────────────┘
            ▼
         ┌─────┐
         │ End │
         └─────┘
```

## Prerequisites

- .NET 10.0 SDK
- Azure OpenAI deployment (optional - falls back to heuristic classification)

## Configuration

Set the following environment variables for LLM-powered classification:

```bash
# Required for LLM-based classification
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"  # or your deployment name
```

If these are not set, the workflow uses heuristic-based classification.

## Running the Sample

```bash
cd samples/dotnet/src/agent-framework/DocumentClassifierWorkflow
dotnet run
```

## Workflow Components

### Executors

| Executor | Purpose |
| -------- | ------- |
| `PreparePromptExecutor` | Routes input based on classifier type (PI/ContentType/Standard) |
| `AzurePIServiceExecutor` | Detects personally identifiable information |
| `SuggestContentTypeExecutor` | LLM-based content type suggestion |
| `GenericIdentificationExecutor` | LLM-based generic document identification |
| `ProcessOutputExecutor` | Merges parallel results into unified payload |
| `Encompass5SearchExecutor` | Searches for matches in known content types |
| `MatchDecisionExecutor` | Routes based on match result |
| `ParseRationalizerInputExecutor` | Prepares input for rationalization |
| `GenericRationalizerExecutor` | Generic rationalization decisions |
| `ContentTypeRationalizerExecutor` | Content-type specific rationalization |
| `ParseRationalizerOutputExecutor` | Combines rationalizer outputs |
| `SelectRationalizerOutputExecutor` | Selects best rationalization result |
| `AssembleOutputExecutor` | Produces final workflow output |

### Rationalization Decisions

The rationalizers can make three decisions:

- **CREATE_NEW**: Document type is genuinely novel
- **MAP**: Direct mapping to an existing category
- **MAP_AS_VARIANT**: Similar to existing category but distinct enough to be a variant

## Sample Output

```text
Document Classifier Workflow - Microsoft Agent Framework
============================================================

Processing: Legal Contract (Content Type path)
--------------------------------------------------

  [RESULT] Classification Output:
    Selected Rationalizer: N/A (direct match)
    Final Decision: Match found
    Candidate Responses:
      - Type: Legal Contract
        Confidence: 95%
        Source: Encompass5Search (heart)
```

## Key Microsoft Agent Framework Patterns Used

1. **Fan-Out Edges**: Parallel execution of PI, ContentType, and Generic processors
2. **Fan-In Aggregation**: Merging results from parallel executors
3. **Conditional Routing**: MatchDecision routes based on search results
4. **Multi-handler Executors**: ProcessOutputExecutor handles multiple input types
5. **Output Yielding**: Direct output emission vs. message forwarding

## Extending the Workflow

### Adding New Content Types

Edit the `ContentTypeVariants` dictionary in `Encompass5SearchExecutor.cs`:

```csharp
["Your New Type"] = ["Variant1", "Variant2", "Synonym"]
```

### Custom LLM Prompts

Modify the `SystemPrompt` constants in the LLM executor classes.

### Additional PI Detection

Extend the `ContainsPIPattern` method in `AzurePIServiceExecutor.cs`.

## License

Copyright (c) Microsoft. All rights reserved.
