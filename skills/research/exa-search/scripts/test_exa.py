#!/usr/bin/env python3
"""
Exa API Test Suite - Verify all endpoints and features work correctly.

This script tests the Exa Search skill's scripts to ensure proper API connectivity
and feature functionality. Run after making changes to verify nothing is broken.

Usage:
    python3 test_exa.py              # Offline tests + full live suite (~$0.15)
    python3 test_exa.py --quick      # Offline tests only: no key, no network
    python3 test_exa.py --verbose    # Show detailed output
    python3 test_exa.py --endpoint search  # Live tests for one endpoint

Live tests require EXA_API_KEY. Offline tests live in test_offline.py.
"""

import os
import sys
import json
import argparse
import subprocess
from typing import List, Tuple

# Add scripts directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Test status tracking
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors: List[str] = []

    def record_pass(self, name: str, verbose: bool = False):
        self.passed += 1
        if verbose:
            print(f"  ✓ {name}")

    def record_fail(self, name: str, error: str, verbose: bool = False):
        self.failed += 1
        self.errors.append(f"{name}: {error}")
        if verbose:
            print(f"  ✗ {name}: {error}")

    def record_skip(self, name: str, reason: str, verbose: bool = False):
        self.skipped += 1
        if verbose:
            print(f"  ○ {name}: {reason}")

    def summary(self) -> str:
        total = self.passed + self.failed + self.skipped
        lines = [
            f"\n{'='*60}",
            f"TEST RESULTS: {self.passed}/{total} passed",
            f"  Passed:  {self.passed}",
            f"  Failed:  {self.failed}",
            f"  Skipped: {self.skipped}",
        ]
        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        return "\n".join(lines)


def check_api_key() -> bool:
    """Check if EXA_API_KEY is set."""
    return bool(os.environ.get("EXA_API_KEY"))


def test_search_basic(results: TestResults, verbose: bool = False):
    """Test basic search functionality."""
    from exa_search import search

    try:
        result = search("Python programming", num_results=3)
        if result.get("results") and len(result["results"]) > 0:
            results.record_pass("search_basic", verbose)
        else:
            results.record_fail("search_basic", "No results returned", verbose)
    except Exception as e:
        results.record_fail("search_basic", str(e), verbose)


def test_search_with_category(results: TestResults, verbose: bool = False):
    """Test search with category filter."""
    from exa_search import search

    try:
        result = search("machine learning", num_results=3, category="publication")
        if result.get("results"):
            results.record_pass("search_with_category", verbose)
        else:
            results.record_fail("search_with_category", "No results returned", verbose)
    except Exception as e:
        results.record_fail("search_with_category", str(e), verbose)


def test_search_with_domain(results: TestResults, verbose: bool = False):
    """Test search with domain filter."""
    from exa_search import search

    try:
        result = search(
            "Python tutorials",
            num_results=3,
            include_domains=["docs.python.org", "realpython.com"]
        )
        if result.get("results"):
            # Verify domains are correct
            all_valid = all(
                any(d in r.get("url", "") for d in ["docs.python.org", "realpython.com"])
                for r in result["results"]
            )
            if all_valid:
                results.record_pass("search_with_domain", verbose)
            else:
                results.record_fail("search_with_domain", "Off-domain result returned", verbose)
        else:
            results.record_fail("search_with_domain", "No results returned", verbose)
    except Exception as e:
        results.record_fail("search_with_domain", str(e), verbose)


def test_search_deep(results: TestResults, verbose: bool = False):
    """Test deep search mode."""
    from exa_search import search

    try:
        result = search("AI agents", num_results=3, search_type="deep")
        if result.get("results"):
            results.record_pass("search_deep", verbose)
        else:
            results.record_fail("search_deep", "No results returned", verbose)
    except Exception as e:
        results.record_fail("search_deep", str(e), verbose)


def test_contents_basic(results: TestResults, verbose: bool = False):
    """Test basic content extraction."""
    from exa_contents import get_contents

    try:
        result = get_contents(["https://example.com"])
        if result.get("results"):
            results.record_pass("contents_basic", verbose)
        else:
            results.record_fail("contents_basic", "No content returned", verbose)
    except Exception as e:
        results.record_fail("contents_basic", str(e), verbose)


