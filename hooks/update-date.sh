#!/bin/bash
# SessionStart hook — update currentDate in all project MEMORY.md files
# 2026 "template literal" pattern: hooks rewrite auto-memory on session start.
TODAY=$(date +%Y-%m-%d)
for mem in "$HOME"/.claude/projects/*/memory/MEMORY.md; do
  [ -f "$mem" ] && sed -i '' "s/^Today's date is .*/Today's date is ${TODAY}./" "$mem"
done
