---
name: slack
description: "This skill should be used when interacting with a Slack workspace — posting messages, reading channels, searching, reacting, uploading files, managing channels/users, or running the Claudius daemon (pseudo soul engine with cognitive steps, three-tier memory, and cross-thread soul state). Provides 7 on-demand scripts and a persistent Socket Mode daemon."
---

# Slack Skill

Full Slack workspace integration: 7 Python scripts for on-demand operations + a Socket Mode daemon with a pseudo soul engine for persistent, personality-driven conversations.

## When to Use This Skill

### Scripts (on-demand)
- Posting messages to Slack channels or threads
- Reading channel history or thread replies
- Searching messages or files across the workspace
- Adding or managing reactions on messages
- Uploading files or code snippets
- Listing channels, getting channel info, or joining channels
- Looking up users by name, ID, or email

### Daemon (persistent)
- Responding to @mentions in real time as "Claudius, Artifex Maximus"
- Answering DMs sent to the bot
- Multi-turn conversations in threads (session continuity via SQLite)
- Per-user personality modeling (learns communication style, interests, expertise)
- Cross-thread soul state (tracks current project, task, topic, emotional state)
- Three-tier memory: working memory (per-thread), user models (per-user), soul memory (global)

## Prerequisites

All scripts require the `SLACK_BOT_TOKEN` environment variable (a Bot User OAuth Token starting with `xoxb-`). Scripts also require `requests` (`uv pip install --system requests`).

```bash
# Verify token is set
echo $SLACK_BOT_TOKEN
```

### First-Time Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App → From Scratch
2. Name it "Claude Code" → select your workspace
3. OAuth & Permissions → Bot Token Scopes → add:
   - `chat:write`
   - `channels:history`, `groups:history`, `im:history`, `mpim:history`
   - `channels:read`, `groups:read`, `im:read`, `im:write`
   - `search:read`
   - `reactions:write`, `reactions:read`
   - `files:write`, `files:read`
   - `users:read`, `users:read.email`
4. Install to Workspace → copy Bot User OAuth Token
5. `export SLACK_BOT_TOKEN=xoxb-...` (add to shell profile)
6. Invite the bot to channels: `/invite @Claude Code`

---

## Quick Start

```bash
# Post a message
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Hello from Claude"

# Read recent messages
python3 ~/.claude/skills/slack/scripts/slack_read.py "#general" -n 10

# Search the workspace
python3 ~/.claude/skills/slack/scripts/slack_search.py "deployment status"

# Start the daemon (must run from daemon directory for local imports)
cd ~/.claude/skills/slack/daemon && python3 bot.py --verbose
```

---

## Available Scripts

### 1. slack_post.py — Post Messages

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_post.py`

Post messages, reply to threads, schedule, update, and delete messages.

```bash
# Post to a channel
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Hello from Claude"

# Reply to a thread
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Thread reply" --thread 1234567890.123456

# Post with rich blocks
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Update" \
  --blocks '[{"type":"section","text":{"type":"mrkdwn","text":"*Bold heading*\nDetails here"}}]'

# Schedule a message
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Daily reminder" --schedule "2026-02-12T09:00:00"

# Update an existing message
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Corrected text" --update 1234567890.123456

# Delete a message
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" --delete 1234567890.123456

# Post with link unfurling
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Check: https://example.com" --unfurl
```

**Parameters**: `channel`, `text`, `--thread`, `--blocks`, `--schedule`, `--update`, `--delete`, `--unfurl`, `--json`

---

### 2. slack_read.py — Read Messages

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_read.py`

Read channel history and thread replies.