def test_contents_livecrawl(results: TestResults, verbose: bool = False):
    """Test livecrawl content extraction."""
    from exa_contents import get_contents

    try:
        result = get_contents(
            ["https://news.ycombinator.com"],
            livecrawl="preferred"
        )
        if result.get("results"):
            results.record_pass("contents_livecrawl", verbose)
        else:
            results.record_fail("contents_livecrawl", "No content returned", verbose)
    except Exception as e:
        results.record_fail("contents_livecrawl", str(e), verbose)


def test_contents_context(results: TestResults, verbose: bool = False):
    """Test context parameter for RAG."""
    from exa_contents import get_contents

    try:
        result = get_contents(
            ["https://example.com"],
            get_context=True,
            context_max_chars=5000
        )
        if not result.get("results"):
            results.record_fail("contents_context", "No results returned", verbose)
        elif result.get("context"):
            results.record_pass("contents_context", verbose)
        else:
            results.record_skip("contents_context", "Deprecated context field not returned", verbose)
    except Exception as e:
        results.record_fail("contents_context", str(e), verbose)


def test_similar_basic(results: TestResults, verbose: bool = False):
    """Test basic find similar."""
    from exa_similar import find_similar

    try:
        result = find_similar("https://github.com/python/cpython", num_results=3)
        if result.get("results"):
            results.record_pass("similar_basic", verbose)
        else:
            results.record_fail("similar_basic", "No similar pages found", verbose)
    except Exception as e:
        results.record_fail("similar_basic", str(e), verbose)


def test_similar_with_moderation(results: TestResults, verbose: bool = False):
    """Test find similar with moderation."""
    from exa_similar import find_similar

    try:
        result = find_similar(
            "https://github.com/python/cpython",
            num_results=3,
            moderation=True
        )
        if result.get("results"):
            results.record_pass("similar_with_moderation", verbose)
        else:
            results.record_fail("similar_with_moderation", "No results returned", verbose)
    except Exception as e:
        results.record_fail("similar_with_moderation", str(e), verbose)


def test_research_basic(results: TestResults, verbose: bool = False):
    """Test basic research/answer."""
    from exa_research import research

    try:
        result = research("What is Python?")
        if result.get("answer") and result.get("citations"):
            results.record_pass("research_basic", verbose)
        else:
            results.record_fail("research_basic", "No answer or citations returned", verbose)
    except Exception as e:
        results.record_fail("research_basic", str(e), verbose)


def test_research_stream(results: TestResults, verbose: bool = False):
    """Test streaming research."""
    from exa_research import research, process_stream

    try:
        response = research("What is 2+2?", stream=True)
        try:
            streamed = process_stream(response, echo=False)
        finally:
            response.close()
        if streamed["answer"] and streamed["citations"] and streamed.get("costDollars"):
            results.record_pass("research_stream", verbose)
        else:
            results.record_fail("research_stream", f"Incomplete stream: {list(streamed)}", verbose)
    except Exception as e:
        results.record_fail("research_stream", str(e), verbose)






# --- Exa Deep tests ---

def test_search_deep_reasoning(results: TestResults, verbose: bool = False):
    """Test deep-reasoning search type."""
    from exa_search import search

    try:
        result = search("What are the main AI agent frameworks?", num_results=3, search_type="deep-reasoning")
        if result.get("results") or result.get("output"):
            results.record_pass("search_deep_reasoning", verbose)
        else:
            results.record_fail("search_deep_reasoning", "No results or output returned", verbose)
    except Exception as e:
        results.record_fail("search_deep_reasoning", str(e), verbose)


def test_search_output_schema_text(results: TestResults, verbose: bool = False):
    """Test structured output with text schema."""
    from exa_search import search

    try:
        result = search(
            "Who is the CEO of Stripe?",
            num_results=3,
            output_schema={"type": "text", "description": "Short one-sentence answer"}
        )
        output = result.get("output", {})
        content = output.get("content") if output else None
        if isinstance(content, str) and len(content) > 0:
            results.record_pass("search_output_schema_text", verbose)
        else:
            results.record_fail("search_output_schema_text", "No text content in output", verbose)
    except Exception as e:
        results.record_fail("search_output_schema_text", str(e), verbose)


