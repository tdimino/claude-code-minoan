#!/usr/bin/env python3
"""
Stop hook — check Slack inbox and block stopping if messages are pending.

When Claude finishes responding, this hook checks inbox.jsonl.
If unhandled messages exist and stop_hook_active is False,
it blocks stopping and instructs Claude to process them.

Loop prevention: stop_hook_active is True when Claude is already
continuing from a Stop hook. We only check inbox when False.
"""
import json
import os
import sys

INBOX = os.path.expanduser("~/.claude/skills/slack/daemon/inbox.jsonl")
PID_FILE = os.path.expanduser("~/.claude/skills/slack/daemon/listener.pid")


def _listener_running():
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (FileNotFoundError, ValueError, OSError):
        return False


def _count_unhandled():
    if not os.path.exists(INBOX):
        return 0
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
        return 0
    return count


def main():
    input_data = json.load(sys.stdin)

    # CRITICAL: Don't block if already continuing from a Stop hook.
    # This prevents infinite loops.
    if input_data.get("stop_hook_active"):
        sys.exit(0)

    # Only check if listener is running
    if not _listener_running():
        sys.exit(0)

    count = _count_unhandled()
    if count > 0:
        result = {
            "decision": "block",
            "reason": (
                f"You have {count} unhandled Slack message"
                f"{'s' if count != 1 else ''}. "
                "Run /slack-respond to process them as Claudicle."
            ),
        }
        print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
