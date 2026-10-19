#!/usr/bin/env python3
"""
Exa Search - web search on Exa's /search endpoint (Exa 3.0, spec 2.0.0).

Search types:
- auto (default, ~1s, $7/1k): best quality/speed balance; contents for 10 results included
- lite (--lite, $4/1k): cache-only, cheapest; accepts query, category, numResults,
  domains, dates, contents.text/highlights, snapshotAsOf, location, moderation only
- deep-lite (--deep-lite, ~4s, $12/1k) and deep (--deep, 4-15s, $12/1k): multi-step
  search with synthesis
- legacy: --fast, --instant, --deep-reasoning, --neural (still accepted, print a hint)

Features:
- Structured output (outputSchema) on every type except lite, with field-level grounding
- 5 preset schemas: company, paper-survey, competitor-analysis, person, news-digest
- Categories: company, publication, news, personal site, financial report, people
- Domain, date, and location filters; content moderation
- Content options: text (maxCharacters, verbosity, sections), highlights (incl. Dynamic
  Highlights beta), summary, extras, snapshot-as-of
- Response warnings → stderr; notices → shown with the results

Usage:
    exa_search.py "AI agent frameworks" -n 10
    exa_search.py "python requests timeout" --lite --highlights --no-text
    exa_search.py "transformer papers" --category publication --deep
    exa_search.py "Top AI startups" --deep --schema-preset company
    exa_search.py "Who is the CEO of Stripe?" --text-output "Short answer"
    exa_search.py "solar costs" --dynamic --no-text

Requires: EXA_API_KEY environment variable
Install: pip install requests
"""

import json
import argparse
from typing import Optional, List, Dict, Any, Tuple

from _exa_common import (  # PRESET_SCHEMAS is re-exported for callers that import it from here
    CATEGORY_CHOICES, LIVECRAWL_CHOICES, PRESET_SCHEMAS, VALID_SECTIONS, ExaAPIError, add_list_arg,
    add_schema_args, check_snapshot, context_option, date_bound, die, extras_option, format_cost,
    format_grounding, format_notices, highlights_option, legacy, load_schema, note, parse_location, post,
    report_warnings, resolve_category, resolve_max_age, text_option,
)

__all__ = ["PRESET_SCHEMAS", "build_search_payload", "search", "format_results"]

SEARCH_TYPES = ["auto", "lite", "deep-lite", "deep", "fast", "instant", "deep-reasoning", "neural"]
DEEP_TYPES = ("deep-lite", "deep", "deep-reasoning")
LEGACY_TYPES = {
    "fast": "use --lite (cheaper) or the default auto.",
    "instant": "use --lite.",
    "deep-reasoning": "use --deep, or exa_agent.py for multi-hop research.",
    "neural": "sent as auto (neural is no longer a documented type).",
}


