<!-- markdownlint-disable-file -->
# Implementation Details: .NET 10 Blazor MAI-Image-2 Sample App

## Context Reference

Sources: .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md, .copilot-tracking/research/subagents/2026-04-07/mai-image-2-sdk-and-inference-research.md, .copilot-tracking/research/subagents/2026-04-07/blazor-auth-config-research.md, .copilot-tracking/research/subagents/2026-04-07/repo-dotnet-sample-conventions-research.md

## Implementation Phase 1: Scaffold the sample shell

<!-- parallelizable: false -->

### Step 1.1: Reconfirm the MAI client path before coding

Perform one quick documentation check immediately before implementation to confirm no first-party .NET MAI-specific client has been published since planning. If one exists and is fully documented for MAI-Image-2, record the change and reassess the service step before proceeding. Otherwise, continue with the REST wrapper plan.

Files:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md - update only if the SDK recommendation materially changes before implementation begins.

Success criteria:
* The implementation begins with a confirmed MAI client path rather than relying on stale SDK assumptions.
* Any change in the official SDK landscape is captured before code edits spread through the sample.

Context references:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 31-36) - follow-on research items.

Dependencies:
* None.

### Step 1.2: Create a minimal Blazor Web App project

Create a new basic Blazor Web App under samples/dotnet/src/blazor/mai-image-2-simple targeting net10.0. Keep the template close to the default output so the sample remains intentionally simple and easy to compare with standard Blazor guidance.

Files:
* samples/dotnet/src/blazor/mai-image-2-simple/mai-image-2-simple.csproj - new sample project targeting net10.0 with Azure.Identity dependency only if template does not already include required packages.
* samples/dotnet/src/blazor/mai-image-2-simple/Program.cs - default Blazor startup, later extended for options and service registration.
* samples/dotnet/src/blazor/mai-image-2-simple/Components/Pages/Home.razor - default page to replace with prompt-driven image generation UI.
* samples/dotnet/src/blazor/mai-image-2-simple/appsettings.json - sample defaults for endpoint, deployment, width, and height.

Success criteria:
* A new runnable Blazor sample exists under samples/dotnet/src/blazor/mai-image-2-simple.
* The project targets net10.0 and builds as part of the samples solution.
* The template remains close to the default Blazor app rather than introducing extra architectural layers.

Context references:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 113-123) - repository structure and implementation patterns.
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 129-135) - MAI route and payload basics.

Dependencies:
* samples/dotnet/global.json net10.0 baseline.
* Step 1.1 completion.

### Step 1.3: Add configuration and startup wiring

Add a strongly typed options class for the Foundry endpoint, deployment name, and default image dimensions. Register options binding and the image generation service in Program.cs using the standard appsettings plus environment variable layering already used in repository samples.

Files:
* samples/dotnet/src/blazor/mai-image-2-simple/Models/MicrosoftFoundryOptions.cs - options class with validation-friendly properties.
* samples/dotnet/src/blazor/mai-image-2-simple/Program.cs - configuration binding and DI registration.
* samples/dotnet/src/blazor/mai-image-2-simple/appsettings.json - default values and placeholder endpoint text.

Success criteria:
* Configuration keys are grouped under a single MicrosoftFoundry section.
* Service registration is ready for injection into the page component.
* Defaults satisfy MAI minimum size constraints or guard against invalid values.

Context references:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 153-160) - configuration example.
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 176-182) - preferred config approach.

Dependencies:
* Step 1.2 completion.

### Step 1.4: Update the samples solution with the new app project

Add the new Blazor sample project to samples/dotnet/microsoft-foundry-jumpstart-samples.slnx in the appropriate folder group so local tasks and CI can discover the app as soon as it exists.

Files:
* samples/dotnet/microsoft-foundry-jumpstart-samples.slnx - add the new sample project entry.

Success criteria:
* The app project is present in the samples solution.
* Standard dotnet build and format commands include the new sample without ad hoc project paths.

Context references:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 113-118) - repository structure requirements.

Dependencies:
* Step 1.2 completion.

### Step 1.5: Validate phase changes

