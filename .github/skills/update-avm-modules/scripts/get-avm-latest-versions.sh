#!/usr/bin/env bash
# Get-AvmLatestVersions — Shell variant
#
# Scans a Bicep file for Azure Verified Module (AVM) references,
# queries mcr.microsoft.com for available tags, and outputs a comparison table.
#
# Usage:
#   ./get-avm-latest-versions.sh <bicep-file>
#
# Requirements: curl, jq, grep, sed, sort

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <bicep-file>" >&2
    exit 1
fi

BICEP_FILE="$1"

if [ ! -f "$BICEP_FILE" ]; then
    echo "Error: File not found: $BICEP_FILE" >&2
    exit 1
fi

for cmd in curl jq grep sed sort; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: Required command '$cmd' not found." >&2
        exit 1
    fi
done

# Compare two semantic versions. Returns: -1, 0, or 1
compare_semver() {
    local v1="$1" v2="$2"
    local IFS='.'
    read -ra parts1 <<<"$v1"
    read -ra parts2 <<<"$v2"

    local max=${#parts1[@]}
    [ ${#parts2[@]} -gt "$max" ] && max=${#parts2[@]}

    for ((i = 0; i < max; i++)); do
        local p1=${parts1[$i]:-0}
        local p2=${parts2[$i]:-0}
        if [ "$p1" -lt "$p2" ]; then echo "-1"; return; fi
        if [ "$p1" -gt "$p2" ]; then echo "1"; return; fi
    done
    echo "0"
}

# Sort versions and return the latest stable (no pre-release suffix)
get_latest_stable() {
    local tags_json="$1"
    echo "$tags_json" | jq -r '.tags[]' 2>/dev/null \
        | grep -E '^\d+\.\d+(\.\d+)?$' \
        | sort -t. -k1,1n -k2,2n -k3,3n \
        | tail -1
}

# Extract AVM module references from the Bicep file
modules=$(grep -oE 'br/public:(avm/(res|ptn|utl)/[^:]+):([0-9]+\.[0-9]+(\.[0-9]+)?)' "$BICEP_FILE" \
    | sed -E 's|br/public:(avm/[^:]+):([0-9]+\.[0-9]+(\.[0-9]+)?)|\1 \2|' \
    | sort -u)

if [ -z "$modules" ]; then
    echo "No AVM module references found in: $BICEP_FILE"
    exit 0
fi

echo ""
echo "AVM Module Version Check: $BICEP_FILE"
echo "================================================================================"
echo ""
printf "%-55s %-10s %-10s %-8s %s\n" "Module" "Current" "Latest" "Status" "Icon"
echo "-----------------------------------------------------------------------------------------------"

update_count=0
current_count=0
failed_count=0
total_count=0
json_results="["

while IFS=' ' read -r module_path current_version; do
    total_count=$((total_count + 1))
    mcr_path="bicep/$module_path"
    tags_url="https://mcr.microsoft.com/v2/$mcr_path/tags/list"

    latest_version=""
    status="FAILED"
    icon="❌"

    if tags_json=$(curl -sf --max-time 15 "$tags_url" 2>/dev/null); then
        latest_version=$(get_latest_stable "$tags_json")

        if [ -n "$latest_version" ]; then
            cmp_result=$(compare_semver "$current_version" "$latest_version")

            if [ "$cmp_result" = "0" ]; then
                status="CURRENT"
                icon="✅"
                current_count=$((current_count + 1))
            else
                current_major=$(echo "$current_version" | cut -d. -f1)
                latest_major=$(echo "$latest_version" | cut -d. -f1)
                current_minor=$(echo "$current_version" | cut -d. -f2)
                latest_minor=$(echo "$latest_version" | cut -d. -f2)

                if [ "$current_major" != "$latest_major" ]; then
                    status="MAJOR"
                    icon="⚠️"
                elif [ "$current_minor" != "$latest_minor" ]; then
                    status="MINOR"
                    icon="🔄"
                else
                    status="PATCH"
                    icon="🔄"
                fi
                update_count=$((update_count + 1))
            fi
        else
            latest_version="N/A"
            failed_count=$((failed_count + 1))
        fi
    else
        latest_version="ERROR"
        failed_count=$((failed_count + 1))
        echo "Warning: Failed to query MCR for $module_path" >&2
    fi

    printf "%-55s %-10s %-10s %-8s %s\n" "$module_path" "$current_version" "$latest_version" "$status" "$icon"

    # Build JSON
    [ "$total_count" -gt 1 ] && json_results="$json_results,"
    json_results="$json_results{\"Module\":\"$module_path\",\"Current\":\"$current_version\",\"Latest\":\"$latest_version\",\"Status\":\"$status\"}"

done <<<"$modules"

json_results="$json_results]"

echo ""
echo "Summary: $total_count modules checked, $update_count updates available, $current_count current, $failed_count failed"
echo ""
echo "$json_results" | jq .
