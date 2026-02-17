#!/usr/bin/env python3
"""
Post messages to Slack — send, reply, schedule, update, delete.

Usage:
    slack_post.py "#channel" "message text"
    slack_post.py "#channel" "reply" --thread 1234567890.123456
    slack_post.py "#channel" "reminder" --schedule "2026-02-12T09:00:00"
    slack_post.py "#channel" "updated" --update 1234567890.123456
    slack_post.py "#channel" --delete 1234567890.123456

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, resolve_channel, SlackError


def post_message(channel_id: str, text: str, thread_ts: str = None,
                 blocks: str = None, unfurl: bool = False) -> dict:
    params = {"channel": channel_id, "text": text}
    if thread_ts:
        params["thread_ts"] = thread_ts
    if blocks:
        params["blocks"] = json.loads(blocks)
    if unfurl:
        params["unfurl_links"] = True
        params["unfurl_media"] = True
    return slack_api("chat.postMessage", **params)


def schedule_message(channel_id: str, text: str, post_at: str, thread_ts: str = None) -> dict:
    dt = datetime.fromisoformat(post_at)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    params = {
        "channel": channel_id,
        "text": text,
        "post_at": int(dt.timestamp()),
    }
    if thread_ts:
        params["thread_ts"] = thread_ts
    return slack_api("chat.scheduleMessage", **params)


def update_message(channel_id: str, ts: str, text: str) -> dict:
    return slack_api("chat.update", channel=channel_id, ts=ts, text=text)


def delete_message(channel_id: str, ts: str) -> dict:
    return slack_api("chat.delete", channel=channel_id, ts=ts)


def main():
    parser = argparse.ArgumentParser(description="Post messages to Slack")
    parser.add_argument("channel", help="Channel name (#general) or ID (C12345)")
    parser.add_argument("text", nargs="?", default="", help="Message text")
    parser.add_argument("--thread", help="Thread timestamp to reply to")
    parser.add_argument("--blocks", help="JSON blocks for rich formatting")
    parser.add_argument("--schedule", help="ISO datetime to schedule message (e.g. 2026-02-12T09:00:00)")
    parser.add_argument("--update", help="Timestamp of message to update")
    parser.add_argument("--delete", help="Timestamp of message to delete")
    parser.add_argument("--unfurl", action="store_true", help="Unfurl links in message")
    parser.add_argument("--json", action="store_true", help="Output raw JSON response")
    args = parser.parse_args()

    try:
        channel_id = resolve_channel(args.channel)

        if args.delete:
            result = delete_message(channel_id, args.delete)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Deleted message {args.delete} from {args.channel}")

        elif args.update:
            if not args.text:
                print("Error: --update requires message text", file=sys.stderr)
                sys.exit(1)
            result = update_message(channel_id, args.update, args.text)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Updated message {args.update} in {args.channel}")

        elif args.schedule:
            if not args.text:
                print("Error: --schedule requires message text", file=sys.stderr)
                sys.exit(1)
            result = schedule_message(channel_id, args.text, args.schedule, args.thread)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                ts = result.get("scheduled_message_id", "")
                print(f"Scheduled message in {args.channel} (id: {ts})")

        else:
            if not args.text:
                print("Error: message text required", file=sys.stderr)
                sys.exit(1)
            result = post_message(channel_id, args.text, args.thread, args.blocks, args.unfurl)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                ts = result.get("ts", "")
                thread_info = f" (thread: {args.thread})" if args.thread else ""
                print(f"Posted to {args.channel}{thread_info} [ts: {ts}]")

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