Run build-focused validation once the project is added to the solution. Defer tests until service and UI logic exist.

Validation commands:
* dotnet build microsoft-foundry-jumpstart-samples.slnx - validate sample compiles inside the existing solution.
* dotnet format microsoft-foundry-jumpstart-samples.slnx --verify-no-changes - confirm template edits follow repository formatting expectations.

## Implementation Phase 2: Implement MAI image generation service

<!-- parallelizable: false -->

### Step 2.1: Implement the REST-backed MAI service with Entra auth

Create a small service over HttpClient that acquires a bearer token from DefaultAzureCredential, posts to /mai/v1/images/generations, parses the response, and returns either a base64 image payload or a structured error result suitable for UI display.

Files:
* samples/dotnet/src/blazor/mai-image-2-simple/Services/IMaiImageService.cs - service contract to isolate page logic from HTTP details.
* samples/dotnet/src/blazor/mai-image-2-simple/Services/MaiImageService.cs - request construction, token acquisition, response parsing, and error mapping.
* samples/dotnet/src/blazor/mai-image-2-simple/Models/MaiImageRequest.cs - prompt and parameter model.
* samples/dotnet/src/blazor/mai-image-2-simple/Models/MaiImageResult.cs - success and error model returned to UI.
* samples/dotnet/src/blazor/mai-image-2-simple/Models/MaiApiContracts.cs - internal DTOs for response parsing and service-local schema handling.

Success criteria:
* The service authenticates with DefaultAzureCredential without requiring API keys.
* The request uses the deployment name in the model field and enforces MAI dimension constraints before sending.
* Success returns a base64 PNG payload ready for a data URL.
* Failures return friendly error content without leaking raw exception noise into the UI.

Context references:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 127-135) - MAI technical findings.
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 137-152) - .NET code pattern for token acquisition and POST request.
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 198-204) - selected implementation details.

Dependencies:
* Step 1.3 completion.
* Azure.Identity package reference available.

### Step 2.2: Add focused unit coverage and wire the new test project into the solution

Create narrow unit tests for dimension validation, request/result handling, and representative error parsing. Keep tests independent of live Azure calls by mocking HttpMessageHandler and avoiding credential acquisition in unit scope where possible. Add the new test project to samples/dotnet/microsoft-foundry-jumpstart-samples.slnx once it exists.

Files:
* samples/dotnet/tests/unit/blazor/mai-image-2-simple/MaiImageServiceTests.cs - service-level tests for validation and parsing.
* samples/dotnet/tests/unit/blazor/mai-image-2-simple/mai-image-2-simple.Tests.csproj - MSTest project referencing the sample project.
* samples/dotnet/microsoft-foundry-jumpstart-samples.slnx - add the new test project entry.

Success criteria:
* Unit tests cover minimum dimension guardrails and base64 response parsing.
* Tests are marked with Unit category to satisfy the repository filter.
* No live cloud dependency exists in unit test execution.
* The new test project is present in the samples solution before Phase 2 validation runs.

Context references:
* .copilot-tracking/research/subagents/2026-04-07/repo-dotnet-sample-conventions-research.md - unit test and CI expectations.

Dependencies:
* Step 2.1 completion.

### Step 2.3: Validate phase changes

Run the sample build and targeted unit tests after the service layer is implemented.

Validation commands:
* dotnet build microsoft-foundry-jumpstart-samples.slnx - validate service and tests compile.
* dotnet test --solution microsoft-foundry-jumpstart-samples.slnx --filter TestCategory=Unit --configuration Release --no-restore - run unit coverage slice for new sample.

## Implementation Phase 3: Build the simple Blazor UI and documentation

<!-- parallelizable: false -->

### Step 3.1: Replace the home page with a prompt-to-image workflow

Update the default home page to collect a prompt, width, and height, invoke the MAI image service asynchronously, and render loading, error, and success states. Keep the UI minimal: one form, one submit button, one image result panel, and one error region.

