#!/usr/bin/env python3
"""Offline tests for first_world.py: no key, no network. Run: python3 test_first_world.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from first_world import OUTPUT_CAP, apply_edits, build_body, extract_html, parse_edits  # noqa: E402

SOURCE = "<!doctype html>\n<html>\nconst A = 1;\nconst B = 2;   \nconst C = 3;\nconst B2 = 2;\n</html>\n"


def block(search: str, replace: str) -> str:
    return f"<<<<<<< SEARCH\n{search}\n=======\n{replace}\n>>>>>>> REPLACE\n"


class ApplyEdits(unittest.TestCase):
    def test_replace(self):
        out, log = apply_edits(SOURCE, "Changed A.\n" + block("const A = 1;", "const A = 10;"))
        self.assertIn("const A = 10;", out)
        self.assertNotIn("const A = 1;\n", out)
        self.assertEqual([e["ok"] for e in log], [True])

    def test_blocks_apply_in_order(self):
        out, log = apply_edits(SOURCE, block("const A = 1;", "const A = 10;") + block("const A = 10;", "const A = 11;"))
        self.assertIn("const A = 11;", out)
        self.assertTrue(all(e["ok"] for e in log))

    def test_delete_with_empty_replacement(self):
        out, log = apply_edits(SOURCE, "<<<<<<< SEARCH\nconst C = 3;\n=======\n>>>>>>> REPLACE\n")
        self.assertNotIn("const C", out)
        self.assertTrue(log[0]["ok"])

    def test_missing_search_is_rejected_and_the_rest_applied(self):
        out, log = apply_edits(SOURCE, block("const Z = 9;", "x") + block("const C = 3;", "const C = 30;"))
        self.assertEqual([e["ok"] for e in log], [False, True])
        self.assertEqual(log[0]["reason"], "SEARCH not found")
        self.assertIn("const C = 30;", out)

    def test_ambiguous_search_is_rejected(self):
        out, log = apply_edits(SOURCE, block("= 2;", "= 20;"))
        self.assertFalse(log[0]["ok"])
        self.assertIn("2 places", log[0]["reason"])
        self.assertEqual(out, SOURCE)

    def test_trailing_whitespace_is_forgiven(self):
        out, log = apply_edits(SOURCE, block("const B = 2;\nconst C = 3;", "const B = 5;\nconst C = 3;"))
        self.assertTrue(log[0]["ok"])
        self.assertIn("const B = 5;\nconst C = 3;", out)

    def test_unclosed_block_is_not_applied(self):
        out, log = apply_edits(SOURCE, "<<<<<<< SEARCH\nconst A = 1;\n=======\nconst A = ")
        self.assertEqual((out, log), (SOURCE, []))
        self.assertTrue(parse_edits("<<<<<<< SEARCH\nconst A = 1;\n=======\nconst A = ")[1])
        self.assertFalse(parse_edits(block("const A = 1;", "const A = 10;"))[1])

    def test_malformed_block_does_not_swallow_the_next(self):
        bad = "<<<<<<< SEARCH\nconst A = 1;\n"  # no divider and no close before the next block opens
        out, log = apply_edits(SOURCE, bad + block("const C = 3;", "const C = 30;"))
        self.assertEqual([(e["ok"], e["reason"]) for e in log], [(False, "malformed block"), (True, None)])
        self.assertIn("const C = 30;", out)
        self.assertIn("const A = 1;", out)

    def test_overlapping_repeat_is_ambiguous(self):
        source = "x();\nx();\nx();\n"
        out, log = apply_edits(source, block("x();\nx();", "y();"))
        self.assertFalse(log[0]["ok"])
        self.assertEqual(out, source)

    def test_text_between_blocks_is_kept_apart(self):
        blocks, cut_off, outside = parse_edits("Changed A.\n" + block("const A = 1;", "const A = 10;") + "Done.")
        self.assertEqual((blocks, cut_off, outside), ([("const A = 1;", "const A = 10;")], False, "Changed A.\nDone."))


class Calls(unittest.TestCase):
    def test_max_tokens_is_clamped_to_the_real_cap(self):
        class Args:
            max_tokens, effort, temperature = 943718, "none", None
        body = build_body("google/gemini-4-neon", {"top_provider": {"max_completion_tokens": 943718}}, "x", Args)
        self.assertEqual(body["max_tokens"], OUTPUT_CAP)

    def test_first_closing_tag_ends_the_document(self):
        html, complete, outside = extract_html("<!doctype html><html></html>\nNote: I closed with </html> and then")
        self.assertTrue(complete)
        self.assertTrue(html.rstrip().endswith("</html>"))
        self.assertIn("Note", outside)


if __name__ == "__main__":
    unittest.main()
