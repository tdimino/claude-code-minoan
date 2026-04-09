#!/usr/bin/env python3
"""
Delete Slack messages — single, batch, or thread cleanup.

Usage:
    slack_delete.py "CHANNEL" TS1 [TS2 TS3 ...]
    slack_delete.py "CHANNEL" --thread 1234567890.123456 [--all]
    slack_delete.py "CHANNEL" --thread 1234567890.123456 --before 1234567890.123456

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, resolve_channel, SlackError


def get_bot_user_id() -> str:
    """Get the bot's own user ID via auth.test."""
    data = slack_api("auth.test")
    return data.get("user_id", "")


def delete_message(channel_id: str, ts: str) -> dict:
    """Delete a single message. Returns API response."""
    return slack_api("chat.delete", channel=channel_id, ts=ts)


def get_thread_messages(channel_id: str, thread_ts: str) -> list:
    """Fetch all messages in a thread."""
    data = slack_api("conversations.replies", channel=channel_id, ts=thread_ts, limit=200)
    return data.get("messages", [])


def main():
    parser = argparse.ArgumentParser(description="Delete Slack messages")
    parser.add_argument("channel", help="Channel name (#general) or ID (C12345)")
    parser.add_argument("timestamps", nargs="*", help="Message timestamps to delete")
    parser.add_argument("--thread", help="Delete bot messages from this thread")
    parser.add_argument("--all", action="store_true",
                        help="With --thread: delete ALL bot messages including parent")
    parser.add_argument("--before", metavar="TS",
                        help="With --thread: only delete bot messages before this timestamp")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if not args.timestamps and not args.thread:
        parser.error("Provide timestamps or --thread")

    try:
        channel_id = resolve_channel(args.channel)
        results = []

        if args.thread:
            # Thread cleanup mode — delete bot's own messages
            bot_id = get_bot_user_id()
            messages = get_thread_messages(channel_id, args.thread)

            targets = []
            for msg in messages:
                if msg.get("user") != bot_id:
                    continue
                # Skip parent message unless --all
                if msg.get("ts") == args.thread and not args.all:
                    continue
                # Filter by --before if specified
                if args.before and float(msg["ts"]) >= float(args.before):
                    continue
                targets.append(msg["ts"])

            # Delete newest first
            targets.sort(reverse=True)

            for ts in targets:
                try:
                    delete_message(channel_id, ts)
                    results.append({"ts": ts, "ok": True})
                    # Respect rate limit (Tier 3: 50/min)
                    time.sleep(0.1)
                except SlackError as e:
                    results.append({"ts": ts, "ok": False, "error": str(e)})

        else:
            # Direct timestamp mode
            for ts in args.timestamps:
                try:
                    delete_message(channel_id, ts)
                    results.append({"ts": ts, "ok": True})
                    time.sleep(0.1)
                except SlackError as e:
                    results.append({"ts": ts, "ok": False, "error": str(e)})

        # Output
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            deleted = sum(1 for r in results if r["ok"])
            failed = sum(1 for r in results if not r["ok"])
            print(f"Deleted {deleted} message(s)" + (f", {failed} failed" if failed else ""))
            for r in results:
                if not r["ok"]:
                    print(f"  Failed: {r['ts']} — {r['error']}", file=sys.stderr)

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
