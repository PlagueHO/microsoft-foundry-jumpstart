<#
.SYNOPSIS
    Queries the Microsoft Container Registry for the latest versions of AVM
    modules referenced in a Bicep file.

.DESCRIPTION
    Scans a Bicep file for Azure Verified Module (AVM) references matching
    br/public:avm/{type}/{service}/{resource}:{version}, queries
    mcr.microsoft.com for available tags, and outputs a comparison table.

.PARAMETER BicepFile
    Path to the Bicep file to scan for AVM module references.

.EXAMPLE
    .\Get-AvmLatestVersions.ps1 -BicepFile "infra/main.bicep"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateScript({ Test-Path $_ -PathType Leaf })]
    [string]$BicepFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Compare-SemanticVersion {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Version1,

        [Parameter(Mandatory)]
        [string]$Version2
    )

    $parts1 = $Version1.Split('.')
    $parts2 = $Version2.Split('.')

    for ($i = 0; $i -lt [Math]::Max($parts1.Length, $parts2.Length); $i++) {
        $v1 = if ($i -lt $parts1.Length) { [int]$parts1[$i] } else { 0 }
        $v2 = if ($i -lt $parts2.Length) { [int]$parts2[$i] } else { 0 }

        if ($v1 -lt $v2) { return -1 }
        if ($v1 -gt $v2) { return 1 }
    }

    return 0
}

function Get-LatestStableTag {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Tags
    )

    $stableTags = $Tags | Where-Object { $_ -notmatch '-' }

    $sorted = $stableTags | Sort-Object {
        $parts = $_.Split('.')
        $major = if ($parts.Length -ge 1) { [int]$parts[0] } else { 0 }
        $minor = if ($parts.Length -ge 2) { [int]$parts[1] } else { 0 }
        $patch = if ($parts.Length -ge 3) { [int]$parts[2] } else { 0 }
        $major * 1000000 + $minor * 1000 + $patch
    } -Descending

    return $sorted | Select-Object -First 1
}

# Read the Bicep file
$content = Get-Content -Path $BicepFile -Raw

# Extract AVM module references
$pattern = "br/public:(avm/(?:res|ptn|utl)/[^:]+):(\d+\.\d+(?:\.\d+)?)"
$matches = [regex]::Matches($content, $pattern)

if ($matches.Count -eq 0) {
    Write-Host "No AVM module references found in: $BicepFile"
    exit 0
}

# Deduplicate modules
$modules = @{}
foreach ($match in $matches) {
    $modulePath = $match.Groups[1].Value
    $currentVersion = $match.Groups[2].Value

    if (-not $modules.ContainsKey($modulePath)) {
        $modules[$modulePath] = $currentVersion
    }
}

Write-Host ""
Write-Host "AVM Module Version Check: $BicepFile"
Write-Host ("=" * 80)
Write-Host ""

$results = @()

foreach ($entry in $modules.GetEnumerator() | Sort-Object Name) {
    $modulePath = $entry.Key
    $currentVersion = $entry.Value
    $mcrPath = "bicep/$modulePath"
    $tagsUrl = "https://mcr.microsoft.com/v2/$mcrPath/tags/list"

    try {
        $response = Invoke-RestMethod -Uri $tagsUrl -TimeoutSec 15
        $latestVersion = Get-LatestStableTag -Tags $response.tags

        if (-not $latestVersion) {
            $results += [PSCustomObject]@{
                Module  = $modulePath
                Current = $currentVersion
                Latest  = "N/A"
                Status  = "FAILED"
                Icon    = [char]0x274C  # ❌
            }
            continue
        }

        $comparison = Compare-SemanticVersion -Version1 $currentVersion -Version2 $latestVersion
        $currentParts = $currentVersion.Split('.')
        $latestParts = $latestVersion.Split('.')

        if ($comparison -eq 0) {
            $status = "CURRENT"
            $icon = [char]0x2705  # ✅
        }
        elseif ($currentParts[0] -ne $latestParts[0]) {
            $status = "MAJOR"
            $icon = [char]0x26A0  # ⚠️
        }
        elseif ($currentParts.Length -ge 2 -and $latestParts.Length -ge 2 -and
                $currentParts[1] -ne $latestParts[1]) {
            $status = "MINOR"
            $icon = [char]0x1F504  # 🔄
        }
        else {
            $status = "PATCH"
            $icon = [char]0x1F504  # 🔄
        }

        $results += [PSCustomObject]@{
            Module  = $modulePath
            Current = $currentVersion
            Latest  = $latestVersion
            Status  = $status
            Icon    = $icon
        }
    }
    catch {
        $results += [PSCustomObject]@{
            Module  = $modulePath
            Current = $currentVersion
            Latest  = "ERROR"
            Status  = "FAILED"
            Icon    = [char]0x274C  # ❌
        }
        Write-Warning "Failed to query MCR for $modulePath : $($_.Exception.Message)"
    }
}

# Output table
$headerFormat = "{0,-55} {1,-10} {2,-10} {3,-8} {4}"
$rowFormat = "{0,-55} {1,-10} {2,-10} {3,-8} {4}"

Write-Host ($headerFormat -f "Module", "Current", "Latest", "Status", "Icon")
Write-Host ("-" * 95)

foreach ($result in $results) {
    Write-Host ($rowFormat -f $result.Module, $result.Current, $result.Latest, $result.Status, $result.Icon)
}

Write-Host ""

$updateCount = @($results | Where-Object { $_.Status -in @('MINOR', 'PATCH', 'MAJOR') }).Count
$currentCount = @($results | Where-Object { $_.Status -eq 'CURRENT' }).Count
$failedCount = @($results | Where-Object { $_.Status -eq 'FAILED' }).Count

Write-Host "Summary: $($results.Count) modules checked, $updateCount updates available, $currentCount current, $failedCount failed"
Write-Host ""

# Output results as JSON for machine consumption
$results | ConvertTo-Json -Depth 3
