# Session Bridge — Installation & Usage Guide

Connect any running Claude Code session to Slack. A lightweight background listener catches @mentions and DMs, writes them to an inbox file. This session reads the inbox, processes messages with full tool access, and posts responses back.

**Why Session Bridge**: no extra API costs (messages processed in current session), full tool access, full session context, portable to any Claude Code session. No Claude Agent SDK required.

## Installation

### 1. Prerequisites

- Python 3.10+
- Slack Bot Token (`SLACK_BOT_TOKEN` / `xoxb-...`)
- Slack App Token (`SLACK_APP_TOKEN` / `xapp-...`) — Socket Mode must be enabled
- Bot event subscriptions: `app_mention`, `message.im`

See SKILL.md "First-Time Setup" for full Slack app creation steps.

### 2. Install Dependencies

```bash
cd ~/.claude/skills/slack/daemon
uv pip install --system slack_bolt slack_sdk
```

Or from requirements.txt:
```bash
uv pip install --system -r requirements.txt
```

### 3. Verify Environment

```bash
echo $SLACK_BOT_TOKEN   # should start with xoxb-
echo $SLACK_APP_TOKEN   # should start with xapp-
```

### 4. Test the Listener (Foreground)

```bash
cd ~/.claude/skills/slack/daemon && python3 slack_listen.py
```

Send a DM to the bot in Slack — you should see output in the terminal. `Ctrl+C` to stop.

### 5. (Optional) Register Auto-Check Hook

Add to `~/.claude/settings.json` to auto-surface unhandled messages at the start of every Claude Code turn:

```json
{
    "hooks": {
        "UserPromptSubmit": [
            {
                "type": "command",
                "command": "python3 ~/.claude/skills/slack/scripts/slack_inbox_hook.py"
            }
        ]
    }
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  This Claude Code Session (full tools, context)  │
│                                                   │
│  1. Start:  python3 slack_listen.py --bg          │
│  2. Check:  python3 slack_check.py                │
│  3. Stop:   python3 slack_listen.py --stop        │
│                                                   │
│  Processing flow:                                 │
│    Read inbox.jsonl → process → slack_post.py     │
└─────────────────────────────────────────────────┘
        ▲ reads                    │ posts
        │                          ▼
┌───────────────┐          ┌──────────────────┐
│  inbox.jsonl  │          │  Slack API        │
│  (append-only)│          │  (chat.postMessage│
└───────┬───────┘          │   via slack_post) │
        │                  └──────────────────┘
        │ writes
┌───────────────────────────────────────────┐
│  slack_listen.py  (background process)     │
│  Socket Mode: @mentions + DMs → inbox     │
│  Adds hourglass reaction on receipt        │
└───────────────────────────────────────────┘
```

### Inbox File Format

`daemon/inbox.jsonl` — one JSON object per line, append-only:

```json
{
  "ts": 1739300000.123,
  "channel": "C12345",
  "thread_ts": "1739300000.123456",
  "user_id": "U12345",
  "display_name": "Tom",
  "text": "What's the status?",
  "handled": false
}
```

---

## Usage

### Connect (Start Listener)

```bash
# Background mode (recommended)
cd ~/.claude/skills/slack/daemon && python3 slack_listen.py --bg

# Check if running
python3 ~/.claude/skills/slack/daemon/slack_listen.py --status

# Foreground mode (for testing/debugging)
python3 ~/.claude/skills/slack/daemon/slack_listen.py
```

The listener writes a PID file to `daemon/listener.pid` and redirects output to `daemon/logs/listener.log`.

### Check for Messages

```bash
python3 ~/.claude/skills/slack/scripts/slack_check.py
```

Output:
```
[1] #C12345 | Tom (thread: 1234567890.123456): "What's the status?"
[2] DM:D456 | Alice (thread: 1234567890.789012): "Check the tests"
```

### Respond to a Message

```bash
# Post response to the thread
python3 ~/.claude/skills/slack/scripts/slack_post.py "C12345" "Here's the status..." --thread "1234567890.123456"

# Remove hourglass reaction
python3 ~/.claude/skills/slack/scripts/slack_react.py "C12345" "1234567890.123456" "hourglass_flowing_sand" --remove

# Mark as handled
python3 ~/.claude/skills/slack/scripts/slack_check.py --ack 1
```

### Inbox Management

```bash
python3 ~/.claude/skills/slack/scripts/slack_check.py --ack 1      # mark #1 as handled
python3 ~/.claude/skills/slack/scripts/slack_check.py --ack-all    # mark all as handled
python3 ~/.claude/skills/slack/scripts/slack_check.py --clear      # delete inbox file
python3 ~/.claude/skills/slack/scripts/slack_check.py --quiet      # one-line summary (for hooks)
```

### Disconnect (Stop Listener)

```bash
python3 ~/.claude/skills/slack/daemon/slack_listen.py --stop
```

---

## Soul Formatter (Optional)

`scripts/slack_format.py` implements the Open Souls cognitive step paradigm as a lightweight CLI. Use it to add soul-engine-style formatting to bridge responses.

### Format Incoming Perceptions

```bash
python3 ~/.claude/skills/slack/scripts/slack_format.py perception "Tom" "What's the status?"
# → Tom said, "What's the status?"
```

### Extract External Dialogue

```bash
# Plain extraction (for posting)
echo "$raw_response" | python3 ~/.claude/skills/slack/scripts/slack_format.py extract

# Narrated format
echo "$raw_response" | python3 ~/.claude/skills/slack/scripts/slack_format.py extract --narrate
# → Claudius explained, "The BG3 port is at 93% parity."
```

### Get Cognitive Step Instructions

```bash
python3 ~/.claude/skills/slack/scripts/slack_format.py instructions
```

Prints the XML format for `internalMonologue`, `externalDialog`, and `mentalQuery` — inject into prompt context when processing Slack messages.

### Log Internal State

```bash
echo "$raw_response" | python3 ~/.claude/skills/slack/scripts/slack_format.py extract --log
# → logs internalMonologue + mentalQuery to daemon/logs/monologue.log
```

---

## Auto-Notification Hook

When registered (see Installation step 5), the `slack_inbox_hook.py` hook runs at the start of every Claude Code turn:

- If inbox has unhandled messages → outputs: `[Slack: 2 unhandled messages -- run /slack-check to view]`
- If inbox is empty or all handled → silent (no output)
- If listener not running → silent (no output)

---

## Files

| File | Purpose |
|------|---------|
| `daemon/slack_listen.py` | Background Socket Mode listener → writes inbox.jsonl |
| `daemon/inbox.jsonl` | Incoming messages (auto-created, gitignored) |
| `daemon/listener.pid` | PID file for lifecycle management (gitignored) |
| `scripts/slack_check.py` | Read/ack/clear inbox messages |
| `scripts/slack_inbox_hook.py` | UserPromptSubmit auto-check hook |
| `scripts/slack_format.py` | Soul formatter: perception/extract/instructions |
| `daemon/soul.md` | Claudius personality guidelines |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `slack_listen.py --bg` fails silently | Run in foreground first to see errors: `python3 slack_listen.py` |
| "No unhandled Slack messages" but you sent one | Check listener is running: `python3 slack_listen.py --status` |
| Hook doesn't fire | Verify `settings.json` hook config; check `python3 slack_inbox_hook.py` runs without error |
| `ModuleNotFoundError: slack_bolt` | Install: `uv pip install --system slack_bolt slack_sdk` |
| Hourglass reaction not appearing | Ensure `reactions:write` scope is added to the Slack app |
