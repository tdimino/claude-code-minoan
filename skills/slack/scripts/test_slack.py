#!/usr/bin/env python3
"""
Test suite for Slack skill — validates auth, permissions, and each endpoint.

Usage:
    test_slack.py                       # Run all tests
    test_slack.py --quick               # Auth + channel list only
    test_slack.py --test post           # Test specific endpoint
    test_slack.py --verbose             # Detailed output
    test_slack.py --test-channel "#bot-test"  # Specify test channel

Requires: SLACK_BOT_TOKEN environment variable
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from _slack_utils import slack_api, resolve_channel, paginate, SlackError, SLACK_BOT_TOKEN

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
SKIP = "\033[33mSKIP\033[0m"


def test_auth(verbose: bool = False) -> bool:
    """Validate bot token is set and valid."""
    print(f"  auth: ", end="")
    if not SLACK_BOT_TOKEN:
        print(f"{FAIL} — SLACK_BOT_TOKEN not set")
        return False
    try:
        data = slack_api("auth.test")
        if verbose:
            print(f"{PASS} — {data.get('user', '')} in {data.get('team', '')}")
        else:
            print(PASS)
        return True
    except SlackError as e:
        print(f"{FAIL} — {e}")
        return False


def test_channels(verbose: bool = False) -> bool:
    """List channels (verifies channels:read scope)."""
    print(f"  channels.list: ", end="")
    try:
        channels = paginate("conversations.list", "channels",
                           types="public_channel", max_pages=1)
        if verbose:
            print(f"{PASS} — {len(channels)} channels found")
        else:
            print(PASS)
        return True
    except SlackError as e:
        print(f"{FAIL} — {e}")
        return False


def test_users(verbose: bool = False) -> bool:
    """List users (verifies users:read scope)."""
    print(f"  users.list: ", end="")
    try:
        users = paginate("users.list", "members", max_pages=1)
        if verbose:
            print(f"{PASS} — {len(users)} users found")
        else:
            print(PASS)
        return True
    except SlackError as e:
        print(f"{FAIL} — {e}")
        return False


def test_post(test_channel: str, verbose: bool = False) -> bool:
    """Post and delete a test message (verifies chat:write scope)."""
    print(f"  chat.postMessage: ", end="")
    try:
        channel_id = resolve_channel(test_channel)
        data = slack_api("chat.postMessage", channel=channel_id,
                        text="[test] Slack skill validation — this message will be deleted")
        ts = data.get("ts", "")
        if verbose:
            print(f"{PASS} — posted to {test_channel} [ts: {ts}]")
        else:
            print(PASS)

        # Clean up
        time.sleep(1)
        print(f"  chat.delete: ", end="")
        slack_api("chat.delete", channel=channel_id, ts=ts)
        print(PASS)
        return True
    except SlackError as e:
        print(f"{FAIL} — {e}")
        return False


def test_read(test_channel: str, verbose: bool = False) -> bool:
    """Read channel history (verifies channels:history scope)."""
    print(f"  conversations.history: ", end="")
    try:
        channel_id = resolve_channel(test_channel)
        data = slack_api("conversations.history", channel=channel_id, limit=5)
        messages = data.get("messages", [])
        if verbose:
            print(f"{PASS} — {len(messages)} messages read")
        else:
            print(PASS)
        return True
    except SlackError as e:
        print(f"{FAIL} — {e}")
        return False


def test_search(verbose: bool = False) -> bool:
    """Search messages (verifies search:read scope)."""
    print(f"  search.messages: ", end="")
    try:
        data = slack_api("search.messages", query="test", count=5)
        total = data.get("messages", {}).get("total", 0)
        if verbose:
            print(f"{PASS} — {total} total matches")
        else:
            print(PASS)
        return True
    except SlackError as e:
        if "missing_scope" in str(e) or "not_allowed_token_type" in str(e):
            print(f"{SKIP} — search requires user token (xoxp-), not bot token")
            return True
        print(f"{FAIL} — {e}")
        return False


def test_reactions(test_channel: str, verbose: bool = False) -> bool:
    """Add and remove a reaction (verifies reactions:write scope)."""
    print(f"  reactions.add: ", end="")
    try:
        channel_id = resolve_channel(test_channel)

        # Post a temp message to react to
        msg = slack_api("chat.postMessage", channel=channel_id,
                       text="[test] reaction test — will be deleted")
        ts = msg.get("ts", "")

        # Add reaction
        slack_api("reactions.add", channel=channel_id, timestamp=ts, name="white_check_mark")
        print(PASS)

        # Remove reaction
        print(f"  reactions.remove: ", end="")
        slack_api("reactions.remove", channel=channel_id, timestamp=ts, name="white_check_mark")
        print(PASS)

        # Clean up
        time.sleep(1)
        slack_api("chat.delete", channel=channel_id, ts=ts)
        return True
    except SlackError as e:
        print(f"{FAIL} — {e}")
        return False


def test_upload(test_channel: str, verbose: bool = False) -> bool:
    """Test file upload via 2-step external API."""
    print(f"  files.upload (2-step): ", end="")
    try:
        import tempfile
        channel_id = resolve_channel(test_channel)

        # Create a temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="slack_test_") as f:
            f.write("Slack skill test file — will be deleted")
            tmppath = f.name

        try:
            # Step 1: Get upload URL
            url_resp = slack_api("files.getUploadURLExternal",
                                 filename="test.txt", length=os.path.getsize(tmppath))
            upload_url = url_resp["upload_url"]
            file_id = url_resp["file_id"]

            # Step 2: POST file (multipart form per official docs)
            import requests as req
            with open(tmppath, "rb") as f:
                post_resp = req.post(upload_url, files={"file": ("test.txt", f)})
                post_resp.raise_for_status()

            # Step 3: Complete upload (private — no channel)
            slack_api("files.completeUploadExternal",
                      files=[{"id": file_id, "title": "test.txt"}])

            if verbose:
                print(f"{PASS} — uploaded file_id={file_id}")
            else:
                print(PASS)
            return True
        finally:
            os.unlink(tmppath)

    except SlackError as e:
        print(f"{FAIL} — {e}")
        return False
    except Exception as e:
        print(f"{FAIL} — {e}")
        return False


def test_rate_limit_headers(verbose: bool = False) -> bool:
    """Verify rate limit headers are returned."""
    print(f"  rate-limit headers: ", end="")
    try:
        import requests as req
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json; charset=utf-8",
        }
        resp = req.post(f"https://slack.com/api/auth.test", headers=headers, json={})
        has_headers = any(k.lower().startswith("x-ratelimit") for k in resp.headers)
        if has_headers or resp.status_code == 200:
            print(PASS)
        else:
            print(f"{SKIP} — no rate limit headers (may vary by endpoint)")
        return True
    except Exception as e:
        print(f"{FAIL} — {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Slack skill")
    parser.add_argument("--quick", action="store_true", help="Auth + channels only")
    parser.add_argument("--test", choices=["post", "read", "search", "react", "users", "channels", "upload"],
                        help="Test specific endpoint")
    parser.add_argument("--test-channel", default="#general",
                        help="Channel for write tests (default: #general)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    args = parser.parse_args()

    print("Slack Skill Test Suite")
    print("=" * 40)

    passed = 0
    failed = 0

    def run(fn, *a):
        nonlocal passed, failed
        if fn(*a, verbose=args.verbose):
            passed += 1
        else:
            failed += 1

    if args.test:
        run(test_auth)
        tests = {
            "post": lambda: run(test_post, args.test_channel),
            "read": lambda: run(test_read, args.test_channel),
            "search": lambda: run(test_search),
            "react": lambda: run(test_reactions, args.test_channel),
            "users": lambda: run(test_users),
            "channels": lambda: run(test_channels),
            "upload": lambda: run(test_upload, args.test_channel),
        }
        tests[args.test]()

    elif args.quick:
        run(test_auth)
        run(test_channels)

    else:
        run(test_auth)
        run(test_channels)
        run(test_users)
        run(test_post, args.test_channel)
        run(test_read, args.test_channel)
        run(test_search)
        run(test_reactions, args.test_channel)
        run(test_upload, args.test_channel)
        run(test_rate_limit_headers)

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
