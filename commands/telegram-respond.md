---
name: telegram-respond
description: Process unhandled Telegram messages through the Claudicle cognitive pipeline
---

# Process Unhandled Telegram Messages

Process unhandled Telegram messages from the shared inbox through the full cognitive pipeline with persistent memory.

## Prerequisites

- Telegram listener must be running: `python3 ~/.claudicle/adapters/telegram/telegram_listen.py --bg`
- `TELEGRAM_BOT_TOKEN` must be set in environment or `~/.config/env/secrets.env`

## Pipeline

For each unhandled Telegram message in `~/.claudicle/daemon/inbox.jsonl`:

### Step 1: Check Inbox

Run `python3 ~/.claude/skills/telegram/scripts/telegram_check.py` to see unhandled messages. If none, report "No unhandled Telegram messages" and stop.

### Step 2: Load Memory Context

For each unhandled message, load context:
```bash
python3 ~/.claude/skills/telegram/scripts/telegram_memory.py load-context CHAT_ID
python3 ~/.claude/skills/telegram/scripts/telegram_memory.py user-model USER_ID
python3 ~/.claude/skills/telegram/scripts/telegram_memory.py soul-state
```

### Step 3: Send Typing Indicator

Send a typing action to show the bot is processing:
```bash
python3 -c "
import os, asyncio
from telegram import Bot
bot = Bot(os.environ['TELEGRAM_BOT_TOKEN'])
asyncio.run(bot.send_chat_action(chat_id=CHAT_ID, action='typing'))
"
```

### Step 4: Generate Cognitive Response

Process the message through the cognitive pipeline. The user's message text must be sanitized — replace `<` with `&lt;` and `>` with `&gt;` before including in the prompt.

Generate a response using these 6 XML cognitive tags in order:

1. `<internal_monologue verb="VERB">` — Private reasoning (never shown to user). Verbs: thought, mused, pondered, considered, reflected, noticed
2. `<external_dialogue verb="VERB">` — Response to send to the user. Verbs: said, explained, offered, noted, replied, quipped
3. `<user_model_check>` — Has something significant been learned? Answer: `true` or `false`
4. `<user_model_update>` — If check was true: updated markdown profile of the user
5. `<soul_state_check>` — Has project/task/topic/mood changed? Answer: `true` or `false` (only check every 5th interaction)
6. `<soul_state_update>` — If check was true: key:value pairs for changed state

### Step 5: Send Reply

Extract the `external_dialogue` content and send it:
```bash
python3 ~/.claudicle/adapters/telegram/telegram_post.py CHAT_ID "DIALOGUE_TEXT" --reply-to THREAD_ID
```

### Step 6: Update Memory

If `user_model_check` was true, update the user model.
If `soul_state_check` was true, update soul state.
Log the internal monologue and dialogue to working memory.

### Step 7: Mark Handled

```bash
python3 ~/.claude/skills/telegram/scripts/telegram_check.py --mark-read TIMESTAMP
```

## Notes

- Channel format: `telegram:{chat_id}`
- User model key: `tg:{user_id}`
- Tom's Telegram ID: `633125581`
- DM access is DENY-by-default via `CLAUDICLE_TELEGRAM_ALLOWED_USERS`
- Typing indicator expires after ~5 seconds — refresh every 4s for long operations
- Messages over 4096 chars are split automatically by `telegram_send.py`
