<!-- markdownlint-disable-file -->
# Release Changes: .NET 10 Blazor MAI-Image-2 Sample App

**Related Plan**: mai-image-2-blazor-sample-plan.instructions.md
**Implementation Date**: 2026-04-07

## Summary

Implementing a minimal .NET 10 Blazor sample app that calls MAI-Image-2 through the documented MAI REST endpoint with DefaultAzureCredential authentication.
Completed the missing Phase 2 service/test slice and Phase 3 UI/documentation slice required before rerunning review.

## Changes

### Added

* samples/dotnet/src/blazor/mai-image-2-simple/Services/IMaiImageService.cs - Introduced MAI service abstraction for page-level image generation calls.
* samples/dotnet/src/blazor/mai-image-2-simple/Services/MaiImageService.cs - Implemented REST call path to /mai/v1/images/generations with DefaultAzureCredential token acquisition, dimension guardrails, and friendly error mapping.
* samples/dotnet/src/blazor/mai-image-2-simple/Models/MaiImageRequest.cs - Added prompt and image-parameter request model.
* samples/dotnet/src/blazor/mai-image-2-simple/Models/MaiImageResult.cs - Added success/error result model consumed by the UI.
* samples/dotnet/src/blazor/mai-image-2-simple/Models/MaiApiContracts.cs - Added internal MAI API request/response/error DTOs for contract parsing.
* samples/dotnet/tests/unit/blazor/mai-image-2-simple/mai-image-2-simple.Tests.csproj - Added sample-specific MSTest project.
* samples/dotnet/tests/unit/blazor/mai-image-2-simple/MaiImageServiceTests.cs - Added unit tests for dimension validation, success parsing, and error mapping.
* samples/dotnet/src/blazor/mai-image-2-simple/README.md - Added sample runbook with auth, endpoint, and configuration guidance.

### Modified

* samples/dotnet/src/blazor/mai-image-2-simple/Program.cs - Registered TokenCredential singleton and typed MAI service HttpClient.
* samples/dotnet/src/blazor/mai-image-2-simple/Components/Pages/Home.razor - Replaced template page with prompt-to-image workflow including loading/error/success states.
* samples/dotnet/src/blazor/mai-image-2-simple/wwwroot/app.css - Added minimal styles for form and image panel.
* samples/dotnet/microsoft-foundry-jumpstart-samples.slnx - Added blazor sample unit test project to solution.
* samples/dotnet/README.md - Added blazor sample discoverability entry.

### Removed

* None.

## Additional or Deviating Changes

* Initial Phase 2 build failed once due to incorrect test project reference path.
	* Corrected the relative ProjectReference in samples/dotnet/tests/unit/blazor/mai-image-2-simple/mai-image-2-simple.Tests.csproj and reran validation successfully.
* Existing warnings remain outside this implementation scope.
	* NU1902 warning on KubernetesClient in samples/dotnet/src/orchestrator/AppHost/AppHost.csproj persists.
	* MSTEST0001 analyzer warning is present for test parallelization configuration.
* Live MAI smoke-test execution remains pending.
	* Endpoint/deployment runtime access was not part of this Phase 2 and 3 completion pass.
* Unrelated infrastructure delta remains present.
	* infra/sample-model-deployments.json includes independent edits and was not modified in this phase execution.

## Release Summary

Scope completed in this pass:

* Plan coverage:
	* Phase 2 Step 2.1, Step 2.2, and Step 2.3 completed.
	* Phase 3 Step 3.1, Step 3.2, and Step 3.3 completed.
* Validation evidence captured during implementation:
	* dotnet build microsoft-foundry-jumpstart-samples.slnx: Pass
	* dotnet format microsoft-foundry-jumpstart-samples.slnx --verify-no-changes: Pass
	* dotnet test --solution microsoft-foundry-jumpstart-samples.slnx --filter TestCategory=Unit --configuration Release --no-restore: Pass (31 passed, 0 failed)
* Remaining scope:
	* Phase 4 validation, including conditional live smoke test and explicit blocked-or-pass outcome recording, remains open.
