#!/usr/bin/env python3
"""
SessionEnd hook — remove this session from the soul registry.

Fires when a Claude Code session terminates. Removes the entry
from registry.json so SESSIONS.md stays accurate.

Hook config (settings.json):
    Added to the SessionEnd hooks array alongside precompact-handoff.py.
"""

import json
import os
import subprocess
import sys

REGISTRY_SCRIPT = os.path.expanduser("~/.claude/hooks/soul-registry.py")


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    session_id = hook_input.get("session_id", "")
    if not session_id:
        sys.exit(0)

    # Remove from registry
    try:
        subprocess.run(
            ["python3", REGISTRY_SCRIPT, "deregister", session_id],
            capture_output=True, text=True, timeout=5
        )
    except Exception:
        pass

    # Clean up ensoul marker file
    marker = os.path.expanduser(f"~/.claude/soul-sessions/active/{session_id}")
    try:
        os.remove(marker)
    except FileNotFoundError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