```bash
# Read recent messages
python3 ~/.claude/skills/slack/scripts/slack_read.py "#general"

# Read last 20 messages
python3 ~/.claude/skills/slack/scripts/slack_read.py "#general" -n 20

# Read thread replies
python3 ~/.claude/skills/slack/scripts/slack_read.py "#general" --thread 1234567890.123456

# Read since a specific date
python3 ~/.claude/skills/slack/scripts/slack_read.py "#general" --since "2026-02-11"

# Resolve user IDs to names
python3 ~/.claude/skills/slack/scripts/slack_read.py "#general" --resolve-users

# JSON output
python3 ~/.claude/skills/slack/scripts/slack_read.py "#general" --json
```

**Parameters**: `channel`, `-n/--num`, `--thread`, `--since`, `--resolve-users`, `--json`

---

### 3. slack_search.py — Search Messages & Files

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_search.py`

Search messages and files across the workspace.

```bash
# Search messages
python3 ~/.claude/skills/slack/scripts/slack_search.py "deployment failed"

# Search in a specific channel
python3 ~/.claude/skills/slack/scripts/slack_search.py "bug report" --channel "#engineering"

# Search from a specific user
python3 ~/.claude/skills/slack/scripts/slack_search.py "API update" --from "@tom"

# Date-filtered search
python3 ~/.claude/skills/slack/scripts/slack_search.py "release" --after 2026-02-01 --before 2026-02-11

# Search files
python3 ~/.claude/skills/slack/scripts/slack_search.py "architecture diagram" --files

# Sort by relevance
python3 ~/.claude/skills/slack/scripts/slack_search.py "soul engine" --sort score
```

**Parameters**: `query`, `-n/--num`, `--channel`, `--from`, `--after`, `--before`, `--files`, `--sort`, `--page`, `--json`

**Note**: With a bot token (`xoxb-`), search only covers channels the bot is a member of. For workspace-wide search, use a user token (`xoxp-`) with `search:read` scope.

---

### 4. slack_react.py — Manage Reactions

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_react.py`

```bash
# Add a reaction
python3 ~/.claude/skills/slack/scripts/slack_react.py "#general" 1234567890.123456 rocket

# Remove a reaction
python3 ~/.claude/skills/slack/scripts/slack_react.py "#general" 1234567890.123456 rocket --remove

# List reactions on a message
python3 ~/.claude/skills/slack/scripts/slack_react.py "#general" 1234567890.123456 --list
```

**Parameters**: `channel`, `timestamp`, `emoji`, `--remove`, `--list`, `--json`

---

### 5. slack_upload.py — Upload Files

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_upload.py`

Upload files using the 2-step external upload API.

```bash
# Upload a file
python3 ~/.claude/skills/slack/scripts/slack_upload.py "#general" ./report.pdf

# Upload with title and message
python3 ~/.claude/skills/slack/scripts/slack_upload.py "#general" ./chart.png --title "Q1 Results" --message "Latest chart"

# Upload to a thread
python3 ~/.claude/skills/slack/scripts/slack_upload.py "#general" ./data.csv --thread 1234567890.123456

# Upload a code snippet
python3 ~/.claude/skills/slack/scripts/slack_upload.py "#general" --snippet "print('hello')" --filetype python --title "Example"
```

**Parameters**: `channel`, `file`, `--title`, `--message`, `--thread`, `--snippet`, `--filetype`, `--json`

---

### 6. slack_channels.py — Channel Management

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_channels.py`

```bash
# List all channels
python3 ~/.claude/skills/slack/scripts/slack_channels.py

# Show member counts
python3 ~/.claude/skills/slack/scripts/slack_channels.py --members

# Get channel details
python3 ~/.claude/skills/slack/scripts/slack_channels.py --info "#general"

# Join a channel
python3 ~/.claude/skills/slack/scripts/slack_channels.py --join "#new-channel"

# Filter by name pattern
python3 ~/.claude/skills/slack/scripts/slack_channels.py --filter "eng-"

# Include private channels
python3 ~/.claude/skills/slack/scripts/slack_channels.py --private
```

**Parameters**: `--info`, `--join`, `--filter`, `--members`, `--private`, `--json`

---

