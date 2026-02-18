#!/usr/bin/env python3
"""
UserPromptSubmit hook — silently check Slack inbox.

Runs slack_check.py --quiet at the start of every Claude Code turn.
If unhandled messages exist, outputs a one-line summary.
Otherwise produces no output (silent).

Hook config (settings.json):
    {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "type": "command",
                    "command": "python3 ~/.claude/skills/slack/scripts/slack_inbox_hook.py"
                }
            ]
        }
    }
"""

import json
import os
import sys

DAEMON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daemon")
INBOX = os.path.join(DAEMON_DIR, "inbox.jsonl")
PID_FILE = os.path.join(DAEMON_DIR, "listener.pid")


def _listener_running():
    """Check if the Slack listener is running."""
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (FileNotFoundError, ValueError, OSError):
        return False


def main():
    # Only check if listener is actually running
    if not _listener_running():
        return

    # Count unhandled messages
    if not os.path.exists(INBOX):
        return

    count = 0
    try:
        with open(INBOX) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if not entry.get("handled"):
                        count += 1
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return

    if count > 0:
        print(f"[Slack: {count} unhandled message{'s' if count != 1 else ''} -- run /slack-check to view]")


if __name__ == "__main__":
    main()
