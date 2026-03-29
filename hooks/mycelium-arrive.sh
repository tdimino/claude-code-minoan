#!/usr/bin/env bash
# SessionStart hook (async): load mycelium constraints and warnings on session start.
# Only fires in git repos with mycelium activated.

set -euo pipefail

# Check mycelium.sh is installed
command -v mycelium.sh &>/dev/null || exit 0

# Check we're in a git repo
git rev-parse --git-dir &>/dev/null || exit 0

# Check mycelium is activated (notes ref exists)
git notes --ref=mycelium list &>/dev/null || exit 0

# Collect constraints and warnings
constraints=$(mycelium.sh find constraint 2>/dev/null || true)
warnings=$(mycelium.sh find warning 2>/dev/null || true)
report=$(mycelium.sh compost --report 2>/dev/null || true)

# Build context output
output=""

if [[ -n "$constraints" ]]; then
    output+="=== Mycelium Constraints ===
$constraints
"
fi

if [[ -n "$warnings" ]]; then
    output+="=== Mycelium Warnings ===
$warnings
"
fi

if [[ -n "$report" && "$report" != *"notes  0"* ]]; then
    output+="=== Mycelium Status ===
$report
"
fi

if [[ -n "$output" ]]; then
    printf '%s' "$output" | jq -Rs '{additionalContext: .}'
fi
