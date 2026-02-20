#!/bin/bash
# Stop hook: update agent_docs/active-projects.md in background
# Captures hook stdin to temp file, then launches Python script detached.
# Temp file avoids stdin pipe race condition when backgrounding.
INPUT=$(cat)
TMPFILE=$(mktemp /tmp/hook-input.XXXXXX)
printf '%s' "$INPUT" > "$TMPFILE"
nohup python3 ~/.claude/scripts/update-active-projects.py "$TMPFILE" > /dev/null 2>&1 &
exit 0
