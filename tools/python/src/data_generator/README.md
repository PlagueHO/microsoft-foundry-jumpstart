# Synthetic Data Generator (Package-level Guide)

This package provides the **engine, interfaces and scenario plug-ins** used by the Microsoft Foundry Jumpstart Solution Accelerator to create realistic yet *entirely fictional* datasets with Azure OpenAI + Semantic Kernel.

## 1. Quick Start (One-liner)

```bash
python -m data_generator --scenario tech-support --count 10 --out-dir ./data
```

The command above:

1. Loads environment variables / `.env` for Azure OpenAI connectivity.  
1. Instantiates the requested `DataGeneratorTool` (`tech-support`).  
1. Generates `10` records in parallel and writes them to `./data`  
   (`0001.json`, `0002.json`, …).

---

## 2. Prerequisites

- Python ≥ 3.10
- An Azure OpenAI resource (endpoint + deployment)  
- Either an API key **or** Managed Identity permission

```dotenv
# .env (example)
AZURE_OPENAI_ENDPOINT   = "https://<your>.openai.azure.com"
AZURE_OPENAI_DEPLOYMENT = "gpt-4-1"
# Optional; omit to use Managed Identity
# AZURE_OPENAI_API_KEY  = "<key>"
```

Install dependencies from the repo root:

```bash
pip install -e ".[dev]"
```

---

## 3. Global CLI Flags

| Flag                         | Required | Description                                               | Default  |
|------------------------------|----------|-----------------------------------------------------------|----------|
| `--scenario`                 | Y        | Which tool to run (`tech-support`, `retail-product`, ...) |          |
| `--count`                    |          | Number of records to create                               | `1`      |
| `--out-dir`                  |          | Output folder (auto-created)                              | `./data` |
| `--output-format`            |          | `json`, `yaml`, `txt`                                     | `json`   |
| `--azure-openai-endpoint`    |          | Override env var                                          |          |
| `--azure-openai-deployment`  |          | Override env var                                          |          |
| `--azure-openai-api-key`     |          | Bypass Managed Identity                                   |          |

---

## 4. Tool Reference

### 4.1 Tech-Support (`tech-support`)

Produces synthetic help-desk cases.

| Flag                         | Required | Description                        | Default  |
|------------------------------|----------|------------------------------------|----------|
| `-d`, `--system-description` | Y        | Short blurb of the affected system |          |

Example:

```bash
python -m data_generator \
  --scenario tech-support \
  --count 50 \
  --system-description "ContosoShop – React SPA + Azure SQL back-end" \
  --output-format yaml \
  --out-dir ./sample-data/tech-support
```

### 4.2 Retail-Product (`retail-product`)

Creates e-commerce catalogue entries.

| Flag               | Required | Description                                  | Default   |
|--------------------|----------|----------------------------------------------|-----------|
| `-i`, `--industry` | N        | Industry / theme (electronics, fashion, ...) | `general` |

Example:

```bash
python -m data_generator \
  --scenario retail-product \
  --count 100 \
  --industry electronics \
  --output-format json \
  --out-dir ./sample-data/retail-products
```

### 4.3 Healthcare-Record (`healthcare-record`)

Generate anonymized healthcare documents.

| Flag               | Required | Description                                                      | Default            |
|--------------------|----------|------------------------------------------------------------------|--------------------|
| `--document-type`  | N        | Type of medical document (e.g. Clinic Note, Discharge Summary)   | `Clinic Note`      |
| `--specialty`      | N        | Medical specialty (e.g. Cardiology, Oncology)                    | `General Medicine` |

Example:

```bash
python -m data_generator \
  --scenario healthcare-record \
  --count 10 \
  --document-type "Discharge Summary" \
  --specialty Cardiology \
  --output-format yaml \
  --out-dir ./sample-data/healthcare-records
```

### 4.4 Healthcare-Clinical-Policy (`healthcare-clinical-policy`)

Generate realistic clinical healthcare policy documents including care pathways, treatment protocols, and clinical guidelines.

| Flag               | Required | Description                                                                                                              | Default            |
|--------------------|----------|--------------------------------------------------------------------------------------------------------------------------|--------------------|
| `--specialty`      | N        | Clinical specialty for the policy (e.g. Cardiology, Emergency Medicine, Oncology, Pediatrics, Surgery, Internal Medicine) | `General Medicine` |
| `--policy-type`    | N        | Type of policy: clinical-pathway, treatment-protocol, diagnostic-guideline, medication-management, infection-control, patient-safety, quality-assurance | `clinical-pathway` |
| `--complexity`     | N        | Complexity level: simple, medium, complex                                                                                 | `medium`           |

Example:

