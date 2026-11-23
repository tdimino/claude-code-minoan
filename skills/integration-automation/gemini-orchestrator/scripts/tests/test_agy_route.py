"""Tests for the Antigravity route. A stub `agy` executable replays a stream and records how it was called: no
real run is started, no quota is drawn and nothing reaches OpenRouter.

    uv run python -m unittest discover -s ~/.claude/skills/gemini-orchestrator/scripts/tests
"""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import agy_client as ac  # noqa: E402
from test_gemini_exec import Base, Stub  # noqa: E402

STUB = f"""#!{sys.executable}
import json, os, sys, time
d = os.environ["STUB_AGY_DIR"]
json.dump({{"argv": sys.argv[1:], "cwd": os.getcwd()}}, open(os.path.join(d, "call.json"), "w"))
plan = json.load(open(os.path.join(d, "plan.json")))
model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else ""
for name, text in plan.get("writes", {{}}).items():  # what a builder would have written, relative to the folder
    os.makedirs(os.path.dirname(os.path.abspath(name)), exist_ok=True)
    open(name, "w").write(text)
for line in plan["lines"]:
    sys.stdout.write(line.replace("ASKED_MODEL", model) + "\\n")
    sys.stdout.flush()
sys.stderr.write(plan.get("stderr", ""))
time.sleep(plan.get("hang", 0))
sys.exit(plan.get("exit", 0))
"""
CID = "c0ffee00-0000-4000-8000-000000000001"
USAGE = {"input_tokens": 900, "output_tokens": 40, "thinking_tokens": 12, "cache_read_tokens": 300}
DENIED_NOTE = ('jetski: no output produced — a tool required the "read_file" permission that headless mode cannot '
               "prompt for, so it was auto-denied.\n")


def ev(kind: str, **body) -> str:
    return json.dumps({"event": kind, "conversation_id": CID, kind: {"conversation_id": CID, **body}})


def tool(index: int, name: str, parameters: dict, output: str = "") -> str:
    return ev("step_update", step_index=index, state="DONE", step_type="tool", tool_name=name,
              tool_info={"name": name, "parameters": parameters, "output": output})


def text(index: int, delta: str) -> str:
    return ev("step_update", step_index=index, state="ACTIVE", step_type="agent_response", text_delta=delta)


def result(response: str, status: str = "SUCCESS", **extra) -> str:
    return ev("result", status=status, response=response, duration_seconds=3.2, usage=USAGE, **extra)


INIT = ev("init", model="ASKED_MODEL", cwd="/w", tools=["read_file", "run_command"])  # the stub fills in --model


class AgyBase(Base):
    def setUp(self):
        super().setUp()
        root = self.work.parent
        self.stub_dir = root / "stub"
        self.stub_dir.mkdir()
        stub = self.stub_dir / "agy"
        stub.write_text(STUB)
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
        self.saved = root / "agy-settings.json"
        self.saved.write_text("{}")
        self.installed = root / "installed-agents"  # never the real ~/.gemini/config/agents
        env = {"GEMINI_ORCH_AGY": str(stub), "STUB_AGY_DIR": str(self.stub_dir),
               "GEMINI_ORCH_AGY_SETTINGS": str(self.saved), "GEMINI_ORCH_AGY_AGENTS": str(self.installed),
               "GEMINI_ORCH_AGY_RULES": str(root / "no-GEMINI.md")}  # never the real ~/.gemini/GEMINI.md
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.configure()  # the shipped default route, agy
        (self.agents / "harness").mkdir(parents=True, exist_ok=True)
        (self.agents / "harness" / "default.md").write_text(
            "---\nname: orch-default\ntools:\n  - view_file\n  - run_command\nsubagent: false\n"
            "commandExecutionPolicy: sandbox\n---\nAnswer the task.\n")
        self.plan([INIT, text(1, "Hello"), text(1, " world"), result("Hello world")])

    def plan(self, lines: list[str], **extra) -> None:
        (self.stub_dir / "plan.json").write_text(json.dumps({"lines": lines, **extra}))

    def configure(self, **settings) -> None:
        self.config.write_text(json.dumps({"gate_usd": 1.0, **settings}))

    def call(self) -> dict | None:
        path = self.stub_dir / "call.json"
        return json.loads(path.read_text()) if path.exists() else None

    def settings(self) -> dict:
        argv = self.call()["argv"]
        return json.loads(argv[argv.index("--settings") + 1])

    def rules(self) -> list[str]:
        return self.settings()["permissions"]["deny"]

    def failures(self) -> list[dict]:
        path = self.data / "failures.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def output(self, err: str) -> Path:
        return Path(next(line for line in err.splitlines() if line.startswith("OUTPUT_FILE=")).split("=", 1)[1])


class RouteTests(AgyBase):
    def test_the_default_profile_runs_through_agy_and_not_openrouter(self):
        code, out, err = self.run_cli("run", "default", "Say hello.")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "Hello world")
        self.assertEqual(Stub.calls, 0)
        self.assertEqual(self.call()["cwd"], str(self.work))
        self.assertIn("plan's quota", err)

    def test_a_direct_profile_still_goes_to_openrouter_and_agy_is_not_started(self):
        code, out, _ = self.run_cli("run", "raw", "Say hello.")
        self.assertEqual((code, out.strip()), (0, "Hello world"))
        self.assertEqual(Stub.calls, 1)
        self.assertIsNone(self.call())

    def test_a_route_the_profile_lacks_is_refused(self):
        for argv in (["run", "default", "x", "--direct"], ["run", "default", "x", "--via", "openrouter"],
                     ["run", "raw", "x", "--via", "agy"]):
            code, _, err = self.run_cli(*argv)
            self.assertEqual(code, 2, argv)
            self.assertIn("route", err)
        self.assertEqual(Stub.calls, 0)
        self.assertIsNone(self.call())

    def test_a_profile_with_both_routes_takes_the_configured_default_and_obeys_the_flags(self):
        both = {"model": "neon", "effort": "medium", "routes": ["agy", "openrouter"]}
        self.configure(profiles={"raw": both})
        (self.agents / "harness" / "raw.md").write_text(
            "---\nname: orch-raw\ntools:\n  - view_file\nsubagent: false\n---\nAnswer.\n")
        self.run_cli("run", "raw", "x")
        self.assertIsNotNone(self.call())
        self.assertEqual(Stub.calls, 0)
        self.run_cli("run", "raw", "x", "--direct")
        self.assertEqual(Stub.calls, 1)
        self.configure(profiles={"raw": both}, default_route="openrouter")
        self.run_cli("run", "raw", "x")
        self.assertEqual(Stub.calls, 2)

    def test_under_a_direct_only_folder_nothing_goes_through_agy(self):
        both = {"model": "neon", "effort": "medium", "routes": ["agy", "openrouter"]}
        self.configure(direct_only_paths=[str(self.work.parent).upper()], profiles={"raw": both})
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 2)
        self.assertIn("direct_only_paths", err)
        self.assertEqual(self.run_cli("run", "raw", "x", "--via", "agy")[0], 2)
        self.assertIsNone(self.call())
        self.assertEqual(self.run_cli("run", "raw", "x")[0], 0)  # falls to the direct route without being asked
        self.assertEqual(Stub.calls, 1)

    def test_a_sibling_folder_with_a_longer_name_is_not_direct_only(self):
        self.configure(direct_only_paths=[str(self.work)[:-1]])
        self.assertEqual(self.run_cli("run", "default", "x")[0], 0)

    def test_flags_of_the_direct_route_are_refused_on_agy(self):
        code, _, err = self.run_cli("run", "default", "x", "--approved-usd", "1", "--zdr")
        self.assertEqual(code, 2)
        self.assertIn("--zdr", err)
        self.assertIn("--approved-usd", err)
        self.assertIsNone(self.call())


