#!/usr/bin/env python3
"""
Exa Research - cited answers from Exa's /answer endpoint ($5/1k).

/answer takes only a question (plus model, systemPrompt, userLocation,
outputSchema, text, stream). It has no source filters. When domain, date, or
result-count filters are given, this script routes the question to /search
(type auto + a text outputSchema, $7/1k, ~2s slower) so the filters actually
apply, and says so on stderr.

Features:
- Synthesized answers with citations (--sources lists them)
- Models: exa (default), exa-pro, exa-fast, exa-research
- Structured answers via --output-schema / --schema-file
- Streaming (--stream) of OpenAI-style chunks, then citations and cost
- Filtered answers via automatic /search routing

Usage:
    exa_research.py "What are the main differences between React and Vue?"
    exa_research.py "Latest developments in AI agents" --sources
    exa_research.py "SpaceX valuation history" --after 2024-01-01
    exa_research.py "Python async best practices" --domains docs.python.org realpython.com

Requires: EXA_API_KEY environment variable
Install: pip install requests
"""

import sys
import json
import argparse
import contextlib
from typing import Optional, List, Dict, Any

from _exa_common import (
    ExaAPIError, add_list_arg, die, format_cost, format_grounding, format_notices, load_schema, note,
    parse_location, post, report_warnings,
)
from exa_search import build_search_payload

ANSWER_MODELS = ["exa", "exa-pro", "exa-fast", "exa-research"]
ROUTED_ANSWER_SCHEMA = {"type": "text", "description": "A direct, well-cited answer to the question."}


def build_answer_payload(
    query: str,
    get_text: bool = True,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    user_location: Any = None,
    output_schema: Optional[Dict[str, Any]] = None,
    stream: bool = False,
) -> Dict[str, Any]:
    """Build the /answer request body. /answer accepts nothing else (spec 2.0.0)."""
    payload: Dict[str, Any] = {"query": query}
    if get_text:
        payload["text"] = True
    if model:
        payload["model"] = model
    if system_prompt:
        payload["systemPrompt"] = system_prompt
    if user_location:
        payload["userLocation"] = user_location
    if output_schema:
        payload["outputSchema"] = output_schema
    if stream:
        payload["stream"] = True
    return payload


def research(query: str, stream: bool = False, **kwargs):
    """Ask /answer. Returns the parsed response, or the raw streaming Response."""
    return post("/answer", build_answer_payload(query, stream=stream, **kwargs), stream=stream)


def research_filtered(query: str, output_schema: Optional[Dict[str, Any]] = None,
                      system_prompt: Optional[str] = None, **search_kwargs) -> Dict[str, Any]:
    """Answer via /search (auto + outputSchema) so domain/date/count filters apply.

    Returns an /answer-shaped dict: answer, citations (the search results),
    grounding, costDollars, requestId, plus route="search".
    """
    payload, betas = build_search_payload(
        query, search_type="auto", output_schema=output_schema or ROUTED_ANSWER_SCHEMA,
        system_prompt=system_prompt, **search_kwargs)
    resp = post("/search", payload, betas=betas)
    output = resp.get("output") or {}
    answer: Dict[str, Any] = {
        "route": "search",
        "requestId": resp.get("requestId"),
        "answer": output.get("content"),
        "citations": resp.get("results", []),
        "grounding": output.get("grounding", []),
        "costDollars": resp.get("costDollars"),
    }
    for key in ("warnings", "notices"):
        if resp.get(key):
            answer[key] = resp[key]
    return answer


def process_stream(response, echo: bool = True) -> Dict[str, Any]:
    """Consume an /answer SSE stream.

    Chunks: OpenAI-style {"choices":[{"delta":{"content":...}}]}, then
    {"citations":[...]}, then {"costDollars":...,"requestId":...}, then [DONE].
    Errors arrive as {"tag":"ERROR","payload":{"error":{"code","message"}}}.
    A stream that ends before [DONE] raises STREAM_TRUNCATED.
    """
    response.encoding = "utf-8"  # text/event-stream has no charset; requests would guess ISO-8859-1
    result: Dict[str, Any] = {"answer": "", "citations": []}
    done = False
    for line in response.iter_lines(decode_unicode=True):
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        if not line or not line.startswith("data: "):
            continue
        data = line[6:].strip()
        if data == "[DONE]":
            done = True
            break
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue
        if not isinstance(chunk, dict):
            continue
        if chunk.get("tag") == "ERROR":
            payload = chunk.get("payload") or {}
            err = payload.get("error") or {}
            if echo:
                print()
            code = err.get("code")
            raise ExaAPIError(code if isinstance(code, int) else 500, "STREAM_ERROR",
                              err.get("message", str(chunk)), payload.get("requestId"))
        for choice in chunk.get("choices") or []:
            content = (choice.get("delta") or {}).get("content")
            if content:
                result["answer"] += content
                if echo:
                    print(content, end="", flush=True)
        if "citations" in chunk:
            result["citations"] = chunk["citations"]
        if "costDollars" in chunk:
            result["costDollars"] = chunk["costDollars"]
        if chunk.get("requestId"):
            result["requestId"] = chunk["requestId"]
    if echo:
        print()
    if not done:
        raise ExaAPIError(0, "STREAM_TRUNCATED", "stream ended before [DONE]; the answer may be incomplete",
                          result.get("requestId"))
    return result


