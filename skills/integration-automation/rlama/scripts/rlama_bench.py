#!/usr/bin/env python3
"""
RLAMA Retrieval & Synthesis Benchmark

Evaluates retrieval quality, synthesis accuracy, and grounding across
providers. Runs test cases with known-good expectations and scores results.

Dimensions scored:
  - Retrieval Precision: Do expected documents appear in top-K?
  - Topic Coverage: Does the synthesis mention expected topics?
  - Grounding: Does the synthesis avoid hallucinated topics?
  - Directness: Does the synthesis commit to an answer (vs hedging)?
  - Completeness: How many expected topics are covered?

Usage:
    python3 rlama_bench.py twitter-idaeandaktyl
    python3 rlama_bench.py twitter-idaeandaktyl --provider ollama
    python3 rlama_bench.py twitter-idaeandaktyl --provider ollama --verbose
    python3 rlama_bench.py twitter-idaeandaktyl --provider ollama --case 0
    python3 rlama_bench.py twitter-idaeandaktyl --retrieval-only
"""

import argparse
import json
import os
import re
import sys
import time

# Import retrieve and synthesize from sibling script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from rlama_retrieve import retrieve, synthesize


# ─── Test Cases ───────────────────────────────────────────────────────────────
# Each case: query, expected docs, expected topics in answer, negative topics
# (hallucination markers), and difficulty level.

TEST_CASES = [
    {
        "id": 0,
        "query": "What Claude Code techniques has Tom bookmarked?",
        "description": "Core retrieval test — should pull from the Claude Code bookmarks file",
        "expected_docs": ["claude-code-workflows.md"],
        "expected_topics": ["claude code", "bookmark", "skill", "workflow"],
        "negative_topics": [],
        "difficulty": "easy",
        "top_k": 15,
    },
    {
        "id": 1,
        "query": "Who are the key people in Tom's Twitter intellectual network?",
        "description": "Social dossier test — should surface specific names and roles",
        "expected_docs": ["dossier-intellectual-network.md"],
        "expected_topics": ["anthropic", "engineer", "researcher"],
        "negative_topics": [],
        "difficulty": "medium",
        "top_k": 10,
    },
    {
        "id": 2,
        "query": "What are Tom's public positions on AI and consciousness?",
        "description": "Cross-document synthesis — needs public-positions + consciousness bookmarks",
        "expected_docs": ["dossier-public-positions.md", "ai-consciousness-persona.md"],
        "expected_topics": ["consciousness", "ai", "soul", "daimon"],
        "negative_topics": [],
        "difficulty": "medium",
        "top_k": 15,
    },
    {
        "id": 3,
        "query": "What local ML tools and models has Tom been interested in?",
        "description": "Technical interest test — local ML bookmarks",
        "expected_docs": ["local-ml-finetuning.md"],
        "expected_topics": ["ollama", "local", "model", "fine-tun"],
        "negative_topics": [],
        "difficulty": "medium",
        "top_k": 10,
    },
    {
        "id": 4,
        "query": "What is Tom's voice and identity on Twitter?",
        "description": "Identity dossier test — handle, posting style, etymology",
        "expected_docs": ["dossier-voice-and-identity.md"],
        "expected_topics": ["idaeandaktyl", "daktyl", "voice", "style"],
        "negative_topics": [],
        "difficulty": "easy",
        "top_k": 10,
    },
    {
        "id": 5,
        "query": "What geopolitical topics does Tom follow?",
        "description": "Category test — geopolitics/Palestine bookmarks",
        "expected_docs": ["geopolitics-palestine.md"],
        "expected_topics": ["palestine", "geopolit"],
        "negative_topics": [],
        "difficulty": "easy",
        "top_k": 10,
    },
    {
        "id": 6,
        "query": "What occult and mystical history topics has Tom bookmarked?",
        "description": "Niche category test — occult/mystical bookmarks",
        "expected_docs": ["occult-mystical-history.md"],
        "expected_topics": ["occult", "mystical", "history"],
        "negative_topics": [],
        "difficulty": "easy",
        "top_k": 10,
    },
    {
        "id": 7,
        "query": "What image generation and creative AI tools has Tom bookmarked?",
        "description": "Niche category test — image gen bookmarks",
        "expected_docs": ["image-generation-visual-ai.md"],
        "expected_topics": ["image", "generat"],
        "negative_topics": [],
        "difficulty": "easy",
        "top_k": 10,
    },
]

# ─── Hedging Detection ────────────────────────────────────────────────────────

HEDGE_PATTERNS = [
    r"(?i)insufficient information",
    r"(?i)not enough information",
    r"(?i)do not contain",
    r"(?i)does not contain",
    r"(?i)no specific mention",
    r"(?i)cannot determine",
    r"(?i)unable to determine",
    r"(?i)no direct reference",
    r"(?i)not explicitly",
    r"(?i)not clear from",
    r"(?i)we can conclude that there is no",
    r"(?i)no explicit mention",
]


