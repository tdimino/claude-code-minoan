# Scripts Index

*9 utility scripts in `~/.claude/scripts/` — standalone tools, not hook-bound*

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
| `screenshot-rename/` | macOS launchd service for auto-renaming screenshots with AI-generated descriptions |