def _answer_text(answer: Any) -> str:
    return answer if isinstance(answer, str) else json.dumps(answer, indent=2)


def format_sources(sources: List[Dict[str, Any]], max_text_length: int = 500) -> List[str]:
    output = [f"\n{'='*60}", f"SOURCES ({len(sources)} used):"]
    for i, s in enumerate(sources, 1):
        output.append(f"\n[{i}] {s.get('title') or 'No title'}")
        output.append(f"    URL: {s.get('url', 'No URL')}")
        if s.get('author'):
            output.append(f"    Author: {s['author'][:60]}")
        if s.get('publishedDate'):
            output.append(f"    Published: {s['publishedDate'][:10]}")
        if s.get('highlights'):
            output.append("    Key excerpts:")
            for h in s['highlights'][:2]:
                output.append(f"      \"{h[:150]}...\"")
        if s.get('text') and max_text_length:
            text = s['text'][:max_text_length]
            if len(s['text']) > max_text_length:
                text += "..."
            output.append(f"    Preview: {text}")
    return output


def format_results(results: Dict[str, Any], show_sources: bool = True, max_text_length: int = 500,
                   show_cost: bool = False) -> str:
    """Format an answer (from /answer or the /search route) for readable display."""
    output = []

    if results.get("requestId"):
        output.append(f"Request ID: {results['requestId']}")
    output.extend(format_notices(results))

    if results.get("answer"):
        output.append(f"\n{'='*60}")
        output.append("ANSWER:")
        output.append("-" * 40)
        output.append(_answer_text(results["answer"]))

    sources = results.get("citations") or []
    if sources and show_sources:
        output.extend(format_sources(sources, max_text_length))
        output.extend(format_grounding(results.get("grounding")))

    if show_cost:
        output.extend(format_cost(results.get("costDollars")))

    return "\n".join(output)


def format_markdown_sources(sources: List[Dict[str, Any]]) -> List[str]:
    output = ["\n\n## Sources\n"] if sources else []
    for i, s in enumerate(sources, 1):
        ref = f"[{i}] [{s.get('title') or 'Untitled'}]({s.get('url', '')})"
        if s.get('author'):
            ref += f" by {s['author'][:50]}"
        if s.get('publishedDate'):
            ref += f" ({s['publishedDate'][:10]})"
        output.append(ref)
    return output


def format_markdown(results: Dict[str, Any]) -> str:
    """Format an answer as markdown with numbered citations."""
    output = []
    if results.get("answer"):
        output.append("## Research Answer\n")
        output.append(_answer_text(results["answer"]))
    output.extend(format_markdown_sources(results.get("citations") or []))
    return "\n".join(output)


def _require_answer(results: Dict[str, Any], route: str) -> None:
    """An empty answer is a failure (exit 4), not a blank success."""
    if results.get("answer"):
        return
    n = len(results.get("citations") or [])
    print(f"Error: No answer returned from {route} ({n} sources). "
          f"Request ID: {results.get('requestId')}", file=sys.stderr)
    sys.exit(4)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Research - cited answers (/answer, or /search when filtered)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What is the latest valuation of SpaceX?"
  %(prog)s "Best practices for Python async programming" --sources
  %(prog)s "Compare React vs Vue vs Svelte" --markdown --model exa-pro
  %(prog)s "Recent AI regulation news" --after 2026-06-01 --domains techcrunch.com arstechnica.com
  %(prog)s "How does RLHF work?" --stream

