"""Tests for geniza: the slim archive of Claude Code transcripts (plan 2026-11-21-001).

Every test builds a synthetic projects folder in a temp dir; none reads or writes ~/.claude.
Run: uv run --python 3.14 python -I -m unittest discover -s ~/.claude/scripts/geniza/tests -v
GENIZA_MODULE=<path> runs the suite against another copy of geniza.py (used by the mutant check).
"""
import ast
import base64
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tracemalloc
import unittest
from unittest import mock

MODULE = pathlib.Path(os.environ.get("GENIZA_MODULE", pathlib.Path(__file__).resolve().parent.parent / "geniza.py"))
_spec = importlib.util.spec_from_file_location("geniza", MODULE)
geniza = importlib.util.module_from_spec(_spec)
sys.modules["geniza"] = geniza
_spec.loader.exec_module(geniza)

SID = "11111111-2222-4333-8444-555555555555"
SID2 = "66666666-7777-4888-9999-aaaaaaaaaaaa"
PNG = base64.b64encode(b"\x89PNG" + os.urandom(6000)).decode()
DAY = 86400


def rec_user(text, **kw):
    return {"type": "user", "sessionId": SID, "cwd": "/w", "timestamp": "2026-08-01T00:00:00Z",
            "message": {"role": "user", "content": [{"type": "text", "text": text}]}, **kw}


def rec_assistant(text, tool_input=None):
    content = [{"type": "thinking", "thinking": "pondering " + text, "signature": "S" * 500},
               {"type": "text", "text": text}]
    if tool_input is not None:
        content.append({"type": "tool_use", "id": "tu1", "name": "Bash", "input": tool_input})
    return {"type": "assistant", "sessionId": SID, "timestamp": "2026-08-01T00:00:01Z",
            "message": {"id": "m1", "role": "assistant", "model": "claude-opus-5-5", "content": content,
                        "usage": {"input_tokens": 10, "output_tokens": 20, "cache_read_input_tokens": 5}}}


def rec_tool_result(text, with_image=False):
    inner = [{"type": "text", "text": text}]
    if with_image:
        inner.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": PNG}})
    return {"type": "user", "sessionId": SID, "timestamp": "2026-08-01T00:00:02Z",
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu1", "content": inner}]},
            "toolUseResult": {"stdout": text, "file": {"base64": PNG}}}


def jsonl(records):
    return "".join(json.dumps(r) + "\n" for r in records)


class GenizaCase(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="geniza-test-"))
        self.projects = self.tmp / "projects"
        self.proj = self.projects / "-w"
        self.proj.mkdir(parents=True)
        self.root = self.tmp / "geniza"
        self.settings = self.tmp / "settings.json"
        self.settings.write_text(json.dumps({"cleanupPeriodDays": 99999}))
        self.managed = self.tmp / "managed-settings.json"
        self.managed.write_text(json.dumps({"cleanupPeriodDays": 99999}))
        self.now = time.time() + 2 * 3600  # every planted file is quiet
        self.cfg = self.make_cfg()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_cfg(self, **kw):
        args = dict(root=self.root, projects=self.projects, now=self.now, settings_path=self.settings,
                    managed_path=self.managed, free_floor_bytes=0, lock_timeout=2.0,
                    sessions_dir=self.tmp / "sessions")
        args.update(kw)
        return geniza.Config(**args)

    def write_session(self, sid=SID, records=None, subagent=True):
        main = self.proj / f"{sid}.jsonl"
        main.write_text(jsonl(records if records is not None else
                              [rec_user("hello geniza"), rec_assistant("answer one", {"command": "ls"}),
                               rec_tool_result("out " * 10)]))
        if subagent:
            sub = self.proj / sid / "subagents"
            sub.mkdir(parents=True, exist_ok=True)
            (sub / "agent-x.jsonl").write_text(jsonl([rec_user("sub task", isSidechain=True)]))
        return main

    def slim_lines(self, sid=SID, gen=1):
        path = self.root / "slim" / "-w" / f"{sid}.g{gen}.jsonl.zst"
        return list(geniza.read_slim(path))


