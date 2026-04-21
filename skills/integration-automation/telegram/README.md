# Telegram

Send, read, and respond to Telegram messages from Claude Code. Five Python scripts talk directly to the Telegram Bot API via REST (no asyncio), so they work reliably inside any subprocess or skill invocation. Sending works out of the box with just a bot token; receiving and memory features plug into an optional listener and inbox architecture.

**Last updated:** 2026-04-21

**Reflects:** Telegram Bot API, `python-telegram-bot` v22.

---

## Why This Skill Exists

Claude Code can't talk to Telegram out of the box. This skill bridges that gap with scripts for discrete operations---send messages, check an inbox, read callback queries, verify bot health, and load conversation memory. The sender is fully standalone; the inbox and memory scripts read from a shared JSONL inbox that any polling listener can write to.

---

## Architecture

```
Claude Code session
  ├─ telegram_send.py        REST POST — standalone, no listener needed
  ├─ telegram_check.py       Read telegram:* entries from inbox.jsonl
  ├─ telegram_callback.py    Read callback entries, answerCallbackQuery
  ├─ telegram_status.py      getMe + listener PID + inbox count
  └─ telegram_memory.py      Memory context CLI (optional)
                 ↓
Listener (writes incoming messages to inbox.jsonl)
  └─ Any python-telegram-bot polling script, or the Claudicle adapter
                 ↓
~/.claudicle/daemon/inbox.jsonl   (shared inbox — SMS, Slack, Telegram)
```

The sender hits the Telegram REST API directly and has zero infrastructure dependencies beyond a bot token. The check/callback/status/memory scripts read from `inbox.jsonl`, which any listener can populate. [Claudicle](https://github.com/tdimino/claudicle) ships a ready-made listener and daemon, but the skill doesn't require it.

---

## Structure

```
telegram/
  SKILL.md                   # Full usage guide and reference
  README.md                  # This file
  data/                      # Runtime data directory
  scripts/
    telegram_send.py         # Send messages (text, Markdown, HTML, inline keyboards)
    telegram_check.py        # Read inbox for unhandled Telegram messages
    telegram_callback.py     # Read/answer inline keyboard button taps
    telegram_status.py       # Bot identity and listener health check
    telegram_memory.py       # Memory context CLI (working memory, user models, soul state)
```

---

## Scripts

All scripts authenticate via `TELEGRAM_BOT_TOKEN` from `~/.config/env/secrets.env` or the environment.

| Script | Purpose | Standalone? | Example |
|--------|---------|-------------|---------|
| `telegram_send.py` | Send messages with formatting and inline keyboards | Yes | `python3 telegram_send.py CHAT_ID "Hello"` |
| `telegram_check.py` | Read unhandled Telegram messages from inbox | Needs listener | `python3 telegram_check.py` |
| `telegram_callback.py` | Read pending button taps, answer callback queries | Needs listener | `python3 telegram_callback.py --prefix approve:` |
| `telegram_status.py` | Check bot reachability and listener health | Partial | `python3 telegram_status.py --json` |
| `telegram_memory.py` | Load memory context for a Telegram channel | Needs memory DB | `python3 telegram_memory.py load-context CHAT_ID` |

### Inline Keyboards

Send tappable buttons for approval gates and interactive flows:

```bash
python3 telegram_send.py CHAT_ID "Approve dispatch?" \
  --buttons '[["Approve|approve_day42","Reject|reject_day42"]]'
```

Button format: list of rows, each row a list of `"Label|callback_data"` strings. URL buttons use `"Label|url:https://..."`.

---

## Setup

### Prerequisites

- Python 3.9+
- `pip install requests`

That's enough to send messages. For receiving:

- A polling listener that writes incoming messages to `~/.claudicle/daemon/inbox.jsonl` in the expected JSONL format (one JSON object per line with `channel`, `ts`, `text`, `user_id`, `handled` fields)
- Python 3.10+ if using `python-telegram-bot` v22 as the listener (asyncio bug in 3.9 breaks `CallbackQueryHandler`)
- `pip install python-telegram-bot` (listener only)

### Configuration

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Add `TELEGRAM_BOT_TOKEN` to `~/.config/env/secrets.env` or export it in your shell
3. Find your chat ID by DM'ing [@userinfobot](https://t.me/userinfobot)

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | --- | Bot token from @BotFather (required) |
| `CLAUDICLE_TELEGRAM_ALLOWED_CHATS` | --- | Comma-separated chat IDs for listener access control |
| `CLAUDICLE_TELEGRAM_RESPOND_TO_DMS` | `true` | Listener: respond to private messages |
| `CLAUDICLE_TELEGRAM_RESPOND_TO_MENTIONS` | `true` | Listener: respond to @mentions in groups |

---

## Related Skills

- **`telegram-respond`**: Processes unhandled Telegram messages through a cognitive pipeline (internal monologue, user model, soul state, external response).
- **`sms`** / **`slack`**: Sibling channel integrations sharing the same `inbox.jsonl` format.
- **[Claudicle](https://github.com/tdimino/claudicle)**: Ships a ready-made polling listener, daemon inbox, and memory infrastructure that these scripts can use. Optional---not required for sending.

---

## Requirements

- Python 3.9+ (3.10+ for listener)
- `requests` (send/status/callback scripts)
- `python-telegram-bot` v22 (listener only)
- Telegram Bot Token

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/telegram ~/.claude/skills/
```