```bash
python -m data_generator \
  --scenario healthcare-clinical-policy \
  --count 10 \
  --specialty Cardiology \
  --policy-type clinical-pathway \
  --complexity complex \
  --output-format yaml \
  --out-dir ./sample-data/healthcare-clinical-policies
```

```bash
python -m data_generator \
  --scenario healthcare-clinical-policy \
  --count 5 \
  --specialty "Emergency Medicine" \
  --policy-type treatment-protocol \
  --output-format json \
  --out-dir ./sample-data/healthcare-clinical-policies
```

### 4.5 Financial-Transaction (`financial-transaction`)

Generate synthetic bank-account statements with ≥50 transactions.

| Flag                  | Required | Description                                        | Default    |
|-----------------------|----------|----------------------------------------------------|------------|
| `-a, --account-type`  | N        | Account kind (checking, savings, credit)           | `checking` |
| `--transactions-max`  | N        | Max transactions per statement                     | `50`       |
| `--fraud-percent`     | N        | % chance to include a subtle fraudulent transaction| `0`        |

Example:

```bash
python -m data_generator \
  --scenario financial-transaction \
  --count 20 \
  --account-type savings \
  --transactions-max 100 \
  --fraud-percent 5 \
  --output-format yaml \
  --out-dir ./data/financial
```

### 4.6 Insurance-Claim (`insurance-claim`)

Generate synthetic insurance-claim documents.

| Flag                 | Required | Description                                   | Default |
|----------------------|----------|-----------------------------------------------|---------|
| `-p, --policy-type`  | N        | Policy type (auto, home, health)              | `auto`  |
| `--fraud-percent`    | N        | % chance the claim is fraudulent              | `0`     |

Example:

```bash
python -m data_generator \
  --scenario insurance-claim \
  --count 30 \
  --policy-type home \
  --fraud-percent 5 \
  --output-format yaml \
  --out-dir ./sample-data/insurance-claims
```

### 4.7 Legal-Contract (`legal-contract`)

Generates synthetic legal contracts, including NDAs, service agreements, and negotiation histories.

| Flag                  | Required | Description                                        | Default    |
|-----------------------|----------|----------------------------------------------------|------------|
| `--contract-type`     | N        | Type of contract (NDA, Service Agreement, ...)     | `NDA`      |
| `--num-clauses`      | N        | Number of clauses in the contract                  | `5`        |
| `--complexity`       | N        | Complexity of legal language (simple, complex)    | `simple`   |

Example:

```bash
data_generator generate --tool legal-contract --num-records 10 --contract-type NDA --num-clauses 7 --output-file nda_contracts.jsonl
data_generator generate --tool legal-contract --num-records 5 --contract-type "Service Agreement" --complexity complex --output-file service_agreements.jsonl
```

### 4.8 Tech-Support-SOP (`tech-support-sop`)

Generate synthetic standard operating procedure (SOP) documents for fixing common tech support problems.

| Flag                  | Required | Description                                                          | Default                           |
|-----------------------|----------|----------------------------------------------------------------------|-----------------------------------|
| `--problem-category`  | N        | Category of problem (general, network, application, authentication, hardware, database, cloud, security) | `general`                        |
| `--complexity`        | N        | Complexity level (simple, medium, complex)                           | `medium`                          |
| `--system-context`    | N        | System or environment context for the SOP                            | `Generic enterprise IT environment` |

Example:

```bash
python -m data_generator \
  --scenario tech-support-sop \
  --count 20 \
  --problem-category network \
  --system-context "Azure cloud environment" \
  --output-format yaml \
  --out-dir ./sample-data/tech-support-sops
```

---

## 5. Extending with New Scenarios

1. Add `<new>.py` under `src/data_generator/tools/`.
1. Subclass `DataGeneratorTool`, set unique `name` + `toolName`.
1. Implement `build_prompt`, `cli_arguments`, `validate_args`, etc.
1. No core changes required – the registry auto-discovers the new tool.

For full architectural details refer to [`docs/DESIGN.md`](../docs/DESIGN.md).

### 5.1 Using GitHub Copilot Prompt Files

You can use the GitHub Copilot prompt file [/.github/prompts/data_generator_create_tool.prompt.md](../../.github/prompts/data_generator_create_tool.prompt.md) to generate a new tool.

To use the prompt file, follow these steps:

1. In Visual Studio Code, open GitHub Copilot chat (CTRL+ALT+I).
1. Select `Edit Mode` in the chat.
1. Enter `/data_generator_create_tool: ToolPurpose: Insurance Claims`, changing the Insurance Claims to the purpose of your new tool.
1. Select the appropriate options when prompted.
1. Review and refine the generated code as necessary.
