#!/usr/bin/env python3
"""
Read inbound SMS inbox — messages collected by sms_listen.py daemon.

Usage:
    python3 sms_inbox.py                  # show all unhandled messages
    python3 sms_inbox.py --all            # show all (including handled)
    python3 sms_inbox.py -n 5             # last 5
    python3 sms_inbox.py --from +1732...  # filter by sender
    python3 sms_inbox.py --provider twilio  # filter by provider
    python3 sms_inbox.py --mark-read ID   # mark a message as handled
    python3 sms_inbox.py --mark-all-read  # mark all as handled
"""

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sms_utils import (
    read_inbox, mark_inbox_handled, mark_all_inbox_handled,
    get_listener_pid, format_timestamp, truncate, INBOX_PATH,
)


def print_messages(messages: list):
    """Print inbox messages in a readable format."""
    if not messages:
        print("No unhandled messages.")
        return

    for msg in messages:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg.get("ts", 0)))
        provider = msg.get("provider", "?")[:3]
        body = truncate(msg.get("body", ""), 100)
        handled = " [read]" if msg.get("handled") else ""
        msg_id = msg.get("id", "?")
        id_display = msg_id

        print(f"  {ts}  [{provider}] {msg['from']} → {msg.get('to', '?')}{handled}")
        print(f"    {body}")
        print(f"    ID: {id_display}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Read SMS inbound inbox")
    parser.add_argument("--all", action="store_true", help="Show all messages (including handled)")
    parser.add_argument("-n", "--limit", type=int, help="Number of messages to show")
    parser.add_argument("--from", dest="from_number", help="Filter by sender number")
    parser.add_argument("--provider", choices=["telnyx", "twilio"], help="Filter by provider")
    parser.add_argument("--mark-read", metavar="ID", help="Mark a specific message as handled")
    parser.add_argument("--mark-all-read", action="store_true", help="Mark all messages as handled")
    args = parser.parse_args()

    # Mark operations
    if args.mark_read:
        if mark_inbox_handled(args.mark_read):
            print(f"Marked {args.mark_read} as handled.")
        else:
            print(f"Message ID not found: {args.mark_read}", file=sys.stderr)
            sys.exit(1)
        return

    if args.mark_all_read:
        count = mark_all_inbox_handled()
        print(f"Marked {count} message(s) as handled.")
        return

    # Show listener status
    pid = get_listener_pid()
    if pid:
        print(f"Listener running (PID {pid})")
    else:
        print("Listener is not running. Start with: python3 sms_listen.py --bg")
    print()

    # Read and display
    if not INBOX_PATH.exists():
        print("No inbox file yet. Start the listener and receive some messages.")
        return

    messages = read_inbox(
        filter_handled=not args.all,
        from_number=args.from_number,
        provider=args.provider,
        limit=args.limit,
    )

    label = "All messages" if args.all else "Unhandled messages"
    print(f"{label} ({len(messages)}):")
    print_messages(messages)


if __name__ == "__main__":
    main()
