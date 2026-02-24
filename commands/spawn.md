---
allowed-tools: Bash(~/.claude/skills/claude-tracker-suite/scripts/new-session.sh*)
---

# Spawn Session

Start a new Claude Code session in a terminal tab or run a headless prompt.

## Arguments

$ARGUMENTS

## Instructions

Run the new-session script with the provided arguments:

```bash
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh $ARGUMENTS
```

If no project path is given, use the current working directory.

**Examples:**
- `/spawn ~/my-project` — Interactive session in Ghostty
- `/spawn ~/my-project --prompt "fix the tests"` — Prompt-driven in Ghostty tab
- `/spawn ~/my-project --headless --prompt "summarize"` — Headless JSON output
- `/spawn ~/my-project --vscode --model opus` — Interactive in VS Code
