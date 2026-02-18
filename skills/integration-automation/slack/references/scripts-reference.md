# Slack Scripts Reference

Full documentation for all 7 on-demand Slack scripts. Each script is a standalone Python CLI tool that communicates with the Slack API using a bot token.

All scripts require the `SLACK_BOT_TOKEN` environment variable and `requests` (`uv pip install --system requests`).

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
```

**Parameters**: `channel`, `text`, `--thread`, `--blocks`, `--schedule`, `--update`, `--delete`, `--unfurl`, `--json`

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

## 3. slack_search.py — Search Messages & Files

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
