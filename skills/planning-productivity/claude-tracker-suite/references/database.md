# Database (`tracker.db`)


Single SQLite database at `~/.claude/tracker.db` consolidates all session metadata, git tracking, tags, and three capabilities: checkpoints, phase tracking, and tagged phrases.

**API module**: `~/.claude/lib/tracker-db.js` — synchronous node:sqlite `DatabaseSync` (built into Node >= 22.13, no native module to rebuild), WAL mode, singleton lazy-open. The compat shim keeps the `prepare/run/get/all/exec/pragma/transaction` surface the call sites were written against and throws on a missing named parameter. `isAvailable()` is a real open probe (attempts a read-only open); `tryDb()` in `tracker-utils.js` prints `tracker-db unavailable: <reason> — falling back to JSONL scan` to stderr once per process instead of failing silently.

```bash
# Query directly
sqlite3 ~/.claude/tracker.db "SELECT COUNT(*) FROM sessions;"
sqlite3 ~/.claude/tracker.db "SELECT phase, COUNT(*) FROM phases GROUP BY phase;"
sqlite3 ~/.claude/tracker.db "SELECT phrase, GROUP_CONCAT(tag) FROM tagged_phrases tp LEFT JOIN tagged_phrase_tags tpt ON tpt.phrase_id = tp.id GROUP BY tp.id ORDER BY tp.timestamp DESC LIMIT 10;"
```

**Migration** (idempotent): `node ~/.claude/scripts/migrate-to-sqlite.js`

## Title / Nickname History

The `title_history` table records every name a session has ever had, with provenance. Sources: `user` (from `/rename` custom-title lines), `slug` (auto-nickname from Claude Code), `cache` (May 2026 metadata import from `session-summaries.json`), `summarizer` (from `backfill-summaries.js`).

```bash
# Print the title timeline for a session
node ~/.claude/skills/claude-tracker-suite/scripts/search-sessions.js titles <id-prefix>

# Query raw history
sqlite3 ~/.claude/tracker.db "SELECT title, source, observed_at FROM title_history WHERE session_id LIKE 'abc%' ORDER BY observed_at;"
```

Title events are extracted during transcript indexing (`index-transcripts.js` v4+). `/rename` entries route by the line's own `sessionId`—a rename issued after `/resume` targets the previous session, not the file it was written into. This corrects a known upstream behavior where Claude Code's metadata scanner assigns the rename to the wrong session.

Default search automatically surfaces sessions findable only by a former title under a "former-title matches" heading. The `titles` subcommand prints the full chronological timeline: timestamp, source, title value, and cross-session rename provenance.

## Checkpoints

Named bookmarks within sessions capturing label, git state, workflow phase, and modified files.

```bash
# Manual checkpoint
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js create "finished auth module"
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js create "pre-deploy" --summary "about to push"

# List checkpoints
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js list
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js list --phase implementing
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js list --limit 10
```

Auto-checkpoints are created on git commits (`git-track-post.sh`) and on entering a milestone phase (`testing`, `committing`, `deploying`) via `phase-detect.py`.

## Phase Tracking

Automatic workflow phase detection via PostToolUse hook (`phase-detect.py`). Rolling window of last 10 tool calls, hysteresis to prevent flickering. A phase stays open across turns and closes at SessionEnd (`session-sync-db.py --session-end`); phases of sessions that ended without one (crash, kill) are closed by the hourly indexer run once the session is idle 12 h and not live.

Phases: `exploring`, `planning`, `deepening`, `implementing`, `testing`, `reviewing`, `debugging`, `committing`, `deploying`, `discussing`.

```bash
# Query current phase for a session
sqlite3 ~/.claude/tracker.db "SELECT phase, started_at FROM phases WHERE session_id = 'abc...' AND ended_at IS NULL;"

# Phase history
sqlite3 ~/.claude/tracker.db "SELECT phase, started_at, ended_at, duration_ms FROM phases WHERE session_id = 'abc...' ORDER BY started_at;"

# Phase analytics
sqlite3 ~/.claude/tracker.db "SELECT phase, COUNT(*) as transitions, AVG(duration_ms)/1000 as avg_seconds FROM phases GROUP BY phase;"
```

## Tagged Phrases

Notable excerpts captured from sessions with tags, searchable via FTS5.

```bash
# Capture a phrase
node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js capture "assumptions are the enemy" --tags principle,design

# Search phrases (FTS5)
node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js search "assumptions"

# List by tag
node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js tag principle

# List recent phrases
node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js list --limit 20
```

Phrases are also auto-extracted by the `session-tags-infer.py` Stop hook during LLM inference.
