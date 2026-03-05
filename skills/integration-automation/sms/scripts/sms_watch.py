#!/usr/bin/env python3
"""
Background SMS watcher for Claude Code sessions.

Polls inbox.jsonl for new unhandled messages. Exits when one is detected,
printing a structured line that Claude Code can parse. Designed to be run
as a `run_in_background` bash task — the exit-on-detect pattern chains
naturally with Claude Code's background task notification system.

Usage:
    python3 sms_watch.py [--interval 5]
    python3 sms_watch.py --enrich          # also print memory context on detect

Output on detect:
    NEW_SMS|{full_id}|{from}|{to}|{body}

Output on detect with --enrich:
    NEW_SMS|{full_id}|{from}|{to}|{body}
    ---MEMORY_CONTEXT---
    ## User Model
    ...
    ## Soul State
    ...
    ## Recent Conversation
    ...

Output on no activity (script killed by timeout):
    NO_NEW_SMS
"""

import argparse
import json
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sms_utils import read_inbox

DEFAULT_INTERVAL = 5  # seconds


def get_known_ids() -> set:
    """Snapshot current unhandled message IDs."""
    msgs = read_inbox(filter_handled=True)
    return {m.get("id") for m in msgs if m.get("id")}


def print_memory_context(phone: str) -> None:
    """Load and print sender's memory context for the session to consume."""
    import sms_memory as m

    model = m.ensure_user_model(phone)
    soul = m.format_soul_state()
    recent = m.get_recent_memory(phone, limit=10)
    formatted = m.format_working_memory(recent)

    print("---MEMORY_CONTEXT---", flush=True)
    print("## User Model")
    print(model)
    if soul:
        print(soul)
    if formatted:
        print("## Recent Conversation")
        print(formatted)


def watch(interval: int, enrich: bool = False) -> None:
    """Poll inbox until a new unhandled message appears, then exit."""
    known = get_known_ids()

    while True:
        time.sleep(interval)
        current = read_inbox(filter_handled=True)
        for msg in current:
            msg_id = msg.get("id")
            if msg_id and msg_id not in known:
                body = msg.get("body", "").strip()
                sender = msg.get("from", "?")
                to = msg.get("to", "?")
                print(json.dumps({"event": "NEW_SMS", "id": msg_id,
                                  "from": sender, "to": to, "body": body}),
                      flush=True)
                if enrich:
                    print_memory_context(sender)
                sys.exit(0)


def handle_signal(signum, frame):
    print("NO_NEW_SMS", flush=True)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Watch for new inbound SMS")
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL,
        help=f"Poll interval in seconds (default: {DEFAULT_INTERVAL})"
    )
    parser.add_argument(
        "--enrich", action="store_true",
        help="On detect, also print sender's memory context (user model, soul state, recent conversation)"
    )
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    mode = "enriched " if args.enrich else ""
    print(f"SMS watcher started — {mode}polling every {args.interval}s for new messages...", flush=True)
    watch(args.interval, enrich=args.enrich)


if __name__ == "__main__":
    main()
