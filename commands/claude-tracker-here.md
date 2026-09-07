# Claude Sessions for Current Directory

List Claude Code sessions whose project is the current working directory.

## Arguments

$ARGUMENTS

## Instructions

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/list-sessions.js --here $ARGUMENTS
```

Same render as `/claude-tracker`, filtered to this project: LIVE badge with TTY or INACTIVE, name, summary, slug, git remote and branch, last user message time, session ID, keywords, last 3 user messages.

Resume one in this terminal with `claude --resume <id|name>`, or in a new Ghostty tab with `~/.claude/scripts/ghostty-resume.sh <id>`.
