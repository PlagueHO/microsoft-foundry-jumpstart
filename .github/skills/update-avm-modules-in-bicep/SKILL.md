---
name: update-avm-modules-in-bicep
description: Update Azure Verified Modules (AVM) to latest versions in Bicep files. Use when asked to update, upgrade, or check AVM module versions in Bicep infrastructure files.
compatibility: Designed for GitHub Copilot in VS Code. Requires Azure CLI with Bicep extension and internet access to query MCR.
metadata:
  author: microsoft-foundry-jumpstart
  version: "1.0"
  reference: https://github.com/Azure/bicep-registry-modules/
---

# Update Azure Verified Modules in Bicep Files

This skill guides you through updating Azure Verified Module (AVM) references to their latest versions in Bicep files.

## Process

1. **Scan**: Use `read_file` or `grep_search` to extract all AVM module references and their current versions from the target Bicep file(s). Look for patterns like `br/public:avm/res/{service}/{resource}:{version}`.

2. **Check Latest Versions**: Use `fetch_webpage` to query the Microsoft Container Registry (MCR):
   - API endpoint: `https://mcr.microsoft.com/v2/bicep/avm/res/{service}/{resource}/tags/list`
   - Parse the JSON response and extract the `tags` array
   - Sort tags by semantic versioning to identify the latest stable version

3. **Compare Versions**: For each module, compare the current version with the latest available version using semantic version parsing.

4. **Review Breaking Changes**: For modules with major or significant version changes, use `fetch_webpage` to review the documentation:
   - Documentation URL: `https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/{service}/{resource}`
   - Check the CHANGELOG.md or release notes for breaking changes

5. **Apply Updates**: Use `replace_string_in_file` to update the version numbers in the Bicep file while maintaining file validity.

6. **Validate**: Use `run_in_terminal` to run Bicep linting:
   ```bash
   az bicep build --file <file-path>
   ```

## Breaking Change Policy

⚠️ **PAUSE for user approval** if updates involve:
- Major version changes (e.g., 0.x.x → 1.x.x or 1.x.x → 2.x.x)
- Incompatible parameter changes or removals
- Security or compliance modifications
- Significant behavioral changes

## Output Format

Display results in a table with status icons:

| Module | Current | Latest | Status | Action | Docs |
|--------|---------|--------|--------|--------|------|
| avm/res/compute/virtual-machine | 0.1.0 | 0.2.0 | 🔄 | Updated | [📖](link) |
| avm/res/storage/storage-account | 0.3.0 | 0.3.0 | ✅ | Current | [📖](link) |
| avm/res/network/virtual-network | 0.5.0 | 1.0.0 | ⚠️ | Review | [📖](link) |

## Status Icons

- 🔄 Updated - Module was updated to latest version
- ✅ Current - Module is already at latest version
- ⚠️ Manual review required - Breaking changes detected, needs user approval
- ❌ Failed - Unable to check or update module

## Module Path Pattern

AVM modules follow this pattern in Bicep files:
```bicep
module exampleModule 'br/public:avm/res/{service}/{resource}:{version}' = {
  name: 'deployment-name'
  params: { /* parameters */ }
}
```

Common examples:
- `br/public:avm/res/storage/storage-account:0.14.3`
- `br/public:avm/res/search/search-service:0.11.1`
- `br/public:avm/res/key-vault/vault:0.11.0`
- `br/public:avm/res/operational-insights/workspace:0.9.1`

## Requirements

- Use the MCR tags API only for version discovery (no external package managers)
- Parse JSON tags array and sort by semantic versioning rules
- Maintain Bicep file validity and linting compliance after updates
- Preserve all existing module parameters and configurations
- Do not modify module names or deployment names unless necessary for compatibility

## Example Workflow

1. User asks: "Update AVM modules in infra/main.bicep"
2. Use `grep_search` to scan file for `br/public:avm/res/` patterns
3. For each module found:
   - Use `fetch_webpage` to call MCR API to get available tags
   - Compare versions
   - Report status
4. Present summary table to user
5. If no breaking changes, use `replace_string_in_file` to apply updates
6. If breaking changes exist, wait for user approval
7. Use `run_in_terminal` to validate with `az bicep build`
