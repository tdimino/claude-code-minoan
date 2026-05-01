# Slack

The Slack integration skill. Gives Claude Code full read/write access to Slack workspaces through 9 on-demand Python scripts, dual-token architecture, RTS API search, chat streaming, AI Block Kit components, a Session Bridge, and a Claudicle unified launcher.

**Last updated:** 2026-05-01

**Reflects:** Slack Web API (including RTS API, chat streaming, AI Block Kit — Q4 2025/Q1 2026), Socket Mode, Bolt SDK patterns, and the Session Bridge architecture from [Claudicle](https://github.com/tdimino/claudicle).

---

## Why This Skill Exists

Claude Code can't talk to Slack out of the box. This skill bridges that gap with three complementary approaches: standalone scripts for discrete operations, a Session Bridge for real-time responses using the current session, and a unified launcher for persistent multi-channel operation via the Claude Agent SDK.

---

## What's New (May 2026)

- **Dual-token architecture**: Bot token (`xoxb-`) for standard operations, optional user token (`xoxp-`) for workspace-wide legacy search. Existing callers work unchanged.
- **RTS API search**: Unified search across messages, files, channels, and users via `assistant.search.context` (Feb 2026+). Auto-detects availability, falls back to legacy `search.messages`/`search.files`.
- **Chat streaming**: Real-time streaming responses via `chat.startStream`/`chat.appendStream`/`chat.stopStream`. Available as a standalone script and integrated into the unified launcher.
- **AI Block Kit**: Feedback buttons (thumbs up/down) on bot responses. Available via `--ai` flag on `slack_post.py` and in the daemon's `post_ai()` method.
- **`channels:join` scope**: Bot can join public channels programmatically. Includes `--join-all-public` bulk command.

---

## Structure

```
slack/
  SKILL.md                                 # Usage guide and setup instructions
  README.md                                # This file
  assets/
    app-icon.png                           # Slack app icon
  references/
    daemon-architecture.md                 # Soul engine, memory tiers, App Home
    onboarding-guide.md                    # First-time setup walkthrough
    rate-limits.md                         # Slack API rate limit reference
    scripts-reference.md                   # Detailed script documentation
    session-bridge.md                      # Session Bridge architecture
    unified-launcher-architecture.md       # Terminal + Slack unified process
  scripts/
    _slack_utils.py                        # Shared utilities (auth, dual-token, rate limits)
    slack_post.py                          # Post messages, threads, AI blocks
    slack_read.py                          # Read channel/thread history
    slack_search.py                        # Search via RTS API + legacy fallback
    slack_stream.py                        # Stream messages in real-time
    slack_react.py                         # Add/remove emoji reactions
    slack_upload.py                        # Upload files to channels
    slack_channels.py                      # List, join, bulk-join channels
    slack_users.py                         # Look up user profiles
    slack_format.py                        # Soul formatter (perception/extract/narrate)
    slack_check.py                         # Check inbox for unhandled messages
    slack_inbox_hook.py                    # UserPromptSubmit hook for auto-check
    slack_app_home.py                      # Build + publish App Home tab
    slack_memory.py                        # CLI for three-tier memory system
    slack_delete.py                        # Delete messages (single, batch, thread)
    test_slack.py                          # Integration tests
    test_channels.py                       # Channel listing tests
  daemon/
    claudicle.py                           # Unified launcher (terminal + Slack)
    slack_adapter.py                       # Socket Mode event handling
    slack_listen.py                        # Session Bridge background listener
    claude_handler.py                      # Claude invocation (subprocess + SDK async + streaming)
    soul_engine.py                         # Cognitive prompt wrapping + XML parsing
    working_memory.py                      # Per-thread metadata store
    user_models.py                         # Per-user personality profiles
    soul_memory.py                         # Global soul state
    session_store.py                       # Thread → session ID mapping
    config.py                              # All settings (env var overrides)
    terminal_ui.py                         # Async terminal input + activity log
    bot.py                                 # Legacy standalone daemon (fallback)
    monitor.py                             # Soul Monitor TUI (Textual)
```

---

## Architectures

| Approach | When to Use | How It Works |
|----------|------------|--------------|
| **On-demand scripts** | Discrete operations (post, read, search, stream) | Run script, get result, done |
| **Session Bridge** | Real-time responses with full tool access | Background listener + inbox.jsonl + current session |
| **Unified Launcher** | Persistent multi-channel bot with soul engine | Single process, Agent SDK, per-channel sessions |

### Session Bridge

```
Slack @mention/DM
       |
       v
  Background listener (slack_listen.py --bg)
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

No extra API costs. The listener watches for unhandled messages and writes them to `inbox.jsonl`. The hook surfaces new messages for processing.

### Unified Launcher

Single process handles terminal and Slack interactions with per-channel session isolation via the Claude Agent SDK. Supports streaming responses (when soul engine is off) and AI Block Kit feedback buttons.

```bash
python3 daemon/claudicle.py                            # terminal + Slack
SLACK_DAEMON_STREAMING=true python3 daemon/claudicle.py  # with streaming
```

---

## Scripts

All scripts authenticate via `SLACK_BOT_TOKEN`. Optional `SLACK_USER_TOKEN` enables workspace-wide legacy search.

| Script | Purpose | Example |
|--------|---------|---------|
| `slack_post.py` | Post messages, threads, AI blocks | `slack_post.py "#general" "Hello"` |
| `slack_read.py` | Read channel or thread history | `slack_read.py "#general" -n 20` |
| `slack_search.py` | Search via RTS API + legacy fallback | `slack_search.py "deploy" --rts --type channels` |
| `slack_stream.py` | Stream messages in real-time | `slack_stream.py "#general" "Streaming..."` |
| `slack_react.py` | Add/remove emoji reactions | `slack_react.py "#general" TS thumbsup` |
| `slack_upload.py` | Upload files to channels | `slack_upload.py "#general" report.pdf` |
| `slack_channels.py` | List, join, bulk-join channels | `slack_channels.py --join-all-public` |
| `slack_users.py` | Look up user profiles | `slack_users.py --email user@co.com` |
| `slack_delete.py` | Delete messages (single/batch/thread) | `slack_delete.py "#ch" TS1 TS2` |
| `slack_check.py` | Check inbox for unhandled messages | `slack_check.py [--ack 1]` |

### Utilities

| File | Purpose |
|------|---------|
| `_slack_utils.py` | Shared auth, dual-token routing, channel resolution, rate limits |
| `slack_format.py` | Soul formatter (perception framing, dialogue extraction, monologue logging) |
| `slack_inbox_hook.py` | UserPromptSubmit hook for automatic inbox checking |
| `slack_app_home.py` | Build + publish App Home tab via Block Kit |
| `slack_memory.py` | CLI wrapper for three-tier memory system |

---

## Setup

1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Enable **Socket Mode** and generate an App-Level Token (`xapp-...`)
3. Add Bot Token Scopes:
   - `app_mentions:read`
   - `channels:history`, `groups:history`, `im:history`, `mpim:history`
   - `channels:read`, `groups:read`, `im:read`, `im:write`
   - `channels:join`
   - `chat:write`
   - `files:write`, `files:read`
   - `reactions:write`, `reactions:read`
   - `search:read`
   - `search:read.public`, `search:read.private`, `search:read.im`, `search:read.mpim`, `search:read.files`, `search:read.users` (RTS API)
   - `users:read`, `users:read.email`
   - `users:write` (optional—green presence dot)
4. Subscribe to Bot Events: `app_mention`, `message.im`, `app_home_opened`
5. Install to workspace, copy Bot Token (`xoxb-...`)
6. Set environment variables:
   ```bash
   export SLACK_BOT_TOKEN="xoxb-..."
   export SLACK_APP_TOKEN="xapp-..."
   export SLACK_USER_TOKEN="xoxp-..."  # optional, for legacy workspace-wide search
   ```

See `references/onboarding-guide.md` for the full walkthrough.

---

## Related Skills

- **`slack-respond`**: Processes unhandled Slack messages through a cognitive pipeline with soul state and persistent memory. Uses these scripts for I/O.
- **[Claudicle](https://github.com/tdimino/claudicle)**: The soul agent framework that provides the unified launcher and daemon architecture.

---

## Requirements

- Python 3.10+
- `requests` (`uv pip install --system requests`)
- `slack_bolt`, `slack_sdk` (for Session Bridge / daemon)
- `claude-agent-sdk` (for unified launcher only)
- Slack Bot Token + App Token (Socket Mode)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/slack ~/.claude/skills/
```
