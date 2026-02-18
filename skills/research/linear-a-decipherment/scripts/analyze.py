# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Gordon's 5-step decipherment pipeline — single inscription or batch modes.

Steps: Transliteration → Segmentation → Consonantal Skeleton → Cognate Search
→ Semantic Validation (optional, v2).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.normalization import lookup_in, normalize, WORD_SEPARATORS
from lib.skeleton import extract_skeleton, extract_full
from lib.phonetics import weighted_levenshtein

LASHON_DIR = Path.home() / "Desktop/Programming/lashon-ha-kretan"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_corpus() -> dict[str, dict[str, Any]]:
    cached = DATA_DIR / "corpus.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))
    from lib.js_parser import parse_inscriptions
    return parse_inscriptions(LASHON_DIR / "LinearAInscriptions.js")


def load_gordon() -> dict[str, dict[str, Any]]:
    cached = DATA_DIR / "gordon.json"
    if cached.exists():
        data = json.loads(cached.read_text(encoding="utf-8"))
        return data.get("gordon", data)
    from lib.js_parser import parse_lexicon
    return parse_lexicon(LASHON_DIR / "semiticLexicon.js", "gordon")


def load_yashar_mana() -> dict[str, dict[str, Any]]:
    cached = DATA_DIR / "gordon.json"
    if cached.exists():
        data = json.loads(cached.read_text(encoding="utf-8"))
        return data.get("yasharMana", {})
    from lib.js_parser import parse_lexicon
    return parse_lexicon(LASHON_DIR / "semiticLexicon.js", "yasharMana")


def load_semitic_roots() -> list[dict[str, Any]]:
    cached = DATA_DIR / "semitic_roots.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))
    src = LASHON_DIR / "etymology" / "Semitic.json"
    if src.exists():
        return json.loads(src.read_text(encoding="utf-8"))
    return []


def load_cache() -> dict[str, list[dict]]:
    cache_file = DATA_DIR / "cognate_cache.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    return {}


# --- Single Inscription Analysis ---

def analyze_single(name: str, verbose: bool = False) -> dict[str, Any]:
    """Run Gordon's 5-step pipeline on a single inscription."""
    corpus = load_corpus()
    gordon = load_gordon()
    ym = load_yashar_mana()
    cache = load_cache()

    entry = corpus.get(name) or corpus.get(name.upper())
    if not entry:
        return {"error": f"Inscription '{name}' not found in corpus"}

    result: dict[str, Any] = {
        "name": name,
        "site": entry.get("site", ""),
        "context": entry.get("context", ""),
        "findspot": entry.get("findspot", ""),
    }

    # Step 1: Transliteration
    words = entry.get("transliteratedWords", [])
    if isinstance(words, str):
        words = [words]
    result["transliterated_words"] = words

    # Step 2: Segmentation (words already segmented in GORILA)
    result["word_count"] = len(words)

    # Steps 3-4: Skeleton + Cognate Search per word
    word_analyses = []
    for word in words:
        if word in WORD_SEPARATORS or not word:
            continue

        norm = normalize(word)
        skeleton = extract_skeleton(norm)
        cv = extract_full(norm)

        analysis: dict[str, Any] = {
            "word": word,
            "normalized": norm if norm != word else None,
            "skeleton": skeleton,
            "cv": [(c or "", v) for c, v in cv],
            "matches": [],
        }

        # Gordon direct
        g_match = lookup_in(gordon, word)
        if g_match:
            analysis["matches"].append({
                "method": "gordon_direct",
                "semitic": g_match.get("semitic", ""),
                "meaning": g_match.get("meaning", ""),
                "category": g_match.get("category", ""),
            })

        # YasharMana
        ym_match = lookup_in(ym, word)
        if ym_match:
            analysis["matches"].append({
                "method": "yashar_mana",
                "semitic": ym_match.get("semitic", ""),
                "meaning": ym_match.get("meaning", ""),
            })

        # Proto-Semitic (from cache if available)
        if word in cache:
            for m in cache[word][:3]:
                analysis["matches"].append({
                    "method": "proto_semitic",
                    "root": m.get("root", ""),
                    "meaning": m.get("meaning", ""),
                    "distance": m.get("distance", 0),
                })

        word_analyses.append(analysis)

    result["words"] = word_analyses

    # Summary
    known_count = sum(1 for w in word_analyses if w["matches"])
    result["summary"] = {
        "total_words": len(word_analyses),
        "identified": known_count,
        "unidentified": len(word_analyses) - known_count,
        "coverage": f"{known_count/max(len(word_analyses),1)*100:.0f}%",
    }

    return result


