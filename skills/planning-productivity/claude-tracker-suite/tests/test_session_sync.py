"""Stop-hook registry sync: tags mirror the registry, Qwen fills title/summary gaps.

Run: python3 -m unittest discover -s tests -p 'test_*.py'   (from the suite directory)
"""
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
