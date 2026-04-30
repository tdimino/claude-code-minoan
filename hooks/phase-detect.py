#!/usr/bin/env python3
"""PostToolUse hook: detect workflow phase from rolling tool window.

Matcher: * (all tools)
Maintains a rolling window of the last 10 tool calls per session in
/tmp/claude-phase-tracker/{session_id}.json. Detects phase transitions
with hysteresis (requires 2+ consecutive signals). Writes to tracker.db
only on actual transitions.

Runs async so Python startup latency doesn't block the tool chain.
"""
import fcntl
import json
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import time

WINDOW_SIZE = 10
HYSTERESIS_COUNT = 2
PHASE_DIR = pathlib.Path("/tmp/claude-phase-tracker")
DB_PATH = pathlib.Path.home() / ".claude" / "tracker.db"

TEST_PATTERNS = ["pytest", "jest", "vitest", "cargo test", "go test", "npm test", "bun test", "make test", "rake test", "rspec"]
LINT_PATTERNS = ["eslint", "clippy", "pylint", "ruff", "flake8", "rubocop", "prettier", "biome"]
DEBUG_PATTERNS = ["console.log", "print(", "debugger", "pdb", "byebug", "binding.pry", "gdb", "lldb"]
COMMIT_PATTERNS = ["git commit"]
DEPLOY_PATTERNS = ["git push", "gh pr create", "gh pr merge", "deploy"]


def classify_tool(tool_name, tool_input):
    """Classify a single tool call into a phase signal."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        cmd_lower = cmd.lower()

        for p in COMMIT_PATTERNS:
            if p in cmd_lower:
                return "committing"
        for p in DEPLOY_PATTERNS:
            if p in cmd_lower:
                return "deploying"
        for p in TEST_PATTERNS:
            if p in cmd_lower:
                return "testing"
        for p in LINT_PATTERNS:
            if p in cmd_lower:
                return "reviewing"
        for p in DEBUG_PATTERNS:
            if p in cmd:
                return "debugging"

        return None

    if tool_name in ("Edit", "Write", "NotebookEdit"):
        return "implementing"

    if tool_name in ("Read", "Grep", "Glob", "LS"):
        return "exploring"

    if tool_name in ("EnterPlanMode", "ExitPlanMode"):
        return "planning"

    if tool_name == "Agent":
        return None

    return None


def detect_phase(window):
    """Determine the dominant phase from the rolling window with confidence."""
    if not window:
        return None, 0.0

    counts = {}
    for entry in window:
        phase = entry.get("phase")
        if phase:
            counts[phase] = counts.get(phase, 0) + 1

    if not counts:
        return None, 0.0

    total = len(window)

    # High-confidence signals (any occurrence)
    for high_conf in ("committing", "deploying"):
        if counts.get(high_conf, 0) >= 1:
            return high_conf, 0.95

    # Majority-based detection
    best_phase = max(counts, key=counts.get)
    ratio = counts[best_phase] / total

    confidence_map = {
        "testing": 0.90,
        "reviewing": 0.85,
        "planning": 0.90,
        "implementing": 0.80,
        "exploring": 0.75,
        "debugging": 0.75,
    }

    if ratio >= 0.5:
        return best_phase, confidence_map.get(best_phase, 0.70)
    if ratio >= 0.3 and counts[best_phase] >= HYSTERESIS_COUNT:
        return best_phase, confidence_map.get(best_phase, 0.70) * 0.8

    return None, 0.0


def load_window(session_id):
    """Load the rolling window from /tmp with shared lock."""
    fpath = PHASE_DIR / f"{session_id}.json"
    try:
        with open(fpath) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
        return data.get("window", []), data.get("current_phase"), data.get("pending_phase"), data.get("pending_count", 0), data.get("turn_number", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return [], None, None, 0, 0


def save_window(session_id, window, current_phase, pending_phase, pending_count, turn_number):
    """Save the rolling window to /tmp with exclusive lock + atomic rename."""
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    fpath = PHASE_DIR / f"{session_id}.json"
    fd, tmp = tempfile.mkstemp(dir=str(PHASE_DIR), suffix=".tmp")
    try:
        with open(fd, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump({
                "window": window[-WINDOW_SIZE:],
                "current_phase": current_phase,
                "pending_phase": pending_phase,
                "pending_count": pending_count,
                "turn_number": turn_number,
            }, f)
        pathlib.Path(tmp).rename(fpath)
    except Exception:
        try:
            pathlib.Path(tmp).unlink(missing_ok=True)
        except Exception:
            pass


def get_git_state():
    """Get current branch and HEAD hash. Skips subprocess if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD", "--short", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode != 0:
            return None, None
        lines = result.stdout.strip().split("\n")
        branch = lines[0] if len(lines) > 0 else None
        commit = lines[1] if len(lines) > 1 else None
        return branch or None, commit or None
    except Exception:
        return None, None


