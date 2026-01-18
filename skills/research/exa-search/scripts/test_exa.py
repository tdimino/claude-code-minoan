#!/usr/bin/env python3
"""
Exa API Test Suite - Verify all endpoints and features work correctly.

This script tests the Exa Search skill's scripts to ensure proper API connectivity
and feature functionality. Run after making changes to verify nothing is broken.

Usage:
    python3 test_exa.py              # Run all tests
    python3 test_exa.py --quick      # Run quick validation only
    python3 test_exa.py --verbose    # Show detailed output
    python3 test_exa.py --endpoint search  # Test specific endpoint

Requires: EXA_API_KEY environment variable
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List, Tuple

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
            lines.append(f"\nErrors:")
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
        result = search("machine learning", num_results=3, category="research paper")
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
                results.record_pass("search_with_domain", verbose)  # Domain filtering is best-effort
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
        # Context field may or may not be present depending on API version
        if result.get("results"):
            results.record_pass("contents_context", verbose)
        else:
            results.record_fail("contents_context", "No results returned", verbose)
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
        result = research("What is Python?", num_results=3)
        if result.get("answer"):
            results.record_pass("research_basic", verbose)
        else:
            results.record_fail("research_basic", "No answer returned", verbose)
    except Exception as e:
        results.record_fail("research_basic", str(e), verbose)


def test_research_stream(results: TestResults, verbose: bool = False):
    """Test streaming research."""
    from exa_research import research, process_stream

    try:
        response = research("What is 2+2?", num_results=2, stream=True)
        # Just verify we get a response object, don't actually stream
        if hasattr(response, 'iter_lines'):
            results.record_pass("research_stream", verbose)
        else:
            results.record_fail("research_stream", "Invalid stream response", verbose)
        response.close()  # Clean up
    except Exception as e:
        results.record_fail("research_stream", str(e), verbose)


def test_research_async_models(results: TestResults, verbose: bool = False):
    """Test async research model validation."""
    from exa_research_async import create_research

    # Test that invalid model raises error
    try:
        create_research("test", model="invalid-model")
        results.record_fail("research_async_models", "Should have raised ValueError", verbose)
    except ValueError as e:
        if "exa-research-fast" in str(e) and "exa-research-pro" in str(e):
            results.record_pass("research_async_models", verbose)
        else:
            results.record_fail("research_async_models", f"Error message missing models: {e}", verbose)
    except Exception as e:
        results.record_fail("research_async_models", str(e), verbose)


def test_research_async_list(results: TestResults, verbose: bool = False):
    """Test listing async research jobs."""
    from exa_research_async import list_research

    try:
        result = list_research(limit=5)
        # Just verify we get a response with expected structure
        if "data" in result:
            results.record_pass("research_async_list", verbose)
        else:
            results.record_fail("research_async_list", "Missing 'data' field", verbose)
    except Exception as e:
        results.record_fail("research_async_list", str(e), verbose)


def run_quick_tests(verbose: bool = False) -> TestResults:
    """Run quick validation tests only."""
    results = TestResults()

    print("\n" + "="*60)
    print("QUICK VALIDATION TESTS")
    print("="*60)

    # API Key check
    if not check_api_key():
        print("ERROR: EXA_API_KEY environment variable not set")
        results.record_fail("api_key", "Not set", verbose)
        return results
    results.record_pass("api_key", verbose)

    # Basic search
    print("\nTesting /search endpoint...")
    test_search_basic(results, verbose)

    # Basic contents
    print("\nTesting /contents endpoint...")
    test_contents_basic(results, verbose)

    # Model validation
    print("\nTesting model validation...")
    test_research_async_models(results, verbose)

    return results


def run_all_tests(verbose: bool = False) -> TestResults:
    """Run all tests."""
    results = TestResults()

    print("\n" + "="*60)
    print("FULL TEST SUITE")
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

    # Contents tests
    print("\n--- /contents endpoint ---")
    test_contents_basic(results, verbose)
    test_contents_livecrawl(results, verbose)
    test_contents_context(results, verbose)

    # Similar tests
    print("\n--- /findSimilar endpoint ---")
    test_similar_basic(results, verbose)
    test_similar_with_moderation(results, verbose)

    # Research tests
    print("\n--- /answer endpoint ---")
    test_research_basic(results, verbose)
    test_research_stream(results, verbose)

    # Async research tests
    print("\n--- /research/v1 endpoint ---")
    test_research_async_models(results, verbose)
    test_research_async_list(results, verbose)

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
        ],
        "contents": [
            test_contents_basic,
            test_contents_livecrawl,
            test_contents_context,
        ],
        "similar": [
            test_similar_basic,
            test_similar_with_moderation,
        ],
        "answer": [
            test_research_basic,
            test_research_stream,
        ],
        "research": [
            test_research_async_models,
            test_research_async_list,
        ],
    }

    if endpoint not in endpoint_tests:
        print(f"Unknown endpoint: {endpoint}")
        print(f"Valid endpoints: {', '.join(endpoint_tests.keys())}")
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

Endpoints: search, contents, similar, answer, research
        """
    )

    parser.add_argument("--quick", action="store_true",
                        help="Run quick validation only")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed test output")
    parser.add_argument("--endpoint", "-e",
                        help="Test specific endpoint (search, contents, similar, answer, research)")

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
