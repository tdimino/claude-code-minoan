# Claude Session Tracker

List recent Claude Code sessions with live status.

**Usage:**
- `/claude-tracker` — recent sessions across all projects
- `/claude-tracker --limit 5` — fewer
- `/claude-tracker --vscode` — only projects open in a VS Code workspace

## Arguments

$ARGUMENTS

## Instructions

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/list-sessions.js $ARGUMENTS
```

Each entry shows:
- **LIVE badge with TTY** (from Claude Code's own PID files, matched by session ID) or INACTIVE
- **Name** (the `-n` / auto name shown in the resume picker) and session summary
- **Session slug**, project path, git remote and branch, repos touched
- Last user message time, session ID, keywords, last 3 user messages

To bring a session back: `claude --resume <id|name>` in the right directory, or `~/.claude/scripts/ghostty-resume.sh <id>` for a new Ghostty tab. For crashed sessions use `/claude-tracker-resume` or `claude-tracker-resume --open`.
