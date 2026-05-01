#!/usr/bin/env python3
"""
Omnisearch Test Suite — verify routing, dedup, and provider connectivity.

Tests are grouped by dependency: offline tests (router, dedup) run without API keys;
live tests require the corresponding API key and are skipped gracefully when missing.

Usage:
    python3 test_omnisearch.py              # All tests (skips missing keys)
    python3 test_omnisearch.py --quick      # Offline tests + one basic per available key
    python3 test_omnisearch.py --verbose    # Detailed output
    python3 test_omnisearch.py --group router    # Specific group
    python3 test_omnisearch.py --group dedup
    python3 test_omnisearch.py --group brave
    python3 test_omnisearch.py --group tavily
    python3 test_omnisearch.py --group xpoz
    python3 test_omnisearch.py --group integration

Requires: At least one API key for live tests (BRAVE_API_KEY, TAVILY_API_KEY, etc.)
"""

import os
import sys
import json
import argparse
from typing import List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


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


def has_key(env_var: str) -> bool:
    return bool(os.environ.get(env_var))


# ---------------------------------------------------------------------------
# Group: router (offline)
# ---------------------------------------------------------------------------

def test_classify_general(r: TestResults, v: bool = False):
    from omnisearch import classify_query, QueryCategory
    cat = classify_query("Iran oil production 2025")
    if cat == QueryCategory.GENERAL_WEB:
        r.record_pass("classify_general", v)
    else:
        r.record_fail("classify_general", f"Expected GENERAL_WEB, got {cat.value}", v)


def test_classify_news(r: TestResults, v: bool = False):
    from omnisearch import classify_query, QueryCategory
    cat = classify_query("latest drone strike on US base")
    if cat == QueryCategory.NEWS:
        r.record_pass("classify_news", v)
    else:
        r.record_fail("classify_news", f"Expected NEWS, got {cat.value}", v)


def test_classify_social(r: TestResults, v: bool = False):
    from omnisearch import classify_query, QueryCategory
    for q in ["@IdaeanDaktyl tweet about war", "r/geopolitics Iran", "#IranStrikes on twitter"]:
        cat = classify_query(q)
        if cat != QueryCategory.SOCIAL_MEDIA:
            r.record_fail("classify_social", f"'{q}' → {cat.value}, expected SOCIAL_MEDIA", v)
            return
    r.record_pass("classify_social", v)


def test_classify_academic(r: TestResults, v: bool = False):
    from omnisearch import classify_query, QueryCategory
    cat = classify_query("transformer architecture research paper")
    if cat == QueryCategory.ACADEMIC:
        r.record_pass("classify_academic", v)
    else:
        r.record_fail("classify_academic", f"Expected ACADEMIC, got {cat.value}", v)


def test_classify_factual(r: TestResults, v: bool = False):
    from omnisearch import classify_query, QueryCategory
    cat = classify_query("who is the IRGC commander?")
    if cat == QueryCategory.FACTUAL_QUICK:
        r.record_pass("classify_factual", v)
    else:
        r.record_fail("classify_factual", f"Expected FACTUAL_QUICK, got {cat.value}", v)


def test_classify_company(r: TestResults, v: bool = False):
    from omnisearch import classify_query, QueryCategory
    cat = classify_query("Palantir defense funding round")
    if cat == QueryCategory.COMPANY_RESEARCH:
        r.record_pass("classify_company", v)
    else:
        r.record_fail("classify_company", f"Expected COMPANY_RESEARCH, got {cat.value}", v)


def test_classify_tech(r: TestResults, v: bool = False):
    from omnisearch import classify_query, QueryCategory
    cat = classify_query("Cloudflare Workers API documentation")
    if cat == QueryCategory.TECHNICAL_DOCS:
        r.record_pass("classify_tech", v)
    else:
        r.record_fail("classify_tech", f"Expected TECHNICAL_DOCS, got {cat.value}", v)


def test_select_providers_force(r: TestResults, v: bool = False):
    from omnisearch import select_providers, Provider, QueryCategory
    avail = {p: True for p in Provider}
    selected = select_providers(QueryCategory.GENERAL_WEB, avail, force=Provider.TAVILY)
    if selected == [Provider.TAVILY]:
        r.record_pass("select_force", v)
    else:
        r.record_fail("select_force", f"Expected [TAVILY], got {selected}", v)


