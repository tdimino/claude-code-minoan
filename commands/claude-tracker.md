# Claude Session Tracker

List and browse your saved Claude Code sessions with status (running/inactive/VS Code).

**Usage:**
- `/claude-tracker` - Show all recent sessions
- `/claude-tracker vscode` - Show only sessions from VS Code workspaces (for crash recovery)

## Arguments

$ARGUMENTS

## Instructions

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/list-sessions.js $ARGUMENTS
```

Lists your most recent Claude sessions with:
- **Status badge** (RUNNING or INACTIVE)
- **VS CODE badge** (if open in VS Code)
- **Session summary** (AI-generated description)
- **Session name** (slug like "recursive-popping-hopcroft")
- Project name and path
- **Git remote** (primary repo URL)
- Git branch (if available)
- Last user message time
- Session ID (for `claude --resume`)
- **Keywords** extracted from conversation
- Last 3 user messages

**Crash Recovery Mode:** `/claude-tracker vscode`
- Shows only sessions from current VS Code workspaces
- Displays resume commands prominently for easy copy-paste
- Compact view focused on getting sessions back up

Running sessions detected via `lsof` checking for Claude processes.
VS Code status detected via `~/.claude/ide/*.lock` workspace folders.
