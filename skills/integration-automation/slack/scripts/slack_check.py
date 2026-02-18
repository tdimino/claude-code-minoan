#!/usr/bin/env python3
"""
Read and manage unhandled messages from the Slack inbox.

The inbox (daemon/inbox.jsonl) is populated by slack_listen.py.
This script reads unhandled entries and provides ack/clear operations.

Usage:
    slack_check.py              # show unhandled messages
    slack_check.py --ack 1      # mark message #1 as handled
    slack_check.py --ack-all    # mark all as handled
    slack_check.py --clear      # delete inbox file
    slack_check.py --quiet      # one-line summary (for hooks), silent if none

Output format (default):
    [1] #C12345 | Tom (thread: 1234567890.123456): "What's the status?"
    [2] DM:D456 | Alice (thread: 1234567890.789012): "Check the tests"
"""

import argparse
import json
import os
import sys

DAEMON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daemon")
INBOX = os.path.join(DAEMON_DIR, "inbox.jsonl")


def _read_inbox():
    """Read all entries from inbox.jsonl."""
    if not os.path.exists(INBOX):
        return []
    entries = []
    with open(INBOX) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def _write_inbox(entries):
    """Rewrite inbox.jsonl with updated entries."""
    with open(INBOX, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _unhandled(entries):
    """Filter to unhandled entries, return list of (original_index, entry)."""
    return [(i, e) for i, e in enumerate(entries) if not e.get("handled")]


def cmd_show(quiet=False):
    """Show unhandled messages."""
    entries = _read_inbox()
    unhandled = _unhandled(entries)

    if not unhandled:
        if not quiet:
            print("No unhandled Slack messages.")
        return

    if quiet:
        count = len(unhandled)
        print(f"[Slack: {count} unhandled message{'s' if count != 1 else ''} -- run /slack-check to view]")
        return

    for display_num, (_, entry) in enumerate(unhandled, 1):
        channel = entry.get("channel", "?")
        name = entry.get("display_name", entry.get("user_id", "?"))
        thread_ts = entry.get("thread_ts", "?")
        text = entry.get("text", "")

        # Format channel — DM channels start with D
        if channel.startswith("D"):
            ch_label = f"DM:{channel}"
        else:
            ch_label = f"#{channel}"

        # Truncate long messages for display
        if len(text) > 200:
            text = text[:200] + "..."

        print(f'[{display_num}] {ch_label} | {name} (thread: {thread_ts}): "{text}"')


def cmd_ack(number):
    """Mark a specific unhandled message as handled (by display number)."""
    entries = _read_inbox()
    unhandled = _unhandled(entries)

    if number < 1 or number > len(unhandled):
        print(f"Error: message #{number} not found. {len(unhandled)} unhandled messages.", file=sys.stderr)
        sys.exit(1)

    original_idx = unhandled[number - 1][0]
    entries[original_idx]["handled"] = True
    _write_inbox(entries)
    print(f"Message #{number} marked as handled.")


def cmd_ack_all():
    """Mark all messages as handled."""
    entries = _read_inbox()
    count = 0
    for entry in entries:
        if not entry.get("handled"):
            entry["handled"] = True
            count += 1
    _write_inbox(entries)
    print(f"Marked {count} message{'s' if count != 1 else ''} as handled.")


def cmd_clear():
    """Delete the inbox file entirely."""
    try:
        os.remove(INBOX)
        print("Inbox cleared.")
    except FileNotFoundError:
        print("Inbox already empty.")


def main():
    parser = argparse.ArgumentParser(description="Check Slack inbox")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ack", type=int, metavar="N", help="Mark message #N as handled")
    group.add_argument("--ack-all", action="store_true", help="Mark all as handled")
    group.add_argument("--clear", action="store_true", help="Delete inbox file")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="One-line summary (for hooks), silent if none")
    args = parser.parse_args()

    if args.ack:
        cmd_ack(args.ack)
    elif args.ack_all:
        cmd_ack_all()
    elif args.clear:
        cmd_clear()
    else:
        cmd_show(quiet=args.quiet)


if __name__ == "__main__":
    main()
