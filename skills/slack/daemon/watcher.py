"""
Read-only SQLite watcher for the Claudius Soul Monitor.

Polls memory.db and sessions.db with high-water marks to detect new entries
without interfering with the daemon's write path. Each poll method returns
only *new* data since the last call, making it safe for tight polling loops.

Usage:
    w = SQLiteWatcher("memory.db", "sessions.db")
    new_entries = w.poll_working_memory()   # list[dict] — new cognitive entries
    soul_state  = w.poll_soul_state()       # dict | None — full state if changed
    users       = w.poll_user_models()      # list[dict] — all users if changed
    sessions    = w.poll_sessions()         # list[dict] — all sessions if changed
    running, pid = w.is_daemon_running()    # (bool, int | None)
"""

import os
import sqlite3
import time
from typing import Optional

import psutil


class SQLiteWatcher:
    """Polls daemon SQLite databases for changes using monotonic cursors."""

    def __init__(self, memory_db: str, sessions_db: str):
        self._memory_db = memory_db
        self._sessions_db = sessions_db
        self._mem_conn: Optional[sqlite3.Connection] = None
        self._sess_conn: Optional[sqlite3.Connection] = None

        # High-water marks
        self._last_wm_id: int = 0
        self._last_soul_ts: float = 0.0
        self._last_user_ts: float = 0.0
        self._last_sess_ts: float = 0.0

        # User display name cache (user_id → display_name)
        self._display_names: dict[str, str] = {}

    def _get_mem_conn(self) -> Optional[sqlite3.Connection]:
        """Get or create read-only connection to memory.db."""
        if not os.path.exists(self._memory_db):
            return None
        if self._mem_conn is None:
            self._mem_conn = sqlite3.connect(
                f"file:{self._memory_db}?mode=ro",
                uri=True,
                check_same_thread=False,
            )
            self._mem_conn.row_factory = sqlite3.Row
        return self._mem_conn

    def _get_sess_conn(self) -> Optional[sqlite3.Connection]:
        """Get or create read-only connection to sessions.db."""
        if not os.path.exists(self._sessions_db):
            return None
        if self._sess_conn is None:
            self._sess_conn = sqlite3.connect(
                f"file:{self._sessions_db}?mode=ro",
                uri=True,
                check_same_thread=False,
            )
            self._sess_conn.row_factory = sqlite3.Row
        return self._sess_conn

    def poll_working_memory(self) -> list[dict]:
        """Return new cognitive entries since last poll.

        Uses autoincrement id as a monotonic cursor — guaranteed to only
        move forward, no duplicates.
        """
        conn = self._get_mem_conn()
        if conn is None:
            return []
        try:
            rows = conn.execute(
                "SELECT * FROM working_memory WHERE id > ? ORDER BY id",
                (self._last_wm_id,),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        entries = [dict(r) for r in rows]
        if entries:
            self._last_wm_id = entries[-1]["id"]
            # Refresh display name cache from any new user IDs
            for e in entries:
                uid = e.get("user_id", "")
                if uid and uid not in self._display_names:
                    self._refresh_display_name(uid, conn)
        return entries

    def poll_soul_state(self) -> Optional[dict[str, str]]:
        """Return full soul state dict if anything changed, else None."""
        conn = self._get_mem_conn()
        if conn is None:
            return None
        try:
            row = conn.execute(
                "SELECT MAX(updated_at) as max_ts FROM soul_memory"
            ).fetchone()
        except sqlite3.OperationalError:
            return None
        if row is None or row["max_ts"] is None:
            return None
        max_ts = row["max_ts"]
        if max_ts <= self._last_soul_ts:
            return None
        self._last_soul_ts = max_ts
        rows = conn.execute("SELECT key, value FROM soul_memory").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def poll_user_models(self) -> Optional[list[dict]]:
        """Return all user models if any changed, else None."""
        conn = self._get_mem_conn()
        if conn is None:
            return None
        try:
            row = conn.execute(
                "SELECT MAX(updated_at) as max_ts FROM user_models"
            ).fetchone()
        except sqlite3.OperationalError:
            return None
        if row is None or row["max_ts"] is None:
            return None
        max_ts = row["max_ts"]
        if max_ts <= self._last_user_ts:
            return None
        self._last_user_ts = max_ts
        rows = conn.execute(
            "SELECT user_id, display_name, interaction_count, updated_at FROM user_models ORDER BY updated_at DESC"
        ).fetchall()
        users = [dict(r) for r in rows]
        # Update display name cache
        for u in users:
            if u.get("display_name"):
                self._display_names[u["user_id"]] = u["display_name"]
        return users

    def poll_sessions(self) -> Optional[list[dict]]:
        """Return all sessions if any changed, else None."""
        conn = self._get_sess_conn()
        if conn is None:
            return None
        try:
            row = conn.execute(
                "SELECT MAX(last_used) as max_ts FROM sessions"
            ).fetchone()
        except sqlite3.OperationalError:
            return None
        if row is None or row["max_ts"] is None:
            return None
        max_ts = row["max_ts"]
        if max_ts <= self._last_sess_ts:
            return None
        self._last_sess_ts = max_ts
        rows = conn.execute(
            "SELECT channel, thread_ts, session_id, created_at, last_used FROM sessions ORDER BY last_used DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def resolve_user(self, user_id: str) -> str:
        """Resolve a Slack user ID to display name, falling back to raw ID."""
        return self._display_names.get(user_id, user_id)

    def is_daemon_running(self) -> tuple[bool, Optional[int]]:
        """Check if bot.py is running. Returns (is_running, pid)."""
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                if any("bot.py" in arg for arg in cmdline):
                    return True, proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None

    def get_daemon_uptime(self) -> Optional[float]:
        """Return daemon process uptime in seconds, or None if not running."""
        for proc in psutil.process_iter(["pid", "cmdline", "create_time"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                if any("bot.py" in arg for arg in cmdline):
                    return time.time() - proc.info["create_time"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def _refresh_display_name(self, user_id: str, conn: sqlite3.Connection) -> None:
        """Load a user's display name into the cache."""
        try:
            row = conn.execute(
                "SELECT display_name FROM user_models WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row and row["display_name"]:
                self._display_names[user_id] = row["display_name"]
        except sqlite3.OperationalError:
            pass

    def close(self) -> None:
        """Close all database connections."""
        if self._mem_conn:
            self._mem_conn.close()
            self._mem_conn = None
        if self._sess_conn:
            self._sess_conn.close()
            self._sess_conn = None
