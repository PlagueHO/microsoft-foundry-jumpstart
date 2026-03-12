---
name: azure-github-managed-identity

description: "**WORKFLOW SKILL** — Provision Azure User Assigned Managed Identities with OIDC federation and RBAC for passwordless GitHub authentication. WHEN: \"set up Azure access for GitHub Actions\", \"configure managed identity for GitHub\", \"enable passwordless Azure authentication in CI/CD\", \"configure OIDC federation GitHub Azure\", \"Copilot coding agent Azure identity\". INVOKES: run_in_terminal for PowerShell. FOR SINGLE OPERATIONS: Use az CLI for simple role assignments."

metadata:
  author: PlagueHO
  version: "1.0"
  reference: https://github.com/PlagueHO/plagueho.os/

compatibility: Requires PowerShell 7+, Az.Accounts ≥ 5.3.2, Az.Resources ≥ 9.0.0, Az.ManagedServiceIdentity ≥ 2.0.0, and an authenticated Azure session (Connect-AzAccount) with permission to create resources and assign RBAC roles at subscription scope.

argument-hint: Provide the target GitHub repository name (e.g. `my-repo`) and optionally the GitHub organization, Azure subscription ID, Azure location, environment names, and whether to provision a Copilot coding agent identity.

user-invocable: true
---

## Overview

This skill provisions the Azure infrastructure required for a GitHub repository to authenticate
to Azure using OpenID Connect (OIDC) — no long-lived credentials required. It creates:

- A dedicated **resource group** (`rg-github-<repo>-mi`) to hold all GitHub integration resources
- One **User Assigned Managed Identity** per GitHub environment (e.g. `test`, `staging`, `prod`)
- An optional **User Assigned Managed Identity** for the GitHub Copilot coding agent (`mi-copilot-coding-agent`)
- **Federated Identity Credentials** on each identity, bound to the matching GitHub environment via OIDC
- **RBAC role assignments** on the subscription for each identity:
  - `Contributor` — allows the identity to create and manage Azure resources
  - `User Access Administrator` (with conditions) — allows the identity to assign roles, but prevents it from granting `Owner`, `User Access Administrator`, or `Role Based Access Control Administrator` to any principal

## Prerequisites

Before running this skill, ensure the following are met:

1. **Azure PowerShell modules** are installed (the script will validate this):
   - `Az.Accounts` ≥ 5.3.2
   - `Az.Resources` ≥ 9.0.0
   - `Az.ManagedServiceIdentity` ≥ 2.0.0

   Install missing modules with:

   ```powershell
   Install-Module -Name Az.Accounts, Az.Resources, Az.ManagedServiceIdentity -Scope CurrentUser -Force
   ```

2. **Authenticated Azure session** — run `Connect-AzAccount` if not already authenticated.

3. The authenticated identity must have **subscription-level permissions** to:
   - Create resource groups
   - Create managed identities in `Microsoft.ManagedIdentity`
   - Assign RBAC roles (`Microsoft.Authorization/roleAssignments/write`)

## Script

The PowerShell script is located alongside this file at:
`./Update-AzureUserAssignedManagedIdentityForGitHub.ps1`

## How to use this skill

### Step 1 — Gather required information

Ask the user for the following, or infer from context where possible:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `RepositoryName` | Yes | — | The GitHub repository name (not the full `org/repo` path) |
| `GitHubOrganization` | No | `PlagueHO` | The GitHub organization or user account that owns the repo |
| `SubscriptionId` | No | Current context | The Azure subscription ID to deploy resources into |
| `Location` | No | `New Zealand North` | Azure region for the resource group and identities |
| `Environment` | No | `@('test')` | One or more GitHub environment names to set up GitHub Actions identities for |
| `IncludeCopilot` | No | `$true` | Whether to also create a managed identity for the Copilot coding agent |
| `Force` | No | `$false` | Skip interactive confirmation prompts |

### Step 2 — Run the script

