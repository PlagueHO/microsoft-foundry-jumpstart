# Blazor Auth Config Research (2026-04-07)

## Research Scope

- Minimal .NET 10 Blazor app patterns for calling Azure Foundry model inference using DefaultAzureCredential with local Azure CLI authentication.
- Focus areas:
  1. Endpoint + deployment/model configuration best practices in appsettings/environment variables.
  2. DefaultAzureCredential instantiation pattern for local Azure CLI and Azure managed identity.
  3. RBAC permissions required for model inference via Foundry project endpoint.
  4. Minimal Blazor UI/service async pattern for inference and image/error rendering.
- Also inspect repository conventions in samples/dotnet for configuration, DI, and README style.

## Findings In Progress

## Findings

### 1) Best practice for endpoint + deployment/model configuration in sample apps

Findings:

- For Foundry SDK usage, Microsoft guidance is to use a single project endpoint:
  - `https://<resource-name>.services.ai.azure.com/api/projects/<project-name>`
  - Source: <https://learn.microsoft.com/azure/foundry/how-to/develop/sdk-overview#foundry-sdk>
- For model calls, deployment name (not catalog model ID) should be passed in API calls.
  - Source: <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/generate-responses>
- For OpenAI-compatible calls against a Foundry project endpoint, append `/openai/v1` to the project endpoint.
  - Source: <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/generate-responses>

Repository conventions observed:

- Existing samples commonly use environment variables for endpoint + deployment names and fail fast if missing.
  - samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step01_UnpublishedAgent/Program.cs:40
  - samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step01_UnpublishedAgent/Program.cs:42
- Existing sample also demonstrates appsettings + env var fallback pattern:
  - appsettings + env vars loaded in host configuration:
    - samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:90
    - samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:91
    - samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:92
  - configuration fallback to env vars:
    - samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:108
    - samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:110
- Existing env var names are not fully standardized across samples (`AZURE_OPENAI_*`, `AZURE_FOUNDRY_PROJECT_*`, and `MICROSOFT_FOUNDRY_PROJECT_*` all exist), so a new sample should clearly document one canonical set and optionally support aliases.
  - samples/dotnet/src/agent-framework/AzureArchitect/README.md:20
  - samples/dotnet/src/agent-framework/AzureArchitect/README.md:21

Recommended minimal config pattern for a Blazor sample:

- `Foundry:ProjectEndpoint` + env fallback `AZURE_AI_PROJECT_ENDPOINT` (or project-standard alias).
- `Foundry:ModelDeploymentName` + env fallback `AZURE_AI_MODEL_DEPLOYMENT_NAME`.
- Store defaults/shape in appsettings and override with env vars in local/dev/prod.

### 2) DefaultAzureCredential pattern for local Azure CLI + managed identity in Azure

Findings:

- `DefaultAzureCredential` includes `AzureCliCredential` in its chain and also includes `ManagedIdentityCredential` by default.
  - Source: <https://learn.microsoft.com/dotnet/azure/sdk/authentication/credential-chains#defaultazurecredential-overview>
- Chain order places managed identity before developer-tool credentials, and Azure CLI is in the default dev tool segment.
  - Source: <https://learn.microsoft.com/dotnet/azure/sdk/authentication/credential-chains#defaultazurecredential-overview>
- Microsoft explicitly states this enables local `az login` development and managed identity in Azure without code changes.
  - Source: <https://learn.microsoft.com/dotnet/ai/azure-ai-services-authentication#authentication-using-microsoft-entra-id>
  - Source: <https://learn.microsoft.com/azure/developer/intro/passwordless-overview#introducing-defaultazurecredential>
- For ASP.NET Core apps, Microsoft guidance is to configure shared credentials in DI (`UseCredential`) for Azure clients.
  - Source: <https://learn.microsoft.com/dotnet/azure/sdk/aspnetcore-guidance#authenticate-using-microsoft-entra-id>

Implications for requested behavior:

- To prioritize/allow Azure CLI locally while still supporting managed identity in Azure:
  - Minimal: use plain `new DefaultAzureCredential()` and rely on environment.
  - Deterministic local-dev-only chain: customize `DefaultAzureCredentialOptions` exclusions or use `ChainedTokenCredential` for dev; leave MI enabled for deployed environments.
  - `AZURE_TOKEN_CREDENTIALS` can force dev/prod category or a specific credential in Azure.Identity 1.15+.
  - Source: <https://learn.microsoft.com/dotnet/azure/sdk/authentication/credential-chains#defaultazurecredential-overview>

Repository conventions observed:

- At least one local sample hard-codes `AzureCliCredential` (not DAC) for local scenarios:
  - samples/dotnet/src/agent-framework/DocumentClassifierWorkflow/Program.cs:190
- Another sample uses DAC for Azure OpenAI chat completion fallback:
  - samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs:125

### 3) RBAC permissions required for model inference through Foundry project endpoint

Findings:

- Foundry RBAC distinguishes management permissions from development data actions.
- For least-privilege model invocation/build scenarios, Microsoft documentation positions **Azure AI User** as the minimum role with project data actions.
  - Source: <https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry>
- Foundry get-started and SDK overview docs reinforce **Azure AI User** as least-privilege development role.
  - Source: <https://learn.microsoft.com/azure/foundry/how-to/develop/sdk-overview>
  - Source: <https://learn.microsoft.com/azure/ai-services/multi-service-resource#grant-or-obtain-developer-permissions>
- If calling Azure OpenAI endpoints directly (non-project route), relevant role can be **Cognitive Services OpenAI User**.
  - Source: <https://learn.microsoft.com/dotnet/ai/azure-ai-services-authentication#authentication-using-microsoft-entra-id>

