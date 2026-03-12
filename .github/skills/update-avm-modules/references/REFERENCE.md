# AVM Version Management Reference

Detailed reference documentation for the **update-avm-modules** skill.

## Module Registry Endpoints

### Microsoft Container Registry (MCR)

- **Tags list**: `https://mcr.microsoft.com/v2/bicep/avm/res/{service}/{resource}/tags/list`
- **Pattern modules**: `https://mcr.microsoft.com/v2/bicep/avm/ptn/{pattern}/tags/list`
- **Utility modules**: `https://mcr.microsoft.com/v2/bicep/avm/utl/{utility}/tags/list`

### GitHub Source

- **Resource modules**: `https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/{service}/{resource}`
- **AVM index**: `https://azure.github.io/Azure-Verified-Modules/indexes/bicep/bicep-resource-modules/`
- **CSV index**: `https://raw.githubusercontent.com/Azure/Azure-Verified-Modules/refs/heads/main/docs/static/module-indexes/BicepResourceModules.csv`

## Bicep Module Reference Format

```text
br/public:avm/res/{service}/{resource}:{major}.{minor}.{patch}
```

Examples:

```bicep
module storageAccount 'br/public:avm/res/storage/storage-account:0.14.0' = { }
module virtualNetwork 'br/public:avm/res/network/virtual-network:0.7.2' = { }
module searchService 'br/public:avm/res/search/search-service:0.11.1' = { }
```

## Semantic Versioning Rules

AVM modules follow semantic versioning (`MAJOR.MINOR.PATCH`):

| Change | Meaning | Action |
|--------|---------|--------|
| **MAJOR** (e.g., 0.x → 1.x) | Breaking changes | Review changelog, test thoroughly |
| **MINOR** (e.g., 0.9 → 0.14) | New features, possible parameter changes | Review new parameters, test |
| **PATCH** (e.g., 0.9.0 → 0.9.1) | Bug fixes only | Safe to apply directly |

## Common Breaking Changes in AVM Updates

1. **Renamed parameters**: A parameter name changes (e.g., `sku` → `skuName`)
2. **Removed parameters**: A parameter is no longer accepted
3. **Type changes**: A parameter type changes (e.g., `string` → `object`)
4. **New required parameters**: A previously optional parameter becomes required
5. **Output changes**: Module output names or types change
6. **Default value changes**: Default behavior changes in security-relevant ways

## Validation Commands

```powershell
# Validate a single file
az bicep build --file infra/main.bicep

# Validate all Bicep files recursively
Get-ChildItem -Path ./infra -Filter '*.bicep' -Recurse | ForEach-Object {
    az bicep build --file $_.FullName
}
```
