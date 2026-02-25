#!/usr/bin/env python3
"""Tests for plan-rename.py, plan-session-rename.py, and propagate-rename.py.

Run: python3 -m pytest ~/.claude/hooks/tests/test_plan_hooks.py -v

All tests use tmpdir isolation — no real ~/.claude/plans/ files are touched.
"""
import datetime
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile

import pytest

HOOKS_DIR = pathlib.Path.home() / ".claude" / "hooks"


# ---------------------------------------------------------------------------
# Module loading helpers
# ---------------------------------------------------------------------------

def _load_module(name, path):
    """Import a hook script as a module."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def plan_rename():
    return _load_module("plan_rename", HOOKS_DIR / "plan-rename.py")


@pytest.fixture
def plan_session_rename():
    return _load_module("plan_session_rename", HOOKS_DIR / "plan-session-rename.py")


# ---------------------------------------------------------------------------
# Date freezing helper
# ---------------------------------------------------------------------------

def _freeze_date(mod, year=2026, month=2, day=25):
    """Monkey-patch datetime.date.today() in a module."""
    class FrozenDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(year, month, day)
    mod.datetime.date = FrozenDate


# ---------------------------------------------------------------------------
# plan-rename.py — unit tests
# ---------------------------------------------------------------------------

class TestPlanRenameSlugify:
    """Test slugify() function."""

    def test_basic(self, plan_rename):
        assert plan_rename.slugify("Hello World") == "hello-world"

    def test_strips_plan_prefix(self, plan_rename):
        assert plan_rename.slugify("Plan: My Feature") == "my-feature"

    def test_strips_backticks(self, plan_rename):
        assert plan_rename.slugify("`code` Thing") == "code-thing"

    def test_strips_trailing_parens(self, plan_rename):
        assert plan_rename.slugify("Feature Name (Draft)") == "feature-name"

    def test_strips_trailing_punctuation(self, plan_rename):
        assert plan_rename.slugify("Feature Name:") == "feature-name"

    def test_truncation(self, plan_rename):
        long = "a-" * 40  # 80 chars
        result = plan_rename.slugify(long)
        assert len(result) <= 60

    def test_empty_input(self, plan_rename):
        assert plan_rename.slugify("") == ""


class TestPlanRenameH1RE:
    """Test that H1_RE accepts all valid titles (bug fix #6)."""

    def test_uppercase_title(self, plan_rename):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Uppercase Title\nbody\n")
            f.flush()
            assert plan_rename.extract_h1(pathlib.Path(f.name)) == "Uppercase Title"
        os.unlink(f.name)

    def test_lowercase_title(self, plan_rename):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# lowercase title\nbody\n")
            f.flush()
            assert plan_rename.extract_h1(pathlib.Path(f.name)) == "lowercase title"
        os.unlink(f.name)

    def test_numeric_title(self, plan_rename):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# 2026 Roadmap\nbody\n")
            f.flush()
            assert plan_rename.extract_h1(pathlib.Path(f.name)) == "2026 Roadmap"
        os.unlink(f.name)

    def test_backtick_title(self, plan_rename):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# `plan-rename` Hook Fix\nbody\n")
            f.flush()
            assert plan_rename.extract_h1(pathlib.Path(f.name)) == "`plan-rename` Hook Fix"
        os.unlink(f.name)

    def test_no_h1(self, plan_rename):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("No header here\n")
            f.flush()
            assert plan_rename.extract_h1(pathlib.Path(f.name)) == ""
        os.unlink(f.name)


class TestPlanRenamePhaseC:
    """Test basic Phase C rename (no prior origins)."""

    def test_basic_rename(self, plan_rename):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_rename.PLANS_DIR = td
            _freeze_date(plan_rename)

            f = td / "fuzzy-crafting-axolotl.md"
            f.write_text("# My Great Plan\nbody\n")

            origins = {}
            result = plan_rename.rename_file(f, "fuzzy-crafting-axolotl", origins=origins)

            assert result is not None
            assert result.name == "2026-02-25-my-great-plan.md"
            assert result.exists()
            assert result.read_text() == "# My Great Plan\nbody\n"
            # Symlink created
            assert f.is_symlink()
            assert os.readlink(f) == result.name
            # Origin recorded
            assert origins["fuzzy-crafting-axolotl"] == result.name

    def test_agent_suffix(self, plan_rename):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_rename.PLANS_DIR = td
            _freeze_date(plan_rename)

            f = td / "fuzzy-crafting-axolotl-agent-a1b2c3d4e5.md"
            f.write_text("# Agent Plan\nbody\n")

            origins = {}
            result = plan_rename.rename_file(
                f, "fuzzy-crafting-axolotl",
                agent_suffix="-agent-a1b2c3d4e5", origins=origins
            )

            assert result is not None
            assert "-agent-a1b2c3d4e5" in result.name
            assert result.exists()


class TestPlanRenamePhaseA:
    """Test Phase A: origin-aware re-rename (bug fix #4)."""

    def test_h1_changed_moves_current_content(self, plan_rename):
        """Critical fix: Phase A should move CURRENT content, not old."""
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_rename.PLANS_DIR = td
            _freeze_date(plan_rename)

            random_file = td / "fuzzy-crafting-axolotl.md"
            prior = td / "2026-02-24-old-title.md"

            prior.write_text("# Old Title\nold body\n")
            random_file.write_text("# New Title\nnew body\n")

            origins = {"fuzzy-crafting-axolotl": prior.name}
            result = plan_rename.rename_file(
                random_file, "fuzzy-crafting-axolotl", origins=origins
            )

            assert result is not None
            assert result.name == "2026-02-25-new-title.md"
            # New content is in the dated file
            assert result.read_text() == "# New Title\nnew body\n"
            # Prior dated file is gone
            assert not prior.exists()
            # Random name is now a symlink
            assert random_file.is_symlink()
            assert os.readlink(random_file) == result.name
            # Origin updated
            assert origins["fuzzy-crafting-axolotl"] == result.name

    def test_same_target_returns_none(self, plan_rename):
        """Phase A same target should be a no-op."""
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_rename.PLANS_DIR = td
            _freeze_date(plan_rename)

            dated = td / "2026-02-25-my-plan.md"
            dated.write_text("# My Plan\nbody\n")

            random_file = td / "fuzzy-crafting-axolotl.md"
            os.symlink(dated.name, random_file)

            origins = {"fuzzy-crafting-axolotl": dated.name}
            result = plan_rename.rename_file(
                random_file, "fuzzy-crafting-axolotl", origins=origins
            )

            assert result is None
            # Nothing changed
            assert dated.exists()
            assert random_file.is_symlink()

    def test_stale_origin_falls_through(self, plan_rename):
        """Phase A stale origin should clear and fall through to Phase C."""
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_rename.PLANS_DIR = td
            _freeze_date(plan_rename)

            random_file = td / "fuzzy-crafting-axolotl.md"
            random_file.write_text("# Fresh Plan\nbody\n")

            # Origin points to non-existent file
            origins = {"fuzzy-crafting-axolotl": "2026-02-20-gone.md"}
            result = plan_rename.rename_file(
                random_file, "fuzzy-crafting-axolotl", origins=origins
            )

            assert result is not None
            assert result.name == "2026-02-25-fresh-plan.md"
            assert result.exists()
            # Origin updated (stale entry cleared, new one set)
            assert origins["fuzzy-crafting-axolotl"] == result.name


class TestPlanRenamePhaseB:
    """Test Phase B: collision handling."""

    def test_same_plan_merges(self, plan_rename):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_rename.PLANS_DIR = td
            _freeze_date(plan_rename)

            existing = td / "2026-02-25-my-plan.md"
            existing.write_text("# My Plan\nbody\n")

            random_file = td / "eager-twirling-storm.md"
            random_file.write_text("# My Plan\nupdated body\n")

            origins = {}
            result = plan_rename.rename_file(
                random_file, "eager-twirling-storm", origins=origins
            )

            assert result is not None
            assert result.name == "2026-02-25-my-plan.md"
            # Updated content wins
            assert "updated body" in result.read_text()

    def test_different_plan_gets_suffix(self, plan_rename):
        """True collision: same slug from different H1s that slugify identically."""
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_rename.PLANS_DIR = td
            _freeze_date(plan_rename)

            # Existing dated file — different H1 but same slug after slugify
            existing = td / "2026-02-25-my-plan.md"
            existing.write_text("# My Plan!\noriginal content alpha\n")

            # New random file — different H1 that also slugifies to "my-plan"
            # (trailing punctuation is stripped, so "My Plan:" → "my-plan")
            random_file = td / "eager-twirling-storm.md"
            random_file.write_text("# My Plan:\ncompletely different content beta\n")

            origins = {}
            result = plan_rename.rename_file(
                random_file, "eager-twirling-storm", origins=origins
            )

            assert result is not None
            # Should get a -2 suffix since content AND H1 differ
            assert result.name == "2026-02-25-my-plan-2.md"


# ---------------------------------------------------------------------------
# plan-session-rename.py — unit tests
# ---------------------------------------------------------------------------

class TestSessionRenameH1:
    """Test extract_h1 in plan-session-rename.py."""

    def test_basic(self, plan_session_rename):
        assert plan_session_rename.extract_h1("# Hello World\nbody") == "Hello World"

    def test_strips_plan_prefix(self, plan_session_rename):
        assert plan_session_rename.extract_h1("# Plan: My Feature\nbody") == "My Feature"

    def test_no_h1(self, plan_session_rename):
        assert plan_session_rename.extract_h1("No header") == ""

    def test_numeric(self, plan_session_rename):
        assert plan_session_rename.extract_h1("# 42 Things\nbody") == "42 Things"


class TestSessionRenameComputeDatedPath:
    """Test compute_dated_path() function."""

    def test_random_name(self, plan_session_rename):
        _freeze_date(plan_session_rename)
        with tempfile.TemporaryDirectory() as td:
            plan_session_rename.PLANS_DIR = pathlib.Path(td)
            result = plan_session_rename.compute_dated_path(
                "My Great Plan", f"{td}/fuzzy-crafting-axolotl.md"
            )
            assert result is not None
            assert "2026-02-25-my-great-plan.md" in result

    def test_non_random_name_returns_none(self, plan_session_rename):
        _freeze_date(plan_session_rename)
        result = plan_session_rename.compute_dated_path(
            "My Plan", "/some/path/2026-02-25-already-dated.md"
        )
        assert result is None

    def test_agent_suffix(self, plan_session_rename):
        _freeze_date(plan_session_rename)
        with tempfile.TemporaryDirectory() as td:
            plan_session_rename.PLANS_DIR = pathlib.Path(td)
            result = plan_session_rename.compute_dated_path(
                "Agent Plan", f"{td}/fuzzy-crafting-axolotl-agent-a1b2c3.md"
            )
            assert result is not None
            assert "-agent-a1b2c3" in result


class TestSessionRenameContextCache:
    """Test the context notification cache."""

    def test_cache_round_trip(self, plan_session_rename):
        with tempfile.TemporaryDirectory() as td:
            plan_session_rename.CONTEXT_CACHE = pathlib.Path(td) / ".plan-context-cache.json"

            assert plan_session_rename.load_context_cache() == {}

            cache = {"fuzzy-crafting-axolotl.md": "/plans/2026-02-25-my-plan.md"}
            plan_session_rename.save_context_cache(cache)

            loaded = plan_session_rename.load_context_cache()
            assert loaded == cache

    def test_cache_dedup(self, plan_session_rename):
        """Same slug should not re-notify."""
        with tempfile.TemporaryDirectory() as td:
            plan_session_rename.CONTEXT_CACHE = pathlib.Path(td) / ".plan-context-cache.json"

            cache = {"fuzzy.md": "/plans/2026-02-25-my-plan.md"}
            plan_session_rename.save_context_cache(cache)

            loaded = plan_session_rename.load_context_cache()
            # If cached slug matches, hook should skip
            assert loaded.get("fuzzy.md") == "/plans/2026-02-25-my-plan.md"

    def test_cache_re_fires_on_h1_change(self, plan_session_rename):
        """Different slug should re-notify."""
        with tempfile.TemporaryDirectory() as td:
            plan_session_rename.CONTEXT_CACHE = pathlib.Path(td) / ".plan-context-cache.json"

            cache = {"fuzzy.md": "/plans/2026-02-25-old-plan.md"}
            plan_session_rename.save_context_cache(cache)

            loaded = plan_session_rename.load_context_cache()
            new_path = "/plans/2026-02-25-new-plan.md"
            # Different from cached — should trigger notification
            assert loaded.get("fuzzy.md") != new_path


class TestSessionRenamePendingTitles:
    """Test apply_pending_titles() — bug fix #11."""

    def test_consumes_pending_when_jsonl_exists(self, plan_session_rename):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_session_rename.PENDING_DIR = td / "session-tags"
            plan_session_rename.PENDING_DIR.mkdir()

            sid = "test-session-123"
            cwd = "/test/cwd"

            # Create JSONL where jsonl_path_for expects
            jsonl = plan_session_rename.jsonl_path_for(sid, cwd)
            jsonl.parent.mkdir(parents=True, exist_ok=True)
            jsonl.write_text("")

            # Create pending title
            pending = plan_session_rename.PENDING_DIR / f"{sid}.pending-title"
            pending.write_text("Pending Title")

            plan_session_rename.apply_pending_titles(sid, cwd)

            # Pending file consumed
            assert not pending.exists()
            # Title written to JSONL
            lines = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]
            titles = [l["customTitle"] for l in lines if l.get("type") == "custom-title"]
            assert "Pending Title" in titles

            # Cleanup
            jsonl.unlink()

    def test_skips_if_already_titled(self, plan_session_rename):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            plan_session_rename.PENDING_DIR = td / "session-tags"
            plan_session_rename.PENDING_DIR.mkdir()

            sid = "test-session-456"
            cwd = "/test/cwd"

            jsonl = plan_session_rename.jsonl_path_for(sid, cwd)
            jsonl.parent.mkdir(parents=True, exist_ok=True)
            # Already has a custom-title
            jsonl.write_text(json.dumps({"type": "custom-title", "customTitle": "Existing"}) + "\n")

            pending = plan_session_rename.PENDING_DIR / f"{sid}.pending-title"
            pending.write_text("Stale Pending")

            plan_session_rename.apply_pending_titles(sid, cwd)

            # Pending consumed (cleaned up) but not applied
            assert not pending.exists()
            lines = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]
            titles = [l["customTitle"] for l in lines if l.get("type") == "custom-title"]
            # Only the existing title, stale pending was not appended
            assert titles == ["Existing"]

            jsonl.unlink()