Practical RBAC conclusion for this research scope:

- For inference through Foundry **project endpoint**, assign **Azure AI User** to:
  - the developer/user principal (local `az login` path), and
  - the app's managed identity in Azure hosting environments.

### 4) Minimal Blazor UI/service pattern to call async inference and render generated image or error

Findings:

- Blazor guidance recommends API calls through service abstractions and DI (especially for prerendered/interactive modes), with async lifecycle methods and explicit error handling.
  - Source: <https://learn.microsoft.com/aspnet/core/blazor/call-web-api?view=aspnetcore-10.0#service-abstractions-for-web-api-calls>
  - Source: <https://learn.microsoft.com/aspnet/core/blazor/call-web-api?view=aspnetcore-10.0#named-%60httpclient%60-with-%60ihttpclientfactory%60>
- For image generation in Foundry/OpenAI APIs, payloads return base64 image output (`b64_json`), which can be rendered by converting to a data URL in UI.
  - Source: <https://learn.microsoft.com/azure/foundry/openai/how-to/dall-e#call-the-image-generation-api>
- Responses API docs confirm project endpoint + `/openai/v1` usage and deployment-name targeting for requests.
  - Source: <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/generate-responses>

Recommended minimal Blazor architecture:

- `Program.cs`:
  - bind `FoundryOptions` from appsettings + env vars
  - register credential/service singleton/scoped
- Service layer (`IFoundryInferenceService`):
  - builds client with `DefaultAzureCredential`
  - performs async call
  - maps output to either `GeneratedImageBase64` (or text) or typed error result
- Razor component:
  - fields: prompt, `isLoading`, `errorMessage`, `imageDataUrl`
  - `async` submit handler with try/catch
  - render states: loading spinner/text, `<img src="data:image/png;base64,...">`, friendly error panel

## Repository convention inspection summary (samples/dotnet)

- Configuration:
  - appsettings + environment variable layering is used in some samples.
  - Environment variables are strongly emphasized in README setup sections.
- DI:
  - Console samples use `Host.CreateDefaultBuilder` for configuration/logging; not all samples use rich DI yet.
  - For Blazor sample addition, follow ASP.NET Core DI patterns from Microsoft docs and align naming with current sample env-var conventions.
- README style:
  - Sectioned, task-oriented structure with prerequisites/configuration/run/troubleshooting.
  - Evidence:
    - samples/dotnet/README.md:16
    - samples/dotnet/README.md:22
    - samples/dotnet/README.md:38
    - samples/dotnet/src/semantic-kernel/home-loan-agent/README.md:28
    - samples/dotnet/src/semantic-kernel/home-loan-agent/README.md:30
    - samples/dotnet/src/semantic-kernel/home-loan-agent/README.md:43

## Confidence and caveats

- Confidence: High for credential-chain behavior, endpoint format, and RBAC least-privilege role recommendation.
- Caveat: Foundry docs currently show both project endpoint and resource endpoint scenarios. Keep sample focused on project endpoint to match requested scope.
- Caveat: SDK/package landscape is evolving (Foundry + OpenAI routes); pin package versions in sample docs.

## Sources

- Microsoft Foundry SDK overview: <https://learn.microsoft.com/azure/foundry/how-to/develop/sdk-overview>
- Foundry model Responses API guide: <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/generate-responses>
- Endpoints for Foundry models: <https://learn.microsoft.com/azure/foundry/foundry-models/concepts/endpoints>
- Credential chains in Azure Identity (.NET): <https://learn.microsoft.com/dotnet/azure/sdk/authentication/credential-chains>
- Azure SDK in ASP.NET Core guidance: <https://learn.microsoft.com/dotnet/azure/sdk/aspnetcore-guidance>
- Authentication in .NET + Azure AI services: <https://learn.microsoft.com/dotnet/ai/azure-ai-services-authentication>
- Passwordless and DefaultAzureCredential overview: <https://learn.microsoft.com/azure/developer/intro/passwordless-overview>
- Foundry RBAC concepts: <https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry>
- Foundry quickstart permission guidance: <https://learn.microsoft.com/azure/ai-services/multi-service-resource#grant-or-obtain-developer-permissions>
- Blazor web API calling guidance (.NET 10): <https://learn.microsoft.com/aspnet/core/blazor/call-web-api?view=aspnetcore-10.0>
- Azure OpenAI image generation output (`b64_json`): <https://learn.microsoft.com/azure/foundry/openai/how-to/dall-e#call-the-image-generation-api>

- Workspace evidence:
  - samples/dotnet/README.md
  - samples/dotnet/src/semantic-kernel/home-loan-agent/Program.cs
  - samples/dotnet/src/semantic-kernel/home-loan-agent/README.md
  - samples/dotnet/src/semantic-kernel/home-loan-agent/appsettings.json
  - samples/dotnet/src/agent-framework/DocumentClassifierWorkflow/Program.cs
  - samples/dotnet/src/agent-framework/AgentPersistence/AgentPersistence_Step01_UnpublishedAgent/Program.cs
  - samples/dotnet/src/agent-framework/AzureArchitect/README.md

## Open Questions

- Should the future sample standardize on `AZURE_AI_PROJECT_ENDPOINT`/`AZURE_AI_MODEL_DEPLOYMENT_NAME` even if existing repo samples also use `AZURE_FOUNDRY_*` and `MICROSOFT_FOUNDRY_*` variants?
- Should we target Foundry SDK (`Azure.AI.Projects` + project OpenAI client) or direct OpenAI SDK against `projectEndpoint + /openai/v1` for the minimal Blazor example?
- Do you want text-only responses, image generation, or both in the first minimal Blazor sample?
