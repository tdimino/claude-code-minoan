# cmux CLI Reference

cmux (Manaflow AI) is a native macOS terminal app built on libghostty (Swift/AppKit, AGPL-3.0).
Binary: `/Applications/cmux.app/Contents/Resources/bin/cmux`
Repo: `manaflow-ai/cmux`

## Hierarchy

```
Window → Workspace (sidebar tab) → Pane (split region) → Surface (tab within pane)
```

| Level | UI Element | Created By | ID Format |
|-------|-----------|------------|-----------|
| Window | macOS window | `cmux new-window` / `Cmd+Shift+N` | window:N |
| Workspace | Sidebar entry | `cmux new-workspace` / `Cmd+N` | workspace:N |
| Pane | Split region | `cmux new-split <dir>` / `Cmd+D` | pane:N |
| Surface | Tab within pane | `cmux new-surface` / `Cmd+T` | surface:N |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CMUX_WORKSPACE_ID` | Auto-set in cmux terminals. Default `--workspace` for all commands |
| `CMUX_SURFACE_ID` | Auto-set in cmux terminals. Default `--surface` |
| `CMUX_TAB_ID` | Optional alias for `tab-action`/`rename-tab` default |
| `CMUX_SOCKET_PATH` | Override Unix socket path (default: `~/Library/Application Support/cmux/cmux.sock`) |
| `CMUX_SOCKET_PASSWORD` | Socket auth (fallback from `--password` flag) |

## ID Formats

Commands accept UUIDs, short refs (`window:1`, `workspace:2`, `pane:3`, `surface:4`), or indexes.
`tab-action` also accepts `tab:<n>`.
Output defaults to refs; pass `--id-format uuids` or `--id-format both` for UUIDs.

## Windows

```bash
cmux new-window
cmux list-windows
cmux current-window
cmux focus-window --window <id>
cmux close-window --window <id>
cmux rename-window [--workspace <id>] <title>
cmux next-window
cmux previous-window
cmux last-window
cmux find-window [--content] [--select] <query>
```

## Workspaces

```bash
cmux new-workspace [--cwd <path>] [--command <text>]
cmux list-workspaces
cmux current-workspace
cmux select-workspace --workspace <id|ref>
cmux close-workspace --workspace <id|ref>
cmux rename-workspace [--workspace <id>] <title>
cmux move-workspace-to-window --workspace <id|ref> --window <id|ref>
cmux reorder-workspace --workspace <id|ref|index> (--index <n> | --before <id> | --after <id>) [--window <id>]
cmux workspace-action --action <name> [--workspace <id>] [--title <text>]
```

## Splits & Panes

```bash
# Create splits
cmux new-split <left|right|up|down> [--workspace <id>] [--surface <id>] [--panel <id>]
cmux new-pane [--type <terminal|browser>] [--direction <left|right|up|down>] [--workspace <id>] [--url <url>]

# Navigate
cmux list-panes [--workspace <id>]
cmux focus-pane --pane <id|ref> [--workspace <id>]
cmux last-pane [--workspace <id>]

# Manage
cmux resize-pane --pane <id|ref> [--workspace <id>] (-L|-R|-U|-D) [--amount <n>]
cmux swap-pane --pane <id|ref> --target-pane <id|ref> [--workspace <id>]
cmux break-pane [--workspace <id>] [--pane <id>] [--surface <id>] [--no-focus]
cmux join-pane --target-pane <id|ref> [--workspace <id>] [--pane <id>] [--surface <id>] [--no-focus]

# Panels
cmux list-panels [--workspace <id>]
cmux focus-panel --panel <id|ref> [--workspace <id>]
```

### 4-Quadrant Layout Recipe

```bash
cmux new-split right        # Split into left/right
cmux new-split down          # Split right pane into top-right/bottom-right
cmux focus-pane --pane pane:1
cmux new-split down          # Split left pane into top-left/bottom-left
```

## Surfaces (Tabs Within Panes)

```bash
cmux new-surface [--type <terminal|browser>] [--pane <id>] [--workspace <id>] [--url <url>]
cmux list-pane-surfaces [--workspace <id>] [--pane <id>]
cmux close-surface [--surface <id>] [--workspace <id>]
cmux move-surface --surface <id> [--pane <id>] [--workspace <id>] [--window <id>] [--before <id>] [--after <id>] [--index <n>] [--focus <bool>]
cmux reorder-surface --surface <id> (--index <n> | --before <id> | --after <id>)
cmux drag-surface-to-split --surface <id|ref> <left|right|up|down>

# Tab actions
cmux tab-action --action <name> [--tab <id>] [--surface <id>] [--workspace <id>] [--title <text>] [--url <url>]
cmux rename-tab [--workspace <id>] [--tab <id>] [--surface <id>] <title>
```

## Input

```bash
# Send text to terminal
cmux send [--workspace <id>] [--surface <id>] <text>
cmux send-key [--workspace <id>] [--surface <id>] <key>