def test_search_output_schema_json(results: TestResults, verbose: bool = False):
    """Test structured output with object schema and grounding."""
    from exa_search import search

    try:
        schema = {
            "type": "object",
            "required": ["answer"],
            "properties": {
                "answer": {"type": "string", "description": "The answer"},
                "confidence": {"type": "string", "description": "Confidence level"}
            }
        }
        result = search(
            "What programming language is most popular in 2025?",
            num_results=3,
            search_type="deep",
            output_schema=schema
        )
        output = result.get("output", {})
        content = output.get("content") if output else None
        if isinstance(content, dict) and content.get("answer"):
            results.record_pass("search_output_schema_json", verbose)
        else:
            results.record_fail("search_output_schema_json", "No structured output returned", verbose)
    except Exception as e:
        results.record_fail("search_output_schema_json", str(e), verbose)






def test_contents_max_age_hours(results: TestResults, verbose: bool = False):
    """Test content extraction with maxAgeHours (livecrawl replacement)."""
    from exa_contents import get_contents

    try:
        result = get_contents(
            ["https://example.com"],
            max_age_hours=0
        )
        if result.get("results"):
            results.record_pass("contents_max_age_hours", verbose)
        else:
            results.record_fail("contents_max_age_hours", "No content returned", verbose)
    except Exception as e:
        results.record_fail("contents_max_age_hours", str(e), verbose)


def test_contents_verbosity_sections(results: TestResults, verbose: bool = False):
    """Test content extraction with verbosity and section filtering (requires livecrawl)."""
    from exa_contents import get_contents

    try:
        result = get_contents(
            ["https://example.com"],
            max_age_hours=0,
            verbosity="compact",
            exclude_sections=["navigation", "footer"]
        )
        if result.get("results"):
            results.record_pass("contents_verbosity_sections", verbose)
        else:
            results.record_fail("contents_verbosity_sections", "No content returned", verbose)
    except Exception as e:
        results.record_fail("contents_verbosity_sections", str(e), verbose)


def test_contents_highlights_max_chars(results: TestResults, verbose: bool = False):
    """Test highlights with maxCharacters (preferred over numSentences)."""
    from exa_contents import get_contents

    try:
        result = get_contents(
            ["https://example.com"],
            get_highlights=True,
            highlights_max_chars=500
        )
        if result.get("results"):
            results.record_pass("contents_highlights_max_chars", verbose)
        else:
            results.record_fail("contents_highlights_max_chars", "No content returned", verbose)
    except Exception as e:
        results.record_fail("contents_highlights_max_chars", str(e), verbose)


def test_research_output_schema(results: TestResults, verbose: bool = False):
    """Test /answer endpoint with outputSchema for structured JSON."""
    from exa_research import research

    try:
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}}
            }
        }
        result = research("What is Python?", output_schema=schema)
        answer = result.get("answer")
        if isinstance(answer, dict) and answer.get("answer"):
            results.record_pass("research_output_schema", verbose)
        else:
            results.record_fail("research_output_schema", "No answer returned", verbose)
    except Exception as e:
        results.record_fail("research_output_schema", str(e), verbose)




# --- Exa 3.0 tests ---

def _cli(script: str, *argv: str) -> Tuple[int, str, str]:
    proc = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, script), *argv],
                          capture_output=True, text=True, timeout=300)
    return proc.returncode, proc.stdout, proc.stderr


def test_search_lite(results: TestResults, verbose: bool = False):
    """Lite search returns results at the $4/1k tier."""
    from exa_search import search

    try:
        result = search("python requests library", num_results=3, search_type="lite", get_highlights=True)
        if result.get("results") and 0 < (result.get("costDollars", {}).get("total") or 0) <= 0.005:
            results.record_pass("search_lite", verbose)
        else:
            results.record_fail("search_lite", f"Unexpected response: {str(result)[:200]}", verbose)
    except Exception as e:
        results.record_fail("search_lite", str(e), verbose)


