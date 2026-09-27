# claude-peers

Peer discovery, messaging, and lifecycle management for AI coding agents on the same machine. Enables Claude Code and Codex CLI sessions to find each other, exchange messages, and manage session lifecycles through a shared broker daemon. When a message arrives, the broker **wakes the recipient natively** instead of relying on polling, so no agent has to promise to "check back later".

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
                        SQLite (~/.claude/claude-peers.db, 0600)
                                        |
                  on send_message: wake the recipient with a fixed nudge
                 ┌──────────────────────┴──────────────────────┐
     Claude inbox socket                                 codex queue
  (CLAUDE_CODE_MESSAGING_SOCKET)                  --thread <session_id>
```

Recipients read the message with `check_messages`, which is the only place a message is acknowledged. Turn-boundary hooks (`hooks/peers-hook.ts`) catch any wake that fails.

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_peers` | Discover other agents (scope: machine/directory/repo), with wake transport and last wake status |
| `send_message` | Send a message to a peer by ID; reports whether the recipient's wake was queued |
| `set_summary` | Set a summary visible to other peers |
| `check_messages` | Read and acknowledge messages; call it whenever a wake nudge arrives |
| `kill_peer` | Terminate a stuck peer's agent session (SIGTERM to parent) |

## Delivery

| Client | Wake | Idle | Busy | Sandbox |
|--------|------|------|------|---------|
| `claude-code` (v2.1.224+) | Inbox socket, registered by the MCP server | Starts a turn | Read between tool calls | No restrictions |
| `codex` | `codex queue`, thread registered by a Codex hook | Starts a turn | After the current turn | Requires `danger-full-access` |
| `claude-code` (older) | `claude/channel` push (needs `--dangerously-load-development-channels`) | Pushed | Pushed | No restrictions |
| `cli` | none | — | — | Unsandboxed |

The nudge never carries the message body: `[claude-peers] New message from <peer> (<client>, <dir>). Call check_messages to read and reply.` One wake covers a batch of unread messages; an unanswered wake re-arms after 5 minutes. Unread messages survive an MCP server restart (they move to the agent's new server) and outlive their sender.

## Hooks

| Event | Claude Code | Codex | Behavior while messages are unread |
|-------|:-----------:|:-----:|------------------------------------|
| `Stop` | ✓ | ✓ | Block finishing once, asking the agent to call `check_messages` and reply |
| `PreToolUse` (Bash) | ✓ | ✓ | Before `git add/commit/push`, add a non-blocking reminder to check peer messages |
| `UserPromptSubmit` | ✓ | ✓ | Add the unread count as context; Codex also re-registers its thread |
| `SessionStart` | — | ✓ | Register the Codex thread ID for `codex queue` |

The hook fails open (never blocks on its own errors) and logs quiet failures to `~/.claude/run/claude-peers-hook.log`.

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
        <key>CLAUDE_PEERS_DB</key>
        <string>/Users/you/.claude/claude-peers.db</string>
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

The broker finds `codex` for `codex queue` on its own `PATH` plus `/opt/homebrew/bin` and `/usr/local/bin`; set `CLAUDE_PEERS_CODEX_BIN` if it lives elsewhere.

### Add the hooks to Claude Code

In `~/.claude/settings.json`, add this handler to the `Stop` and `UserPromptSubmit` groups and to the `PreToolUse` group whose matcher is `Bash`:

```json
{
  "type": "command",
  "command": "/path/to/bun /path/to/claude-peers-mcp/hooks/peers-hook.ts --harness claude",
  "timeout": 5
}
```

### Add the hooks to Codex CLI

In `~/.codex/hooks.json`, add the same handler with `--harness codex` under `SessionStart` (matcher `startup|resume`), `UserPromptSubmit`, `Stop`, and `PreToolUse` (matcher `^Bash$`). Then run `/hooks` in Codex and trust the entries; Codex skips untrusted hooks, and without `SessionStart` the thread is never registered for wakes.

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
| `CLAUDE_PEERS_DB` | `~/.claude-peers.db` | SQLite database path (the launchd plist sets `~/.claude/claude-peers.db`) |
| `CLAUDE_PEERS_TCP` | unset | Set to `1` to enable TCP fallback (port 7899) |
| `CLAUDE_PEERS_URL` | unset | Client TCP override (e.g., `http://127.0.0.1:7899`) |
| `CLAUDE_PEERS_CODEX_BIN` | `codex` on PATH + Homebrew | Binary used for `codex queue` wakes |
| `CLAUDE_PEERS_INBOX_TIMEOUT_MS` | `2000` | Claude inbox write timeout |
| `CLAUDE_PEERS_CODEX_TIMEOUT_MS` | `10000` | `codex queue` timeout |
| `CLAUDE_PEERS_WAKE_REARM_MS` | `300000` | Re-arm an unanswered wake after this long |
| `CLAUDE_PEERS_SWEEP_MS` | `30000` | Stale-peer sweep interval |
| `CLAUDE_PEERS_HOOK_LOG` | `~/.claude/run/claude-peers-hook.log` | Hook quiet-failure log |

## Tests

```bash
cd ~/tools/claude-peers-mcp && bun test   # broker (spawned against a temp DB/socket) + hook
```

## Transport

The broker uses a Unix domain socket instead of TCP because Codex CLI's macOS seatbelt sandbox blocks TCP `connect()` to localhost from sandboxed child processes. Unix socket `connect()` is allowed by both Codex and Claude Code sandboxes when the broker runs as an unsandboxed launchd daemon.

Claude Code's own inbox socket and `codex queue` were verified on 2026-09-27 (Claude Code 2.1.283, codex-cli 0.157.1): both wake an idle session, and a live Claude-to-Codex-to-Claude round trip completed without polling or the development-channels flag.

**Note:** Codex's `workspace-write` sandbox currently also blocks Unix socket `connect()`. Codex sessions require `--dangerously-bypass-approvals-and-sandbox` or `danger-full-access` sandbox mode. This is tracked at Codex issue #11095.

## License

MIT