def build_search_payload(
    query: str,
    search_type: str = "auto",
    additional_queries: Optional[List[str]] = None,
    output_schema: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    objective: Optional[str] = None,
    category: Optional[str] = None,
    num_results: int = 10,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    include_text: Optional[List[str]] = None,
    exclude_text: Optional[List[str]] = None,
    get_text: bool = True,
    max_characters: Optional[int] = None,
    get_summary: Optional[str] = None,
    get_highlights: bool = False,
    highlights_query: Optional[str] = None,
    highlights_max_chars: Optional[int] = None,
    dynamic_highlights: bool = False,
    get_context: bool = False,
    context_max_chars: Optional[int] = None,
    subpages: int = 0,
    subpage_target: Optional[str] = None,
    get_links: int = 0,
    get_image_links: int = 0,
    max_age_hours: Optional[int] = None,
    livecrawl: Optional[str] = None,
    snapshot_as_of: Optional[str] = None,
    verbosity: Optional[str] = None,
    include_sections: Optional[List[str]] = None,
    exclude_sections: Optional[List[str]] = None,
    user_location: Any = None,
    moderation: bool = False,
) -> Tuple[Dict[str, Any], List[str]]:
    """Build the /search request body. Returns (payload, beta flags).

    Validation that Exa does server-side (what lite accepts, schema limits,
    category filter restrictions) is left to the server so its message surfaces.
    """
    if search_type not in SEARCH_TYPES:
        raise ValueError(f"Invalid search type '{search_type}'. Must be one of: {SEARCH_TYPES}")
    if num_results < 1:
        raise ValueError("-n/--num must be at least 1")
    check_snapshot(snapshot_as_of, max_age_hours, livecrawl, subpages)
    if snapshot_as_of and (category or search_type in ("deep", "deep-reasoning")):
        raise ValueError("--snapshot-as-of does not support --category, --deep, or --deep-reasoning")
    if additional_queries and len(additional_queries) > 10:
        raise ValueError("--additional-queries accepts at most 10 queries")
    highlights, betas = highlights_option(get_highlights, highlights_query, highlights_max_chars,
                                          dynamic_highlights)

    payload: Dict[str, Any] = {
        "query": query,
        "type": "auto" if search_type == "neural" else search_type,
        "numResults": min(num_results, 100),
    }

    if additional_queries:
        if search_type in DEEP_TYPES:
            payload["additionalQueries"] = additional_queries
        else:
            note("--additional-queries ignored; it applies only to --deep-lite/--deep.")
    if output_schema:
        payload["outputSchema"] = output_schema
    if system_prompt:
        payload["systemPrompt"] = system_prompt
    if objective:
        payload["objective"] = objective

    category = resolve_category(category)
    if category:
        payload["category"] = category

    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains
    if start_published_date:
        payload["startPublishedDate"] = date_bound(start_published_date)
    if end_published_date:
        payload["endPublishedDate"] = date_bound(end_published_date, end=True)

    if include_text:
        legacy("--must-include", "Exa matches it approximately at word level; prefer a sharper query or --domains.")
        payload["includeText"] = include_text
    if exclude_text:
        legacy("--must-exclude", "Exa matches it approximately at word level; prefer --exclude-domains.")
        payload["excludeText"] = exclude_text

    if user_location:
        payload["userLocation"] = user_location
    if moderation:
        payload["moderation"] = True

    contents: Dict[str, Any] = {}

    if get_text:
        contents["text"] = text_option(max_characters, verbosity, include_sections, exclude_sections)
    if get_summary:
        contents["summary"] = {"query": get_summary}
    if highlights is not None:
        contents["highlights"] = highlights

    max_age = resolve_max_age(max_age_hours, livecrawl, lite=search_type == "lite")
    if max_age is not None:
        contents["maxAgeHours"] = max_age
    if snapshot_as_of:
        contents["snapshotAsOf"] = snapshot_as_of

    context = context_option(get_context, context_max_chars)
    if context is not None:
        contents["context"] = context

    if subpages > 0:
        legacy("--subpages", "deprecated on /search; prefer exa_contents.py URL --subpages N.")
        contents["subpages"] = subpages
        if subpage_target:
            contents["subpageTarget"] = subpage_target

    extras = extras_option(get_links, get_image_links)
    if extras:
        contents["extras"] = extras

    if contents:
        payload["contents"] = contents
    return payload, betas


def search(query: str, **kwargs) -> Dict[str, Any]:
    """Run a /search request. Keyword arguments match build_search_payload."""
    payload, betas = build_search_payload(query, **kwargs)
    return post("/search", payload, betas=betas)


