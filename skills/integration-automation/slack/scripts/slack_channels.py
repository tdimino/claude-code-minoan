#!/usr/bin/env python3
"""
List, inspect, and join Slack channels.

Usage:
    slack_channels.py                       # List all channels
    slack_channels.py --members             # Include member counts
    slack_channels.py --info "#general"     # Get channel details
    slack_channels.py --join "#new-channel" # Join a channel
    slack_channels.py --filter "eng-"       # Filter by name pattern

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, paginate, resolve_channel, SlackError


def list_channels(types: str = "public_channel,private_channel",
                  include_members: bool = False) -> list:
    channels = paginate("conversations.list", "channels", types=types)
    if include_members:
        # conversations.list doesn't return num_members by default for all types
        # but it does for public channels. For accuracy, we return what we have.
        pass
    return channels


def get_channel_info(channel_id: str) -> dict:
    data = slack_api("conversations.info", channel=channel_id, include_num_members=True)
    return data.get("channel", {})


def join_channel(channel_id: str) -> dict:
    return slack_api("conversations.join", channel=channel_id)


def format_channel(ch: dict, show_members: bool = False) -> str:
    name = ch.get("name", "unnamed")
    cid = ch.get("id", "")
    purpose = ch.get("purpose", {}).get("value", "")[:80]
    is_member = "+" if ch.get("is_member") else " "
    members = f" ({ch.get('num_members', '?')} members)" if show_members else ""

    line = f"  {is_member} #{name:<30} {cid}{members}"
    if purpose:
        line += f"\n    {purpose}"
    return line


def main():
    parser = argparse.ArgumentParser(description="Manage Slack channels")
    parser.add_argument("--info", help="Get detailed info for a channel")
    parser.add_argument("--join", help="Join a channel")
    parser.add_argument("--filter", help="Filter channels by name pattern")
    parser.add_argument("--members", action="store_true", help="Show member counts")
    parser.add_argument("--private", action="store_true", help="Include private channels")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        if args.info:
            channel_id = resolve_channel(args.info)
            info = get_channel_info(channel_id)
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print(f"Channel: #{info.get('name', '')}")
                print(f"ID: {info.get('id', '')}")
                print(f"Members: {info.get('num_members', '?')}")
                print(f"Created: {info.get('created', '')}")
                purpose = info.get("purpose", {}).get("value", "")
                if purpose:
                    print(f"Purpose: {purpose}")
                topic = info.get("topic", {}).get("value", "")
                if topic:
                    print(f"Topic: {topic}")
                print(f"Archived: {info.get('is_archived', False)}")
                print(f"Member: {info.get('is_member', False)}")

        elif args.join:
            channel_id = resolve_channel(args.join)
            join_channel(channel_id)
            print(f"Joined {args.join}")

        else:
            types = "public_channel"
            if args.private:
                types += ",private_channel"
            channels = list_channels(types, args.members)

            if args.filter:
                pattern = args.filter.lower()
                channels = [c for c in channels if pattern in c.get("name", "").lower()]

            channels.sort(key=lambda c: c.get("name", ""))

            if args.json:
                print(json.dumps(channels, indent=2))
            else:
                print(f"{'='*60}")
                print(f"Channels ({len(channels)}) — '+' = bot is a member")
                print(f"{'='*60}")
                for ch in channels:
                    print(format_channel(ch, args.members))

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
