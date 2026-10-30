#!/usr/bin/env python3
"""Stop hook: sync session metadata to tracker.db.

Ensures the session row exists with up-to-date metadata and writes tags
to DB if session-tags-infer has already populated session-registry.json.

Stop fires after every turn, so phase state is left alone here. With
--session-end (SessionEnd hook) it also closes the open phase and removes
the phase-detect window file.
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


# Tag rows that are copies of the registry: written by this hook, or by the
# one-time migrate-to-sqlite.js import. Both are pruned when the registry
# drops a tag; rows from any other source are left alone.
REGISTRY_TAG_SOURCE = "hook:session-tags-infer"
REGISTRY_TAG_SOURCES = (REGISTRY_TAG_SOURCE, "migration:session-registry")
LOG_PATH = pathlib.Path.home() / ".claude" / "logs" / "session-sync-db.log"


def log_error(session_id, where, exc):
    """Hooks must never fail a turn, but a swallowed error still leaves a line."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {session_id[:8]} {where}: "
                    f"{type(exc).__name__}: {exc}\n")
    except OSError:
        pass


def connect():
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    # Autocommit mode + explicit BEGIN IMMEDIATE: the Node indexer writes
    # this DB concurrently (Stop hook, on-search refresh, hourly job). A
    # deferred read-then-write transaction under WAL returns BUSY_SNAPSHOT
    # immediately instead of waiting on busy_timeout.
    conn.isolation_level = None
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def string_list(value):
    """A tagger tag field as clean strings: a lone string is one tag, not
    one tag per character; non-string items are dropped."""
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [v.strip() for v in value if isinstance(v, str) and v.strip()]


def read_registry_entry(session_id):
    """This session's registry entry, or {} for any missing or malformed shape.
    Writers replace the file via tmp+rename, so an unlocked read is whole."""
    try:
        with open(REGISTRY_PATH) as f:
            doc = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except OSError as e:
        log_error(session_id, "read registry", e)
        return {}
    sessions = doc.get("sessions") if isinstance(doc, dict) else None
    entry = sessions.get(session_id) if isinstance(sessions, dict) else None
    return entry if isinstance(entry, dict) else {}


def sync_registry_tags(conn, session_id, entry, now):
    """Mirror the registry's current tag set for this session.

    The tagger rewrites its tags every few turns; appending each version left
    up to 87 live tags per session. Registry-copy rows (REGISTRY_TAG_SOURCES)
    the registry no longer lists are soft-removed via removed_at, so history
    survives. A conflicting row from another source is revived but keeps its
    source, so it is never pruned here.
    """
    current = set()
    for key, tag_type in (("tags", "auto"), ("display_tags", "display"), ("user_tags", "user")):
        for tag in string_list(entry.get(key)):
            current.add((tag, tag_type))

    placeholders = ", ".join("?" * len(REGISTRY_TAG_SOURCES))
    conn.executemany(
        f"""INSERT INTO session_tags (session_id, tag, tag_type, source, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id, tag, tag_type) DO UPDATE SET
              removed_at = NULL,
              source = CASE WHEN session_tags.source IN ({placeholders})
                            THEN excluded.source ELSE session_tags.source END""",
        [(session_id, tag, tag_type, REGISTRY_TAG_SOURCE, now, *REGISTRY_TAG_SOURCES)
         for tag, tag_type in current],
    )
    owned = conn.execute(
        f"""SELECT tag, tag_type FROM session_tags
            WHERE session_id = ? AND source IN ({placeholders}) AND removed_at IS NULL""",
        (session_id, *REGISTRY_TAG_SOURCES),
    ).fetchall()
    conn.executemany(
        "UPDATE session_tags SET removed_at = ? WHERE session_id = ? AND tag = ? AND tag_type = ?",
        [(now, session_id, tag, tag_type) for tag, tag_type in owned if (tag, tag_type) not in current],
    )


def fill_from_registry(conn, session_id, entry):
    """The local tagger's title/summary, labelled 'qwen-local'.

    Fills empty columns and refreshes values it wrote earlier; never replaces
    a value from another source (Claude Code's ai-title/away_summary once the
    indexer writes them, or unlabelled titles from before provenance existed).
    """
    title = entry.get("title")
    summary = entry.get("summary")
    if isinstance(title, str) and title.strip():
        conn.execute(
            """UPDATE sessions SET auto_title = ?, title_source = 'qwen-local'
               WHERE session_id = ? AND (COALESCE(auto_title, '') = '' OR title_source = 'qwen-local')""",
            (title.strip(), session_id),
        )
    if isinstance(summary, str) and summary.strip():
        conn.execute(
            """UPDATE sessions SET summary = ?, summary_source = 'qwen-local'
               WHERE session_id = ? AND (COALESCE(summary, '') = '' OR summary_source = 'qwen-local')""",
            (summary.strip(), session_id),
        )


def end_session(session_id, now):
    """Close the open phase, then drop the phase-detect window file.

    Runs before the transcript check: after `claude purge` or a /cd move the
    transcript is gone, but the phase must still close. The window file goes
    only once the close has committed, or the phase would stay open forever.
    """
    conn = None
    try:
        conn = connect()
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "UPDATE phases SET ended_at = ?, duration_ms = CAST((julianday(?) - julianday(started_at)) * 86400000 AS INTEGER) WHERE session_id = ? AND ended_at IS NULL",
            (now, now, session_id),
        )
        conn.execute("COMMIT")
    except Exception as e:
        log_error(session_id, "close phases", e)
        if conn:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
        return
    finally:
        if conn:
            conn.close()
    try:
        (PHASE_DIR / f"{session_id}.json").unlink(missing_ok=True)
    except OSError:
        pass


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    session_id = data.get("session_id", "")
    transcript_path = data.get("transcript_path", "")
    session_end = "--session-end" in sys.argv[1:]

    if not session_id or not DB_PATH.exists():
        return
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    if session_end:
        end_session(session_id, now)
    # A session with no transcript on disk is a phantom — never upsert it
    if not transcript_path or not os.path.isfile(transcript_path):
        return

    conn = None
    try:
        conn = connect()
        conn.execute("BEGIN IMMEDIATE")
        ensure_session(conn, session_id, transcript_path, now)

        entry = read_registry_entry(session_id)
        if entry:
            # Bad tagger output must never cost the session upsert above
            conn.execute("SAVEPOINT registry")
            try:
                sync_registry_tags(conn, session_id, entry, now)
                fill_from_registry(conn, session_id, entry)
                conn.execute("RELEASE registry")
            except Exception as e:
                conn.execute("ROLLBACK TO registry")
                conn.execute("RELEASE registry")
                log_error(session_id, "registry sync", e)

        conn.execute("COMMIT")
    except Exception as e:
        log_error(session_id, "session sync", e)
        if conn:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
