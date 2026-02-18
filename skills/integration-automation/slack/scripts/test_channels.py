#!/usr/bin/env python3
"""
Verify bot access to all channels it's been invited to.

Tests read + write on each channel the bot is a member of.

Usage:
    test_channels.py              # Test all channels bot is in
    test_channels.py --read-only  # Only test reading (no posts)
    test_channels.py --verbose    # Detailed output
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from _slack_utils import slack_api, paginate, SlackError, SLACK_BOT_TOKEN

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def get_bot_channels():
    """Get all channels the bot is a member of (public + private)."""
    public = paginate("conversations.list", "channels", types="public_channel")
    private = paginate("conversations.list", "channels", types="private_channel")
    pub_members = [ch for ch in public if ch.get("is_member")]
    priv_members = [ch for ch in private if ch.get("is_member")]
    return pub_members + priv_members


def test_channel(channel_id, channel_name, read_only=False, verbose=False):
    """Test read (and optionally write) access to a channel."""
    results = {"read": None, "write": None}

    # Test read
    try:
        data = slack_api("conversations.history", channel=channel_id, limit=1)
        msgs = data.get("messages", [])
        if verbose:
            print(f"  read: {PASS} ({len(msgs)} messages)")
        else:
            print(f"  read: {PASS}")
        results["read"] = True
    except SlackError as e:
        print(f"  read: {FAIL} — {e}")
        results["read"] = False

    if read_only:
        return results

    # Test write (post + delete)
    try:
        msg = slack_api("chat.postMessage", channel=channel_id,
                        text="[test] Channel access verification — deleting now")
        ts = msg.get("ts", "")
        time.sleep(0.5)
        slack_api("chat.delete", channel=channel_id, ts=ts)
        print(f"  write: {PASS}")
        results["write"] = True
    except SlackError as e:
        print(f"  write: {FAIL} — {e}")
        results["write"] = False

    return results


def main():
    parser = argparse.ArgumentParser(description="Verify bot channel access")
    parser.add_argument("--read-only", action="store_true", help="Only test reading")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    args = parser.parse_args()

    if not SLACK_BOT_TOKEN:
        print("Error: SLACK_BOT_TOKEN not set")
        sys.exit(1)

    print("Slack Channel Access Verification")
    print("=" * 50)

    channels = get_bot_channels()
    if not channels:
        print("Bot is not a member of any channels.")
        sys.exit(1)

    passed = 0
    failed = 0

    for ch in sorted(channels, key=lambda c: c["name"]):
        name = ch["name"]
        ctype = "private" if ch.get("is_private") else "public"
        print(f"\n#{name} [{ctype}] (id: {ch['id']})")

        results = test_channel(ch["id"], name, args.read_only, args.verbose)
        for test, result in results.items():
            if result is None:
                continue
            if result:
                passed += 1
            else:
                failed += 1

    print(f"\n{'=' * 50}")
    print(f"Channels: {len(channels)}")
    print(f"Tests: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
