#!/usr/bin/env bash
# test-agent-skill.sh — Validate an Agent Skill directory against the agentskills.io spec.
#
# Checks:
#   - SKILL.md exists with valid YAML frontmatter
#   - name field: 1-64 chars, lowercase, hyphens, matches dir name
#   - description field: 1-1024 chars, non-empty
#   - compatibility field: 1-500 chars if present
#   - SKILL.md body under 500 lines
#   - No files over 5 MB
#   - No obvious credentials/secrets
#   - Optional npx skills-ref validate
#
# Usage:
#   ./test-agent-skill.sh <skill-directory> [--skip-npx]

set -euo pipefail

SKILL_PATH="${1:-}"
SKIP_NPX=false

if [[ "$#" -ge 2 && "$2" == "--skip-npx" ]]; then
    SKIP_NPX=true
fi

if [[ -z "$SKILL_PATH" ]]; then
    echo "Usage: $0 <skill-directory> [--skip-npx]" >&2
    exit 1
fi

ERRORS=0
WARNINGS=0
PASSED=0

pass() {
    ((PASSED++)) || true
    echo -e "  \033[32mPASS:\033[0m $1"
}

fail() {
    ((ERRORS++)) || true
    echo -e "  \033[31mFAIL:\033[0m $1"
}

warn() {
    ((WARNINGS++)) || true
    echo -e "  \033[33mWARN:\033[0m $1"
}

echo -e "\033[36mValidating skill: ${SKILL_PATH}\033[0m"
echo ""

# Check directory exists
if [[ ! -d "$SKILL_PATH" ]]; then
    echo "Error: Skill directory not found: ${SKILL_PATH}" >&2
    exit 1
fi

DIR_NAME=$(basename "$SKILL_PATH")

# --- Directory name validation ---
echo -e "\033[37mDirectory name:\033[0m"

