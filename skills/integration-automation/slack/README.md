# Slack

The Slack integration skill. Gives Claude Code full read/write access to Slack workspaces through 7 on-demand Python scripts and a Session Bridge architecture that connects any running session to Slack in real time.

**Last updated:** 2026-02-18

**Reflects:** Slack Web API, Socket Mode, Bolt SDK patterns, and the Session Bridge architecture from [Claudicle](https://github.com/tdimino/claudicle).

---

## Why This Skill Exists

Claude Code can't talk to Slack out of the box. This skill bridges that gap with two complementary approaches: a set of standalone scripts for discrete operations (post a message, search channels, upload a file) and a Session Bridge that lets any Claude Code session receive and respond to Slack messages in real time---without spawning new processes or incurring extra API costs.

The scripts handle the common cases. The Session Bridge handles the hard case: keeping Claude Code's full tool access (file ops, web search, code editing) available when responding to Slack, rather than falling back to a stripped-down bot.

---

## Structure

```
slack/
  SKILL.md                                 # Usage guide and setup instructions
  README.md                                # This file
  assets/
    app-icon.png                           # Slack app icon
  references/
    daemon-architecture.md                 # Standalone daemon design (legacy)
    onboarding-guide.md                    # First-time setup walkthrough
    rate-limits.md                         # Slack API rate limit reference
    scripts-reference.md                   # Detailed script documentation
    session-bridge.md                      # Session Bridge architecture
    unified-launcher-architecture.md       # Terminal + Slack unified process
  scripts/
    _slack_utils.py                        # Shared utilities (auth, channels, formatting)
    slack_post.py                          # Post messages and threads
    slack_read.py                          # Read channel/thread history
    slack_search.py                        # Search messages across workspace
    slack_react.py                         # Add/remove emoji reactions
    slack_upload.py                        # Upload files to channels
    slack_channels.py                      # List and browse channels
    slack_users.py                         # Look up user profiles
    slack_format.py                        # Message formatting utilities
    slack_check.py                         # Check inbox for unhandled messages
    slack_inbox_hook.py                    # UserPromptSubmit hook for auto-check
    test_slack.py                          # Integration tests
    test_channels.py                       # Channel listing tests
```

---

## What It Covers

### Two Architectures

| Approach | When to Use | How It Works |
|----------|------------|--------------|
| **On-demand scripts** | Discrete operations (post, read, search) | Run script, get result, done |
| **Session Bridge** | Real-time responses with full tool access | Background listener + inbox.jsonl + current session |

The scripts are standalone---call them from any Claude Code session. The Session Bridge is an architecture pattern that keeps the current session connected to Slack without spawning new processes.

### Session Bridge

```
Slack @mention/DM
       |
       v
  Background listener (slack_check.py --watch)
       |
       v
  inbox.jsonl  <--- new message appended
       |
       v
  Current Claude Code session (via UserPromptSubmit hook)
       |
       v
  Process with full tool access → post response to Slack
```

No extra API costs. The listener watches for unhandled messages and writes them to `inbox.jsonl`. The `slack_inbox_hook.py` hook checks the inbox on each prompt submit and surfaces new messages for processing.

### Unified Launcher

For advanced use: a single process handles both terminal and Slack interactions, with per-channel session isolation via the Claude Agent SDK. See `references/unified-launcher-architecture.md`. This replaces the legacy per-message subprocess pattern.

---

## Scripts

All scripts authenticate via `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` environment variables.

| Script | Purpose | Example |
|--------|---------|---------|
| `slack_post.py` | Post messages and thread replies | `python3 slack_post.py -c general -m "Hello"` |
| `slack_read.py` | Read channel or thread history | `python3 slack_read.py -c general -n 20` |
| `slack_search.py` | Search messages across workspace | `python3 slack_search.py -q "deploy failed"` |
| `slack_react.py` | Add/remove emoji reactions | `python3 slack_react.py -c general -t 123.456 -e thumbsup` |
| `slack_upload.py` | Upload files to channels | `python3 slack_upload.py -c general -f report.pdf` |
| `slack_channels.py` | List and browse channels | `python3 slack_channels.py --public` |
| `slack_users.py` | Look up user profiles | `python3 slack_users.py -u U12345` |
| `slack_check.py` | Check inbox for unhandled messages | `python3 slack_check.py [--watch]` |

### Utilities

| File | Purpose |
|------|---------|
| `_slack_utils.py` | Shared auth, channel resolution, error handling |
| `slack_format.py` | Message formatting (markdown, blocks, attachments) |
| `slack_inbox_hook.py` | UserPromptSubmit hook for automatic inbox checking |

### Hook Integration

Add to `~/.claude/settings.json` to auto-check Slack on every prompt:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "command": "python3 ~/.claude/skills/slack/scripts/slack_inbox_hook.py"
    }]
  }
}
```

---

## Setup

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable **Socket Mode** and generate an App-Level Token (`xapp-...`)
3. Add Bot Token Scopes: `chat:write`, `channels:read`, `channels:history`, `groups:read`, `groups:history`, `im:read`, `im:history`, `reactions:write`, `files:write`, `search:read`, `users:read`
4. Install to workspace, copy Bot Token (`xoxb-...`)
5. Set environment variables:
   ```bash
   export SLACK_BOT_TOKEN="xoxb-..."
   export SLACK_APP_TOKEN="xapp-..."
   ```

See `references/onboarding-guide.md` for the full walkthrough.

---

## Related Skills

- **`slack-respond`**: Processes unhandled Slack messages through a cognitive pipeline with soul state and persistent memory. Uses these scripts for I/O.
- **[Claudicle](https://github.com/tdimino/claudicle)**: The soul agent framework that provides the unified launcher and daemon architecture.

---

## Requirements

- Python 3.9+
- `slack_sdk` (`pip install slack_sdk`)
- Slack Bot Token + App Token (Socket Mode)
- No additional dependencies for scripts

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/slack ~/.claude/skills/
```