def detect_hedging(answer: str) -> tuple[bool, list[str]]:
    """Detect hedging language in synthesis answer. Returns (is_hedging, matched_patterns)."""
    matches = []
    for pattern in HEDGE_PATTERNS:
        if re.search(pattern, answer):
            matches.append(pattern)
    return len(matches) > 0, matches


# ─── Scoring ──────────────────────────────────────────────────────────────────

def score_retrieval(result: dict, case: dict) -> dict:
    """Score retrieval precision — do expected docs appear in results?"""
    retrieved_docs = [r["document_id"] for r in result["results"]]
    expected = case["expected_docs"]

    hits = 0
    misses = []
    for doc in expected:
        if any(doc in rd for rd in retrieved_docs):
            hits += 1
        else:
            misses.append(doc)

    precision = hits / len(expected) if expected else 1.0
    return {
        "precision": round(precision, 3),
        "hits": hits,
        "total_expected": len(expected),
        "misses": misses,
        "retrieved_docs": list(set(retrieved_docs)),
    }


def score_synthesis(answer: str, case: dict) -> dict:
    """Score synthesis quality across multiple dimensions."""
    if not answer:
        return {
            "topic_coverage": 0.0,
            "topics_found": [],
            "topics_missing": case["expected_topics"],
            "grounding": 1.0,
            "hallucinations": [],
            "directness": 0.0,
            "hedge_patterns": [],
            "word_count": 0,
        }

    answer_lower = answer.lower()

    # Topic coverage
    topics_found = []
    topics_missing = []
    for topic in case["expected_topics"]:
        if topic.lower() in answer_lower:
            topics_found.append(topic)
        else:
            topics_missing.append(topic)

    coverage = len(topics_found) / len(case["expected_topics"]) if case["expected_topics"] else 1.0

    # Grounding (absence of hallucinated topics)
    hallucinations = []
    for neg in case.get("negative_topics", []):
        if neg.lower() in answer_lower:
            hallucinations.append(neg)

    neg_count = len(case.get("negative_topics", []))
    grounding = 1.0 - (len(hallucinations) / neg_count) if neg_count > 0 else 1.0

    # Directness (absence of hedging)
    is_hedging, hedge_matches = detect_hedging(answer)
    directness = 0.0 if is_hedging else 1.0

    return {
        "topic_coverage": round(coverage, 3),
        "topics_found": topics_found,
        "topics_missing": topics_missing,
        "grounding": round(grounding, 3),
        "hallucinations": hallucinations,
        "directness": directness,
        "hedge_patterns": hedge_matches,
        "word_count": len(answer.split()),
    }


def composite_score(retrieval: dict, synthesis: dict) -> float:
    """Weighted composite score (0-100)."""
    weights = {
        "retrieval_precision": 0.25,
        "topic_coverage": 0.30,
        "grounding": 0.15,
        "directness": 0.30,
    }
    raw = (
        weights["retrieval_precision"] * retrieval["precision"]
        + weights["topic_coverage"] * synthesis["topic_coverage"]
        + weights["grounding"] * synthesis["grounding"]
        + weights["directness"] * synthesis["directness"]
    )
    return round(raw * 100, 1)


# ─── Runner ───────────────────────────────────────────────────────────────────

def run_case(rag_name: str, case: dict, provider: str = None,
             synth_model: str = None, verbose: bool = False) -> dict:
    """Run a single test case and return scores."""
    start = time.time()

    # Retrieve
    result = retrieve(
        rag_name=rag_name,
        query=case["query"],
        top_k=case.get("top_k", 10),
    )

    retrieval_time = time.time() - start
    retrieval_scores = score_retrieval(result, case)

    # Synthesize (if provider given)
    synthesis_scores = None
    answer = None
    synth_time = 0

    if provider:
        synth_start = time.time()
        synth_result = synthesize(
            query=case["query"],
            chunks=result["results"],
            provider=provider,
            model=synth_model,
        )
        synth_time = time.time() - synth_start

        if synth_result.get("error"):
            answer = f"[ERROR: {synth_result['error']}]"
            synthesis_scores = score_synthesis("", case)
        else:
            answer = synth_result.get("answer", "")
            synthesis_scores = score_synthesis(answer, case)

    # Composite
    composite = None
    if synthesis_scores:
        composite = composite_score(retrieval_scores, synthesis_scores)

    return {
        "case_id": case["id"],
        "query": case["query"],
        "difficulty": case["difficulty"],
        "retrieval": retrieval_scores,
        "retrieval_time": round(retrieval_time, 2),
        "synthesis": synthesis_scores,
        "synth_time": round(synth_time, 2),
        "composite_score": composite,
        "answer": answer,
    }


