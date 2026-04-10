#!/usr/bin/env python3
"""
Read and process Telegram callback query entries from the shared inbox.

When a user taps an inline keyboard button, the listener's CallbackQueryHandler
writes an entry to ~/.claudicle/daemon/inbox.jsonl with:

    {
      "entry_type": "telegram_callback",
      "channel": "telegram:{chat_id}",
      "callback_query_id": "...",
      "callback_data": "approve:run-xxx",
      "message_id": 42,
      "user_id": "633125581",
      "ts": 1775828391.0,
      "handled": false
    }

This script provides a general CLI for reading those entries, filtering by
prefix (e.g., `approve:`, `mazkir_`, `deploy_`), marking them handled, and
answering the callback to clear the Telegram spinner.

Usage:
    python3 telegram_callback.py                          # All pending callbacks
    python3 telegram_callback.py --all                    # Include handled
    python3 telegram_callback.py --prefix approve:        # Filter by prefix
    python3 telegram_callback.py --limit 5                # Last 5
    python3 telegram_callback.py --json                   # JSON output
    python3 telegram_callback.py --mark-read TS           # Mark one handled
    python3 telegram_callback.py --mark-all-read          # Mark all handled
    python3 telegram_callback.py --answer QUERY_ID "text" # Answer callback toast

The --answer flag calls Telegram's answerCallbackQuery endpoint, which shows
a toast notification to the user and clears the loading spinner on the button.
This should be called quickly after a tap (within ~30s) or the callback expires.

Mazkir integration:
    The worldwarwatcher Mazkir pipeline uses its own sidecar
    (scripts/mazkir-callback-watcher.py) with its own staging state machine.
    Use this skill's telegram_callback.py for ad-hoc inspection and for
    namespaces other than Mazkir.
"""

import argparse
import fcntl
import json
import os
import sys
import time
from pathlib import Path

import requests

INBOX_PATH = Path.home() / ".claudicle" / "daemon" / "inbox.jsonl"
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


def read_callbacks(show_all: bool = False, prefix: str | None = None, limit: int = 0) -> list[dict]:
    if not INBOX_PATH.exists():
        return []

    entries = []
    for line in INBOX_PATH.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry.get("entry_type") != "telegram_callback":
            continue
        if not entry.get("channel", "").startswith("telegram:"):
            continue
        if not show_all and entry.get("handled"):
            continue
        if prefix and not entry.get("callback_data", "").startswith(prefix):
            continue
        entries.append(entry)

    if limit > 0:
        entries = entries[-limit:]
    return entries


def mark_handled(target_ts: str, mark_all: bool = False):
    if not INBOX_PATH.exists():
        print("No inbox file found.", file=sys.stderr)
        return 0

    marked = 0
    with open(INBOX_PATH, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        lines = f.readlines()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                new_lines.append(line)
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError:
                new_lines.append(line)
                continue

            is_callback = (
                entry.get("entry_type") == "telegram_callback"
                and entry.get("channel", "").startswith("telegram:")
            )
            if is_callback and not entry.get("handled"):
                if mark_all or str(entry.get("ts", "")) == target_ts:
                    entry["handled"] = True
                    marked += 1
            new_lines.append(json.dumps(entry) + "\n")

        f.seek(0)
        f.writelines(new_lines)
        f.truncate()
    return marked


def answer_callback(query_id: str, text: str, token: str) -> bool:
    """Acknowledge a callback query (shows toast, clears loading spinner)."""
    url = TELEGRAM_API.format(token=token, method="answerCallbackQuery")
    try:
        r = requests.post(
            url,
            json={
                "callback_query_id": query_id,
                "text": text[:200],  # Telegram limits toast to 200 chars
                "show_alert": False,
            },
            timeout=15,
        )
        data = r.json()
        if not data.get("ok"):
            print(f"Error: {data}", file=sys.stderr)
            return False
        return True
    except requests.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def display_entries(entries: list[dict]):
    if not entries:
        print("No callback queries pending.")
        return
    for entry in entries:
        ts = entry.get("ts", 0)
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "?"
        data = entry.get("callback_data", "")
        channel = entry.get("channel", "?")
        user = entry.get("user_id", "?")
        msg_id = entry.get("message_id", "?")
        handled = "HANDLED" if entry.get("handled") else "PENDING"
        query_id = entry.get("callback_query_id", "?")

        print(f"[{ts_str}] [{handled}] {channel} msg:{msg_id} user:{user}")
        print(f"  data:  {data}")
        print(f"  query: {query_id}")
        print(f"  ts:    {ts}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Read/process Telegram callback query entries"
    )
    parser.add_argument("--all", action="store_true", help="Include handled entries")
    parser.add_argument(
        "--prefix",
        default=None,
        help="Filter by callback_data prefix (e.g., 'approve:', 'mazkir_')",
    )
    parser.add_argument("--limit", type=int, default=0, help="Show last N entries")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--mark-read",
        metavar="TS",
        help="Mark callback with this ts as handled",
    )
    parser.add_argument(
        "--mark-all-read",
        action="store_true",
        help="Mark all telegram callback entries as handled",
    )
    parser.add_argument(
        "--answer",
        nargs=2,
        metavar=("QUERY_ID", "TEXT"),
        help="Answer a callback query (shows toast to user)",
    )
    args = parser.parse_args()

    load_secrets()

    if args.answer:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            print("Error: TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
            sys.exit(1)
        ok = answer_callback(args.answer[0], args.answer[1], token)
        sys.exit(0 if ok else 1)

    if args.mark_read:
        marked = mark_handled(args.mark_read)
        print(f"Marked {marked} callback(s) as handled.")
        return

    if args.mark_all_read:
        marked = mark_handled("", mark_all=True)
        print(f"Marked {marked} callback(s) as handled.")
        return

    entries = read_callbacks(show_all=args.all, prefix=args.prefix, limit=args.limit)
    if args.json:
        print(json.dumps(entries, indent=2))
    else:
        display_entries(entries)


if __name__ == "__main__":
    main()
