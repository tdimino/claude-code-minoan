"""Throwaway HOME with a fresh tracker.db for driving the real tracker hooks."""
import json
import os
import pathlib
import sqlite3
import subprocess
import tempfile
import unittest
import uuid

SUITE = pathlib.Path(__file__).resolve().parent.parent
REPO = SUITE.parent.parent.parent
HOOKS = pathlib.Path(os.environ.get("TRACKER_HOOKS_DIR", REPO / "hooks"))
LIB = pathlib.Path(os.environ.get("TRACKER_LIB_DIR", REPO / "lib"))
PHASE_DIR = pathlib.Path("/tmp/claude-phase-tracker")


class HookEnv(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="tracker-home-")
        self.addCleanup(subprocess.run, ["rm", "-rf", self.home])
        self.env = {**os.environ, "HOME": self.home}
        self.sid = str(uuid.uuid4())
        self.addCleanup(lambda: (PHASE_DIR / f"{self.sid}.json").unlink(missing_ok=True))
        self.claude = pathlib.Path(self.home) / ".claude"
        self.claude.mkdir()
        subprocess.run(
            ["node", "-e", f"require({json.dumps(str(LIB / 'tracker-db.js'))}).initSchema()"],
            env=self.env, check=True, capture_output=True,
        )
        self.db = self.claude / "tracker.db"
        proj = self.claude / "projects" / "-tmp-fixture"
        proj.mkdir(parents=True)
        self.transcript = proj / f"{self.sid}.jsonl"
        self.transcript.write_text(json.dumps({
            "type": "user", "sessionId": self.sid, "cwd": "/tmp/fixture",
            "timestamp": "2026-10-30T12:00:00.000Z",
            "message": {"role": "user", "content": "go"},
        }) + "\n")

    def hook(self, script, payload, *args):
        r = subprocess.run(
            ["python3", str(HOOKS / script), *args],
            input=json.dumps(payload), text=True, env=self.env,
            capture_output=True, cwd=self.home,
        )
        self.assertEqual(r.returncode, 0, f"{script} failed:\n{r.stderr}")
        return r

    def hook_log(self):
        """Errors the hooks swallowed but logged (they never fail a turn)."""
        log = self.claude / "logs" / "session-sync-db.log"
        return log.read_text() if log.exists() else ""

    def tool(self, name, tool_input=None):
        return self.hook("phase-detect.py", {
            "session_id": self.sid, "tool_name": name, "tool_input": tool_input or {},
            "hook_event_name": "PostToolUse",
        })

    def stop(self, *args):
        self.hook("session-sync-db.py", {
            "session_id": self.sid, "transcript_path": str(self.transcript),
            "hook_event_name": "SessionEnd" if args else "Stop",
        }, *args)

    def rows(self, sql, *params):
        with sqlite3.connect(self.db) as conn:
            return conn.execute(sql, params or (self.sid,)).fetchall()

    def execute(self, sql, *params):
        with sqlite3.connect(self.db) as conn:
            conn.execute(sql, params)
