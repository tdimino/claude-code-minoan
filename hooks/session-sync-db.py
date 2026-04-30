#!/usr/bin/env python3
"""Stop hook: sync final session metadata to tracker.db.

Closes open phases, marks session as not running, and ensures the
session row exists with up-to-date metadata. Also writes tags to DB
if session-tags-infer has already populated session-registry.json.
"""
import json
import os
import pathlib
import sqlite3
import sys
import time

DB_PATH = pathlib.Path.home() / ".claude" / "tracker.db"
REGISTRY_PATH = pathlib.Path.home() / ".claude" / "session-registry.json"
PHASE_DIR = pathlib.Path("/tmp/claude-phase-tracker")


def read_first_line_metadata(transcript_path):
    """Read timestamp, slug, and cwd from first JSONL line."""
    try:
        with open(transcript_path) as f:
            first = f.readline()
            if first:
                obj = json.loads(first)
                return obj.get("timestamp", ""), obj.get("slug", ""), obj.get("cwd", "")
    except Exception:
        pass
    return "", "", ""


def derive_project_from_transcript(transcript_path, cwd=""):
    """Extract project dir, path, and name from transcript path and cwd.

    Uses cwd from JSONL first line (authoritative), falls back to dir name.
    """
    p = pathlib.Path(transcript_path)
    project_dir = p.parent.name
    project_path = cwd or project_dir
    project_name = pathlib.Path(project_path).name or project_dir
    return project_dir, project_path, project_name


def read_custom_title(transcript_path):
    """Read last custom-title event from JSONL tail."""
    try:
        size = os.path.getsize(transcript_path)
        read_bytes = min(size, 131072)
        with open(transcript_path, "rb") as f:
            f.seek(max(0, size - read_bytes))
            tail = f.read().decode("utf-8", errors="replace")
        title = ""
        for line in tail.split("\n"):
            if '"custom-title"' in line:
                try:
                    obj = json.loads(line)
                    if obj.get("type") == "custom-title" and obj.get("customTitle"):
                        title = obj["customTitle"]
                except Exception:
                    pass
        return title
    except Exception:
        return ""


def ensure_session(conn, session_id, transcript_path, now):
    """Upsert session row — create if missing, update metadata if exists."""
    existing = conn.execute(
        "SELECT session_id FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()

    created_at, slug, cwd = read_first_line_metadata(transcript_path)
    project_dir, project_path, project_name = derive_project_from_transcript(transcript_path, cwd)
    custom_title = read_custom_title(transcript_path)
    transcript_size = 0
    try:
        transcript_size = os.path.getsize(transcript_path)
    except Exception:
        pass

    if existing:
        conn.execute(
            """UPDATE sessions SET
                modified_at = ?, is_running = 0, pid = NULL,
                transcript_size = ?,
                slug = COALESCE(?, slug),
                custom_title = COALESCE(?, custom_title)
            WHERE session_id = ?""",
            (now, transcript_size, slug or None, custom_title or None, session_id),
        )
    else:
        conn.execute(
            """INSERT INTO sessions (
                session_id, short_id, project_dir, project_path, project_name,
                cwd, transcript_path, transcript_size, slug, custom_title,
                created_at, modified_at, is_running
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (
                session_id,
                session_id[:8],
                project_dir,
                project_path,
                project_name,
                cwd or None,
                transcript_path,
                transcript_size,
                slug or None,
                custom_title or None,
                created_at or now,
                now,
            ),
        )


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    session_id = data.get("session_id", "")
    transcript_path = data.get("transcript_path", "")

    if not session_id or not DB_PATH.exists():
        return

    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        now = time.strftime("%Y-%m-%dT%H:%M:%S")

        # Ensure session row exists before any FK-dependent operations
        if transcript_path:
            ensure_session(conn, session_id, transcript_path, now)

        # Close any open phases
        conn.execute(
            "UPDATE phases SET ended_at = ?, duration_ms = CAST((julianday(?) - julianday(started_at)) * 86400000 AS INTEGER) WHERE session_id = ? AND ended_at IS NULL",
            (now, now, session_id),
        )

        # Mark session as not running (redundant with ensure_session but covers no-transcript case)
        conn.execute(
            "UPDATE sessions SET is_running = 0, pid = NULL, modified_at = ? WHERE session_id = ?",
            (now, session_id),
        )

        # Sync tags from registry if available
        try:
            with open(REGISTRY_PATH) as f:
                registry = json.load(f).get("sessions", {})
            entry = registry.get(session_id, {})
            if entry:
                tag_rows = []
                for tag in entry.get("tags", []):
                    tag_rows.append((session_id, tag, "auto", "hook:session-tags-infer", now))
                for tag in entry.get("display_tags", []):
                    tag_rows.append((session_id, tag, "display", "hook:session-tags-infer", now))
                for tag in entry.get("user_tags", []):
                    tag_rows.append((session_id, tag, "user", "hook:session-tags-infer", now))

                if tag_rows:
                    conn.executemany(
                        "INSERT OR IGNORE INTO session_tags (session_id, tag, tag_type, source, created_at) VALUES (?, ?, ?, ?, ?)",
                        tag_rows,
                    )
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            conn.close()

    # Clean up phase tracker temp file
    phase_file = PHASE_DIR / f"{session_id}.json"
    try:
        phase_file.unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