class CommandTests(AgyBase):
    def test_every_run_carries_the_sandbox_and_its_own_settings(self):
        self.run_cli("run", "default", "/usage")
        argv = self.call()["argv"]
        for flag in ("--sandbox", "--disable-slash-commands", "--print"):
            self.assertIn(flag, argv)
        self.assertNotIn("--dangerously-skip-permissions", argv)
        # Was assertNotIn("--agent"): without a persona agy's own web search ran (probed live 2026-11-22), so
        # `default` now runs under a two-tool persona like every other profile.
        self.assertEqual(argv[argv.index("--agent") + 1], "orch-default")
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
        self.assertEqual(argv[argv.index("--model") + 1], "gemini-4-neon-medium")
        self.assertEqual(argv[argv.index("--print-timeout") + 1], "1200s")
        s = self.settings()
        self.assertEqual((s["agentMode"], s["toolPermission"], s["enableTerminalSandbox"], s["useG1Credits"]),
                         ("", "proceed-in-sandbox", True, False))

    def test_model_effort_and_timeout_follow_the_flags(self):
        self.run_cli("run", "default", "x", "--model", "flash", "--reasoning", "low", "--timeout", "90")
        argv = self.call()["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], "gemini-3.8-flash-low")
        self.assertEqual(argv[argv.index("--print-timeout") + 1], "90s")

    def test_a_model_or_effort_agy_lacks_is_a_usage_error(self):
        for argv in (["--model", "carbon"], ["--model", "flash", "--reasoning", "xhigh"]):
            code, _, err = self.run_cli("run", "default", "x", *argv)
            self.assertEqual(code, 2, argv)
        self.assertIsNone(self.call())
        self.assertEqual(ac.model_slug("gemini-4-neon-high", None), "gemini-4-neon-high")
        self.assertEqual(ac.model_slug("hydrogen", None), "gemini-4-hydrogen-medium")

    def test_the_prompt_carries_the_brief_the_hints_and_the_citation_form(self):
        self.write("src/a.py", "x = 1\n")
        self.run_cli("run", "default", "Review it.", "--context", "src/a.py")
        prompt = self.call()["argv"][self.call()["argv"].index("--print") + 1]
        self.assertIn("<task>\nReview it.\n</task>", prompt)
        self.assertIn("Start with these files: src/a.py", prompt)
        self.assertIn("[path/from/this/folder:L12-L14]", prompt)
        self.assertEqual(self.run_cli("run", "default", "x", "--context", "missing.py")[0], 2)

    def test_agy_missing_is_a_failure_that_names_the_fix(self):
        with mock.patch.dict(os.environ, {"GEMINI_ORCH_AGY": str(self.stub_dir / "absent")}):
            code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 1)
        self.assertIn("--direct still works", err)


class DenyRuleTests(AgyBase):
    def test_read_only_and_the_fixed_rules_are_absolute_paths(self):
        (self.work / ".git").mkdir()
        self.run_cli("run", "default", "x")
        rules = self.rules()
        self.assertIn(f"write_file({self.work})", rules)
        self.assertIn(f"read_file({Path.home() / '.gitconfig'})", rules)
        self.assertIn(f"read_file({self.work / '.git'})", rules)
        for rule in rules:
            self.assertTrue(rule.split("(", 1)[1].startswith("/"), rule)

    def test_files_that_may_not_leave_are_denied_one_by_one(self):
        self.configure(egress_denylist=["planted@example.org"])
        self.write("notes/contact.md", "Write to Planted@Example.org.\n")
        self.write(".env", "A=1\n")
        self.write("deploy.sh", "export API_KEY=abcdefghijklmnop1234\n")
        self.write("blob.bin", "\0\0planted@example.org")
        self.write("fine.md", "Nothing here.\n")
        self.write("node_modules/pkg/.env", "A=1\n")
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 0, err)
        rules = self.rules()
        named = ("notes/contact.md", ".env", "deploy.sh", "blob.bin", "node_modules/pkg/.env")
        for name in named:
            self.assertIn(f"withheld: {name}", err)
        # Until the review of 2026-11-22 a count of six stood here, which held the credentials file under
        # node_modules to be readable. The rules inside the folder are now given exactly; those for git's own
        # configs lie outside it and differ by machine.
        inside = sorted(r for r in rules if r.split("(", 1)[1].startswith(f"{self.work}"))
        self.assertEqual(inside, sorted([*(f"read_file({self.work / name})" for name in named),
                                         f"write_file({self.work})"]))

    def test_allow_exempts_a_secret_pattern_but_never_an_address(self):
        self.configure(egress_denylist=["planted@example.org"])
        self.write("fixture.txt", "API_KEY=abcdefghijklmnop1234\n")
        self.write("both.txt", "API_KEY=abcdefghijklmnop1234 planted@example.org\n")
        self.run_cli("run", "default", "x", "--allow", "fixture.txt", "both.txt")
        rules = self.rules()
        self.assertNotIn(f"read_file({self.work / 'fixture.txt'})", rules)
        self.assertIn(f"read_file({self.work / 'both.txt'})", rules)

    def test_a_link_is_denied_with_its_target(self):
        self.configure(egress_denylist=["planted@example.org"])
        target = self.work.parent / "elsewhere.md"
        target.write_text("planted@example.org\n")
        (self.work / "link.md").symlink_to(target)
        self.run_cli("run", "default", "x")
        self.assertIn(f"read_file({self.work / 'link.md'})", self.rules())
        self.assertIn(f"read_file({target})", self.rules())

    def test_a_file_too_large_to_scan_is_withheld(self):
        self.write("big.dat", "x" * 64)
        with mock.patch.object(ac, "MAX_SCAN_BYTES", 32):
            _, _, err = self.run_cli("run", "default", "x")
        self.assertIn(f"read_file({self.work / 'big.dat'})", self.rules())
        self.assertIn("too large to scan", err)

    def test_a_folder_with_too_many_files_is_refused(self):
        for n in range(4):
            self.write(f"f{n}.txt", "x\n")
        with mock.patch.object(ac, "MAX_SCAN_FILES", 3):
            code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 2)
        self.assertIsNone(self.call())

    def test_a_brief_that_carries_a_denied_address_is_never_run(self):
        self.configure(egress_denylist=["planted@example.org"])
        code, _, _ = self.run_cli("run", "default", "Mail planted@example.org")
        self.assertEqual(code, 5)
        self.assertIsNone(self.call())


class CreditsTests(AgyBase):
    def test_with_credits_on_a_run_needs_the_approval_flag(self):
        self.saved.write_text(json.dumps({"useG1Credits": True}))
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 3)
        self.assertIn("--approved-credits", err)
        self.assertIsNone(self.call())
        self.assertEqual(self.run_cli("run", "default", "x", "--approved-credits")[0], 0)

    def test_estimate_quotes_no_dollars_and_starts_nothing(self):
        self.configure(egress_denylist=["planted@example.org"])
        self.write("contact.md", "planted@example.org\n")
        code, out, _ = self.run_cli("estimate", "default", "x")
        self.assertEqual(code, 0)
        self.assertIn("gemini-4-neon-medium", out)
        self.assertIn("withheld: contact.md (denied email address)", out)
        self.assertIn("1 files withheld", out)
        self.assertNotIn("$", out)
        self.assertIsNone(self.call())
        self.assertEqual(self.ledger(), [])


