# Search Claude Sessions

Search across all your Claude sessions for specific keywords.

## Arguments

$ARGUMENTS - Search term(s) to find in your sessions

## Instructions

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/search-sessions.js "$ARGUMENTS"
```

Search across all Claude sessions by keyword with:
- Project name and session age
- Session summary (AI-generated description)
- Session name (slug)
- **Git remote** (primary repo URL)
- **Project directory** path
- Session ID for resuming
- Highlighted matches (up to 5 per session)
- Shows first 15 matching sessions (override with `--limit N`)

Filters out system context injections (CLAUDE.md, MEMORY.md, active-projects) to show only real conversation matches. Scans up to 8000 lines per session file (vs 500 in legacy).

**Example:** `/claude-tracker-search websocket` finds all sessions mentioning websocket.