class TestSweep(GenizaCase):
    def test_sweep_archives_session_with_header_manifest(self):
        main = self.write_session()
        r = geniza.sweep(self.cfg)
        self.assertEqual(r["archived"], 1)
        lines = self.slim_lines()
        head = lines[0]
        self.assertEqual(head["type"], "geniza-header")
        paths = {m["path"]: m for m in head["members"]}
        self.assertEqual(set(paths), {f"{SID}.jsonl", f"{SID}/subagents/agent-x.jsonl"})
        self.assertEqual(paths[f"{SID}.jsonl"]["sha256"], hashlib.sha256(main.read_bytes()).hexdigest())
        self.assertEqual(lines[-1]["type"], "geniza-end")
        row = geniza.current_row(self.cfg, "-w", SID)
        self.assertIsNotNone(row["verified_at"])

    def test_unchanged_session_is_not_rewritten(self):
        self.write_session()
        geniza.sweep(self.cfg)
        slim = self.root / "slim" / "-w" / f"{SID}.g1.jsonl.zst"
        before = slim.stat().st_mtime_ns
        with mock.patch.object(geniza, "clone", wraps=geniza.clone) as cl:
            r = geniza.sweep(self.cfg)
        cl.assert_not_called()  # an unchanged manifest is settled by stat alone
        self.assertEqual(r["archived"], 0)
        self.assertEqual(r["unchanged"], 1)
        self.assertEqual(slim.stat().st_mtime_ns, before)

    def test_touched_but_identical_session_is_not_rewritten(self):
        main = self.write_session()
        geniza.sweep(self.cfg)
        slim = self.root / "slim" / "-w" / f"{SID}.g1.jsonl.zst"
        before = slim.stat().st_mtime_ns
        later = time.time() + 60
        os.utime(main, (later, later))
        r = geniza.sweep(self.make_cfg(now=later + 3600))
        self.assertEqual(r["unchanged"], 1)
        self.assertEqual(slim.stat().st_mtime_ns, before)

    def test_growth_replaces_the_same_generation(self):
        main = self.write_session()
        geniza.sweep(self.cfg)
        n1 = len(self.slim_lines())
        with main.open("a") as f:
            f.write(json.dumps(rec_user("a later turn")) + "\n")
        r = geniza.sweep(self.cfg)
        self.assertEqual(r["grown"], 1)
        self.assertEqual(len(self.slim_lines()), n1 + 1)
        self.assertFalse((self.root / "slim" / "-w" / f"{SID}.g2.jsonl.zst").exists())

    def test_vanished_member_forks_a_generation_and_keeps_the_old(self):
        main = self.write_session()
        geniza.sweep(self.cfg)
        main.unlink()  # a sweep bug takes the transcript and leaves the folder
        r = geniza.sweep(self.cfg)
        self.assertEqual(r["forked"], 1)
        old = self.slim_lines(gen=1)
        self.assertTrue(any(l.get("type") == "user" and "hello geniza" in json.dumps(l) for l in old))
        self.assertTrue((self.root / "slim" / "-w" / f"{SID}.g2.jsonl.zst").exists())
        self.assertIn("fork", (self.root / "alerts.log").read_text())

    def test_rewrite_in_place_forks(self):
        main = self.write_session()
        geniza.sweep(self.cfg)
        data = main.read_bytes()
        main.write_bytes(data.replace(b"hello geniza", b"HELLO GENIZA"))  # same length, different bytes
        r = geniza.sweep(self.cfg)
        self.assertEqual(r["forked"], 1)

    def test_folder_without_transcript_is_a_session_and_non_sessions_are_ignored(self):
        sub = self.proj / SID2 / "subagents"
        sub.mkdir(parents=True)
        (sub / "agent-y.jsonl").write_text(jsonl([rec_user("orphan sub")]))
        (self.proj / "memory").mkdir()
        (self.proj / "memory" / "MEMORY.md").write_text("# m")
        (self.proj / "memory.bak-2026-11-20").mkdir()
        (self.proj / "sessions-index.json").write_text("{}")
        found = geniza.enumerate_sessions(self.projects)
        self.assertEqual(set(found), {("-w", SID2)})
        geniza.sweep(self.cfg)
        self.assertEqual(len(self.slim_lines(SID2)) > 2, True)

    def test_sibling_copies_are_members(self):
        self.write_session(subagent=False)
        (self.proj / f"{SID}.jsonl.bak-1").write_text(jsonl([rec_user("bak copy")]))
        geniza.sweep(self.cfg)
        paths = {m["path"] for m in self.slim_lines()[0]["members"]}
        self.assertIn(f"{SID}.jsonl.bak-1", paths)

    def test_quiet_window_defers_a_session_still_being_written(self):
        self.write_session()
        r = geniza.sweep(self.make_cfg(now=time.time()))
        self.assertEqual(r["archived"], 0)
        self.assertEqual(r["pending"], 1)
        r = geniza.sweep(self.cfg)
        self.assertEqual(r["archived"], 1)

    def test_partial_trailing_line_is_skipped_then_caught(self):
        main = self.write_session(subagent=False)
        with main.open("a") as f:
            f.write('{"type": "user", "message": {"content": "half')
        geniza.sweep(self.cfg)
        first = self.slim_lines()
        users = [l for l in first if l.get("type") == "user"]
        self.assertGreater(first[-1]["dropped"].get("partial_tail_bytes", 0), 0)
        self.assertNotIn("geniza-unparsed", [l.get("type") for l in first])
        with main.open("a") as f:
            f.write(' a line"}}\n')
        r = geniza.sweep(self.cfg)
        self.assertEqual(r["grown"], 1)
        users2 = [l for l in self.slim_lines() if l.get("type") == "user"]
        self.assertEqual(len(users2), len(users) + 1)