Files:
* samples/dotnet/src/blazor/mai-image-2-simple/Components/Pages/Home.razor - form controls, submit flow, and image/error rendering.
* samples/dotnet/src/blazor/mai-image-2-simple/Components/Pages/Home.razor.cs or inline @code block - simple state management for loading and error handling.
* samples/dotnet/src/blazor/mai-image-2-simple/wwwroot/app.css - minimal styling only if the default template needs small layout adjustments.

Success criteria:
* User can submit a prompt and see either a generated image or a clear error.
* The page disables repeated submission while a request is in flight.
* The rendered image uses a data URL built from the returned base64 payload.

Context references:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 169-182) - selected Blazor architecture and UX scope.
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 205-210) - UI binding pattern.

Dependencies:
* Step 2.1 completion.

### Step 3.2: Document prerequisites and run instructions

Write a sample README that explains the resource endpoint requirement, MAI deployment requirement, Azure AI User role, az login prerequisite, configuration keys, and run commands. Update the dotnet sample index if needed so the sample is discoverable.

Files:
* samples/dotnet/src/blazor/mai-image-2-simple/README.md - sample-specific documentation.
* samples/dotnet/README.md - add a short entry if the repository index enumerates samples explicitly.

Success criteria:
* README clearly distinguishes resource endpoint from project endpoint.
* README includes az login and RBAC prerequisites.
* Documentation is sufficient to run the sample without reading source code.

Context references:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 127-135) - MAI endpoint contract.
* .copilot-tracking/research/subagents/2026-04-07/blazor-auth-config-research.md - auth and RBAC findings.

Dependencies:
* Step 3.1 completion.

### Step 3.3: Validate phase changes

Run the full dotnet validation slice after documentation and solution wiring are complete.

Validation commands:
* dotnet build microsoft-foundry-jumpstart-samples.slnx
* dotnet format microsoft-foundry-jumpstart-samples.slnx --verify-no-changes
* dotnet test --solution microsoft-foundry-jumpstart-samples.slnx --filter TestCategory=Unit --configuration Release --no-restore

## Implementation Phase 4: Final validation

<!-- parallelizable: false -->

### Step 4.1: Run full project validation

Execute all validation commands relevant to the modified dotnet sample scope:
* dotnet restore microsoft-foundry-jumpstart-samples.slnx
* dotnet build microsoft-foundry-jumpstart-samples.slnx
* dotnet format microsoft-foundry-jumpstart-samples.slnx --verify-no-changes
* dotnet test --solution microsoft-foundry-jumpstart-samples.slnx --filter TestCategory=Unit --configuration Release --no-restore

### Step 4.2: Run a conditional live smoke test against MAI-Image-2

If a real Foundry resource endpoint, deployment name, and authorized identity are available, run the sample locally and verify one successful prompt and one representative failure path. Capture any runtime contract mismatch before closing implementation.

Success criteria:
* The sample can generate at least one image against a real MAI-Image-2 deployment when access is available.
* Runtime failures, if any, are documented with enough detail to guide follow-up fixes.

Context references:
* .copilot-tracking/research/2026-04-07/mai-image-2-blazor-sample-research.md (Lines 31-36) - live validation follow-on research item.

Dependencies:
* Step 4.1 completion.
* Access to a configured MAI-Image-2 deployment.

### Step 4.3: Fix minor validation issues

Iterate on straightforward compile, formatting, or test failures. Keep fixes limited to the new sample, new tests, or necessary solution wiring.

### Step 4.4: Report blocking issues

When failures require live Azure access, updated endpoint contracts, or broader repository changes, document them and hand them back as implementation follow-up instead of expanding scope inline.

## Dependencies

* .NET 10 SDK from samples/dotnet/global.json
* Azure.Identity for DefaultAzureCredential auth
* Access to a MAI-Image-2 deployment in Microsoft Foundry
* Azure AI User role for the executing identity

## Success Criteria

* The repository contains a minimal .NET 10 Blazor sample for MAI-Image-2 image generation.
* The sample authenticates with DefaultAzureCredential and documents Azure CLI local usage.
* The sample exposes prompt and image parameter input and renders generated image or error output.
* The sample and its tests build and validate through the existing dotnet solution and CI workflow.
