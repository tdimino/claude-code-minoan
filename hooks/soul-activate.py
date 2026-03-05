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
import tempfile

SOUL_MD = os.path.expanduser("~/.claudicle/soul/soul.md")
SOUL_MEMORY_DIR = os.path.expanduser("~/.claudicle/daemon")
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
        sys.path.insert(0, SOUL_MEMORY_DIR)
        from memory import soul_memory
        state = soul_memory.format_for_prompt()
        soul_memory.close()
        return state
    except ImportError:
        return ""  # daemon not installed — expected during initial setup
    except Exception as e:
        print(f"soul-activate: soul state load failed: {e}", file=sys.stderr)
        return ""
    finally:
        if SOUL_MEMORY_DIR in sys.path:
            sys.path.remove(SOUL_MEMORY_DIR)


def _get_working_memory(session_id):
    """Get recent working memory entries for this terminal channel."""
    try:
        sys.path.insert(0, SOUL_MEMORY_DIR)
        from memory import working_memory
        channel = f"terminal:{session_id}"
        entries = working_memory.get_recent(channel, session_id, limit=10)
        if entries:
            formatted = working_memory.format_for_prompt(entries)
            working_memory.close()
            return formatted
        working_memory.close()
        return ""
    except ImportError:
        return ""
    except Exception as e:
        print(f"soul-activate: working memory load failed: {e}", file=sys.stderr)
        return ""
    finally:
        if SOUL_MEMORY_DIR in sys.path:
            sys.path.remove(SOUL_MEMORY_DIR)


def _get_user_model():
    """Get the primary user's model from shared memory.db."""
    try:
        sys.path.insert(0, SOUL_MEMORY_DIR)
        import config
        from memory import user_models
        model = user_models.get(config.PRIMARY_USER_ID)
        user_models.close()
        return model or ""
    except ImportError:
        return ""
    except Exception as e:
        print(f"soul-activate: user model load failed: {e}", file=sys.stderr)
        return ""
    finally:
        if SOUL_MEMORY_DIR in sys.path:
            sys.path.remove(SOUL_MEMORY_DIR)


def _registry_cmd(*args):
    """Run a soul-registry.py subcommand, return stdout."""
    try:
        result = subprocess.run(
            ["python3", REGISTRY_SCRIPT] + list(args),
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            print(f"soul-activate: registry {args[0] if args else '?'} "
                  f"failed (rc={result.returncode}): {result.stderr[:100]}",
                  file=sys.stderr)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"soul-activate: registry {args[0] if args else '?'} timed out",
              file=sys.stderr)
        return ""
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

    # Mode 2: Explicit env var override (both naming conventions)
    if os.environ.get("CLAUDICLE_SOUL", "").strip() == "1":
        return True
    if os.environ.get("CLAUDIUS_SOUL", "").strip() == "1":
        return True

    return False


def _write_env_file(session_id, soul_active):
    """Write a CLAUDE_ENV_FILE with soul state for all Bash subprocesses.

    Claude Code sources this file before every Bash command, so any skill
    or script can check $CLAUDICLE_SOUL_ACTIVE instead of importing Python.
    """
    env_dir = os.path.expanduser("~/.claude/soul-sessions/env")
    os.makedirs(env_dir, exist_ok=True)

    # Detect active soul profile (if any)
    profile = os.environ.get("CLAUDICLE_SOUL_PROFILE", "default")

    env_lines = [
        f"CLAUDICLE_SESSION_ID={session_id}",
        f"CLAUDICLE_SOUL_ACTIVE={'1' if soul_active else '0'}",
        f"CLAUDICLE_CHANNEL=terminal:{session_id}",
        f"CLAUDICLE_SOUL_PROFILE={profile}",
    ]

    # Write to a stable path (not tmp) so it survives the session
    env_path = os.path.join(env_dir, f"{session_id}.env")
    with open(env_path, "w") as f:
        f.write("\n".join(env_lines) + "\n")

    return env_path


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
    soul_active = _is_soul_active(session_id)

    # 4. Write env file (always — session ID is useful even without soul)
    env_path = _write_env_file(session_id, soul_active)

    if not soul_active:
        # Even without soul, export the env file so Bash gets session context
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "CLAUDE_ENV_FILE": env_path,
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # 5. Build additionalContext (only when soul is active)
    parts = []

    # Soul personality
    soul_md = _read_soul_md()
    if soul_md:
        parts.append(soul_md)

    # Soul state
    soul_state = _get_soul_state()
    if soul_state:
        parts.append(soul_state)

    # Working memory — recent cognitive entries from this terminal channel
    terminal_memory = _get_working_memory(session_id)
    if terminal_memory:
        parts.append("## Recent Memory\n\n" + terminal_memory)

    # User model — primary user's living model from shared memory.db
    user_model = _get_user_model()
    if user_model:
        parts.append("## User Model\n\n" + user_model)

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
        # Still export env file even if no context parts
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