def record_transition(session_id, phase, turn_number, confidence, tool_counts):
    """Write phase transition and auto-checkpoint to tracker.db."""
    if not DB_PATH.exists():
        return

    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=2)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")

        now = time.strftime("%Y-%m-%dT%H:%M:%S")

        # Get previous phase for checkpoint label
        prev = conn.execute(
            "SELECT phase FROM phases WHERE session_id = ? AND ended_at IS NULL",
            (session_id,),
        ).fetchone()
        prev_phase = prev[0] if prev else None

        # Close current open phase
        conn.execute(
            "UPDATE phases SET ended_at = ?, turn_end = ?, duration_ms = CAST((julianday(?) - julianday(started_at)) * 86400000 AS INTEGER) WHERE session_id = ? AND ended_at IS NULL",
            (now, turn_number, now, session_id),
        )

        # Insert new phase
        conn.execute(
            "INSERT INTO phases (session_id, phase, turn_start, started_at, trigger, confidence, tool_counts) VALUES (?, ?, ?, ?, 'auto', ?, ?)",
            (session_id, phase, turn_number, now, confidence, json.dumps(tool_counts)),
        )

        # Auto-checkpoint on phase transition
        label = f"auto: {prev_phase} -> {phase} @{turn_number}" if prev_phase else f"auto: -> {phase} @{turn_number}"
        git_branch, git_commit = get_git_state()
        conn.execute(
            "INSERT OR IGNORE INTO checkpoints (session_id, label, phase, git_branch, git_commit_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, label, phase, git_branch, git_commit, now),
        )

        conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            conn.close()


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    session_id = data.get("session_id", "")
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if not session_id:
        return

    phase_signal = classify_tool(tool_name, tool_input)

    window, current_phase, pending_phase, pending_count, turn_number = load_window(session_id)
    turn_number += 1

    window.append({
        "tool": tool_name,
        "phase": phase_signal,
        "ts": time.time(),
    })
    window = window[-WINDOW_SIZE:]

    detected, confidence = detect_phase(window)

    if detected and detected != current_phase:
        if detected == pending_phase:
            pending_count += 1
        else:
            pending_phase = detected
            pending_count = 1

        # Hysteresis: require HYSTERESIS_COUNT consecutive signals for non-high-confidence phases
        if pending_count >= HYSTERESIS_COUNT or confidence >= 0.95:
            tool_counts = {}
            for entry in window:
                t = entry.get("tool", "unknown")
                tool_counts[t] = tool_counts.get(t, 0) + 1

            record_transition(session_id, detected, turn_number, confidence, tool_counts)
            current_phase = detected
            pending_phase = None
            pending_count = 0
    elif detected == current_phase:
        pending_phase = None
        pending_count = 0

    save_window(session_id, window, current_phase, pending_phase, pending_count, turn_number)


if __name__ == "__main__":
    main()
