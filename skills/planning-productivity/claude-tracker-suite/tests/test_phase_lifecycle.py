"""Phase lifecycle across turns: a Stop must not reset phase state.

Run: python3 -m unittest discover -s tests -p 'test_*.py'   (from the suite directory)
"""
import sqlite3
import threading
import time
import unittest

from hookenv import PHASE_DIR, HookEnv


class PhaseLifecycle(HookEnv):
    def test_stop_keeps_the_open_phase(self):
        self.tool("Edit")
        self.tool("Edit")
        self.stop()
        self.tool("Edit")
        self.tool("Edit")
        phases = self.rows("SELECT phase, ended_at FROM phases WHERE session_id = ?")
        self.assertEqual(phases, [("implementing", None)])

    def test_hysteresis_survives_stop(self):
        # One signal, a Stop, then a second signal: the pending count must
        # carry across the turn boundary (the window file is not reset)
        self.tool("Bash", {"command": "pytest"})
        self.stop()
        self.tool("Bash", {"command": "pytest"})
        self.assertEqual(self.rows("SELECT phase FROM phases WHERE session_id = ?"), [("testing",)])

    def test_session_end_closes_phase_and_clears_state(self):
        self.tool("Edit")
        self.tool("Edit")
        self.stop("--session-end")
        phases = self.rows("SELECT phase, ended_at IS NOT NULL FROM phases WHERE session_id = ?")
        self.assertEqual(phases, [("implementing", 1)])
        self.assertFalse((PHASE_DIR / f"{self.sid}.json").exists())

    def test_session_end_without_transcript_still_closes_phase(self):
        # After `claude purge` or a /cd move the transcript path is gone
        self.tool("Edit")
        self.tool("Edit")
        self.transcript.unlink()
        self.stop("--session-end")
        self.assertEqual(self.rows("SELECT count(*) FROM phases WHERE session_id = ? AND ended_at IS NULL"), [(0,)])
        self.assertFalse((PHASE_DIR / f"{self.sid}.json").exists())

    def test_auto_checkpoints_only_at_milestones(self):
        for name in ("Read", "Read", "Edit", "Edit", "Edit", "Edit"):
            self.tool(name)
        self.tool("Bash", {"command": "git commit -m x"})
        labels = [r[0] for r in self.rows(
            "SELECT label FROM checkpoints WHERE session_id = ? AND label LIKE 'auto:%' ORDER BY id")]
        self.assertEqual(len(labels), 1, labels)
        self.assertIn("committing", labels[0])

    def test_testing_and_deploying_are_milestones(self):
        self.tool("Bash", {"command": "pytest"})
        self.tool("Bash", {"command": "pytest"})
        self.tool("Bash", {"command": "git push"})
        phases = [r[0] for r in self.rows(
            "SELECT phase FROM checkpoints WHERE session_id = ? AND label LIKE 'auto:%' ORDER BY id")]
        self.assertEqual(phases, ["testing", "deploying"])

    def test_lost_window_does_not_reopen_the_same_phase(self):
        self.tool("Edit")
        self.tool("Edit")
        (PHASE_DIR / f"{self.sid}.json").unlink()
        self.tool("Edit")
        self.tool("Edit")
        self.assertEqual(len(self.rows("SELECT id FROM phases WHERE session_id = ?")), 1)

    def test_failed_write_is_retried_not_forgotten(self):
        # A transition that could not be written (DB locked past busy_timeout)
        # must not be recorded as current in the window file, or the phase
        # is never written for the rest of the session
        self.tool("Edit")
        lock = sqlite3.connect(self.db, timeout=10, isolation_level=None)
        lock.execute("BEGIN EXCLUSIVE")
        try:
            self.tool("Edit")  # would record 'implementing'; DB is locked
        finally:
            lock.execute("ROLLBACK")
            lock.close()
        self.assertEqual(self.rows("SELECT count(*) FROM phases WHERE session_id = ?"), [(0,)])
        self.tool("Edit")
        self.assertEqual(self.rows("SELECT phase FROM phases WHERE session_id = ?"), [("implementing",)])

    def test_concurrent_calls_open_one_phase(self):
        self.tool("Edit")
        threads = [threading.Thread(target=self.tool, args=("Edit",)) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(self.rows("SELECT count(*) FROM phases WHERE session_id = ?"), [(1,)])


if __name__ == "__main__":
    unittest.main()
