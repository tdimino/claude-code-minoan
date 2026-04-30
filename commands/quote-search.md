# Search Captured Phrases

Search notable phrases captured via `/quote` or auto-extracted from sessions.
Uses FTS5 full-text search or tag-based filtering.

## Arguments

`$ARGUMENTS` - search query or `--tag <tag-name>`. Without arguments, lists
recent phrases across all sessions.

## Instructions

```bash
if [ -z "$ARGUMENTS" ]; then
  node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js list --limit 20
  exit 0
fi

# Check if first arg is --tag
case "$ARGUMENTS" in
  --tag*)
    node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js tag ${ARGUMENTS#--tag }
    ;;
  --session*)
    node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js list $ARGUMENTS
    ;;
  *)
    node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js search $ARGUMENTS
    ;;
esac
```

## Examples

- `/quote-search assumptions` — FTS5 search for "assumptions"
- `/quote-search --tag design` — list phrases tagged "design"
- `/quote-search --session abc12345` — phrases from a specific session
- `/quote-search` — list recent phrases across all sessions

## Related

- `/quote` — capture a new phrase
- `/claude-tracker-search` — search sessions by keyword