class OutcomeTests(AgyBase):
    def test_a_good_run_is_recorded_with_tokens_and_no_dollar_figure(self):
        code, _, err = self.run_cli("run", "default", "x")
        entry = self.ledger()[-1]
        self.assertEqual((entry["route"], entry["status"], entry["cost"]), ("agy", "ok", None))
        self.assertEqual((entry["prompt_tokens"], entry["completion_tokens"], entry["reasoning_tokens"]),
                         (900, 40, 12))
        self.assertEqual(entry["conversation"], CID)
        self.assertIsInstance(entry["longest_gap_seconds"], float)
        self.assertEqual(self.failures(), [])
        self.assertIn("route=agy", err)
        self.assertIn("cost=quota", err)
        out = self.output(err)
        self.assertTrue(out.read_text().startswith("Hello world\n"))
        self.assertEqual(len(out.with_suffix(".stream.jsonl").read_text().splitlines()), 4)
        _, shown, _ = self.run_cli("spend")
        self.assertIn("1 of those runs went through agy", shown)
        self.assertIn("952 tokens", shown)

    def test_a_run_ended_by_a_permission_request_is_a_failure_that_names_the_tool(self):
        self.plan([INIT, result("", denied_actions=[{"action": "read_file", "display_name": "ReadFile"}])],
                  stderr=DENIED_NOTE)
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 4)
        self.assertIn("stopped at a permission request (read_file)", err)
        failure = self.failures()[-1]
        self.assertEqual((failure["route"], failure["stage"], failure["denied"]), ("agy", "after the run", ["read_file"]))
        self.assertIn("auto-denied", failure["stderr"])

    def test_the_notice_alone_marks_a_permission_stop_and_plain_emptiness_is_told_apart(self):
        self.plan([INIT, result("")], stderr=DENIED_NOTE)
        _, _, err = self.run_cli("run", "default", "x")
        self.assertIn("stopped at a permission request (tool not named)", err)
        self.plan([INIT, result("  \n")])
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 4)
        self.assertIn("status=empty answer", err)

    def test_an_error_from_agy_is_logged_with_its_message(self):
        self.plan([result("", status="ERROR", error="model not found")], stderr="boom\n", exit=1)
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 1)
        failure = self.failures()[-1]
        self.assertIn("ERROR: model not found", failure["status"])
        self.assertEqual((failure["stage"], failure["agy_exit"]), ("before the run", 1))

    def test_a_stream_that_ends_without_a_result_keeps_the_text_so_far(self):
        self.plan([INIT, text(1, "first step"), tool(2, "run_command", {"CommandLine": "ls"}),
                   text(3, "Half an"), text(3, " answer")], exit=2)
        code, out, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "Half an answer")
        self.assertIn("no result from agy (exit 2)", err)
        self.assertEqual(self.failures()[-1]["stage"], "during the run")

    def test_a_silent_run_is_stopped(self):
        self.configure(agy_idle_seconds=0.3)
        self.plan([INIT], hang=20)
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 1)
        self.assertIn("stopped by the launcher (no step for", err)
        self.assertLess(self.ledger()[-1]["seconds"], 10)

    def test_a_run_past_its_time_limit_is_stopped(self):
        self.plan([INIT], hang=20)
        stopped = ac.run([os.environ["GEMINI_ORCH_AGY"]], self.work, idle_seconds=30, total_seconds=0.3)
        self.assertEqual(stopped.stopped, "time limit of 0 s")
        self.assertEqual(ac.outcome(stopped)[0], "stopped")
        self.assertLess(stopped.timing["total_s"], 10)

    def test_the_launchers_limit_sits_past_agys_own(self):
        seen = {}

        def fake(cmd, cwd, **kw):
            seen.update(kw)
            return ac.AgyResult(status="SUCCESS", response="ok")
        with mock.patch.object(ac, "run", fake):
            self.run_cli("run", "default", "x", "--timeout", "60")
        self.assertEqual((seen["total_seconds"], seen["idle_seconds"]), (90.0, 300.0))


class AuditTests(AgyBase):
    def test_the_manifest_lists_files_read_and_commands_run(self):
        self.write("a.py", "x = 1\n")
        self.plan([INIT, tool(1, "read_file", {"Path": str(self.work / "a.py")}, "1 lines, 6 bytes"),
                   tool(2, "run_command", {"CommandLine": "grep -n x a.py"}, "1:x = 1"), result("Done.")])
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 0, err)
        manifest = json.loads(self.output(err).with_suffix(".manifest.json").read_text())
        self.assertEqual([(f["path"], f["read"]) for f in manifest["files"]], [("a.py", True)])
        self.assertEqual(manifest["commands"], ["grep -n x a.py"])
        self.assertIn(f"write_file({self.work})", manifest["deny_rules"])
        self.assertIn("files_read=1 commands=1", err)
        entry = self.ledger()[-1]
        self.assertEqual((entry["steps"], entry["tools"], entry["files_read"], entry["egress"]), (3, 2, 1, 0))

    def test_a_denied_address_in_a_tool_output_is_reported_even_when_the_answer_is_good(self):
        self.configure(egress_denylist=["planted@example.org"])
        self.plan([INIT, tool(1, "run_command", {"CommandLine": "git log -1"}, "Author: P <planted@example.org>"),
                   result("One commit.")])
        code, out, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 5)
        self.assertEqual(out.strip(), "One commit.")
        self.assertIn("egress=1", err)
        self.assertIn("<step 1 run_command>", err)
        failure = self.failures()[-1]
        self.assertEqual(failure["egress"][0]["kind"], "denied email address")
        self.assertNotIn("planted@example.org", json.dumps(failure["egress"]))

    def test_a_file_read_that_holds_a_secret_is_reported(self):
        outside = self.work.parent / "outside.txt"
        outside.write_text("TOKEN=abcdefghijklmnop1234\n")
        self.plan([INIT, tool(1, "view_file", {"Path": str(outside)}, "1 lines"), result("Read it.")])
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 5)
        self.assertIn(f"{outside}:1  assigned secret", err)

    def test_no_profile_runs_without_a_persona(self):
        # Probed live 2026-11-22: without a persona agy's own search_web ran, outside the sandbox and past the deny
        # rules; under a persona's tool list it was not offered. So a missing persona stops the run, `default` too.
        _, _, err = self.run_cli("run", "default", "x")
        self.assertIn("agent orch-default, read-only in the sandbox with no network,", err)
        (self.agents / "harness" / "default.md").unlink()
        (self.stub_dir / "call.json").unlink()
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 2)
        self.assertIn("no harness persona", err)
        self.assertIsNone(self.call())

    def test_a_read_the_deny_rules_refused_is_not_counted_as_read(self):
        # The live check of 2026-11-22: four planted files were refused, and the audit reported all four as leaks.
        self.write("ok.txt", "fine\n")
        self.write("held/.env", "TOKEN=abcdefghijklmnop1234\n")
        held = self.work / "held" / ".env"
        refused = ev("step_update", step_index=2, state="ERROR", step_type="tool", tool_name="read_file",
                     tool_info={"name": "read_file", "parameters": {"Path": str(held)},
                                "error": {"type": "TOOL_ERROR", "message": "permission check failed for read_file"}})
        started = ev("step_update", step_index=2, state="ACTIVE", step_type="tool", tool_name="read_file",
                     tool_info={"name": "read_file", "parameters": {"Path": str(held)}})
        self.plan([INIT, tool(1, "read_file", {"Path": str(self.work / "ok.txt")}, "1 lines"), started, refused,
                   result("One read, one refused.")])
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 0, err)
        self.assertIn("files_read=1", err)
        self.assertIn("refused=1", err)
        self.assertIn("egress=0", err)
        manifest = json.loads(self.output(err).with_suffix(".manifest.json").read_text())
        self.assertEqual([f["path"] for f in manifest["files"]], ["ok.txt"])
        self.assertEqual(manifest["refused"], ["held/.env"])

    def test_a_read_cut_off_before_it_finished_is_still_audited(self):
        outside = self.work.parent / "outside.txt"
        outside.write_text("TOKEN=abcdefghijklmnop1234\n")
        started = ev("step_update", step_index=1, state="ACTIVE", step_type="tool", tool_name="read_file",
                     tool_info={"name": "read_file", "parameters": {"Path": str(outside)}})
        self.plan([INIT, started, result("Read it.")])
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 5)
        self.assertIn(f"{outside}:1  assigned secret", err)

    def test_citations_are_checked_against_the_cited_files_even_when_read_by_a_command(self):
        self.write("doc.md", "alpha\nbeta gamma\n")
        answer = '[doc.md:L2] "beta gamma" and [doc.md:L1] "delta" and [../outside.md:L1] "x"'
        (self.work.parent / "outside.md").write_text("x\n")
        self.plan([INIT, tool(1, "run_command", {"CommandLine": "cat doc.md"}, "alpha\nbeta gamma"), result(answer)])
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 0)
        self.assertIn("citations=1/3", err)
        self.assertIn("not_found", err)
        self.assertIn("unknown_file", err)


