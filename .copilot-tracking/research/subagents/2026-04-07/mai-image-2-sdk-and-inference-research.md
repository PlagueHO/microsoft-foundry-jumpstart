---
title: MAI-Image-2 .NET SDK and Inference Research
description: Evidence-backed research on MAI-Image-2 text-to-image inference from .NET for Microsoft Foundry Models Direct
author: GitHub Copilot
ms.date: 2026-04-07
ms.topic: reference
keywords:
  - microsoft foundry
  - models direct
  - mai-image-2
  - dotnet
  - azure ai openai
estimated_reading_time: 8
---

## Research Scope

* Determine which .NET SDKs can call MAI-Image-2 for text-to-image inference.
* Identify current recommended SDK path for Foundry Models Direct.
* Capture exact endpoint, auth, and API version requirements.
* Capture minimal request and response shape for image generation.
* Capture caveats, preview constraints, and repository usage patterns.

## Questions

1. What .NET SDKs can call MAI-Image-2 (Azure.AI.Inference, Azure.AI.OpenAI, REST only)?
2. Which SDK is currently recommended for Models Direct in Foundry, and why?
3. What are the exact auth and endpoint requirements, including API versions?
4. What is the minimal request and response pattern for image generation?
5. What caveats or preview constraints apply?

## Repository Findings