# Send to panel
cmux send-panel --panel <id|ref> [--workspace <id>] <text>
cmux send-key-panel --panel <id|ref> [--workspace <id>] <key>
```

**Common pattern — run a command in a new tab:**
```bash
SURFACE=$(cmux new-surface --type terminal | grep -o 'surface:[0-9]*')
cmux send --surface "$SURFACE" "cd /path && some-command"
cmux send-key --surface "$SURFACE" enter
cmux rename-tab --surface "$SURFACE" "My Tab"
```

## Screen Reading

```bash
cmux read-screen [--workspace <id>] [--surface <id>] [--scrollback] [--lines <n>]
cmux capture-pane [--workspace <id>] [--surface <id>] [--scrollback] [--lines <n>]
cmux clear-history [--workspace <id>] [--surface <id>]
```

**Note:** `read-screen` fails with "Surface is not a terminal" on browser surfaces.

## Browser Pane

```bash
cmux browser open [url]                    # Create browser split
cmux browser open-split [url]
cmux browser goto|navigate <url> [--snapshot-after]
cmux browser back|forward|reload [--snapshot-after]
cmux browser url|get-url
cmux browser snapshot [--interactive|-i] [--cursor] [--compact] [--max-depth <n>] [--selector <css>]
cmux browser eval <script>
cmux browser wait [--selector <css>] [--text <text>] [--url-contains <text>] [--load-state <state>] [--function <js>] [--timeout-ms <ms>]
cmux browser click|dblclick|hover|focus|check|uncheck|scroll-into-view <selector> [--snapshot-after]
cmux browser type <selector> <text> [--snapshot-after]
cmux browser fill <selector> [text] [--snapshot-after]
cmux browser press|keydown|keyup <key> [--snapshot-after]
cmux browser select <selector> <value> [--snapshot-after]
cmux browser scroll [--selector <css>] [--dx <n>] [--dy <n>] [--snapshot-after]
cmux browser screenshot [--out <path>] [--json]
cmux browser get <url|title|text|html|value|attr|count|box|styles> [...]
cmux browser is <visible|enabled|checked> <selector>
cmux browser find <role|text|label|placeholder|alt|title|testid|first|last|nth> ...
cmux browser frame <selector|main>
cmux browser dialog <accept|dismiss> [text]
cmux browser download [wait] [--path <path>] [--timeout-ms <ms>]
cmux browser cookies <get|set|clear> [...]
cmux browser storage <local|session> <get|set|clear> [...]
cmux browser tab <new|list|switch|close|<index>> [...]
cmux browser console <list|clear>
cmux browser errors <list|clear>
cmux browser highlight <selector>
cmux browser state <save|load> <path>
cmux browser addinitscript <script>
cmux browser addscript <script>
cmux browser addstyle <css>
cmux browser identify [--surface <id>]
```

## Sidebar Metadata

```bash
cmux set-status <key> <value> [--icon <name>] [--color <#hex>] [--workspace <id>]
cmux clear-status <key> [--workspace <id>]
cmux list-status [--workspace <id>]
cmux set-progress <0.0-1.0> [--label <text>] [--workspace <id>]
cmux clear-progress [--workspace <id>]
cmux log [--level <level>] [--source <name>] [--workspace <id>] [--] <message>
cmux clear-log [--workspace <id>]
cmux list-log [--limit <n>] [--workspace <id>]
cmux sidebar-state [--workspace <id>]
```

Log levels: `error`, `info`, `success`, `warning`, `progress`

## Notifications

```bash
cmux notify --title <text> [--subtitle <text>] [--body <text>] [--workspace <id>] [--surface <id>]
cmux list-notifications
cmux clear-notifications
```

## Clipboard / Buffers

```bash
cmux set-buffer [--name <name>] <text>
cmux list-buffers
cmux paste-buffer [--name <name>] [--workspace <id>] [--surface <id>]
```

## Markdown Viewer

```bash
cmux markdown open <path>    # Formatted viewer panel with live reload
```

## Claude Integration

```bash
cmux claude-teams [claude-args...]
cmux claude-hook <session-start|stop|notification> [--workspace <id>] [--surface <id>]
```

## Utility

```bash
cmux ping                                    # Check if running
cmux version
cmux capabilities
cmux identify [--workspace <id>] [--surface <id>] [--no-caller]
cmux tree [--all] [--workspace <id>]         # Full hierarchy view
cmux refresh-surfaces
cmux surface-health [--workspace <id>]
cmux trigger-flash [--workspace <id>] [--surface <id>]
cmux respawn-pane [--workspace <id>] [--surface <id>] [--command <cmd>]
cmux display-message [-p|--print] <text>
cmux set-app-focus <active|inactive|clear>
```

## Hooks

```bash
cmux set-hook <event> <command>
cmux set-hook --list
cmux set-hook --unset <event>
```

## tmux Compatibility

```bash
cmux capture-pane    # alias for read-screen
cmux pipe-pane --command <shell-command> [--workspace <id>] [--surface <id>]
cmux wait-for [-S|--signal] <name> [--timeout <seconds>]
cmux popup
cmux bind-key | unbind-key | copy-mode
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New workspace | `Cmd+N` |
| New window | `Cmd+Shift+N` |
| Split right | `Cmd+D` |
| Split down | `Cmd+Shift+D` |
| New surface (tab) | `Cmd+T` |
| Navigate panes | `Opt+Cmd+Arrow` |
| Jump to workspace 1-9 | `Cmd+1` through `Cmd+9` |
| Navigate surfaces | `Cmd+[` / `Cmd+]` or `Ctrl+1-9` |
| Close workspace | `Cmd+Shift+W` |
| Prev/next workspace | `Cmd+Shift+[` / `Cmd+Shift+]` |

## Socket API

All commands available via Unix domain socket. Send newline-terminated JSON:

```json
{"id":"req-1","method":"workspace.list","params":{}}
{"id":"req-2","method":"surface.split","params":{"direction":"right"}}
```

Default socket: `~/Library/Application Support/cmux/cmux.sock`