def _format_entity(entity: Dict[str, Any]) -> List[str]:
    etype = entity.get("type", "unknown")
    props = entity.get("properties") or {}
    out = [f"    ENTITY ({etype}):"]
    if etype == "company":
        if props.get("name"):
            out.append(f"      Name: {props['name']}")
        if props.get("foundedYear"):
            out.append(f"      Founded: {props['foundedYear']}")
        if props.get("description"):
            out.append(f"      Description: {props['description'][:200]}")
        hq = props.get("headquarters")
        if hq:
            parts = [hq.get("city"), hq.get("country")]
            out.append(f"      HQ: {', '.join(p for p in parts if p)}")
        fin = props.get("financials") or {}
        if fin.get("fundingTotal"):
            out.append(f"      Total Funding: ${fin['fundingTotal']:,}")
        if fin.get("revenueAnnual"):
            out.append(f"      Annual Revenue: ${fin['revenueAnnual']:,}")
        wf = props.get("workforce") or {}
        if wf.get("total"):
            out.append(f"      Employees: {wf['total']:,}")
        wt = props.get("webTraffic") or {}
        if wt.get("visitsMonthly"):
            out.append(f"      Monthly Visits: {wt['visitsMonthly']:,}")
    elif etype == "person":
        if props.get("name"):
            out.append(f"      Name: {props['name']}")
        if props.get("location"):
            out.append(f"      Location: {props['location']}")
        for wh in (props.get("workHistory") or [])[:3]:
            title = wh.get("title", "")
            company = (wh.get("company") or {}).get("name", "")
            if title or company:
                out.append(f"      {title}{' @ ' + company if company else ''}")
    elif etype == "publication":
        if props.get("title"):
            out.append(f"      Title: {props['title']}")
        authors = [a.get("name") for a in (props.get("authors") or []) if a.get("name")]
        if authors:
            more = f" +{len(authors) - 5}" if len(authors) > 5 else ""
            out.append(f"      Authors: {', '.join(authors[:5])}{more}")
        for label, key in [("Year", "year"), ("Citations", "citationCount"), ("DOI", "doi")]:
            if props.get(key) is not None:
                out.append(f"      {label}: {props[key]}")
    else:
        for key, val in list(props.items())[:6]:
            if isinstance(val, (str, int, float)):
                out.append(f"      {key}: {str(val)[:120]}")
    return out


def format_results(results: Dict[str, Any], max_text_length: int = 500, show_cost: bool = False) -> str:
    """Format search results for readable display."""
    output = []

    if results.get("requestId"):
        output.append(f"Request ID: {results['requestId']}")
    output.extend(format_notices(results))

    if results.get("context"):
        output.append(f"\n{'='*60}")
        output.append("CONTEXT STRING (for RAG):")
        output.append("-" * 40)
        ctx = results["context"][:2000]
        if len(results["context"]) > 2000:
            ctx += "\n... [truncated]"
        output.append(ctx)

    search_results = results.get("results") or []
    output.append(f"\n{'='*60}")
    output.append(f"RESULTS ({len(search_results)} found):")
    if search_results:

        for i, r in enumerate(search_results, 1):
            output.append(f"\n[{i}] {r.get('title') or 'No title'}")
            output.append(f"    URL: {r.get('url', 'No URL')}")

            if r.get('author'):
                output.append(f"    Author: {r['author'][:80]}")
            if r.get('publishedDate'):
                output.append(f"    Published: {r['publishedDate'][:10]}")

            if r.get('summary'):
                output.append(f"    Summary: {r['summary'][:300]}...")

            if r.get('highlights'):
                output.append("    Highlights:")
                for h in r['highlights'][:3]:
                    output.append(f"      - {h[:200]}...")

            if r.get('text'):
                text = r['text'][:max_text_length]
                if len(r['text']) > max_text_length:
                    text += "..."
                output.append(f"    Text: {text}")

            if r.get('subpages'):
                output.append(f"    Subpages: {len(r['subpages'])} found")
                for sp in r['subpages'][:3]:
                    output.append(f"      - {(sp.get('title') or 'No title')[:60]}")
                    output.append(f"        {sp.get('url', '')}")

            if r.get('extras'):
                extras = r['extras']
                if extras.get('links'):
                    output.append(f"    Links: {len(extras['links'])} extracted")
                if extras.get('imageLinks'):
                    output.append(f"    Images: {len(extras['imageLinks'])} found")

            for entity in r.get('entities') or []:
                output.extend(_format_entity(entity))

    # Synthesized output (outputSchema): text or JSON, with field-level grounding
    if results.get("output"):
        output_data = results["output"]
        output.append(f"\n{'='*60}")
        output.append("STRUCTURED OUTPUT:")
        output.append("-" * 40)

        content = output_data.get("content")
        if isinstance(content, str):
            output.append(content)
        elif content is not None:
            output.append(json.dumps(content, indent=2))
        output.extend(format_grounding(output_data.get("grounding")))

    if show_cost:
        output.extend(format_cost(results.get("costDollars")))

    return "\n".join(output)


