#!/usr/bin/env python3
"""
Check the shared Claudicle inbox for unhandled Telegram messages.

Reads from ~/.claudicle/daemon/inbox.jsonl, filters for telegram:* channels.

Usage:
    python3 telegram_check.py                    # Unhandled entries
    python3 telegram_check.py --all              # All entries
    python3 telegram_check.py --limit 5          # Last 5
    python3 telegram_check.py --mark-read MSG_TS # Mark entry handled
    python3 telegram_check.py --mark-all-read    # Mark all handled
"""

import argparse
import fcntl
import json
import os
import sys
import time

INBOX_PATH = os.path.expanduser("~/.claudicle/daemon/inbox.jsonl")


def read_inbox(show_all: bool = False, limit: int = 0) -> list[dict]:
    if not os.path.isfile(INBOX_PATH):
        return []

    entries = []
    with open(INBOX_PATH) as f:
        for line in f:
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
            if not show_all and entry.get("handled"):
                continue
            entries.append(entry)

    if limit > 0:
        entries = entries[-limit:]
    return entries


def mark_handled(target_ts: str):
    if not os.path.isfile(INBOX_PATH):
        print("No inbox file found.", file=sys.stderr)
        return

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
            if (entry.get("channel", "").startswith("telegram:")
                    and str(entry.get("ts", "")) == target_ts
                    and not entry.get("handled")):
                entry["handled"] = True
                marked += 1
            new_lines.append(json.dumps(entry) + "\n")
        f.seek(0)
        f.writelines(new_lines)
        f.truncate()
    print(f"Marked {marked} entry/entries as handled.")


def mark_all_handled():
    if not os.path.isfile(INBOX_PATH):
        print("No inbox file found.", file=sys.stderr)
        return

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
            if (entry.get("channel", "").startswith("telegram:")
                    and not entry.get("handled")):
                entry["handled"] = True
                marked += 1
            new_lines.append(json.dumps(entry) + "\n")
        f.seek(0)
        f.writelines(new_lines)
        f.truncate()
    print(f"Marked {marked} Telegram entries as handled.")


def display_entries(entries: list[dict]):
    if not entries:
        print("No Telegram messages in inbox.")
        return

    for entry in entries:
        ts = entry.get("ts", 0)
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "?"
        name = entry.get("display_name", entry.get("user_id", "?"))
        channel = entry.get("channel", "?")
        text = entry.get("text", "")[:120]
        handled = "HANDLED" if entry.get("handled") else "NEW"
        thread = entry.get("thread_ts", "")

        print(f"[{ts_str}] [{handled}] {name} in {channel}")
        if thread:
            print(f"  thread: {thread}")
        print(f"  {text}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Check Telegram inbox")
    parser.add_argument("--all", action="store_true", help="Show all entries (including handled)")
    parser.add_argument("--limit", type=int, default=0, help="Show last N entries")
    parser.add_argument("--mark-read", metavar="TS", help="Mark entry with this timestamp as handled")
    parser.add_argument("--mark-all-read", action="store_true", help="Mark all Telegram entries as handled")
    args = parser.parse_args()

    if args.mark_read:
        mark_handled(args.mark_read)
    elif args.mark_all_read:
        mark_all_handled()
    else:
        entries = read_inbox(show_all=args.all, limit=args.limit)
        display_entries(entries)


if __name__ == "__main__":
    main()
