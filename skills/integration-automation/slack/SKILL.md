---
name: slack
description: "Full Slack workspace integration — post messages, read channels, search, react, upload files, manage channels and users. 8 specialized scripts with built-in rate limiting for post-May 2025 API restrictions. This skill should be used when reading Slack messages, posting to channels, searching workspace content, uploading files, or managing channels and users."
---

# Slack Skill

Full Slack workspace integration through 8 specialized Python scripts, each targeting a specific set of API methods with built-in rate limiting.

## When to Use This Skill

Use this skill when:
- Posting messages to Slack channels or threads
- Reading channel history or thread replies
- Searching messages or files across the workspace
- Adding or managing reactions on messages
- Uploading files or code snippets
- Listing channels, getting channel info, or joining channels
- Looking up users by name, ID, or email

## Prerequisite

All scripts require the `SLACK_BOT_TOKEN` environment variable (a Bot User OAuth Token starting with `xoxb-`).

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
   - `channels:read`, `groups:read`
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

**Rate limit warning**: `conversations.history` is Tier 1 (1 req/min) for commercial non-Marketplace apps. Internal apps get Tier 3 (50/min). Reading a single channel is always fine.

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

Add, remove, or list reactions on messages.

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

Upload files using the new 2-step external upload API (NOT the deprecated `files.upload`).

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

List, inspect, and join channels.

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

List and look up workspace users.

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

Rate limits vary by app type. Tier 1 only applies to `conversations.history/replies` for commercially-distributed non-Marketplace apps.

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

## Test Suite

Verify your setup:

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
```

The test suite verifies:
- Auth token validation (`auth.test`)
- Channel listing (`conversations.list`)
- User listing (`users.list`)
- Post + delete cycle (`chat.postMessage`, `chat.delete`)
- History read (`conversations.history`)
- Message search (`search.messages`)
- Reaction add + remove cycle
- Rate limit header presence
