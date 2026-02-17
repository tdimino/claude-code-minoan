"""
SQLite store mapping Slack threads to Claude Code session IDs.

Enables multi-turn conversations: when a user @mentions the bot in a thread,
subsequent replies in the same thread resume the same Claude session.

Thread-safe: each thread gets its own SQLite connection via threading.local().
"""

import os
import sqlite3
import threading
import time
from typing import Optional

from config import SESSION_TTL_HOURS

DB_PATH = os.path.join(os.path.dirname(__file__), "sessions.db")

_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS sessions (
        channel TEXT NOT NULL,
        thread_ts TEXT NOT NULL,
        session_id TEXT NOT NULL,
        created_at REAL NOT NULL,
        last_used REAL NOT NULL,
        PRIMARY KEY (channel, thread_ts)
    )
"""

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.execute(_CREATE_TABLE)
        _local.conn.commit()
    return _local.conn


def get(channel: str, thread_ts: str) -> Optional[str]:
    """Get Claude session ID for a Slack thread, or None if expired/missing."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT session_id, last_used FROM sessions WHERE channel = ? AND thread_ts = ?",
        (channel, thread_ts),
    ).fetchone()
    if row is None:
        return None
    session_id, last_used = row
    if time.time() - last_used > SESSION_TTL_HOURS * 3600:
        conn.execute(
            "DELETE FROM sessions WHERE channel = ? AND thread_ts = ?",
            (channel, thread_ts),
        )
        conn.commit()
        return None
    return session_id


def save(channel: str, thread_ts: str, session_id: str) -> None:
    """Save or update a thread→session mapping."""
    conn = _get_conn()
    now = time.time()
    conn.execute(
        """INSERT INTO sessions (channel, thread_ts, session_id, created_at, last_used)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(channel, thread_ts)
           DO UPDATE SET session_id = excluded.session_id, last_used = excluded.last_used""",
        (channel, thread_ts, session_id, now, now),
    )
    conn.commit()


def touch(channel: str, thread_ts: str) -> None:
    """Update last_used timestamp for a thread."""
    conn = _get_conn()
    conn.execute(
        "UPDATE sessions SET last_used = ? WHERE channel = ? AND thread_ts = ?",
        (time.time(), channel, thread_ts),
    )
    conn.commit()


def cleanup() -> int:
    """Remove expired sessions. Returns count of deleted rows."""
    conn = _get_conn()
    cutoff = time.time() - SESSION_TTL_HOURS * 3600
    cursor = conn.execute("DELETE FROM sessions WHERE last_used < ?", (cutoff,))
    conn.commit()
    return cursor.rowcount


def close() -> None:
    """Close the thread-local connection if open."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None