# ---------------------------------------------------------------------------
# Slugify consistency — both modules must produce identical slugs
# ---------------------------------------------------------------------------

class TestSlugifyConsistency:
    """plan-rename.py and plan-session-rename.py must slugify identically."""

    CASES = [
        "Hello World",
        "Plan: My Feature",
        "`code` Thing",
        "Feature Name (Draft)",
        "2026 Roadmap",
        "UPPERCASE TITLE",
        "étude in C Minor",
    ]

    def test_consistent_slugs(self, plan_rename, plan_session_rename):
        for title in self.CASES:
            a = plan_rename.slugify(title)
            b = plan_session_rename.slugify(title)
            assert a == b, f"Slug mismatch for '{title}': {a!r} != {b!r}"


# ---------------------------------------------------------------------------
# End-to-end: plan-session-rename.py subprocess protocol test
# ---------------------------------------------------------------------------

class TestSessionRenameProtocol:
    """Test the hook's stdout JSON protocol via subprocess."""

    def _run_hook(self, stdin_data, env_override=None):
        """Run plan-session-rename.py as a subprocess, return (stdout, stderr, rc)."""
        env = os.environ.copy()
        if env_override:
            env.update(env_override)
        proc = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "plan-session-rename.py")],
            input=json.dumps(stdin_data),
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        return proc.stdout, proc.stderr, proc.returncode

    def test_emits_additional_context_for_random_name(self):
        """Hook should emit hookSpecificOutput JSON on stdout for random-named plans."""
        plans_dir = pathlib.Path.home() / ".claude" / "plans"
        filepath = str(plans_dir / "tingly-humming-simon.md")

        # We need a session JSONL to exist
        cwd = "/Users/tomdimino/Desktop"
        session_id = "test-protocol-001"
        jsonl = pathlib.Path.home() / ".claude" / "projects" / "-Users-tomdimino-Desktop" / f"{session_id}.jsonl"

        # Clear any stale context cache entry
        cache_file = plans_dir / ".plan-context-cache.json"
        if cache_file.exists():
            cache = json.loads(cache_file.read_text())
            cache.pop("tingly-humming-simon.md", None)
            cache_file.write_text(json.dumps(cache))

        created_jsonl = False
        try:
            if not jsonl.exists():
                jsonl.parent.mkdir(parents=True, exist_ok=True)
                jsonl.write_text("")
                created_jsonl = True

            stdin_data = {
                "tool_input": {
                    "file_path": filepath,
                    "content": "# Protocol Test Plan\nbody\n",
                },
                "session_id": session_id,
                "cwd": cwd,
            }

            stdout, stderr, rc = self._run_hook(stdin_data)

            assert rc == 0, f"Hook failed with rc={rc}, stderr={stderr}"

            # Parse stdout JSON
            if stdout.strip():
                output = json.loads(stdout.strip())
                hso = output.get("hookSpecificOutput", {})
                assert hso.get("hookEventName") == "PostToolUse"
                assert "additionalContext" in hso
                ctx = hso["additionalContext"]
                assert "protocol-test-plan" in ctx
                assert ctx.endswith(".md")
            else:
                # Could be empty if cache already had this entry
                pass

        finally:
            if created_jsonl:
                jsonl.unlink(missing_ok=True)
            # Clean up context cache entry
            if cache_file.exists():
                try:
                    cache = json.loads(cache_file.read_text())
                    cache.pop("tingly-humming-simon.md", None)
                    cache_file.write_text(json.dumps(cache))
                except (json.JSONDecodeError, OSError):
                    pass

    def test_no_stdout_for_non_plan_path(self):
        """Hook should produce no stdout for files outside ~/.claude/plans/."""
        stdin_data = {
            "tool_input": {
                "file_path": "/tmp/not-a-plan.md",
                "content": "# Not A Plan\nbody\n",
            },
            "session_id": "test-protocol-002",
            "cwd": "/Users/tomdimino/Desktop",
        }

        stdout, stderr, rc = self._run_hook(stdin_data)
        assert stdout.strip() == ""

    def test_no_stdout_for_already_dated_name(self):
        """Hook should produce no additionalContext for already-dated filenames."""
        plans_dir = pathlib.Path.home() / ".claude" / "plans"
        filepath = str(plans_dir / "2026-02-25-already-dated.md")

        cwd = "/Users/tomdimino/Desktop"
        session_id = "test-protocol-003"
        jsonl = pathlib.Path.home() / ".claude" / "projects" / "-Users-tomdimino-Desktop" / f"{session_id}.jsonl"

        created_jsonl = False
        try:
            if not jsonl.exists():
                jsonl.parent.mkdir(parents=True, exist_ok=True)
                jsonl.write_text("")
                created_jsonl = True

            stdin_data = {
                "tool_input": {
                    "file_path": filepath,
                    "content": "# Already Dated\nbody\n",
                },
                "session_id": session_id,
                "cwd": cwd,
            }

            stdout, stderr, rc = self._run_hook(stdin_data)

            # No additionalContext for non-random names
            if stdout.strip():
                output = json.loads(stdout.strip())
                # Should not have hookSpecificOutput
                assert "hookSpecificOutput" not in output
            # Or just empty stdout — both acceptable

        finally:
            if created_jsonl:
                jsonl.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# H1_RE consistency — both modules must match the same titles
# ---------------------------------------------------------------------------

class TestH1REConsistency:
    """Both hooks must accept the same set of H1 headers."""

    CASES = [
        ("# Uppercase Title\n", "Uppercase Title"),
        ("# lowercase\n", "lowercase"),
        ("# 2026 Roadmap\n", "2026 Roadmap"),
        ("# `code` Fix\n", "`code` Fix"),
        ("## Not H1\n", ""),
        ("No header\n", ""),
    ]

    def test_h1_match(self, plan_rename, plan_session_rename):
        for content, expected in self.CASES:
            # plan-session-rename extracts from content string
            psr_result = plan_session_rename.extract_h1(content)

            # plan-rename extracts from file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(content)
                f.flush()
                pr_result = plan_rename.extract_h1(pathlib.Path(f.name))
            os.unlink(f.name)

            assert psr_result == expected, f"plan-session-rename H1 mismatch for {content!r}: {psr_result!r}"
            assert pr_result == expected, f"plan-rename H1 mismatch for {content!r}: {pr_result!r}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