def test_search_lite_rejects_summary(results: TestResults, verbose: bool = False):
    """Lite's 400 for unsupported fields surfaces verbatim with a hint."""
    code, _, err = _cli("exa_search.py", "python requests", "--lite", "--summary", "what is it", "-n", "2")
    if code == 1 and 'Not supported with type "lite"' in err and "drop --lite" in err:
        results.record_pass("search_lite_rejects_summary", verbose)
    else:
        results.record_fail("search_lite_rejects_summary", f"exit {code}: {err[:200]}", verbose)


def test_search_dynamic_highlights(results: TestResults, verbose: bool = False):
    """Dynamic Highlights (beta header) returns highlights."""
    from exa_search import search

    try:
        result = search("solar installation cost trends", num_results=3, get_text=False, dynamic_highlights=True)
        if any(r.get("highlights") for r in result.get("results", [])):
            results.record_pass("search_dynamic_highlights", verbose)
        else:
            results.record_fail("search_dynamic_highlights", "No highlights returned", verbose)
    except Exception as e:
        results.record_fail("search_dynamic_highlights", str(e), verbose)


def test_research_sources_cli(results: TestResults, verbose: bool = False):
    """exa_research.py --sources lists /answer citations."""
    code, out, err = _cli("exa_research.py", "What is the Exa search API?", "--sources")
    if code == 0 and "SOURCES (" in out and "URL: http" in out:
        results.record_pass("research_sources_cli", verbose)
    else:
        results.record_fail("research_sources_cli", f"exit {code}: {(err or out)[-200:]}", verbose)


def test_research_domain_filter(results: TestResults, verbose: bool = False):
    """exa_research.py --domains routes to /search and only cites that domain."""
    code, out, err = _cli("exa_research.py", "What is Exa Lite?", "--domains", "exa.ai", "--json")
    try:
        doc = json.loads(out)
        urls = [c["url"] for c in doc.get("citations", [])]
        urls += [c["url"] for g in doc.get("grounding", []) for c in g.get("citations", [])]
        if code == 0 and doc.get("answer") and urls and all("exa.ai" in u for u in urls):
            results.record_pass("research_domain_filter", verbose)
        else:
            results.record_fail("research_domain_filter", f"Off-domain or empty: {urls[:5]}", verbose)
    except Exception as e:
        results.record_fail("research_domain_filter", f"{e}: {(err or out)[:200]}", verbose)


def test_agent_list(results: TestResults, verbose: bool = False):
    """GET /agent/runs works."""
    code, out, err = _cli("exa_agent.py", "list", "--limit", "3", "--json")
    try:
        if code == 0 and json.loads(out).get("object") == "list":
            results.record_pass("agent_list", verbose)
        else:
            results.record_fail("agent_list", f"exit {code}: {err[:200]}", verbose)
    except Exception as e:
        results.record_fail("agent_list", f"{e}: {err[:200]}", verbose)


def test_agent_run_minimal(results: TestResults, verbose: bool = False):
    """A minimal-effort run ($0.012) reaches a terminal status."""
    code, out, err = _cli("exa_agent.py", "run", "What is the capital of Crete? One word.",
                          "--effort", "minimal", "--timeout", "180", "--json")
    try:
        run = json.loads(out)
        if code == 0 and run.get("status") == "completed" and run.get("output", {}).get("text"):
            results.record_pass("agent_run_minimal", verbose)
        else:
            results.record_fail("agent_run_minimal", f"status={run.get('status')} exit={code}", verbose)
    except Exception as e:
        results.record_fail("agent_run_minimal", f"{e}: {err[:200]}", verbose)


def run_quick_tests(verbose: bool = False) -> TestResults:
    """Run the offline suite (test_offline.py): payloads, routing, parsing, fixtures."""
    import test_offline

    results = TestResults()
    print("\n" + "="*60)
    print("OFFLINE TESTS (no key, no network)")
    print("="*60)
    failed = test_offline.run(verbose)
    results.passed += len(test_offline.TESTS) - failed
    if failed:
        results.failed += failed
        results.errors.append(f"{failed} offline test(s) failed (see above)")
    return results