def test_select_providers_force_missing(r: TestResults, v: bool = False):
    from omnisearch import select_providers, Provider, QueryCategory
    avail = {p: False for p in Provider}
    try:
        select_providers(QueryCategory.GENERAL_WEB, avail, force=Provider.BRAVE)
        r.record_fail("select_force_missing", "Should have raised ValueError", v)
    except ValueError:
        r.record_pass("select_force_missing", v)


def test_select_providers_parallel(r: TestResults, v: bool = False):
    from omnisearch import select_providers, Provider, QueryCategory, WEB_PROVIDERS
    avail = {p: True for p in Provider}
    selected = select_providers(QueryCategory.GENERAL_WEB, avail, parallel=True)
    if set(selected) == WEB_PROVIDERS:
        r.record_pass("select_parallel", v)
    else:
        r.record_fail("select_parallel", f"Expected WEB_PROVIDERS, got {selected}", v)


def test_select_providers_fallback(r: TestResults, v: bool = False):
    from omnisearch import select_providers, Provider, QueryCategory
    avail = {p: False for p in Provider}
    avail[Provider.TAVILY] = True
    selected = select_providers(QueryCategory.GENERAL_WEB, avail)
    if Provider.TAVILY in selected:
        r.record_pass("select_fallback", v)
    else:
        r.record_fail("select_fallback", f"Expected TAVILY in fallback, got {selected}", v)


def test_select_providers_none(r: TestResults, v: bool = False):
    from omnisearch import select_providers, Provider, QueryCategory
    avail = {p: False for p in Provider}
    try:
        select_providers(QueryCategory.GENERAL_WEB, avail)
        r.record_fail("select_none", "Should have raised ValueError", v)
    except ValueError:
        r.record_pass("select_none", v)


def test_routing_table_coverage(r: TestResults, v: bool = False):
    from omnisearch import ROUTING_TABLE, QueryCategory
    missing = [c for c in QueryCategory if c not in ROUTING_TABLE]
    if not missing:
        r.record_pass("routing_table_coverage", v)
    else:
        r.record_fail("routing_table_coverage", f"Missing categories: {missing}", v)


# ---------------------------------------------------------------------------
# Group: dedup (offline)
# ---------------------------------------------------------------------------

def test_dedup_exact_url(r: TestResults, v: bool = False):
    from omnisearch import deduplicate, UnifiedResult
    results = [
        UnifiedResult(title="A", url="https://example.com/page", snippet="short", source="brave", score=0.9),
        UnifiedResult(title="B", url="https://example.com/page", snippet="longer snippet here", source="tavily", score=0.8),
    ]
    deduped = deduplicate(results)
    if len(deduped) == 1 and deduped[0].snippet == "longer snippet here":
        r.record_pass("dedup_exact_url", v)
    else:
        r.record_fail("dedup_exact_url", f"Expected 1 result with longer snippet, got {len(deduped)}", v)


def test_dedup_normalized_url(r: TestResults, v: bool = False):
    from omnisearch import deduplicate, UnifiedResult
    results = [
        UnifiedResult(title="A", url="https://Example.Com/Page/", snippet="x", source="brave", score=0.9),
        UnifiedResult(title="B", url="https://example.com/page?ref=123", snippet="y", source="tavily", score=0.8),
    ]
    deduped = deduplicate(results)
    if len(deduped) == 1:
        r.record_pass("dedup_normalized_url", v)
    else:
        r.record_fail("dedup_normalized_url", f"Expected 1 result after URL normalization, got {len(deduped)}", v)


def test_dedup_title_jaccard(r: TestResults, v: bool = False):
    from omnisearch import deduplicate, UnifiedResult
    results = [
        UnifiedResult(title="Iran launches drone strikes on US bases", url="https://a.com/1", snippet="x", source="brave", score=0.9),
        UnifiedResult(title="Iran launches drone strikes on US military bases", url="https://b.com/2", snippet="y", source="tavily", score=0.8),
    ]
    deduped = deduplicate(results)
    if len(deduped) == 1:
        r.record_pass("dedup_title_jaccard", v)
    else:
        r.record_fail("dedup_title_jaccard", f"Expected 1 after title dedup, got {len(deduped)}", v)