class ReviewFindingTests(AgyBase):
    """Defects found by the first live reviewer run through this route (2026-11-22), each reproduced before its fix."""

    def sh(self, script: str, **limits) -> tuple[ac.AgyResult, float]:
        import time
        started = time.monotonic()
        res = ac.run(["sh", "-c", script], self.work, **{"idle_seconds": 5, "total_seconds": 10, **limits})
        return res, time.monotonic() - started

    def test_a_helper_that_outlives_agy_does_not_hold_the_run_open(self):
        done = result("ok").replace("'", "")
        for helper in ("(sleep 6 >/dev/null) &", "(sleep 6) &"):  # holding stderr only, then stdout too
            res, elapsed = self.sh(f"{helper} printf '%s\\n' '{done}'", idle_seconds=1, total_seconds=2)
            self.assertLess(elapsed, 3, helper)
            self.assertEqual(ac.outcome(res), ("ok", "ok"), helper)

    def test_a_result_followed_by_a_failing_exit_is_not_a_success(self):
        res, _ = self.sh(f"printf '%s\\n' '{result('partial')}'; exit 1")
        self.assertEqual(res.exit_code, 1)
        self.assertEqual(ac.outcome(res)[0], "error")
        self.plan([INIT, result("partial")], exit=1)
        self.assertEqual(self.run_cli("run", "default", "x")[0], 1)

    def test_the_stderr_notice_survives_a_helper_that_keeps_stderr_open(self):
        res, _ = self.sh(f"(sleep 6 >/dev/null) & echo auto-denied >&2; printf '%s\\n' '{result('')}'",
                         idle_seconds=1, total_seconds=2)
        self.assertEqual(ac.outcome(res)[0], "permission")

    def test_malformed_events_do_not_raise(self):
        res = ac.AgyResult()
        ac.absorb(res, json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "",
                                                                 "denied_actions": ["read_file", None]}}), 1.0)
        self.assertEqual(res.denied, ["read_file"])
        ac.absorb(res, json.dumps({"event": "step_update", "step_update": {"step_index": "x", "step_type": "tool"}}), 1.0)
        ac.absorb(res, json.dumps({"event": "step_update", "step_update": "nonsense"}), 1.0)

    def test_an_exception_while_reading_still_ends_the_process(self):
        pidfile = self.work.parent / "pid"
        with mock.patch.object(ac, "absorb", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                ac.run(["sh", "-c", f"echo $$ > {pidfile}; echo line; sleep 30"], self.work, idle_seconds=5,
                       total_seconds=10)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(pidfile.read_text()), 0)

    def test_an_unfinished_tool_step_is_kept_and_a_repeated_one_is_not_doubled(self):
        res = ac.AgyResult()
        active = ev("step_update", step_index=2, state="ACTIVE", step_type="tool", tool_name="run_command",
                    tool_info={"name": "run_command", "parameters": {"CommandLine": "cat x"}})
        for line in (active, tool(1, "read_file", {"Path": "a"}, "1 lines"), tool(1, "read_file", {"Path": "a"}, "1 lines")):
            ac.absorb(res, line, 1.0)
        self.assertEqual([(t["index"], t["name"]) for t in res.tools], [(1, "read_file"), (2, "run_command")])
        manifest, _ = ac.audit(res, self.work, [])
        self.assertEqual(manifest["commands"], ["cat x"])

    def test_the_longest_gap_counts_the_silence_before_a_stop(self):
        res, _ = self.sh("echo line; sleep 30", idle_seconds=0.5, total_seconds=10)
        self.assertGreaterEqual(res.timing["longest_gap_s"], 0.5)

    def test_skipped_folders_that_hold_records_are_denied_whole(self):
        for name in ("sub/.git/config", ".subdaimon-output/old.stream.jsonl", ".beans/db", "node_modules/pkg/a.js"):
            self.write(name, "x\n")
        self.run_cli("run", "default", "x")
        rules = self.rules()
        for folder in ("sub/.git", ".subdaimon-output", ".beans"):
            self.assertIn(f"read_file({self.work / folder})", rules)
        self.assertNotIn(f"read_file({self.work / 'node_modules'})", rules)  # dependencies stay readable, unscanned

    def test_a_linked_folder_is_denied_with_its_target(self):
        private = self.work.parent / "private"
        private.mkdir()
        (self.work / "ext").symlink_to(private, target_is_directory=True)
        self.run_cli("run", "default", "x")
        self.assertIn(f"read_file({self.work / 'ext'})", self.rules())
        self.assertIn(f"read_file({private})", self.rules())

    def test_a_folder_above_a_direct_only_folder_refuses_agy_too(self):
        (self.work / "inner").mkdir()
        self.configure(direct_only_paths=[str(self.work / "inner")])
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 2)
        self.assertIn("direct_only_paths", err)
        self.configure(direct_only_paths=["/"])
        self.assertEqual(self.run_cli("run", "default", "x")[0], 2)
        self.assertIsNone(self.call())

    def test_names_and_contents_that_slipped_the_scan_are_withheld(self):
        self.configure(egress_denylist=["planted@example.org"])
        outside = self.work.parent / "outside"
        outside.mkdir()
        (outside / ".env").write_text("A=1\n")
        (self.work / "notes.txt").symlink_to(outside / ".env")
        self.write(".ENV", "A=1\n")
        self.write("Keystore.P12", "x")
        (self.work / "db.bin").write_bytes(b"\0\0sk-or-v1-1234567890abcdefghij123456\n")
        (self.work / "wide.txt").write_bytes("contact: planted@example.org\n".encode("utf-16"))
        (self.work / "wide-le.txt").write_bytes("contact: planted@example.org\n".encode("utf-16-le"))
        self.run_cli("run", "default", "x")
        for name in ("notes.txt", ".ENV", "Keystore.P12", "db.bin", "wide.txt", "wide-le.txt"):
            self.assertIn(f"read_file({self.work / name})", self.rules(), name)

    def test_every_place_git_keeps_the_address_is_denied(self):
        home = self.work.parent / "home"
        (home / "dotfiles").mkdir(parents=True)
        (home / "dotfiles" / "gitconfig").write_text("[user]\n")
        (home / ".gitconfig").symlink_to(home / "dotfiles" / "gitconfig")
        env = {"HOME": str(home), "GIT_CONFIG_GLOBAL": str(home / "elsewhere"), "XDG_CONFIG_HOME": str(home / "xdg")}
        with mock.patch.dict(os.environ, env):
            self.run_cli("run", "default", "x")
        for p in (home / ".gitconfig", home / "dotfiles" / "gitconfig"):
            self.assertIn(f"read_file({p})", self.rules(), p)
        self.assertNotIn(f"read_file({home / 'elsewhere'})", self.rules())  # no rule for a path that is not there
        (home / "elsewhere").write_text("[user]\n")
        (home / "xdg/git").mkdir(parents=True)
        (home / "xdg/git/config").write_text("[user]\n")
        with mock.patch.dict(os.environ, env):
            self.run_cli("run", "default", "x")
        for p in (home / "elsewhere", home / "xdg/git/config"):
            self.assertIn(f"read_file({p})", self.rules(), p)

    def test_from_a_subfolder_the_repository_above_is_still_denied(self):
        import subprocess
        subprocess.run(["git", "init", "-q", str(self.work)], check=True)
        (self.work / "sub").mkdir()
        os.chdir(self.work / "sub")
        self.run_cli("run", "default", "x")
        self.assertIn(f"read_file({self.work / '.git'})", self.rules())

    def test_a_run_served_by_another_model_is_not_a_success(self):
        self.plan([ev("init", model="gemini-3.8-flash-medium"), result("Hello")])
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 6)
        self.assertIn("served by a different model", err)
        self.assertEqual(self.failures()[-1]["exit_code"], 6)

    def test_a_relative_path_in_a_read_is_taken_from_the_workspace(self):
        self.write("a.py", "x = 1\n")
        res = ac.AgyResult(status="SUCCESS", response="ok", tools=[
            {"index": 1, "name": "read_file", "parameters": {"Path": "a.py"}, "output": ""}])
        os.chdir(self.work.parent)
        manifest, _ = ac.audit(res, self.work, [])
        self.assertEqual([(f["path"], f["abs"]) for f in manifest["files"]], [("a.py", str(self.work / "a.py"))])

    def test_what_the_model_wrote_is_not_egress_but_what_it_was_shown_is(self):
        key = "sk-or-v1-1234567890abcdefghij123456"
        self.plan([INIT, tool(1, "run_command", {"CommandLine": f"echo {key}"}, "ran"), result(f"For example {key}")])
        self.assertEqual(self.run_cli("run", "default", "x")[0], 0)
        self.plan([INIT, tool(1, "run_command", {"CommandLine": "cat k"}, key), result("Done.")])
        self.assertEqual(self.run_cli("run", "default", "x")[0], 5)


