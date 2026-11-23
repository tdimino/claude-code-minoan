"""Tests for gemini-orchestrator's client, packer and CLI.

Everything runs against a stub server on localhost: no request reaches OpenRouter and nothing is spent.

    uv run python -m unittest discover -s ~/.claude/skills/gemini-orchestrator/scripts/tests
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import citations as ct  # noqa: E402
import context_pack as cp  # noqa: E402
import gemini_exec as ge  # noqa: E402
import or_client as oc  # noqa: E402

NEON = {
    "id": "google/gemini-4-neon", "canonical_slug": "google/gemini-4-neon-20261118", "context_length": 1048576,
    "pricing": {"prompt": "0.000003", "completion": "0.000015"},
    "top_provider": {"max_completion_tokens": 943718},
    "reasoning": {"mandatory": True, "supported_efforts": ["xhigh", "high", "medium", "low"],
                  "default_effort": "medium"},
}
HYDROGEN = {
    "id": "google/gemini-4-hydrogen", "context_length": 1048576,
    "pricing": {"prompt": "0.0000015", "completion": "0.0000075"},
    "top_provider": {"max_completion_tokens": 943718},
    "reasoning": {"mandatory": True, "supported_efforts": ["high", "medium", "low"], "default_effort": "medium"},
}
TINY = {
    "id": "google/gemini-tiny", "context_length": 2000, "pricing": {"prompt": "0.000001", "completion": "0.000001"},
    "top_provider": {"max_completion_tokens": 1000}, "reasoning": {"supported_efforts": ["low"]},
}
USAGE = {"prompt_tokens": 120, "completion_tokens": 40, "cost": 0.00096,
         "completion_tokens_details": {"reasoning_tokens": 25}, "prompt_tokens_details": {"cached_tokens": 0}}


def sse(*chunks) -> bytes:
    return "".join(f"data: {json.dumps(c) if not isinstance(c, str) else c}\n\n" for c in chunks).encode()


def chunk(text=None, *, finish=None, usage=None, model="google/gemini-4-neon-20261118", **extra) -> dict:
    c = {"id": "gen-1", "model": model, "provider": "Google", "choices": [{"delta": {}, "finish_reason": finish}]}
    if text is not None:
        c["choices"][0]["delta"]["content"] = text
    if usage:
        c["usage"] = usage
    c.update(extra)
    return c


class Stub(BaseHTTPRequestHandler):
    scenario = "ok"
    requests: list = []
    lookups: list = []
    calls = 0

    def log_message(self, *a):  # keep test output clean
        pass

    def _send(self, status: int, body: bytes, kind: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/generation"):
            type(self).lookups.append(self.path)
            return self._send(200, json.dumps({"data": {"id": "gen-1", "total_cost": 0.0123, "latency": 9000,
                                                        "generation_time": 9500, "secret_field": "x"}}).encode())
        if self.path.startswith("/credits"):
            return self._send(200, json.dumps({"data": {"total_credits": 120, "total_usage": 109.55}}).encode())
        self._send(200, json.dumps({"data": [NEON, HYDROGEN, TINY]}).encode())

    def do_POST(self):
        cls = type(self)
        cls.calls += 1
        cls.requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        cls.headers_seen = dict(self.headers)
        s = cls.scenario
        if s == "http402":
            return self._send(402, json.dumps({"error": {"message": "Insufficient credits"}}).encode())
        if s == "flaky" and cls.calls == 1:
            return self._send(503, json.dumps({"error": {"message": "overloaded"}}).encode())
        if s == "empty":
            body = sse(chunk(finish="length", usage=USAGE), "[DONE]")
        elif s == "midstream_error":
            body = sse(chunk("Half an"), {"id": "gen-1", "error": {"message": "provider dropped"},
                                         "choices": [{"delta": {}, "finish_reason": "error"}]}, "[DONE]")
        elif s == "answer":
            body = sse(chunk(cls.answer), chunk(finish="stop", usage=USAGE), "[DONE]")
        elif s == "wrong_model":
            body = sse(chunk("Hi", model="openai/gpt-x"), chunk(finish="stop", usage=USAGE, model="openai/gpt-x"),
                       "[DONE]")
        elif s == "keepalive":
            body = b": OPENROUTER PROCESSING\n\n" + sse(chunk("Hello")) + b": OPENROUTER PROCESSING\n\n" + \
                sse(chunk(" world"), chunk(finish="stop", usage=USAGE), "[DONE]")
        elif s == "reasoning":
            think = {"id": "gen-1", "model": "google/gemini-4-neon-20261118", "provider": "Google",
                     "choices": [{"delta": {"reasoning": "thinking"}, "finish_reason": None}]}
            body = sse(think, think, chunk("Hello"), chunk(finish="stop", usage=USAGE), "[DONE]")
        elif s == "no_finish":
            body = sse(chunk("Cut"))
        else:
            body = sse(chunk("Hello"), chunk(" world"), chunk(finish="stop", usage=USAGE), "[DONE]")
        self._send(200, body, "text/event-stream")


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Stub.scenario, Stub.requests, Stub.calls, Stub.lookups = "ok", [], 0, []
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        self.work, self.data, self.agents = root / "work", root / "data", root / "agents"
        for d in (self.work, self.data, self.agents):
            d.mkdir()
        self.config = root / "config.json"
        # A default call (Neon at medium, 40,000 max_tokens) has a ceiling of $0.60, over the shipped $0.50 gate.
        # Tests that are not about the gate run under a gate of $1; the gate tests write their own config.
        # These tests are about the direct route, so it is the default here; profiles that also have the agy route
        # would otherwise start the Antigravity CLI. test_agy_route.py sets its own.
        self.config.write_text(json.dumps({"gate_usd": 1.0, "default_route": "openrouter"}))
        env = {"OPENROUTER_BASE_URL": f"http://127.0.0.1:{self.server.server_address[1]}",
               "OPENROUTER_API_KEY": "test-key", "GEMINI_ORCH_DATA_DIR": str(self.data),
               "GEMINI_ORCH_AGENTS": str(self.agents), "GEMINI_ORCH_CONFIG": str(self.config),
               "GEMINI_ORCH_BACKOFF": "0"}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        # No real address source is consulted in tests; each test names its own.
        deny = mock.patch.object(cp, "deny_addresses", lambda extra=None: sorted(extra or []))
        deny.start()
        self.addCleanup(deny.stop)
        old = os.getcwd()
        os.chdir(self.work)
        self.addCleanup(os.chdir, old)

    def run_cli(self, *argv) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ge.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def write(self, name: str, text: str) -> Path:
        p = self.work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def ledger(self) -> list[dict]:
        path = self.data / "ledger.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


class FailureLogTests(Base):
    def failures(self) -> list[dict]:
        path = self.data / "failures.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_a_good_call_logs_no_failure_and_the_ledger_gains_its_seconds(self):
        code, _, _ = self.run_cli("run", "raw", "Say hello.")
        self.assertEqual(code, 0)
        self.assertEqual(self.failures(), [])
        self.assertEqual(Stub.lookups, [])
        entry = self.ledger()[-1]
        self.assertIsInstance(entry["seconds"], float)
        self.assertIsInstance(entry["first_text_seconds"], float)

    def test_a_stream_without_a_finish_is_logged_with_timings_and_openrouters_record(self):
        Stub.scenario = "no_finish"
        code, _, err = self.run_cli("run", "raw", "Say hello.", "--reasoning", "low")
        self.assertEqual(code, 1)
        (f,) = self.failures()
        self.assertEqual((f["stage"], f["exit_code"], f["profile"], f["effort"]), ("during the stream", 1, "raw", "low"))
        self.assertIn("without a finish reason", f["status"])
        self.assertEqual((f["timing"]["data_chunks"], f["timing"]["keepalives"], f["timing"]["done"]), (1, 0, False))
        self.assertIsNotNone(f["timing"]["first_text_s"])
        self.assertEqual(f["answer_chars"], 3)
        self.assertEqual(f["openrouter_record"]["total_cost"], 0.0123)
        self.assertNotIn("secret_field", f["openrouter_record"])
        self.assertEqual(Stub.lookups, ["/generation?id=gen-1"])
        self.assertIn("FAILURE_LOG=", err)
        self.assertIn("$0.0123 charged", err)

    def test_an_empty_answer_is_logged_after_the_stream(self):
        Stub.scenario = "empty"
        code, _, _ = self.run_cli("run", "raw", "Say hello.")
        self.assertEqual(code, 4)
        (f,) = self.failures()
        self.assertEqual((f["stage"], f["exit_code"], f["finish"]), ("after the stream", 4, "length"))
        self.assertEqual(f["usage"]["completion_tokens_details"]["reasoning_tokens"], 25)
        self.assertEqual(f["timing"]["first_text_s"], None)

    def test_keepalives_are_counted(self):
        Stub.scenario = "keepalive"
        self.assertEqual(self.run_cli("run", "raw", "Say hello.")[0], 0)
        result = oc.chat({"model": "google/gemini-4-neon", "messages": []}, "test-key")
        self.assertEqual((result.timing["keepalives"], result.timing["done"]), (2, True))

    def test_stream_reasoning_asks_for_the_text_counts_it_and_keeps_none(self):
        Stub.scenario = "reasoning"
        code, out, _ = self.run_cli("run", "raw", "Say hello.", "--reasoning", "low", "--stream-reasoning")
        self.assertEqual(code, 0)
        self.assertEqual(Stub.requests[-1]["reasoning"], {"effort": "low", "exclude": False})
        self.assertEqual(out.strip(), "Hello")
        entry = self.ledger()[-1]
        self.assertEqual((entry["stream_reasoning"], entry["reasoning_chunks"]), (True, 2))
        written = Path(entry["output"]).read_text()
        self.assertNotIn("thinking", written)

    def test_reasoning_stays_excluded_without_the_flag(self):
        self.run_cli("run", "raw", "Say hello.", "--reasoning", "low")
        self.assertEqual(Stub.requests[-1]["reasoning"], {"effort": "low", "exclude": True})
        self.assertEqual(self.ledger()[-1]["stream_reasoning"], False)

    def test_a_refusal_before_the_stream_is_logged_with_its_http_status(self):
        Stub.scenario = "http402"
        code, _, err = self.run_cli("run", "raw", "Say hello.")
        self.assertEqual(code, 1)
        (f,) = self.failures()
        self.assertEqual((f["stage"], f["http_status"]), ("before the stream", 402))
        self.assertIn("Insufficient credits", f["status"])
        self.assertEqual(Stub.lookups, [])
        self.assertIn("FAILURE_LOG=", err)

    def test_the_log_never_holds_the_key_or_the_brief(self):
        Stub.scenario = "no_finish"
        self.run_cli("run", "raw", "A brief with a private sentence in it.")
        text = (self.data / "failures.jsonl").read_text()
        self.assertNotIn("test-key", text)
        self.assertNotIn("private sentence", text)

    def test_spend_shows_the_failure_count_and_the_balance(self):
        Stub.scenario = "no_finish"
        self.run_cli("run", "raw", "Say hello.")
        code, out, _ = self.run_cli("spend")
        self.assertEqual(code, 0)
        self.assertIn("failed 1 calls recorded", out)
        self.assertIn("OpenRouter balance $10.45", out)

    def test_failures_command_lists_them(self):
        code, out, _ = self.run_cli("failures")
        self.assertEqual(code, 0)
        self.assertIn("no failures recorded", out)
        Stub.scenario = "no_finish"
        self.run_cli("run", "raw", "Say hello.")
        Stub.scenario = "http402"
        self.run_cli("run", "raw", "Say hello.")
        code, out, _ = self.run_cli("failures", "--last", "1")
        self.assertIn("before the stream", out)
        self.assertNotIn("during the stream", out)
        self.assertIn("1 shown", out)
        code, out, _ = self.run_cli("failures", "--json")
        self.assertEqual([json.loads(line)["stage"] for line in out.splitlines()],
                         ["during the stream", "before the stream"])


class RunTests(Base):
    def test_ok_writes_answer_trailer_manifest_and_ledger(self):
        self.write("a.txt", "alpha\nbeta\n")
        code, out, err = self.run_cli("run", "raw", "Say hello", "--context", "a.txt")
        self.assertEqual(code, ge.EXIT_OK, err)
        self.assertEqual(out.strip(), "Hello world")
        produced = list((self.work / ".subdaimon-output").glob("gemini-raw-*.md"))
        self.assertEqual(len(produced), 1)
        text = produced[0].read_text()
        self.assertIn("Hello world", text)
        self.assertIn("status=ok", text)
        self.assertIn("served=google/gemini-4-neon-20261118", text)
        self.assertIn("provider=Google", text)
        self.assertIn("cost=$0.0010", text)
        self.assertIn("reasoning=25", text)
        manifest = json.loads(produced[0].with_suffix(".manifest.json").read_text())
        self.assertEqual([f["path"] for f in manifest["files"]], ["a.txt"])
        self.assertEqual(len(manifest["files"][0]["sha256"]), 64)
        entry = self.ledger()[0]
        self.assertEqual(entry["cost"], 0.00096)
        self.assertEqual(entry["model"], "google/gemini-4-neon")
        self.assertEqual(entry["generation_id"], "gen-1")

    def test_request_body(self):
        self.write("a.txt", "alpha\nbeta\n")
        self.run_cli("run", "raw", "Say hello", "--context", "a.txt", "--reasoning", "low", "--answer-tokens", "800")
        body = Stub.requests[0]
        self.assertEqual(body["model"], "google/gemini-4-neon")
        self.assertEqual(body["reasoning"], {"effort": "low", "exclude": True})
        self.assertEqual(body["max_tokens"], 8800)  # 800 for the answer + 8,000 allowed for reasoning at low
        self.assertEqual(body["provider"], {"data_collection": "deny", "require_parameters": True})
        self.assertTrue(body["stream"])
        self.assertNotIn("models", body)
        self.assertNotIn("plugins", body)
        user = body["messages"][-1]["content"]
        self.assertIn('<file path="a.txt" lines="2">', user)
        self.assertIn("1| alpha\n2| beta", user)
        self.assertTrue(user.rstrip().endswith("<task>\nSay hello\n</task>"))
        self.assertLess(user.index("<context_pack"), user.index("<task>"))  # pack first, brief last

    def test_headers_carry_no_contact_detail(self):
        self.run_cli("run", "raw", "Say hello")
        self.assertEqual(Stub.headers_seen["User-Agent"], "gemini-orchestrator/0.1")
        self.assertNotIn("@", " ".join(f"{k}: {v}" for k, v in Stub.headers_seen.items()))

    def test_persona_becomes_system_message(self):
        (self.agents / "reader.md").write_text("You have no tools.")
        self.run_cli("run", "reader", "Read it")
        self.assertEqual(Stub.requests[0]["messages"][0], {"role": "system", "content": "You have no tools."})

    def test_shared_rules_come_before_the_persona(self):
        (self.agents / "_shared.md").write_text("Shared rules.")
        (self.agents / "reader.md").write_text("Reader role.")
        self.run_cli("run", "reader", "Read it")
        self.assertEqual(Stub.requests[0]["messages"][0]["content"], "Shared rules.\n\nReader role.")

    def test_every_shipped_profile_has_a_persona(self):
        shipped = Path(ge.__file__).resolve().parent.parent / "agents"
        for profile, spec in ge.DEFAULTS["profiles"].items():
            # A persona file is the direct route's system message. A profile with only the agy route (`default`,
            # which runs agy's own agent) never reads one.
            if profile != "raw" and "openrouter" in (spec.get("routes") or ["openrouter"]):
                self.assertTrue((shipped / f"{profile}.md").exists(), profile)
        self.assertTrue((shipped / "_shared.md").exists())

    def test_profile_without_persona_is_usage_error(self):
        code, _, err = self.run_cli("run", "reviewer", "Review")
        self.assertEqual(code, ge.EXIT_USAGE)
        self.assertIn("no persona file", err)
        self.assertEqual(Stub.calls, 0)

    def test_keepalive_comments_are_ignored(self):
        Stub.scenario = "keepalive"
        code, out, _ = self.run_cli("run", "raw", "Say hello")
        self.assertEqual(code, ge.EXIT_OK)
        self.assertEqual(out.strip(), "Hello world")

    def test_empty_answer_is_exit_4_and_not_retried(self):
        Stub.scenario = "empty"
        code, out, err = self.run_cli("run", "raw", "Say hello")
        self.assertEqual(code, ge.EXIT_EMPTY)
        self.assertEqual(Stub.calls, 1)
        self.assertIn("--reasoning-tokens 50", err)  # twice the 25 reasoning tokens the stub reported
        self.assertEqual(self.ledger()[0]["cost"], 0.00096)  # the spend is recorded even though nothing came back

    def test_midstream_error_keeps_partial_text(self):
        Stub.scenario = "midstream_error"
        code, _, err = self.run_cli("run", "raw", "Say hello")
        self.assertEqual(code, ge.EXIT_API)
        self.assertEqual(Stub.calls, 1)  # a broken stream may have been billed, so it is never retried
        produced = next((self.work / ".subdaimon-output").glob("*.md")).read_text()
        self.assertIn("Half an", produced)
        self.assertIn("status=partial (provider dropped)", produced)

    def test_stream_without_finish_reason_is_partial(self):
        Stub.scenario = "no_finish"
        code, _, _ = self.run_cli("run", "raw", "Say hello")
        self.assertEqual(code, ge.EXIT_API)

    def test_wrong_model_is_exit_6(self):
        Stub.scenario = "wrong_model"
        code, _, err = self.run_cli("run", "raw", "Say hello")
        self.assertEqual(code, ge.EXIT_MODEL)
        self.assertIn("served by a different model", err)

    def test_http_402_is_not_retried(self):
        Stub.scenario = "http402"
        code, _, err = self.run_cli("run", "raw", "Say hello")
        self.assertEqual(code, ge.EXIT_API)
        self.assertEqual(Stub.calls, 1)
        self.assertIn("Insufficient credits", err)
        self.assertEqual(self.ledger(), [])

    def test_http_503_before_any_text_is_retried(self):
        Stub.scenario = "flaky"
        code, out, _ = self.run_cli("run", "raw", "Say hello")
        self.assertEqual(code, ge.EXIT_OK)
        self.assertEqual(Stub.calls, 2)
        self.assertEqual(out.strip(), "Hello world")

    def test_session_carries_the_conversation(self):
        session = str(self.work / "s.json")
        self.run_cli("run", "raw", "First", "--session", session)
        self.run_cli("run", "raw", "Second", "--session", session)
        roles = [m["role"] for m in Stub.requests[1]["messages"]]
        self.assertEqual(roles, ["user", "assistant", "user"])
        self.assertEqual(Stub.requests[1]["messages"][1]["content"], "Hello world")

    def test_cache_marks_the_pack(self):
        self.write("a.txt", "alpha\n")
        self.run_cli("run", "raw", "Q", "--context", "a.txt", "--cache")
        parts = Stub.requests[0]["messages"][-1]["content"]
        self.assertEqual(parts[0]["cache_control"], {"type": "ephemeral"})
        self.assertIn("<context_pack", parts[0]["text"])
        self.assertNotIn("cache_control", parts[-1])

    def test_pdf_pins_the_native_engine(self):
        self.write("doc.pdf", "%PDF-1.4\n1 0 obj << /Type /Pages >>\n2 0 obj << /Type /Page >>\n3 0 obj << /Type /Page >>\n")
        self.run_cli("run", "raw", "Read", "--attach", "doc.pdf")
        body = Stub.requests[0]
        self.assertEqual(body["plugins"], [{"id": "file-parser", "pdf": {"engine": "native"}}])
        kinds = [p["type"] for p in body["messages"][-1]["content"]]
        self.assertEqual(kinds, ["file", "text"])

    def test_schema_sets_response_format(self):
        self.write("s.schema.json", json.dumps({"type": "object", "properties": {"a": {"type": "string"}}}))
        self.run_cli("run", "raw", "Q", "--schema", "s.schema.json")
        fmt = Stub.requests[0]["response_format"]
        self.assertEqual(fmt["type"], "json_schema")
        self.assertTrue(fmt["json_schema"]["strict"])
        with_schema, without = self.ledger()[0]["estimated_input_tokens"], None
        self.run_cli("run", "raw", "Q")
        without = self.ledger()[1]["estimated_input_tokens"]
        self.assertGreater(with_schema, without + 50)  # the schema is billed as input, so the quote counts it


class GateTests(Base):
    def test_over_gate_sends_nothing_and_quotes(self):
        # xhigh: 8,000 answer + 64,000 reasoning = 72,000 max_tokens x $15/M = $1.08
        code, _, err = self.run_cli("run", "raw", "Think hard", "--reasoning", "xhigh")
        self.assertEqual(code, ge.EXIT_GATE)
        self.assertEqual(Stub.calls, 0)
        self.assertIn("max_tokens 72,000", err)
        self.assertIn("--approved-usd 1.09", err)
        self.assertEqual(self.ledger(), [])

    def test_approval_below_the_ceiling_is_refused(self):
        code, _, _ = self.run_cli("run", "raw", "Think hard", "--reasoning", "xhigh", "--approved-usd", "1.00")
        self.assertEqual(code, ge.EXIT_GATE)
        self.assertEqual(Stub.calls, 0)

    def test_approval_at_the_ceiling_sends(self):
        code, _, _ = self.run_cli("run", "raw", "Think hard", "--reasoning", "xhigh", "--approved-usd", "1.09")
        self.assertEqual(code, ge.EXIT_OK)
        self.assertEqual(Stub.calls, 1)

    def test_project_spend_rule_makes_the_gate_zero(self):
        rule = self.work / ".claude/rules/paid-api-spend.md"
        rule.parent.mkdir(parents=True)
        rule.write_text("quote first")
        sub = self.work / "deep/er"
        sub.mkdir(parents=True)
        os.chdir(sub)  # the rule is found from below
        code, _, err = self.run_cli("run", "raw", "Tiny", "--reasoning", "low", "--answer-tokens", "100")
        self.assertEqual(code, ge.EXIT_GATE)
        self.assertEqual(Stub.calls, 0)
        self.assertIn("spend rule", err)

    def test_daily_ceiling_blocks_even_with_approval(self):
        self.config.write_text(json.dumps({"daily_ceiling_usd": 0.05}))
        code, _, err = self.run_cli("run", "raw", "Say hello", "--approved-usd", "5")
        self.assertEqual(code, ge.EXIT_GATE)
        self.assertEqual(Stub.calls, 0)
        self.assertIn("Daily ceiling", err)

    def test_config_gate_is_read(self):
        self.config.write_text(json.dumps({"gate_usd": 0.01}))
        code, _, _ = self.run_cli("run", "raw", "Say hello")
        self.assertEqual(code, ge.EXIT_GATE)

    def test_estimate_sends_nothing(self):
        code, out, _ = self.run_cli("estimate", "raw", "Think hard", "--reasoning", "xhigh")
        self.assertEqual(code, ge.EXIT_OK)
        self.assertEqual(Stub.calls, 0)
        self.assertIn("ceiling $1.08", out)

    def test_effort_the_model_rejects(self):
        code, _, err = self.run_cli("run", "raw", "Q", "--model", "hydrogen", "--reasoning", "xhigh")
        self.assertEqual(code, ge.EXIT_USAGE)
        self.assertIn("accepted: high, medium, low", err)
        self.assertEqual(Stub.calls, 0)

    def test_no_reasoning_on_a_mandatory_model(self):
        code, _, err = self.run_cli("run", "raw", "Q", "--reasoning", "none")
        self.assertEqual(code, ge.EXIT_USAGE)
        self.assertIn("cannot run without reasoning", err)

    def test_unknown_model(self):
        code, _, err = self.run_cli("run", "raw", "Q", "--model", "xenon")
        self.assertEqual(code, ge.EXIT_USAGE)
        self.assertIn("not in today's OpenRouter list", err)

    def test_pack_larger_than_the_window(self):
        self.write("big.txt", "word " * 4000)
        code, _, err = self.run_cli("run", "raw", "Q", "--model", "google/gemini-tiny", "--context", "big.txt")
        self.assertEqual(code, ge.EXIT_USAGE)
        self.assertIn("big.txt", err)
        self.assertIn("window", err)


class EgressTests(Base):
    def setUp(self):
        super().setUp()
        self.config.write_text(json.dumps({"egress_denylist": ["person@example.org"], "gate_usd": 1.0}))

    def test_denied_address_in_a_packed_file(self):
        self.write("notes.md", "line one\ncontact: Person@Example.org\n")
        code, _, err = self.run_cli("run", "raw", "Q", "--context", "notes.md")
        self.assertEqual(code, ge.EXIT_EGRESS)
        self.assertEqual(Stub.calls, 0)
        self.assertIn("notes.md:2  denied email address", err)
        self.assertNotIn("example.org", err.lower())  # the report names the place, not the address

    def test_denied_address_in_the_brief(self):
        code, _, err = self.run_cli("run", "raw", "Write to person@example.org")
        self.assertEqual(code, ge.EXIT_EGRESS)
        self.assertIn("<brief>:1", err)

    def test_url_encoded_address(self):
        self.write("u.txt", "https://x.test/?from=person%40example.org\n")
        code, _, _ = self.run_cli("run", "raw", "Q", "--context", "u.txt")
        self.assertEqual(code, ge.EXIT_EGRESS)

    def test_redact_replaces_the_address_and_sends(self):
        self.write("notes.md", "contact: Person@Example.org\n")
        code, _, _ = self.run_cli("run", "raw", "Q", "--context", "notes.md", "--redact")
        self.assertEqual(code, ge.EXIT_OK)
        sent = json.dumps(Stub.requests[0])
        self.assertNotIn("example.org", sent)
        self.assertIn("[email]", sent)

    def test_secret_in_a_packed_file(self):
        self.write("conf.py", "x = 1\nKEY = 'sk-or-v1-" + "a" * 40 + "'\n")
        code, _, err = self.run_cli("run", "raw", "Q", "--context", "conf.py")
        self.assertEqual(code, ge.EXIT_EGRESS)
        self.assertIn("conf.py:2  OpenRouter key", err)
        self.assertNotIn("a" * 40, err)

    def test_redact_does_not_excuse_a_secret(self):
        self.write("conf.py", "API_TOKEN = 'abcdefghijklmnop1234'\n")
        code, _, _ = self.run_cli("run", "raw", "Q", "--context", "conf.py", "--redact")
        self.assertEqual(code, ge.EXIT_EGRESS)

    def test_allow_exempts_a_file_from_secret_patterns_only(self):
        self.write("doc.md", "Set OPENROUTER_API_KEY=your_key_goes_here_1234\n")
        code, _, _ = self.run_cli("run", "raw", "Q", "--context", "doc.md", "--allow", "doc.md")
        self.assertEqual(code, ge.EXIT_OK)
        self.write("doc2.md", "first line\nperson@example.org\n")  # every line of an exempt file is still read
        code, _, _ = self.run_cli("run", "raw", "Q", "--context", "doc2.md", "--allow", "doc2.md")
        self.assertEqual(code, ge.EXIT_EGRESS)

    def test_env_file_named_explicitly_is_refused(self):
        self.write(".env", "A=1\n")
        code, _, err = self.run_cli("run", "raw", "Q", "--context", ".env")
        self.assertEqual(code, ge.EXIT_USAGE)
        self.assertIn("never packed", err)

    def test_env_file_inside_a_folder_is_left_out(self):
        self.write("proj/main.py", "print('hi')\n")
        self.write("proj/secrets.env", "A=1\n")
        self.write("proj/blob.bin", "a\0b")
        code, _, err = self.run_cli("run", "raw", "Q", "--context", "proj")
        self.assertEqual(code, ge.EXIT_OK, err)
        sent = Stub.requests[0]["messages"][-1]["content"]
        self.assertIn("proj/main.py", sent)
        self.assertNotIn("secrets.env", sent)
        self.assertIn("proj/secrets.env (credentials file)", err)
        self.assertIn("proj/blob.bin (binary)", err)


class CitationTests(Base):
    TEXT = ("# Dossier\n"                                  # 1
            "The root k-n-s means to gather.\n"            # 2
            "Astour reads Membliaros as waters without light.\n"   # 3
            "\n"                                           # 4
            "Hebrew: תְּהוֹם is Tehom; transliterated ḥayyā.\n"    # 5
            "A closing line about purple dye.\n")          # 6

    def verdicts(self, answer: str) -> list[str]:
        self.write("d.md", self.TEXT)
        files, _ = cp.collect(["d.md"])
        return [c.verdict for c in ct.check_answer(answer, cp.manifest(files))]

    def test_exact_quotation_in_its_lines(self):
        self.assertEqual(self.verdicts('[d.md:L2] "The root k-n-s means to gather."'), ["verified"])

    def test_span_en_dash_and_curly_quotes(self):
        self.assertEqual(self.verdicts("[d.md:L2–L3] “means to gather. Astour reads Membliaros”"), ["verified"])

    def test_one_line_off_still_verifies_two_does_not(self):
        self.assertEqual(self.verdicts('[d.md:L4] "waters without light"'), ["verified"])
        self.assertEqual(self.verdicts('[d.md:L6] "waters without light"'), ["misplaced"])

    def test_invented_quotation(self):
        self.assertEqual(self.verdicts('[d.md:L2] "The root k-n-s means to scatter."'), ["not_found"])

    def test_ellipsis_joins_pieces_in_order(self):
        self.assertEqual(self.verdicts('[d.md:L3] "Astour reads ... without light"'), ["verified"])
        self.assertEqual(self.verdicts('[d.md:L3] "without light … Astour reads"'), ["not_found"])

    def test_nfd_quotation_matches_nfc_file(self):
        import unicodedata
        quote = unicodedata.normalize("NFD", "תְּהוֹם is Tehom; transliterated ḥayyā")
        self.assertNotEqual(quote, unicodedata.normalize("NFC", quote))
        self.assertEqual(self.verdicts(f'[d.md:L5] "{quote}"'), ["verified"])

    def test_unknown_file_and_out_of_range(self):
        self.assertEqual(self.verdicts('[other.md:L2] "The root"'), ["unknown_file"])
        self.assertEqual(self.verdicts('[d.md:L40] "The root"'), ["out_of_range"])

    def test_bare_citation_is_located_and_not_counted(self):
        self.write("d.md", self.TEXT)
        files, _ = cp.collect(["d.md"])
        checks = ct.check_answer('See [d.md:L2] and [d.md:L3] "waters without light".', cp.manifest(files))
        self.assertEqual([c.verdict for c in checks], ["located", "verified"])
        self.assertEqual(ct.summarise(checks), ("1/1", []))

    def test_run_reports_citations_in_trailer_and_ledger(self):
        self.write("d.md", self.TEXT)
        Stub.scenario = "answer"
        Stub.answer = ('True: [d.md:L3] "waters without light". '
                       'False: [d.md:L6] "A closing line about saffron."')
        code, _, err = self.run_cli("run", "raw", "Q", "--context", "d.md")
        self.assertEqual(code, ge.EXIT_OK)
        self.assertIn("citations=1/2", err)
        self.assertIn("not_found", err)
        self.assertIn("saffron", err)
        self.assertEqual(self.ledger()[0]["citations"], "1/2")

    def test_verify_command_and_changed_file(self):
        target = self.write("d.md", self.TEXT)
        Stub.scenario = "answer"
        Stub.answer = '[d.md:L3] "waters without light"'
        self.run_cli("run", "raw", "Q", "--context", "d.md", "--out", "out.md")
        code, out, _ = self.run_cli("verify", "out.md")
        self.assertEqual(code, ge.EXIT_OK)
        self.assertIn("citations verified: 1/1", out)
        target.write_text(self.TEXT + "edited after packing\n", encoding="utf-8")
        code, out, _ = self.run_cli("verify", "out.md")
        self.assertNotEqual(code, ge.EXIT_OK)
        self.assertIn("file_changed", out)  # a changed file is reported as changed, not as a false quotation


class UnitTests(Base):
    def test_max_tokens_leaves_room_for_the_answer(self):
        self.assertEqual(oc.max_tokens_for(8000, "high", NEON), 56000)
        self.assertEqual(oc.max_tokens_for(8000, "medium", NEON), 40000)
        self.assertEqual(oc.max_tokens_for(8000, None, NEON), 8000)
        self.assertEqual(oc.max_tokens_for(500, "high", NEON, 1000), 1500)  # --reasoning-tokens overrides
        self.assertEqual(oc.max_tokens_for(8000, "low", TINY), 1000)  # capped at the model's maximum

    def test_aliases_resolve_against_the_live_list(self):
        models = oc.fetch_models()
        self.assertEqual(oc.resolve_model("neon", models)["id"], "google/gemini-4-neon")
        self.assertEqual(oc.resolve_model("google/gemini-4-hydrogen", models)["id"], "google/gemini-4-hydrogen")
        with self.assertRaises(oc.ClientError):
            oc.resolve_model("carbon", models)  # aliased, but absent from this list: fails loudly

    def test_model_list_is_cached(self):
        oc.fetch_models()
        with mock.patch.object(oc.urllib.request, "urlopen", side_effect=AssertionError("network used")):
            self.assertEqual(len(oc.fetch_models()), 3)

    def test_estimate_by_content_class(self):
        # Ratios follow the 2026-11-20 pilot: prose 2.9, JSON and code 1.95, non-ASCII 2.0 bytes per token.
        prose = "the quick brown fox " * 145           # 2,900 bytes
        dense = '{"a": 1, "b": [2, 3]}\n' * 100         # 2,200 bytes of punctuation and digits
        hebrew = "שָׁלוֹם " * 200
        self.assertEqual(cp.estimate_tokens(prose), 1000)
        self.assertEqual(cp.estimate_tokens(dense), -(-2200 // 1.95))
        self.assertEqual(cp.estimate_tokens(hebrew), -(-len(hebrew.encode()) // 2.0))
        code = "12| result = compute(value, other[0]) + offset[1] * 2\n" * 50  # 69% letters and spaces
        self.assertEqual(cp.estimate_tokens(code), -(-len(code) // 2.5))
        self.assertEqual(cp.estimate_tokens(""), 0)

    def test_each_file_is_estimated_by_its_own_class(self):
        self.write("a.md", "the quick brown fox jumps over the lazy dog " * 200)
        self.write("b.json", '{"a": 1, "b": [2, 3], "c": {"d": 4}}\n' * 240)
        self.run_cli("run", "raw", "Q", "--context", "a.md", "b.json")
        files, _ = cp.collect(["a.md", "b.json"])
        separately = sum(cp.estimate_tokens(cp.render([f])) for f in files)
        together = cp.estimate_tokens(cp.render(files))
        self.assertNotEqual(separately, together)
        estimated = self.ledger()[0]["estimated_input_tokens"]
        self.assertAlmostEqual(estimated, (separately + cp.estimate_tokens("<task>\nQ\n</task>")) * 1.2, delta=2)

    def test_pack_is_sorted_numbered_and_deduplicated(self):
        self.write("b.txt", "two\n")
        self.write("a.txt", "one\nlast without newline")
        self.write("empty.txt", "")
        files, skipped = cp.collect(["b.txt", "a.txt", "a.txt", "empty.txt"])
        self.assertEqual([f.path for f in files], ["a.txt", "b.txt", "empty.txt"])
        self.assertEqual([f.lines for f in files], [2, 1, 0])
        self.assertIn("2| last without newline", cp.render(files))

    def test_path_with_spaces_and_glob(self):
        self.write("my notes/x y.md", "hello\n")
        files, _ = cp.collect(["my notes/*.md"])
        self.assertEqual([f.path for f in files], ["my notes/x y.md"])

    def test_missing_path(self):
        code, _, err = self.run_cli("run", "raw", "Q", "--context", "nope.txt")
        self.assertEqual(code, ge.EXIT_USAGE)
        self.assertIn("nope.txt", err)

    def test_large_file_needs_the_flag(self):
        self.write("large.txt", "x" * (cp.MAX_FILE_BYTES + 1))
        files, skipped = cp.collect(["large.txt"])
        self.assertEqual(files, [])
        self.assertIn("2 MB", skipped[0][1])
        files, _ = cp.collect(["large.txt"], allow_large=True)
        self.assertEqual(len(files), 1)

    def test_ledger_survives_a_malformed_line(self):
        (self.data / "ledger.jsonl").write_text('{"time": "2026-11-20T10:00:00", "cost": 0.25}\nnot json\n'
                                                 '{"time": "2026-11-19T10:00:00", "cost": 1.0}\n')
        entries = ge.read_ledger()
        self.assertEqual(len(entries), 2)
        self.assertEqual(ge.spent(entries, "2026-11-20"), 0.25)
        self.assertEqual(ge.spent(entries, "2026-11"), 1.25)

    def test_models_command_lists_aliased_models(self):
        code, out, _ = self.run_cli("models")
        self.assertEqual(code, ge.EXIT_OK)
        self.assertIn("neon", out)
        self.assertIn("$3.000", out)
        self.assertIn("$15.000", out)
        self.assertNotIn("gemini-tiny", out)

    def test_audio_attachment_is_refused_for_now(self):
        self.write("a.mp3", "x")
        code, _, err = self.run_cli("run", "raw", "Q", "--attach", "a.mp3")
        self.assertEqual(code, ge.EXIT_USAGE)
        self.assertIn("P8", err)


if __name__ == "__main__":
    unittest.main()