def test_dedup_short_title_no_merge(r: TestResults, v: bool = False):
    from omnisearch import deduplicate, UnifiedResult
    results = [
        UnifiedResult(title="War", url="https://a.com/1", snippet="x", source="brave", score=0.9),
        UnifiedResult(title="War", url="https://b.com/2", snippet="y", source="tavily", score=0.8),
    ]
    deduped = deduplicate(results)
    if len(deduped) == 2:
        r.record_pass("dedup_short_title_no_merge", v)
    else:
        r.record_fail("dedup_short_title_no_merge", f"Expected 2 (short titles kept), got {len(deduped)}", v)


def test_dedup_sort_by_score(r: TestResults, v: bool = False):
    from omnisearch import deduplicate, UnifiedResult
    results = [
        UnifiedResult(title="Low score result aaa bbb", url="https://a.com/1", snippet="x", source="brave", score=0.3),
        UnifiedResult(title="High score result ccc ddd", url="https://b.com/2", snippet="y", source="tavily", score=0.95),
        UnifiedResult(title="Mid score result eee fff", url="https://c.com/3", snippet="z", source="exa", score=0.7),
    ]
    deduped = deduplicate(results)
    scores = [r.score for r in deduped]
    if scores == sorted(scores, reverse=True):
        r.record_pass("dedup_sort_by_score", v)
    else:
        r.record_fail("dedup_sort_by_score", f"Not sorted by score: {scores}", v)


def test_dedup_mixed_providers(r: TestResults, v: bool = False):
    from omnisearch import deduplicate, UnifiedResult
    results = [
        UnifiedResult(title="Unique brave result about defense", url="https://a.com/1", snippet="x", source="brave", score=0.9),
        UnifiedResult(title="Unique tavily result about defense", url="https://b.com/2", snippet="y", source="tavily", score=0.8),
        UnifiedResult(title="Same URL different source", url="https://a.com/1", snippet="longer snippet for dedup", source="exa", score=0.7),
    ]
    deduped = deduplicate(results)
    if len(deduped) == 2:
        r.record_pass("dedup_mixed_providers", v)
    else:
        r.record_fail("dedup_mixed_providers", f"Expected 2, got {len(deduped)}", v)


def test_url_normalize(r: TestResults, v: bool = False):
    from omnisearch import _normalize_url
    cases = [
        ("https://Example.COM/Path/?q=1", "example.com/path"),
        ("http://foo.bar/page/", "foo.bar/page"),
        ("https://a.com", "a.com"),
    ]
    for url, expected in cases:
        got = _normalize_url(url)
        if got != expected:
            r.record_fail("url_normalize", f"'{url}' → '{got}', expected '{expected}'", v)
            return
    r.record_pass("url_normalize", v)


def test_jaccard(r: TestResults, v: bool = False):
    from omnisearch import _jaccard
    cases = [
        ({"a", "b", "c"}, {"a", "b", "c"}, 1.0),
        ({"a", "b"}, {"c", "d"}, 0.0),
        ({"a", "b", "c"}, {"a", "b", "d"}, 0.5),
        (set(), {"a"}, 0.0),
    ]
    for a, b, expected in cases:
        got = _jaccard(a, b)
        if abs(got - expected) > 0.01:
            r.record_fail("jaccard", f"{a} ∩ {b} → {got}, expected {expected}", v)
            return
    r.record_pass("jaccard", v)


# ---------------------------------------------------------------------------
# Group: format (offline)
# ---------------------------------------------------------------------------

def test_format_results(r: TestResults, v: bool = False):
    from omnisearch import format_results, SearchResponse, UnifiedResult
    resp = SearchResponse(
        query="test", category="general_web", providers_used=["brave"],
        results=[UnifiedResult(title="Title", url="https://x.com", snippet="Snippet", source="brave", score=0.9)],
        total_results=1, deduplicated=0,
    )
    out = format_results(resp)
    if "Title" in out and "brave" in out and "https://x.com" in out:
        r.record_pass("format_results", v)
    else:
        r.record_fail("format_results", "Missing expected content in output", v)


