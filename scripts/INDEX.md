# Scripts Index

*14 utility scripts in `~/.claude/scripts/` — standalone tools, not hook-bound*

## Plugin Management

| Script | Description |
|--------|-------------|
| `claude-plugins.py` | Plugin profile manager — switches between plugin sets to keep total agents under the ~40 limit |
| `plugin-profiles.json` | Profile definitions (soul, compound, lean) |

## Session Browsing

| Script | Description |
|--------|-------------|
| `cc-sessions.sh` | Session history viewer with auto-categorization |
| `cc-sessions-fzf.sh` | Interactive session picker with fzf + tmux integration |
| `cc-sessions-ui.py` | Visual TUI for browsing and resuming sessions |

## Maintenance

| Script | Description |
|--------|-------------|
| `update-active-projects.py` | Auto-update `agent_docs/active-projects.md` from session and plan data |
| `batch-rename-plans.py` | One-time batch rename of randomly-named plan files to dated slugs |

## Subdirectories

| Directory | Description |
|-----------|-------------|
| `clean-browser-screenshot/` | Take browser screenshots with no toolbar or UI chrome via CleanShot X fullscreen capture |
| `cpu-watchdog/` | **phroura** — launchd daemon detecting runaway processes (>90% CPU sustained), alerts via `alerter` + Telegram, Claude session enrichment (session ID, revoked FDs) |
| `screenshot-rename/` | macOS launchd service for auto-renaming screenshots with AI-generated descriptions |
| `syspeek/` | macOS system resource monitor — categorized processes, Kothar-compatible JSON, Claudicle memory integration, launchd daemon |
| `skill-audit/` | Skill freshness audit pipeline — `skill-audit.py` for local inventory/staleness report (80 skills, ANSI table + JSON), `skill-freshness.py` for automated Exa/Firecrawl upstream validation, `freshness-registry.yaml` for curated upstream metadata |
| `terminal-greeting/` | Illuminated-manuscript greeting for new shell sessions — random classical salutations, `print -z "claude"` buffer hint, ANSI gold/rose box art |
| `speculator/` | **speculator** — launchd daemon mapping Ghostty terminal tabs to running Claude Code sessions. Process-tree discovery (Ghostty → login children → TTYs → Claude PIDs → session metadata), enriched from soul registry, session summaries, tags, and git branches. JSON + Markdown snapshots every 5 minutes, synced to `agent_docs/ghostty-sessions.md`. Integrates with `claude-tracker-suite` via `tracker-utils.js` |
| `wterm-server/` | **wterm** — Node.js web terminal daimon (node-pty + @wterm/react). Browser-based shell access, deploy on any macOS machine. Deploys to `~/daimones/wterm-server/`, managed by `skills/wterm/` |
