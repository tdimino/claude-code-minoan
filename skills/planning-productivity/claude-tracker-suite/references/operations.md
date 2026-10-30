# Operations

Indexing, maintenance, workspace snapshots, terminal integration, and setup for the claude-tracker-suite. The everyday commands (search, recent, resume, spawn, alive) are in `SKILL.md`.

## Transcript Index & Summary Backfill

```bash
# Incremental index refresh (skips unchanged files; runs automatically via hooks and launchd)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js

# Full rebuild (also forced automatically when EXTRACTOR_VERSION bumps)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --rebuild

# Single session (what the hooks call)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --session <id>
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --stdin --quiet --debounce 30

# Budget-limited refresh (what search-sessions.js calls in-process)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --budget 1500

# Backfill missing summaries — DISABLED BY DEFAULT, requires --enable
# (or TRACKER_SUMMARIZER=1). Hermetic when run: --safe-mode
# --no-session-persistence, no hooks fire, no synthetic sessions persist.
node ~/.claude/skills/claude-tracker-suite/scripts/backfill-summaries.js --enable
node ~/.claude/skills/claude-tracker-suite/scripts/backfill-summaries.js --enable --session <id-prefix>  # force one

# OpenRouter backend instead of claude CLI (default model moonshotai/kimi-k2;
# key from OPENROUTER_API_KEY or ~/.config/env/secrets.env)
node ~/.claude/skills/claude-tracker-suite/scripts/backfill-summaries.js --enable --provider openrouter

# Preview excerpts without any LLM calls (no gate needed)
node ~/.claude/skills/claude-tracker-suite/scripts/backfill-summaries.js --dry-run

# NOTE: the watcher-daemon auto-name path (update-active-projects.py) is also
# gated off by default; set TRACKER_AUTO_NAME=1 to re-enable it.

# Recall regression suite — run after touching search code or synonyms
node ~/.claude/skills/claude-tracker-suite/scripts/search-regression.js

# Suite self-audit → AUDIT.md (P0-P3 findings)
node ~/.claude/skills/claude-tracker-suite/scripts/audit-suite.js
```

The indexer runs automatically through three channels: Stop and SessionEnd hooks (`--stdin --quiet --debounce 30` async on Stop, `--stdin --quiet --debounce 10 --detach` on SessionEnd, which hands the work to a detached child logging to `~/.claude/logs/transcript-index-hook.log`, so indexing never holds up exit; the other SessionEnd hooks still get up to 10 s), the hourly `com.claude.transcript-index` launchd agent (plist in `scripts/`, installed in `~/Library/LaunchAgents/`, logs in `~/.claude/logs/transcript-index.{log,err}`), and in-process from `search-sessions.js` before every body search (1.5s budget). Sessions are searchable within seconds of their last turn.

Incremental indexing skips files whose size, mtime, and `EXTRACTOR_VERSION` all match `transcript_index_state`, and reads a file that only grew from the byte offset its last pass reached. Bumping the version constant forces a full reindex under new extraction rules. Full runs print a `Sanity:` line when recent sessions carry impossible metadata (zero turns on a large transcript, output without a model or cost source, an estimated cost for an unpriced model). Read errors are never recorded as indexed—the session stays eligible for the next run, preventing a partial read from permanently masking content from search. Deleted transcripts are pruned on full (unlimited) runs.

Since v4, the indexer also extracts **title history events** from each transcript: `/rename` custom-title lines (source `user`), slug changes (source `slug`). Custom-title lines route by the line's own `sessionId` field, not the containing file—a `/rename` after `/resume` writes into the active transcript but targets the previous session. Claude Code's own metadata scanner gets this wrong, overwriting the active session's title with the rename target's title. Consecutive duplicate title values within a file collapse to a single event.

Known lexical limit: a session can only be found by words that actually occur in it—the `[expected fail]` regression fixture documents this; a semantic (rlama) layer is the designated future fix.

## Auto-Summarize Daemon

Watch for new sessions and auto-populate summary cache:

```bash
claude-tracker-watch --status            # Check if daemon is running
claude-tracker-watch --daemon            # Start in background
claude-tracker-watch --stop              # Stop running daemon
claude-tracker-watch --verbose           # Foreground with debug output
```

Dormant: it watches `sessions-index.json`, which Claude Code no longer writes, so it never fires on current versions. Kept for reference; see `references/daemon-setup.md` for the launchd agents that do run (workspace-snapshot, transcript-index, db-maintain).

## Detect Projects

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/detect-projects.js                # List all
node ~/.claude/skills/claude-tracker-suite/scripts/detect-projects.js --suggest      # Suggest additions
node ~/.claude/skills/claude-tracker-suite/scripts/detect-projects.js --scaffold     # Create CLAUDE.md stubs
node ~/.claude/skills/claude-tracker-suite/scripts/detect-projects.js --since 30d    # Recent only
```

## Update Active Projects

```bash
python3 ~/.claude/scripts/update-active-projects.py              # Regenerate active-projects.md
python3 ~/.claude/scripts/update-active-projects.py --summarize  # Show sessions needing summaries
```

The generated table includes Model, Turns, and Cost columns from enriched session data (extracted from JSONL transcripts). Git worktree sessions show a tree emoji badge. The auto-name path (one-shot `claude --model haiku` call for sessions without summaries) is disabled by default—set `TRACKER_AUTO_NAME=1` to re-enable it. Native Claude Code session summaries stopped generating around v2.1.31 (February 2026), so `sessions-index.json` summary fields are stale for newer sessions; use `backfill-summaries.js` or the transcript index instead.

## Bootstrap New Setup

Generate a complete `~/.claude/` configuration for a new machine:

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/bootstrap-claude-setup.js --user "Name" --dry-run
node ~/.claude/skills/claude-tracker-suite/scripts/bootstrap-claude-setup.js --user "Name"
```

