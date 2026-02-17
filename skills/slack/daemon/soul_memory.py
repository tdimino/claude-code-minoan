"""
Cross-thread persistent soul memory for Claudius.

Unlike working memory (thread-scoped, TTL-expired) or user models (per-user),
soul memory is global state that persists across all threads and sessions.
It represents Claudius's ongoing awareness of what it's working on, its
emotional state, and accumulated context.

Modeled after the Aldea Soul Engine's useSoulMemory hook, adapted for
SQLite single-process persistence.

Thread-safe: uses threading.local() for SQLite connections.
"""

import os
import sqlite3
import threading
import time
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")

SOUL_MEMORY_DEFAULTS = {
    "currentProject": "",
    "currentTask": "",
    "currentTopic": "",
    "emotionalState": "neutral",
    "conversationSummary": "",
}

_CREATE_SOUL_MEMORY = """
    CREATE TABLE IF NOT EXISTS soul_memory (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at REAL NOT NULL
    )
"""

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute(_CREATE_SOUL_MEMORY)
        _local.conn.commit()
    return _local.conn


def get(key: str) -> Optional[str]:
    """Get a soul memory value, or None if not set."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT value FROM soul_memory WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        return SOUL_MEMORY_DEFAULTS.get(key)
    return row["value"]


def set(key: str, value: str) -> None:
    """Set a soul memory value."""
    conn = _get_conn()
    conn.execute(
        """INSERT INTO soul_memory (key, value, updated_at)
           VALUES (?, ?, ?)
           ON CONFLICT(key)
           DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at""",
        (key, value, time.time()),
    )
    conn.commit()


def get_all() -> dict[str, str]:
    """Get all soul memory values, merged with defaults for missing keys."""
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM soul_memory").fetchall()
    result = dict(SOUL_MEMORY_DEFAULTS)
    for row in rows:
        result[row["key"]] = row["value"]
    return result


def format_for_prompt() -> str:
    """Format soul memory as a prompt section.

    Returns a '## Soul State' markdown section, or empty string
    if all values are at their defaults (nothing to report).
    """
    state = get_all()

    # Skip if everything is empty/default
    has_content = any(
        state.get(k) and state.get(k) != SOUL_MEMORY_DEFAULTS.get(k)
        for k in SOUL_MEMORY_DEFAULTS
    )
    if not has_content:
        return ""

    lines = ["## Soul State", ""]
    if state.get("currentProject"):
        lines.append(f"- **Current Project**: {state['currentProject']}")
    if state.get("currentTask"):
        lines.append(f"- **Current Task**: {state['currentTask']}")
    if state.get("emotionalState") and state["emotionalState"] != "neutral":
        lines.append(f"- **Emotional State**: {state['emotionalState']}")
    if state.get("currentTopic"):
        lines.append(f"- **Current Topic**: {state['currentTopic']}")
    if state.get("conversationSummary"):
        lines.append(f"- **Recent Context**: {state['conversationSummary']}")

    return "\n".join(lines)


def close() -> None:
    """Close the thread-local connection if open."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None
