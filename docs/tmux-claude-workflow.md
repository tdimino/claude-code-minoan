# tmux + Claude Code Workflow Reference

Quick reference for tmux session management with Claude Code.

## Session Picker (`cc-pick`)

Interactive fzf-based session picker that combines Claude Code history with tmux status:

```bash
cc-pick          # Launch interactive picker
cc-pick 30       # Show last 30 sessions
```

**Features:**
- Shows Claude sessions with category tags (🐛 bug, ✨ feature, etc.)
- Indicates tmux status: 🟢 claude running, 🟡 tmux idle, ⚪ no tmux
- Preview pane with session details
- Direct resume into tmux

**Keybindings:**
| Key | Action |
|-----|--------|
| `Enter` | Resume session in tmux (creates/attaches + runs `claude --resume`) |
| `Ctrl-O` | Open project in VSCode/Cursor (copies resume command) |
| `Ctrl-T` | Attach to tmux session only (no Claude resume) |
| `Ctrl-Y` | Copy session ID to clipboard |
| `Esc` | Cancel |

## CLI Tools (`~/.local/bin/`)

| Command | Usage | Description |
|---------|-------|-------------|
| `cc` | `cc [name]` | Create/attach tmux session with Claude running |
| `ccls` | `ccls` | List sessions with status (🟢 claude / ⚪ idle) |
| `ccpick` | `ccpick` | Interactive fzf picker with live preview |
| `cckill` | `cckill` | Kill only idle sessions (preserves active Claude) |
| `ccnew` | `ccnew <path> [--ghostty\|--vscode\|--cursor] [--model <m>]` | Open new Claude session in project dir |
| `ccresume` | `ccresume <session-id> [--ghostty\|--vscode\|--cursor] [--project <path>]` | Resume session in Ghostty/VS Code/Cursor |

## Shell Aliases (`.zshrc`)

| Alias | Expands To | Description |
|-------|------------|-------------|
| `t` | `tmux` | Quick tmux access |
| `ta` | `tmux attach -t` | Attach to named session |
| `tn` | `tmux new -s` | Create new named session |
| `tls` | `tmux list-sessions` | List all sessions |
| `tk` | `tmux kill-session -t` | Kill named session |

## tmux Keybindings

**Prefix:** `Ctrl+A` (not default Ctrl+B, to avoid Claude Code conflict)

### Pane Mode (`Ctrl+P`, then...)

| Key | Action |
|-----|--------|
| `h` | Move left |
| `j` | Move down |
| `k` | Move up |
| `l` | Move right |
| `s` | Split horizontal (pane below) |
| `v` | Split vertical (pane right) |
| `x` | Kill pane |

### Tab Mode (`Ctrl+T`, then...)

| Key | Action |
|-----|--------|
| `n` | New window |
| `h` | Previous window |
| `l` | Next window |
| `x` | Kill window |
| `r` | Rename window |

### Popup Commands (prefix + key)

| Key | Action |
|-----|--------|
| `s` | Session picker (fzf popup) |
| `g` | Lazygit popup (90% screen) |

## Terminal Title Hook

When enabled, terminal titles show Claude status:
- 🔴 `project-name` — Claude is thinking
- 🟢 `project-name` — Ready for input

Also plays sound and sends desktop notification on completion.

## Crash Recovery

tmux sessions survive VSCode/Cursor crashes:

```bash
# After crash, just reattach
ccpick          # Interactive picker
# or
ta session-name # Direct attach
```

## Common Workflows

### Start new Claude session
```bash
cd ~/my-project
cc              # Creates session named "my-project" with Claude (tmux)

# Or open directly in Ghostty/VS Code/Cursor:
ccnew ~/my-project                      # Ghostty tab (default)
ccnew ~/my-project --vscode             # VS Code terminal
ccnew ~/my-project --model sonnet       # With model override
```

### Check what's running
```bash
ccls
# Output:
# my-project     🟢 claude  (Jan 18 12:30)
# other-project  ⚪ idle    (Jan 17 09:00)
```

### Clean up old sessions
```bash
cckill          # Offers to kill idle sessions only
```

### Quick session switch
```bash
# Inside tmux
Ctrl+A, s       # Opens fzf session picker popup
```

## Configuration Files

- **tmux config:** `~/.tmux.conf`
- **Claude hooks:** `~/.claude/settings.json`
- **Terminal title hook:** `~/.claude/hooks/terminal-title.sh`
- **CLI tools:** `~/.local/bin/cc`, `ccls`, `ccpick`, `cckill`, `ccnew`, `ccresume`
- **Session scripts:** `~/.claude/scripts/cc-sessions-fzf.sh`, `cc-sessions.sh`
- **New session launcher:** `~/.claude/skills/claude-tracker-suite/scripts/new-session.sh`

## Session History Scripts (`~/.claude/scripts/`)

| Script | Usage | Description |
|--------|-------|-------------|
| `cc-sessions-fzf.sh` | `cc-pick` | Interactive fzf picker with tmux integration |
| `cc-sessions.sh` | `cc-sessions [n]` | List last n sessions with categories |

## Reload Config

```bash
tmux source-file ~/.tmux.conf
```

## Troubleshooting

### fzf picker not showing data
```bash
# Check if history exists
ls -la ~/.claude/history.jsonl

# Test data extraction
jq -s 'length' ~/.claude/history.jsonl
```

### tmux session not detected
```bash
# List tmux sessions
tmux list-sessions

# Check session paths
tmux list-sessions -F "#{session_name}: #{pane_current_path}"
```

### Terminal title not updating
1. Verify hooks in `~/.claude/settings.json`
2. Check tmux passthrough: `set -g set-titles on` in `~/.tmux.conf`
3. Restart Claude for hooks to take effect