def format_case_result(r: dict, verbose: bool = False) -> str:
    """Format a single case result for display."""
    lines = []
    status = ""

    # Retrieval status
    ret = r["retrieval"]
    if ret["precision"] == 1.0:
        ret_icon = "+"
    elif ret["precision"] > 0:
        ret_icon = "~"
    else:
        ret_icon = "X"

    # Synthesis status
    if r["synthesis"]:
        syn = r["synthesis"]
        if syn["directness"] == 0:
            syn_icon = "HEDGE"
        elif syn["topic_coverage"] >= 0.75:
            syn_icon = "GOOD"
        elif syn["topic_coverage"] >= 0.5:
            syn_icon = "PARTIAL"
        else:
            syn_icon = "WEAK"

        composite = r["composite_score"]
        lines.append(
            f"  [{r['case_id']}] [{ret_icon}] [{syn_icon}] score={composite} "
            f"| ret={ret['precision']:.0%} cov={syn['topic_coverage']:.0%} "
            f"dir={syn['directness']:.0%} "
            f"| {r['retrieval_time']}s+{r['synth_time']}s "
            f"| {r['difficulty']}"
        )
        lines.append(f"      Q: {r['query']}")

        if verbose:
            if ret["misses"]:
                lines.append(f"      Retrieval misses: {ret['misses']}")
            lines.append(f"      Topics found: {syn['topics_found']}")
            if syn["topics_missing"]:
                lines.append(f"      Topics missing: {syn['topics_missing']}")
            if syn["hedge_patterns"]:
                lines.append(f"      Hedge patterns: {[p.replace('(?i)', '') for p in syn['hedge_patterns']]}")
            if r["answer"]:
                preview = r["answer"][:300].replace("\n", " ")
                if len(r["answer"]) > 300:
                    preview += "..."
                lines.append(f"      Answer: {preview}")
    else:
        lines.append(
            f"  [{r['case_id']}] [{ret_icon}] ret={ret['precision']:.0%} "
            f"| {r['retrieval_time']}s | {r['difficulty']}"
        )
        lines.append(f"      Q: {r['query']}")
        if verbose and ret["misses"]:
            lines.append(f"      Retrieval misses: {ret['misses']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark RLAMA retrieval and synthesis quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s twitter-idaeandaktyl --retrieval-only
  %(prog)s twitter-idaeandaktyl --provider ollama
  %(prog)s twitter-idaeandaktyl --provider ollama --verbose
  %(prog)s twitter-idaeandaktyl --provider ollama --case 0
  %(prog)s twitter-idaeandaktyl --provider ollama --synth-model qwen2.5:14b
""",
    )

    parser.add_argument("rag_name", help="Name of the RAG to benchmark")
    parser.add_argument("--provider", default=None, help="Synthesis provider (ollama, openrouter, togetherai)")
    parser.add_argument("--synth-model", default=None, help="Override synthesis model")
    parser.add_argument("--retrieval-only", action="store_true", help="Only test retrieval, skip synthesis")
    parser.add_argument("--case", type=int, default=None, help="Run a single test case by ID")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if args.retrieval_only:
        provider = None
    else:
        provider = args.provider

    # Select cases
    if args.case is not None:
        cases = [c for c in TEST_CASES if c["id"] == args.case]
        if not cases:
            print(f"No test case with ID {args.case}. Available: {[c['id'] for c in TEST_CASES]}", file=sys.stderr)
            sys.exit(1)
    else:
        cases = TEST_CASES

    # Header
    mode = f"synthesis ({provider})" if provider else "retrieval-only"
    model_str = args.synth_model or (provider and "default") or ""
    print(f"=== RLAMA Bench: {args.rag_name} | {mode} {model_str} | {len(cases)} cases ===\n", file=sys.stderr)

    # Run
    results = []
    for case in cases:
        print(f"  Running case {case['id']}...", file=sys.stderr, end=" ", flush=True)
        r = run_case(
            rag_name=args.rag_name,
            case=case,
            provider=provider,
            synth_model=args.synth_model,
            verbose=args.verbose,
        )
        results.append(r)
        print("done", file=sys.stderr)

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
        return

    print()
    print(f"=== RLAMA Bench Results: {args.rag_name} | {mode} ===\n")

    for r in results:
        print(format_case_result(r, args.verbose))
        print()

    # Summary
    if provider:
        composites = [r["composite_score"] for r in results if r["composite_score"] is not None]
        coverages = [r["synthesis"]["topic_coverage"] for r in results if r["synthesis"]]
        directness_scores = [r["synthesis"]["directness"] for r in results if r["synthesis"]]
        hedge_count = sum(1 for r in results if r["synthesis"] and r["synthesis"]["directness"] == 0)

        print("--- Summary ---")
        print(f"  Composite: {sum(composites)/len(composites):.1f}/100 avg")
        print(f"  Topic Coverage: {sum(coverages)/len(coverages):.0%} avg")
        print(f"  Directness: {sum(directness_scores)/len(directness_scores):.0%} avg")
        print(f"  Hedging: {hedge_count}/{len(results)} cases hedged")

    retrieval_precisions = [r["retrieval"]["precision"] for r in results]
    print(f"  Retrieval: {sum(retrieval_precisions)/len(retrieval_precisions):.0%} avg precision")

    total_time = sum(r["retrieval_time"] + r.get("synth_time", 0) for r in results)
    print(f"  Total time: {total_time:.1f}s ({total_time/len(results):.1f}s avg/case)")
    print()


if __name__ == "__main__":
    main()
