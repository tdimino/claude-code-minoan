---
name: claude-tracker-suite
description: "Claude Code session management suite: search sessions by topic/ID, resume crashed sessions, monitor live sessions, detect projects, auto-summarize new sessions, and bootstrap new setups. This skill should be used when searching past sessions, checking running sessions, resuming work, or bootstrapping a new machine."
argument-hint: [query or --id <prefix>]
allowed-tools: Bash(claude-tracker*), Bash(node ~/.claude/skills/claude-tracker-suite/scripts/*), Bash(python3 ~/.claude/scripts/*), Read, Grep, Glob, Edit, Write, Skill
---

# Claude Session Management Suite

Search, browse, monitor, and manage Claude Code session history across all projects.

## Tools Overview

| Tool | Purpose |
|------|---------|
| `claude-tracker-search` | Search sessions by topic, ID, project, or time range |
| `claude-tracker-resume` | Find and resume crashed/inactive sessions |
| `claude-tracker-alive` | Check which sessions have running processes |
| `claude-tracker-watch` | Daemon: auto-summarize new sessions, update active-projects.md |
| `claude-tracker` | List recent sessions (all or VS Code only) |
| `detect-projects.js` | Scan sessions to find all projects, check CLAUDE.md coverage |
| `bootstrap-claude-setup.js` | Generate complete ~/.claude/ config for new machine |
| `update-active-projects.py` | Regenerate active-projects.md with enriched session data |

## Quick Start

```bash
# Search by topic
claude-tracker-search "kothar mac mini"

# Interactive search with fzf
claude-tracker-search "kothar" --fzf

# Search by session ID prefix
claude-tracker-search --id 1da2b718

# Check what's alive
claude-tracker-alive

# Resume crashed sessions in tmux
claude-tracker-resume --tmux

# Start auto-summarize daemon
claude-tracker-watch --daemon
```

## Search

```bash
claude-tracker-search "$ARGUMENTS"
```

**Search targets** (weighted ranking): Summary (3x), First prompt (2x), Project name (1x), Git branch (1x).

| Flag | Description |
|------|-------------|
| `--limit <n>` | Max results (default: 20) |
| `--id <prefix>` | Lookup by session ID prefix (8+ chars) |
| `--project <name>` | Filter by project name (substring) |
| `--since <duration>` | Recent only: `7d`, `24h`, `30m`, `2w` |
| `--json` | Machine-readable JSON output |
| `--fzf` | Interactive selection via fzf (outputs resume command) |

## Resume Crashed Sessions

```bash
claude-tracker-resume                    # List crashed sessions with resume commands
claude-tracker-resume --tmux             # Resume all in tmux windows
claude-tracker-resume --zsh              # Resume all in Terminal.app tabs (macOS)
claude-tracker-resume --all              # Include non-VS Code sessions
claude-tracker-resume --dry-run          # Preview without acting
```

Smart fallback: if `--resume` fails on an expired session, automatically starts a fresh session in that project directory. Sessions older than 7 days show a STALE badge.

## Alive Detection

Check which sessions have running Claude processes:

```bash
claude-tracker-alive                     # Running + stale sessions overview
claude-tracker-alive --running           # Only sessions with active processes
claude-tracker-alive --stale             # Only sessions with no process
claude-tracker-alive --json              # Machine-readable output
```

Cross-references running `claude` PIDs (via `pgrep` + `lsof`) against recent session files. Sessions >3 days without a process show an OLD badge.

## Auto-Summarize Daemon

Watch for new sessions and auto-populate summary cache:

```bash
claude-tracker-watch --status            # Check if daemon is running
claude-tracker-watch --daemon            # Start in background
claude-tracker-watch --stop              # Stop running daemon
claude-tracker-watch --verbose           # Foreground with debug output
```

The daemon watches `~/.claude/projects/*/sessions-index.json` for changes. When new sessions appear, it caches summaries from Claude Code metadata and regenerates `active-projects.md`. See `references/daemon-setup.md` for launchd plist and lifecycle details.

## Session Listing

```bash
claude-tracker                           # All recent sessions
claude-tracker vscode                    # VS Code sessions only
```

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

The generated table includes Model, Turns, and Cost columns from enriched session data (extracted from JSONL transcripts). Git worktree sessions show a tree emoji badge. Sessions without summaries are auto-named via one-shot `claude --model haiku` call.

## Bootstrap New Setup

Generate a complete `~/.claude/` configuration for a new machine:

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/bootstrap-claude-setup.js --user "Name" --dry-run
node ~/.claude/skills/claude-tracker-suite/scripts/bootstrap-claude-setup.js --user "Name"
```

Creates directory structure, global CLAUDE.md, userModel template, agent_docs stubs, and project CLAUDE.md scaffolds. Follow up with `/claude-md-manager` to enrich generated files.

## Workflow: Find and Resume

1. `claude-tracker-search "topic"` — find matching sessions
2. `claude --resume <session-id>` — resume the one you want
3. Or `claude-tracker-resume --tmux` — auto-resume all crashed sessions

## Workflow: Monitor Active Work

1. `claude-tracker-alive` — see what's running vs stale
2. `claude-tracker-watch --daemon` — keep summaries auto-updated
3. Read `~/.claude/agent_docs/active-projects.md` — curated project overview

## References

For detailed schemas and infrastructure:

- `references/data-schemas.md` — Session index, summary cache, and JSONL transcript schemas; data source locations; shared library API
- `references/daemon-setup.md` — Watcher daemon lifecycle and launchd plist template