def format_report(result: dict[str, Any]) -> str:
    """Format analysis result as readable report."""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = [
        f"{'='*60}",
        f"Inscription: {result['name']}",
        f"Context: {result.get('context', 'unknown')}",
        f"Findspot: {result.get('findspot', 'unknown')}",
        f"Words: {result['word_count']}",
        f"{'='*60}",
        "",
    ]

    for w in result.get("words", []):
        word = w["word"]
        skel = w["skeleton"]
        lines.append(f"  {word}  →  skeleton: {skel}")

        if w.get("normalized"):
            lines.append(f"    (normalized: {w['normalized']})")

        for m in w["matches"]:
            method = m["method"]
            if method in ("gordon_direct", "yashar_mana"):
                lines.append(
                    f"    [{method}] {m.get('semitic', '')} = \"{m['meaning']}\""
                )
            else:
                lines.append(
                    f"    [{method}] {m.get('root', '')} = \"{m['meaning']}\" (d={m.get('distance', '?')})"
                )

        if not w["matches"]:
            lines.append("    [no matches]")
        lines.append("")

    s = result.get("summary", {})
    lines.extend([
        f"Summary: {s.get('identified', 0)}/{s.get('total_words', 0)} words identified ({s.get('coverage', '?')})",
        "",
        "⚠ DISCLAIMER: All readings are hypothetical. Linear A remains undeciphered.",
        "Gordon's Semitic hypothesis is one of several competing frameworks.",
    ])

    return "\n".join(lines)


# --- Batch Analysis Modes ---

def batch_unknowns(min_count: int, top_n: int) -> list[dict]:
    """Find unidentified words that appear frequently — best targets for new readings."""
    corpus = load_corpus()
    gordon = load_gordon()
    ym = load_yashar_mana()

    from collections import Counter
    word_counts: Counter = Counter()
    for entry in corpus.values():
        words = entry.get("transliteratedWords", [])
        if isinstance(words, list):
            word_counts.update(words)

    unknowns = []
    for word, count in word_counts.most_common():
        if count < min_count:
            break
        if word in WORD_SEPARATORS or not word:
            continue
        if lookup_in(gordon, word) or lookup_in(ym, word):
            continue
        skeleton = extract_skeleton(word)
        unknowns.append({
            "word": word,
            "count": count,
            "skeleton": skeleton,
        })

    return unknowns[:top_n]


def batch_cognate_scan(top_n: int) -> list[dict]:
    """Scan all corpus words and rank by best Proto-Semitic match distance."""
    cache = load_cache()
    if not cache:
        print("No cognate cache found. Run: cognate_search.py --build-cache", file=sys.stderr)
        return []

    scored = []
    for word, matches in cache.items():
        if matches:
            best = matches[0]
            scored.append({
                "word": word,
                "skeleton": extract_skeleton(word),
                "root": best.get("root", ""),
                "meaning": best.get("meaning", ""),
                "distance": best.get("distance", 999),
            })

    scored.sort(key=lambda x: x["distance"])
    return scored[:top_n]


def batch_libation(show_alignment: bool = False) -> list[dict]:
    """Find and group libation formula inscriptions (JA-SA-SA-RA-ME pattern)."""
    corpus = load_corpus()

    libation_words = {"JA-SA-SA-RA-ME", "A-TA-I-*301-WA-JA", "I-DA-MA-TE"}
    results = []

    for name, entry in corpus.items():
        words = entry.get("transliteratedWords", [])
        if isinstance(words, list):
            common = set(words) & libation_words
            if common:
                result: dict[str, Any] = {
                    "name": name,
                    "site": entry.get("site", ""),
                    "context": entry.get("context", ""),
                    "words": words,
                    "libation_words": sorted(common),
                }
                if show_alignment:
                    result["skeletons"] = {
                        w: extract_skeleton(w) for w in words if w not in WORD_SEPARATORS
                    }
                results.append(result)

    results.sort(key=lambda x: x["name"])
    return results


