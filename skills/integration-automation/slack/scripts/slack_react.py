#!/usr/bin/env python3
"""
Add, remove, or list reactions on Slack messages.

Usage:
    slack_react.py "#general" 1234567890.123456 rocket
    slack_react.py "#general" 1234567890.123456 rocket --remove
    slack_react.py "#general" 1234567890.123456 --list

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, resolve_channel, SlackError


def add_reaction(channel_id: str, timestamp: str, emoji: str) -> dict:
    return slack_api("reactions.add", channel=channel_id, timestamp=timestamp, name=emoji)


def remove_reaction(channel_id: str, timestamp: str, emoji: str) -> dict:
    return slack_api("reactions.remove", channel=channel_id, timestamp=timestamp, name=emoji)


def list_reactions(channel_id: str, timestamp: str) -> list:
    data = slack_api("reactions.get", channel=channel_id, timestamp=timestamp)
    msg = data.get("message", {})
    return msg.get("reactions", [])


def main():
    parser = argparse.ArgumentParser(description="Manage Slack reactions")
    parser.add_argument("channel", help="Channel name (#general) or ID")
    parser.add_argument("timestamp", help="Message timestamp")
    parser.add_argument("emoji", nargs="?", help="Emoji name (without colons)")
    parser.add_argument("--remove", action="store_true", help="Remove reaction instead of adding")
    parser.add_argument("--list", action="store_true", help="List reactions on message")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        channel_id = resolve_channel(args.channel)

        if args.list:
            reactions = list_reactions(channel_id, args.timestamp)
            if args.json:
                print(json.dumps(reactions, indent=2))
            else:
                if not reactions:
                    print("No reactions on this message.")
                else:
                    for r in reactions:
                        users = ", ".join(r.get("users", []))
                        print(f":{r['name']}: ({r.get('count', 0)}) — {users}")

        elif not args.emoji:
            print("Error: emoji name required (or use --list)", file=sys.stderr)
            sys.exit(1)

        elif args.remove:
            remove_reaction(channel_id, args.timestamp, args.emoji)
            print(f"Removed :{args.emoji}: from message {args.timestamp}")

        else:
            add_reaction(channel_id, args.timestamp, args.emoji)
            print(f"Added :{args.emoji}: to message {args.timestamp}")

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
