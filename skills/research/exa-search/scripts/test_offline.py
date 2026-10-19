#!/usr/bin/env python3
"""
Offline tests for the exa-search scripts: no API key, no network.

Every request goes through a patched `requests.post`/`requests.get` that records
the URL, headers, and JSON body and returns a canned response (often a real
fixture from scripts/fixtures/, captured from the live API on 2026-10-19).

Run directly (python3 test_offline.py) or via `test_exa.py --quick`.
"""

import contextlib
import importlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURES = SCRIPT_DIR / "fixtures"
sys.path.insert(0, str(SCRIPT_DIR))

import requests  # noqa: E402


def fixture(name: str) -> Any:
    path = FIXTURES / name
    return path.read_text() if path.suffix == ".sse" else json.loads(path.read_text())


NOT_JSON = object()


class FakeResponse:
    """Mimics requests.Response, including its ISO-8859-1 fallback for charset-less text/* streams."""

    def __init__(self, body: Any = None, status: int = 200, lines: Optional[List[str]] = None,
                 text: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        self.body = {"results": []} if body is None else body
        self.status_code = status
        self.lines = lines or []
        self.text = text if text is not None else json.dumps(self.body)
        self.headers = headers or {}
        self.encoding: Optional[str] = None  # text/event-stream without charset → requests guesses ISO-8859-1

    def json(self):
        if self.body is NOT_JSON:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self.body

    def iter_lines(self, decode_unicode: bool = False):
        for line in self.lines:
            raw = line.encode("utf-8")
            yield raw.decode(self.encoding or "ISO-8859-1") if decode_unicode else raw

    def close(self):
        pass


class Capture:
    """Patch requests.post/get; record calls; serve canned responses in order."""

    def __init__(self, *responses: Any):
        self.responses = list(responses)
        self.strict = bool(responses)  # given responses → an extra request is a test failure
        self.calls: List[Dict[str, Any]] = []

    def _fake(self, method: str) -> Callable:
        def fake(url, headers=None, json=None, params=None, **kw):
            self.calls.append({"method": method, "url": url, "headers": headers or {},
                               "json": json, "params": params})
            if not self.responses:
                if self.strict:
                    raise AssertionError(f"unexpected extra request: {method} {url}")
                return FakeResponse()
            nxt = self.responses.pop(0)
            if isinstance(nxt, BaseException):
                raise nxt
            return nxt
        return fake

    @property
    def payload(self) -> Dict[str, Any]:
        return self.calls[-1]["json"]

    def __enter__(self):
        self._saved = (requests.post, requests.get)
        requests.post, requests.get = self._fake("POST"), self._fake("GET")
        self._key = os.environ.get("EXA_API_KEY")
        os.environ["EXA_API_KEY"] = "offline-test-key"
        return self

    def __exit__(self, *exc):
        requests.post, requests.get = self._saved
        if self._key is None:
            os.environ.pop("EXA_API_KEY", None)
        else:
            os.environ["EXA_API_KEY"] = self._key
        return False


def run_cli(module: str, argv: List[str], *responses: FakeResponse):
    """Run module.main() with argv; return (capture, exit_code, stdout, stderr)."""
    mod = importlib.import_module(module)
    out, err = io.StringIO(), io.StringIO()
    saved_argv = sys.argv
    sys.argv = [f"{module}.py", *argv]
    code = 0
    with Capture(*responses) as cap, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            mod.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        finally:
            sys.argv = saved_argv
    return cap, code, out.getvalue(), err.getvalue()


# --- tests -----------------------------------------------------------------

TESTS: List[Callable[[], None]] = []


def test(fn):
    TESTS.append(fn)
    return fn


@test
def search_highlights_sends_no_deprecated_fields():
    cap, code, _, _ = run_cli("exa_search", ["q", "--highlights", "--json"])
    assert code == 0, code
    hl = cap.payload["contents"]["highlights"]
    assert hl is True, hl


@test
def search_highlights_query_and_max_chars_object():
    cap, _, _, _ = run_cli("exa_search", ["q", "--highlights-query", "pricing", "--highlights-max-chars", "800", "--json"])
    assert cap.payload["contents"]["highlights"] == {"query": "pricing", "maxCharacters": 800}, cap.payload


@test
def contents_highlights_sends_no_deprecated_fields():
    cap, code, _, err = run_cli("exa_contents", ["https://example.com", "--highlights", "--sentences", "5", "--json"])
    assert code == 0, code
    assert cap.payload["highlights"] is True, cap.payload
    assert "--sentences" in err, err


@test
def livecrawl_maps_to_max_age_hours():
    for mode, expected in [("always", 0), ("preferred", 1), ("never", -1)]:
        cap, _, _, err = run_cli("exa_search", ["q", "--livecrawl", mode, "--json"])
        contents = cap.payload["contents"]
        assert "livecrawl" not in contents, contents
        assert contents["maxAgeHours"] == expected, (mode, contents)
        assert "--livecrawl" in err, err
    cap, _, _, _ = run_cli("exa_search", ["q", "--livecrawl", "fallback", "--json"])
    assert "maxAgeHours" not in cap.payload["contents"] and "livecrawl" not in cap.payload["contents"]


@test
def contents_livecrawl_maps_to_max_age_hours():
    cap, _, _, _ = run_cli("exa_contents", ["https://example.com", "--livecrawl", "always", "--json"])
    assert cap.payload.get("maxAgeHours") == 0 and "livecrawl" not in cap.payload, cap.payload


@test
def max_age_hours_wins_over_livecrawl():
    cap, _, _, _ = run_cli("exa_search", ["q", "--max-age-hours", "24", "--livecrawl", "always", "--json"])
    assert cap.payload["contents"]["maxAgeHours"] == 24, cap.payload


@test
def lite_drops_livecrawl_mapping():
    cap, _, _, _ = run_cli("exa_search", ["q", "--lite", "--livecrawl", "never", "--json"])
    assert cap.payload["type"] == "lite", cap.payload
    assert "maxAgeHours" not in cap.payload.get("contents", {}), cap.payload


@test
def research_paper_category_becomes_publication():
    cap, _, _, err = run_cli("exa_search", ["q", "--category", "research paper", "--json"])
    assert cap.payload["category"] == "publication", cap.payload
    assert "publication" in err, err


@test
def invalid_category_rejected_with_message():
    from exa_search import search
    with Capture():
        try:
            search("q", category="tweet")
        except ValueError as e:
            assert "Invalid category 'tweet'" in str(e), e
            return
    raise AssertionError("tweet category was accepted")


@test
def repeated_domain_flags_accumulate():
    cap, _, _, _ = run_cli("exa_search", ["q", "--domains", "a.com", "--domains", "b.com", "c.com", "--json"])
    assert cap.payload["includeDomains"] == ["a.com", "b.com", "c.com"], cap.payload


@test
def comma_joined_domains_split():
    cap, _, _, _ = run_cli("exa_research", ["q", "--domains", "jstor.org,persee.fr", "--domains", "x.org", "--json"],
                           FakeResponse(fixture("search_auto_text_output.json")))
    assert cap.payload["includeDomains"] == ["jstor.org", "persee.fr", "x.org"], cap.payload


@test
def dynamic_highlights_sets_beta_header():
    cap, code, _, _ = run_cli("exa_search", ["q", "--dynamic", "--json"])
    assert code == 0
    assert cap.calls[-1]["headers"].get("Exa-Beta") == "dynamic-highlights-2026-08-28", cap.calls[-1]["headers"]
    assert cap.payload["contents"]["highlights"] == {"dynamic": True}, cap.payload


@test
def dynamic_rejects_highlights_max_chars():
    cap, code, _, err = run_cli("exa_search", ["q", "--dynamic", "--highlights-max-chars", "500"])
    assert code != 0 and not cap.calls, (code, cap.calls)
    assert "--dynamic" in err, err


@test
def snapshot_rejects_freshness_flags():
    for extra in (["--max-age-hours", "0"], ["--livecrawl", "always"], ["--subpages", "2"]):
        cap, code, _, err = run_cli("exa_search", ["q", "--snapshot-as-of", "2026-01-15", *extra])
        assert code != 0 and not cap.calls, (extra, code)
    cap, code, _, _ = run_cli("exa_search", ["q", "--snapshot-as-of", "2026-01-15", "--json"])
    assert cap.payload["contents"]["snapshotAsOf"] == "2026-01-15", cap.payload


@test
def output_schema_allowed_on_any_type():
    # Spec: outputSchema "works with every search type" except lite (server rejects).
    cap, code, _, err = run_cli("exa_search", ["q", "--fast", "--text-output", "Short answer", "--json"])
    assert code == 0, (code, err)
    assert cap.payload["type"] == "fast", cap.payload
    assert cap.payload["outputSchema"] == {"type": "text", "description": "Short answer"}, cap.payload
    assert "--fast" in err, err


@test
def lite_unsupported_field_surfaces_server_400():
    body = fixture("search_lite_summary_400.json")["body"]
    cap, code, _, err = run_cli("exa_search", ["q", "--lite", "--summary", "x"], FakeResponse(body, 400))
    assert len(cap.calls) == 1 and code == 1, (cap.calls, code)
    assert 'Not supported with type "lite": contents.summary' in err, err
    assert "--lite" in err, err


@test
def additional_queries_for_deep_lite_capped_at_ten():
    cap, _, _, _ = run_cli("exa_search", ["q", "--deep-lite", "--additional-queries", "a", "b", "--json"])
    assert cap.payload["type"] == "deep-lite" and cap.payload["additionalQueries"] == ["a", "b"], cap.payload
    cap, code, _, _ = run_cli("exa_search", ["q", "--deep", "--additional-queries", *[str(i) for i in range(11)]])
    assert code != 0 and not cap.calls


@test
def search_warnings_to_stderr_notices_to_stdout():
    body = dict(fixture("search_ignored_field_warning.json"))
    body["notices"] = [{"code": "RESTRICTIONS_RELAXED", "message": "Date filter relaxed."},
                       {"code": "SOMETHING_NEW", "message": "Unknown code text."}]
    _, code, out, err = run_cli("exa_search", ["q"], FakeResponse(body))
    assert code == 0
    assert "IGNORED_FIELD" in err and "IGNORED_FIELD" not in out, (out[:200], err)
    assert "Date filter relaxed." in out and "Unknown code text." in out, out[:400]


@test
def null_warnings_and_notices_tolerated():
    _, code, out, _ = run_cli("exa_search", ["q", "--cost"], FakeResponse({"results": [], "warnings": None, "notices": None,
                                                                          "costDollars": {"total": 0.004}}))
    assert code == 0 and "COST: $0.0040" in out, out


@test
def json_mode_stdout_is_one_document():
    body = dict(fixture("search_ignored_field_warning.json"))
    body["notices"] = [{"code": "RESTRICTIONS_RELAXED", "message": "relaxed"}]
    _, _, out, _ = run_cli("exa_search", ["q", "--json"], FakeResponse(body))
    assert json.loads(out)["notices"][0]["message"] == "relaxed"


@test
def cost_reads_nested_search_breakdown():
    _, _, out, _ = run_cli("exa_search", ["q", "--cost"], FakeResponse(fixture("search_auto_text_output.json")))
    assert "COST: $0.0070" in out and "search.neural: $0.0070" in out, out[-300:]


@test
def search_error_envelope_parsed():
    body = {"requestId": "r1", "error": "Invalid request body | bad field", "tag": "INVALID_REQUEST_BODY"}
    _, code, _, err = run_cli("exa_search", ["q"], FakeResponse(body, 400))
    assert code == 1 and "INVALID_REQUEST_BODY" in err and "bad field" in err, err


@test
def agent_error_envelope_parsed():
    body = fixture("agent_error_budget_fixed.json")["body"]
    _, code, _, err = run_cli("exa_agent", ["run", "q", "--effort", "auto"], FakeResponse(body, 400))
    assert code == 1 and "INVALID_REQUEST" in err, err
    assert "maxCostDollars is currently supported only for metered efforts" in err, err


@test
def company_category_date_filter_hint():
    body = {"error": "Invalid request body | startPublishedDate not supported", "tag": "INVALID_REQUEST_BODY"}
    _, code, _, err = run_cli("exa_search", ["q", "--category", "company", "--after", "2026-01-01"], FakeResponse(body, 400))
    assert code == 1 and "date filters" in err, err


@test
def research_plain_sends_only_answer_fields():
    allowed = {"query", "stream", "text", "model", "systemPrompt", "userLocation", "outputSchema", "userIdentifier"}
    cap, code, _, _ = run_cli("exa_research", ["q", "--model", "exa-pro", "--system-prompt", "be terse", "--json"],
                              FakeResponse(fixture("answer_response.json")))
    assert code == 0 and cap.calls[-1]["url"].endswith("/answer"), cap.calls
    assert set(cap.payload) <= allowed, set(cap.payload) - allowed
    assert cap.payload["model"] == "exa-pro" and cap.payload["systemPrompt"] == "be terse"


@test
def research_sources_lists_citations():
    _, code, out, _ = run_cli("exa_research", ["q", "--sources"], FakeResponse(fixture("answer_response.json")))
    first = fixture("answer_response.json")["citations"][0]["url"]
    assert code == 0 and "SOURCES" in out and first in out, out


@test
def research_filters_route_to_search():
    cap, code, out, err = run_cli("exa_research", ["q", "--domains", "exa.ai", "-n", "3"],
                                  FakeResponse(fixture("search_auto_text_output.json")))
    assert code == 0, err
    call = cap.calls[-1]
    assert call["url"].endswith("/search"), call["url"]
    p = call["json"]
    assert p["type"] == "auto" and p["includeDomains"] == ["exa.ai"] and p["numResults"] == 3, p
    assert p["outputSchema"]["type"] == "text", p
    assert "/search" in err, err
    assert "Exa Lite is a new search type" in out, out[:300]


@test
def research_markdown_handles_dict_answer():
    body = {"answer": {"summary": "x", "points": ["a"]}, "citations": [{"url": "https://e.com", "title": "E"}]}
    _, code, out, _ = run_cli("exa_research", ["q", "--markdown"], FakeResponse(body))
    assert code == 0 and '"summary": "x"' in out and "https://e.com" in out, out


@test
def research_stream_parses_openai_chunks():
    lines = fixture("answer_stream.sse").splitlines()
    _, code, out, _ = run_cli("exa_research", ["q", "--stream", "--sources", "--cost"], FakeResponse(lines=lines))
    text = "".join(json.loads(ln[6:])["choices"][0]["delta"].get("content", "")
                   for ln in lines if ln.startswith("data: {\"choices\""))
    assert code == 0 and text in out, out[:300]
    assert "alphasignal.ai" in out and "COST: $0.0050" in out, out[-500:]


@test
def research_stream_json_is_one_document():
    lines = fixture("answer_stream.sse").splitlines()
    _, code, out, _ = run_cli("exa_research", ["q", "--stream", "--json"], FakeResponse(lines=lines))
    doc = json.loads(out)
    assert code == 0 and doc["citations"] and doc["costDollars"]["total"] == 0.005, doc.keys()


@test
def research_stream_error_chunk():
    lines = ['data: {"choices":[{"index":0,"delta":{"content":"Hel"}}]}',
             'data: {"tag":"ERROR","payload":{"error":{"code":500,"message":"upstream failed"},"requestId":"r"}}']
    _, code, _, err = run_cli("exa_research", ["q", "--stream"], FakeResponse(lines=lines))
    assert code == 1 and "upstream failed" in err, err


@test
def agent_default_effort_is_explicit_medium():
    cap, code, out, _ = run_cli("exa_agent", ["run", "capital of Crete?"],
                                FakeResponse(fixture("agent_run_created.json")),
                                FakeResponse(fixture("agent_run_completed.json")))
    assert code == 0, code
    assert cap.calls[0]["json"] == {"query": "capital of Crete?", "effort": "medium"}, cap.calls[0]["json"]
    assert cap.calls[1]["method"] == "GET" and cap.calls[1]["url"].endswith(fixture("agent_run_created.json")["id"])
    assert "Heraklion" in out and "schema_satisfied" in out, out


@test
def agent_budget_guards():
    cap, code, _, err = run_cli("exa_agent", ["run", "q", "--effort", "medium", "--max-cost", "5"])
    assert code != 0 and not cap.calls and "--max-cost" in err, err
    cap, code, _, err = run_cli("exa_agent", ["run", "q", "--effort", "auto", "--max-duration", "600"])
    assert code != 0 and not cap.calls and "--max-duration" in err, err
    cap, code, _, _ = run_cli("exa_agent", ["run", "q", "--effort", "ultra", "--max-cost", "30",
                                            "--max-duration", "900", "--no-wait"],
                              FakeResponse(fixture("agent_run_created.json")))
    assert code == 0 and cap.calls[0]["json"]["budget"] == {"maxCostDollars": 30.0, "maxDurationSeconds": 900}


@test
def agent_budget_ranges():
    for argv in (["--effort", "auto", "--max-cost", "0.5"], ["--effort", "ultra", "--max-cost", "150"],
                 ["--effort", "ultra", "--max-duration", "100"], ["--effort", "ultra", "--max-duration", "20000"]):
        cap, code, _, _ = run_cli("exa_agent", ["run", "q", *argv])
        assert code != 0 and not cap.calls, argv


@test
def agent_input_file_single_record_jsonl():
    import tempfile
    from exa_agent import _load_records
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        f.write('{"name": "Acme"}\n')
    try:
        assert _load_records(f.name, "--input-file") == [{"name": "Acme"}]
    finally:
        os.unlink(f.name)


@test
def agent_status_wait_exit_codes():
    failed = dict(fixture("agent_run_completed.json"), status="failed", stopReason="error")
    _, code, _, _ = run_cli("exa_agent", ["status", failed["id"], "--wait"], FakeResponse(failed))
    assert code == 1, code
    running = dict(fixture("agent_run_completed.json"), status="running")
    _, code, _, _ = run_cli("exa_agent", ["status", running["id"], "--wait", "--timeout", "0"], FakeResponse(running))
    assert code == 3, code


@test
def research_every_filter_routes_to_search():
    for argv in (["--after", "2026-01-01"], ["--before", "2026-06-01"], ["--exclude-domains", "x.com"]):
        cap, code, _, _ = run_cli("exa_research", ["q", *argv, "--json"], FakeResponse(fixture("search_auto_text_output.json")))
        assert code == 0 and cap.calls[-1]["url"].endswith("/search"), (argv, cap.calls)


@test
def agent_stop_only_for_ultra():
    run = dict(fixture("agent_run_completed.json"), status="running")
    cap, code, _, err = run_cli("exa_agent", ["stop", run["id"]], FakeResponse(run))
    assert code != 0 and all(c["method"] == "GET" for c in cap.calls) and "ultra" in err, (cap.calls, err)


@test
def research_async_stub_points_to_agent():
    _, code, _, err = run_cli("exa_research_async", ["create", "some question"])
    assert code == 2 and "exa_agent.py run" in err, err


@test
def preset_schemas_exist():
    from exa_search import PRESET_SCHEMAS
    for name in ["company", "paper-survey", "competitor-analysis", "person", "news-digest"]:
        assert isinstance(PRESET_SCHEMAS[name], dict) and PRESET_SCHEMAS[name]["type"] == "object", name


# --- failure paths (review round 2) ----------------------------------------

@test
def network_error_is_clean_exit():
    _, code, out, err = run_cli("exa_search", ["q", "--json"], requests.exceptions.ConnectionError("DNS failure"))
    assert code == 1 and out == "" and "ConnectionError" in err and "DNS failure" in err, (code, err)
    _, code, _, err = run_cli("exa_research", ["q"], requests.exceptions.ReadTimeout("read timed out"))
    assert code == 1 and "ReadTimeout" in err, err


@test
def non_json_2xx_body_reported():
    _, code, _, err = run_cli("exa_search", ["q"], FakeResponse(NOT_JSON, 200, text="<html>proxy</html>"))
    assert code == 1 and "INVALID_JSON" in err and "proxy" in err, err


@test
def stream_decodes_utf8():
    lines = ['data: {"choices":[{"index":0,"delta":{"content":"Exa — λόγος, café"}}]}', "data: [DONE]"]
    _, code, out, _ = run_cli("exa_research", ["q", "--stream"], FakeResponse(lines=lines))
    assert code == 0 and "Exa — λόγος, café" in out, out


@test
def stream_truncated_is_error():
    lines = ['data: {"choices":[{"index":0,"delta":{"content":"partial ans"}}]}']
    _, code, _, err = run_cli("exa_research", ["q", "--stream"], FakeResponse(lines=lines))
    assert code == 1 and "truncated" in err.lower(), (code, err)


@test
def stream_non_dict_chunk_ignored():
    lines = ['data: "keepalive"', 'data: {"choices":[{"index":0,"delta":{"content":"ok"}}]}', "data: [DONE]"]
    _, code, out, _ = run_cli("exa_research", ["q", "--stream"], FakeResponse(lines=lines))
    assert code == 0 and "ok" in out, (code, out)


@test
def empty_answer_is_not_success():
    body = {"requestId": "r", "results": [{"url": "https://exa.ai/x", "title": "x"}], "costDollars": {"total": 0.007}}
    _, code, _, err = run_cli("exa_research", ["q", "--domains", "exa.ai"], FakeResponse(body))
    assert code == 4 and "No answer" in err, (code, err)
    _, code, _, err = run_cli("exa_research", ["q"], FakeResponse({"answer": "", "citations": []}))
    assert code == 4 and "No answer" in err, (code, err)


@test
def zero_results_stated():
    _, code, out, _ = run_cli("exa_search", ["q"], FakeResponse({"requestId": "r", "results": []}))
    assert code == 0 and "RESULTS (0 found)" in out, out


@test
def null_fields_do_not_crash_formatters():
    body = {"results": [{"url": "https://e.com", "title": None,
                         "subpages": [{"url": "https://e.com/a", "title": None}]}],
            "costDollars": {"total": None}}
    _, code, out, _ = run_cli("exa_contents", ["https://e.com", "--cost"], FakeResponse(body))
    assert code == 0 and "No title" in out and "None" not in out.replace("Request ID", ""), out
    _, code, out, _ = run_cli("exa_similar", ["https://e.com"], FakeResponse({"results": [{"url": "u", "title": None}]}))
    assert code == 0 and "No title" in out, out


@test
def contents_all_urls_failed():
    body = {"results": [], "statuses": [{"id": "https://gone.example", "status": "error", "error": None}]}
    _, code, _, err = run_cli("exa_contents", ["https://gone.example", "--json"], FakeResponse(body))
    assert code == 1 and "gone.example" in err, (code, err)


@test
def agent_poll_retries_transient_errors():
    created = fixture("agent_run_created.json")
    _, code, out, _ = run_cli("exa_agent", ["run", "q"], FakeResponse(created),
                              FakeResponse({"error": "upstream", "tag": "SERVER"}, 503),
                              FakeResponse(fixture("agent_run_completed.json")))
    assert code == 0 and "Heraklion" in out, (code, out)


@test
def agent_poll_failure_keeps_run_id():
    created = fixture("agent_run_created.json")
    fails = [requests.exceptions.ConnectionError("down")] * 4
    _, code, _, err = run_cli("exa_agent", ["run", "q"], FakeResponse(created), *fails)
    assert code == 3 and f"status {created['id']} --wait" in err, (code, err)


@test
def agent_cancelled_is_not_success():
    run = dict(fixture("agent_run_completed.json"), status="cancelled", stopReason="cancelled")
    _, code, _, err = run_cli("exa_agent", ["status", run["id"], "--wait"], FakeResponse(run))
    assert code == 1 and "cancelled" in err, (code, err)


@test
def agent_list_tolerates_nulls():
    listing = {"object": "list", "hasMore": False, "data": [
        {"id": "agent_run_x", "status": None, "request": None, "costDollars": {"total": None}, "createdAt": None}]}
    _, code, out, _ = run_cli("exa_agent", ["list"], FakeResponse(listing))
    assert code == 0 and "agent_run_x" in out, out


@test
def agent_stop_with_unknown_effort_proceeds():
    run = dict(fixture("agent_run_completed.json"), status="running", request=None)
    cap, code, _, _ = run_cli("exa_agent", ["stop", run["id"]], FakeResponse(run), FakeResponse(run))
    assert code == 0 and cap.calls[-1]["method"] == "POST" and cap.calls[-1]["url"].endswith("/stop"), cap.calls


@test
def agent_client_side_limits():
    cap, code, _, _ = run_cli("exa_agent", ["run", "q", *sum([["--data-source", d] for d in
                              ["fiber", "jinko", "particle", "polymarket", "macrobond", "affiliate"]], [])])
    assert code == 2 and not cap.calls
    cap, code, _, err = run_cli("exa_agent", ["run", "q", "--max-items", "5"])
    assert code == 2 and not cap.calls and "--max-items" in err, err


@test
def search_num_must_be_positive():
    cap, code, _, _ = run_cli("exa_search", ["q", "-n", "0"])
    assert code == 2 and not cap.calls


@test
def neural_sends_auto():
    cap, _, _, err = run_cli("exa_search", ["q", "--neural", "--json"])
    assert cap.payload["type"] == "auto" and "--neural" in err, cap.payload


@test
def similar_uses_native_fields():
    cap, code, _, err = run_cli("exa_similar", ["https://www.nytimes.com/x", "--exclude-source", "--safe", "--json"])
    assert code == 0, err
    p = cap.payload
    assert p.get("excludeSourceDomain") is True and "excludeDomains" not in p, p
    assert "moderation" not in p and "--safe" in err, (p, err)


@test
def ignored_flags_are_not_called_legacy():
    _, _, _, err = run_cli("exa_research", ["q", "--domains", "x.com", "--model", "exa"],
                           FakeResponse(fixture("search_auto_text_output.json")))
    assert "--model ignored" in err and "is legacy" not in err, err


@test
def request_id_from_header():
    body = {"error": {"type": "INVALID_REQUEST", "code": "INVALID_REQUEST", "message": "bad"}}
    _, code, _, err = run_cli("exa_agent", ["run", "q"], FakeResponse(body, 400, headers={"x-request-id": "hdr123"}))
    assert code == 1 and "hdr123" in err, err


@test
def error_hint_keyed_on_server_message():
    body = {"error": "Invalid request body | outputSchema has more than 10 properties", "tag": "INVALID_REQUEST_BODY"}
    _, code, _, err = run_cli("exa_search", ["q", "--category", "company", "--text-output", "x"], FakeResponse(body, 400))
    assert code == 1 and "10 properties" in err.split("Hint:")[-1] and "date filters" not in err, err


@test
def research_async_stub_suggestions():
    _, code, _, err = run_cli("exa_research_async", ["status", "r_abc"])
    assert code == 2 and 'run "status"' not in err and "exa_agent.py" in err, err
    _, code, _, err = run_cli("exa_research_async", ["--timeout", "600", "my question", "--pro"])
    assert code == 2 and "'my question'" in err and "--effort high" in err, err


@test
def contents_bad_summary_schema_is_usage_error():
    cap, code, _, _ = run_cli("exa_contents", ["https://e.com", "--summary", "x", "--summary-schema", "{bad"])
    assert code == 2 and not cap.calls



@test
def snapshot_rejects_category_and_deep():
    for extra in (["--category", "news"], ["--deep"], ["--deep-reasoning"]):
        cap, code, _, err = run_cli("exa_search", ["q", "--snapshot-as-of", "2026-07-01", *extra])
        assert code == 2 and not cap.calls and "--snapshot-as-of" in err, (extra, code)

def run(verbose: bool = False) -> int:
    importlib.import_module("exa_agent").POLL_INTERVAL = 0  # no real sleeping in polls/retries
    failed = 0
    for fn in TESTS:
        try:
            fn()
            if verbose:
                print(f"  ✓ {fn.__name__}")
        except Exception as e:  # noqa: BLE001 — report every failure, keep going
            failed += 1
            print(f"  ✗ {fn.__name__}: {type(e).__name__}: {str(e)[:300]}")
    print(f"\nOFFLINE: {len(TESTS) - failed}/{len(TESTS)} passed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run(verbose="-v" in sys.argv or "--verbose" in sys.argv) else 0)