class SecondReviewTests(AgyBase):
    """Defects found by the Hydrogen reviewer run of 2026-11-22, each reproduced before its fix."""

    def test_a_git_config_that_cannot_be_examined_is_denied_all_the_same(self):
        locked = self.work.parent / "locked.gitconfig"
        real_exists = Path.exists

        def exists(p, *a, **k):
            if p == locked:
                raise PermissionError(1, "Operation not permitted", str(p))
            return real_exists(p, *a, **k)

        with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(locked)}), \
                mock.patch.object(Path, "exists", exists):
            self.assertIn(locked, ac._git_places(self.work))

    def test_a_relative_git_config_path_gives_only_absolute_rules(self):
        self.write("rel.gitconfig", "[user]\n")
        before = os.getcwd()
        os.chdir(self.work)
        try:
            with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": "rel.gitconfig"}):
                places = ac._git_places(self.work)
        finally:
            os.chdir(before)
        self.assertIn((self.work / "rel.gitconfig").resolve(), places)
        self.assertEqual([p for p in places if not p.is_absolute()], [])

    def test_a_link_into_a_folder_that_cannot_be_entered_is_withheld_not_a_crash(self):
        vault = self.work.parent / "vault"
        vault.mkdir()
        (vault / "secret.txt").write_text("x\n")
        (self.work / "link.txt").symlink_to(vault / "secret.txt")
        vault.chmod(0)
        self.addCleanup(vault.chmod, 0o700)
        rules, withheld = ac.deny_rules(self.work, [])
        self.assertIn(("link.txt", "could not be scanned"), withheld)
        self.assertIn(f"read_file({self.work.resolve() / 'link.txt'})", rules)

    def test_the_audit_finds_an_address_in_a_utf16_file(self):
        outside = self.work.parent / "wide.txt"
        outside.write_bytes("contact: planted@example.org\n".encode("utf-16-le"))
        res = ac.AgyResult()
        ac.absorb(res, tool(1, "view_file", {"Path": str(outside)}, "1 lines"), 1.0)
        _, findings = ac.audit(res, self.work, ["planted@example.org"])
        self.assertEqual([f.kind for f in findings], ["denied email address"])

    def test_saved_settings_that_are_not_an_object_count_as_none(self):
        for text in ("null", "[]", '"x"'):
            self.saved.write_text(text)
            self.assertEqual(ac.saved_settings(), {}, text)
        self.assertEqual(self.run_cli("run", "default", "x")[0], 0)

    def test_a_time_limit_under_a_second_is_not_sent_as_no_limit(self):
        cmd = ac.build_command("agy", "p", "gemini-4-neon-medium", {}, seconds=0.5)
        self.assertEqual(cmd[cmd.index("--print-timeout") + 1], "1s")  # agy reads 0s as "wait for ever"

    def test_a_denied_address_in_a_context_path_stops_the_run(self):
        self.configure(egress_denylist=["planted@example.org"])
        self.write("notes-planted@example.org.txt", "nothing private\n")
        code, _, err = self.run_cli("run", "default", "x", "--context", "notes-planted@example.org.txt")
        self.assertEqual(code, 5, err)
        self.assertIsNone(self.call())


WRITE_FRONT = ("name: orch-builder\ndescription: Test builder.\ntools:\n  - view_file\n  - run_command\n"
               "  - write_to_file\n  - replace_file_content\nsubagent: false\ncommandExecutionPolicy: sandbox\n")