def test_format_markdown(r: TestResults, v: bool = False):
    from omnisearch import format_markdown, SearchResponse, UnifiedResult
    resp = SearchResponse(
        query="test", category="news", providers_used=["tavily"],
        results=[UnifiedResult(title="News", url="https://n.com", snippet="Body", source="tavily", score=0.8)],
        answer="AI answer here", total_results=1, deduplicated=0,
    )
    out = format_markdown(resp)
    if "# Omnisearch:" in out and "## Answer" in out and "AI answer here" in out:
        r.record_pass("format_markdown", v)
    else:
        r.record_fail("format_markdown", "Missing markdown structure", v)


def test_to_json(r: TestResults, v: bool = False):
    from omnisearch import to_json, SearchResponse, UnifiedResult
    resp = SearchResponse(
        query="test", category="general_web", providers_used=["brave"],
        results=[UnifiedResult(title="T", url="https://x.com", snippet="S", source="brave", score=0.9, raw={"key": "val"})],
        total_results=1, deduplicated=0,
    )
    d = to_json(resp)
    if d["query"] == "test" and "raw" not in d["results"][0]:
        r.record_pass("to_json", v)
    else:
        r.record_fail("to_json", "JSON serialization incorrect or raw not stripped", v)


def test_format_no_text(r: TestResults, v: bool = False):
    from omnisearch import format_results, SearchResponse, UnifiedResult
    resp = SearchResponse(
        query="test", category="general_web", providers_used=["brave"],
        results=[UnifiedResult(title="Title", url="https://x.com", snippet="Should not appear", source="brave", score=0.9)],
        total_results=1, deduplicated=0,
    )
    out = format_results(resp, no_text=True)
    if "Title" in out and "Should not appear" not in out:
        r.record_pass("format_no_text", v)
    else:
        r.record_fail("format_no_text", "Snippet appeared in no_text mode", v)


def test_dedup_empty_results(r: TestResults, v: bool = False):
    from omnisearch import deduplicate
    deduped = deduplicate([])
    if len(deduped) == 0:
        r.record_pass("dedup_empty_results", v)
    else:
        r.record_fail("dedup_empty_results", f"Expected 0, got {len(deduped)}", v)


def test_format_answer_text(r: TestResults, v: bool = False):
    from omnisearch import format_results, SearchResponse, UnifiedResult
    resp = SearchResponse(
        query="test", category="factual_quick", providers_used=["tavily"],
        results=[UnifiedResult(title="T", url="https://x.com", snippet="S", source="tavily", score=0.9)],
        answer="The answer is 42.", total_results=1, deduplicated=0,
    )
    out = format_results(resp)
    if "ANSWER:" in out and "The answer is 42." in out:
        r.record_pass("format_answer_text", v)
    else:
        r.record_fail("format_answer_text", "Answer not rendered in text output", v)


def test_format_answer_markdown(r: TestResults, v: bool = False):
    from omnisearch import format_markdown, SearchResponse, UnifiedResult
    resp = SearchResponse(
        query="test", category="factual_quick", providers_used=["tavily"],
        results=[UnifiedResult(title="T", url="https://x.com", snippet="S", source="tavily", score=0.9)],
        answer="The answer is 42.", total_results=1, deduplicated=0,
    )
    out = format_markdown(resp)
    if "## Answer" in out and "The answer is 42." in out:
        r.record_pass("format_answer_markdown", v)
    else:
        r.record_fail("format_answer_markdown", "Answer not in markdown output", v)


def test_format_empty_results(r: TestResults, v: bool = False):
    from omnisearch import format_results, SearchResponse
    resp = SearchResponse(
        query="nothing", category="general_web", providers_used=["brave"],
        results=[], total_results=0, deduplicated=0,
    )
    out = format_results(resp)
    if "Results: 0" in out and "brave" in out:
        r.record_pass("format_empty_results", v)
    else:
        r.record_fail("format_empty_results", "Empty results not formatted correctly", v)


# ---------------------------------------------------------------------------
# Group: brave (live API)
# ---------------------------------------------------------------------------

