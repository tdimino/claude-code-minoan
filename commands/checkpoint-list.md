# List Session Checkpoints

Query checkpoints created via `/checkpoint` or auto-generated on commits
and phase transitions. Shows label, git state, phase, and summary.

## Arguments

`$ARGUMENTS` - optional flags: `--phase <phase>`, `--limit N`, `--session <id>`.
Without arguments, lists checkpoints for the current session (or recent across
all sessions if no active session detected).

## Instructions

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js list $ARGUMENTS
```

## Examples

- `/checkpoint-list` — show checkpoints for current session
- `/checkpoint-list --phase implementing` — filter by workflow phase
- `/checkpoint-list --limit 10` — recent checkpoints across all sessions
- `/checkpoint-list --session abc12345` — checkpoints for a specific session

## Related

- `/checkpoint` — create a new checkpoint
- `/claude-tracker-search` — search sessions by keyword
