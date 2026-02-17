"""
Shared Slack API utilities — auth, rate limiting, API calls, formatters.

All slack_*.py scripts import from this module.

Requires: SLACK_BOT_TOKEN environment variable (xoxb-*)
Install: pip install requests
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
BASE_URL = "https://slack.com/api"

# Slack rate limits (corrected Feb 2026 per official docs)
# Tier 1 reduction (1/min) only applies to conversations.history/replies
# for commercially-distributed non-Marketplace apps. Internal apps get Tier 3.
RATE_LIMITS = {
    "conversations.history":  {"calls": 1, "period": 60},   # Tier 1 (commercial non-Marketplace)
    "conversations.replies":  {"calls": 1, "period": 60},   # Tier 1 (commercial non-Marketplace)
    "conversations.list":     {"calls": 20, "period": 60},  # Tier 2
    "conversations.info":     {"calls": 50, "period": 60},  # Tier 3
    "conversations.join":     {"calls": 50, "period": 60},  # Tier 3
    "chat.postMessage":       {"calls": 1, "period": 1},    # Special (1/sec/channel)
    "chat.update":            {"calls": 50, "period": 60},  # Tier 3
    "chat.delete":            {"calls": 50, "period": 60},  # Tier 3
    "chat.scheduleMessage":   {"calls": 50, "period": 60},  # Tier 3
    "search.messages":        {"calls": 20, "period": 60},  # Tier 2 (bot: channels bot is in only)
    "search.files":           {"calls": 20, "period": 60},  # Tier 2
    "reactions.add":          {"calls": 50, "period": 60},  # Tier 3
    "reactions.remove":       {"calls": 50, "period": 60},  # Tier 3
    "reactions.get":          {"calls": 50, "period": 60},  # Tier 3
    "users.list":             {"calls": 20, "period": 60},  # Tier 2
    "users.info":             {"calls": 50, "period": 60},  # Tier 3
    "users.lookupByEmail":    {"calls": 50, "period": 60},  # Tier 3
    "files.getUploadURLExternal":   {"calls": 100, "period": 60},  # Tier 4
    "files.completeUploadExternal": {"calls": 100, "period": 60},  # Tier 4
}

# Track last call time per method for local rate limiting
_last_call: Dict[str, float] = {}


class SlackError(Exception):
    """Raised when Slack API returns an error."""
    def __init__(self, method: str, error: str, detail: str = ""):
        self.method = method
        self.error = error
        self.detail = detail
        super().__init__(f"{method}: {error}" + (f" — {detail}" if detail else ""))


def _headers() -> Dict[str, str]:
    if not SLACK_BOT_TOKEN:
        print("Error: SLACK_BOT_TOKEN not set.", file=sys.stderr)
        print("Get a Bot token at https://api.slack.com/apps", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }


def _enforce_rate_limit(method: str):
    """Sleep if needed to respect per-method rate limits."""
    limit = RATE_LIMITS.get(method)
    if not limit:
        return
    min_interval = limit["period"] / limit["calls"]
    last = _last_call.get(method, 0)
    elapsed = time.time() - last
    if elapsed < min_interval:
        wait = min_interval - elapsed
        if wait > 5:
            print(f"  [rate limit] Waiting {wait:.0f}s for {method}...", file=sys.stderr)
        time.sleep(wait)
    _last_call[method] = time.time()


# Methods that require form-encoded data instead of JSON
_FORM_ENCODED_METHODS = {
    "files.getUploadURLExternal",
}

# Methods that must use GET with query params (not POST with JSON body).
# Slack's list/query endpoints ignore JSON body params for the types filter.
_GET_METHODS = {
    "conversations.list",
    "conversations.history",
    "conversations.replies",
    "conversations.info",
    "conversations.members",
    "users.list",
    "users.info",
    "users.lookupByEmail",
    "users.conversations",
    "search.messages",
    "search.files",
    "reactions.get",
}


def slack_api(method: str, retries: int = 2, **params) -> Dict[str, Any]:
    """
    Call a Slack Web API method. Handles rate limiting and retries.

    Args:
        method: Slack API method (e.g. "chat.postMessage")
        retries: Number of 429 retries (default 2)
        **params: Method parameters

    Returns:
        Parsed JSON response dict

    Raises:
        SlackError: If Slack returns ok=false
    """
    _enforce_rate_limit(method)

    for attempt in range(retries + 1):
        if method in _GET_METHODS:
            resp = requests.get(
                f"{BASE_URL}/{method}",
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                params=params,
            )
        elif method in _FORM_ENCODED_METHODS:
            resp = requests.post(
                f"{BASE_URL}/{method}",
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                data=params,
            )
        else:
            resp = requests.post(
                f"{BASE_URL}/{method}",
                headers=_headers(),
                json=params,
            )

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 30))
            if attempt < retries:
                print(f"  [429] Rate limited on {method}, retrying in {retry_after}s...", file=sys.stderr)
                time.sleep(retry_after)
                continue
            else:
                raise SlackError(method, "rate_limited", f"Retry-After: {retry_after}s")

        resp.raise_for_status()
        data = resp.json()

        if not data.get("ok"):
            raise SlackError(method, data.get("error", "unknown"), data.get("detail", ""))

        return data

    raise SlackError(method, "max_retries", "Exhausted retries")


def paginate(method: str, result_key: str, limit: int = 200, max_pages: int = 5, **params) -> List[Dict]:
    """
    Cursor-based pagination for Slack list endpoints.

    Args:
        method: API method
        result_key: Key in response containing the list (e.g. "channels", "members")
        limit: Items per page (max 1000, default 200)
        max_pages: Safety limit on pages fetched
        **params: Additional method parameters

    Returns:
        Flat list of all items across pages
    """
    all_items = []
    cursor = None

    for page in range(max_pages):
        call_params = {**params, "limit": limit}
        if cursor:
            call_params["cursor"] = cursor

        data = slack_api(method, **call_params)
        items = data.get(result_key, [])
        all_items.extend(items)

        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break

        slow_methods = {"conversations.history", "conversations.replies"}
        if method in slow_methods and page < max_pages - 1:
            print(f"  [pagination] Page {page + 2} of {method} (Tier 1 = 1/min)...", file=sys.stderr)

    return all_items


_channel_cache: Dict[str, str] = {}


def resolve_channel(channel: str) -> str:
    """
    Resolve a channel name (like #general) to a channel ID (like C12345).
    If already an ID (starts with C/G/D), return as-is.
    Results are cached to avoid repeated Tier 1 API calls.
    """
    if not channel or channel == "#":
        raise SlackError("resolve_channel", "invalid_channel", "Channel name cannot be empty")

    if channel.startswith(("C", "G", "D")) and len(channel) >= 9:
        return channel

    name = channel.lstrip("#").lower()

    # Check cache first (avoids Tier 1 rate limit hit)
    if name in _channel_cache:
        return _channel_cache[name]

    channels = paginate("conversations.list", "channels", types="public_channel,private_channel")

    for ch in channels:
        ch_name = ch["name"].lower()
        _channel_cache[ch_name] = ch["id"]
        if ch_name == name:
            return ch["id"]

    raise SlackError("resolve_channel", "channel_not_found", f"No channel named #{name}")


def format_ts(ts: str) -> str:
    """Convert Slack timestamp (e.g. '1234567890.123456') to human-readable."""
    try:
        dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, TypeError, OSError):
        return ts


def format_message(msg: Dict, resolve_users: bool = False) -> str:
    """Format a Slack message dict to readable text."""
    user = msg.get("user", msg.get("bot_id", "unknown"))
    ts = format_ts(msg.get("ts", ""))
    text = msg.get("text", "")

    # Resolve user ID to display name
    if resolve_users and user.startswith("U"):
        try:
            info = slack_api("users.info", user=user)
            profile = info.get("user", {}).get("profile", {})
            user = profile.get("display_name") or profile.get("real_name", user)
        except SlackError:
            pass

    lines = [f"[{ts}] {user}:"]
    if text:
        lines.append(f"  {text}")

    # Attachments
    for att in msg.get("attachments", []):
        if att.get("text"):
            lines.append(f"  [attachment] {att['text'][:200]}")

    # Files
    for f in msg.get("files", []):
        lines.append(f"  [file] {f.get('name', 'unnamed')} ({f.get('mimetype', '')})")

    return "\n".join(lines)