Routing:
  No filters  → /answer ($5/1k). --model, --stream, --location apply.
  --domains, --exclude-domains, --after, --before, or -n
              → /search type auto with a text outputSchema ($7/1k, ~2s slower),
                because /answer has no source filters.
        """
    )

    parser.add_argument("query", help="Research question or topic")

    parser.add_argument("-n", "--num", type=int,
                        help="Number of sources (routes to /search; /answer picks its own)")
    add_list_arg(parser, "--domains", split_commas=True, help="Only use these domains as sources (routes to /search)")
    add_list_arg(parser, "--exclude-domains", split_commas=True, help="Exclude these domains (routes to /search)")
    parser.add_argument("--after", help="Only sources published after date, YYYY-MM-DD (routes to /search)")
    parser.add_argument("--before", help="Only sources published before date, YYYY-MM-DD (routes to /search)")

    parser.add_argument("--model", choices=ANSWER_MODELS, help="Answer model (default: exa)")
    parser.add_argument("--system-prompt", help="Instructions for the answer (tone, format, source preferences)")
    parser.add_argument("--location", help="User location: US, LAT,LON, or US,LAT,LON")

    parser.add_argument("--no-text", action="store_true", help="Don't include source text")
    parser.add_argument("--highlights", action="store_true",
                        help="Include source excerpts (with the /search route only)")

    schema_group = parser.add_mutually_exclusive_group()
    schema_group.add_argument("--output-schema", help="JSON schema string for a structured answer")
    schema_group.add_argument("--schema-file", help="Path to JSON schema file for a structured answer")

    parser.add_argument("--stream", action="store_true", help="Stream the answer in real time")

    parser.add_argument("--sources", action="store_true", help="Show source details")
    parser.add_argument("--markdown", action="store_true", help="Output as markdown with citations")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--answer-only", action="store_true", help="Only output the answer text")
    parser.add_argument("--cost", action="store_true", help="Show cost breakdown")
    parser.add_argument("--text-limit", type=int, default=500,
                        help="Max source text chars to display (default: 500)")

    args = parser.parse_args()

    try:
        output_schema = load_schema(args.output_schema, args.schema_file)
        user_location = parse_location(args.location)
    except ValueError as e:
        parser.error(str(e))

    routed = any([args.domains, args.exclude_domains, args.after, args.before, args.num is not None])

    try:
        if routed:
            print("Note: source filters → /search (type auto + outputSchema; $7/1k vs $5/1k, ~2s slower), "
                  "since /answer has no filters.", file=sys.stderr)
            if args.model:
                note("--model ignored on the /search route.")
            if args.stream:
                note("--stream ignored on the /search route.")
            try:
                results = research_filtered(
                    args.query,
                    output_schema=output_schema,
                    system_prompt=args.system_prompt,
                    num_results=args.num or 10,
                    include_domains=args.domains,
                    exclude_domains=args.exclude_domains,
                    start_published_date=args.after,
                    end_published_date=args.before,
                    get_text=not args.no_text,
                    get_highlights=args.highlights,
                    user_location=user_location,
                )
            except ExaAPIError as e:
                hint = None
                if e.status == 400 and output_schema:
                    hint = ("/search object schemas allow at most 10 properties and 2 levels of nesting; "
                            "simplify the schema or drop the filters to use /answer.")
                die(e, hint)
            report_warnings(results)
        elif args.stream:
            if args.highlights:
                note("--highlights ignored by /answer; add a filter to use the /search route.")
            response = research(args.query, stream=True, get_text=not args.no_text, model=args.model,
                                system_prompt=args.system_prompt, user_location=user_location,
                                output_schema=output_schema)
            echo = not args.json
            if echo and args.markdown:
                print("## Research Answer\n")
            elif echo and not args.answer_only:
                print("ANSWER:", file=sys.stderr)
                print("-" * 40, file=sys.stderr)
            with contextlib.closing(response):
                results = process_stream(response, echo=echo)
            if args.json:
                print(json.dumps(results, indent=2))
            elif not args.answer_only:
                if args.markdown:
                    print("\n".join(format_markdown_sources(results["citations"])))
                elif args.sources and results["citations"]:
                    print("\n".join(format_sources(results["citations"], args.text_limit)))
                if args.cost:
                    print("\n".join(format_cost(results.get("costDollars"))))
            _require_answer(results, "/answer stream")
            return
        else:
            if args.highlights:
                note("--highlights ignored by /answer; add a filter to use the /search route.")
            results = research(args.query, get_text=not args.no_text, model=args.model,
                               system_prompt=args.system_prompt, user_location=user_location,
                               output_schema=output_schema)
            report_warnings(results)
    except (ExaAPIError, ValueError) as e:
        die(e)

    if args.json:
        print(json.dumps(results, indent=2))
    elif args.answer_only:
        if results.get("answer"):
            print(_answer_text(results["answer"]))
    elif args.markdown:
        print(format_markdown(results))
    else:
        print(format_results(results, show_sources=args.sources, max_text_length=args.text_limit,
                             show_cost=args.cost))
    _require_answer(results, "/search route" if routed else "/answer")


if __name__ == "__main__":
    main()
