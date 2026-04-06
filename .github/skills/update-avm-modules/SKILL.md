---
name: update-avm-modules

description: >-
  **WORKFLOW SKILL** — Update Azure Verified Modules (AVM) to their latest
  versions in Bicep files. Scans for AVM module references, queries the
  Microsoft Container Registry (MCR) for latest versions, compares using
  semantic versioning, reviews breaking changes, and applies updates with
  validation. WHEN: 'update AVM', 'update Bicep modules', 'latest AVM versions',
  'update Azure Verified Modules', 'upgrade Bicep dependencies', 'check AVM
  versions', 'update module versions'. INVOKES: run_in_terminal for MCR API
  queries and bicep lint. FOR SINGLE OPERATIONS: Use az bicep build to validate
  individual files.

metadata:
  author: plagueho.os
  version: "1.0"
  reference: https://github.com/Azure/bicep-registry-modules

compatibility:
  - GitHub Copilot
  - VS Code
  - Requires az CLI with Bicep extension
  - Requires network access to mcr.microsoft.com

argument-hint: >-
  Specify the Bicep file(s) to update (e.g., "infra/main.bicep") or say
  "all Bicep files" to scan the entire infra/ directory.

user-invocable: true
---

# Update AVM Modules

Update Azure Verified Modules (AVM) in Bicep files to their latest published
versions. The workflow scans Bicep files for module references, queries the
Microsoft Container Registry (MCR) for available versions, identifies updates,
reviews breaking changes, applies updates, and validates the result.

## Prerequisites

- **Azure CLI** with Bicep extension (`az bicep build` must work).
- **Network access** to `mcr.microsoft.com` for version queries.
- **PowerShell 7+** (Windows) or **curl + jq** (macOS/Linux) for the version
  check scripts.

## Process

### Step 1 — Identify Target Files

Determine which Bicep files to update:

- If the user specified a file, use that file.
- If the user said "all", scan `infra/` recursively for `*.bicep` files.
- List the files and confirm with the user before proceeding.

### Step 2 — Extract Module References

For each target file, extract all AVM module references matching the pattern:

```text
br/public:avm/res/{service}/{resource}:{version}
br/public:avm/ptn/{pattern}:{version}
br/public:avm/utl/{utility}:{version}
```

Build a list of `{ module, currentVersion, filePath, lineNumber }` entries.
If no AVM modules are found, inform the user and stop.

### Step 3 — Query Latest Versions

Use the version check script to query MCR for the latest version of each
unique module. The scripts are in this skill's `scripts/` directory.

**PowerShell** (Windows):

```powershell
& "<skill-path>/scripts/Get-AvmLatestVersions.ps1" -BicepFile "<path>"
```

**Shell** (macOS/Linux):

```bash
"<skill-path>/scripts/get-avm-latest-versions.sh" "<path>"
```

The scripts output a table with columns: `Module`, `Current`, `Latest`, `Status`.

If the scripts are unavailable, query the MCR API directly:

```text
GET https://mcr.microsoft.com/v2/bicep/{module}/tags/list
```

Parse the `tags` array and sort by semantic versioning to find the latest
stable release (exclude pre-release tags containing `-`).

### Step 4 — Compare and Classify

For each module, classify the update:

| Status | Condition | Icon |
|--------|-----------|------|
| Current | `current == latest` | ✅ |
| Patch update | Major and minor match, patch differs | 🔄 |
| Minor update | Major matches, minor differs | 🔄 |
| Major update | Major version differs | ⚠️ |
| Failed | MCR query failed | ❌ |

### Step 5 — Review Breaking Changes

For any **major** or **minor** version updates:

1. Fetch the module changelog/README from GitHub:
   `https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/{service}/{resource}`
2. Check for incompatible parameter changes, removed parameters, renamed
   parameters, or behavioral changes.
3. If breaking changes are detected, **PAUSE and present them to the user**
   before applying. Ask for explicit approval.

**Breaking Change Policy** — always pause for approval when updates involve:

- Incompatible parameter changes (renamed, removed, type changed)
- Security or compliance modifications
- Behavioral changes that affect deployment outcomes

### Step 6 — Apply Updates

For approved updates, edit each Bicep file to replace the old version with
the new version in the module reference:

```bicep
// Before
module storageAccount 'br/public:avm/res/storage/storage-account:0.9.0' = {

// After
module storageAccount 'br/public:avm/res/storage/storage-account:0.14.0' = {
```

If breaking changes require parameter adjustments, apply those as well.

### Step 7 — Validate

Run Bicep linting to ensure all updated files are valid:

```powershell
az bicep build --file <updated-file>
```

If validation fails:

1. Report the specific error.
2. Attempt to fix parameter issues caused by the version change.
3. Re-validate.
4. If still failing, revert that module to its previous version and mark it
   as ⚠️ in the results.

### Step 8 — Present Results

Display a summary table:

| Module | Current | Latest | Status | Action | Docs |
|--------|---------|--------|--------|--------|------|
| `avm/res/storage/storage-account` | 0.9.0 | 0.14.0 | 🔄 | Updated | [📖](https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/storage/storage-account) |
| `avm/res/search/search-service` | 0.11.1 | 0.11.1 | ✅ | Current | [📖](https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/search/search-service) |
| `avm/res/network/virtual-network` | 0.5.0 | 0.8.0 | ⚠️ | Manual review | [📖](https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/network/virtual-network) |

**Status Icons:**

- ✅ Current — already on latest version
- 🔄 Updated — successfully updated
- ⚠️ Manual review required — breaking changes need attention
- ❌ Failed — update could not be applied or validated

After the table, list any files that were modified and remind the user to
run `az bicep build --file infra/main.bicep` for a final end-to-end validation.

## MCR API Reference

### Tags List Endpoint

```text
GET https://mcr.microsoft.com/v2/bicep/avm/res/{service}/{resource}/tags/list
```

Returns JSON:

```json
{
  "name": "bicep/avm/res/storage/storage-account",
  "tags": ["0.6.0", "0.7.0", "0.8.0", "0.9.0", "0.14.0"]
}
```

### Module Path Mapping

| Bicep Reference | MCR Path |
|----------------|----------|
| `br/public:avm/res/storage/storage-account:0.14.0` | `bicep/avm/res/storage/storage-account` |
| `br/public:avm/ptn/ai-platform/baseline:0.1.0` | `bicep/avm/ptn/ai-platform/baseline` |

### GitHub Documentation

```text
https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/{service}/{resource}
```

## Edge Cases

- **Custom/local modules** (not `br/public:avm/`): Skip — only update AVM
  registry modules.
- **Pre-release tags**: Exclude tags containing `-` (e.g., `0.5.0-preview`).
- **Network errors**: If MCR is unreachable, report the error and skip that
  module rather than failing the entire run.
- **Multiple files referencing same module at different versions**: Update all
  to the same latest version for consistency.
