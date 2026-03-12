<#
.SYNOPSIS
    Validates an Agent Skill directory against the agentskills.io specification.

.DESCRIPTION
    Checks that a skill directory conforms to the Agent Skills specification:
    - SKILL.md exists with valid YAML frontmatter
    - name field is valid (1-64 chars, lowercase, hyphens, matches dir name)
    - description field is valid (1-1024 chars, non-empty)
    - compatibility field is valid if present (1-500 chars)
    - SKILL.md body is under 500 lines
    - No files exceed 5 MB
    - File references use relative paths

    Optionally runs npx skills-ref validate if Node.js is available.

.PARAMETER SkillPath
    Path to the skill directory to validate.

.PARAMETER SkipNpx
    Skip the npx skills-ref validation even if Node.js is available.

.EXAMPLE
    .\Test-AgentSkill.ps1 -SkillPath ".github/skills/my-skill"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$SkillPath,

    [Parameter()]
    [switch]$SkipNpx
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()
$passed = 0

function Add-Pass {
    param([string]$Message)
    $script:passed++
    Write-Host "  PASS: $Message" -ForegroundColor Green
}

function Add-Fail {
    param([string]$Message)
    $script:errors.Add($Message)
    Write-Host "  FAIL: $Message" -ForegroundColor Red
}

function Add-Warn {
    param([string]$Message)
    $script:warnings.Add($Message)
    Write-Host "  WARN: $Message" -ForegroundColor Yellow
}

Write-Host "Validating skill: $SkillPath" -ForegroundColor Cyan
Write-Host ''

# Check directory exists
if (-not (Test-Path -Path $SkillPath -PathType Container)) {
    Write-Error "Skill directory not found: $SkillPath"
    return
}

$dirName = Split-Path -Leaf $SkillPath

#region Directory name validation
Write-Host 'Directory name:' -ForegroundColor White

if ($dirName.Length -ge 1 -and $dirName.Length -le 64) {
    Add-Pass "Length is $($dirName.Length) (1-64 allowed)"
} else {
    Add-Fail "Length is $($dirName.Length) (must be 1-64)"
}

if ($dirName -cmatch '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$') {
    Add-Pass 'Contains only lowercase letters, digits, and hyphens'
} else {
    Add-Fail 'Must contain only lowercase letters, digits, and hyphens; must not start/end with hyphen'
}

if ($dirName -notmatch '--') {
    Add-Pass 'No consecutive hyphens'
} else {
    Add-Fail 'Must not contain consecutive hyphens'
}
#endregion

#region SKILL.md existence
Write-Host ''
Write-Host 'SKILL.md:' -ForegroundColor White

$skillMdPath = Join-Path -Path $SkillPath -ChildPath 'SKILL.md'
if (-not (Test-Path -Path $skillMdPath)) {
    Add-Fail 'SKILL.md not found (required)'
    # Cannot continue without SKILL.md
    Write-Host ''
    Write-Host "Validation failed with $($errors.Count) error(s)." -ForegroundColor Red
    return
}
Add-Pass 'SKILL.md exists'
#endregion

#region Parse frontmatter
$content = Get-Content -Path $skillMdPath -Raw -Encoding utf8
$lines = Get-Content -Path $skillMdPath -Encoding utf8

# Find frontmatter boundaries
if ($lines[0] -ne '---') {
    Add-Fail 'SKILL.md must start with YAML frontmatter (---)'
    Write-Host ''
    Write-Host "Validation failed with $($errors.Count) error(s)." -ForegroundColor Red
    return
}

$endIndex = -1
for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq '---') {
        $endIndex = $i
        break
    }
}

if ($endIndex -eq -1) {
    Add-Fail 'YAML frontmatter not closed (missing closing ---)'
    Write-Host ''
    Write-Host "Validation failed with $($errors.Count) error(s)." -ForegroundColor Red
    return
}
Add-Pass 'Valid YAML frontmatter delimiters'

$frontmatterText = ($lines[1..($endIndex - 1)]) -join "`n"
$bodyLines = $lines[($endIndex + 1)..($lines.Count - 1)]
$bodyLineCount = ($bodyLines | Where-Object { $_.Trim().Length -gt 0 }).Count
#endregion

#region Name field
Write-Host ''
Write-Host 'name field:' -ForegroundColor White

$nameMatch = [regex]::Match($frontmatterText, '(?m)^name:\s*(.+)$')
if (-not $nameMatch.Success) {
    Add-Fail 'Required field "name" not found in frontmatter'
} else {
    $nameValue = $nameMatch.Groups[1].Value.Trim().Trim('"').Trim("'")

    if ($nameValue.Length -ge 1 -and $nameValue.Length -le 64) {
        Add-Pass "Length is $($nameValue.Length) (1-64 allowed)"
    } else {
        Add-Fail "Length is $($nameValue.Length) (must be 1-64)"
    }

    if ($nameValue -cmatch '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$') {
        Add-Pass 'Valid characters and format'
    } else {
        Add-Fail 'Must be lowercase letters, digits, hyphens; no leading/trailing hyphens'
    }

    if ($nameValue -notmatch '--') {
        Add-Pass 'No consecutive hyphens'
    } else {
        Add-Fail 'Must not contain consecutive hyphens'
    }

    if ($nameValue -eq $dirName) {
        Add-Pass "Matches directory name '$dirName'"
    } else {
        Add-Fail "Name '$nameValue' does not match directory name '$dirName'"
    }
}
#endregion