def test_brave_web_search(r: TestResults, v: bool = False):
    if not has_key("BRAVE_API_KEY"):
        r.record_skip("brave_web_search", "BRAVE_API_KEY not set", v)
        return
    from brave_search import web_search
    try:
        result = web_search("Iran oil production", count=3)
        web_results = result.get("web", {}).get("results", [])
        if len(web_results) > 0:
            r.record_pass("brave_web_search", v)
        else:
            r.record_fail("brave_web_search", "No web results returned", v)
    except Exception as e:
        r.record_fail("brave_web_search", str(e), v)


def test_brave_news_search(r: TestResults, v: bool = False):
    if not has_key("BRAVE_API_KEY"):
        r.record_skip("brave_news_search", "BRAVE_API_KEY not set", v)
        return
    from brave_search import news_search
    try:
        result = news_search("conflict escalation", count=3)
        news = result.get("results", result.get("news", {}).get("results", []))
        if isinstance(news, list):
            r.record_pass("brave_news_search", v)
        else:
            r.record_fail("brave_news_search", f"Unexpected response shape", v)
    except Exception as e:
        r.record_fail("brave_news_search", str(e), v)


def test_brave_freshness(r: TestResults, v: bool = False):
    if not has_key("BRAVE_API_KEY"):
        r.record_skip("brave_freshness", "BRAVE_API_KEY not set", v)
        return
    from brave_search import web_search
    try:
        result = web_search("Iran news", count=3, freshness="pw")
        if "web" in result or "query" in result:
            r.record_pass("brave_freshness", v)
        else:
            r.record_fail("brave_freshness", "Missing expected keys", v)
    except Exception as e:
        r.record_fail("brave_freshness", str(e), v)


def test_brave_format(r: TestResults, v: bool = False):
    if not has_key("BRAVE_API_KEY"):
        r.record_skip("brave_format", "BRAVE_API_KEY not set", v)
        return
    from brave_search import web_search, format_results, format_markdown
    try:
        result = web_search("test query", count=2)
        text = format_results(result)
        md = format_markdown(result)
        if text and md and "# Search:" in md:
            r.record_pass("brave_format", v)
        else:
            r.record_fail("brave_format", "Formatter returned empty or malformed", v)
    except Exception as e:
        r.record_fail("brave_format", str(e), v)


# ---------------------------------------------------------------------------
# Group: tavily (live API)
# ---------------------------------------------------------------------------

def test_tavily_basic(r: TestResults, v: bool = False):
    if not has_key("TAVILY_API_KEY"):
        r.record_skip("tavily_basic", "TAVILY_API_KEY not set", v)
        return
    from tavily_search import search
    try:
        result = search("oil prices 2025", max_results=3)
        if result.get("results") and len(result["results"]) > 0:
            r.record_pass("tavily_basic", v)
        else:
            r.record_fail("tavily_basic", "No results", v)
    except Exception as e:
        r.record_fail("tavily_basic", str(e), v)


def test_tavily_advanced(r: TestResults, v: bool = False):
    if not has_key("TAVILY_API_KEY"):
        r.record_skip("tavily_advanced", "TAVILY_API_KEY not set", v)
        return
    from tavily_search import search
    try:
        result = search("semiconductor supply chain", search_depth="advanced", max_results=3)
        if result.get("results"):
            r.record_pass("tavily_advanced", v)
        else:
            r.record_fail("tavily_advanced", "No results from advanced search", v)
    except Exception as e:
        r.record_fail("tavily_advanced", str(e), v)


def test_tavily_answer(r: TestResults, v: bool = False):
    if not has_key("TAVILY_API_KEY"):
        r.record_skip("tavily_answer", "TAVILY_API_KEY not set", v)
        return
    from tavily_search import search
    try:
        result = search("what is the current oil price", include_answer=True, max_results=3)
        if result.get("answer"):
            r.record_pass("tavily_answer", v)
        else:
            r.record_fail("tavily_answer", "No answer returned", v)
    except Exception as e:
        r.record_fail("tavily_answer", str(e), v)