def batch_promising(top_n: int) -> list[dict]:
    """Find inscriptions with highest ratio of identified words — best for study."""
    corpus = load_corpus()
    gordon = load_gordon()
    ym = load_yashar_mana()

    scored = []
    for name, entry in corpus.items():
        words = entry.get("transliteratedWords", [])
        if not isinstance(words, list) or len(words) < 2:
            continue

        valid_words = [w for w in words if w not in WORD_SEPARATORS and w]
        if not valid_words:
            continue

        known = sum(1 for w in valid_words if lookup_in(gordon, w) or lookup_in(ym, w))
        ratio = known / len(valid_words)
        if known > 0:
            scored.append({
                "name": name,
                "total_words": len(valid_words),
                "identified": known,
                "coverage": f"{ratio*100:.0f}%",
                "context": entry.get("context", ""),
            })

    scored.sort(key=lambda x: (-x["identified"], -float(x["coverage"].rstrip("%"))))
    return scored[:top_n]


# --- CLI ---

def cmd_single(args: argparse.Namespace) -> None:
    result = analyze_single(args.name, verbose=args.verbose)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))


def cmd_batch(args: argparse.Namespace) -> None:
    mode = args.mode
    top_n = args.top or 20

    if mode == "unknowns":
        results = batch_unknowns(min_count=args.min_count or 3, top_n=top_n)
        if args.format == "json":
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"Unknown Words (count >= {args.min_count or 3}, top {top_n})")
            print(f"{'Word':<25} {'Count':>6} {'Skeleton':<15}")
            print("-" * 48)
            for r in results:
                print(f"{r['word']:<25} {r['count']:>6} {r['skeleton']:<15}")

    elif mode == "cognate-scan":
        results = batch_cognate_scan(top_n=top_n)
        if args.format == "json":
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"Best Proto-Semitic Matches (top {top_n})")
            print(f"{'Word':<20} {'Skeleton':<10} {'Root':<20} {'Meaning':<25} {'Dist':>6}")
            print("-" * 85)
            for r in results:
                print(f"{r['word']:<20} {r['skeleton']:<10} {r['root']:<20} {r['meaning']:<25} {r['distance']:>6.3f}")

    elif mode == "promising":
        results = batch_promising(top_n=top_n)
        if args.format == "json":
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"Most Promising Inscriptions (top {top_n})")
            print(f"{'Name':<15} {'Words':>6} {'Known':>6} {'Coverage':>10} {'Context':<15}")
            print("-" * 56)
            for r in results:
                print(f"{r['name']:<15} {r['total_words']:>6} {r['identified']:>6} {r['coverage']:>10} {r['context']:<15}")

    elif mode == "libation":
        results = batch_libation(show_alignment=args.alignment)
        if args.format == "json":
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"Libation Formula Inscriptions ({len(results)} found)")
            for r in results:
                lw = ", ".join(r["libation_words"])
                print(f"  {r['name']:<15} [{r.get('site', '')}] {lw}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Linear A decipherment pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    # Single inscription
    p_single = sub.add_parser("single", help="Analyze a single inscription")
    p_single.add_argument("name", help="Inscription name (e.g., HT1, HT88)")
    p_single.add_argument("--format", choices=["report", "json"], default="report")
    p_single.add_argument("--verbose", "-v", action="store_true")
    p_single.set_defaults(func=cmd_single)

    # Batch modes
    p_batch = sub.add_parser("batch", help="Batch analysis modes")
    p_batch.add_argument("--mode", "-m", required=True,
                         choices=["unknowns", "cognate-scan", "promising", "libation"])
    p_batch.add_argument("--top", "-n", type=int, default=20)
    p_batch.add_argument("--min-count", type=int, default=3)
    p_batch.add_argument("--format", choices=["table", "json"], default="table")
    p_batch.add_argument("--alignment", action="store_true", help="Show skeleton alignment (libation)")
    p_batch.add_argument("--output", "-o", help="Output file")
    p_batch.set_defaults(func=cmd_batch)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
