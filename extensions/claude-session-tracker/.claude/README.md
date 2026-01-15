# Claude Code Commands

Slash commands for browsing and searching Claude Code sessions from within Claude Code.

## Installation

Copy commands to your Claude config:

```bash
cp -r commands/* ~/.claude/commands/
```

Or run the setup script:

```bash
../scripts/install-commands.sh
```

## Commands

| Command | Description |
|---------|-------------|
| `/claude-tracker` | List 20 most recent sessions across all projects |
| `/claude-tracker-here` | List sessions for current directory only |
| `/claude-tracker-search <term>` | Search all sessions for a keyword |

## Usage Examples

```
/claude-tracker                    # See all recent sessions
/claude-tracker-here               # Sessions for this project
/claude-tracker-search websocket   # Find sessions mentioning "websocket"
```

## Output

Each session shows:
- Project name and path
- Git branch (if available)
- Last active time
- Session ID (for `claude --resume`)
- Last 2-3 user messages
