#!/usr/bin/env python3
"""
SessionStart hook (matcher: compact) — re-inject soul after context compaction.

When Claude Code compacts context, all prior conversation is summarized and
the model loses fine-grained state. This hook fires on the compact event and
injects:
  1. Condensed soul identity (soul.md)
  2. Soul state from memory.db
  3. The handoff YAML that precompact-handoff.py wrote moments before compaction
  4. CLAUDE_ENV_FILE for Bash subprocess awareness

This gives Claude immediate awareness of what it was doing before context loss.
"""

import glob
import json
import os
import sys

SOUL_MD = os.path.expanduser("~/.claudicle/soul/soul.md")
SOUL_MEMORY_DIR = os.path.expanduser("~/.claudicle/daemon")
HANDOFFS_DIR = os.path.expanduser("~/.claude/handoffs")


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


def _get_latest_handoff(session_id):
    """Load the most recent handoff YAML for this session."""
    # Try session-specific handoff first
    session_handoff = os.path.join(HANDOFFS_DIR, f"{session_id}.yaml")
    if os.path.exists(session_handoff):
        try:
            with open(session_handoff) as f:
                return f.read().strip()
        except Exception:
            pass

    # Fall back to most recently modified handoff
    pattern = os.path.join(HANDOFFS_DIR, "*.yaml")
    handoffs = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if handoffs:
        try:
            with open(handoffs[0]) as f:
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


def _get_env_file(session_id):
    """Return path to existing env file (written by startup hook)."""
    env_path = os.path.expanduser(f"~/.claude/soul-sessions/env/{session_id}.env")
    if os.path.exists(env_path):
        return env_path
    return None


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    session_id = hook_input.get("session_id", "")
    if not session_id:
        sys.exit(0)

    if not _is_soul_active(session_id):
        sys.exit(0)

    parts = []

    # Compact-specific preamble
    parts.append(
        "⚠️ **Context was just compacted.** Your prior conversation was summarized. "
        "The handoff below captures what you were doing before context loss."
    )

    # Condensed soul identity
    soul_md = _read_soul_md()
    if soul_md:
        parts.append(soul_md)

    # Soul state
    soul_state = _get_soul_state()
    if soul_state:
        parts.append(soul_state)

    # Handoff from precompact-handoff.py
    handoff = _get_latest_handoff(session_id)
    if handoff:
        parts.append("## Pre-Compaction Handoff\n\n```yaml\n" + handoff + "\n```")

    if not parts:
        sys.exit(0)

    context = "\n\n".join(parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }

    # Include env file if it exists
    env_path = _get_env_file(session_id)
    if env_path:
        output["hookSpecificOutput"]["CLAUDE_ENV_FILE"] = env_path

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
