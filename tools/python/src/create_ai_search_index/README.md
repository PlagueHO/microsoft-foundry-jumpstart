# Azure AI Search – Index Pipeline Builder (Package-level Guide)

This tool provides a simple way to add an index to an Azure AI Search account. It does this by:

1. Creating/updating the structure of the index
1. Adding a data source connection to an Azure Storage Account blob container that contains the documents
1. Creating an indexer using the data source with a skillsset to chunk and embed the documents using an Azure OpenAI model embedding model
1. Triggering the indexer to populate the index

## 1. Quick Start (One-liner)

```bash
python -m create_ai_search_index \
  --storage-account contosodata \
  --storage-container sales-docs \
  --search-service contoso-search \
  --index-name sales-rag-idx
```

The command above:

1. Authenticates to Azure using environment variables / Managed Identity.  
1. Generates a default **pipeline** (data source ⇒ skillset ⇒ indexer ⇒ index).  
1. Triggers the indexer to start processing documents in the blob container.

---

## 2. Prerequisites

- Python ≥ 3.10  
- An Azure subscription with:
  - Storage account + container (source docs)  
  - Azure AI Search service (vector-enabled tier)  
  - Azure OpenAI deployment for embeddings  
- Either an Entra ID (Managed Identity) **or** service principal creds

```dotenv
# .env (example)
AZURE_STORAGE_ACCOUNT   = "contosodata"
AZURE_STORAGE_SAS_TOKEN = "?sv=2024-01-01&..."
AZURE_SEARCH_ENDPOINT   = "https://contoso-search.search.windows.net"
AZURE_OPENAI_ENDPOINT   = "https://contoso-openai.openai.azure.com"
AZURE_OPENAI_EMBED_MODEL= "text-embedding-3-small"
# Optional; omit to use Managed Identity
# AZURE_OPENAI_API_KEY  = "<key>"
# AZURE_SEARCH_API_KEY  = "<key>"
```

Install dependencies from the repo root:

```bash
pip install -e ".[dev]"
```

---

## 3. Global CLI Flags

| Flag                                | Required | Description                                                     | Default |
|-------------------------------------|----------|-----------------------------------------------------------------|---------|
| `--storage-account`                 | Y        | Name of the Azure Storage account                               |         |
| `--storage-container`               | Y        | Name of the blob container holding source docs                  |         |
| `--search-service`                  | Y        | Name of the Azure AI Search service                             |         |
| `--index-name`                      | Y        | Name of the search index to create / overwrite                  |         |
| `--embedding-model`                 |          | Azure OpenAI deployment used for embeddings                     | `.env`  |
| `--chunk-size`                      |          | Max characters per content chunk                                | `2000`  |
| `--chunk-overlap`                   |          | Overlap between successive chunks                               | `200`   |
| `--file-types`                      |          | Comma-sep list (pdf,docx,md,txt,…)                              | `*`     |
| `--vector-dim`                      |          | Embedding dimension (auto from model when omitted)              |         |
| `--batch-size`                      |          | Docs processed per indexer batch                                | `200`   |
| `--rate-limit-per-minute`           |          | Throttle embedding calls                                        | `60`    |
| `--delete-existing`                 |          | Drop existing index + pipeline before creation (`true/false`)   | `false` |

---

## 4. Advanced Index Options

| Flag                      | Description                                                                    |
|---------------------------|--------------------------------------------------------------------------------|
| `--search-sku`            | SKU for new Search service if auto-provisioning (e.g., `standard`, `standardv2`)|
| `--index-vector-config`   | JSON string overriding the default vector configuration                        |
| `--semantic-config`       | JSON string defining semantic ranking settings                                 |
| `--fields`                | JSON file defining custom index fields; omit to auto-generate                  |

Example:

```bash
python -m create_ai_search_index \
  --storage-account contosodata \
  --storage-container knowledge-base \
  --search-service contoso-search \
  --index-name kb-idx \
  --embedding-model text-embedding-ada-002 \
  --chunk-size 1500 \
  --chunk-overlap 100 \
  --file-types pdf,md \
  --delete-existing true
```

---

## 5. How It Works

1. **Data Source** – Registers the blob container as a data source, using either SAS or Managed Identity.
1. **Skillset** – Adds chunking + embedding skills (powered by Azure OpenAI) and optional custom skills.
1. **Indexer** – Streams documents, applies the skillset, and sends results to the target index.
1. **Index** – Vector-enabled index with metadata fields + vector column for chybrid (keyword + vector) search.

All resources follow Azure Verified Modules (AVM) guidance and can be deployed stand-alone or embedded into a larger Bicep template.

---

## 6. Pipeline Lifecycle

| Command                                  | Behaviour                                              |
|------------------------------------------|--------------------------------------------------------|
| `python -m create_ai_search_index ...`   | Create / update pipeline and start indexing            |
| `--delete-existing true`                 | Tear down and fully regenerate pipeline + index        |
| `--dry-run`                              | Print REST payloads without hitting the API            |
| `--watch`                                | Stream indexer execution status until completion       |

---

## 7. Extending

1. Implement a new `DocumentLoader` in `src/create_ai_search_index/loaders/` for bespoke file formats.
1. Add custom skills by subclassing `Skill` in `src/create_ai_search_index/skills/`.
1. Update `PipelineBuilder` to register additional resources.
1. Documentation should be automatically surfaced in this README when you add new CLI arguments to `cli.py`.

For the architectural blueprint, see [`docs/INDEXER_DESIGN.md`](../../docs/INDEXER_DESIGN.md).
