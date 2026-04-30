# Create Session Checkpoint

Create a named bookmark in the current session capturing: label, git state
(branch + HEAD commit), current workflow phase, modified files, and optional
summary. Checkpoints are stored in `tracker.db` and queryable via
`/checkpoint-list`.

## Arguments

`$ARGUMENTS` - checkpoint label (required), optionally followed by
`--summary "description"`.

## Instructions

```bash
if [ -z "$ARGUMENTS" ]; then
  echo "Usage: /checkpoint <label> [--summary \"description\"]"
  exit 1
fi

node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js create $ARGUMENTS
```

## Examples

- `/checkpoint "finished auth module"` — label only
- `/checkpoint "started refactor" --summary "breaking out auth into separate service"`
- `/checkpoint "pre-deploy"` — mark state before risky action

## Related

- `/checkpoint-list` — query checkpoints
- `/tag` — attach keyword tags to sessions
- `/claude-tracker-search` — search sessions by keyword
