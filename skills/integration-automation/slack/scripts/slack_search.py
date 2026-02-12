#!/usr/bin/env python3
"""
Search Slack messages and files across the workspace.

Usage:
    slack_search.py "deployment failed"
    slack_search.py "bug report" --channel "#engineering"
    slack_search.py "API update" --from "@tom"
    slack_search.py "release" --after 2026-02-01
    slack_search.py "architecture diagram" --files

Requires: SLACK_BOT_TOKEN environment variable
Note: search.messages requires a User token for full results.
      Bot tokens can search channels the bot is a member of.
"""

import argparse
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, format_ts, SlackError


def search_messages(query: str, count: int = 20, sort: str = "timestamp",
                    page: int = 1) -> dict:
    return slack_api("search.messages", query=query, count=count,
                     sort=sort, sort_dir="desc", page=page)


def search_files(query: str, count: int = 20, page: int = 1) -> dict:
    return slack_api("search.files", query=query, count=count, page=page)


def build_query(base: str, channel: str = None, user: str = None,
                after: str = None, before: str = None) -> str:
    """Build Slack search query with modifiers."""
    parts = [base]
    if channel:
        parts.append(f"in:{channel.lstrip('#')}")
    if user:
        parts.append(f"from:{user.lstrip('@')}")
    if after:
        parts.append(f"after:{after}")
    if before:
        parts.append(f"before:{before}")
    return " ".join(parts)


def format_match(match: dict) -> str:
    """Format a search result match."""
    ts = format_ts(match.get("ts", ""))
    user = match.get("username", match.get("user", "unknown"))
    channel = match.get("channel", {})
    ch_name = channel.get("name", "unknown") if isinstance(channel, dict) else str(channel)
    text = match.get("text", "")[:300]
    permalink = match.get("permalink", "")

    lines = [f"[{ts}] #{ch_name} — {user}:"]
    if text:
        lines.append(f"  {text}")
    if permalink:
        lines.append(f"  {permalink}")
    return "\n".join(lines)


def format_file_match(match: dict) -> str:
    """Format a file search result."""
    name = match.get("name", "unnamed")
    filetype = match.get("filetype", "")
    user = match.get("username", match.get("user", "unknown"))
    created = format_ts(str(match.get("created", "")))
    permalink = match.get("permalink", "")

    lines = [f"[{created}] {name} ({filetype}) — {user}"]
    if permalink:
        lines.append(f"  {permalink}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search Slack messages and files")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=20, help="Number of results (default: 20)")
    parser.add_argument("--channel", help="Filter to channel (#name)")
    parser.add_argument("--from", dest="from_user", help="Filter to user (@name)")
    parser.add_argument("--after", help="Messages after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Messages before date (YYYY-MM-DD)")
    parser.add_argument("--files", action="store_true", help="Search files instead of messages")
    parser.add_argument("--sort", choices=["timestamp", "score"], default="timestamp",
                        help="Sort by timestamp or relevance (default: timestamp)")
    parser.add_argument("--page", type=int, default=1, help="Results page")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    try:
        query = build_query(args.query, args.channel, args.from_user, args.after, args.before)

        if args.files:
            result = search_files(query, args.num, args.page)
            matches = result.get("files", {}).get("matches", [])
            total = result.get("files", {}).get("total", 0)
        else:
            result = search_messages(query, args.num, args.sort, args.page)
            matches = result.get("messages", {}).get("matches", [])
            total = result.get("messages", {}).get("total", 0)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            kind = "files" if args.files else "messages"
            print(f"{'='*60}")
            print(f"Search: \"{args.query}\" — {len(matches)} of {total} {kind}")
            print(f"{'='*60}")

            if not matches:
                print("No results found.")
                return

            formatter = format_file_match if args.files else format_match
            for m in matches:
                print(formatter(m))
                print()

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
