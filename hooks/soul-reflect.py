#!/usr/bin/env python3
"""Stop hook subprocess: run retrospective cognitive pipeline on terminal sessions.

Reads the JSONL transcript, extracts the last user→assistant exchange,
and runs the Claudicle cognitive pipeline (internal monologue, user model
check/update, soul state check/update) via daemon/engine/reflect.py.

Launched fire-and-forget by stop-handoff.py. Writes to shared memory.db
and soul-stream.jsonl. Never blocks the main Claude Code session.

Cooldown: REFLECT_COOLDOWN seconds (default 60) between reflections per session.
"""

import json
import os
import pathlib
import sys
import time


# Claudicle daemon directory — needed for imports
DAEMON_DIR = os.path.expanduser("~/.claudicle/daemon")
COOLDOWN_DIR = pathlib.Path.home() / ".claude" / "soul-sessions" / "reflect-cooldown"

# Framework-injected text prefixes to filter from user messages
_NOISE_PREFIXES = (
    "[Request interrupted",
    "Base directory for this skill:",
    "<context_window>",
    "HUMAN TURN",
)


def _extract_last_exchange(transcript_path: str) -> tuple[str, str]:
    """Extract last user message and assistant response from JSONL transcript.

    Returns (user_message, assistant_response) or ("", "") if extraction fails.
    """
    try:
        with open(transcript_path) as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError, MemoryError):
        return "", ""

    # Scan all lines — tool-heavy sessions push user text 200+ lines from end.
    # We only keep the last user→assistant pair, so memory is constant.
    last_user = ""
    last_assistant = ""
    pair_complete = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_type = entry.get("type", "")

        if msg_type in ("human", "user"):
            # Extract text from human/user message content blocks
            content = entry.get("message", {}).get("content", [])
            dict_texts = []
            str_chars = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "").strip()
                    # Skip framework-injected noise
                    if text and not any(text.startswith(p) for p in _NOISE_PREFIXES):
                        dict_texts.append(text)
                elif isinstance(block, str):
                    str_chars.append(block)
            # Prefer dict text blocks; fall back to concatenated string blocks
            # (Claude Code sends user input as per-character strings)
            if dict_texts:
                last_user = "\n".join(dict_texts)
            elif str_chars:
                last_user = "".join(str_chars)
            if dict_texts or str_chars:
                last_assistant = ""  # Reset — looking for the next assistant turn
                pair_complete = False

        elif msg_type == "assistant":
            # Extract text from assistant message content blocks
            content = entry.get("message", {}).get("content", [])
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
            if texts:
                last_assistant = "\n".join(texts)
                pair_complete = True

    # Only return a matched pair — avoid stale mismatches from mid-tool-chain exits
    if not pair_complete:
        return "", ""
    return last_user, last_assistant


def _check_cooldown(session_id: str) -> bool:
    """Return True if cooldown has elapsed and reflection should run."""
    COOLDOWN_DIR.mkdir(parents=True, exist_ok=True)
    cooldown_file = COOLDOWN_DIR / session_id

    # Import config after sys.path setup for REFLECT_COOLDOWN
    try:
        sys.path.insert(0, DAEMON_DIR)
        import config
        cooldown_secs = config.REFLECT_COOLDOWN
    except Exception:
        cooldown_secs = 60
    finally:
        if DAEMON_DIR in sys.path:
            sys.path.remove(DAEMON_DIR)

    now = time.time()
    if cooldown_file.exists():
        try:
            last_time = float(cooldown_file.read_text().strip())
            if (now - last_time) < cooldown_secs:
                return False
        except (ValueError, OSError):
            pass

    # Cooldown elapsed — don't stamp yet, stamp after successful reflection
    return True


def _stamp_cooldown(session_id: str) -> None:
    """Write cooldown timestamp after successful reflection."""
    COOLDOWN_DIR.mkdir(parents=True, exist_ok=True)
    cooldown_file = COOLDOWN_DIR / session_id
    try:
        cooldown_file.write_text(str(time.time()))
    except OSError:
        pass


def _resolve_user_id() -> tuple[str, str]:
    """Resolve the primary user's ID and display name from config."""
    try:
        sys.path.insert(0, DAEMON_DIR)
        import config
        user_id = config.PRIMARY_USER_ID
        display_name = config.DEFAULT_USER_NAME
        # Try to get actual display name from user model
        try:
            from memory import user_models
            name = user_models.get_display_name(user_id)
            if name:
                display_name = name
        except Exception:
            pass
        return user_id, display_name
    except Exception:
        return "terminal-user", "Human"
    finally:
        if DAEMON_DIR in sys.path:
            sys.path.remove(DAEMON_DIR)


def main():
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    if not session_id or not transcript_path or not os.path.exists(transcript_path):
        return

    # Cooldown gate
    if not _check_cooldown(session_id):
        return

    # Extract the last exchange from transcript
    user_message, assistant_response = _extract_last_exchange(transcript_path)
    if not user_message.strip() or not assistant_response.strip():
        print(f"soul-reflect: no exchange extracted from {transcript_path}", file=sys.stderr)
        return

    # Truncate long messages (keep under ~4K chars each for the reflection prompt)
    if len(user_message) > 4000:
        user_message = user_message[:4000] + "\n...(truncated)"
    if len(assistant_response) > 4000:
        assistant_response = assistant_response[:4000] + "\n...(truncated)"

    # Resolve user identity
    user_id, display_name = _resolve_user_id()

    # Channel convention: terminal:{session_id}
    channel = f"terminal:{session_id}"
    thread_ts = session_id

    # Run the reflection pipeline
    sys.path.insert(0, DAEMON_DIR)
    try:
        from engine.reflect import run_reflection
        result = run_reflection(
            user_message=user_message,
            assistant_response=assistant_response,
            user_id=user_id,
            channel=channel,
            thread_ts=thread_ts,
            display_name=display_name,
        )
        steps = result.get("steps", [])
        trace_id = result.get("trace_id", "?")
        if steps:
            # Stamp cooldown only after successful reflection
            _stamp_cooldown(session_id)
            # Subprocess summary (Y/N flags for each subprocess)
            sp = result.get("subprocesses", {})
            sp_parts = []
            for name in ("modelsTheUser", "updatesState"):
                if name in sp:
                    flag = "Y" if sp[name].get("check") else "N"
                    sp_parts.append(f"{name}={flag}")
            sp_label = f" ({', '.join(sp_parts)})" if sp_parts else ""
            print(
                f"soul-reflect: [{trace_id}] {len(steps)} steps{sp_label}: {', '.join(steps)}",
                file=sys.stderr,
            )
        elif result.get("skipped"):
            print(f"soul-reflect: skipped ({result.get('reason', '?')})", file=sys.stderr)
        elif result.get("error"):
            print(f"soul-reflect: error: {result['error'][:100]}", file=sys.stderr)
    except Exception as e:
        print(f"soul-reflect: failed: {e}", file=sys.stderr)
    finally:
        if DAEMON_DIR in sys.path:
            sys.path.remove(DAEMON_DIR)


if __name__ == "__main__":
    main()
