# Capture Notable Phrase

Capture a notable phrase or excerpt from the current session with optional
tags. Stored in `tracker.db` and searchable via `/quote-search`.

## Arguments

`$ARGUMENTS` - the phrase text (required), optionally followed by
`--tags tag1,tag2` and/or `--source user|assistant`.

## Instructions

```bash
if [ -z "$ARGUMENTS" ]; then
  echo "Usage: /quote \"phrase text\" [--tags tag1,tag2] [--source user|assistant]"
  exit 1
fi

node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js capture $ARGUMENTS
```

## Examples

- `/quote "assumptions are the enemy"` — capture a phrase
- `/quote "assumptions are the enemy" --tags principle,design` — with tags
- `/quote "use ON CONFLICT instead of INSERT OR REPLACE" --source assistant --tags sqlite,pattern` — assistant quote with tags

## Related

- `/quote-search` — search captured phrases
- `/checkpoint` — create session checkpoint
- `/tag` — attach keyword tags to sessions
