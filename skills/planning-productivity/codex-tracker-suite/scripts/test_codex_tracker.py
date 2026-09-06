#!/usr/bin/env python3

import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("codex_tracker.py")
SPEC = importlib.util.spec_from_file_location("codex_tracker", MODULE_PATH)
tracker = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(tracker)


class TrackerTests(unittest.TestCase):
    def test_resume_command_quotes_working_directory(self):
        thread = {"id": "abc-123", "cwd": "/tmp/project with spaces"}
        self.assertEqual(
            tracker.resume_command(thread),
            "cd '/tmp/project with spaces' && codex resume abc-123",
        )

    def test_extract_visible_messages_ignores_tool_items(self):
        thread = {
            "turns": [
                {
                    "items": [
                        {"type": "userMessage", "content": [{"type": "text", "text": "hello"}]},
                        {"type": "functionCallOutput", "output": {"content": "secret noise"}},
                        {"type": "agentMessage", "text": "goodbye"},
                    ]
                }
            ]
        }
        self.assertEqual(
            tracker.extract_visible_messages(thread),
            [
                {"role": "user", "text": "hello"},
                {"role": "assistant", "text": "goodbye"},
            ],
        )

    def test_resume_parser_does_not_require_limit(self):
        args = tracker.build_parser().parse_args(["resume", "abc-123"])
        self.assertFalse(hasattr(args, "limit"))


if __name__ == "__main__":
    unittest.main()
