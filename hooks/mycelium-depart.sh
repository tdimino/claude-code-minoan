#!/usr/bin/env bash
# Stop hook (async): run mycelium composting report.
# Follows stop-handoff.py throttle pattern with cooldown file.

set -euo pipefail

COOLDOWN_FILE="/tmp/mycelium-depart-cooldown"
COOLDOWN_SECONDS=180  # 3 minutes

# Check cooldown
if [[ -f "$COOLDOWN_FILE" ]]; then
    last=$(cat "$COOLDOWN_FILE" 2>/dev/null || echo 0)
    now=$(date +%s)
    elapsed=$(( now - last ))
    if (( elapsed < COOLDOWN_SECONDS )); then
        exit 0
    fi
fi

# Check mycelium.sh is installed
command -v mycelium.sh &>/dev/null || exit 0

# Check we're in a git repo
git rev-parse --git-dir &>/dev/null || exit 0

# Check mycelium is activated
git notes --ref=mycelium list &>/dev/null || exit 0

# All preconditions passed — update cooldown
date +%s > "$COOLDOWN_FILE"

# Run composting report
report=$(mycelium.sh compost --report 2>/dev/null || true)

# Check for stale notes
if [[ -n "$report" ]]; then
    stale_count=$(echo "$report" | sed -n 's/.*stale:\([0-9]*\).*/\1/p' 2>/dev/null)
    stale_count="${stale_count:-0}"
    if (( stale_count > 20 )); then
        printf '%s' "Mycelium: $stale_count stale notes detected. Consider running: mycelium.sh compost <path> --dry-run" | \
            jq -Rs '{additionalContext: .}'
    fi
fi