### 7. slack_users.py — User Lookup

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_users.py`

```bash
# List all users
python3 ~/.claude/skills/slack/scripts/slack_users.py

# Active humans only (no bots/deactivated)
python3 ~/.claude/skills/slack/scripts/slack_users.py --active

# Get user details by ID
python3 ~/.claude/skills/slack/scripts/slack_users.py --info U12345678

# Lookup by email
python3 ~/.claude/skills/slack/scripts/slack_users.py --email tom@aldea.ai
```

**Parameters**: `--info`, `--email`, `--active`, `--json`

---

## Script Selection Guide

| Task | Script | Example |
|------|--------|---------|
| Post a message | `slack_post.py` | `slack_post.py "#general" "Hello"` |
| Reply to a thread | `slack_post.py` | `slack_post.py "#ch" "reply" --thread TS` |
| Schedule a message | `slack_post.py` | `slack_post.py "#ch" "msg" --schedule ISO` |
| Read channel history | `slack_read.py` | `slack_read.py "#general" -n 20` |
| Read thread | `slack_read.py` | `slack_read.py "#ch" --thread TS` |
| Search messages | `slack_search.py` | `slack_search.py "query"` |
| Search files | `slack_search.py` | `slack_search.py "query" --files` |
| Add reaction | `slack_react.py` | `slack_react.py "#ch" TS emoji` |
| Upload file | `slack_upload.py` | `slack_upload.py "#ch" ./file.pdf` |
| Share code snippet | `slack_upload.py` | `slack_upload.py "#ch" --snippet CODE` |
| List channels | `slack_channels.py` | `slack_channels.py` |
| Join channel | `slack_channels.py` | `slack_channels.py --join "#ch"` |
| Find user by email | `slack_users.py` | `slack_users.py --email user@co.com` |

---

## Rate Limit Awareness

| Tier | Rate | Key Methods |
|------|------|-------------|
| **Tier 1** | **1/min** | `conversations.history`, `conversations.replies` (commercial non-Marketplace only) |
| Tier 2 | 20/min | `conversations.list`, `users.list`, `search.messages`, `search.files` |
| Tier 3 | 50/min | `reactions.*`, `conversations.info`, `users.info`, `chat.update`, `chat.delete` |
| Tier 4 | 100+/min | `files.getUploadURLExternal`, `files.completeUploadExternal` |
| Special | 1/sec/channel | `chat.postMessage` (per-channel, not global) |

All scripts handle rate limits automatically via `_slack_utils.py`:
- Local cooldown timer prevents most 429s
- Automatic retry with `Retry-After` on 429 responses
- Stderr warnings when waiting >5 seconds

See `references/rate-limits.md` for full details.

---

## Test Suite

```bash
# Run all tests
python3 ~/.claude/skills/slack/scripts/test_slack.py

# Quick validation (auth + channel list)
python3 ~/.claude/skills/slack/scripts/test_slack.py --quick

# Test specific endpoint
python3 ~/.claude/skills/slack/scripts/test_slack.py --test post
python3 ~/.claude/skills/slack/scripts/test_slack.py --test read
python3 ~/.claude/skills/slack/scripts/test_slack.py --test search

# Verbose output
python3 ~/.claude/skills/slack/scripts/test_slack.py --verbose

# Use a specific test channel (default: #general)
python3 ~/.claude/skills/slack/scripts/test_slack.py --test-channel "#bot-test"