def test_tavily_extract(r: TestResults, v: bool = False):
    if not has_key("TAVILY_API_KEY"):
        r.record_skip("tavily_extract", "TAVILY_API_KEY not set", v)
        return
    from tavily_search import extract
    try:
        result = extract(["https://httpbin.org/html"])
        extracted = result.get("results", [])
        if len(extracted) > 0 and extracted[0].get("raw_content"):
            r.record_pass("tavily_extract", v)
        else:
            r.record_fail("tavily_extract", "No content extracted", v)
    except Exception as e:
        r.record_fail("tavily_extract", str(e), v)


# ---------------------------------------------------------------------------
# Group: xpoz (live API)
# ---------------------------------------------------------------------------

def test_xpoz_twitter(r: TestResults, v: bool = False):
    if not has_key("XPOZ_API_KEY"):
        r.record_skip("xpoz_twitter", "XPOZ_API_KEY not set", v)
        return
    import subprocess
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "xpoz_search.py"),
             "twitter", "Iran conflict", "-n", "3", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            if isinstance(data, (list, dict)):
                r.record_pass("xpoz_twitter", v)
            else:
                r.record_fail("xpoz_twitter", "Unexpected output type", v)
        else:
            r.record_fail("xpoz_twitter", proc.stderr.strip()[:200], v)
    except Exception as e:
        r.record_fail("xpoz_twitter", str(e), v)


def test_xpoz_reddit(r: TestResults, v: bool = False):
    if not has_key("XPOZ_API_KEY"):
        r.record_skip("xpoz_reddit", "XPOZ_API_KEY not set", v)
        return
    import subprocess
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "xpoz_search.py"),
             "reddit", "geopolitics Iran", "-n", "3", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            r.record_pass("xpoz_reddit", v)
        else:
            r.record_fail("xpoz_reddit", proc.stderr.strip()[:200], v)
    except Exception as e:
        r.record_fail("xpoz_reddit", str(e), v)


def test_xpoz_user_tweets(r: TestResults, v: bool = False):
    if not has_key("XPOZ_API_KEY"):
        r.record_skip("xpoz_user_tweets", "XPOZ_API_KEY not set", v)
        return
    import subprocess
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "xpoz_search.py"),
             "twitter-user", "elikishtaini", "-n", "3", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode == 0:
            r.record_pass("xpoz_user_tweets", v)
        else:
            r.record_fail("xpoz_user_tweets", proc.stderr.strip()[:200], v)
    except Exception as e:
        r.record_fail("xpoz_user_tweets", str(e), v)


# ---------------------------------------------------------------------------
# Group: integration (live API, cross-provider)
# ---------------------------------------------------------------------------

def test_integration_auto_route(r: TestResults, v: bool = False):
    any_key = any(has_key(k) for k in ["BRAVE_API_KEY", "TAVILY_API_KEY", "EXA_API_KEY"])
    if not any_key:
        r.record_skip("integration_auto_route", "No web API keys set", v)
        return
    from omnisearch import search
    try:
        resp = search("Iran missile defense", num=3)
        if resp.providers_used and resp.results:
            r.record_pass("integration_auto_route", v)
        else:
            r.record_fail("integration_auto_route", f"providers={resp.providers_used}, results={len(resp.results)}", v)
    except Exception as e:
        r.record_fail("integration_auto_route", str(e), v)


def test_integration_parallel(r: TestResults, v: bool = False):
    keys = sum(1 for k in ["BRAVE_API_KEY", "TAVILY_API_KEY", "EXA_API_KEY"] if has_key(k))
    if keys < 2:
        r.record_skip("integration_parallel", "Need 2+ web API keys for parallel test", v)
        return
    from omnisearch import search
    try:
        resp = search("oil infrastructure damage", num=3, parallel=True)
        if len(resp.providers_used) >= 2:
            r.record_pass("integration_parallel", v)
        else:
            r.record_fail("integration_parallel", f"Only {len(resp.providers_used)} providers used", v)
    except Exception as e:
        r.record_fail("integration_parallel", str(e), v)


