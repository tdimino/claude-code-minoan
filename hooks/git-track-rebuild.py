#!/usr/bin/env python3
"""
Rebuild git-tracking-index.json from git-tracking.jsonl.

Called from SessionEnd hook chain. Reads the append-only JSONL event log
and builds a bidirectional index: sessions -> repos and repos -> sessions.

Uses fcntl file locking + atomic rename (matches soul-registry.py pattern).

Usage:
    python3 ~/.claude/hooks/git-track-rebuild.py [--max-lines 10000]
"""

import datetime
import fcntl
import json
import os
import sys
import tempfile

CLAUDE_DIR = os.path.expanduser("~/.claude")
JSONL_FILE = os.path.join(CLAUDE_DIR, "git-tracking.jsonl")
INDEX_FILE = os.path.join(CLAUDE_DIR, "git-tracking-index.json")
DEFAULT_MAX_LINES = 10000


def load_jsonl(max_lines=DEFAULT_MAX_LINES):
    """Read JSONL event log, return list of parsed events."""
    if not os.path.exists(JSONL_FILE):
        return []

    events = []
    try:
        with open(JSONL_FILE) as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []

    return events


def build_index(events):
    """Build bidirectional index from events."""
    sessions = {}  # session_id -> session data
    repo_index = {}  # repo_path -> [session_ids]

    # First pass: collect all events by session
    for event in events:
        sid = event.get("sid", "")
        if not sid:
            continue

        # Skip enrichment/result lines (they supplement, not create sessions)
        if event.get("type") == "result":
            continue

        repo = event.get("repo", "")
        if not repo:
            continue

        # Initialize session entry
        if sid not in sessions:
            sessions[sid] = {
                "short_id": event.get("short", sid[:8]),
                "start_cwd": event.get("cwd", ""),
                "first_seen": event.get("ts", ""),
                "last_git_at": event.get("ts", ""),
                "repos": {},
            }

        session = sessions[sid]

        # Update session timestamps
        ts = event.get("ts", "")
        if ts > session["last_git_at"]:
            session["last_git_at"] = ts

        # Initialize repo entry within session
        if repo not in session["repos"]:
            session["repos"][repo] = {
                "remote": event.get("remote", ""),
                "branches": [],
                "operations": [],
                "commits": [],
                "first_seen": ts,
                "last_seen": ts,
            }

        repo_data = session["repos"][repo]

        # Update repo timestamps
        if ts > repo_data["last_seen"]:
            repo_data["last_seen"] = ts

        # Update remote if we got a better one
        if event.get("remote") and not repo_data["remote"]:
            repo_data["remote"] = event["remote"]

        # Add branch
        branch = event.get("branch", "")
        if branch and branch not in repo_data["branches"]:
            repo_data["branches"].append(branch)

        # Add operations (deduplicated)
        ops = event.get("ops", "")
        if ops:
            for op in ops.split(","):
                op = op.strip()
                if op and op not in repo_data["operations"]:
                    repo_data["operations"].append(op)

        # Build repo_index
        if repo not in repo_index:
            repo_index[repo] = []
        if sid not in repo_index[repo]:
            repo_index[repo].append(sid)

    # Second pass: enrich with result data (commit hashes, branch switches)
    for event in events:
        if event.get("type") != "result":
            continue

        sid = event.get("sid", "")
        repo = event.get("repo", "")
        if not sid or not repo:
            continue

        if sid not in sessions or repo not in sessions[sid]["repos"]:
            continue

        repo_data = sessions[sid]["repos"][repo]

        # Add commit
        commit_hash = event.get("hash", "")
        if commit_hash:
            # Check for duplicate
            existing_hashes = {c["hash"] for c in repo_data["commits"]}
            if commit_hash not in existing_hashes:
                repo_data["commits"].append({
                    "hash": commit_hash,
                    "msg": event.get("commit_msg", ""),
                    "ts": event.get("ts", ""),
                    "branch": event.get("switched_branch", ""),
                })

        # Add switched branch
        switched = event.get("switched_branch", "")
        if switched and switched not in repo_data["branches"]:
            repo_data["branches"].append(switched)

    return {
        "version": 1,
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "sessions": sessions,
        "repo_index": repo_index,
    }


def save_index(index_data):
    """Atomic write with file locking (matches soul-registry.py pattern)."""
    fd, tmp_path = tempfile.mkstemp(dir=CLAUDE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(index_data, f, indent=2)
            f.write("\n")
            fcntl.flock(f, fcntl.LOCK_UN)
        os.rename(tmp_path, INDEX_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def truncate_jsonl(max_lines=DEFAULT_MAX_LINES):
    """Trim JSONL to last max_lines if it's grown too large."""
    if not os.path.exists(JSONL_FILE):
        return

    try:
        with open(JSONL_FILE) as f:
            lines = f.readlines()
    except OSError:
        return

    if len(lines) <= max_lines:
        return

    # Keep only the last max_lines
    trimmed = lines[-max_lines:]
    try:
        fd, tmp_path = tempfile.mkstemp(dir=CLAUDE_DIR, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            f.writelines(trimmed)
        os.rename(tmp_path, JSONL_FILE)
        print(
            f"Trimmed git-tracking.jsonl: {len(lines)} -> {len(trimmed)} lines",
            file=sys.stderr,
        )
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def main():
    max_lines = DEFAULT_MAX_LINES

    # Parse --max-lines argument
    args = sys.argv[1:]
    if "--max-lines" in args:
        idx = args.index("--max-lines")
        if idx + 1 < len(args):
            try:
                max_lines = int(args[idx + 1])
            except ValueError:
                pass

    if not os.path.exists(JSONL_FILE):
        return

    events = load_jsonl(max_lines)
    if not events:
        return

    index_data = build_index(events)
    save_index(index_data)

    # Truncate JSONL if needed
    truncate_jsonl(max_lines)

    session_count = len(index_data["sessions"])
    repo_count = len(index_data["repo_index"])
    print(
        f"Git tracking index rebuilt: {session_count} sessions, {repo_count} repos",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