class TestSlimForm(GenizaCase):
    def test_slim_cuts_payloads_and_keeps_the_conversation(self):
        long_out = "x" * 20000
        self.write_session(records=[
            rec_user("the question"),
            rec_assistant("the answer", {"command": "cat big", "content": "y" * 30000}),
            rec_tool_result(long_out, with_image=True),
            {"type": "file-history-snapshot", "snapshot": {"trackedFileBackups": {"a": "b" * 5000}}},
            {"type": "attachment", "attachment": {"content": "z" * 5000}},
            {"type": "custom-title", "customTitle": "My Title", "sessionId": SID},
        ], subagent=False)
        geniza.sweep(self.cfg)
        lines = self.slim_lines()
        blob = json.dumps(lines)
        self.assertNotIn(PNG[:200], blob)                       # image bytes gone
        self.assertIn(hashlib.sha256(PNG.encode()).hexdigest(), blob)  # its reference kept
        self.assertIn("the question", blob)
        self.assertIn("the answer", blob)
        self.assertIn("pondering the answer", blob)              # thinking kept
        self.assertNotIn("S" * 500, blob)                         # thinking signature dropped
        self.assertNotIn("toolUseResult", blob)
        self.assertNotIn("file-history-snapshot", [l.get("type") for l in lines])
        self.assertNotIn("attachment", [l.get("type") for l in lines])
        self.assertIn("My Title", blob)
        assistant = next(l for l in lines if l.get("type") == "assistant")
        self.assertEqual(assistant["message"]["usage"]["output_tokens"], 20)
        tr = next(l for l in lines if l.get("type") == "user" and "tool_result" in json.dumps(l))
        text = tr["message"]["content"][0]["content"][0]["text"]
        self.assertLess(len(text), 6000)
        self.assertIn("20000 bytes", text)
        tool_in = assistant["message"]["content"][2]["input"]["content"]
        self.assertLess(len(tool_in), 6000)
        foot = lines[-1]
        self.assertEqual(foot["dropped"].get("file-history-snapshot"), 1)
        self.assertEqual(foot["dropped"].get("attachment"), 1)

    def test_lone_surrogate_is_kept_exactly_and_read_shows_a_replacement(self):
        # Claude Code (JavaScript) truncates strings by UTF-16 unit and writes the half character as a JSON escape.
        half = "math 𝕏 cut here \ud835 and on"
        self.write_session(records=[rec_user(half), rec_assistant("answer \udc00 too")], subagent=False)
        self.assertIn("\\ud835", (self.proj / f"{SID}.jsonl").read_text())
        r = geniza.sweep(self.cfg)
        self.assertEqual((r["archived"], r["errors"]), (1, 0))
        user = next(l for l in self.slim_lines() if l.get("type") == "user")
        self.assertEqual(user["message"]["content"][0]["text"], half)
        slim = self.root / "slim" / "-w" / f"{SID}.g1.jsonl.zst"
        with geniza.zstd.open(slim, "rb") as f:
            f.read().decode("utf-8")  # strict UTF-8 for every reader (Node, jq), not only Python's surrogatepass
        out = geniza.render(self.cfg, SID[:8])
        self.assertIn("cut here \N{REPLACEMENT CHARACTER} and on", out)
        self.assertIn("answer \N{REPLACEMENT CHARACTER} too", out)
        out.encode("utf-8")  # printable: no lone surrogate survives into the Markdown


