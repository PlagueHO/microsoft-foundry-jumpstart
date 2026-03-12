<#
.SYNOPSIS
    Scaffolds a new Agent Skill directory with a template SKILL.md.

.DESCRIPTION
    Creates a new Agent Skill directory structure conforming to the
    agentskills.io specification (https://agentskills.io/specification).
    Generates the directory tree and a template SKILL.md with pre-populated
    YAML frontmatter.

.PARAMETER Name
    The skill name. Must be 1-64 characters, lowercase letters, digits,
    and hyphens only. Must not start/end with a hyphen or contain
    consecutive hyphens. The directory will be named to match.

.PARAMETER Description
    The skill description (1-1024 characters). Should explain what the
    skill does and when to use it.

.PARAMETER OutputPath
    The parent directory where the skill folder will be created.
    Defaults to the current directory.

.PARAMETER Author
    Optional author name for the metadata field.

.PARAMETER Version
    Optional version string for the metadata field. Defaults to "1.0".

.PARAMETER License
    Optional license identifier (e.g., "MIT", "Apache-2.0").

.PARAMETER Compatibility
    Optional compatibility string (1-500 chars) for environment
    requirements.

.PARAMETER IncludeScripts
    Creates a scripts/ subdirectory with placeholder files.

.PARAMETER IncludeReferences
    Creates a references/ subdirectory with a placeholder REFERENCE.md.

.PARAMETER IncludeAssets
    Creates an assets/ subdirectory.

.EXAMPLE
    .\New-AgentSkill.ps1 -Name "pdf-processing" -Description "Extract and merge PDFs." -OutputPath ".github/skills"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Name,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Description,

    [Parameter()]
    [string]$OutputPath = '.',

    [Parameter()]
    [string]$Author = '',

    [Parameter()]
    [string]$Version = '1.0',

    [Parameter()]
    [string]$License = '',

    [Parameter()]
    [string]$Compatibility = '',

    [Parameter()]
    [switch]$IncludeScripts,

    [Parameter()]
    [switch]$IncludeReferences,

    [Parameter()]
    [switch]$IncludeAssets
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

#region Validation

# Name: 1-64 chars, lowercase a-z, digits 0-9, hyphens only
if ($Name.Length -gt 64) {
    Write-Error "Name must be 1-64 characters. Got $($Name.Length)."
    return
}

if ($Name -notmatch '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$') {
    Write-Error "Name must contain only lowercase letters, digits, and hyphens. Must not start/end with a hyphen."
    return
}

if ($Name -match '--') {
    Write-Error "Name must not contain consecutive hyphens ('--')."
    return
}

# Description: 1-1024 chars
if ($Description.Length -gt 1024) {
    Write-Error "Description must be 1-1024 characters. Got $($Description.Length)."
    return
}

# Compatibility: 1-500 chars if provided
if ($Compatibility -and $Compatibility.Length -gt 500) {
    Write-Error "Compatibility must be 1-500 characters. Got $($Compatibility.Length)."
    return
}

#endregion

#region Create directory structure

$skillDir = Join-Path -Path $OutputPath -ChildPath $Name

if (Test-Path -Path $skillDir) {
    Write-Error "Directory '$skillDir' already exists. Remove it first or choose a different name."
    return
}

Write-Host "Creating skill directory: $skillDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $skillDir -Force | Out-Null

if ($IncludeScripts) {
    $scriptsDir = Join-Path -Path $skillDir -ChildPath 'scripts'
    New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    Write-Host "  Created: scripts/" -ForegroundColor DarkGray
}

if ($IncludeReferences) {
    $refsDir = Join-Path -Path $skillDir -ChildPath 'references'
    New-Item -ItemType Directory -Path $refsDir -Force | Out-Null

    $refContent = @"
# Reference

Detailed reference documentation for the **$Name** skill.

## Overview

<!-- Add detailed documentation here. -->
"@
    Set-Content -Path (Join-Path -Path $refsDir -ChildPath 'REFERENCE.md') -Value $refContent -Encoding utf8NoBOM
    Write-Host "  Created: references/REFERENCE.md" -ForegroundColor DarkGray
}

if ($IncludeAssets) {
    $assetsDir = Join-Path -Path $skillDir -ChildPath 'assets'
    New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
    Write-Host "  Created: assets/" -ForegroundColor DarkGray
}

#endregion

#region Generate SKILL.md

$frontmatter = [System.Text.StringBuilder]::new()
[void]$frontmatter.AppendLine('---')
[void]$frontmatter.AppendLine("name: $Name")
[void]$frontmatter.AppendLine('')

# Description — use block scalar for long descriptions
if ($Description.Length -gt 80) {
    [void]$frontmatter.AppendLine('description: >-')
    # Word-wrap at ~78 chars with 2-space indent
    $words = $Description -split '\s+'
    $line = '  '
    foreach ($word in $words) {
        if (($line.Length + $word.Length + 1) -gt 80 -and $line.Trim().Length -gt 0) {
            [void]$frontmatter.AppendLine($line.TrimEnd())
            $line = "  $word"
        } else {
            if ($line.Trim().Length -eq 0) {
                $line = "  $word"
            } else {
                $line += " $word"
            }
        }
    }
    if ($line.Trim().Length -gt 0) {
        [void]$frontmatter.AppendLine($line.TrimEnd())
    }
} else {
    [void]$frontmatter.AppendLine("description: `"$($Description -replace '"', '\"')`"")
}

if ($License) {
    [void]$frontmatter.AppendLine('')
    [void]$frontmatter.AppendLine("license: $License")
}

if ($Compatibility) {
    [void]$frontmatter.AppendLine('')
    [void]$frontmatter.AppendLine("compatibility: $Compatibility")
}

if ($Author -or $Version) {
    [void]$frontmatter.AppendLine('')
    [void]$frontmatter.AppendLine('metadata:')
    if ($Author) {
        [void]$frontmatter.AppendLine("  author: $Author")
    }
    if ($Version) {
        [void]$frontmatter.AppendLine("  version: `"$Version`"")
    }
}

[void]$frontmatter.AppendLine('---')

# Build body
$title = ($Name -replace '-', ' ') -replace '(^| )(.)', { $_.Value.ToUpper() }

$body = @"

# $title

<!-- One-paragraph description of what this skill does, why it matters, and
     the expected outcome. -->

## Prerequisites

<!-- List any tools, runtimes, or access requirements. Remove if none. -->

## Process

### Step 1 — <Title>

<!-- Describe the first step. Use imperative form. -->

### Step 2 — <Title>

<!-- Describe the next step. -->

## Examples

<!-- Provide input/output examples where applicable. -->

**Example 1:**

Input: <description>
Output: <description>

## Edge Cases

<!-- Document edge cases and how to handle them. -->

- <Edge case description and resolution>

## Validation

<!-- How to verify the skill produced a correct result. -->

1. <Verification step>
"@

$skillContent = $frontmatter.ToString() + $body
$skillPath = Join-Path -Path $skillDir -ChildPath 'SKILL.md'
Set-Content -Path $skillPath -Value $skillContent -Encoding utf8NoBOM

Write-Host "  Created: SKILL.md" -ForegroundColor DarkGray

#endregion

#region Summary

Write-Host ''
Write-Host "Skill '$Name' scaffolded successfully." -ForegroundColor Green
Write-Host ''
Write-Host 'Directory structure:' -ForegroundColor Cyan

$allItems = Get-ChildItem -Path $skillDir -Recurse
$tree = @("$Name/")
foreach ($item in $allItems) {
    $relative = $item.FullName.Substring($skillDir.Length + 1) -replace '\\', '/'
    $depth = ($relative -split '/').Count - 1
    $indent = '    ' * $depth
    $display = Split-Path -Leaf $item.FullName
    if ($item.PSIsContainer) {
        $display += '/'
    }
    $tree += "${indent}├── $display"
}
$tree | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }

Write-Host ''
Write-Host 'Next steps:' -ForegroundColor Yellow
Write-Host '  1. Edit SKILL.md to add your skill instructions' -ForegroundColor DarkGray
Write-Host '  2. Add any scripts, references, or asset files' -ForegroundColor DarkGray
Write-Host '  3. Validate with: npx skills-ref validate' $skillDir -ForegroundColor DarkGray

#endregion
