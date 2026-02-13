"""
SQLite-backed working memory for Claudius's pseudo soul engine.

Stores all cognitive outputs (internal monologue, external dialogue, mentalQuery
results, tool actions, user messages) with verbs intact, forming a persistent
working memory that gets injected into future prompts.

Thread-safe: each thread gets its own SQLite connection via threading.local().
"""

import json
import os
import sqlite3
import threading
import time
from typing import Any, Optional

from config import WORKING_MEMORY_TTL_HOURS

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")

_CREATE_WORKING_MEMORY = """
    CREATE TABLE IF NOT EXISTS working_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT NOT NULL,
        thread_ts TEXT NOT NULL,
        user_id TEXT NOT NULL,
        entry_type TEXT NOT NULL,
        verb TEXT,
        content TEXT NOT NULL,
        metadata TEXT,
        created_at REAL NOT NULL
    )
"""

_CREATE_USER_MODELS = """
    CREATE TABLE IF NOT EXISTS user_models (
        user_id TEXT PRIMARY KEY,
        display_name TEXT,
        model_md TEXT NOT NULL,
        interaction_count INTEGER DEFAULT 0,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    )
"""

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute(_CREATE_WORKING_MEMORY)
        _local.conn.execute(_CREATE_USER_MODELS)
        _local.conn.commit()
    return _local.conn


def add(
    channel: str,
    thread_ts: str,
    user_id: str,
    entry_type: str,
    content: str,
    verb: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """Store a working memory entry."""
    conn = _get_conn()
    conn.execute(
        """INSERT INTO working_memory (channel, thread_ts, user_id, entry_type, verb, content, metadata, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            channel,
            thread_ts,
            user_id,
            entry_type,
            verb,
            content,
            json.dumps(metadata) if metadata else None,
            time.time(),
        ),
    )
    conn.commit()


def get_recent(channel: str, thread_ts: str, limit: int = 20) -> list[dict]:
    """Get recent working memory entries for a thread."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT entry_type, verb, content, user_id, metadata, created_at
           FROM working_memory
           WHERE channel = ? AND thread_ts = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (channel, thread_ts, limit),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_user_history(user_id: str, limit: int = 50) -> list[dict]:
    """Get recent working memory entries for a specific user across all threads."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT entry_type, verb, content, channel, thread_ts, metadata, created_at
           FROM working_memory
           WHERE user_id = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def format_for_prompt(entries: list[dict], soul_name: str = "Claudius") -> str:
    """Format working memory entries as pseudo-working memory for prompt injection.

    Produces lines like:
        User said: "Can you help me with CI/CD?"
        Claudius pondered: "This user seems experienced..."
        Claudius explained: "Here's how to set up..."
        Claudius evaluated: "Should update user model?" → true
    """
    if not entries:
        return ""

    lines = []
    for entry in entries:
        entry_type = entry["entry_type"]
        verb = entry.get("verb")
        content = entry["content"]
        meta = entry.get("metadata")

        if entry_type == "userMessage":
            lines.append(f'User said: "{content}"')
        elif entry_type == "internalMonologue":
            v = verb or "thought"
            lines.append(f'{soul_name} {v}: "{content}"')
        elif entry_type == "externalDialog":
            v = verb or "said"
            lines.append(f'{soul_name} {v}: "{content}"')
        elif entry_type == "mentalQuery":
            if meta:
                try:
                    m = json.loads(meta) if isinstance(meta, str) else meta
                    result = m.get("result", "")
                    lines.append(
                        f'{soul_name} evaluated: "{content}" → {result}'
                    )
                except (json.JSONDecodeError, TypeError):
                    lines.append(f'{soul_name} evaluated: "{content}"')
            else:
                lines.append(f'{soul_name} evaluated: "{content}"')
        elif entry_type == "toolAction":
            lines.append(f"{soul_name} {content}")
        else:
            lines.append(f"{content}")

    return "\n".join(lines)


def cleanup(max_age_hours: Optional[int] = None) -> int:
    """Remove expired working memory entries. Returns count of deleted rows."""
    hours = max_age_hours or WORKING_MEMORY_TTL_HOURS
    conn = _get_conn()
    cutoff = time.time() - hours * 3600
    cursor = conn.execute(
        "DELETE FROM working_memory WHERE created_at < ?", (cutoff,)
    )
    conn.commit()
    return cursor.rowcount


def close() -> None:
    """Close the thread-local connection if open."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None
