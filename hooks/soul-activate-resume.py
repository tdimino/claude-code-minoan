#!/usr/bin/env python3
"""
SessionStart hook (matcher: resume) — re-inject soul when resuming a session.

When `claude --resume <id>` is used, the model gets the prior conversation
but may have lost soul state. This hook injects:
  1. Full soul identity (soul.md)
  2. Soul state from memory.db
  3. The session's handoff YAML (if it exists) for recovery context
  4. CLAUDE_ENV_FILE for Bash subprocess awareness

Compared to the compact handler, this includes the full soul (not condensed)
since resume sessions have the prior conversation in context.
"""

import json
import os
import subprocess
import sys

SOUL_MD = os.path.expanduser("~/.claudicle/soul/soul.md")
SOUL_MEMORY_DIR = os.path.expanduser("~/.claudicle/daemon")
HANDOFFS_DIR = os.path.expanduser("~/.claude/handoffs")
REGISTRY_SCRIPT = os.path.expanduser("~/.claude/hooks/soul-registry.py")


def _read_soul_md():
    try:
        with open(SOUL_MD) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def _get_soul_state():
    try:
        sys.path.insert(0, SOUL_MEMORY_DIR)
        from memory import soul_memory
        state = soul_memory.format_for_prompt()
        soul_memory.close()
        return state
    except (ImportError, Exception):
        return ""
    finally:
        if SOUL_MEMORY_DIR in sys.path:
            sys.path.remove(SOUL_MEMORY_DIR)


def _get_handoff(session_id):
    """Load the handoff YAML for this specific session."""
    handoff_path = os.path.join(HANDOFFS_DIR, f"{session_id}.yaml")
    if os.path.exists(handoff_path):
        try:
            with open(handoff_path) as f:
                return f.read().strip()
        except Exception:
            pass
    return ""


def _is_soul_active(session_id):
    marker_dir = os.path.expanduser("~/.claude/soul-sessions/active")
    if os.path.exists(os.path.join(marker_dir, session_id)):
        return True
    if os.environ.get("CLAUDICLE_SOUL", "").strip() == "1":
        return True
    if os.environ.get("CLAUDIUS_SOUL", "").strip() == "1":
        return True
    return False


def _registry_cmd(*args):
    try:
        result = subprocess.run(
            ["python3", REGISTRY_SCRIPT] + list(args),
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _write_env_file(session_id, soul_active):
    """Write env file for Bash subprocesses."""
    env_dir = os.path.expanduser("~/.claude/soul-sessions/env")
    os.makedirs(env_dir, exist_ok=True)
    profile = os.environ.get("CLAUDICLE_SOUL_PROFILE", "default")
    env_lines = [
        f"CLAUDICLE_SESSION_ID={session_id}",
        f"CLAUDICLE_SOUL_ACTIVE={'1' if soul_active else '0'}",
        f"CLAUDICLE_CHANNEL=terminal:{session_id}",
        f"CLAUDICLE_SOUL_PROFILE={profile}",
    ]
    env_path = os.path.join(env_dir, f"{session_id}.env")
    with open(env_path, "w") as f:
        f.write("\n".join(env_lines) + "\n")
    return env_path


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    session_id = hook_input.get("session_id", "")
    cwd = hook_input.get("cwd", os.getcwd())

    if not session_id:
        sys.exit(0)

    # Re-register this session on resume
    _registry_cmd("register", session_id, cwd, "--pid", str(os.getppid()))

    soul_active = _is_soul_active(session_id)
    env_path = _write_env_file(session_id, soul_active)

    if not soul_active:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "CLAUDE_ENV_FILE": env_path,
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    parts = []

    # Full soul identity
    soul_md = _read_soul_md()
    if soul_md:
        parts.append(soul_md)

    # Soul state
    soul_state = _get_soul_state()
    if soul_state:
        parts.append(soul_state)

    # Session handoff for recovery context
    handoff = _get_handoff(session_id)
    if handoff:
        parts.append("## Session Recovery Context\n\n```yaml\n" + handoff + "\n```")

    if not parts:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "CLAUDE_ENV_FILE": env_path,
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    context = "\n\n".join(parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
            "CLAUDE_ENV_FILE": env_path,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