* Existing .NET samples in this repo predominantly use Azure.AI.OpenAI package references (for example, multiple projects under samples/dotnet/src/agent-framework/* reference Azure.AI.OpenAI 2.7.0-beta.2).
* Foundry agent-oriented samples also use Azure.AI.Projects for agent APIs, which is distinct from model direct inference routes.
* No existing repo sample currently shows MAI-Image-2 invocation or direct calls to /mai/v1/images/generations from C#.

Representative paths observed:

* samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step01_Simple/AzureArchitect_Step01_Simple.csproj
* samples/dotnet/src/agent-framework/AzureArchitect/AzureArchitect_Step06_UsingImages/AzureArchitect_Step06_UsingImages.csproj
* architectures/pattern-cross-region-webapp/app/CrossRegionAgent.csproj

Implication for SDK choice:

* Repo conventions already favor Azure SDKs and DefaultAzureCredential patterns, so a direct REST call wrapped in a small typed C# client is compatible with current style if no first-class MAI SDK surface exists.

## External Documentation Findings

### 1) .NET SDK options for MAI-Image-2

* MAI-Image-2 documentation currently presents only Python and raw REST for image generation against the MAI endpoint, not a C# SDK sample or MAI-specific .NET client.
  * Evidence: MAI article tabs and examples show Python and REST usage for `POST https://<resource-name>.services.ai.azure.com/mai/v1/images/generations`.
* Azure.AI.OpenAI is documented for Azure OpenAI image models (`gpt-image-*`) through `/openai/deployments/{deployment-id}/images/generations` and does not document MAI route usage.
* Azure.AI.Inference (beta) is deprecated/retiring, and Microsoft guidance is to migrate to OpenAI/v1 + stable OpenAI SDK for supported OpenAI/v1 scenarios.

Conclusion:

* For MAI-Image-2 specifically: official docs currently support REST against `/mai/v1/images/generations`.
* For general Foundry model direct inference using OpenAI-compatible routes: use OpenAI/v1 with OpenAI SDK / Azure.AI.OpenAI guidance per endpoint docs.

### 2) Recommended/preferred SDK for Models Direct now

* For Foundry Models generally, Microsoft explicitly recommends moving away from Azure AI Inference beta SDK and using OpenAI/v1 with stable OpenAI SDKs.
  * Rationale in docs: broader compatibility, newest features, simplified unified patterns, and less API-version churn.
* For MAI-Image-2 specifically, current MAI how-to is a dedicated MAI API path (`/mai/v1/...`) and currently documented via REST examples only.

Working recommendation split:

* Models Direct (OpenAI-compatible endpoints): OpenAI/v1 + OpenAI SDK (preferred).
* MAI-Image-2 text-to-image: direct REST to MAI endpoint until/if official C# MAI SDK surface is documented.

### 3) Auth and endpoint requirements

* MAI-Image-2 endpoint shape:
  * `https://<resource-name>.services.ai.azure.com/mai/v1/images/generations`
* MAI auth options:
  * API key header: `api-key`
  * Entra bearer token: `Authorization: Bearer <token>`
  * Token scope for MAI examples: `https://cognitiveservices.azure.com/.default`
* MAI request uses deployment name in payload field `model` (the deployment name you assigned).
* MAI route versioning is path-based (`/mai/v1/...`), not a query `api-version` parameter in documented examples.

Contrast with OpenAI inference endpoint:

* OpenAI data-plane endpoint uses `/openai/deployments/{deployment-id}/...` with `api-version=2024-10-21` in GA reference (or `/openai/v1/` style for OpenAI SDK usage per migration guidance).

Project endpoint vs resource/model endpoint:

* MAI docs instruct using the Foundry resource endpoint from Keys and Endpoint (`<resource>.services.ai.azure.com`), then MAI path.
* This differs from Foundry agent project endpoints (`.../api/projects/...`) used by Azure.AI.Projects scenarios.

### 4) Minimal request/response pattern for MAI image generation

Minimal request body fields:

* `model`: deployment name
* `prompt`: text prompt
* `width`: integer >= 768
* `height`: integer >= 768

Minimal response pattern:

* JSON with `data` array
* First item contains `b64_json` containing base64-encoded PNG bytes
* Decode `b64_json` to bytes and write image file (for UI, convert to data URL or raw bytes stream)

Output form:

* MAI doc states output is always PNG.
* Example pipeline decodes base64 into `output.png`.

### 5) Caveats and preview constraints

* MAI-Image-2 is explicitly in Preview.
* Regional/deployment constraints listed for Global Standard only (West Central US, East US, West US, West Europe, Sweden Central, South India).
* Hard image constraints:
  * `width >= 768`
  * `height >= 768`
  * `width * height <= 1,048,576`
* Output is one PNG image.
* Rate limits (RPM tiers) are documented for MAI-Image-2 Global Standard.
* Responsible AI and content-safety constraints apply; harmful prompts can be blocked.

## Answers Mapped To Questions

1. .NET SDKs for MAI-Image-2:

* Officially documented for MAI today: REST (Python + REST examples).
* Azure.AI.OpenAI is documented for OpenAI image endpoints, not MAI route.
* Azure.AI.Inference is deprecated and retiring, not recommended for new work.

1. Recommended SDK/path:

* For Models Direct generally: OpenAI/v1 + stable OpenAI SDK (per migration and endpoint docs).
* For MAI-Image-2 specifically: use MAI REST endpoint now, because MAI docs currently expose REST usage and MAI route.

1. Auth/endpoint/API requirements:

* MAI: `https://<resource>.services.ai.azure.com/mai/v1/images/generations`; API key or Entra token (`https://cognitiveservices.azure.com/.default` in MAI examples).
* OpenAI image endpoint (different API family): `https://{endpoint}/openai/deployments/{deployment-id}/images/generations?api-version=2024-10-21`.

1. Minimal request/response:

* Request: `{ model, prompt, width, height }`.
* Response: `data[0].b64_json` (base64 image bytes), decode to PNG.

1. Caveats/preview:

* Preview status, region/deployment constraints, strict width/height/total-pixel constraints, RPM limits, and responsible AI filters.

## Open Clarifications

* There is no explicit Microsoft Learn C# SDK sample for MAI `/mai/v1/images/generations` at time of this research; if one exists outside Learn pages returned, it was not surfaced.
* MAI endpoint docs do not currently publish a dedicated formal Swagger reference URL analogous to OpenAI reference pages in the materials retrieved.

## Sources

* <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai>
* <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai#overview-of-image-generation-with-mai-image-2>
* <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai#generate-images>
* <https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai#api-quotas-and-limits>
* <https://learn.microsoft.com/azure/foundry/foundry-models/concepts/endpoints>
* <https://learn.microsoft.com/azure/foundry/how-to/model-inference-to-openai-migration>
* <https://learn.microsoft.com/azure/foundry/openai/reference#image-generation>
* <https://learn.microsoft.com/azure/foundry/openai/how-to/dall-e>
* <https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure#microsoft-models-sold-directly-by-azure>