class BuilderTests(AgyBase):
    """The one profile that writes. What the live probe of 2026-11-22 showed is in the plan under Phase 3."""

    def setUp(self):
        super().setUp()
        harness = self.agents / "harness"
        (harness / "builder.md").write_text(f"---\n{WRITE_FRONT}---\n# Builder\nBuild it.\n")
        (harness / "_shared.md").write_text("You cannot write.\n")
        (harness / "_shared-write.md").write_text("You may write inside the folder.\n")
        self.configure(profiles={"builder": {"model": "neon", "effort": "medium", "routes": ["agy", "openrouter"],
                                             "access": "write"}})

    def git(self, *argv: str, cwd: Path | None = None) -> str:
        import subprocess
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}
        return subprocess.run(["git", "-C", str(cwd or self.work), *argv], capture_output=True, text=True, env=env,
                              check=True).stdout

    def repo(self) -> None:
        self.git("init", "-q")
        self.write("a.py", "x = 1\n")
        self.git("add", "a.py")
        self.git("commit", "-q", "-m", "start")

    def test_write_tools_are_for_a_write_persona_only(self):
        harness = self.agents / "harness"
        text = ac.compose_persona("builder", harness, write=True)
        self.assertIn("  - write_to_file\n", text)
        self.assertIn("You may write inside the folder.", text)
        self.assertNotIn("You cannot write.", text)
        with self.assertRaises(ac.AgyError):
            ac.compose_persona("builder", harness)  # the same file under a read-only profile
        (harness / "builder.md").write_text(f"---\n{WRITE_FRONT}---\nBuild.\n".replace("write_to_file", "browser_input"))
        with self.assertRaises(ac.AgyError):
            ac.compose_persona("builder", harness, write=True)

    def test_a_write_run_cannot_write_what_git_cannot_restore(self):
        self.repo()
        self.write(".gitignore", "ignored.dat\ncache/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-q", "-m", "ignore")
        self.write("ignored.dat", "kept\n")
        self.write("cache/big.bin", "kept\n")
        self.write(".env", "A=1\n")
        self.write("untracked-notes.txt", "never committed\n")
        work = self.work.resolve()
        rules, _ = ac.deny_rules(self.work, [], write=True)
        self.assertNotIn(f"write_file({work})", rules)
        for name in (".git", ".env", "ignored.dat", "cache", "untracked-notes.txt"):
            self.assertIn(f"write_file({work / name})", rules, name)
        self.assertIn(f"read_file({work / '.env'})", rules)
        self.assertNotIn(f"write_file({work / 'a.py'})", rules)
        self.assertNotIn(f"read_file({work / 'ignored.dat'})", rules)  # still readable, as before

    def test_a_write_run_is_told_to_accept_edits(self):
        cmd = ac.build_command("agy", "p", "gemini-4-neon-medium", {}, seconds=60, agent="orch-builder", write=True)
        self.assertEqual(cmd[cmd.index("--mode") + 1], "accept-edits")
        self.assertNotIn("--mode", ac.build_command("agy", "p", "gemini-4-neon-medium", {}, seconds=60))
        self.assertNotIn("--dangerously-skip-permissions", cmd)

    def test_a_write_run_needs_a_repository_with_no_uncommitted_edits(self):
        code, _, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 2)
        self.assertIn("git repository", err)
        self.repo()
        self.write("a.py", "x = 2\n")
        for command in ("run", "estimate"):
            code, out, err = self.run_cli(command, "builder", "Build it.")
            self.assertEqual(code, 2, command)
            self.assertIn("a.py", out + err)
        self.assertIsNone(self.call())

    def test_a_write_run_reports_what_changed(self):
        self.repo()
        self.write("untracked-notes.txt", "never committed\n")
        self.plan([INIT, result("Built.")], writes={"a.py": "x = 2\n", "new/b.py": "y = 1\n"})
        code, _, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 0, err)
        argv = self.call()["argv"]
        self.assertEqual(argv[argv.index("--agent") + 1], "orch-builder")
        self.assertEqual(argv[argv.index("--mode") + 1], "accept-edits")
        work = self.work.resolve()
        self.assertNotIn(f"write_file({work})", self.rules())
        self.assertIn(f"write_file({work / 'untracked-notes.txt'})", self.rules())
        self.assertIn("writes inside this folder", err)
        self.assertIn("changed=2", err)
        self.assertIn("Changed files (review the diff and run the tests):\n   M a.py\n  ?? new/b.py\n", err)
        manifest = json.loads(self.output(err).with_suffix(".manifest.json").read_text())
        self.assertEqual(manifest["changed"], [{"status": "M", "path": "a.py"}, {"status": "??", "path": "new/b.py"}])
        self.assertEqual(self.ledger()[-1]["changed"], 2)
        self.assertIn("  - write_to_file\n", (self.installed / "orch-builder" / "agent.md").read_text())

    def test_changes_are_reported_when_the_run_fails(self):
        self.repo()
        self.plan([INIT, result("")], writes={"a.py": "x = 3\n"}, stderr=DENIED_NOTE)
        code, _, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 4)
        self.assertIn("changed=1", err)
        self.assertIn("   M a.py\n", err)

    def test_a_read_only_profile_reports_no_changes_and_keeps_its_rules(self):
        self.repo()
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 0, err)
        self.assertNotIn("changed=", err)
        self.assertIn(f"write_file({self.work})", self.rules())
        self.assertNotIn("--mode", self.call()["argv"])

    # --- found by the compound-engineering review of 2026-11-22, each reproduced before its fix ---

    def manifest(self, err: str) -> dict:
        return json.loads(self.output(err).with_suffix(".manifest.json").read_text())

    def ignoring(self, text: str) -> None:
        self.repo()
        self.write(".gitignore", text)
        self.git("add", ".gitignore")
        self.git("commit", "-q", "-m", "ignore")

    def test_the_builder_is_not_told_that_it_cannot_write(self):
        self.repo()
        self.run_cli("run", "builder", "Build it.")
        argv = self.call()["argv"]
        prompt = argv[argv.index("--print") + 1]
        self.assertNotIn("cannot write", prompt)
        self.assertIn("create and edit files inside this folder", prompt)
        self.run_cli("run", "default", "x")
        argv = self.call()["argv"]
        self.assertIn("You cannot write files", argv[argv.index("--print") + 1])

    def test_new_files_git_ignores_and_files_in_the_output_folder_are_reported(self):
        self.ignoring("*.log\nbuild/\n")
        self.plan([INIT, result("Built.")],
                  writes={"debug.log": "x\n", "build/out.js": "x\n", ".subdaimon-output/x.py": "x\n"})
        code, _, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 0, err)
        self.assertEqual({c["path"] for c in self.manifest(err)["changed"]},
                         {"debug.log", "build/", ".subdaimon-output/x.py"})
        self.assertNotIn("stream.jsonl", err.split("Changed files")[1])  # the launcher's own files are not listed

    def test_a_folder_git_ignores_does_not_count_as_an_uncommitted_edit(self):
        self.ignoring("build/\n")
        self.write("build/old.js", "x\n")
        code, _, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 0, err)
        self.assertIn("No file was changed.", err)

    def test_a_repository_inside_the_folder_and_a_worktrees_git_file_are_write_denied(self):
        self.repo()
        inner = self.work / "sub"
        inner.mkdir()
        self.git("init", "-q", cwd=inner)
        (inner / "f.txt").write_text("x\n")
        self.git("add", "f.txt", cwd=inner)
        self.git("commit", "-q", "-m", "inner", cwd=inner)
        self.git("add", "sub")
        self.git("commit", "-q", "-m", "link")
        rules, _ = ac.deny_rules(self.work, [], write=True)
        self.assertIn(f"write_file({self.work / 'sub'})", rules)  # git records only its commit, not its files
        tree = self.work.parent / "wt"
        self.git("worktree", "add", "-q", str(tree))
        rules, _ = ac.deny_rules(tree, [], write=True)
        for kind in ("read_file", "write_file"):
            self.assertIn(f"{kind}({tree / '.git'})", rules)  # here .git is a file that points at the repository
        (tree / "deep").mkdir()
        (tree / "deep" / ".git").write_text("gitdir: ../../elsewhere\n")  # as a submodule's checkout has, at any depth
        self.assertIn(f"read_file({tree / 'deep' / '.git'})", ac.deny_rules(tree, [])[0])

    def test_files_that_steer_an_agent_are_write_denied_and_a_change_to_one_fails_the_run(self):
        self.ignoring(".claude/settings.local.json\n")
        self.plan([INIT, result("Built.")], writes={".claude/settings.local.json": "{}\n", "a.py": "x = 2\n"})
        code, _, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 1, err)
        for name in (".claude", ".agents", ".gemini", "AGENTS.md", "GEMINI.md", "CLAUDE.md", ".envrc"):
            self.assertIn(f"write_file({self.work / name})", self.rules(), name)
        self.assertIn("control files changed", err)
        self.assertIn("  .claude/settings.local.json\n", err.split("steer")[1])
        self.assertEqual(self.failures()[-1]["exit_code"], 1)
        self.assertTrue(ac.control_file("docs/claude.md") and ac.control_file("x/.agents/agents/a/agent.md"))
        self.assertTrue(ac.control_file("CLAUDE.md") and ac.control_file("sub/Agents.MD"))
        self.assertFalse(ac.control_file("src/agents.py"))

    def test_an_untracked_or_withheld_file_that_changed_fails_the_run(self):
        self.repo()
        self.write("untracked-notes.txt", "never committed\n")
        self.write(".env", "A=1\n")
        self.write("gone.txt", "x\n")
        paths = ac.guarded(self.work, [(".env", "credentials file")])
        self.assertEqual({p.name for p in paths}, {".env", "untracked-notes.txt", "gone.txt"})
        before = ac.fingerprints(paths)
        self.assertEqual(ac.disturbed(before, paths), [])
        (self.work / "gone.txt").unlink()
        (self.work / ".env").write_text("A=2\n")
        self.assertEqual(ac.disturbed(before, paths), [(str(self.work / ".env"), "altered"),
                                                       (str(self.work / "gone.txt"), "missing")])
        self.write("gone.txt", "x\n")
        self.plan([INIT, result("Built.")], writes={"untracked-notes.txt": "overwritten\n"})
        code, _, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 1, err)
        self.assertIn("untracked-notes.txt (altered)", err)
        self.assertEqual(self.manifest(err)["disturbed"],
                         [{"path": str(self.work / "untracked-notes.txt"), "what": "altered"}])

    def test_git_failing_after_the_run_does_not_lose_the_answer(self):
        self.repo()
        real, calls = ac.git_changes, []

        def flaky(workspace):
            calls.append(1)
            if len(calls) > 1:
                raise ac.AgyError("git status failed: index.lock exists")
            return real(workspace)

        self.plan([INIT, result("Built.")], writes={"a.py": "x = 2\n"})
        with mock.patch.object(ac, "git_changes", flaky):
            code, out, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 1, err)
        self.assertIn("Built.", out)
        self.assertIn("changed=unknown", err)
        self.assertIn("index.lock", err)
        self.assertTrue(self.output(err).exists())
        self.assertEqual(len(self.ledger()), 1)
        self.assertEqual(self.failures()[-1]["exit_code"], 1)

    def test_an_interrupted_write_run_is_still_recorded_with_its_changes(self):
        self.repo()
        self.plan([INIT, result("Built.")], writes={"a.py": "x = 2\n"})
        with mock.patch.object(ac, "absorb", side_effect=KeyboardInterrupt):
            code, _, err = self.run_cli("run", "builder", "Build it.")
        self.assertEqual(code, 1, err)
        self.assertIn("interrupted", self.ledger()[-1]["status"])
        self.assertIn("   M a.py\n", err)
        self.assertEqual(len(self.failures()), 1)

    def test_only_a_missing_repository_is_called_a_missing_repository(self):
        with self.assertRaises(ac.AgyError) as none:
            ac._git(self.work, "status")
        self.assertTrue(none.exception.usage)
        self.assertIn("needs a git repository", str(none.exception))
        self.repo()
        with self.assertRaises(ac.AgyError) as other:
            ac._git(self.work, "no-such-command")
        self.assertFalse(other.exception.usage)
        self.assertNotIn("needs a git repository", str(other.exception))