Use `run_in_terminal` to execute the script from the repository root in a PowerShell session that is already authenticated to Azure.

**Minimal invocation (uses all defaults):**

```powershell
.\.github\skills\azure-github-managed-identity\Update-AzureUserAssignedManagedIdentityForGitHub.ps1 `
    -RepositoryName 'my-repo'
```

**Full invocation with all parameters:**

```powershell
.\.github\skills\azure-github-managed-identity\Update-AzureUserAssignedManagedIdentityForGitHub.ps1 `
    -RepositoryName 'my-repo' `
    -GitHubOrganization 'MyOrg' `
    -SubscriptionId '12345678-1234-1234-1234-123456789012' `
    -Location 'East US' `
    -Environment @('test', 'staging', 'prod') `
    -IncludeCopilot:$true `
    -Force
```

**With `-WhatIf` to preview changes without making them:**

```powershell
.\.github\skills\azure-github-managed-identity\Update-AzureUserAssignedManagedIdentityForGitHub.ps1 `
    -RepositoryName 'my-repo' `
    -WhatIf
```

### Step 3 — Configure GitHub repository secrets and environments

After the script completes, it will print the values needed for GitHub. Configure the following in the repository settings (`Settings → Secrets and variables → Actions`):

**Repository-level secrets (shared across all environments):**

| Secret | Value |
|--------|-------|
| `AZURE_TENANT_ID` | The Azure AD tenant ID (printed by the script) |
| `AZURE_SUBSCRIPTION_ID` | The Azure subscription ID (printed by the script) |

**Per-environment secrets** (set under `Settings → Environments → <env name> → Secrets`):

| Secret | Value |
|--------|-------|
| `AZURE_CLIENT_ID` | The `clientId` of the managed identity for that environment (printed by the script) |

For the Copilot coding agent environment (`copilot`), set `AZURE_CLIENT_ID` under the `copilot` environment in GitHub repository settings.

### Step 4 — Use the managed identity in GitHub Actions

Add the following to any GitHub Actions workflow YAML that needs Azure access:

```yaml
permissions:
  id-token: write   # Required for OIDC token request
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: test   # Must match the environment name used when creating the identity
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

For Copilot coding agent workflows, use `environment: copilot`.

## Resource naming conventions

The script uses the following naming pattern for created resources:

| Resource | Name pattern |
|----------|-------------|
| Resource group | `rg-github-<RepositoryName>-mi` |
| GitHub Actions identity | `mi-github-actions-<environment>-environment` |
| Copilot coding agent identity | `mi-copilot-coding-agent` |
| Federated credential | `<GitHubOrganization>-<RepositoryName>-<environment>-env` |

## Idempotency

The script is **idempotent** — running it multiple times against the same repository is safe. It will skip creation of any resource that already exists and only create what is missing.

## Edge cases and when to pause

- **`RepositoryName` not provided** — this is the only mandatory parameter. If the user has not supplied it, ask before running the script.
- **Multiple environments requested** — confirm the list of environment names with the user before proceeding, as each environment creates a separate managed identity and role assignments.
- **Non-default `SubscriptionId`** — if the user provides a subscription ID that differs from the current Azure context, confirm which subscription to use before running.
- **`-Force` flag** — do not pass `-Force` unless the user explicitly requests skipping confirmation prompts; without it the script will prompt for each resource before creating it.
- **Role assignment failures** — the script retries up to 3 times. If all retries fail (e.g. due to insufficient permissions), stop, surface the error to the user, and ask them to verify their Azure permissions before retrying.

## Security notes

- No static credentials (client secrets) are created. All authentication uses short-lived OIDC tokens issued by GitHub at runtime.
- The `User Access Administrator` role is granted with a condition expression that prevents the managed identity from assigning `Owner`, `User Access Administrator`, or `Role Based Access Control Administrator` roles to any principal, following the principle of least privilege.
- Output from the script may contain tenant and subscription IDs. These are non-secret identifiers but should not be committed to public repositories — use GitHub secrets for storage.
