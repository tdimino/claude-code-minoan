#!/usr/bin/env python3
"""
Check Telegram bot and listener status.

Reports:
  - Bot identity via getMe REST call (username, ID, name)
  - Listener PID (running / not running) from ~/.claudicle/daemon/telegram_listener.pid
  - Unhandled Telegram message count in ~/.claudicle/daemon/inbox.jsonl
  - Configured env vars (allowed chats, DM/mention response flags)

Usage:
    python3 telegram_status.py              # Human-readable report
    python3 telegram_status.py --json       # Machine-readable JSON

Exit codes:
    0 = bot reachable AND listener running
    1 = bot reachable but listener not running
    2 = bot unreachable (token missing or network error)
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

INBOX_PATH = Path.home() / ".claudicle" / "daemon" / "inbox.jsonl"
PID_FILE = Path.home() / ".claudicle" / "daemon" / "telegram_listener.pid"
TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def load_secrets():
    secrets_path = Path.home() / ".config" / "env" / "secrets.env"
    if not secrets_path.exists():
        return
    for line in secrets_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        val = val.strip().strip("'\"")
        os.environ.setdefault(key, val)


def check_bot(token: str) -> dict:
    """Call getMe. Returns dict with ok, username, id, error."""
    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"}
    try:
        r = requests.get(TELEGRAM_API.format(token=token, method="getMe"), timeout=15)
        data = r.json()
        if not data.get("ok"):
            return {"ok": False, "error": data.get("description", "unknown")}
        result = data["result"]
        return {
            "ok": True,
            "username": result.get("username"),
            "id": result.get("id"),
            "first_name": result.get("first_name"),
        }
    except requests.RequestException as e:
        return {"ok": False, "error": str(e)}


def check_listener() -> dict:
    """Check listener PID file + process existence."""
    if not PID_FILE.exists():
        return {"running": False, "pid": None, "reason": "no PID file"}
    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, OSError) as e:
        return {"running": False, "pid": None, "reason": f"PID file unreadable: {e}"}
    try:
        os.kill(pid, 0)
    except OSError:
        return {"running": False, "pid": pid, "reason": "process not alive (stale PID)"}
    return {"running": True, "pid": pid, "reason": None}


def count_unhandled() -> dict:
    """Count unhandled telegram:* entries in inbox.jsonl."""
    if not INBOX_PATH.exists():
        return {"unhandled": 0, "total": 0, "inbox": str(INBOX_PATH), "exists": False}
    unhandled = 0
    total = 0
    for line in INBOX_PATH.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        channel = entry.get("channel", "")
        if not channel.startswith("telegram:"):
            continue
        total += 1
        if not entry.get("handled"):
            unhandled += 1
    return {
        "unhandled": unhandled,
        "total": total,
        "inbox": str(INBOX_PATH),
        "exists": True,
    }


def get_config() -> dict:
    """Return the Telegram env config the listener reads."""
    return {
        "TELEGRAM_BOT_TOKEN": "set" if os.environ.get("TELEGRAM_BOT_TOKEN") else "unset",
        "CLAUDICLE_TELEGRAM_ALLOWED_CHATS": os.environ.get(
            "CLAUDICLE_TELEGRAM_ALLOWED_CHATS", ""
        ) or "(empty)",
        "CLAUDICLE_TELEGRAM_ALLOWED_USERS": os.environ.get(
            "CLAUDICLE_TELEGRAM_ALLOWED_USERS", ""
        ) or "(empty)",
        "CLAUDICLE_TELEGRAM_RESPOND_TO_DMS": os.environ.get(
            "CLAUDICLE_TELEGRAM_RESPOND_TO_DMS", "true"
        ),
        "CLAUDICLE_TELEGRAM_RESPOND_TO_MENTIONS": os.environ.get(
            "CLAUDICLE_TELEGRAM_RESPOND_TO_MENTIONS", "true"
        ),
    }


def render_human(status: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("Telegram Skill Status")
    lines.append("=" * 60)

    bot = status["bot"]
    if bot["ok"]:
        lines.append(f"Bot:       @{bot['username']} (ID: {bot['id']})  [OK]")
        lines.append(f"           first_name: {bot.get('first_name', '?')}")
    else:
        lines.append(f"Bot:       UNREACHABLE — {bot['error']}")

    listener = status["listener"]
    if listener["running"]:
        lines.append(f"Listener:  running (PID {listener['pid']})  [OK]")
    else:
        reason = listener.get("reason") or "unknown"
        lines.append(f"Listener:  NOT RUNNING ({reason})")
        if listener.get("pid"):
            lines.append(f"           stale PID: {listener['pid']}")

    inbox = status["inbox"]
    if inbox["exists"]:
        lines.append(
            f"Inbox:     {inbox['unhandled']} unhandled / {inbox['total']} total"
        )
        lines.append(f"           path: {inbox['inbox']}")
    else:
        lines.append(f"Inbox:     not created yet ({inbox['inbox']})")

    lines.append("")
    lines.append("Configuration:")
    for key, val in status["config"].items():
        lines.append(f"  {key}={val}")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check Telegram bot and listener status")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    load_secrets()

    status = {
        "bot": check_bot(os.environ.get("TELEGRAM_BOT_TOKEN", "")),
        "listener": check_listener(),
        "inbox": count_unhandled(),
        "config": get_config(),
    }

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(render_human(status))

    # Exit code logic
    if not status["bot"]["ok"]:
        sys.exit(2)
    if not status["listener"]["running"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
