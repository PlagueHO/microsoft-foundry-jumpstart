#!/usr/bin/env bash
# new-agent-skill.sh — Scaffold a new Agent Skill directory with a template SKILL.md.
#
# Creates a conformant skill directory per https://agentskills.io/specification
#
# Usage:
#   ./new-agent-skill.sh --name <skill-name> --description <description> \
#       [--output-path <dir>] [--author <author>] [--version <version>] \
#       [--license <license>] [--compatibility <compat>] \
#       [--include-scripts] [--include-references] [--include-assets]

set -euo pipefail

# Defaults
NAME=""
DESCRIPTION=""
OUTPUT_PATH="."
AUTHOR=""
VERSION="1.0"
LICENSE=""
COMPATIBILITY=""
INCLUDE_SCRIPTS=false
INCLUDE_REFERENCES=false
INCLUDE_ASSETS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --name)
            NAME="$2"; shift 2 ;;
        --description)
            DESCRIPTION="$2"; shift 2 ;;
        --output-path)
            OUTPUT_PATH="$2"; shift 2 ;;
        --author)
            AUTHOR="$2"; shift 2 ;;
        --version)
            VERSION="$2"; shift 2 ;;
        --license)
            LICENSE="$2"; shift 2 ;;
        --compatibility)
            COMPATIBILITY="$2"; shift 2 ;;
        --include-scripts)
            INCLUDE_SCRIPTS=true; shift ;;
        --include-references)
            INCLUDE_REFERENCES=true; shift ;;
        --include-assets)
            INCLUDE_ASSETS=true; shift ;;
        -h|--help)
            echo "Usage: $0 --name <name> --description <desc> [options]"
            echo ""
            echo "Options:"
            echo "  --name <name>            Skill name (required, 1-64 chars, lowercase+hyphens)"
            echo "  --description <desc>     Skill description (required, 1-1024 chars)"
            echo "  --output-path <dir>      Parent directory (default: current dir)"
            echo "  --author <author>        Author name for metadata"
            echo "  --version <version>      Version string (default: 1.0)"
            echo "  --license <license>      License identifier"
            echo "  --compatibility <compat> Compatibility string (1-500 chars)"
            echo "  --include-scripts        Create scripts/ subdirectory"
            echo "  --include-references     Create references/ subdirectory with REFERENCE.md"
            echo "  --include-assets         Create assets/ subdirectory"
            exit 0
            ;;
        *)
            echo "Error: Unknown argument '$1'" >&2
            exit 1
            ;;
    esac
done

# Validation
if [[ -z "$NAME" ]]; then
    echo "Error: --name is required." >&2
    exit 1
fi

if [[ -z "$DESCRIPTION" ]]; then
    echo "Error: --description is required." >&2
    exit 1
fi

name_len=${#NAME}
if [[ $name_len -gt 64 ]]; then
    echo "Error: Name must be 1-64 characters. Got ${name_len}." >&2
    exit 1
fi

if ! echo "$NAME" | grep -qE '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'; then
    echo "Error: Name must contain only lowercase letters, digits, and hyphens. Must not start/end with a hyphen." >&2
    exit 1
fi

if echo "$NAME" | grep -q -- '--'; then
    echo "Error: Name must not contain consecutive hyphens ('--')." >&2
    exit 1
fi

desc_len=${#DESCRIPTION}
if [[ $desc_len -gt 1024 ]]; then
    echo "Error: Description must be 1-1024 characters. Got ${desc_len}." >&2
    exit 1
fi

if [[ -n "$COMPATIBILITY" ]]; then
    compat_len=${#COMPATIBILITY}
    if [[ $compat_len -gt 500 ]]; then
        echo "Error: Compatibility must be 1-500 characters. Got ${compat_len}." >&2
        exit 1
    fi
fi

# Create directory structure
SKILL_DIR="${OUTPUT_PATH}/${NAME}"

if [[ -d "$SKILL_DIR" ]]; then
    echo "Error: Directory '${SKILL_DIR}' already exists. Remove it first or choose a different name." >&2
    exit 1
fi

echo "Creating skill directory: ${SKILL_DIR}"
mkdir -p "$SKILL_DIR"

if [[ "$INCLUDE_SCRIPTS" == true ]]; then
    mkdir -p "${SKILL_DIR}/scripts"
    echo "  Created: scripts/"
fi

if [[ "$INCLUDE_REFERENCES" == true ]]; then
    mkdir -p "${SKILL_DIR}/references"
    cat > "${SKILL_DIR}/references/REFERENCE.md" << 'REFEOF'
# Reference

Detailed reference documentation for this skill.

## Overview

<!-- Add detailed documentation here. -->
REFEOF
    echo "  Created: references/REFERENCE.md"
fi

if [[ "$INCLUDE_ASSETS" == true ]]; then
    mkdir -p "${SKILL_DIR}/assets"
    echo "  Created: assets/"
fi

# Generate SKILL.md
SKILL_FILE="${SKILL_DIR}/SKILL.md"

{
    echo "---"
    echo "name: ${NAME}"
    echo ""

    # Description
    if [[ $desc_len -gt 80 ]]; then
        echo "description: >-"
        # Word-wrap with 2-space indent
        echo "  ${DESCRIPTION}" | fold -s -w 78 | sed 's/^/  /' | sed '1s/^    //'
    else
        # Escape double quotes for YAML
        escaped_desc=$(echo "$DESCRIPTION" | sed 's/"/\\"/g')
        echo "description: \"${escaped_desc}\""
    fi

    if [[ -n "$LICENSE" ]]; then
        echo ""
        echo "license: ${LICENSE}"
    fi

    if [[ -n "$COMPATIBILITY" ]]; then
        echo ""
        echo "compatibility: ${COMPATIBILITY}"
    fi

    if [[ -n "$AUTHOR" || -n "$VERSION" ]]; then
        echo ""
        echo "metadata:"
        if [[ -n "$AUTHOR" ]]; then
            echo "  author: ${AUTHOR}"
        fi
        if [[ -n "$VERSION" ]]; then
            echo "  version: \"${VERSION}\""
        fi
    fi

    echo "---"

    # Generate title from name (capitalize words)
    title=$(echo "$NAME" | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')

    cat << BODYEOF

# ${title}

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
BODYEOF
} > "$SKILL_FILE"

echo "  Created: SKILL.md"

# Summary
echo ""
echo "Skill '${NAME}' scaffolded successfully."
echo ""
echo "Directory structure:"
find "$SKILL_DIR" -print | sort | while IFS= read -r path; do
    relative="${path#"${SKILL_DIR}"}"
    if [[ -z "$relative" ]]; then
        echo "  ${NAME}/"
    else
        depth=$(echo "$relative" | tr -cd '/' | wc -c)
        indent=""
        for ((i = 1; i < depth; i++)); do
            indent="${indent}    "
        done
        basename=$(basename "$path")
        if [[ -d "$path" ]]; then
            basename="${basename}/"
        fi
        echo "  ${indent}├── ${basename}"
    fi
done

echo ""
echo "Next steps:"
echo "  1. Edit SKILL.md to add your skill instructions"
echo "  2. Add any scripts, references, or asset files"
echo "  3. Validate with: npx skills-ref validate ${SKILL_DIR}"
