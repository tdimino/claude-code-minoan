#!/usr/bin/env python3
"""
SessionStart hook — inject Claudicle soul identity when opted in.

Opt-in per session: run /ensoul to create a marker file, or set
CLAUDICLE_SOUL=1. Without either, sessions are registered in the
soul registry but receive no persona injection.

When active: reads soul.md, soul state from memory.db, and sibling sessions
from the registry. Outputs additionalContext JSON.

Always: registers the session in the soul registry (lightweight, persona-free).

Activation modes:
    - /ensoul command → marker file → soul persists through compaction/resume
    - CLAUDICLE_SOUL=1 env var → full soul injection
    - Neither → registry only (no persona injection)
"""

import json
import os
import subprocess
import sys

SOUL_MD = os.path.expanduser("~/.claude/skills/slack/daemon/soul.md")
SOUL_MEMORY_DIR = os.path.expanduser("~/.claude/skills/slack/daemon")
REGISTRY_SCRIPT = os.path.expanduser("~/.claude/hooks/soul-registry.py")


def _read_soul_md():
    """Read the soul personality file."""
    try:
        with open(SOUL_MD) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def _get_soul_state():
    """Get formatted soul state from memory.db via soul_memory module."""
    try:
        # Import soul_memory from the daemon directory
        sys.path.insert(0, SOUL_MEMORY_DIR)
        import soul_memory
        state = soul_memory.format_for_prompt()
        soul_memory.close()
        return state
    except Exception:
        return ""
    finally:
        # Clean up sys.path
        if SOUL_MEMORY_DIR in sys.path:
            sys.path.remove(SOUL_MEMORY_DIR)


def _registry_cmd(*args):
    """Run a soul-registry.py subcommand, return stdout."""
    try:
        result = subprocess.run(
            ["python3", REGISTRY_SCRIPT] + list(args),
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _is_soul_active(session_id):
    """Check if soul should be injected in this session.

    Activation is opt-in per session:
        - /ensoul command creates a marker file → soul persists through compaction
        - CLAUDICLE_SOUL=1 env var → soul for all sessions in this shell
    """
    # Mode 1: Per-session marker file (set by /ensoul command)
    marker_dir = os.path.expanduser("~/.claude/soul-sessions/active")
    if os.path.exists(os.path.join(marker_dir, session_id)):
        return True

    # Mode 2: Explicit env var override
    if os.environ.get("CLAUDICLE_SOUL", "").strip() == "1":
        return True

    return False


def main():
    # Read hook input
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    session_id = hook_input.get("session_id", "")
    cwd = hook_input.get("cwd", os.getcwd())

    if not session_id:
        sys.exit(0)

    # 1. Clean up stale sessions
    _registry_cmd("cleanup")

    # 2. Register this session (always, even without soul)
    _registry_cmd("register", session_id, cwd, "--pid", str(os.getppid()))

    # 3. Check if soul should be injected
    if not _is_soul_active(session_id):
        sys.exit(0)

    # 4. Build additionalContext (only when soul is active)
    parts = []

    # Soul personality
    soul_md = _read_soul_md()
    if soul_md:
        parts.append(soul_md)

    # Soul state
    soul_state = _get_soul_state()
    if soul_state:
        parts.append(soul_state)

    # Sibling sessions
    siblings = _registry_cmd("list", "--md")
    if siblings and siblings != "No active sessions.":
        sibling_lines = siblings.strip().splitlines()
        # Mark the current session
        marked = []
        short_id = session_id[:8]
        for line in sibling_lines:
            if short_id in line:
                marked.append(f"{line} ← this session")
            else:
                marked.append(line)
        parts.append("## Active Sessions\n\n" + "\n".join(marked))

    if not parts:
        sys.exit(0)

    context = "\n\n".join(parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