def _error_hint(error: ExaAPIError, search_type: str, category: Optional[str]) -> Optional[str]:
    """Hint keyed on the server's own message, so it names the real cause."""
    if error.status != 400:
        return None
    msg = error.message
    if 'type "lite"' in msg or (search_type == "lite" and "Not supported" in msg):
        return "--lite accepts a limited parameter set; drop --lite (default auto) to use this option."
    if "outputSchema" in msg:
        return ("/search object schemas allow at most 10 properties in total (nested and array items count) "
                "and 2 levels; use exa_agent.py for larger shapes.")
    if category in ("company", "people") and ("PublishedDate" in msg or "excludeDomains" in msg):
        return ("--category company/people rejects date filters (--after/--before); "
                "people also rejects --exclude-domains.")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Exa Search - AI-powered web search (Exa 3.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "AI agent frameworks"
  %(prog)s "python requests timeout" --lite --highlights --no-text
  %(prog)s "transformer interpretability" --category publication
  %(prog)s "Python libraries" --domains github.com pypi.org
  %(prog)s "startup news" --category news --after 2026-06-01
  %(prog)s "Top AI startups" --deep --schema-preset company
  %(prog)s "Who founded OpenAI?" --text-output "Short answer"
  %(prog)s "solar cost trends" --dynamic --no-text

Types: auto (default), --lite, --deep-lite, --deep. Legacy: --fast, --instant, --deep-reasoning, --neural
Categories: company, publication, news, personal site, financial report, people
        """
    )

    parser.add_argument("query", help="Search query")

    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument("--lite", action="store_true", help="Lite search: cache-only, $4/1k, limited parameters")
    type_group.add_argument("--deep-lite", action="store_true", help="Deep-lite search: lightweight synthesis (~4s)")
    type_group.add_argument("--deep", action="store_true", help="Deep search: multi-step with synthesis (4-15s)")
    type_group.add_argument("--fast", action="store_true", help="(Legacy) fast search")
    type_group.add_argument("--instant", action="store_true", help="(Legacy) instant search")
    type_group.add_argument("--deep-reasoning", action="store_true", help="(Legacy) deep-reasoning search (12-40s)")
    type_group.add_argument("--neural", action="store_true", help="(Legacy) neural search")
    add_list_arg(parser, "--additional-queries", help="Extra queries for --deep-lite/--deep (max 10)")

    add_schema_args(parser)
    parser.add_argument("--system-prompt", help="Instructions for the synthesized output (not with --lite)")
    parser.add_argument("--objective", help="What the search is for; guides retrieval")

    parser.add_argument("--category", "-c", choices=CATEGORY_CHOICES, help="Filter by category")
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of results (max 100)")

    add_list_arg(parser, "--domains", split_commas=True, help="Only include these domains (repeatable)")
    add_list_arg(parser, "--exclude-domains", split_commas=True, help="Exclude these domains (repeatable)")

    parser.add_argument("--after", help="Published after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Published before date (YYYY-MM-DD)")

    add_list_arg(parser, "--must-include", help="(Deprecated) text that must be present")
    add_list_arg(parser, "--must-exclude", help="(Deprecated) text that must NOT be present")

    parser.add_argument("--no-text", action="store_true", help="Don't include full text (saves context, not cost)")
    parser.add_argument("--max-chars", type=int, help="Max characters of text per result")
    parser.add_argument("--summary", help="Generate summary with this query (not with --lite)")
    parser.add_argument("--highlights", action="store_true", help="Include query-relevant excerpts")
    parser.add_argument("--highlights-query", help="Custom query for highlights (implies --highlights)")
    parser.add_argument("--highlights-max-chars", type=int, help="Fixed highlight budget per page (implies --highlights)")
    parser.add_argument("--dynamic", action="store_true",
                        help="Dynamic Highlights (beta): one shared budget across all results")
    parser.add_argument("--context", action="store_true", help="(Deprecated) combine results into one context string")
    parser.add_argument("--context-chars", type=int, help="(Deprecated) max characters for --context")

    parser.add_argument("--max-age-hours", type=int,
                        help="Max cached content age in hours (0=always fetch fresh, -1=cache only)")
    parser.add_argument("--livecrawl", choices=LIVECRAWL_CHOICES,
                        help="(Deprecated) mapped to --max-age-hours")
    parser.add_argument("--snapshot-as-of", help="Page versions as of a date/time (paid tiers)")

    parser.add_argument("--verbosity", choices=["compact", "standard", "full"],
                        help="Text verbosity (requires --max-age-hours 0)")
    add_list_arg(parser, "--include-sections", choices=VALID_SECTIONS,
                 help="Only include these page sections (requires --max-age-hours 0)")
    add_list_arg(parser, "--exclude-sections", choices=VALID_SECTIONS,
                 help="Exclude these page sections (requires --max-age-hours 0)")

    parser.add_argument("--subpages", type=int, default=0, help="(Deprecated here) subpages to crawl per result")
    parser.add_argument("--subpage-target", help="Where to find subpage links")

    parser.add_argument("--links", type=int, default=0, help="Extract N links per result")
    parser.add_argument("--images", type=int, default=0, help="Extract N images per result")

    parser.add_argument("--location", help="User location: US, LAT,LON, or US,LAT,LON")
    parser.add_argument("--safe", action="store_true", help="Enable content moderation")

    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--cost", action="store_true", help="Show cost breakdown")

    args = parser.parse_args()

    search_type = "auto"
    for flag in ["lite", "deep_lite", "deep", "fast", "instant", "deep_reasoning", "neural"]:
        if getattr(args, flag):
            search_type = flag.replace("_", "-")
    if search_type in LEGACY_TYPES:
        legacy(f"--{search_type}", LEGACY_TYPES[search_type])

    try:
        output_schema = load_schema(args.output_schema, args.schema_file, args.schema_preset, args.text_output)
        payload, betas = build_search_payload(
            query=args.query,
            search_type=search_type,
            additional_queries=args.additional_queries,
            output_schema=output_schema,
            system_prompt=args.system_prompt,
            objective=args.objective,
            category=args.category,
            num_results=args.num,
            include_domains=args.domains,
            exclude_domains=args.exclude_domains,
            start_published_date=args.after,
            end_published_date=args.before,
            include_text=args.must_include,
            exclude_text=args.must_exclude,
            get_text=not args.no_text,
            max_characters=args.max_chars,
            get_summary=args.summary,
            get_highlights=args.highlights,
            highlights_query=args.highlights_query,
            highlights_max_chars=args.highlights_max_chars,
            dynamic_highlights=args.dynamic,
            get_context=args.context,
            context_max_chars=args.context_chars,
            max_age_hours=args.max_age_hours,
            livecrawl=args.livecrawl,
            snapshot_as_of=args.snapshot_as_of,
            verbosity=args.verbosity,
            include_sections=args.include_sections,
            exclude_sections=args.exclude_sections,
            subpages=args.subpages,
            subpage_target=args.subpage_target,
            get_links=args.links,
            get_image_links=args.images,
            user_location=parse_location(args.location),
            moderation=args.safe,
        )
    except ValueError as e:
        parser.error(str(e))

    try:
        results = post("/search", payload, betas=betas)
    except ExaAPIError as e:
        die(e, _error_hint(e, search_type, payload.get("category")))
    except ValueError as e:
        die(e)

    report_warnings(results)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results, show_cost=args.cost))


if __name__ == "__main__":
    main()
