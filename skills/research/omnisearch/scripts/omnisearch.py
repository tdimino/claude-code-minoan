#!/usr/bin/env python3
"""
Omnisearch Meta-Router — unified search across Brave, Tavily, Xpoz, Exa, and Firecrawl.

Routes queries to the best search API based on automatic classification, or runs
parallel searches across multiple providers and deduplicates results.

Providers:
  brave     — Google-indexed web + news, LLM Context API ($5/1k requests)
  tavily    — Agent-native search with AI answers, free 1000/month
  xpoz      — Social media: Twitter/X, Reddit, Instagram (free 100K/month)
  exa       — Neural/semantic search, research papers (cross-skill subprocess)
  firecrawl — Web scraping + search (cross-skill subprocess)

Usage:
    omnisearch.py "Iran oil sanctions"                      # Auto-route to best provider
    omnisearch.py "Iran oil sanctions" --provider brave      # Force specific provider
    omnisearch.py "Iran oil sanctions" --parallel            # All web providers, merged
    omnisearch.py "Strait of Hormuz" --social                # Social media (Xpoz)
    omnisearch.py "who is the IRGC commander" --answer       # AI answer (Tavily/Brave)
    omnisearch.py "transformer architecture paper" --academic # Route to Exa
    omnisearch.py "latest drone strike" --news --parallel    # News from all sources

Requires: At least one of BRAVE_API_KEY, TAVILY_API_KEY, XPOZ_API_KEY
Optional: EXA_API_KEY, FIRECRAWL_API_KEY (for cross-skill routing)
Install: pip install requests
"""

import os
import sys
import json
import re
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Enums & Data Types
# ---------------------------------------------------------------------------

class QueryCategory(Enum):
    GENERAL_WEB = "general_web"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    ACADEMIC = "academic"
    FACTUAL_QUICK = "factual_quick"
    COMPANY_RESEARCH = "company_research"
    TECHNICAL_DOCS = "technical_docs"


class Provider(Enum):
    BRAVE = "brave"
    TAVILY = "tavily"
    XPOZ = "xpoz"
    EXA = "exa"
    FIRECRAWL = "firecrawl"


@dataclass
class UnifiedResult:
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    published_date: str = ""
    score: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    query: str
    category: str = ""
    providers_used: List[str] = field(default_factory=list)
    results: List[UnifiedResult] = field(default_factory=list)
    answer: Optional[str] = None
    total_results: int = 0
    deduplicated: int = 0


# ---------------------------------------------------------------------------
# Provider Availability
# ---------------------------------------------------------------------------

PROVIDER_KEYS: Dict[Provider, str] = {
    Provider.BRAVE: "BRAVE_API_KEY",
    Provider.TAVILY: "TAVILY_API_KEY",
    Provider.XPOZ: "XPOZ_API_KEY",
    Provider.EXA: "EXA_API_KEY",
    Provider.FIRECRAWL: "FIRECRAWL_API_KEY",
}

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
EXA_SCRIPT = os.path.expanduser("~/.claude/skills/exa-search/scripts/exa_search.py")
FIRECRAWL_SCRIPT = os.path.expanduser("~/.claude/skills/firecrawl/scripts/firecrawl_api.py")


def get_available() -> Dict[Provider, bool]:
    """Check which provider API keys are set."""
    return {p: bool(os.environ.get(k)) for p, k in PROVIDER_KEYS.items()}


# ---------------------------------------------------------------------------
# Query Classification
# ---------------------------------------------------------------------------

_SOCIAL_PATTERNS = re.compile(
    r"@\w+|#\w+|\btweet\b|\btwitter\b|\breddit\b|\br/\w+|\btiktok\b"
    r"|\binstagram\b|\bon twitter\b|\bon reddit\b|\bsubreddit\b",
    re.IGNORECASE,
)
_NEWS_PATTERNS = re.compile(
    r"\blatest\b|\bbreaking\b|\btoday\b|\byesterday\b|\bthis week\b"
    r"|\bnews about\b|\brecent\b|\bjust happened\b|\breported\b",
    re.IGNORECASE,
)
_ACADEMIC_PATTERNS = re.compile(
    r"\bpaper\b|\bresearch paper\b|\barxiv\b|\bstudy\b|\bjournal\b"
    r"|\bpublication\b|\bcitation\b|\bscholar\b",
    re.IGNORECASE,
)
_QUICK_PATTERNS = re.compile(
    r"^(who|what|when|where|how many|how much|is |are |was |were |did )\b",
    re.IGNORECASE,
)
_COMPANY_PATTERNS = re.compile(
    r"\bcompany\b|\bstartup\b|\bfunding\b|\bvaluation\b|\bcompetitor\b"
    r"|\bseries [a-z]\b|\bipo\b|\bacquisition\b",
    re.IGNORECASE,
)
_TECH_PATTERNS = re.compile(
    r"\bdocumentation\b|\bapi\b|\btutorial\b|\bhow to\b|\binstall\b"
    r"|\bconfigure\b|\bsetup\b|\bsdk\b",
    re.IGNORECASE,
)


