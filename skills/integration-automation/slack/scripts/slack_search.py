#!/usr/bin/env python3
"""
Search Slack messages, files, channels, and users across the workspace.

Usage:
    slack_search.py "deployment failed"
    slack_search.py "bug report" --channel "#engineering"
    slack_search.py "API update" --from "@tom"
    slack_search.py "release" --after 2026-02-01
    slack_search.py "architecture diagram" --files
    slack_search.py "onboarding" --rts --type channels
    slack_search.py "design doc" --rts --type files

Requires: SLACK_BOT_TOKEN environment variable
Optional: SLACK_USER_TOKEN for workspace-wide legacy search
Note: RTS API (assistant.search.context) is tried first when available.
      Falls back to search.messages/search.files automatically.
"""

import argparse
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _slack_utils import slack_api, format_ts, SlackError

_rts_available = None


def rts_search(query: str, count: int = 20, content_types: list = None,
               channel_types: list = None) -> dict:
    """Search via RTS API (assistant.search.context).

    Works with bot token. Requires search:read.* scopes.
    """
    params = {"query": query, "count": count}
    if content_types:
        params["content_types"] = ",".join(content_types)
    if channel_types:
        params["channel_types"] = ",".join(channel_types)
    return slack_api("assistant.search.context", **params)


def check_rts() -> bool:
    """Lazily detect whether RTS API is available."""
    global _rts_available
    if _rts_available is not None:
        return _rts_available
    try:
        rts_search("test", count=1)
        _rts_available = True
    except SlackError as e:
        if e.error in ("missing_scope", "not_allowed_token_type", "invalid_method",
                        "method_not_supported_for_channel_type"):
            _rts_available = False
        else:
            _rts_available = False
    return _rts_available


def search_messages(query: str, count: int = 20, sort: str = "timestamp",
                    page: int = 1) -> dict:
    return slack_api("search.messages", query=query, count=count,
                     sort=sort, sort_dir="desc", page=page)


def search_files(query: str, count: int = 20, page: int = 1) -> dict:
    return slack_api("search.files", query=query, count=count, page=page)


def search(query: str, count: int = 20, sort: str = "timestamp",
           page: int = 1, resource_type: str = "messages",
           force_legacy: bool = False, force_rts: bool = False) -> dict:
    """Unified search: RTS API first, legacy fallback.

    Args:
        resource_type: "messages", "files", "channels", "users"
        force_legacy: Skip RTS, use search.messages/search.files directly
        force_rts: Only use RTS, error if unavailable
    """
    if not force_legacy and (force_rts or check_rts()):
        return rts_search(query, count, content_types=[resource_type])

    if resource_type == "files":
        return search_files(query, count, page)
    return search_messages(query, count, sort, page)


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


def format_rts_result(result: dict) -> str:
    """Format a result from assistant.search.context."""
    rtype = result.get("type", "message")
    if rtype == "file":
        return format_file_match(result)
    if rtype == "channel":
        name = result.get("name", "unknown")
        cid = result.get("id", "")
        purpose = result.get("purpose", {})
        pval = purpose.get("value", "") if isinstance(purpose, dict) else str(purpose)
        line = f"#{name} ({cid})"
        if pval:
            line += f"\n  {pval[:200]}"
        return line
    if rtype == "user":
        name = result.get("real_name", result.get("name", "unknown"))
        uid = result.get("id", "")
        return f"@{name} ({uid})"
    return format_match(result)


def _extract_rts_results(data: dict) -> tuple:
    """Extract results list and total from RTS API response."""
    results = data.get("results", [])
    total = data.get("total", len(results))
    return results, total


def main():
    parser = argparse.ArgumentParser(description="Search Slack messages and files")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=20, help="Number of results (default: 20)")
    parser.add_argument("--channel", help="Filter to channel (#name)")
    parser.add_argument("--from", dest="from_user", help="Filter to user (@name)")
    parser.add_argument("--after", help="Messages after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Messages before date (YYYY-MM-DD)")
    parser.add_argument("--files", action="store_true", help="Search files instead of messages")
    parser.add_argument("--type", dest="resource_type",
                        choices=["messages", "files", "channels", "users"],
                        default=None, help="Resource type (RTS API)")
    parser.add_argument("--rts", action="store_true", help="Force RTS API (assistant.search.context)")
    parser.add_argument("--no-rts", action="store_true", help="Force legacy search (search.messages/files)")
    parser.add_argument("--sort", choices=["timestamp", "score"], default="timestamp",
                        help="Sort by timestamp or relevance (default: timestamp)")
    parser.add_argument("--page", type=int, default=1, help="Results page")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    resource_type = args.resource_type or ("files" if args.files else "messages")
    use_rts = args.rts or (args.resource_type is not None)
    use_legacy = args.no_rts

    try:
        query = build_query(args.query, args.channel, args.from_user, args.after, args.before)

        if use_rts and not use_legacy:
            result = search(query, args.num, args.sort, args.page,
                           resource_type, force_rts=True)
            results, total = _extract_rts_results(result)

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"{'='*60}")
                print(f"RTS Search: \"{args.query}\" — {len(results)} of {total} {resource_type}")
                print(f"{'='*60}")
                if not results:
                    print("No results found.")
                    return
                for r in results:
                    print(format_rts_result(r))
                    print()

        elif args.files or resource_type == "files":
            result = search_files(query, args.num, args.page)
            matches = result.get("files", {}).get("matches", [])
            total = result.get("files", {}).get("total", 0)

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"{'='*60}")
                print(f"Search: \"{args.query}\" — {len(matches)} of {total} files")
                print(f"{'='*60}")
                if not matches:
                    print("No results found.")
                    return
                for m in matches:
                    print(format_file_match(m))
                    print()

        else:
            result = search(query, args.num, args.sort, args.page,
                           resource_type, force_legacy=use_legacy)

            if check_rts() and not use_legacy:
                results, total = _extract_rts_results(result)
                if args.json:
                    print(json.dumps(result, indent=2))
                else:
                    print(f"{'='*60}")
                    print(f"RTS Search: \"{args.query}\" — {len(results)} of {total} {resource_type}")
                    print(f"{'='*60}")
                    if not results:
                        print("No results found.")
                        return
                    for r in results:
                        print(format_rts_result(r))
                        print()
            else:
                matches = result.get("messages", {}).get("matches", [])
                total = result.get("messages", {}).get("total", 0)
                if args.json:
                    print(json.dumps(result, indent=2))
                else:
                    print(f"{'='*60}")
                    print(f"Search: \"{args.query}\" — {len(matches)} of {total} messages")
                    print(f"{'='*60}")
                    if not matches:
                        print("No results found.")
                        return
                    for m in matches:
                        print(format_match(m))
                        print()

    except SlackError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
