---
name: claude-tracker-search
description: Search Claude Code sessions by summary, content, or session ID. Use when finding specific past sessions, locating work on particular topics, identifying which sessions to resume, detecting projects, or bootstrapping a new Claude Code setup. Also updates active-projects.md and session summaries.
argument-hint: [query or --id <prefix>]
user-invocable: true
allowed-tools: Bash(claude-tracker*), Bash(node ~/.claude/skills/claude-tracker-search/scripts/*), Bash(python3 ~/.claude/scripts/*), Read, Grep, Glob, Edit, Write, Skill
---

# Claude Tracker Search

Search, browse, and manage Claude Code session history. Find past sessions by topic, detect projects, resume crashed sessions, update docs, and bootstrap new setups.

## Quick Start

```bash
# Search by topic
claude-tracker-search "kothar mac mini"

# Search by session ID prefix
claude-tracker-search --id 1da2b718

# Filter by project
claude-tracker-search --project Aldea

# Recent sessions only
claude-tracker-search --since 7d

# JSON output for processing
claude-tracker-search --json
```

## Core Capabilities

### 1. Session Search

Search across all Claude Code sessions using `claude-tracker-search`:

```bash
claude-tracker-search "$ARGUMENTS"
```

**Search targets** (weighted ranking):
- Summary (3x) — Claude Code's session summary from sessions-index.json
- First prompt (2x) — The user's opening message
- Project name (1x) — Repository/directory name
- Git branch (1x) — Branch at time of session

**Flags:**
| Flag | Description |
|------|-------------|
| `--limit <n>` | Max results (default: 20) |
| `--id <prefix>` | Lookup by session ID prefix (8+ chars) |
| `--project <name>` | Filter by project name (substring) |
| `--since <duration>` | Only recent sessions: `7d`, `24h`, `30m`, `2w` |
| `--json` | JSON output for piping |

### 2. Session Listing

```bash
claude-tracker                    # All recent sessions
claude-tracker vscode             # VS Code sessions only (crash recovery)
```

### 3. Resume Crashed Sessions

Find and resume sessions that were running in VS Code but crashed:

```bash
claude-tracker-resume                    # List crashed sessions
claude-tracker-resume --tmux             # Resume all in tmux windows
claude-tracker-resume --zsh              # Resume all in Terminal.app tabs (macOS)
claude-tracker-resume --all              # Include non-VS Code sessions
claude-tracker-resume --tmux --dry-run   # Preview without acting
```

### 4. Detect Projects

Scan all sessions to find every unique project, check CLAUDE.md coverage, and identify gaps:

```bash
node ~/.claude/skills/claude-tracker-search/scripts/detect-projects.js                # List all
node ~/.claude/skills/claude-tracker-search/scripts/detect-projects.js --suggest      # Suggest additions
node ~/.claude/skills/claude-tracker-search/scripts/detect-projects.js --scaffold     # Create CLAUDE.md stubs
node ~/.claude/skills/claude-tracker-search/scripts/detect-projects.js --since 30d    # Recent only
```

### 5. Bootstrap New Setup

Generate a complete `~/.claude/` configuration for a new machine or user:

```bash
node ~/.claude/skills/claude-tracker-search/scripts/bootstrap-claude-setup.js --user "Name" --dry-run
node ~/.claude/skills/claude-tracker-search/scripts/bootstrap-claude-setup.js --user "Name"
```

This creates the directory structure, global CLAUDE.md, userModel template, agent_docs stubs, and project CLAUDE.md scaffolds.

**After bootstrap, activate `/claude-md-manager`** to enrich the generated files:
1. Run bootstrap to create the skeleton
2. Activate the `claude-md-manager` skill (`/claude-md-manager`) to apply the WHAT/WHY/HOW framework to each project CLAUDE.md
3. For each project missing a CLAUDE.md, use `claude-md-manager` to analyze the project and generate a proper CLAUDE.md
4. For the global CLAUDE.md, use `claude-md-manager` to refine it based on user preferences

**For the userModel**, conduct an interview with the user:
1. Bootstrap creates `~/.claude/userModels/userModel.md` with a template
2. Ask the user about their persona, worldview, intellectual style, communication preferences, research domains, and working patterns
3. Fill in the template based on their answers
4. The userModel evolves naturally across sessions as Claude learns more

### 6. Update Active Projects Doc

```bash
python3 ~/.claude/scripts/update-active-projects.py
```

Scans all project directories, reads session titles, generates llama-cli summaries for untitled sessions, and writes `~/.claude/agent_docs/active-projects.md`.

## Workflow: Find and Resume

1. Run `claude-tracker-search` with the user's query
2. Present matching sessions with summaries and resume commands
3. If the user wants to update docs, run `python3 ~/.claude/scripts/update-active-projects.py`

## Workflow: New Machine / New User Setup

1. Run `bootstrap-claude-setup.js --user "Name"` to create skeleton
2. Activate `/claude-md-manager` to enrich the global CLAUDE.md
3. Run `detect-projects.js --suggest` to find projects to add
4. For each project, activate `/claude-md-manager` to create rich CLAUDE.md
5. Interview the user to populate `userModel.md`
6. Commit: `cd ~/.claude && git add -A && git commit -m "Initial setup"`

## Data Sources

| Source | Location | Content |
|--------|----------|---------|
| Session index | `~/.claude/projects/*/sessions-index.json` | Summary, firstPrompt, sessionId, timestamps, branch |
| Summary cache | `~/.claude/session-summaries.json` | llama-cli generated titles/summaries |
| Session files | `~/.claude/projects/*/*.jsonl` | Full conversation transcripts |
| Active projects | `~/.claude/agent_docs/active-projects.md` | Curated project list with sessions |

## Shared Library

All tracker scripts use `~/.claude/lib/tracker-utils.js` for:
- `loadSessionsIndex()` — Load all sessions-index.json into flat array
- `loadSummaryCache()` — Load cached llama-cli summaries
- `decodeProjectPath()` — Convert encoded dir names back to real paths
- `getAllSessionFiles()` — List all session JSONL files
- `parseSession()` — Parse individual JSONL for messages/metadata
- `formatAge()` — Human-readable time formatting
