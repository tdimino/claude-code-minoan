#!/usr/bin/env python3
"""
Component Gallery query — semantic search across 60 UI components and 95 design systems.

Usage:
    python3 query.py "accordion accessibility patterns"
    python3 query.py "flyout panel" -k 20
    python3 query.py "drawer vs modal" --json
    python3 query.py "tabs" --component tabs
    python3 query.py "color tokens" --system "Carbon Design System"
    python3 query.py "3D gallery" --source mesh3d
"""

import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys

RLAMA_RETRIEVE = os.path.expanduser("~/.claude/skills/rlama/scripts/rlama_retrieve.py")
RAG_NAME = "component-gallery"
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGING_DIR = os.path.join(SKILL_DIR, ".staging")
REFERENCES_DIR = os.path.join(SKILL_DIR, "references")

# rlama's `run --query` provides hybrid retrieval with reranking when configured,
# but it also invokes an LLM for generation, adding latency and requiring a running
# model. Since we only need ranked chunk retrieval, rlama_retrieve.py (pure cosine
# over the embedding cache) is the right primary path. Lexical fallback handles the
# Ollama-down case without any external dependency.


def _ollama_reachable() -> bool:
    """Quick check: can we reach Ollama's embedding endpoint?"""
    import urllib.request
    import urllib.error
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        req = urllib.request.Request(f"{host}/api/tags", method="GET")
        urllib.request.urlopen(req, timeout=3)
        return True
    except (urllib.error.URLError, OSError):
        return False


def _collect_corpus_files() -> list[str]:
    """Gather all .md files from .staging and references for lexical search."""
    paths = []
    for pattern in [
        os.path.join(STAGING_DIR, "**", "*.md"),
        os.path.join(REFERENCES_DIR, "*.md"),
    ]:
        paths.extend(glob.glob(pattern, recursive=True))
    return paths


def _path_matches_filters(path: str, component: str = None,
                          system: str = None, source: str = None) -> bool:
    """Pre-filter a file path by component slug, system name, or source kind."""
    rel = os.path.relpath(path, SKILL_DIR).lower()
    basename = os.path.basename(path).lower()

    if source:
        source_l = source.lower()
        if source_l == "mesh3d" and "mesh3d" not in rel:
            return False
        if source_l == "component.gallery" and "mesh3d" in rel:
            return False
        if source_l not in ("mesh3d", "component.gallery") and source_l not in rel:
            return False

    if component:
        slug = component.lower().replace(" ", "-")
        if slug not in basename and f"components-{slug}" not in basename:
            return False

    if system:
        sys_l = system.lower()
        if sys_l not in basename and sys_l not in rel:
            content_check = True
        else:
            content_check = False
        if content_check:
            return "defer"

    return True


def _tf_score(query_terms: list[str], text: str) -> float:
    """Simple term-frequency score: fraction of query terms found in text."""
    text_lower = text.lower()
    if not query_terms:
        return 0.0
    hits = sum(1 for t in query_terms if t in text_lower)
    return hits / len(query_terms)


def lexical_search(query: str, top_k: int = 10, component: str = None,
                   system: str = None, source: str = None) -> dict:
    """Grep-style term-frequency search over local .md files."""
    terms = [t.lower() for t in re.split(r'\s+', query.strip()) if len(t) > 1]
    files = _collect_corpus_files()

    scored = []
    for path in files:
        pre = _path_matches_filters(path, component, system, source)
        if pre is False:
            continue

        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            continue

        if pre == "defer" and system and system.lower() not in content.lower():
            continue

        score = _tf_score(terms, content)
        if score > 0:
            scored.append((score, path, content))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for rank, (score, path, content) in enumerate(scored[:top_k], 1):
        preview = content[:600]
        if len(content) > 600:
            preview += "..."
        results.append({
            "rank": rank,
            "score": round(score, 4),
            "content": preview,
            "document_id": os.path.relpath(path, SKILL_DIR),
            "chunk_index": 0,
            "metadata": {},
        })

    return {
        "query": query,
        "rag_name": RAG_NAME,
        "results": results,
        "total_chunks": len(files),
        "cache_status": "lexical",
        "embed_model": "none",
        "error": None,
    }


