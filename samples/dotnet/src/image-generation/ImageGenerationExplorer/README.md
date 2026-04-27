---
title: Image Generation Explorer
description: A Blazor Server app for side-by-side comparison of image generation across multiple Microsoft Foundry model deployments.
author: PlagueHO
ms.date: 2026-04-27
ms.topic: tutorial
keywords:
  - image generation
  - blazor
  - microsoft foundry
  - mai image
  - azure openai
estimated_reading_time: 3
---

## Overview

Image Generation Explorer is a .NET 10 Blazor Server application that lets you compare image generation results from multiple Microsoft Foundry model deployments side by side. Enter a prompt, select which models to use, and see the results laid out in a table with timing and resolution metadata.

Features:

* Side-by-side comparison across any number of configured models
* Per-model endpoint configuration supporting both MAI and Azure OpenAI API types
* Selectable width and height per model per run
* 10 built-in sample prompts for quick testing
* Dark and light theme toggle

## Prerequisites

* [.NET 10 SDK](https://dotnet.microsoft.com/download)
* A Microsoft Foundry resource with one or more image generation model deployments
* **Azure AI User** role (or equivalent inference permissions) on the resource
* [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) installed and signed in

```bash
az login
```

## Configuration

Each model requires its own endpoint URL. Edit `appsettings.json` in this project folder, or set environment variables before running.

```json
{
  "ImageGenerationExplorer": {
    "ApiKey": "",
    "Models": [
      {
        "DeploymentName": "mai-image-2-1",
        "DisplayName": "MAI Image 2",
        "ApiType": "Mai",
        "Endpoint": "https://<resource>.services.ai.azure.com",
        "DefaultWidth": 1024,
        "DefaultHeight": 1024,
        "MaxWidth": 2048,
        "MaxHeight": 2048,
        "Enabled": true
      },
      {
        "DeploymentName": "gpt-image-1",
        "DisplayName": "GPT Image",
        "ApiType": "OpenAi",
        "Endpoint": "https://<resource>.openai.azure.com",
        "DefaultWidth": 1024,
        "DefaultHeight": 1024,
        "MaxWidth": 1792,
        "MaxHeight": 1792,
        "Enabled": true
      }
    ]
  }
}
```

Leave `ApiKey` empty to use `DefaultAzureCredential` (recommended). Set it only when using an API key directly.

Endpoint format by API type:

* **MAI**: `https://<resource>.services.ai.azure.com`
* **OpenAI**: `https://<resource>.openai.azure.com`

## Run

From the `samples/dotnet` directory:

```bash
dotnet run --project src/image-generation/ImageGenerationExplorer
```

Open the URL shown in the terminal output. The app is available at `https://localhost:7201` by default.

> [!NOTE]
> If you run both this app and the `image-gen-explorer` sample at the same time, they use different ports (5134/7201 vs 5133/7200) so there is no conflict.
