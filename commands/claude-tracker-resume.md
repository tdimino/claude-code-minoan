# Claude Session Resume

Bring a session back in a new Ghostty tab, found by session ID prefix, name, or a transcript search.

**Usage:**
- `/claude-tracker-resume 1da2b718` — by session ID (8+ hex chars)
- `/claude-tracker-resume kothar mac mini` — top transcript-search hit
- `/claude-tracker-resume --here <id>` — print the launcher command to run in this terminal instead of opening a tab
- `/claude-tracker-resume` — no argument: list crashed sessions (newest per project with no live process)

## Arguments

$ARGUMENTS

## Instructions

```bash
ARGS="$ARGUMENTS"
HERE=false
case "$ARGS" in --here*) HERE=true; ARGS="${ARGS#--here}"; ARGS="${ARGS# }";; esac
if [ -z "$ARGS" ]; then
  ~/.local/bin/claude-tracker-resume
elif printf '%s' "$ARGS" | grep -Eq '^[0-9a-fA-F-]{8,}$'; then
  if $HERE; then
    L=$(~/.claude/scripts/ghostty-resume.sh "$ARGS" --print) && echo "Run in this terminal: bash $L"
  else
    ~/.claude/scripts/ghostty-resume.sh "$ARGS"
  fi
elif $HERE; then
  node ~/.claude/skills/claude-tracker-suite/scripts/search-sessions.js "$ARGS" --limit 1
else
  node ~/.claude/skills/claude-tracker-suite/scripts/search-sessions.js "$ARGS" --open --limit 1
fi
```

A session that is already live is refused by Claude Code ("already running"); `/claude-tracker-here` shows which ones are. If Ghostty cannot be scripted, the opener prints the exact `bash ~/.claude/run/launch/r-….sh` line to run by hand. To reopen every tab from the last workspace stamp: `claude-tracker-resume --workspace`.
