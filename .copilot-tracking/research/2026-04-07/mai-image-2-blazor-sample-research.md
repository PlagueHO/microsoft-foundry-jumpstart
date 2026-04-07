<!-- markdownlint-disable-file -->
# Task Research: .NET 10 Blazor MAI-Image-2 Sample App

Research for implementing a new, minimal .NET 10 Blazor sample app under samples/dotnet that demonstrates text-to-image inference using the MAI-Image-2 model as a Models Direct model in Microsoft Foundry.

## Task Implementation Requests

* Create a new .NET 10 Blazor sample app in samples/dotnet (or subfolder) using the basic Blazor + .NET 10 template.
* Configure the app to allow Microsoft Foundry project endpoint configuration.
* Authenticate using DefaultAzureCredential with Azure CLI credential available.
* Research exact requirements and code for MAI-Image-2 inference and identify recommended SDK(s).
* Build a simple UI: prompt input, model parameter selection, image output or error message.

## Scope and Success Criteria

* Scope: Research implementation requirements, SDK choices, endpoint/auth setup, inference API usage, and minimal Blazor wiring pattern for this repository.
* Assumptions:
  * MAI-Image-2 is available to the target Foundry project as a Models Direct deployment.
  * The sample should align with repository conventions for samples/dotnet.
  * The app can use environment variables or app settings for endpoint/deployment configuration.
* Success Criteria:
  * Verified SDK/API recommendation for .NET and MAI-Image-2 image generation.
  * End-to-end minimal code pattern for prompt -> image bytes/base64 -> display.
  * Clear auth approach using DefaultAzureCredential (Azure CLI in local development).
  * Concrete implementation plan with file-level impact for samples/dotnet.

## Outline

1. Inspect repository sample conventions and structure for new dotnet sample placement.
2. Research MAI-Image-2 model invocation options in Foundry from .NET (SDK vs REST).
3. Validate authentication and endpoint configuration requirements.
4. Produce minimal Blazor architecture and parameter model.
5. Evaluate alternatives and select one implementation approach.

## Potential Next Research

* Live smoke test against a real MAI-Image-2 deployment.
  * Reasoning: Validate current response shape and error payload details in runtime conditions.
  * Reference: https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai
* Verify whether a first-party .NET MAI-specific SDK client is published after this research date.
  * Reasoning: Replace custom REST wrapper once first-class support exists.
  * Reference: https://learn.microsoft.com/azure/foundry/foundry-models/concepts/endpoints

## Research Executed

### File Analysis

* samples/dotnet/README.md
  * documents dotnet sample structure (src and tests) and standard build/run/test commands.
* samples/dotnet/microsoft-foundry-jumpstart-samples.slnx
  * confirms project organization and requirement to add new sample project to solution.
* samples/dotnet/global.json
  * confirms .NET 10 SDK baseline for samples.
* samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs
  * demonstrates configuration layering and DefaultAzureCredential usage pattern.
* samples/dotnet/src/agent-framework/DocumentClassifierWorkflow/Program.cs
  * demonstrates AzureCliCredential usage in existing samples.
* .github/workflows/lint-and-test-dotnet-apps.yml
  * confirms dotnet CI gates for restore, build, format verification, and tests.
* .vscode/tasks.json
  * confirms local build/test/format tasks against samples/dotnet solution.

### Code Search Results

* Search term: DefaultAzureCredential
  * Found in dotnet samples, including semantic-kernel sample startup configuration.
* Search term: AzureCliCredential
  * Found in multiple agent-framework samples.
* Search term: MAI / image generation in dotnet samples
  * No existing C# MAI-Image-2 sample found in current repository.

### External Research

* Microsoft Learn Foundry MAI model usage:
  * https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai
  * Confirms MAI endpoint route and image generation request/response behavior.
* Microsoft Learn Foundry model endpoints and migration guidance:
  * https://learn.microsoft.com/azure/foundry/foundry-models/concepts/endpoints
  * https://learn.microsoft.com/azure/foundry/how-to/model-inference-to-openai-migration
  * Confirms Azure AI Inference beta SDK retirement guidance and OpenAI/v1 migration for supported models.