def test_integration_cross_skill_exa(r: TestResults, v: bool = False):
    if not has_key("EXA_API_KEY"):
        r.record_skip("integration_cross_skill_exa", "EXA_API_KEY not set", v)
        return
    from omnisearch import search, QueryCategory, Provider
    try:
        resp = search("transformer architecture paper", num=3, force_provider=Provider.EXA)
        if "exa" in resp.providers_used and resp.results:
            r.record_pass("integration_cross_skill_exa", v)
        else:
            r.record_fail("integration_cross_skill_exa", f"Exa call failed: {resp.providers_used}", v)
    except Exception as e:
        r.record_fail("integration_cross_skill_exa", str(e), v)


def test_integration_json_output(r: TestResults, v: bool = False):
    any_key = any(has_key(k) for k in ["BRAVE_API_KEY", "TAVILY_API_KEY", "EXA_API_KEY"])
    if not any_key:
        r.record_skip("integration_json_output", "No web API keys set", v)
        return
    import subprocess
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "omnisearch.py"),
             "test query", "-n", "3", "--json"],
            capture_output=True, text=True, timeout=45,
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            if "query" in data and "results" in data and "providers_used" in data:
                r.record_pass("integration_json_output", v)
            else:
                r.record_fail("integration_json_output", f"Missing keys: {list(data.keys())}", v)
        else:
            r.record_fail("integration_json_output", proc.stderr.strip()[:200], v)
    except Exception as e:
        r.record_fail("integration_json_output", str(e), v)


# ---------------------------------------------------------------------------
# Test Registry
# ---------------------------------------------------------------------------

GROUPS = {
    "router": [
        test_classify_general,
        test_classify_news,
        test_classify_social,
        test_classify_academic,
        test_classify_factual,
        test_classify_company,
        test_classify_tech,
        test_select_providers_force,
        test_select_providers_force_missing,
        test_select_providers_parallel,
        test_select_providers_fallback,
        test_select_providers_none,
        test_routing_table_coverage,
    ],
    "dedup": [
        test_dedup_exact_url,
        test_dedup_normalized_url,
        test_dedup_title_jaccard,
        test_dedup_short_title_no_merge,
        test_dedup_sort_by_score,
        test_dedup_mixed_providers,
        test_dedup_empty_results,
        test_url_normalize,
        test_jaccard,
    ],
    "format": [
        test_format_results,
        test_format_markdown,
        test_to_json,
        test_format_no_text,
        test_format_answer_text,
        test_format_answer_markdown,
        test_format_empty_results,
    ],
    "brave": [
        test_brave_web_search,
        test_brave_news_search,
        test_brave_freshness,
        test_brave_format,
    ],
    "tavily": [
        test_tavily_basic,
        test_tavily_advanced,
        test_tavily_answer,
        test_tavily_extract,
    ],
    "xpoz": [
        test_xpoz_twitter,
        test_xpoz_reddit,
        test_xpoz_user_tweets,
    ],
    "integration": [
        test_integration_auto_route,
        test_integration_parallel,
        test_integration_cross_skill_exa,
        test_integration_json_output,
    ],
}

QUICK_GROUPS = ["router", "dedup", "format"]
LIVE_QUICK = {
    "brave": [test_brave_web_search],
    "tavily": [test_tavily_basic],
    "xpoz": [test_xpoz_twitter],
}


def main():
    parser = argparse.ArgumentParser(description="Omnisearch test suite")
    parser.add_argument("--quick", action="store_true", help="Offline tests + one basic per available key")
    parser.add_argument("--verbose", action="store_true", help="Detailed output")
    parser.add_argument("--group", choices=list(GROUPS.keys()), help="Run specific test group")
    args = parser.parse_args()

    results = TestResults()

    if args.group:
        groups_to_run = {args.group: GROUPS[args.group]}
    elif args.quick:
        groups_to_run = {g: GROUPS[g] for g in QUICK_GROUPS}
        for g, tests in LIVE_QUICK.items():
            groups_to_run[g] = tests
    else:
        groups_to_run = GROUPS

    for group_name, tests in groups_to_run.items():
        print(f"\n--- {group_name.upper()} ---")
        for test_fn in tests:
            test_fn(results, args.verbose)

    print(results.summary())
    sys.exit(0 if results.failed == 0 else 1)


if __name__ == "__main__":
    main()