def semantic_search(query: str, top_k: int = 10, rebuild_cache: bool = False,
                    json_output: bool = False, component: str = None,
                    system: str = None, source: str = None,
                    extra_args: list = None) -> dict | None:
    """Run semantic search via rlama_retrieve.py, returns parsed result or None on failure."""
    cmd = ["python3", RLAMA_RETRIEVE, RAG_NAME, query, "-k", str(top_k)]
    if rebuild_cache:
        cmd.append("--rebuild-cache")
    cmd.append("--json")
    if extra_args:
        cmd.extend(extra_args)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    if proc.returncode != 0:
        return None

    try:
        result = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return None

    if result.get("error"):
        return None

    if component or system or source:
        result["results"] = _filter_semantic_results(
            result["results"], component, system, source
        )

    return result


def _filter_semantic_results(results: list[dict], component: str = None,
                             system: str = None, source: str = None) -> list[dict]:
    """Post-filter semantic results by metadata path patterns."""
    filtered = []
    for r in results:
        # document_id is a bare filename; metadata.document_name keeps the
        # staging subdirectory (pages/, curated/, deep-dives/) — prefer it.
        meta = r.get("metadata") or {}
        doc_id = (meta.get("document_name") or r.get("document_id", "")).lower()
        content = r.get("content", "").lower()

        if source:
            src = source.lower()
            if src == "mesh3d" and "mesh3d" not in doc_id:
                continue
            if src == "component.gallery" and "mesh3d" in doc_id:
                continue
            if src not in ("mesh3d", "component.gallery") and src not in doc_id:
                continue

        if component:
            slug = component.lower().replace(" ", "-")
            if slug not in doc_id and f"components-{slug}" not in doc_id:
                if slug not in content[:200]:
                    continue

        if system:
            sys_l = system.lower()
            if sys_l not in doc_id and sys_l not in content:
                continue

        filtered.append(r)

    for i, r in enumerate(filtered, 1):
        r["rank"] = i

    return filtered


def format_human(result: dict, fallback: bool = False) -> str:
    """Format results for human reading."""
    lines = []
    header = f'=== {len(result["results"])} results for: "{result["query"]}" ==='
    if fallback:
        header = "[semantic retrieval unavailable — lexical fallback]\n" + header
    lines.append(header)
    lines.append(
        f'    source: {result["rag_name"]} ({result["total_chunks"]} total, '
        f'mode: {result["cache_status"]})'
    )
    lines.append("")

    for r in result["results"]:
        content_preview = r["content"][:500]
        if len(r["content"]) > 500:
            content_preview += "..."
        lines.append(
            f'[{r["rank"]}] (score: {r["score"]:.3f}) {r["document_id"]}'
        )
        lines.append(content_preview)
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Query component-gallery data (semantic with lexical fallback)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s "accordion accessibility patterns"
  %(prog)s "flyout panel slide from edge" -k 20
  %(prog)s "responsive table patterns" --json
  %(prog)s "tabs" --component tabs
  %(prog)s "tokens" --system "Carbon Design System"
  %(prog)s "3D portfolio" --source mesh3d
""",
    )

    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "-k", "--top-k", type=int, default=10,
        help="Number of results (default: 10)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--rebuild-cache", action="store_true",
        help="Force rebuild the embedding cache",
    )
    parser.add_argument(
        "--component", metavar="SLUG",
        help="Filter to a specific component (e.g. accordion, drawer)",
    )
    parser.add_argument(
        "--system", metavar="NAME",
        help="Filter to a specific design system (e.g. 'Carbon Design System')",
    )
    parser.add_argument(
        "--source", metavar="KIND",
        help="Filter by source: mesh3d, component.gallery",
    )
    parser.add_argument(
        "--lexical", action="store_true",
        help="Force lexical search (skip semantic)",
    )

    args = parser.parse_args()

    use_lexical = args.lexical
    fallback = False

    if not use_lexical:
        if not _ollama_reachable():
            use_lexical = True
            fallback = True
            print("Ollama unreachable, falling back to lexical search...",
                  file=sys.stderr)

    result = None
    if not use_lexical:
        result = semantic_search(
            query=args.query,
            top_k=args.top_k,
            rebuild_cache=args.rebuild_cache,
            json_output=args.json,
            component=args.component,
            system=args.system,
            source=args.source,
        )
        if result is None:
            use_lexical = True
            fallback = True
            print("Semantic search failed, falling back to lexical...",
                  file=sys.stderr)

    if use_lexical:
        result = lexical_search(
            query=args.query,
            top_k=args.top_k,
            component=args.component,
            system=args.system,
            source=args.source,
        )

    if args.json:
        if fallback:
            result["fallback"] = "lexical"
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result, fallback=fallback))

    sys.exit(0)


if __name__ == "__main__":
    main()
