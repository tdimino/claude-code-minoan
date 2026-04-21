# SMS

Send, read, listen, respond, and manage SMS/MMS conversations from the terminal via Telnyx and Twilio. Supports multiple phone numbers across both providers with auto-detection, conversation threading, MMS, real-time inbound listening, background watcher, batch reply processor, and auto-reply.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Two-way SMS from a Claude Code session---send texts, read inboxes, monitor inbound messages, and auto-reply---without touching a phone or web UI. Supports both Telnyx and Twilio with provider auto-detection based on the sending number.

---

## Structure

```
sms/
  SKILL.md                          # Full usage guide with all flags
  README.md                         # This file
  references/                       # (reserved)
  scripts/
    sms_send.py                     # Send SMS/MMS
    sms_read.py                     # Read inbox (API query)
    sms_conversation.py             # View conversation thread
    sms_numbers.py                  # List available phone numbers
    sms_listen.py                   # Real-time inbound listener daemon
    sms_inbox.py                    # Read inbound inbox (from listener)
    sms_watch.py                    # Background watcher for new messages
    sms_respond.py                  # Auto-reply daemon (standalone)
    sms_process_reply.py            # Batch reply + memory update
    sms_memory.py                   # 3-tier SQLite memory (working, user model, soul)
    _sms_utils.py                   # Shared utilities (provider detection, credentials)
```

---

## Usage

```bash
# Send a text
python3 sms_send.py "+19175551234" "Hello from Claude"

# Read recent messages
python3 sms_read.py -n 10 --provider twilio

# View conversation thread
python3 sms_conversation.py "+19175551234"

# List all available numbers
python3 sms_numbers.py

# Start real-time listener (background)
python3 sms_listen.py --bg

# Check inbound messages
python3 sms_inbox.py

# Start auto-reply daemon (standalone, headless)
python3 sms_respond.py --daemon --bg
```

---

## Scripts

| Script | Purpose | Standalone? |
|--------|---------|-------------|
| `sms_send.py` | Send SMS/MMS (auto-detects provider) | Yes |
| `sms_read.py` | Read inbox via Telnyx/Twilio API | Yes |
| `sms_conversation.py` | View threaded conversation with a number | Yes |
| `sms_numbers.py` | List phone numbers across providers | Yes |
| `sms_listen.py` | Background daemon polling for inbound messages | Yes |
| `sms_inbox.py` | Read messages collected by the listener | Yes (needs listener running) |
| `sms_watch.py` | Background watcher, notifies on new messages | Yes (needs listener running) |
| `sms_respond.py` | Auto-reply daemon using `claude -p` subprocess | Yes (standalone only) |
| `sms_process_reply.py` | Batch reply sender + memory operations | Yes |
| `sms_memory.py` | 3-tier SQLite memory system | Library (used by other scripts) |

---

## Key Features

| Feature | How |
|---------|-----|
| Multi-provider | Telnyx + Twilio, auto-detected from `--from` number |
| MMS | `sms_send.py --media URL` |
| Conversation threading | `sms_conversation.py NUMBER` |
| Real-time monitoring | `sms_listen.py --bg` (polls Twilio, webhooks Telnyx) |
| Auto-reply | `sms_respond.py --daemon` (standalone) or `/sms-respond` (in-session) |
| Background watcher | `sms_watch.py` detects new messages, prints structured JSON |
| Memory | 3-tier SQLite: working memory, user models, soul state |

---

## Setup

### Prerequisites

- Python 3.9+
- `pip install requests`
- **Telnyx**: `TELNYX_API_KEY` env var or in `~/.claude.json`
- **Twilio**: `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` env vars

### Provider Defaults

| Provider | Default From | Notes |
|----------|-------------|-------|
| Telnyx | configured number | Send-only (no REST read API) |
| Twilio | configured number | Full read/write/conversation |

---

## Related Skills

- **`twilio-api`**: Twilio API reference with production patterns (webhooks, TwiML, signature validation).
- **`resend`**: Email sending---for email notifications instead of SMS.
- **`telegram`**: Telegram messaging---alternative chat channel.

---

## Requirements

- Python 3.9+
- `requests`
- Telnyx API key and/or Twilio credentials

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/sms ~/.claude/skills/
```
