#!/usr/bin/env python3
"""
Test suite for Firecrawl API wrapper.

This script tests the firecrawl_api.py module to verify all endpoints work correctly.
Run this to validate your Firecrawl setup and API key.

Usage:
    python3 test_firecrawl.py              # Run all tests
    python3 test_firecrawl.py --quick      # Run quick tests only (no async jobs)
    python3 test_firecrawl.py --verbose    # Show detailed output
    python3 test_firecrawl.py --test scrape  # Run specific test

Requires: FIRECRAWL_API_KEY environment variable
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List, Callable

# Add the scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import firecrawl_api as fc
except ImportError as e:
    print(f"Error importing firecrawl_api: {e}")
    print("Make sure firecrawl_api.py is in the same directory")
    sys.exit(1)

# Test configuration
TEST_URL = "https://example.com"
TEST_SEARCH_QUERY = "web scraping python"


class TestResult:
    """Holds the result of a test."""
    def __init__(self, name: str, passed: bool, message: str = "", data: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.data = data


def test_api_key() -> TestResult:
    """Test that API key is configured."""
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        return TestResult("API Key", False, "FIRECRAWL_API_KEY not set")
    if not api_key.startswith("fc-"):
        return TestResult("API Key", False, f"API key doesn't start with 'fc-': {api_key[:10]}...")
    return TestResult("API Key", True, f"API key configured: {api_key[:10]}...")


def test_scrape_basic() -> TestResult:
    """Test basic scrape functionality."""
    try:
        result = fc.scrape(TEST_URL, formats=["markdown"])
        if "data" in result or "markdown" in str(result):
            return TestResult("Scrape (basic)", True, "Successfully scraped", result)
        return TestResult("Scrape (basic)", False, f"Unexpected response: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Scrape (basic)", False, f"Error: {str(e)}")


def test_scrape_formats() -> TestResult:
    """Test scrape with multiple formats."""
    try:
        result = fc.scrape(TEST_URL, formats=["markdown", "html", "links"])
        data = result.get("data", result)
        has_formats = any(k in str(data) for k in ["markdown", "html", "links"])
        if has_formats:
            return TestResult("Scrape (formats)", True, "Multiple formats returned", result)
        return TestResult("Scrape (formats)", False, f"Missing formats: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Scrape (formats)", False, f"Error: {str(e)}")


def test_scrape_with_location() -> TestResult:
    """Test scrape with geo-targeting."""
    try:
        result = fc.scrape(
            TEST_URL,
            formats=["markdown"],
            location={"country": "US", "languages": ["en-US"]}
        )
        if "data" in result or "markdown" in str(result):
            return TestResult("Scrape (location)", True, "Geo-targeted scrape worked", result)
        return TestResult("Scrape (location)", False, f"Unexpected response: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Scrape (location)", False, f"Error: {str(e)}")


def test_scrape_with_cache() -> TestResult:
    """Test scrape with caching parameters."""
    try:
        result = fc.scrape(
            TEST_URL,
            formats=["markdown"],
            max_age=3600,
            store_in_cache=True
        )
        if "data" in result or "markdown" in str(result):
            return TestResult("Scrape (cache)", True, "Cached scrape worked", result)
        return TestResult("Scrape (cache)", False, f"Unexpected response: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Scrape (cache)", False, f"Error: {str(e)}")


def test_search() -> TestResult:
    """Test search functionality."""
    try:
        result = fc.search(TEST_SEARCH_QUERY, limit=3)
        data = result.get("data", result)
        if isinstance(data, list) and len(data) > 0:
            return TestResult("Search", True, f"Found {len(data)} results", result)
        if isinstance(data, dict) and any(data.get(k) for k in ["web", "results"]):
            return TestResult("Search", True, "Search returned results", result)
        return TestResult("Search", False, f"No results: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Search", False, f"Error: {str(e)}")


def test_map() -> TestResult:
    """Test map functionality."""
    try:
        result = fc.map_site(TEST_URL, limit=10)
        links = result.get("links", [])
        if links:
            return TestResult("Map", True, f"Found {len(links)} URLs", result)
        return TestResult("Map", False, f"No links found: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Map", False, f"Error: {str(e)}")


def test_batch_scrape() -> TestResult:
    """Test batch scrape functionality (starts async job)."""
    try:
        urls = [TEST_URL, "https://httpbin.org/html"]
        result = fc.batch_scrape(urls, formats=["markdown"])
        job_id = result.get("id", result.get("job_id"))
        if job_id:
            return TestResult("Batch Scrape", True, f"Job started: {job_id}", result)
        return TestResult("Batch Scrape", False, f"No job ID: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Batch Scrape", False, f"Error: {str(e)}")


def test_crawl_async() -> TestResult:
    """Test async crawl functionality."""
    try:
        result = fc.crawl(TEST_URL, limit=2, async_mode=True)
        job_id = result.get("job_id", result.get("id"))
        if job_id:
            return TestResult("Crawl (async)", True, f"Job started: {job_id}", result)
        return TestResult("Crawl (async)", False, f"No job ID: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Crawl (async)", False, f"Error: {str(e)}")


def test_extract() -> TestResult:
    """Test extract functionality."""
    try:
        result = fc.extract(
            [TEST_URL],
            prompt="Find the page title and main heading"
        )
        job_id = result.get("id", result.get("job_id"))
        if job_id:
            return TestResult("Extract", True, f"Job started: {job_id}", result)
        return TestResult("Extract", False, f"No job ID: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Extract", False, f"Error: {str(e)}")


def test_agent_mini() -> TestResult:
    """Test agent with spark-1-mini model (async)."""
    try:
        result = fc.agent(
            "What is the main purpose of example.com?",
            urls=[TEST_URL],
            async_mode=True,
            model="spark-1-mini"
        )
        job_id = result.get("job_id")
        if job_id:
            return TestResult("Agent (mini)", True, f"Job started: {job_id}", result)
        return TestResult("Agent (mini)", False, f"No job ID: {str(result)[:100]}")
    except Exception as e:
        return TestResult("Agent (mini)", False, f"Error: {str(e)}")


def test_crawl_active() -> TestResult:
    """Test getting active crawls."""
    try:
        result = fc.get_active_crawls()
        # This might return empty list if no active crawls
        crawls = result.get("crawls", result.get("data", []))
        return TestResult("Active Crawls", True, f"Found {len(crawls)} active crawls", result)
    except Exception as e:
        return TestResult("Active Crawls", False, f"Error: {str(e)}")


def run_tests(tests: List[Callable], verbose: bool = False) -> Dict[str, Any]:
    """Run a list of tests and return results."""
    results = []
    passed = 0
    failed = 0

    print("\n" + "=" * 60)
    print("FIRECRAWL API TEST SUITE")
    print("=" * 60 + "\n")

    for test_fn in tests:
        test_name = test_fn.__name__.replace("test_", "").replace("_", " ").title()
        print(f"Testing: {test_name}...", end=" ", flush=True)

        result = test_fn()
        results.append(result)

        if result.passed:
            print(f"✓ PASSED - {result.message}")
            passed += 1
        else:
            print(f"✗ FAILED - {result.message}")
            failed += 1

        if verbose and result.data:
            print(f"  Response: {json.dumps(result.data, indent=2, default=str)[:500]}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {len(results)} total")
    print("=" * 60 + "\n")

    return {
        "passed": passed,
        "failed": failed,
        "total": len(results),
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="Test Firecrawl API wrapper")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (no async jobs)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--test", help="Run specific test (e.g., 'scrape', 'search', 'agent')")
    args = parser.parse_args()

    # Define test sets
    quick_tests = [
        test_api_key,
        test_scrape_basic,
        test_scrape_formats,
        test_search,
        test_map,
    ]

    async_tests = [
        test_scrape_with_location,
        test_scrape_with_cache,
        test_batch_scrape,
        test_crawl_async,
        test_extract,
        test_agent_mini,
        test_crawl_active,
    ]

    all_tests = quick_tests + async_tests

    # Select tests to run
    if args.test:
        test_name = f"test_{args.test.lower().replace(' ', '_')}"
        matching_tests = [t for t in all_tests if args.test.lower() in t.__name__.lower()]
        if not matching_tests:
            print(f"No test matching '{args.test}' found")
            print("Available tests:")
            for t in all_tests:
                print(f"  - {t.__name__.replace('test_', '')}")
            sys.exit(1)
        tests_to_run = matching_tests
    elif args.quick:
        tests_to_run = quick_tests
    else:
        tests_to_run = all_tests

    # Run tests
    results = run_tests(tests_to_run, verbose=args.verbose)

    # Exit with appropriate code
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
