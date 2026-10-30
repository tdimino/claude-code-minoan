"""Stop-hook registry sync: tags mirror the registry, Qwen fills title/summary gaps.

Run: python3 -m unittest discover -s tests -p 'test_*.py'   (from the suite directory)
"""
import datetime
import json
import unittest

from hookenv import HookEnv

HOOK_SOURCE = "hook:session-tags-infer"


class SessionSync(HookEnv):
    def write_registry(self, **entry):
        self.write_registry_raw({"sessions": {self.sid: entry}})

    def write_registry_raw(self, doc):
        (self.claude / "session-registry.json").write_text(json.dumps(doc))

    def active_tags(self):
        return sorted(self.rows(
            "SELECT tag, tag_type FROM session_tags WHERE session_id = ? AND removed_at IS NULL"))

    def meta(self):
        return self.rows(
            "SELECT auto_title, title_source, summary, summary_source FROM sessions WHERE session_id = ?")

    # ---- session row ------------------------------------------------------

    def test_stop_without_registry_upserts_session(self):
        self.stop()
        self.assertEqual(self.rows("SELECT project_path FROM sessions WHERE session_id = ?"), [("/tmp/fixture",)])

    # ---- timestamps -------------------------------------------------------
    # The indexer writes UTC ('…Z'); the hook's values sort against them, so
    # they must be UTC too. UTC+14 makes a local time impossible to pass off.

    def assert_utc_now(self, value):
        self.assertTrue(value.endswith("Z"), value)
        at = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        self.assertLess(abs((datetime.datetime.now(datetime.timezone.utc) - at).total_seconds()), 120, value)

    def test_modified_at_is_utc_on_insert_and_update(self):
        self.env["TZ"] = "Pacific/Kiritimati"
        self.stop()
        self.assert_utc_now(self.rows("SELECT modified_at FROM sessions WHERE session_id = ?")[0][0])
        self.execute("UPDATE sessions SET modified_at = '2000-01-01T00:00:00.000Z' WHERE session_id = ?", self.sid)
        self.stop()
        self.assert_utc_now(self.rows("SELECT modified_at FROM sessions WHERE session_id = ?")[0][0])

    def test_live_title_change_is_observed_in_utc(self):
        self.env["TZ"] = "Pacific/Kiritimati"
        self.stop()
        with self.transcript.open("a") as f:
            f.write(json.dumps({"type": "custom-title", "sessionId": self.sid, "customTitle": "Renamed"}) + "\n")
        self.stop()
        [(observed,)] = self.rows("SELECT observed_at FROM title_history WHERE session_id = ? AND title = 'Renamed'")
        self.assert_utc_now(observed)

    def test_phase_duration_is_unaffected_by_the_time_zone(self):
        # Phase times stay in the hook's local clock, start and end alike
        self.env["TZ"] = "Pacific/Kiritimati"
        self.hook("phase-detect.py", {"session_id": self.sid, "tool_name": "Edit", "tool_input": {},
                                      "hook_event_name": "PostToolUse"})
        self.hook("phase-detect.py", {"session_id": self.sid, "tool_name": "Edit", "tool_input": {},
                                      "hook_event_name": "PostToolUse"})
        self.stop("--session-end")
        [(ms,)] = self.rows("SELECT duration_ms FROM phases WHERE session_id = ?")
        self.assertLess(abs(ms), 60_000)

    # ---- tags -------------------------------------------------------------

    def test_tags_mirror_the_registry(self):
        self.write_registry(tags=["old a", "old b"], display_tags=["old a"])
        self.stop()
        self.write_registry(tags=["new a", "old b"], display_tags=["new a"])
        self.stop()
        self.assertEqual(self.active_tags(), [
            ("new a", "auto"), ("new a", "display"), ("old b", "auto")])

    def test_dropped_tags_are_soft_removed_and_can_return(self):
        self.write_registry(tags=["a", "b"])
        self.stop()
        self.write_registry(tags=["b"])
        self.stop()
        self.assertEqual(self.rows(
            "SELECT tag FROM session_tags WHERE session_id = ? AND removed_at IS NOT NULL"), [("a",)])
        self.write_registry(tags=["a", "b"])
        self.stop()
        self.assertEqual(self.active_tags(), [("a", "auto"), ("b", "auto")])

    def test_user_tags_mirror(self):
        self.write_registry(user_tags=["pinned"])
        self.stop()
        self.assertEqual(self.active_tags(), [("pinned", "user")])

    def test_migration_rows_are_pruned_like_hook_rows(self):
        # migrate-to-sqlite.js copied the registry under its own source label
        self.stop()
        self.execute(
            "INSERT INTO session_tags (session_id, tag, tag_type, source) VALUES (?, 'stale', 'auto', 'migration:session-registry')",
            self.sid)
        self.write_registry(tags=["fresh"])
        self.stop()
        self.assertEqual(self.active_tags(), [("fresh", "auto")])

    def test_manual_tags_survive(self):
        self.stop()
        self.execute(
            "INSERT INTO session_tags (session_id, tag, tag_type, source) VALUES (?, 'mine', 'user', 'manual')",
            self.sid)
        self.write_registry(tags=["auto one"])
        self.stop()
        self.assertEqual(self.active_tags(), [("auto one", "auto"), ("mine", "user")])
        self.assertEqual(self.rows(
            "SELECT source FROM session_tags WHERE session_id = ? AND tag = 'mine'"), [("manual",)])

    # ---- malformed tagger output -------------------------------------------

    def test_string_tags_are_one_tag_not_characters(self):
        self.write_registry(tags="auth bug")
        self.stop()
        self.assertEqual(self.active_tags(), [("auth bug", "auto")])

    def test_bad_tag_values_are_skipped_not_fatal(self):
        self.write_registry(tags=["ok", {"bad": 1}, None, 7], title="Still titled")
        self.stop()
        self.assertEqual(self.active_tags(), [("ok", "auto")])
        self.assertEqual(self.meta()[0][0], "Still titled")

    def test_malformed_registry_never_drops_the_session_sync(self):
        for doc in ({"sessions": None}, {"sessions": {self.sid: "not a dict"}}, ["not", "a", "dict"]):
            with self.subTest(doc=doc):
                self.write_registry_raw(doc)
                self.stop()
                self.assertEqual(self.rows("SELECT count(*) FROM sessions WHERE session_id = ?"), [(1,)])

    # ---- title / summary --------------------------------------------------

    def test_registry_title_and_summary_fill_gaps(self):
        self.write_registry(title="Qwen title", summary="Qwen summary.")
        self.stop()
        self.assertEqual(self.meta(), [("Qwen title", "qwen-local", "Qwen summary.", "qwen-local")])

    def test_registry_refreshes_its_own_values(self):
        self.write_registry(title="First guess", summary="First summary.")
        self.stop()
        self.write_registry(title="Better title", summary="Better summary.")
        self.stop()
        self.assertEqual(self.meta(), [("Better title", "qwen-local", "Better summary.", "qwen-local")])

    def test_registry_never_overwrites_other_sources(self):
        self.stop()
        self.execute(
            """UPDATE sessions SET auto_title = 'AI title', title_source = 'claude-code',
               summary = 'Away recap.', summary_source = 'claude-code' WHERE session_id = ?""",
            self.sid)
        self.write_registry(title="Qwen title", summary="Qwen summary.")
        self.stop()
        self.assertEqual(self.meta(), [("AI title", "claude-code", "Away recap.", "claude-code")])

    def test_unlabelled_legacy_title_is_kept(self):
        self.stop()
        self.execute("UPDATE sessions SET auto_title = 'Legacy title' WHERE session_id = ?", self.sid)
        self.write_registry(title="Qwen title")
        self.stop()
        self.assertEqual(self.meta()[0][:2], ("Legacy title", None))


if __name__ == "__main__":
    unittest.main()