def run_all_tests(verbose: bool = False) -> TestResults:
    """Run the offline suite, then every live test."""
    results = run_quick_tests(verbose)

    print("\n" + "="*60)
    print("LIVE TEST SUITE")
    print("="*60)

    # API Key check
    if not check_api_key():
        print("ERROR: EXA_API_KEY environment variable not set")
        results.record_fail("api_key", "Not set", verbose)
        return results
    results.record_pass("api_key", verbose)

    # Search tests
    print("\n--- /search endpoint ---")
    test_search_basic(results, verbose)
    test_search_with_category(results, verbose)
    test_search_with_domain(results, verbose)
    test_search_deep(results, verbose)
    test_search_deep_reasoning(results, verbose)
    test_search_output_schema_text(results, verbose)
    test_search_output_schema_json(results, verbose)
    test_search_lite(results, verbose)
    test_search_lite_rejects_summary(results, verbose)
    test_search_dynamic_highlights(results, verbose)

    # Contents tests
    print("\n--- /contents endpoint ---")
    test_contents_basic(results, verbose)
    test_contents_livecrawl(results, verbose)
    test_contents_max_age_hours(results, verbose)
    test_contents_verbosity_sections(results, verbose)
    test_contents_highlights_max_chars(results, verbose)
    test_contents_context(results, verbose)

    # Similar tests
    print("\n--- /findSimilar endpoint ---")
    test_similar_basic(results, verbose)
    test_similar_with_moderation(results, verbose)

    # Research tests
    print("\n--- /answer endpoint ---")
    test_research_basic(results, verbose)
    test_research_stream(results, verbose)
    test_research_output_schema(results, verbose)
    test_research_sources_cli(results, verbose)
    test_research_domain_filter(results, verbose)

    # Agent tests
    print("\n--- /agent/runs endpoint ---")
    test_agent_list(results, verbose)
    test_agent_run_minimal(results, verbose)

    return results


def run_endpoint_tests(endpoint: str, verbose: bool = False) -> TestResults:
    """Run tests for a specific endpoint."""
    results = TestResults()

    if not check_api_key():
        print("ERROR: EXA_API_KEY environment variable not set")
        results.record_fail("api_key", "Not set", verbose)
        return results
    results.record_pass("api_key", verbose)

    endpoint_tests = {
        "search": [
            test_search_basic,
            test_search_with_category,
            test_search_with_domain,
            test_search_deep,
            test_search_deep_reasoning,
            test_search_output_schema_text,
            test_search_output_schema_json,
            test_search_lite,
            test_search_lite_rejects_summary,
            test_search_dynamic_highlights,
        ],
        "contents": [
            test_contents_basic,
            test_contents_livecrawl,
            test_contents_max_age_hours,
            test_contents_verbosity_sections,
            test_contents_highlights_max_chars,
            test_contents_context,
        ],
        "similar": [
            test_similar_basic,
            test_similar_with_moderation,
        ],
        "answer": [
            test_research_basic,
            test_research_stream,
            test_research_output_schema,
            test_research_sources_cli,
            test_research_domain_filter,
        ],
        "agent": [
            test_agent_list,
            test_agent_run_minimal,
        ],
    }

    if endpoint not in endpoint_tests:
        print(f"Unknown endpoint: {endpoint}")
        print(f"Valid endpoints: {', '.join(endpoint_tests.keys())}")
        results.record_fail("endpoint", f"unknown endpoint '{endpoint}'", verbose)
        return results

    print(f"\n--- Testing /{endpoint} endpoint ---")
    for test_func in endpoint_tests[endpoint]:
        test_func(results, verbose)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Exa API Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     Run all tests
  %(prog)s --quick             Run quick validation
  %(prog)s --verbose           Show detailed output
  %(prog)s --endpoint search   Test only search endpoint

Endpoints: search, contents, similar, answer, agent
        """
    )

    parser.add_argument("--quick", action="store_true",
                        help="Run offline tests only (no key, no network)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed test output")
    parser.add_argument("--endpoint", "-e",
                        help="Live tests for one endpoint (search, contents, similar, answer, agent)")

    args = parser.parse_args()

    if args.endpoint:
        results = run_endpoint_tests(args.endpoint, args.verbose)
    elif args.quick:
        results = run_quick_tests(args.verbose)
    else:
        results = run_all_tests(args.verbose)

    print(results.summary())

    # Exit with error code if any tests failed
    sys.exit(1 if results.failed > 0 else 0)


if __name__ == "__main__":
    main()