class ThirdReviewTests(AgyBase):
    """Defects found by the compound-engineering review of 2026-11-22, each reproduced before its fix."""

    def test_a_stop_signal_ends_the_delegate_and_its_helpers(self):
        import signal
        import subprocess
        import time
        pid, kid = self.work.parent / "pid", self.work.parent / "kid"
        script = f"sleep 60 & echo $! > {kid}; echo $$ > {pid}; echo line; wait"
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import agy_client as ac\n"
                "r = ac.run(['sh', '-c', sys.argv[2]], sys.argv[3], idle_seconds=30, total_seconds=60)\n"
                "print('stopped:', r.stopped)\n")
        for name in ("SIGTERM", "SIGHUP"):
            pid.unlink(missing_ok=True)
            proc = subprocess.Popen([sys.executable, "-c", code, str(Path(ac.__file__).parent), script,
                                     str(self.work)], stdout=subprocess.PIPE, text=True)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not (pid.exists() and pid.read_text().strip()):
                time.sleep(0.05)
            time.sleep(0.2)  # the launcher is reading the stream by now
            proc.send_signal(getattr(signal, name))
            out, _ = proc.communicate(timeout=15)
            self.assertIn(f"stopped: signal {name}", out)  # the launcher went on to its bookkeeping
            for f in (pid, kid):  # the whole group, not only the process agy_client started
                deadline = time.monotonic() + 3
                alive = True
                while alive and time.monotonic() < deadline:
                    try:
                        os.kill(int(f.read_text()), 0)
                        time.sleep(0.05)
                    except ProcessLookupError:
                        alive = False
                self.assertFalse(alive, f"{name}: {f.name}")

    def test_an_agent_file_in_the_tree_that_could_replace_the_persona_is_refused(self):
        for folder in (self.work, self.work.parent):
            shadow = folder / ".agents/agents/orch-default/agent.md"
            shadow.parent.mkdir(parents=True)
            shadow.write_text("---\nname: orch-default\ntools:\n  - search_web\n---\n")
            for command in ("run", "estimate"):
                code, out, err = self.run_cli(command, "default", "x")
                self.assertEqual(code, 2, folder)
                self.assertIn("orch-default", out + err)
            self.assertIsNone(self.call())
            shadow.unlink()
            shadow.parent.rmdir()
        (self.work / ".agents/agents/my-own").mkdir(parents=True)  # the user's own agents are no concern
        self.assertEqual(self.run_cli("run", "default", "x")[0], 0)

    def test_a_rules_file_agy_loads_by_itself_is_scanned_and_listed(self):
        self.configure(egress_denylist=["planted@example.org"])
        above = self.work.parent / "AGENTS.md"
        home_rules = Path(os.environ["GEMINI_ORCH_AGY_RULES"])
        for path in (above, self.work / "GEMINI.md", home_rules):
            path.write_text("Mail planted@example.org.\n")
            self.assertEqual(self.run_cli("run", "default", "x")[0], 5, path)
            self.assertIsNone(self.call(), path)
            path.write_text("Be brief.\n")
        code, _, err = self.run_cli("run", "default", "x")
        self.assertEqual(code, 0, err)
        manifest = json.loads(self.output(err).with_suffix(".manifest.json").read_text())
        self.assertEqual(sorted(manifest["rules_files"]), sorted(map(str, (above, self.work / "GEMINI.md", home_rules))))

    def test_a_credentials_file_in_a_dependency_folder_is_denied_by_name(self):
        self.write("node_modules/pkg/.env", "A=1\n")
        self.write("venv/id_rsa", "x\n")
        self.write("node_modules/pkg/index.js", "API_KEY=abcdefghijklmnop1234\n")  # contents there stay unscanned
        rules, withheld = ac.deny_rules(self.work, [])
        for name in ("node_modules/pkg/.env", "venv/id_rsa"):
            self.assertIn(f"read_file({self.work / name})", rules)
            self.assertIn((name, "credentials file"), withheld)
        self.assertNotIn(f"read_file({self.work / 'node_modules/pkg/index.js'})", rules)

    def test_configs_that_gits_global_config_includes_are_denied(self):
        home = self.work.parent / "home"
        home.mkdir()
        (home / ".gitconfig").write_text('[include]\n\tpath = ~/.gitconfig-a\n[includeIf "gitdir:~/some where/"]\n'
                                         "\tpath = extra/b.inc\n")
        (home / ".gitconfig-a").write_text("[user]\n")
        (home / "extra").mkdir()
        (home / "extra/b.inc").write_text("[user]\n")
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            os.environ.pop("GIT_CONFIG_GLOBAL", None)
            places = ac._git_places(self.work)
        for p in (home / ".gitconfig", home / ".gitconfig-a", home / "extra/b.inc"):
            self.assertIn(p, places)

    def test_a_device_named_as_gits_config_gets_no_rule(self):
        with mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": os.devnull}):
            self.assertNotIn(Path(os.devnull), ac._git_places(self.work))

    def test_the_repository_above_is_found_without_gits_help(self):
        (self.work / ".git").mkdir()
        (self.work / "sub").mkdir()
        with mock.patch.object(ac.subprocess, "run", side_effect=OSError("no git")):
            self.assertIn(self.work / ".git", ac._git_dirs(self.work / "sub"))

    def test_a_path_whose_rule_agy_might_misread_stops_the_run(self):
        for name in ("a (copy)/.env", "x\n.env", "app/[id]/.env", "what?.pem"):
            self.write(name, "A=1\n")
            with self.assertRaises(ac.AgyError) as refused:
                ac.deny_rules(self.work, [])
            self.assertTrue(refused.exception.usage, name)
            self.assertIn(repr(str(self.work / name)), str(refused.exception))
            (self.work / name).unlink()
        self.write("a (copy)/fine.md", "nothing\n")  # a file that needs no rule may be named anything
        ac.deny_rules(self.work, [])

    def test_a_file_cleared_with_allow_may_be_read_without_failing_the_run(self):
        self.configure(egress_denylist=["planted@example.org"])
        key = "API_KEY=abcdefghijklmnop1234"
        self.write("fixture.txt", key + "\n")
        self.plan([INIT, tool(1, "view_file", {"Path": str(self.work / "fixture.txt")}, key), result("Done.")])
        code, _, err = self.run_cli("run", "default", "x", "--allow", "fixture.txt")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.run_cli("run", "default", "x")[0], 5)  # not cleared: the audit reports it
        self.plan([INIT, tool(1, "view_file", {"Path": str(self.work / "fixture.txt")}, "planted@example.org"),
                   result("Done.")])
        self.assertEqual(self.run_cli("run", "default", "x", "--allow", "fixture.txt")[0], 5)  # never an address

    def test_reading_a_credentials_file_is_a_finding_whatever_it_holds(self):
        outside = self.work.parent / "id_rsa"
        outside.write_text("nothing that matches a pattern\n")
        res = ac.AgyResult()
        ac.absorb(res, tool(1, "view_file", {"Path": str(outside)}, "1 lines"), 1.0)
        _, findings = ac.audit(res, self.work, [])
        self.assertEqual([(f.path, f.kind) for f in findings], [(str(outside), "credentials file read")])

    def test_a_tool_step_with_no_name_is_not_called_none(self):
        res = ac.AgyResult()
        ac.absorb(res, ev("step_update", step_index=1, state="DONE", step_type="tool", tool_info={}), 1.0)
        self.assertEqual(res.tools[0]["name"], "")

    def test_the_quote_counts_the_denied_addresses_and_warns_when_there_are_none(self):
        _, out, err = self.run_cli("estimate", "default", "x")
        self.assertIn("0 denied addresses", out)
        self.assertIn("no denied address is known", err)
        self.configure(egress_denylist=["planted@example.org"])
        code, out, err = self.run_cli("estimate", "default", "x")
        self.assertIn("1 denied address,", out)
        self.assertNotIn("no denied address", err)