# Verify per-channel read/write access
python3 ~/.claude/skills/slack/scripts/test_channels.py
```

---

## Daemon Mode — Claudius, Artifex Maximus

The daemon is a persistent Socket Mode bot with a **pseudo soul engine** — cognitive architecture adapted from the Aldea Soul Engine for single-shot `claude -p` subprocess calls. It provides personality, three-tier memory, per-user modeling, and cross-thread soul state.

For full architecture details (cognitive steps, XML format, memory tiers, entry types, user model template, personality, prompt injection defense), see `references/daemon-architecture.md`.

### Prerequisites

1. **Enable Socket Mode**: [api.slack.com/apps](https://api.slack.com/apps) → Your App → Settings → Socket Mode → Enable
2. **Generate app-level token**: Basic Information → App-Level Tokens → Generate Token
   - Name: `socket-mode`
   - Scope: `connections:write`
   - Copy the `xapp-` token
3. **Add bot event subscriptions**: Event Subscriptions → Subscribe to Bot Events → Add:
   - `app_mention` — channel @mentions
   - `message.im` — direct messages
4. **Add bot scope**: OAuth & Permissions → Bot Token Scopes → `app_mentions:read`
5. **Reinstall app** to workspace after scope changes

### Environment Variables

```bash
export SLACK_BOT_TOKEN=xoxb-...   # Bot User OAuth Token
export SLACK_APP_TOKEN=xapp-...   # App-Level Token (Socket Mode)
```

### Running the Daemon

The daemon must be run from its directory due to local module imports.

```bash
# Install dependencies
cd ~/.claude/skills/slack/daemon
uv pip install --system slack-bolt

# Dev mode — foreground with debug logging
python3 bot.py --verbose

# Without soul engine (raw claude -p passthrough)
SLACK_DAEMON_SOUL_ENGINE=false python3 bot.py --verbose

# Production — launchd (Mac Mini M4)
./launchd/install.sh install    # load LaunchAgent
./launchd/install.sh status     # check if running
./launchd/install.sh logs       # tail logs
./launchd/install.sh restart    # reload
./launchd/install.sh uninstall  # stop and remove
```

### Configuration

All settings can be overridden via environment variables prefixed with `SLACK_DAEMON_`:

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| Claude timeout | `SLACK_DAEMON_TIMEOUT` | `120` s | Max seconds per `claude -p` call |
| Working directory | `SLACK_DAEMON_CWD` | `~/Desktop/Programming` | CWD for Claude subprocess |
| Allowed tools | `SLACK_DAEMON_TOOLS` | `Read,Glob,Grep,Bash,WebFetch` | Tools Claude can use |
| Session TTL | `SLACK_DAEMON_SESSION_TTL` | `24` hours | Thread session expiry |
| Soul engine | `SLACK_DAEMON_SOUL_ENGINE` | `true` | Enable/disable soul engine |
| Memory window | `SLACK_DAEMON_MEMORY_WINDOW` | `20` | Working memory entries per prompt |
| Memory TTL | `SLACK_DAEMON_MEMORY_TTL` | `72` hours | Working memory expiry |
| Soul state interval | `SLACK_DAEMON_SOUL_STATE_INTERVAL` | `3` | Interactions between soul state update prompts |
| Max response length | *(config.py)* | `3000` chars | Slack message truncation (limit ~4000) |

### Inspecting Memory

```bash
cd ~/.claude/skills/slack/daemon

# View soul state
sqlite3 memory.db "SELECT key, value FROM soul_memory"

# View user models
sqlite3 memory.db "SELECT user_id, display_name, interaction_count FROM user_models"

# View recent working memory
sqlite3 memory.db "SELECT entry_type, verb, content FROM working_memory ORDER BY created_at DESC LIMIT 20"

