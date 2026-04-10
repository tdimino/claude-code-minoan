# Tag Current Session

Attach manual keyword metatags to the current Claude Code session. These tags
supplement the auto-generated Qwen tags in `~/.claude/session-registry.json`
and are searchable via `/claude-tracker-search <tag> --name` (and, after the
Phase 2 default-mode pre-pass, via the bare `/claude-tracker-search <tag>`).

Use this when the auto-tagger missed a keyword that matters for future recall —
e.g., the user's mental label for the session that's never spoken verbatim in
the transcript.

## Arguments

`$ARGUMENTS` - one or more tags, space-separated. Prefix a tag with `-` to
remove it. Use hyphenated words (`codex-skill-detection`) rather than quoted
multi-word strings for slash-command ergonomics.

## Instructions

```bash
# Split arguments into adds and removes. A leading `-` means remove.
ADDS=()
REMOVES=()
for arg in $ARGUMENTS; do
  case "$arg" in
    -*) REMOVES+=("${arg#-}") ;;
    *)  ADDS+=("$arg") ;;
  esac
done

if [ ${#ADDS[@]} -eq 0 ] && [ ${#REMOVES[@]} -eq 0 ]; then
  echo "Usage: /tag <tag> [<tag>...] or /tag -<tag> to remove"
  exit 1
fi

if [ ${#ADDS[@]} -gt 0 ]; then
  node ~/.claude/skills/claude-tracker-suite/scripts/tag-session.js add "${ADDS[@]}"
fi

if [ ${#REMOVES[@]} -gt 0 ]; then
  node ~/.claude/skills/claude-tracker-suite/scripts/tag-session.js remove "${REMOVES[@]}"
fi
```

## Examples

- `/tag codex-skill-detection` — add one tag
- `/tag codex-skill-detection eval-design` — add two tags
- `/tag -off-topic-tag` — remove a tag
- `/tag foo -bar baz` — mixed add/remove in one call
- `node tag-session.js list` — inspect current tags (CLI only, no slash command yet)

## How it works

- **Live session (this one):** Writes a `.pending-tags` breadcrumb to
  `~/.claude/session-tags/{session_id}.pending-tags`. The next Stop event
  triggers `session-tags-infer.py`, which reads the breadcrumb BEFORE its
  3-min Qwen cooldown, upserts `user_tags` in `session-registry.json` under
  fcntl lock, and deletes the breadcrumb. The tag is searchable immediately
  after that Stop event fires.
- **Closed session:** Use `node tag-session.js add <tag> --session <id>`
  directly — it writes to the registry without needing a live hook.

## Related

- `/claude-tracker-search` — search by keyword (body or metadata)
- `/claude-tracker-here` — list sessions for current directory
- Plan: `~/.claude/plans/2026-04-10-claude-tracker-session-metatags.md`
