---
applyTo: '.copilot-tracking/changes/2026-04-07/mai-image-2-blazor-sample-changes.md'
---
<!-- markdownlint-disable-file -->
# Implementation Plan: .NET 10 Blazor MAI-Image-2 Sample App

## Overview

Create a minimal .NET 10 Blazor Web App sample under samples/dotnet that generates images with the MAI-Image-2 model through the documented MAI REST endpoint, authenticated with DefaultAzureCredential.

## Objectives

### User Requirements

* Create a new .NET 10 Blazor sample app in samples/dotnet using the basic Blazor app template. — Source: conversation request
* Allow configuration for the Microsoft Foundry endpoint and authenticate with DefaultAzureCredential using Azure CLI locally. — Source: conversation request
* Research and implement the correct MAI-Image-2 inference code path and SDK choice. — Source: conversation request
* Keep the app very simple: prompt entry, model parameter inputs, generated image display, and error display. — Source: conversation request

### Derived Objectives

* Use the MAI REST route rather than an unverified typed SDK client. — Derived from: research found no verified first-party .NET MAI SDK path and MAI docs explicitly define the REST contract
* Configure the sample around the Foundry resource endpoint plus deployment name, and document why this differs from the user's original project-endpoint wording. — Derived from: MAI image generation is documented against the resource-scoped MAI route
* Add the project to the existing samples solution and include narrow unit coverage so repository build and CI gates remain green. — Derived from: repository conventions and CI workflow requirements in dotnet sample research

## Context Summary

### Project Files

* samples/dotnet/global.json - defines the .NET 10 SDK baseline for dotnet samples.
* samples/dotnet/microsoft-foundry-jumpstart-samples.slnx - existing solution that must include the new sample and tests.
* samples/dotnet/README.md - documents dotnet sample structure and run/test commands.
* samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs - reference for appsettings plus environment variable layering and DefaultAzureCredential.
* .github/workflows/lint-and-test-dotnet-apps.yml - CI gates covering restore, build, format verification, and unit tests.

### References

* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md - primary research findings, selected approach, and MAI endpoint evidence.
* .copilot-tracking/research/subagents/2026-04-07/mai-image-2-sdk-and-inference-research.md - SDK and REST-path evaluation.
* .copilot-tracking/research/subagents/2026-04-07/blazor-auth-config-research.md - auth, RBAC, and configuration findings.
* .copilot-tracking/research/subagents/2026-04-07/repo-dotnet-sample-conventions-research.md - repository-specific project and test conventions.
* https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai - MAI-Image-2 endpoint and request/response contract.

### Standards References

* .github/copilot-instructions.md — repository architecture, sample conventions, and validation expectations.
* .github/instructions/csharp-14-best-practices.instructions.md — C# style and implementation guidance for new .NET files.

## Implementation Checklist

### [ ] Implementation Phase 1: Scaffold the sample shell

<!-- parallelizable: false -->

* [ ] Step 1.1: Reconfirm that no first-party .NET MAI client path has appeared since planning.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 12-27)
* [ ] Step 1.2: Create the basic Blazor Web App project structure under samples/dotnet/src/blazor/mai-image-2-simple.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 29-50)
* [ ] Step 1.3: Add MicrosoftFoundry options binding and startup wiring in Program.cs and appsettings.json.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 52-71)
* [ ] Step 1.4: Update samples/dotnet/microsoft-foundry-jumpstart-samples.slnx with the new app project.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 73-88)
* [ ] Step 1.5: Validate project scaffolding and solution wiring.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 90-96)

### [x] Implementation Phase 2: Implement the MAI inference slice

<!-- parallelizable: false -->

* [x] Step 2.1: Implement the REST-backed MAI service with DefaultAzureCredential authentication.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 102-126)
* [x] Step 2.2: Add focused unit tests and wire the new test project into the solution.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 128-145)
* [x] Step 2.3: Validate build and targeted unit tests for the inference layer.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 147-153)

### [x] Implementation Phase 3: Build the UI and docs

<!-- parallelizable: false -->

* [x] Step 3.1: Replace the default home page with the prompt-to-image workflow.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 159-178)
* [x] Step 3.2: Document prerequisites, endpoint configuration, and run instructions.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 180-198)
* [x] Step 3.3: Validate the completed sample slice inside the dotnet solution.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 200-207)

### [ ] Implementation Phase 4: Validation

<!-- parallelizable: false -->

* [ ] Step 4.1: Run full dotnet validation for restore, build, format, and unit tests.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 213-219)
* [ ] Step 4.2: Run a conditional live MAI-Image-2 smoke test when endpoint access is available.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 221-234)
* [ ] Step 4.3: Fix minor compile, formatting, unit-test, or live-smoke issues limited to the new sample scope.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 236-238)
* [ ] Step 4.4: Report blocking live-service or contract issues as follow-on work instead of expanding scope.
  * Details: .copilot-tracking/details/2026-04-07/mai-image-2-blazor-sample-details.md (Lines 240-242)

## Planning Log

See .copilot-tracking/plans/logs/2026-04-07/mai-image-2-blazor-sample-log.md for discrepancy tracking, implementation paths considered, and suggested follow-on work.

## Dependencies

* .NET 10 SDK from samples/dotnet/global.json
* Azure.Identity package for DefaultAzureCredential auth
* Access to a MAI-Image-2 deployment in Microsoft Foundry
* Azure AI User role for the executing identity
* Existing samples/dotnet solution and CI workflow for validation

## Success Criteria

* A new minimal Blazor sample exists under samples/dotnet/src and is added to the samples solution. — Traces to: user requirement for a new .NET 10 Blazor sample
* The sample uses DefaultAzureCredential and documents Azure CLI local authentication. — Traces to: user requirement and auth research findings
* The sample calls MAI-Image-2 through the documented MAI REST contract and renders either image output or errors. — Traces to: MAI endpoint research and UI requirement
* Unit validation and dotnet solution validation can run through the repository's established build/test workflow. — Traces to: repository conventions and CI research