# View active sessions
sqlite3 sessions.db "SELECT channel, thread_ts, session_id FROM sessions"
```

### Graceful Shutdown

On SIGTERM or SIGINT:
1. Close Socket Mode handler
2. Cleanup expired working memory and sessions
3. Close all SQLite connections (session_store, working_memory, user_models, soul_memory)

The soul state update interval counter resets on daemon restart (in-process memory only).

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Bot not responding to @mentions | Socket Mode not enabled or `SLACK_APP_TOKEN` missing | Enable Socket Mode in app settings; verify `xapp-` token is exported |
| "missing_scope" error | Bot lacks required OAuth scope | Add the missing scope in OAuth & Permissions → reinstall app |
| No search results | Bot token only searches channels bot is a member of | Invite bot to channels with `/invite @Claude Code`, or use a user token (`xoxp-`) |
| Rate limited (429) | Too many API calls | Scripts auto-retry; reduce batch sizes or add `--test-channel` for testing |
| Daemon exits immediately | `claude` CLI not in PATH | Verify `which claude` returns a path; check `/opt/homebrew/bin` is in PATH |
| Soul engine XML parsing fails | Claude response didn't include expected tags | Check `daemon/logs/daemon.log`; fallback raw text is returned to Slack |
| "No virtual environment found" | `uv pip` without `--system` flag | Use `uv pip install --system slack-bolt` |

---

## New User Onboarding

When setting up Claudius for a new user or team, have the bot conduct a structured interview to bootstrap personalized configuration. This creates two foundational files that make every future interaction more effective.

### Step 1: Build a User Model via Slack DM

DM the Claudius bot and ask it to interview you. The soul engine's user model system will automatically build a personality profile over time, but an explicit interview accelerates this dramatically.

Prompt Claudius with:
> "Interview me so you can build a detailed model of who I am, how I work, and what I care about. Ask me about my role, technical domains, communication style, working patterns, and interests. Keep going until you have a thorough picture."

The bot will ask questions iteratively. After the interview, the user model in `daemon/memory.db` will contain a rich markdown profile. Export it for use as a persistent userModel:

```bash
# View what Claudius learned
sqlite3 ~/.claude/skills/slack/daemon/memory.db \
  "SELECT model_text FROM user_models WHERE user_id = 'U12345678'"

# Save as a userModel file for Claude Code
sqlite3 ~/.claude/skills/slack/daemon/memory.db \
  -noheader "SELECT model_text FROM user_models WHERE user_id = 'U12345678'" \
  > ~/.claude/userModels/yourName.md
```

### Step 2: Generate a Personalized CLAUDE.md

Use the `/interview` command in Claude Code to build a first `CLAUDE.md` personalized to the user's work. This can also be done via the Slack bot:

> "Help me create a CLAUDE.md file for my project. Interview me about my codebase, conventions, tools, and preferences until you have enough to write comprehensive project instructions."

The resulting `CLAUDE.md` should reference the userModel:

```markdown
# Project Instructions

## Identity
@userModels/yourName.md

## Principles
- [extracted from interview]

## Tools
- [extracted from interview]
```

### Why This Matters

- **User models** let Claudius adapt its tone, depth, and domain focus per person from the first message
- **CLAUDE.md** ensures every Claude Code session (not just Slack) inherits the user's conventions and constraints
- Both files compound over time — the soul engine updates user models automatically, and CLAUDE.md can be iterated via future interviews

---

## Common Workflows

### Post a Daily Update

```bash
python3 ~/.claude/skills/slack/scripts/slack_post.py "#standup" \
  "*Daily Update — $(date +%Y-%m-%d)*
• Completed: feature X implementation
• In progress: testing Y
• Blocked: waiting on API keys"
```

### Monitor a Channel

```bash
# Read recent messages
python3 ~/.claude/skills/slack/scripts/slack_read.py "#alerts" -n 5

# Search for specific issues
python3 ~/.claude/skills/slack/scripts/slack_search.py "error" --channel "#alerts" --after $(date -v-1d +%Y-%m-%d)
```

### Share a File with Context

```bash
python3 ~/.claude/skills/slack/scripts/slack_upload.py "#engineering" ./architecture.png \
  --title "System Architecture v2" \
  --message "Updated architecture diagram with the new caching layer"
```

### Find Someone's Email

```bash
python3 ~/.claude/skills/slack/scripts/slack_users.py --info U12345678
```

---

## Assets

- `assets/app-icon.png` — Slack app icon for bot configuration