* Azure Identity credential chain docs:
  * https://learn.microsoft.com/dotnet/azure/sdk/authentication/credential-chains#defaultazurecredential-overview
  * Confirms DefaultAzureCredential includes Azure CLI and managed identity chain behavior.
* Foundry RBAC docs:
  * https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry
  * Confirms Azure AI User role alignment for model use in projects.
* Blazor service abstraction guidance:
  * https://learn.microsoft.com/aspnet/core/blazor/call-web-api?view=aspnetcore-10.0#service-abstractions-for-web-api-calls

### Project Conventions

* Standards referenced:
  * .github/copilot-instructions.md
  * .github/instructions/csharp-14-best-practices.instructions.md
* Instructions followed:
  * Keep sample simple, explicit config, net10.0, and repository README/project structure conventions.

## Key Discoveries

### Project Structure

* New sample should be under samples/dotnet/src and ideally mirrored by a unit test project under samples/dotnet/tests/unit when practical.
* New sample must be added to samples/dotnet/microsoft-foundry-jumpstart-samples.slnx so local tasks and CI include it.
* net10.0 is the baseline in samples/dotnet/global.json.

### Implementation Patterns

* Existing samples use two auth styles:
  * AzureCliCredential explicitly (many agent-framework samples).
  * DefaultAzureCredential (semantic-kernel sample and others).
* For this request, DefaultAzureCredential should be the primary implementation because it satisfies local Azure CLI auth and hosted managed identity without code changes.
* Existing samples typically use appsettings plus environment variable fallback for endpoint/deployment settings.

### MAI-Image-2 Technical Findings

* MAI-Image-2 uses MAI route for image generation:
  * POST https://<resource>.services.ai.azure.com/mai/v1/images/generations
* Request body supports model, prompt, width, height (and related options where supported).
* Response includes base64 image payload in data[0].b64_json.
* Constraints include width >= 768, height >= 768, and width*height <= 1048576.
* Model is preview with quota/region constraints.

### Complete Examples

```csharp
using Azure.Core;
using Azure.Identity;
using System.Net.Http.Headers;
using System.Net.Http.Json;

public sealed class MaiImageClient
{
    private static readonly string[] Scopes =
        ["https://cognitiveservices.azure.com/.default"];

    private readonly HttpClient _httpClient;
    private readonly DefaultAzureCredential _credential;

    public MaiImageClient(HttpClient httpClient)
    {
        _httpClient = httpClient;
        _credential = new DefaultAzureCredential();
    }

    public async Task<string> GenerateBase64Async(
        Uri resourceEndpoint,
        string deploymentName,
        string prompt,
        int width,
        int height,
        CancellationToken cancellationToken)
    {
        var token = await _credential.GetTokenAsync(
            new TokenRequestContext(Scopes),
            cancellationToken);

        using var request = new HttpRequestMessage(
            HttpMethod.Post,
            new Uri(resourceEndpoint, "/mai/v1/images/generations"));

        request.Headers.Authorization =
            new AuthenticationHeaderValue("Bearer", token.Token);

        request.Content = JsonContent.Create(new
        {
            model = deploymentName,
            prompt,
            width,
            height
        });

        using var response = await _httpClient.SendAsync(
            request,
            cancellationToken);

        var payload = await response.Content.ReadFromJsonAsync<MaiResponse>(
            cancellationToken: cancellationToken);

        response.EnsureSuccessStatusCode();

        return payload?.Data?.FirstOrDefault()?.Base64Json
            ?? throw new InvalidOperationException("No image returned.");
    }

    private sealed record MaiResponse(MaiImageData[] Data);

    private sealed record MaiImageData(
        [property: System.Text.Json.Serialization.JsonPropertyName("b64_json")]
        string Base64Json);
}
```

### API and Schema Documentation

* MAI model usage and endpoint details:
  * https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai
* Foundry endpoint model concepts:
  * https://learn.microsoft.com/azure/foundry/foundry-models/concepts/endpoints
* OpenAI image generation reference (alternative API family, not selected for MAI-Image-2 route):
  * https://learn.microsoft.com/azure/foundry/openai/reference#image-generation

### Configuration Examples

```json
{
  "MicrosoftFoundry": {
    "ResourceEndpoint": "https://<resource>.services.ai.azure.com",
    "ImageDeployment": "mai-image-2",
    "DefaultWidth": 1024,
    "DefaultHeight": 1024
  }
}
```

## Technical Scenarios

### MAI-Image-2 Inference from .NET 10 Blazor

Simple server-side Blazor sample that accepts prompt and image parameters, calls MAI-Image-2 inference with Entra auth via DefaultAzureCredential, and renders the returned PNG from base64.

**Requirements:**

* Minimal Blazor app UX.
* Foundry resource endpoint and deployment/model configuration.
* DefaultAzureCredential auth.
* Image display and error handling.

**Preferred Approach:**

* Use Blazor Web App (.NET 10 basic template) with a thin service wrapper around HttpClient that calls MAI REST endpoint directly.
* Use DefaultAzureCredential token acquisition for Authorization header.
* Keep configuration in appsettings with environment variable overrides.

Rationale:

* MAI documentation explicitly defines MAI route and payload.
* No verified first-party .NET MAI SDK sample path was found for this route.
* This approach stays minimal and transparent for a sample app.

```text
samples/dotnet/src/blazor/mai-image-2-simple/
samples/dotnet/src/blazor/mai-image-2-simple/Pages/
samples/dotnet/src/blazor/mai-image-2-simple/Services/
samples/dotnet/src/blazor/mai-image-2-simple/Models/
samples/dotnet/src/blazor/mai-image-2-simple/appsettings.json
samples/dotnet/src/blazor/mai-image-2-simple/README.md
samples/dotnet/tests/unit/blazor/mai-image-2-simple/
```

**Implementation Details:**

1. Create basic Blazor Web App project targeting net10.0.
2. Add options class for endpoint/deployment/default size values.
3. Register DefaultAzureCredential-backed image service in DI.
4. Add one page/component with:
   * prompt textarea
   * width/height numeric controls (with min/validation)
   * submit button
   * generated image output and error panel
5. Add README with prerequisites:
   * model deployment available
   * az login completed
   * Azure AI User permissions
6. Add project to solution and optional minimal unit tests for service response parsing and validation.

```csharp
builder.Services.Configure<MicrosoftFoundryOptions>(
    builder.Configuration.GetSection("MicrosoftFoundry"));
builder.Services.AddHttpClient<IMaiImageService, MaiImageService>();

// In component submit handler:
ImageDataUrl = $"data:image/png;base64,{result.Base64Image}";
ErrorMessage = null;
```

#### Considered Alternatives

1. Alternative: Use Azure.AI.Inference SDK for image generation.
   * Rejected because published guidance indicates retirement path and migration away from beta SDK usage for model inference; MAI route specifics are documented as REST endpoint behavior.
   * Evidence: https://learn.microsoft.com/azure/foundry/foundry-models/concepts/endpoints

2. Alternative: Use OpenAI-compatible SDK route for MAI-Image-2.
   * Rejected for this sample because MAI-Image-2 documentation presently prescribes MAI endpoint path and payload, not an explicitly documented C# OpenAI route for MAI image generation.
   * Evidence: https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai

3. Alternative: Use API key auth in sample.
   * Rejected because request explicitly requires DefaultAzureCredential and Azure CLI sign-in local flow.

## Selected Approach Summary

Use a minimal .NET 10 Blazor Web App sample that performs MAI-Image-2 image generation via direct MAI REST endpoint call, authenticated with DefaultAzureCredential bearer tokens.

This is the lowest-risk and most evidence-aligned approach for current MAI documentation while keeping the sample simple and implementation-ready.
