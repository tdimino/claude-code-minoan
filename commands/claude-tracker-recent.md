# Recent Claude Sessions (tracker.db)

The fast listing: recent sessions straight from `tracker.db`, no transcript parsing.

**Usage:**
- `/claude-tracker-recent` — last 10 sessions
- `/claude-tracker-recent --limit 20 --project knossot`
- `/claude-tracker-recent --since 24h --model opus`
- `/claude-tracker-recent --json`

## Arguments

$ARGUMENTS

## Instructions

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/recent-sessions.js $ARGUMENTS
```

Shows title, project, model, turns, cost, tags, branch, short ID and the resume command per session. Add `--copy` to put the first resume command on the clipboard (never done by default).
