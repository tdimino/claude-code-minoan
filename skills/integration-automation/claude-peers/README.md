# claude-peers

Peer discovery, messaging, and lifecycle management for AI coding agents on the same machine. Enables Claude Code and Codex CLI sessions to find each other, exchange messages, and manage session lifecycles through a shared broker daemon.

## Architecture

```
                     Unix socket (~/.claude/run/claude-peers.sock)
                                        |
  ┌─────────────────────────────────────┼───────────────────────────────┐
  |                                     |                               |
Claude Code MCP              Codex MCP                           CLI tool
  fetch({ unix })            fetch({ unix })                 fetch({ unix })
                                        |
                                  Broker daemon
                                (launchd, unsandboxed)
                               Bun.serve({ unix })
                             SQLite (~/.claude-peers.db)
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_peers` | Discover other agents (scope: machine/directory/repo) |
| `send_message` | Send a message to a peer by ID |
| `set_summary` | Set a summary visible to other peers |
| `check_messages` | Poll for new messages (required for Codex; Claude Code gets push) |
| `kill_peer` | Terminate a stuck peer's agent session (SIGTERM to parent) |

## Client Types

| Client | Push | Delivery | Sandbox |
|--------|------|----------|---------|
| `claude-code` | Yes (`claude/channel`) | Instant push | No restrictions |
| `codex` | No | Poll via `check_messages` | Requires `danger-full-access` |
| `cli` | No | Manual | Unsandboxed |

## Setup

### Prerequisites

- [Bun](https://bun.sh) 1.2+
- macOS (Unix domain socket transport)

### Install

```bash
# Copy the MCP server to your tools directory
cp -r mcp-server ~/tools/claude-peers-mcp

# Install dependencies
cd ~/tools/claude-peers-mcp && bun install

# Create the socket directory
mkdir -p ~/.claude/run
```

### Configure the Broker Daemon

Create `~/Library/LaunchAgents/com.minoan.claude-peers-broker.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.minoan.claude-peers-broker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/bun</string>
        <string>/path/to/claude-peers-mcp/broker.ts</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>~/.claude/logs/claude-peers-broker.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

Load it:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.minoan.claude-peers-broker.plist
```

### Add MCP to Claude Code

In `~/.claude/settings.json` under `mcpServers`:

```json
"claude-peers": {
  "command": "/path/to/bun",
  "args": ["/path/to/claude-peers-mcp/server.ts"]
}
```

### Add MCP to Codex CLI

In `~/.codex/config.toml`:

```toml
[mcp_servers.claude-peers]
command = "/path/to/bun"
args = ["/path/to/claude-peers-mcp/server.ts", "--client-type", "codex"]
```

## CLI

```bash
bun cli.ts status        # Broker health + all peers with [type] tags
bun cli.ts peers         # Quick peer listing
bun cli.ts send <id> <msg>  # Send message (tagged as unverified)
bun cli.ts kill <id>     # Kill a peer's agent session
bun cli.ts kill-broker   # Stop the broker daemon
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_PEERS_SOCKET` | `~/.claude/run/claude-peers.sock` | Unix socket path |
| `CLAUDE_PEERS_DB` | `~/.claude-peers.db` | SQLite database path |
| `CLAUDE_PEERS_TCP` | unset | Set to `1` to enable TCP fallback (port 7899) |
| `CLAUDE_PEERS_URL` | unset | Client TCP override (e.g., `http://127.0.0.1:7899`) |

## Transport

The broker uses a Unix domain socket instead of TCP because Codex CLI's macOS seatbelt sandbox blocks TCP `connect()` to localhost from sandboxed child processes. Unix socket `connect()` is allowed by both Codex and Claude Code sandboxes when the broker runs as an unsandboxed launchd daemon.

**Note:** Codex's `workspace-write` sandbox currently also blocks Unix socket `connect()`. Codex sessions require `--dangerously-bypass-approvals-and-sandbox` or `danger-full-access` sandbox mode. This is tracked at Codex issue #11095.

## License

MIT
