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
    """Read timestamp, slug, and cwd from the head of the JSONL.

    The first line is not always a message entry (summaries, system events),
    so scan up to 20 lines until cwd appears.
    """
    timestamp, slug, cwd = "", "", ""
    try:
        with open(transcript_path) as f:
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                timestamp = timestamp or obj.get("timestamp", "")
                slug = slug or obj.get("slug", "")
                cwd = cwd or obj.get("cwd", "")
                if timestamp and slug and cwd:
                    break
    except Exception:
        pass
    return timestamp, slug, cwd


def decode_project_dir(project_dir):
    """Decode an encoded project dir name (-Users-x-y) to an absolute path.

    Mirrors decodeProjectPath in lib/tracker-utils.js: probes the filesystem,
    preferring the longest dash-joined segment run that exists as a directory.
    """
    if not project_dir.startswith("-"):
        return project_dir
    segments = project_dir[1:].split("-")
    current = "/"
    i = 0
    while i < len(segments):
        best_len = 0
        for j in range(len(segments) - 1, i - 1, -1):
            candidate = "-".join(segments[i:j + 1])
            try:
                if os.path.exists(os.path.join(current, candidate)):
                    best_len = j - i + 1
                    break
            except OSError:
                break
        if best_len:
            current = os.path.join(current, "-".join(segments[i:i + best_len]))
            i += best_len
        else:
            current = os.path.join(current, segments[i])
            i += 1
    return current


def derive_project_from_transcript(transcript_path, cwd=""):
    """Extract project dir, path, and name from transcript path and cwd.

    Uses cwd from the JSONL head (authoritative); falls back to decoding the
    encoded dir name rather than storing it verbatim.
    """
    p = pathlib.Path(transcript_path)
    project_dir = p.parent.name
    project_path = cwd or decode_project_dir(project_dir)
    project_name = pathlib.Path(project_path).name or project_dir
    return project_dir, project_path, project_name


def read_custom_title(transcript_path, session_id=None):
    """Read last custom-title event from JSONL tail.

    A /rename issued after /resume writes its custom-title line into the
    ACTIVE file while targeting another session via the line's sessionId —
    Claude Code's own scanner ignores that field and mis-titles the containing
    session. We honor it: lines targeting a different session are skipped.
    """
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
                        target = obj.get("sessionId")
                        if session_id and target and target != session_id:
                            continue
                        title = obj["customTitle"]
                except Exception:
                    pass
        return title
    except Exception:
        return ""


def record_title_change(conn, session_id, new_title, old_title, now):
    """Log a live title change to title_history and drop an auto-checkpoint.

    first_seen_seq -1 marks live capture; the next indexer pass over this file
    replaces these rows with seq-anchored ones (DELETE by observed_in).
    """
    if not new_title or new_title == (old_title or ""):
        return
    try:
        conn.execute(
            """INSERT OR IGNORE INTO title_history
               (session_id, title, source, observed_at, observed_in, first_seen_seq)
               VALUES (?, ?, 'user', ?, ?, -1)""",
            (session_id, new_title, now, session_id),
        )
        label = f"title: {new_title[:60]}"
        conn.execute(
            """INSERT OR IGNORE INTO checkpoints (session_id, label, summary)
               VALUES (?, ?, ?)""",
            (session_id, label,
             f"Session renamed to \"{new_title[:120]}\""
             + (f" (was \"{old_title[:80]}\")" if old_title else "")),
        )
    except Exception as e:
        # Best-effort — never block the sync, but leave a breadcrumb so a
        # schema drift doesn't silence title capture forever
        sys.stderr.write(f"record_title_change: {e}\n")


def ensure_session(conn, session_id, transcript_path, now):
    """Upsert session row — create if missing, update metadata if exists."""
    existing = conn.execute(
        "SELECT session_id, custom_title FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()

    created_at, slug, cwd = read_first_line_metadata(transcript_path)
    project_dir, project_path, project_name = derive_project_from_transcript(transcript_path, cwd)
    custom_title = read_custom_title(transcript_path, session_id)
    transcript_size = 0
    try:
        transcript_size = os.path.getsize(transcript_path)
    except Exception:
        pass

    if existing:
        record_title_change(conn, session_id, custom_title, existing[1], now)
        # Also self-repair path fields — rows written before decode_project_dir
        # existed carry the encoded dir name as project_path
        conn.execute(
            """UPDATE sessions SET
                modified_at = ?, is_running = 0, pid = NULL,
                transcript_size = ?,
                slug = COALESCE(?, slug),
                custom_title = COALESCE(?, custom_title),
                project_path = CASE WHEN ? LIKE '/%' THEN ? ELSE project_path END,
                project_name = CASE WHEN ? LIKE '/%' THEN ? ELSE project_name END,
                cwd = COALESCE(?, cwd),
                transcript_path = COALESCE(?, transcript_path)
            WHERE session_id = ?""",
            (now, transcript_size, slug or None, custom_title or None,
             project_path, project_path, project_path, project_name,
             cwd or None, transcript_path or None, session_id),
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
    # A session with no transcript on disk is a phantom — never upsert it
    if not transcript_path or not os.path.isfile(transcript_path):
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