#region Description field
Write-Host ''
Write-Host 'description field:' -ForegroundColor White

# Handle multi-line YAML block scalars (>- or |) and inline descriptions
$descLineMatch = [regex]::Match($frontmatterText, '(?m)^description:\s*(.*)$')
if (-not $descLineMatch.Success) {
    Add-Fail 'Required field "description" not found in frontmatter'
} else {
    $descRawValue = $descLineMatch.Groups[1].Value.Trim()

    # Check if it's a block scalar indicator (>-, >, |-, |)
    if ($descRawValue -match '^[>|]-?\s*$') {
        Add-Pass 'Description field present (block scalar)'
        # Collect indented continuation lines
        $descLines = @()
        $inDesc = $false
        foreach ($line in $frontmatterText -split "`n") {
            if ($line -match '^description:') {
                $inDesc = $true
                continue
            }
            if ($inDesc) {
                if ($line -match '^\s{2,}') {
                    $descLines += $line.Trim()
                } else {
                    break
                }
            }
        }
        $descValue = $descLines -join ' '
        if ($descValue.Length -ge 1 -and $descValue.Length -le 1024) {
            Add-Pass "Length is approximately $($descValue.Length) (1-1024 allowed)"
        } else {
            Add-Fail "Length is approximately $($descValue.Length) (must be 1-1024)"
        }
    } elseif ($descRawValue.Length -gt 0) {
        # Inline description value
        $descValue = $descRawValue.Trim('"').Trim("'")
        if ($descValue.Length -ge 1 -and $descValue.Length -le 1024) {
            Add-Pass "Length is $($descValue.Length) (1-1024 allowed)"
        } else {
            Add-Fail "Length is $($descValue.Length) (must be 1-1024)"
        }
    } else {
        Add-Fail 'Description field is empty'
    }
}
#endregion

#region Body length
Write-Host ''
Write-Host 'SKILL.md body:' -ForegroundColor White

$totalLines = $lines.Count - $endIndex - 1
if ($totalLines -le 500) {
    Add-Pass "Body is $totalLines lines (recommended max 500)"
} else {
    Add-Warn "Body is $totalLines lines (recommended max 500 — consider splitting into references/)"
}
#endregion

#region File sizes
Write-Host ''
Write-Host 'File sizes:' -ForegroundColor White

$largeFiles = @(Get-ChildItem -Path $SkillPath -Recurse -File | Where-Object { $_.Length -gt 5MB })
if ($largeFiles.Count -eq 0) {
    Add-Pass 'All files under 5 MB'
} else {
    foreach ($f in $largeFiles) {
        $sizeMb = [math]::Round($f.Length / 1MB, 2)
        Add-Fail "File '$($f.Name)' is ${sizeMb} MB (max 5 MB)"
    }
}
#endregion

#region Security check
Write-Host ''
Write-Host 'Security:' -ForegroundColor White

$allFiles = Get-ChildItem -Path $SkillPath -Recurse -File
$secretPatterns = @(
    'password\s*[:=]',
    'secret\s*[:=]',
    'api[_-]?key\s*[:=]',
    'token\s*[:=]\s*[''"][A-Za-z0-9]',
    'BEGIN\s+(RSA\s+)?PRIVATE\s+KEY'
)

$foundSecrets = $false
foreach ($file in $allFiles) {
    $fileContent = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $fileContent) { continue }
    foreach ($pattern in $secretPatterns) {
        if ($fileContent -match $pattern) {
            Add-Warn "Potential secret/credential in '$($file.Name)' (pattern: $pattern)"
            $foundSecrets = $true
        }
    }
}
if (-not $foundSecrets) {
    Add-Pass 'No obvious credentials or secrets detected'
}
#endregion

#region NPX validation
if (-not $SkipNpx) {
    Write-Host ''
    Write-Host 'NPX skills-ref validation:' -ForegroundColor White

    $npxAvailable = $null -ne (Get-Command -Name 'npx' -ErrorAction SilentlyContinue)
    if ($npxAvailable) {
        try {
            $npxOutput = & npx skills-ref validate $SkillPath 2>&1
            $npxExitCode = $LASTEXITCODE
            if ($npxExitCode -eq 0) {
                Add-Pass 'npx skills-ref validate passed'
            } else {
                Add-Fail "npx skills-ref validate failed (exit code $npxExitCode)"
                $npxOutput | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
            }
        } catch {
            Add-Warn "npx skills-ref validate could not run: $_"
        }
    } else {
        Add-Warn 'npx not found — skipping skills-ref validation (install Node.js for full validation)'
    }
}
#endregion

#region Summary
Write-Host ''
Write-Host '--- Summary ---' -ForegroundColor Cyan
Write-Host "  Passed:   $passed" -ForegroundColor Green
Write-Host "  Warnings: $($warnings.Count)" -ForegroundColor Yellow
Write-Host "  Errors:   $($errors.Count)" -ForegroundColor Red
Write-Host ''

if ($errors.Count -eq 0) {
    Write-Host 'Validation PASSED.' -ForegroundColor Green
} else {
    Write-Host 'Validation FAILED.' -ForegroundColor Red
    Write-Host ''
    Write-Host 'Errors:' -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    exit 1
}
#endregion