def classify_query(query: str) -> QueryCategory:
    """Classify a query to determine optimal provider routing."""
    if _SOCIAL_PATTERNS.search(query):
        return QueryCategory.SOCIAL_MEDIA
    if _NEWS_PATTERNS.search(query):
        return QueryCategory.NEWS
    if _ACADEMIC_PATTERNS.search(query):
        return QueryCategory.ACADEMIC
    if _QUICK_PATTERNS.match(query) and len(query.split()) < 12:
        return QueryCategory.FACTUAL_QUICK
    if _COMPANY_PATTERNS.search(query):
        return QueryCategory.COMPANY_RESEARCH
    if _TECH_PATTERNS.search(query):
        return QueryCategory.TECHNICAL_DOCS
    return QueryCategory.GENERAL_WEB


# ---------------------------------------------------------------------------
# Routing Table
# ---------------------------------------------------------------------------

ROUTING_TABLE: Dict[QueryCategory, List[Provider]] = {
    QueryCategory.GENERAL_WEB: [Provider.BRAVE, Provider.TAVILY, Provider.EXA],
    QueryCategory.NEWS: [Provider.BRAVE, Provider.TAVILY],
    QueryCategory.SOCIAL_MEDIA: [Provider.XPOZ],
    QueryCategory.ACADEMIC: [Provider.EXA, Provider.TAVILY],
    QueryCategory.FACTUAL_QUICK: [Provider.TAVILY, Provider.BRAVE],
    QueryCategory.COMPANY_RESEARCH: [Provider.EXA, Provider.BRAVE],
    QueryCategory.TECHNICAL_DOCS: [Provider.EXA, Provider.FIRECRAWL],
}

WEB_PROVIDERS = {Provider.BRAVE, Provider.TAVILY, Provider.EXA, Provider.FIRECRAWL}


def select_providers(
    category: QueryCategory,
    available: Dict[Provider, bool],
    force: Optional[Provider] = None,
    parallel: bool = False,
) -> List[Provider]:
    """Pick providers based on category, availability, and flags."""
    if force:
        if not available.get(force, False):
            env_key = PROVIDER_KEYS.get(force, "UNKNOWN")
            raise ValueError(
                f"Provider {force.value} requested but {env_key} is not set."
            )
        return [force]

    if parallel:
        return [p for p in WEB_PROVIDERS if available.get(p, False)]

    preferred = ROUTING_TABLE.get(category, [Provider.BRAVE, Provider.TAVILY])
    selected = [p for p in preferred if available.get(p, False)]
    if selected:
        return selected[:1]

    fallback = [p for p in Provider if available.get(p, False) and p != Provider.XPOZ]
    if fallback:
        return fallback[:1]

    raise ValueError(
        "No search API keys configured. Set at least one of: "
        + ", ".join(PROVIDER_KEYS.values())
    )


# ---------------------------------------------------------------------------
# Provider Callers
# ---------------------------------------------------------------------------

def _call_brave(query: str, num: int, **kwargs) -> List[UnifiedResult]:
    """Call brave_search.py and normalize results."""
    import brave_search

    if kwargs.get("news"):
        raw = brave_search.news_search(query, count=min(num, 20))
    else:
        raw = brave_search.web_search(query, count=min(num, 20), extra_snippets=True)

    results = []
    web_results = raw.get("web", {}).get("results", [])
    news_results = raw.get("news", {}).get("results", [])

    for i, r in enumerate(web_results[:num]):
        extras = r.get("extra_snippets", [])
        snippet = r.get("description", "")
        if extras:
            snippet = snippet + " " + " ".join(extras[:2])
        results.append(UnifiedResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=snippet.strip(),
            source="brave",
            published_date=r.get("page_age", ""),
            score=round(1.0 - (i * 0.05), 3),
            raw=r,
        ))

    for i, r in enumerate(news_results[:num]):
        results.append(UnifiedResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("description", ""),
            source="brave/news",
            published_date=r.get("age", ""),
            score=round(0.9 - (i * 0.05), 3),
            raw=r,
        ))

    return results


