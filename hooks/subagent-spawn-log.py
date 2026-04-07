#!/usr/bin/env python3
"""SubagentStart logger.

Append-only JSONL log of every subagent spawn. Per-session counter for spawn
distribution analysis. No blocking, no context injection — pure observability.

Log location: ~/.claude/agent-spawn.log
Counter files: /tmp/claude-subagent-count-{session_id} (self-expire after 6h)

Defensive against Claude Code field-name drift:
  agent_type → subagent_type → subagent_name
  agent_id   → subagent_id
  task       → prompt
"""

import fcntl
import json
import os
import sys
import time

LOG = os.path.expanduser("~/.claude/agent-spawn.log")
COUNTER_DIR = "/tmp"
COUNTER_TTL = 6 * 3600  # 6 hours


def get_session_count(session_id: str) -> int:
    """Atomically increment per-session counter, with self-expiry."""
    path = os.path.join(COUNTER_DIR, f"claude-subagent-count-{session_id}")
    try:
        if os.path.exists(path) and time.time() - os.path.getmtime(path) > COUNTER_TTL:
            os.remove(path)  # stale, reset
    except OSError:
        pass

    try:
        with open(path, "a+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.seek(0)
            try:
                count = int(f.read().strip() or "0") + 1
            except ValueError:
                count = 1
            f.seek(0)
            f.truncate()
            f.write(str(count))
            return count
    except OSError:
        return -1  # counter unavailable, log entry still useful


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, OSError):
        sys.exit(0)

    session_id = event.get("session_id", "")
    if not session_id:
        sys.exit(0)

    # Defensive field reads — Claude Code field names have drifted across versions
    agent_type = (
        event.get("agent_type")
        or event.get("subagent_type")
        or event.get("subagent_name")
        or ""
    )
    agent_id = event.get("agent_id") or event.get("subagent_id") or ""
    task = event.get("task") or event.get("prompt") or ""

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "event": "start",
        "session_id": session_id,
        "agent_id": agent_id,
        "agent_type": agent_type,
        "task_preview": task[:120],
        "cwd": event.get("cwd"),
        "session_count": get_session_count(session_id),
    }

    try:
        with open(LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
