# MAI Image 2 Simple Blazor Sample

This sample is a minimal .NET 10 Blazor Web App that generates one image from a text prompt using a MAI-Image-2 deployment.

## Prerequisites

- .NET 10 SDK
- A Microsoft Foundry resource with a MAI-Image-2 deployment
- Access to that resource with the Azure AI User role (or equivalent model inference permissions)
- Azure CLI installed

Authenticate locally before running:

```bash
az login
```

## Configuration

Set Microsoft Foundry settings in appsettings or environment variables.

Required settings:

- MicrosoftFoundry__ResourceEndpoint
- MicrosoftFoundry__ImageDeployment

Optional settings:

- MicrosoftFoundry__DefaultWidth (default: 1024)
- MicrosoftFoundry__DefaultHeight (default: 1024)

Example environment variables:

```bash
setx MicrosoftFoundry__ResourceEndpoint "https://<your-resource>.services.ai.azure.com"
setx MicrosoftFoundry__ImageDeployment "mai-image-2"
setx MicrosoftFoundry__DefaultWidth "1024"
setx MicrosoftFoundry__DefaultHeight "1024"
```

Use the resource endpoint, not a project endpoint. The MAI image API route is called on the resource host.

## Run

From samples/dotnet:

```bash
dotnet run --project src/blazor/mai-image-2-simple
```

Open the app URL shown in the terminal, enter a prompt, and submit.
The page disables the button while a request is in flight and then shows either a generated image or an error message.