def _call_tavily(query: str, num: int, want_answer: bool = False, **kwargs) -> tuple:
    """Call tavily_search.py and normalize. Returns (results, answer_or_None)."""
    import tavily_search

    topic = "news" if kwargs.get("news") else "general"
    raw = tavily_search.search(
        query, max_results=min(num, 20), include_answer=want_answer, topic=topic,
    )

    results = []
    for r in raw.get("results", [])[:num]:
        results.append(UnifiedResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("content", ""),
            source="tavily",
            published_date=r.get("published_date", ""),
            score=round(r.get("score", 0.0), 3),
            raw=r,
        ))

    answer = raw.get("answer") if want_answer else None
    return results, answer


def _run_subprocess(cmd: List[str], label: str, timeout: int = 30) -> Any:
    """Run a subprocess, return parsed JSON output."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"{label} exit code {proc.returncode}")
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"{label} returned invalid JSON: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"{label} timed out after {timeout}s") from e


def _call_xpoz(query: str, num: int, platform: str = "twitter", **kwargs) -> List[UnifiedResult]:
    """Call xpoz_search.py via subprocess (SDK import is fragile cross-module)."""
    cmd = [
        sys.executable,
        os.path.join(SCRIPTS_DIR, "xpoz_search.py"),
        platform, query, "-n", str(num), "--json",
    ]
    if kwargs.get("subreddit"):
        cmd.extend(["--subreddit", kwargs["subreddit"]])

    raw = _run_subprocess(cmd, "xpoz")

    results = []
    items = raw if isinstance(raw, list) else raw.get("results", raw.get("data", []))
    if isinstance(items, dict):
        items = [items]

    for i, r in enumerate(items[:num]):
        title = r.get("text", r.get("title", r.get("content", "")))[:120]
        url = r.get("url", r.get("link", ""))
        snippet = r.get("text", r.get("content", r.get("body", "")))
        results.append(UnifiedResult(
            title=title,
            url=url,
            snippet=snippet[:500],
            source=f"xpoz/{platform}",
            published_date=r.get("created_at", r.get("date", "")),
            score=round(1.0 - (i * 0.03), 3),
            raw=r,
        ))
    return results


def _call_exa(query: str, num: int, **kwargs) -> List[UnifiedResult]:
    """Call exa_search.py via subprocess."""
    if not os.path.isfile(EXA_SCRIPT):
        raise RuntimeError(f"Exa skill not found at {EXA_SCRIPT}")

    cmd = [sys.executable, EXA_SCRIPT, query, "-n", str(num), "--json"]
    if kwargs.get("category"):
        cmd.extend(["--category", kwargs["category"]])

    raw = _run_subprocess(cmd, "exa")

    results = []
    for r in raw.get("results", [])[:num]:
        results.append(UnifiedResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("text", r.get("summary", ""))[:500],
            source="exa",
            published_date=r.get("publishedDate", ""),
            score=round(r.get("score", 0.0), 3),
            raw=r,
        ))
    return results


def _call_firecrawl(query: str, num: int, **kwargs) -> List[UnifiedResult]:
    """Call firecrawl_api.py search via subprocess."""
    if not os.path.isfile(FIRECRAWL_SCRIPT):
        raise RuntimeError(f"Firecrawl skill not found at {FIRECRAWL_SCRIPT}")

    cmd = [sys.executable, FIRECRAWL_SCRIPT, "search", query, "-n", str(num), "--json"]

    raw = _run_subprocess(cmd, "firecrawl")

    results = []
    items = raw if isinstance(raw, list) else raw.get("data", raw.get("results", []))
    for i, r in enumerate(items[:num]):
        results.append(UnifiedResult(
            title=r.get("title", r.get("metadata", {}).get("title", "")),
            url=r.get("url", ""),
            snippet=r.get("markdown", r.get("description", ""))[:500],
            source="firecrawl",
            published_date="",
            score=round(1.0 - (i * 0.05), 3),
            raw=r,
        ))
    return results


PROVIDER_CALLERS: Dict[Provider, Callable] = {
    Provider.BRAVE: _call_brave,
    Provider.EXA: _call_exa,
    Provider.FIRECRAWL: _call_firecrawl,
    # TAVILY and XPOZ are handled inline in search() — they use direct import
    # and subprocess respectively, not the generic _call pattern.
}


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    """Normalize URL for dedup: strip query params, fragment, trailing slash, lowercase."""
    parsed = urlparse(url)
    return f"{parsed.netloc}{parsed.path}".rstrip("/").lower()


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def deduplicate(results: List[UnifiedResult], threshold: float = 0.85) -> List[UnifiedResult]:
    """Remove near-duplicate results by URL and title similarity."""
    seen_urls: Dict[str, int] = {}
    seen_titles: List[set] = []
    kept: List[UnifiedResult] = []

    for r in results:
        norm = _normalize_url(r.url)

        if norm in seen_urls:
            idx = seen_urls[norm]
            if len(r.snippet) > len(kept[idx].snippet):
                kept[idx] = r
                seen_titles[idx] = set(r.title.lower().split())
            continue

        title_tokens = set(r.title.lower().split())
        if len(title_tokens) >= 3:
            is_dup = any(_jaccard(title_tokens, t) > threshold for t in seen_titles)
            if is_dup:
                continue

        seen_urls[norm] = len(kept)
        seen_titles.append(title_tokens)
        kept.append(r)

    return sorted(kept, key=lambda x: x.score, reverse=True)


# ---------------------------------------------------------------------------
# Search Orchestration
# ---------------------------------------------------------------------------

def search(
    query: str,
    num: int = 10,
    category_override: Optional[QueryCategory] = None,
    force_provider: Optional[Provider] = None,
    parallel: bool = False,
    want_answer: bool = False,
    news: bool = False,
    social_platform: str = "twitter",
    **kwargs,
) -> SearchResponse:
    """Execute a search with automatic or manual routing."""
    available = get_available()

    if category_override:
        category = category_override
    elif force_provider == Provider.XPOZ:
        category = QueryCategory.SOCIAL_MEDIA
    elif news:
        category = QueryCategory.NEWS
    else:
        category = classify_query(query)

    providers = select_providers(category, available, force=force_provider, parallel=parallel)

    all_results: List[UnifiedResult] = []
    answer: Optional[str] = None
    providers_used: List[str] = []

    call_kwargs = {**kwargs, "news": news}

    if len(providers) == 1:
        p = providers[0]
        try:
            if p == Provider.TAVILY:
                res, ans = _call_tavily(query, num, want_answer=want_answer, **call_kwargs)
                all_results.extend(res)
                if ans:
                    answer = ans
            elif p == Provider.XPOZ:
                all_results.extend(_call_xpoz(query, num, platform=social_platform, **call_kwargs))
            else:
                caller = PROVIDER_CALLERS[p]
                all_results.extend(caller(query, num, **call_kwargs))
            providers_used.append(p.value)
        except Exception as e:
            print(f"Error from {p.value}: {e}", file=sys.stderr)
    else:
        with ThreadPoolExecutor(max_workers=min(len(providers), 4)) as pool:
            futures = {}
            for p in providers:
                if p == Provider.TAVILY:
                    fut = pool.submit(_call_tavily, query, num, want_answer=want_answer, **call_kwargs)
                elif p == Provider.XPOZ:
                    fut = pool.submit(_call_xpoz, query, num, platform=social_platform, **call_kwargs)
                else:
                    caller = PROVIDER_CALLERS[p]
                    fut = pool.submit(caller, query, num, **call_kwargs)
                futures[fut] = p

            for fut in as_completed(futures, timeout=45):
                p = futures[fut]
                try:
                    result = fut.result()
                    if p == Provider.TAVILY:
                        res, ans = result
                        all_results.extend(res)
                        if ans and not answer:
                            answer = ans
                    else:
                        all_results.extend(result)
                    providers_used.append(p.value)
                except Exception as e:
                    print(f"Warning: {p.value} failed: {e}", file=sys.stderr)

    total = len(all_results)
    deduped = deduplicate(all_results)

    return SearchResponse(
        query=query,
        category=category.value,
        providers_used=sorted(providers_used),
        results=deduped[:num],
        answer=answer,
        total_results=total,
        deduplicated=total - len(deduped),
    )


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def format_results(resp: SearchResponse, no_text: bool = False) -> str:
    """Human-readable output."""
    lines = [
        f"Request ID: omnisearch-{resp.category}",
        f"Providers: {', '.join(resp.providers_used)}",
        f"Results: {len(resp.results)} (deduped {resp.deduplicated} from {resp.total_results} total)",
        "=" * 60,
    ]

    if resp.answer:
        lines.append(f"\nANSWER:\n{resp.answer}\n")
        lines.append("-" * 60)

    for i, r in enumerate(resp.results, 1):
        lines.append(f"\n[{i}] {r.title}")
        lines.append(f"    URL: {r.url}")
        lines.append(f"    Source: {r.source}  Score: {r.score}")
        if r.published_date:
            lines.append(f"    Published: {r.published_date}")
        if not no_text and r.snippet:
            snippet = r.snippet[:300]
            if len(r.snippet) > 300:
                snippet += "..."
            lines.append(f"    {snippet}")

    return "\n".join(lines)


def format_markdown(resp: SearchResponse) -> str:
    """Markdown output."""
    lines = [
        f"# Omnisearch: {resp.query}",
        f"**Category:** {resp.category} | **Providers:** {', '.join(resp.providers_used)} "
        f"| **Results:** {len(resp.results)} (deduped {resp.deduplicated})\n",
    ]

    if resp.answer:
        lines.append(f"## Answer\n\n{resp.answer}\n")

    lines.append("## Results\n")
    for i, r in enumerate(resp.results, 1):
        lines.append(f"{i}. **[{r.title}]({r.url})** ({r.source}, {r.score})")
        if r.published_date:
            lines.append(f"   *{r.published_date}*")
        if r.snippet:
            lines.append(f"   {r.snippet[:200]}\n")

    return "\n".join(lines)


def to_json(resp: SearchResponse) -> Dict[str, Any]:
    """Serialize to JSON-safe dict."""
    d = {
        "query": resp.query,
        "category": resp.category,
        "providers_used": resp.providers_used,
        "answer": resp.answer,
        "total_results": resp.total_results,
        "deduplicated": resp.deduplicated,
        "results": [asdict(r) for r in resp.results],
    }
    for r in d["results"]:
        r.pop("raw", None)
    return d


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Omnisearch — unified web & social search across 5 providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "Iran oil sanctions"                         # Auto-route
    %(prog)s "Iran oil sanctions" --provider brave         # Force Brave
    %(prog)s "Iran oil sanctions" --parallel               # All web providers
    %(prog)s "Strait of Hormuz twitter" --social           # Xpoz social
    %(prog)s "who is Iran defense minister" --answer       # AI answer
    %(prog)s "transformer paper" --academic                # Route to Exa
    %(prog)s "latest drone strike" --news --parallel       # News everywhere
""",
    )

    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=10, help="Results per provider (default 10)")

    route_group = parser.add_argument_group("routing")
    route_group.add_argument(
        "--provider", choices=[p.value for p in Provider],
        help="Force a specific provider",
    )
    route_group.add_argument("--parallel", action="store_true", help="Search all web providers, merge results")
    route_group.add_argument("--social", action="store_true", help="Social media search (Xpoz)")
    route_group.add_argument("--platform", default="twitter",
                             choices=["twitter", "reddit", "instagram"],
                             help="Social platform (default: twitter)")

    hint_group = parser.add_argument_group("query type hints")
    hint_group.add_argument("--news", action="store_true", help="Treat as news query")
    hint_group.add_argument("--academic", action="store_true", help="Treat as academic query")
    hint_group.add_argument("--answer", action="store_true", help="Request AI-generated answer")

    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument("--json", action="store_true", help="Raw JSON output")
    out_group.add_argument("--markdown", action="store_true", help="Markdown output")

    parser.add_argument("--no-text", action="store_true", help="Titles/URLs only")
    parser.add_argument("--verbose", action="store_true", help="Show routing decisions")
    parser.add_argument("--subreddit", help="Reddit subreddit for --social --platform reddit")

    args = parser.parse_args()

    category_override = None
    if args.social:
        category_override = QueryCategory.SOCIAL_MEDIA
    elif args.academic:
        category_override = QueryCategory.ACADEMIC
    elif args.news:
        category_override = QueryCategory.NEWS

    force = Provider(args.provider) if args.provider else None
    if args.social and not force:
        force = Provider.XPOZ

    if args.verbose:
        avail = get_available()
        active = [p.value for p, ok in avail.items() if ok]
        cat = category_override or classify_query(args.query)
        print(f"Classification: {cat.value}", file=sys.stderr)
        print(f"Available: {', '.join(active)}", file=sys.stderr)
        providers = select_providers(cat, avail, force=force, parallel=args.parallel)
        print(f"Selected: {', '.join(p.value for p in providers)}", file=sys.stderr)
        print("-" * 40, file=sys.stderr)

    try:
        resp = search(
            query=args.query,
            num=args.num,
            category_override=category_override,
            force_provider=force,
            parallel=args.parallel,
            want_answer=args.answer,
            news=args.news,
            social_platform=args.platform,
            subreddit=args.subreddit,
        )

        if args.json:
            print(json.dumps(to_json(resp), indent=2))
        elif args.markdown:
            print(format_markdown(resp))
        else:
            print(format_results(resp, no_text=args.no_text))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except (RuntimeError, OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