FRONT = ("name: orch-reviewer\ndescription: Test reviewer.\ntools:\n  - view_file\n  - run_command\n"
         "subagent: false\ncommandExecutionPolicy: sandbox\n")


class PersonaTests(AgyBase):
    def persona(self, front: str = FRONT, body: str = "# Reviewer\nFind defects.\n", name: str = "reviewer") -> None:
        harness = self.agents / "harness"
        harness.mkdir(exist_ok=True)
        (harness / f"{name}.md").write_text(f"---\n{front}---\n{body}")

    def agent_file(self, name: str = "reviewer") -> Path:
        return self.installed / f"orch-{name}" / "agent.md"

    def test_a_persona_profile_is_installed_and_named_to_agy(self):
        self.persona()
        (self.agents / "harness" / "_shared.md").write_text("Shared harness rules.\n")
        code, _, err = self.run_cli("run", "reviewer", "Review it.")
        self.assertEqual(code, 0, err)
        self.assertEqual(Stub.calls, 0)
        argv = self.call()["argv"]
        self.assertEqual(argv[argv.index("--agent") + 1], "orch-reviewer")
        # Briefly gemini-4-hydrogen-high on 2026-11-22, on a quota reading taken straight after the Hydrogen run.
        # The reading lagged: both models at high cost about a quarter of the week's quota for one review.
        self.assertEqual(argv[argv.index("--model") + 1], "gemini-4-neon-high")
        self.assertEqual(self.agent_file().read_text(),
                         f"---\n{FRONT}---\nShared harness rules.\n\n# Reviewer\nFind defects.\n")
        self.assertIn("agent=orch-reviewer", err)
        self.assertEqual(self.ledger()[-1]["agent"], "orch-reviewer")
        self.assertEqual(list(self.agent_file().parent.iterdir()), [self.agent_file()])  # no temporary file left

    def test_the_installed_copy_is_rewritten_only_when_it_differs(self):
        self.persona()
        self.run_cli("run", "reviewer", "x")
        first = self.agent_file().stat().st_mtime_ns
        os.utime(self.agent_file(), ns=(1, 1))
        self.run_cli("run", "reviewer", "x")
        self.assertEqual(self.agent_file().stat().st_mtime_ns, 1)
        self.persona(body="# Reviewer\nFind every defect.\n")
        self.run_cli("run", "reviewer", "x")
        self.assertIn("every defect", self.agent_file().read_text())
        self.assertNotEqual(self.agent_file().stat().st_mtime_ns, 1)
        self.assertGreater(first, 1)

    def test_direct_still_sends_the_tool_less_persona_and_installs_nothing(self):
        self.persona()
        (self.agents / "reviewer.md").write_text("Direct reviewer.")
        code, _, _ = self.run_cli("run", "reviewer", "x", "--direct", "--approved-usd", "2")
        self.assertEqual(code, 0)
        self.assertEqual(Stub.requests[0]["messages"][0]["content"], "Direct reviewer.")
        self.assertIsNone(self.call())
        self.assertFalse(self.installed.exists())

    def test_estimate_checks_the_persona_and_installs_nothing(self):
        self.persona()
        code, out, _ = self.run_cli("estimate", "reviewer", "x")
        self.assertEqual(code, 0)
        self.assertIn("agent orch-reviewer", out)
        self.assertFalse(self.installed.exists())
        self.persona(front=FRONT + "allowNonWorkspaceAccess: true\n")  # an unknown key
        self.assertEqual(self.run_cli("estimate", "reviewer", "x")[0], 1)  # the quote is not given for a bad persona

    def test_a_profile_without_a_harness_persona_is_a_usage_error(self):
        code, _, err = self.run_cli("run", "reviewer", "x")
        self.assertEqual(code, 2)
        self.assertIn("no harness persona", err)
        self.assertIsNone(self.call())

    def test_a_persona_that_would_loosen_the_limits_is_never_installed(self):
        bad = {
            "a write tool": FRONT.replace("  - run_command\n", "  - run_command\n  - write_to_file\n"),
            "no tools": FRONT.replace("  - view_file\n  - run_command\n", ""),
            "wrong name": FRONT.replace("orch-reviewer", "reviewer"),
            "callable as a subagent": FRONT.replace("subagent: false", "subagent: true"),
            "shell outside the sandbox": FRONT.replace("commandExecutionPolicy: sandbox", "commandExecutionPolicy: auto"),
            "a tool at another indent": FRONT.replace("  - run_command\n", "  - run_command\n    - write_to_file\n"),
            "a tool at no indent": FRONT.replace("  - run_command\n", "  - run_command\n- write_to_file\n"),
            "tools as a flow list": FRONT.replace("tools:\n  - view_file\n  - run_command\n",
                                                  "tools: [view_file, write_to_file]\n"),
            # These three pass every later check (allowed tools, subagent false), so only the strict reading stops them.
            "a first subagent line that a later one overrides": "subagent: true\n" + FRONT,
            "a flow list beside allowed items": FRONT.replace("tools:\n", "tools: [write_to_file]\n"),
            "a list item under another key": FRONT + "  - view_file\n",
            "a second subagent line": FRONT + "subagent: true\n",
            "a second policy line": FRONT + "commandExecutionPolicy: auto\n",
            "an unknown key": FRONT + "allowNonWorkspaceAccess: true\n",
        }
        for what, front in bad.items():
            self.persona(front=front)
            code, _, err = self.run_cli("run", "reviewer", "x")
            self.assertEqual(code, 1, what)
            self.assertIsNone(self.call(), what)
            self.assertFalse(self.installed.exists(), what)
        self.persona(front="name: orch-reviewer\n", body="")
        (self.agents / "harness" / "reviewer.md").write_text("# no frontmatter\n")
        self.assertEqual(self.run_cli("run", "reviewer", "x")[0], 1)

    def test_a_persona_holding_a_denied_address_is_not_sent(self):
        self.configure(egress_denylist=["planted@example.org"])
        self.persona(body="Write to planted@example.org.\n")
        self.assertEqual(self.run_cli("run", "reviewer", "x")[0], 5)
        self.assertIsNone(self.call())

    def test_every_shipped_agy_profile_has_a_valid_persona(self):
        shipped = Path(ac.__file__).resolve().parent.parent / "agents" / "harness"
        import gemini_exec as ge
        with_agy = [p for p, spec in ge.DEFAULTS["profiles"].items() if "agy" in (spec.get("routes") or [])]
        # `builder` joined on 2026-11-22 (Phase 3), and `default` is checked like the rest since it too is a persona.
        self.assertEqual(sorted(with_agy), ["adjudicator", "architect", "builder", "chat", "debugger", "default",
                                            "researcher", "reviewer"])
        writers = [p for p in with_agy if ge.DEFAULTS["profiles"][p].get("access") == "write"]
        self.assertEqual(writers, ["builder"])
        for profile in with_agy:
            text = ac.compose_persona(profile, shipped, write=profile in writers)
            self.assertIn("# How you work here", text, profile)
            self.assertIn(f"name: orch-{profile}\n", text, profile)
            self.assertEqual("write_to_file" in text.split("---\n")[1], profile in writers, profile)
            self.assertEqual("You cannot write" in text, profile not in writers, profile)
        self.assertNotIn("run_command", ac.compose_persona("chat", shipped).split("---\n")[1])


if __name__ == "__main__":
    import unittest
    unittest.main()
