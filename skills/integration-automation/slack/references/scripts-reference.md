# Slack Scripts Reference

Full documentation for all 9 on-demand Slack scripts. Each script is a standalone Python CLI tool that communicates with the Slack API using a bot token (and optionally a user token for legacy search).

All scripts require the `SLACK_BOT_TOKEN` environment variable and `requests` (`uv pip install --system requests`). Optional: `SLACK_USER_TOKEN` (`xoxp-`) for workspace-wide legacy search when RTS API is unavailable.

## 1. slack_post.py — Post Messages

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

# Post with AI feedback buttons
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Here's my analysis" --ai

# Post AI message without feedback buttons
python3 ~/.claude/skills/slack/scripts/slack_post.py "#general" "Info only" --ai --no-feedback
```

**Parameters**: `channel`, `text`, `--thread`, `--blocks`, `--schedule`, `--update`, `--delete`, `--unfurl`, `--ai`, `--no-feedback`, `--json`

---

## 2. slack_read.py — Read Messages

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

## 3. slack_search.py — Search Messages, Files, Channels & Users

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_search.py`

Search via RTS API (`assistant.search.context`, Feb 2026+) with automatic fallback to legacy `search.messages`/`search.files`. RTS API supports messages, files, channels, and users with a single bot token.

```bash
# Search messages (auto-detects RTS, falls back to legacy)
python3 ~/.claude/skills/slack/scripts/slack_search.py "deployment failed"

# Force RTS API
python3 ~/.claude/skills/slack/scripts/slack_search.py "deployment" --rts

# Force legacy search
python3 ~/.claude/skills/slack/scripts/slack_search.py "deployment" --no-rts

# Search by resource type (RTS only)
python3 ~/.claude/skills/slack/scripts/slack_search.py "eng" --rts --type channels
python3 ~/.claude/skills/slack/scripts/slack_search.py "tom" --rts --type users

# Search in a specific channel (legacy)
python3 ~/.claude/skills/slack/scripts/slack_search.py "bug report" --channel "#engineering"

# Search from a specific user (legacy)
python3 ~/.claude/skills/slack/scripts/slack_search.py "API update" --from "@tom"

# Date-filtered search (legacy)
python3 ~/.claude/skills/slack/scripts/slack_search.py "release" --after 2026-02-01 --before 2026-02-11

# Search files
python3 ~/.claude/skills/slack/scripts/slack_search.py "architecture diagram" --files

# Sort by relevance
python3 ~/.claude/skills/slack/scripts/slack_search.py "soul engine" --sort score
```

**Parameters**: `query`, `-n/--num`, `--channel`, `--from`, `--after`, `--before`, `--files`, `--sort`, `--page`, `--rts`, `--no-rts`, `--type messages|files|channels|users`, `--json`

**Search modes**:
- **RTS API** (default when available): Uses `assistant.search.context` with bot token. Searches messages, files, channels, and users across the workspace. Requires `search:read.*` scopes.
- **Legacy**: Uses `search.messages`/`search.files`. With bot token (`xoxb-`), only covers channels the bot is a member of. With user token (`xoxp-` via `SLACK_USER_TOKEN`), covers the entire workspace.
- **Auto-detect**: First call probes for RTS availability and caches the result. Falls back to legacy on `missing_scope` or `not_allowed_token_type`.

---

## 3b. slack_stream.py — Stream Messages

**Command**: `python3 ~/.claude/skills/slack/scripts/slack_stream.py`

Stream messages in real-time using Slack's chat streaming API (`chat.startStream`/`chat.appendStream`/`chat.stopStream`). Messages appear character-by-character in the channel.

```bash
# Stream a message
python3 ~/.claude/skills/slack/scripts/slack_stream.py "#general" "Hello streaming world"

# Stream with custom chunk size and delay
python3 ~/.claude/skills/slack/scripts/slack_stream.py "#general" "Detailed response..." --chunk-size 50 --delay 0.05

# Stream from stdin (pipe output from another command)
echo "Piped content" | python3 ~/.claude/skills/slack/scripts/slack_stream.py "#general" --stdin

# Stream to a thread
python3 ~/.claude/skills/slack/scripts/slack_stream.py "#general" "Reply..." --thread 1234567890.123456
```

**Parameters**: `channel`, `text`, `--thread`, `--chunk-size`, `--delay`, `--stdin`, `--json`

---

## 4. slack_react.py — Manage Reactions

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

## 5. slack_upload.py — Upload Files

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

## 6. slack_channels.py — Channel Management

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

## 7. slack_users.py — User Lookup

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
