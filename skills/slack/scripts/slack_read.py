#!/usr/bin/env python3
"""
Read Slack channel history and thread replies.

Usage:
    slack_read.py "#general"
    slack_read.py "#general" -n 20
    slack_read.py "#general" --thread 1234567890.123456
    slack_read.py "#general" --since "2026-02-11"
    slack_read.py "#general" --resolve-users

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, resolve_channel, format_message, format_ts, SlackError


def read_history(channel_id: str, limit: int = 10, oldest: str = None) -> list:
    params = {"channel": channel_id, "limit": min(limit, 1000)}
    if oldest:
        params["oldest"] = oldest
    data = slack_api("conversations.history", **params)
    messages = data.get("messages", [])
    messages.reverse()  # Chronological order (oldest first)
    return messages[:limit]


def read_thread(channel_id: str, thread_ts: str, limit: int = 100) -> list:
    data = slack_api("conversations.replies", channel=channel_id, ts=thread_ts, limit=min(limit, 1000))
    return data.get("messages", [])


def main():
    parser = argparse.ArgumentParser(description="Read Slack channel history")
    parser.add_argument("channel", help="Channel name (#general) or ID")
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of messages (default: 10)")
    parser.add_argument("--thread", help="Thread timestamp to read replies")
    parser.add_argument("--since", help="Read messages since date (YYYY-MM-DD or ISO datetime)")
    parser.add_argument("--resolve-users", action="store_true", help="Resolve user IDs to names (slower)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        channel_id = resolve_channel(args.channel)

        oldest = None
        if args.since:
            dt = datetime.fromisoformat(args.since)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            oldest = str(dt.timestamp())

        if args.thread:
            messages = read_thread(channel_id, args.thread, args.num)
        else:
            messages = read_history(channel_id, args.num, oldest)

        if args.json:
            print(json.dumps(messages, indent=2))
        else:
            if not messages:
                print("No messages found.")
                return

            header = f"Thread {args.thread}" if args.thread else args.channel
            print(f"{'='*60}")
            print(f"{header} — {len(messages)} messages")
            print(f"{'='*60}")

            for msg in messages:
                print(format_message(msg, resolve_users=args.resolve_users))
                print()

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