Creates directory structure, global CLAUDE.md, userModel template, agent_docs stubs, and project CLAUDE.md scaffolds. Follow up with `/claude-md-manager` to enrich generated files.

## Workspace Stamp & Restore (claude + codex)

Survive a logout/reboot with every agent session intact:

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js   # Stamp now (also runs every 5 min via launchd)
claude-tracker-resume --workspace --dry-run                            # Preview the restore
claude-tracker-resume --workspace                                      # Reopen every session in Ghostty tabs, in order
```

The stamp (`~/.claude/workspace-state.json`) captures all live **Claude Code** sessions (from the authoritative `~/.claude/sessions/<pid>.json` PID files) and **Codex CLI** sessions (native binary PIDs joined to their open rollout files via `lsof`; the earliest-opened rollout is the main thread, its filename carries the UUID). Entries are TTY-ordered so tabs restore in their original order. Empty-protection means a post-logout stamp never clobbers the last good one. Restore warns when the stamp is >15 min old and reports per-agent counts.

### Save

```bash
# Snapshot current sessions
node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js

# Preview without writing
node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js --dry-run
```

Detects alive sessions via PID files (`~/.claude/sessions/<pid>.json`) verified against `ps`, matches them to tracker DB entries, and writes `~/.claude/workspace-state.json` with session IDs, project directories, and tab titles. Title precedence: custom_title → auto_title → slug → summary. Deduplicates by sessionId (multiple PIDs from forks and MCP children resolve to one entry). Never overwrites a good snapshot with an empty one—after a crash or logout with zero live sessions, the previous snapshot is preserved.

### Restore

```bash
# Restore all saved sessions into Ghostty tabs
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh

# Preview what would be restored
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh --dry-run

# Restore at most 3 sessions
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh --limit 3

# Slow stagger for a loaded machine
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh --stagger 3
```

Opens each session in a new Ghostty tab via `ghostty-resume.sh`. Default stagger is 1 second between tabs. Skips sessions that are still running, missing project directories, and missing transcripts—each with a reason, never aborting on one failure. Reports per-agent counts.

### Automatic Snapshots (launchd)

A launchd plist at `scripts/com.claude.workspace-snapshot.plist` runs `save-workspace.js` every 300 seconds. Install:

```bash
cp ~/.claude/skills/claude-tracker-suite/scripts/com.claude.workspace-snapshot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.claude.workspace-snapshot.plist
```

## Named Sessions (`cc` Wrapper)

Shell function that wraps `claude` with automatic Ghostty tab naming and tracker tagging.

```bash
# Source in .zshrc (one-time setup)
source ~/.claude/skills/claude-tracker-suite/scripts/claude-wrapper.sh

# Start a named session
cc --name "kothar-refactor"

# Resume with a name
cc --resume abc12345 --name "auth-fix"

# Default: tab title = basename of cwd
cc
```

The `cc` function sets the Ghostty tab title via OSC 1 escape sequence before launching `claude`, then tags the session with the name in `tracker.db` on exit. Tab title resets to the directory basename when the session ends.

## Tab Auto-Naming

`new-session.sh`, `resume-session.sh`, and `ghostty-resume.sh` all accept `--name` to label the session. Claude Code sets the Ghostty tab title itself (`-n` / derived name)—no OSC injection is needed.

## Yazi File Explorer

Open a yazi file manager in a Ghostty split pane for project browsing.

```bash
# Open yazi in a left split (default, sidebar-style)
~/.claude/skills/claude-tracker-suite/scripts/open-file-explorer.sh

# Open at a specific directory
~/.claude/skills/claude-tracker-suite/scripts/open-file-explorer.sh ~/my-project

# Split to the right instead
~/.claude/skills/claude-tracker-suite/scripts/open-file-explorer.sh --right
```

Uses System Events clipboard-paste pattern (Cmd+D for split, then paste yazi command). Requires yazi: `brew install yazi ffmpegthumbnailer unar jq poppler fd ripgrep fzf zoxide`.

## Performance

| Operation | Before | After |
|-----------|--------|-------|
| Search (two-word query) | 11.1s (JSONL scan) | 0.06s (FTS5) |
| List sessions | 1.4s | 0.44s |
| Recent sessions | crash | 0.13s |
| `claude-tracker-alive` | — | 0.25s |
| Live detection | 881ms | ~100ms |
| Index backlog (85 files) | — | 1.3s |
| Index one new turn (1.67 GB transcript) | full re-read | 4–5 ms (byte-offset increment) |
| Hourly index pass | 10–53 s | 0.1–0.4 s |
| Full rebuild (1,780 sessions) | — | ~60 s |
| Both tracker DBs on disk | 1,750 MB | 242 MB after optimize + VACUUM |
| Opener (per tab) | — | ~1–2s |