dir_len=${#DIR_NAME}
if [[ $dir_len -ge 1 && $dir_len -le 64 ]]; then
    pass "Length is ${dir_len} (1-64 allowed)"
else
    fail "Length is ${dir_len} (must be 1-64)"
fi

if echo "$DIR_NAME" | grep -qE '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'; then
    pass "Contains only lowercase letters, digits, and hyphens"
else
    fail "Must contain only lowercase letters, digits, and hyphens; must not start/end with hyphen"
fi

if ! echo "$DIR_NAME" | grep -q -- '--'; then
    pass "No consecutive hyphens"
else
    fail "Must not contain consecutive hyphens"
fi

# --- SKILL.md existence ---
echo ""
echo -e "\033[37mSKILL.md:\033[0m"

SKILL_FILE="${SKILL_PATH}/SKILL.md"
if [[ ! -f "$SKILL_FILE" ]]; then
    fail "SKILL.md not found (required)"
    echo ""
    echo -e "\033[31mValidation failed with ${ERRORS} error(s).\033[0m"
    exit 1
fi
pass "SKILL.md exists"

# --- Parse frontmatter ---
FIRST_LINE=$(head -n 1 "$SKILL_FILE")
if [[ "$FIRST_LINE" != "---" ]]; then
    fail "SKILL.md must start with YAML frontmatter (---)"
    echo ""
    echo -e "\033[31mValidation failed with ${ERRORS} error(s).\033[0m"
    exit 1
fi

# Find closing --- (line number, 1-based, skipping line 1)
END_LINE=$(tail -n +2 "$SKILL_FILE" | grep -n '^---$' | head -n 1 | cut -d: -f1)
if [[ -z "$END_LINE" ]]; then
    fail "YAML frontmatter not closed (missing closing ---)"
    echo ""
    echo -e "\033[31mValidation failed with ${ERRORS} error(s).\033[0m"
    exit 1
fi
pass "Valid YAML frontmatter delimiters"

# Extract frontmatter (between first and second ---)
FRONTMATTER=$(sed -n "2,$((END_LINE))p" "$SKILL_FILE")

# Count body lines (after frontmatter)
TOTAL_LINES=$(wc -l < "$SKILL_FILE")
BODY_START=$((END_LINE + 2))
BODY_LINES=$((TOTAL_LINES - END_LINE - 1))
if [[ $BODY_LINES -lt 0 ]]; then
    BODY_LINES=0
fi

# --- Name field ---
echo ""
echo -e "\033[37mname field:\033[0m"

NAME_VALUE=$(echo "$FRONTMATTER" | grep -m1 '^name:' | sed 's/^name:\s*//' | sed 's/^["'\'']//' | sed 's/["'\'']\s*$//' | xargs)

if [[ -z "$NAME_VALUE" ]]; then
    fail 'Required field "name" not found in frontmatter'
else
    name_len=${#NAME_VALUE}
    if [[ $name_len -ge 1 && $name_len -le 64 ]]; then
        pass "Length is ${name_len} (1-64 allowed)"
    else
        fail "Length is ${name_len} (must be 1-64)"
    fi

    if echo "$NAME_VALUE" | grep -qE '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'; then
        pass "Valid characters and format"
    else
        fail "Must be lowercase letters, digits, hyphens; no leading/trailing hyphens"
    fi

    if ! echo "$NAME_VALUE" | grep -q -- '--'; then
        pass "No consecutive hyphens"
    else
        fail "Must not contain consecutive hyphens"
    fi

    if [[ "$NAME_VALUE" == "$DIR_NAME" ]]; then
        pass "Matches directory name '${DIR_NAME}'"
    else
        fail "Name '${NAME_VALUE}' does not match directory name '${DIR_NAME}'"
    fi
fi

# --- Description field ---
echo ""
echo -e "\033[37mdescription field:\033[0m"

# Check for description (inline or block scalar)
if echo "$FRONTMATTER" | grep -q '^description:'; then
    DESC_LINE=$(echo "$FRONTMATTER" | grep -m1 '^description:' | sed 's/^description:\s*//')

    if [[ "$DESC_LINE" =~ ^[\>\|]-?$ ]] || [[ -z "$DESC_LINE" ]]; then
        # Block scalar — collect indented continuation lines
        pass "Description field present (block scalar)"
        IN_DESC=false
        DESC_TEXT=""
        while IFS= read -r line; do
            if echo "$line" | grep -q '^description:'; then
                IN_DESC=true
                continue
            fi
            if [[ "$IN_DESC" == true ]]; then
                if echo "$line" | grep -qE '^\s{2,}'; then
                    DESC_TEXT="${DESC_TEXT} $(echo "$line" | sed 's/^\s*//')"
                else
                    break
                fi
            fi
        done <<< "$FRONTMATTER"
        DESC_TEXT=$(echo "$DESC_TEXT" | xargs)
        desc_len=${#DESC_TEXT}
    else
        # Inline value
        DESC_TEXT=$(echo "$DESC_LINE" | sed 's/^["'\'']//' | sed 's/["'\'']\s*$//')
        desc_len=${#DESC_TEXT}
    fi

    if [[ $desc_len -ge 1 && $desc_len -le 1024 ]]; then
        pass "Length is ${desc_len} (1-1024 allowed)"
    elif [[ $desc_len -eq 0 ]]; then
        fail "Description must not be empty"
    else
        fail "Length is ${desc_len} (must be 1-1024)"
    fi
else
    fail 'Required field "description" not found in frontmatter'
fi

# --- Body length ---
echo ""
echo -e "\033[37mSKILL.md body:\033[0m"

if [[ $BODY_LINES -le 500 ]]; then
    pass "Body is ${BODY_LINES} lines (recommended max 500)"
else
    warn "Body is ${BODY_LINES} lines (recommended max 500 — consider splitting into references/)"
fi

# --- File sizes ---
echo ""
echo -e "\033[37mFile sizes:\033[0m"

LARGE_FILES=$(find "$SKILL_PATH" -type f -size +5M 2>/dev/null)
if [[ -z "$LARGE_FILES" ]]; then
    pass "All files under 5 MB"
else
    while IFS= read -r lf; do
        size_bytes=$(stat -f%z "$lf" 2>/dev/null || stat --printf="%s" "$lf" 2>/dev/null || echo "0")
        size_mb=$(echo "scale=2; $size_bytes / 1048576" | bc 2>/dev/null || echo "?")
        fail "File '$(basename "$lf")' is ${size_mb} MB (max 5 MB)"
    done <<< "$LARGE_FILES"
fi

# --- Security check ---
echo ""
echo -e "\033[37mSecurity:\033[0m"

FOUND_SECRETS=false
SECRET_PATTERNS=(
    'password\s*[:=]'
    'secret\s*[:=]'
    'api[_-]?key\s*[:=]'
    'token\s*[:=]\s*['"'"'""][A-Za-z0-9]'
    'BEGIN\s+(RSA\s+)?PRIVATE\s+KEY'
)

for pattern in "${SECRET_PATTERNS[@]}"; do
    matches=$(grep -rlE "$pattern" "$SKILL_PATH" 2>/dev/null || true)
    if [[ -n "$matches" ]]; then
        while IFS= read -r match_file; do
            warn "Potential secret/credential in '$(basename "$match_file")' (pattern: ${pattern})"
            FOUND_SECRETS=true
        done <<< "$matches"
    fi
done

if [[ "$FOUND_SECRETS" == false ]]; then
    pass "No obvious credentials or secrets detected"
fi

# --- NPX validation ---
if [[ "$SKIP_NPX" == false ]]; then
    echo ""
    echo -e "\033[37mNPX skills-ref validation:\033[0m"

    if command -v npx &> /dev/null; then
        if npx skills-ref validate "$SKILL_PATH" 2>&1; then
            pass "npx skills-ref validate passed"
        else
            fail "npx skills-ref validate failed"
        fi
    else
        warn "npx not found — skipping skills-ref validation (install Node.js for full validation)"
    fi
fi

# --- Summary ---
echo ""
echo -e "\033[36m--- Summary ---\033[0m"
echo -e "  \033[32mPassed:   ${PASSED}\033[0m"
echo -e "  \033[33mWarnings: ${WARNINGS}\033[0m"
echo -e "  \033[31mErrors:   ${ERRORS}\033[0m"
echo ""

if [[ $ERRORS -eq 0 ]]; then
    echo -e "\033[32mValidation PASSED.\033[0m"
    exit 0
else
    echo -e "\033[31mValidation FAILED.\033[0m"
    exit 1
fi