class TestSafety(GenizaCase):
    def test_crash_before_rename_leaves_no_row_and_the_next_sweep_succeeds(self):
        self.write_session()
        real_replace = os.replace
        with mock.patch.object(geniza.os, "replace", side_effect=OSError("simulated crash")):
            r = geniza.sweep(self.cfg)
        self.assertEqual(r["errors"], 1)
        self.assertIsNone(geniza.current_row(self.cfg, "-w", SID))
        self.assertFalse((self.root / "slim" / "-w" / f"{SID}.g1.jsonl.zst").exists())
        self.assertEqual([p for p in (self.root / "slim" / "-w").iterdir() if ".tmp" in p.name], [])
        self.assertIs(os.replace, real_replace)
        r = geniza.sweep(self.cfg)
        self.assertEqual(r["archived"], 1)
        leftovers = [p for p in (self.root / "slim" / "-w").iterdir() if ".tmp" in p.name]
        self.assertEqual(leftovers, [])

    def test_lock_blocks_a_second_writer_and_frees_when_the_holder_dies(self):
        self.write_session()
        self.root.mkdir(parents=True, exist_ok=True)
        holder = subprocess.Popen([sys.executable, "-I", "-c",
                                   "import fcntl,sys,time; f=open(sys.argv[1],'a'); fcntl.flock(f, fcntl.LOCK_EX); "
                                   "print('held', flush=True); time.sleep(60)", str(self.root / "geniza.lock")],
                                  stdout=subprocess.PIPE, text=True)
        self.assertEqual(holder.stdout.readline().strip(), "held")
        try:
            with self.assertRaises(geniza.Locked):
                geniza.sweep(self.make_cfg(lock_timeout=0.5))
        finally:
            holder.send_signal(signal.SIGKILL)
            holder.wait()
            holder.stdout.close()
        self.assertEqual(geniza.sweep(self.cfg)["archived"], 1)

    def test_read_back_rejects_a_write_whose_count_is_wrong(self):
        self.write_session()
        real = geniza.write_slim
        with mock.patch.object(geniza, "write_slim", side_effect=lambda *a, **k: real(*a, **k) + 1):
            r = geniza.sweep(self.cfg)
        self.assertEqual(r["errors"], 1)
        self.assertIsNone(geniza.current_row(self.cfg, "-w", SID))
        self.assertFalse((self.root / "slim" / "-w" / f"{SID}.g1.jsonl.zst").exists())

    def test_free_space_floor_refuses_and_alerts(self):
        self.write_session()
        cfg = self.make_cfg(free_floor_bytes=10 ** 18)
        r = geniza.sweep(cfg)
        self.assertEqual(r["archived"], 0)
        self.assertEqual(r["errors"], 1)
        self.assertIn("free space", (self.root / "alerts.log").read_text())

    def test_verify_detects_a_corrupted_slim_file(self):
        self.write_session()
        geniza.sweep(self.cfg)
        self.assertEqual(geniza.verify(self.cfg, all_=True)["failed"], 0)
        slim = self.root / "slim" / "-w" / f"{SID}.g1.jsonl.zst"
        data = bytearray(slim.read_bytes())
        data[len(data) // 2] ^= 0xFF
        slim.write_bytes(bytes(data))
        self.assertEqual(geniza.verify(self.cfg, all_=True)["failed"], 1)

    def test_cli_creates_everything_private(self):
        self.write_session()
        logs = self.tmp / "logs"
        env = {**os.environ, "GENIZA_ROOT": str(self.root), "GENIZA_PROJECTS": str(self.projects),
               "GENIZA_LOG_DIR": str(logs), "GENIZA_NOW": str(self.now), "GENIZA_FREE_FLOOR_GB": "0"}
        subprocess.run([sys.executable, "-I", str(MODULE), "sweep"], env=env, check=True, capture_output=True)
        (self.proj / f"{SID}.jsonl").write_text("not json at all, a forked rewrite\n")
        subprocess.run([sys.executable, "-I", str(MODULE), "sweep"], env=env, capture_output=True)
        made = [p for d in (self.root, logs) for p in [d, *d.rglob("*")]]
        self.assertIn(logs / "alerts.log", made)
        loose = [f"{oct(p.stat().st_mode & 0o777)} {p}" for p in made if p.stat().st_mode & 0o077]
        self.assertEqual(loose, [])

    def test_session_end_capture_returns_at_once_and_archives_that_session(self):
        # Project folders start with "-" (-Users-…), which argparse would take for an option
        main = self.write_session(subagent=False)
        other = self.write_session(sid=SID2, subagent=False)
        old = time.time() - 3600
        for f in (main, other):
            os.utime(f, (old, old))
        logs = self.tmp / "logs"
        env = {**os.environ, "GENIZA_ROOT": str(self.root), "GENIZA_PROJECTS": str(self.projects),
               "GENIZA_LOG_DIR": str(logs), "GENIZA_FREE_FLOOR_GB": "0"}
        env.pop("GENIZA_NOW", None)
        payload = json.dumps({"session_id": SID, "transcript_path": str(main), "hook_event_name": "SessionEnd"})
        t0 = time.monotonic()
        subprocess.run([sys.executable, "-I", str(MODULE), "capture", "--stdin"], input=payload, env=env,
                       text=True, check=True, timeout=10)
        self.assertLess(time.monotonic() - t0, 3)
        log = logs / "capture.log"
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and f"capture {SID}" not in (log.read_text() if log.exists() else ""):
            time.sleep(0.2)
        self.assertIn(f"capture {SID}", log.read_text())
        self.assertIsNotNone(geniza.current_row(self.cfg, "-w", SID))
        self.assertIsNone(geniza.current_row(self.cfg, "-w", SID2))

    def test_module_imports_no_network_library(self):
        tree = ast.parse(MODULE.read_text())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        self.assertFalse(names & {"socket", "urllib", "http", "ssl", "requests", "ftplib", "smtplib"})


class TestIndexAndCheck(GenizaCase):
    def test_reindex_rebuilds_an_equal_index(self):
        self.write_session()
        self.write_session(sid=SID2, subagent=False)
        geniza.sweep(self.cfg)
        before = geniza.index_rows(self.cfg)
        (self.root / "index.sqlite").unlink()
        geniza.reindex(self.cfg)
        self.assertEqual(geniza.index_rows(self.cfg), before)

    def test_check_flags_an_old_unarchived_session_until_it_is_archived(self):
        main = self.write_session(subagent=False)
        old = self.now - 80 * DAY
        os.utime(main, (old, old))
        problems = geniza.check(self.cfg)
        self.assertTrue(any(SID in p for p in problems))
        geniza.sweep(self.cfg)
        self.assertFalse(any(SID in p for p in geniza.check(self.cfg)))

    def test_check_flags_a_missing_cleanup_pin(self):
        self.managed.write_text(json.dumps({"deniedModels": ["haiku"]}))
        self.assertTrue(any("managed" in p for p in geniza.check(self.cfg)))

    def test_read_renders_the_conversation(self):
        self.write_session()
        geniza.sweep(self.cfg)
        out = geniza.render(self.cfg, SID[:8])
        self.assertIn("hello geniza", out)
        self.assertIn("answer one", out)


OLD, YOUNG, UNARCHIVED, CHANGED, LIVE = (f"{d * 8}-{d * 4}-4{d * 3}-8{d * 3}-{d * 12}" for d in "abcde")


class TestRetire(GenizaCase):
    """A session leaves projects/ only when it is past 90 days, not live, and its slim copy is current and verified;
    it goes to a dated trash folder, from which untrash brings it back, until purge-trash takes it after 14 days."""

    def plant(self, sid, days_old, archive=True):
        self.write_session(sid=sid)
        (self.proj / f"{sid}.jsonl.bak").write_text("a backup copy\n")
        then = self.now - days_old * DAY
        for f in [*self.proj.glob(f"{sid}*"), *(self.proj / sid).rglob("*")]:
            os.utime(f, (then, then))
        if archive:
            geniza.sweep(self.cfg, only={("-w", sid)})

    def setUp(self):
        super().setUp()
        self.plant(OLD, 100)
        self.plant(YOUNG, 10)
        self.plant(UNARCHIVED, 100, archive=False)
        self.plant(CHANGED, 100)
        with open(self.proj / f"{CHANGED}.jsonl", "a") as f:
            f.write(json.dumps(rec_user("a late line")) + "\n")
        then = self.now - 100 * DAY
        os.utime(self.proj / f"{CHANGED}.jsonl", (then, then))
        self.plant(LIVE, 100)
        sessions = self.tmp / "sessions"
        sessions.mkdir()
        (sessions / f"{os.getpid()}.json").write_text(json.dumps({"pid": os.getpid(), "sessionId": LIVE}))
        (self.proj / "memory").mkdir()
        (self.proj / "memory" / "MEMORY.md").write_text("notes\n")
        (self.proj / "sessions-index.json").write_text("{}")
        self.before = sorted(p.name for p in self.proj.iterdir())

    def entries(self, sid, where=None):
        return sorted(p.name for p in (where or self.proj).glob(f"{sid}*"))

    def test_dry_run_lists_eligible_and_blocked_and_moves_nothing(self):
        plan = {p["sid"]: p for p in geniza.retire_plan(self.cfg)}
        self.assertEqual(set(plan), {OLD, UNARCHIVED, CHANGED, LIVE})       # YOUNG is inside 90 days
        self.assertIsNone(plan[OLD]["blocked"])
        self.assertIn("no slim copy", plan[UNARCHIVED]["blocked"])
        self.assertIn("changed", plan[CHANGED]["blocked"])
        self.assertIn("live", plan[LIVE]["blocked"])
        self.assertGreater(plan[OLD]["bytes"], 0)
        r = geniza.retire(self.cfg)
        self.assertEqual((r["eligible"], r["blocked"], r["moved"]), (1, 3, 0))
        self.assertEqual(sorted(p.name for p in self.proj.iterdir()), self.before)

    def test_apply_moves_only_the_eligible_session_into_dated_trash(self):
        r = geniza.retire(self.cfg, apply=True)
        self.assertEqual(r["moved"], 1)
        trash = self.root / "trash" / r["day"] / "-w"
        self.assertEqual(self.entries(OLD, trash), [OLD, f"{OLD}.jsonl", f"{OLD}.jsonl.bak"])
        self.assertEqual(self.entries(OLD), [])
        for sid in (YOUNG, UNARCHIVED, CHANGED, LIVE):
            self.assertEqual(self.entries(sid), [sid, f"{sid}.jsonl", f"{sid}.jsonl.bak"])
        self.assertTrue((self.proj / "memory" / "MEMORY.md").exists())
        self.assertTrue((self.proj / "sessions-index.json").exists())
        self.assertIn("hello geniza", geniza.render(self.cfg, OLD[:8]))  # still readable from its slim copy
        after = geniza.sweep(self.cfg)
        self.assertEqual((after["forked"], after["errors"]), (0, 0))
        with geniza.db(self.cfg) as con:
            kinds = [r[0] for r in con.execute("SELECT kind FROM events WHERE sid=?", (OLD,))]
        self.assertEqual(kinds, ["retired"])

    def test_apply_rereads_the_slim_copy_and_refuses_a_bad_one(self):
        row = geniza.current_row(self.cfg, "-w", OLD)
        (self.root / row["path"]).write_bytes(b"\x28\xb5\x2f\xfd broken")
        r = geniza.retire(self.cfg, apply=True)
        self.assertEqual(r["moved"], 0)
        self.assertEqual(self.entries(OLD), [OLD, f"{OLD}.jsonl", f"{OLD}.jsonl.bak"])

    def test_untrash_brings_a_day_back_and_refuses_to_overwrite(self):
        day = geniza.retire(self.cfg, apply=True)["day"]
        (self.proj / f"{OLD}.jsonl").write_text("a new file in the way\n")
        with self.assertRaises(FileExistsError):
            geniza.untrash(self.cfg, day)
        self.assertEqual(self.entries(OLD, self.root / "trash" / day / "-w"), [OLD, f"{OLD}.jsonl", f"{OLD}.jsonl.bak"])
        (self.proj / f"{OLD}.jsonl").unlink()
        self.assertEqual(geniza.untrash(self.cfg, day), 3)
        self.assertEqual(self.entries(OLD), [OLD, f"{OLD}.jsonl", f"{OLD}.jsonl.bak"])
        self.assertEqual(geniza.sweep(self.cfg)["forked"], 0)              # back exactly as archived

    def test_purge_takes_only_trash_at_least_14_days_old(self):
        for days in (15, 14, 13):
            d = self.root / "trash" / time.strftime("%Y-%m-%d", time.localtime(self.now - days * DAY)) / "-w"
            d.mkdir(parents=True)
            (d / "x").write_text("x")
        removed = geniza.purge_trash(self.cfg)
        self.assertEqual(len(removed), 2)
        self.assertEqual(len(list((self.root / "trash").iterdir())), 1)


class TestHourly(GenizaCase):
    def test_daily_work_runs_when_due_and_not_again_within_a_day(self):
        self.write_session()
        with mock.patch.object(geniza, "verify", wraps=geniza.verify) as v:
            first = geniza.hourly(self.cfg)
            later = geniza.hourly(self.make_cfg(now=self.now + 23 * 3600))
            next_day = geniza.hourly(self.make_cfg(now=self.now + 25 * 3600))
        self.assertEqual(first["sweep"]["archived"], 1)
        self.assertEqual(v.call_count, 2)
        self.assertIn("verify", first)
        self.assertNotIn("verify", later)
        self.assertIn("verify", next_day)
        bak = self.root / "index.sqlite.bak"
        con = geniza.sqlite3.connect(bak)
        try:
            self.assertEqual(con.execute("SELECT sid FROM slim").fetchall(), [(SID,)])
        finally:
            con.close()

    def test_brief_check_reports_the_last_hourly_findings_without_walking_projects(self):
        main = self.write_session(subagent=False)
        old = self.now - 80 * DAY
        os.utime(main, (old, old))
        cfg = self.make_cfg(free_floor_bytes=10 ** 18)  # the sweep refuses, so the old session stays unarchived
        geniza.hourly(cfg)
        with mock.patch.object(geniza, "enumerate_sessions", side_effect=AssertionError("walked projects/")):
            brief = geniza.brief_problems(cfg)
        self.assertTrue(any(SID in p for p in brief))
        geniza.hourly(self.cfg)                   # archived now; the next hourly check is clean
        self.assertEqual(geniza.brief_problems(self.cfg), [])

    def test_brief_check_flags_a_missing_pin_and_a_stale_sweep(self):
        self.assertIn("no sweep has run", geniza.brief_problems(self.cfg))
        self.assertFalse((self.root / "index.sqlite").exists())    # a brief check creates nothing
        geniza.hourly(self.cfg)
        self.assertEqual(geniza.brief_problems(self.cfg), [])
        stale = geniza.brief_problems(self.make_cfg(now=self.now + 4 * 3600))
        self.assertTrue(any("sweep" in p for p in stale))
        self.managed.write_text(json.dumps({"deniedModels": ["haiku"]}))
        self.assertTrue(any("managed" in p for p in geniza.brief_problems(self.cfg)))


def traced_peak(fn):
    """fn's result and the peak of Python allocations while it ran."""
    tracemalloc.start()
    try:
        out = fn()
        return out, tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


class TestMemory(GenizaCase):
    """Claude Code writes tool output files of up to 64 MiB and sessions of 1.4 GB; geniza holds neither whole."""

    def test_text_member_streamed_equals_the_whole_read(self):
        keep = geniza.TEXT_MEMBER_HEAD + geniza.TEXT_MEMBER_TAIL + 256
        cases = {
            "small.txt": "short note ✓\n".encode(),
            "at-limit.txt": ("é" * keep).encode(),
            "past-limit.txt": ("é" * (keep + 1)).encode(),
            "straddle.txt": b"a" * (geniza.CHUNK - 1) + ("é—🜂 line\n" * 150000).encode(),  # é splits the first chunk
            "late-bad-byte.bin": b"a" * (geniza.CHUNK + 10) + b"\xff tail",
            "truncated-end.txt": ("ok " * 2000).encode() + b"\xe2\x82",
            "empty.txt": b"",
        }
        for name, data in cases.items():
            path = self.tmp / name
            path.write_bytes(data)
            rec = geniza.member_record(f"{SID}/tool-results/{name}", path, {"size": len(data), "sha256": "-"})
            try:
                text = data.decode("utf-8")
                want = {"kind": "text",
                        "text": geniza.cut(text, geniza.TEXT_MEMBER_HEAD, geniza.TEXT_MEMBER_TAIL)}
            except UnicodeDecodeError:
                want = {"kind": "binary"}
            got = {k: rec[k] for k in ("kind", "text") if k in rec}
            with self.subTest(name):
                self.assertEqual(got, want)

    def test_text_member_is_read_in_bounded_memory(self):
        big = self.tmp / "big.txt"
        block = "λόγος geniza text\n" * 45000                    # about 1 MB, multibyte
        with open(big, "w", encoding="utf-8") as f:
            for _ in range(32):
                f.write(block)
        rec, peak = traced_peak(lambda: geniza.member_record("x/big.txt", big, {"size": big.stat().st_size,
                                                                                 "sha256": "-"}))
        self.assertEqual(rec["kind"], "text")
        self.assertIn(f"{big.stat().st_size} bytes", rec["text"])
        self.assertLess(peak, 8 << 20)

    def test_read_streams_the_session(self):
        n = 4000
        records = [{"type": "user", "sessionId": SID, "timestamp": "2026-08-01T00:00:02Z",
                    "message": {"role": "user", "content": [
                        {"type": "tool_result", "tool_use_id": f"t{i}", "content": f"r{i} " + "x" * 6000}]}}
                   for i in range(n)]
        self.write_session(records=records, subagent=False)
        geniza.sweep(self.cfg)
        out, peak = traced_peak(lambda: geniza.render(self.cfg, SID[:8]))
        self.assertIn("← r0 x", out)
        self.assertIn(f"← r{n - 1} x", out)
        self.assertLess(peak, 10 << 20)


if __name__ == "__main__":
    unittest.main()
