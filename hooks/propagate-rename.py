#!/usr/bin/env python3
"""Stop hook: propagate customTitle from sessions-index.json to session-summaries.json.

Runs on every Stop event. Fast path (~20ms) when nothing changed.
No LLM calls, no network — pure local JSON reconciliation.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

SUMMARY_CACHE = pathlib.Path.home() / ".claude" / "session-summaries.json"


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    if not session_id or not transcript_path:
        return

    # 1. Derive project dir from transcript path
    project_dir = pathlib.Path(transcript_path).parent
    index_path = project_dir / "sessions-index.json"

    if not index_path.exists():
        return

    # 2. Read customTitle for this session from sessions-index.json
    try:
        index_data = json.loads(index_path.read_text())
    except (json.JSONDecodeError, OSError):
        return

    custom_title = None
    for entry in index_data.get("entries", []):
        if entry.get("sessionId") == session_id:
            custom_title = entry.get("customTitle") or ""
            break

    if not custom_title:
        return  # No customTitle set — fast path exit

    # 3. Check if session-summaries.json already has this title
    cache = {}
    if SUMMARY_CACHE.exists():
        try:
            cache = json.loads(SUMMARY_CACHE.read_text())
        except (json.JSONDecodeError, OSError):
            cache = {}

    existing = cache.get(session_id, {})
    if existing.get("title") == custom_title:
        return  # Already in sync — fast path exit

    # 4. Update the cache entry (preserve existing fields)
    if session_id not in cache:
        cache[session_id] = {}
    cache[session_id]["title"] = custom_title

    # 5. Atomic write (tmp + rename)
    try:
        tmp = SUMMARY_CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, indent=2))
        tmp.rename(SUMMARY_CACHE)
    except OSError:
        return

    # 6. Fire update-active-projects.py in background to rebuild active-projects.md
    #    (Terminal title is handled by on-ready.sh which reads customTitle directly)
    update_script = pathlib.Path.home() / ".claude" / "scripts" / "update-active-projects.py"
    if update_script.exists():
        try:
            fd, tmpfile = tempfile.mkstemp(prefix="hook-rename-", suffix=".json")
            with os.fdopen(fd, "w") as f:
                json.dump(hook_input, f)
            subprocess.Popen(
                ["python3", str(update_script), tmpfile],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError:
            pass


if __name__ == "__main__":
    main()
