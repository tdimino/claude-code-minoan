# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Search for Semitic cognates of a Linear A transliteration.

Pipeline: transliteration → consonantal skeleton → Gordon direct match →
YasharMana match → Proto-Semitic distance search.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.normalization import lookup_in
from lib.phonetics import weighted_levenshtein
from lib.skeleton import extract_skeleton, extract_full
from lib.types import CognateMatch

LASHON_DIR = Path.home() / "Desktop/Programming/lashon-ha-kretan"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE_FILE = DATA_DIR / "cognate_cache.json"


def load_gordon() -> dict[str, dict[str, Any]]:
    """Load Gordon lexicon from extracted JSON or source JS."""
    cached = DATA_DIR / "gordon.json"
    if cached.exists():
        data = json.loads(cached.read_text(encoding="utf-8"))
        return data.get("gordon", data)

    from lib.js_parser import parse_lexicon
    return parse_lexicon(LASHON_DIR / "semiticLexicon.js", "gordon")


def load_yashar_mana() -> dict[str, dict[str, Any]]:
    """Load YasharMana lexicon."""
    cached = DATA_DIR / "gordon.json"
    if cached.exists():
        data = json.loads(cached.read_text(encoding="utf-8"))
        return data.get("yasharMana", {})

    from lib.js_parser import parse_lexicon
    return parse_lexicon(LASHON_DIR / "semiticLexicon.js", "yasharMana")


def load_scholarly() -> dict[str, dict[str, Any]]:
    """Load scholarly lexicon (post-Gordon readings from other scholars)."""
    cached = DATA_DIR / "gordon.json"
    if cached.exists():
        data = json.loads(cached.read_text(encoding="utf-8"))
        return data.get("scholarly", {})

    from lib.js_parser import parse_lexicon
    return parse_lexicon(LASHON_DIR / "semiticLexicon.js", "scholarly")


def load_semitic_roots() -> list[dict[str, Any]]:
    """Load Proto-Semitic roots."""
    cached = DATA_DIR / "semitic_roots.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))

    src = LASHON_DIR / "etymology" / "Semitic.json"
    if src.exists():
        return json.loads(src.read_text(encoding="utf-8"))
    return []


def search_cognates(
    transliteration: str,
    top_n: int = 5,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Full cognate search pipeline for a transliteration."""
    skeleton = extract_skeleton(transliteration)
    full_cv = extract_full(transliteration)
    results: dict[str, Any] = {
        "transliteration": transliteration,
        "skeleton": skeleton,
        "cv_decomposition": [(c or "", v) for c, v in full_cv],
        "matches": [],
    }

    # Step 1: Gordon direct match
    gordon = load_gordon()
    match = lookup_in(gordon, transliteration)
    if match:
        results["matches"].append({
            "root": match.get("semitic", ""),
            "language": "Semitic (Gordon)",
            "meaning": match.get("meaning", ""),
            "distance": 0.0,
            "method": "gordon_direct",
            "source": match.get("source", ""),
        })

    # Step 2: YasharMana match
    ym = load_yashar_mana()
    ym_match = lookup_in(ym, transliteration)
    if ym_match:
        results["matches"].append({
            "root": ym_match.get("semitic", ""),
            "language": "Semitic (YasharMana)",
            "meaning": ym_match.get("meaning", ""),
            "distance": 0.0,
            "method": "yashar_mana",
            "source": ym_match.get("source", ""),
        })

    # Step 2.5: Scholarly match (post-Gordon readings from other scholars)
    scholarly = load_scholarly()
    sch_match = lookup_in(scholarly, transliteration)
    if sch_match:
        results["matches"].append({
            "root": sch_match.get("semitic", ""),
            "language": "Semitic (Scholarly)",
            "meaning": sch_match.get("meaning", ""),
            "distance": 0.0,
            "method": "scholarly",
            "source": sch_match.get("source", ""),
        })

    # Step 3: Proto-Semitic distance search
    if skeleton:
        if use_cache and CACHE_FILE.exists():
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            cached_matches = cache.get(transliteration, [])
            for m in cached_matches[:top_n]:
                results["matches"].append({**m, "method": "proto_semitic"})
        else:
            ps_matches = _search_proto_semitic(skeleton, top_n)
            results["matches"].extend(ps_matches)

    return results


def _search_proto_semitic(skeleton: str, top_n: int) -> list[dict[str, Any]]:
    """Brute-force search against Proto-Semitic roots."""
    roots = load_semitic_roots()
    if not roots:
        return []

    scored: list[tuple[float, dict]] = []
    for entry in roots:
        root_str = entry.get("Proto-Semitic", "")
        # Extract consonantal root from Proto-Semitic notation: *ʔab- → ʔb
        root_consonants = _extract_root_consonants(root_str)
        if not root_consonants:
            continue

        dist = weighted_levenshtein(skeleton, root_consonants)
        if dist < len(skeleton):  # Only keep reasonable matches
            scored.append((dist, {
                "root": root_str,
                "language": "Proto-Semitic",
                "meaning": entry.get("Meaning", ""),
                "distance": round(dist, 3),
                "method": "proto_semitic",
            }))

    scored.sort(key=lambda x: x[0])
    return [m for _, m in scored[:top_n]]


def _extract_root_consonants(ps_root: str) -> str:
    """Extract consonants from Proto-Semitic notation.

    *ʔab- → ʔb, *θalaθ- → θlθ, *ḥabl- → ḥbl
    """
    # Strip leading * and trailing -
    s = ps_root.strip("*- ")
    # Remove common vowels (a, i, u, e, o and their long forms)
    consonants = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "aiueoāīūēō":
            i += 1
            continue
        consonants.append(ch)
        i += 1
    return "".join(consonants)


def load_corpus() -> dict[str, dict[str, Any]]:
    """Load corpus from extracted JSON."""
    cached = DATA_DIR / "corpus.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))

    from lib.js_parser import parse_inscriptions
    return parse_inscriptions(LASHON_DIR / "LinearAInscriptions.js")


def reverse_root_search(
    root: str,
    max_distance: float = 0.3,
    top_n: int = 20,
) -> dict[str, Any]:
    """Search the corpus for words whose skeletons match a Semitic root.

    Given a consonantal root like 'kns', finds all corpus words with matching
    or similar skeletons. This is the inverse of forward cognate search.
    """
    root_lower = root.lower()
    corpus = load_corpus()
    gordon = load_gordon()
    ym = load_yashar_mana()
    scholarly = load_scholarly()

    # Collect all unique transliterated words with their inscriptions
    word_inscriptions: dict[str, list[str]] = {}
    for name, entry in corpus.items():
        tw = entry.get("transliteratedWords", [])
        if isinstance(tw, list):
            for w in tw:
                if w and w not in ("𐄁", "\n", "") and "-" in w:
                    word_inscriptions.setdefault(w, []).append(name)

    # Score each word against the target root
    scored: list[dict[str, Any]] = []
    seen_skeletons: set[str] = set()

    for word, inscriptions in word_inscriptions.items():
        skeleton = extract_skeleton(word)
        if not skeleton:
            continue

        dist = weighted_levenshtein(skeleton, root_lower)
        if dist > max_distance * max(len(skeleton), len(root_lower), 1):
            continue

        # Check for Gordon/YasharMana/Scholarly reading
        known_reading = None
        g = lookup_in(gordon, word)
        if g:
            known_reading = f"Gordon: {g.get('meaning', '')} ({g.get('semitic', '')})"
        else:
            y = lookup_in(ym, word)
            if y:
                known_reading = f"YasharMana: {y.get('meaning', '')} ({y.get('semitic', '')})"
            else:
                s = lookup_in(scholarly, word)
                if s:
                    known_reading = f"Scholarly: {s.get('meaning', '')} ({s.get('source', '')})"

        # Get site info
        sites = set()
        for iname in inscriptions:
            entry = corpus.get(iname, {})
            site = entry.get("site", "")
            if site:
                sites.add(site)

        scored.append({
            "word": word,
            "skeleton": skeleton,
            "distance": round(dist, 3),
            "occurrences": len(inscriptions),
            "inscriptions": sorted(set(inscriptions)),
            "sites": sorted(sites),
            "known_reading": known_reading,
        })

    # Sort by distance, then by occurrence count (descending)
    scored.sort(key=lambda x: (x["distance"], -x["occurrences"]))

    return {
        "root": root,
        "root_consonants": root_lower,
        "total_matches": len(scored),
        "matches": scored[:top_n],
    }


def format_reverse_table(result: dict[str, Any]) -> str:
    """Format reverse search results as readable table."""
    lines = [
        f"Root search:   {result['root']}",
        f"Consonants:    {result['root_consonants']}",
        f"Total matches: {result['total_matches']}",
        "",
    ]

    matches = result["matches"]
    if not matches:
        lines.append("No corpus words found matching this root.")
        return "\n".join(lines)

    lines.append(f"{'Word':<24} {'Skeleton':<10} {'Dist':>6} {'#':>4} {'Sites':<20} {'Reading'}")
    lines.append("-" * 100)
    for m in matches:
        reading = m["known_reading"] or ""
        sites = ", ".join(m["sites"][:3])
        if len(m["sites"]) > 3:
            sites += f" +{len(m['sites']) - 3}"
        lines.append(
            f"{m['word']:<24} {m['skeleton']:<10} {m['distance']:>6.3f} "
            f"{m['occurrences']:>4} {sites:<20} {reading}"
        )

    return "\n".join(lines)


def build_cache(top_n: int = 5) -> None:
    """Build the precomputed cognate cache."""
    from lib.js_parser import parse_inscriptions

    print("Building cognate cache...", file=sys.stderr)
    inscriptions = parse_inscriptions(LASHON_DIR / "LinearAInscriptions.js")

    # Collect unique words
    words: set[str] = set()
    for entry in inscriptions.values():
        tw = entry.get("transliteratedWords", [])
        if isinstance(tw, list):
            words.update(tw)
        elif isinstance(tw, str):
            words.add(tw)

    # Filter to words with extractable skeletons
    searchable = {}
    for w in words:
        skel = extract_skeleton(w)
        if skel:
            searchable[w] = skel

    print(f"  {len(searchable)} words with extractable skeletons", file=sys.stderr)

    # Search each word
    cache: dict[str, list[dict]] = {}
    roots = load_semitic_roots()
    total = len(searchable)
    for idx, (word, skeleton) in enumerate(searchable.items()):
        if (idx + 1) % 200 == 0:
            print(f"  {idx + 1}/{total}...", file=sys.stderr)

        scored: list[tuple[float, dict]] = []
        for entry in roots:
            root_str = entry.get("Proto-Semitic", "")
            root_consonants = _extract_root_consonants(root_str)
            if not root_consonants:
                continue
            dist = weighted_levenshtein(skeleton, root_consonants)
            if dist < len(skeleton):
                scored.append((dist, {
                    "root": root_str,
                    "language": "Proto-Semitic",
                    "meaning": entry.get("Meaning", ""),
                    "distance": round(dist, 3),
                }))

        scored.sort(key=lambda x: x[0])
        if scored:
            cache[word] = [m for _, m in scored[:top_n]]

    DATA_DIR.mkdir(exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    size_kb = CACHE_FILE.stat().st_size / 1024
    print(f"Wrote {CACHE_FILE} ({size_kb:.0f}KB, {len(cache)} entries)", file=sys.stderr)


def format_table(result: dict[str, Any]) -> str:
    """Format results as readable table."""
    lines = [
        f"Transliteration: {result['transliteration']}",
        f"Skeleton:         {result['skeleton']}",
        f"CV:               {' '.join(f'{c}{v}' for c, v in result['cv_decomposition'])}",
        "",
    ]

    matches = result["matches"]
    if not matches:
        lines.append("No matches found.")
        return "\n".join(lines)

    lines.append(f"{'Method':<16} {'Root':<20} {'Meaning':<30} {'Dist':>6}")
    lines.append("-" * 76)
    for m in matches:
        lines.append(
            f"{m['method']:<16} {m['root']:<20} {m['meaning']:<30} {m['distance']:>6.3f}"
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Search for Semitic cognates")
    parser.add_argument("transliteration", nargs="?", help="Linear A transliteration (e.g., KI-RE-TA)")
    parser.add_argument("--skeleton", action="store_true", help="Only show skeleton extraction")
    parser.add_argument("--top", "-n", type=int, default=5, help="Number of top matches")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    parser.add_argument("--no-cache", action="store_true", help="Skip precomputed cache")
    parser.add_argument("--build-cache", action="store_true", help="Build cognate cache")
    parser.add_argument("--reverse", metavar="ROOT",
                        help="Reverse search: find corpus words matching a Semitic root (e.g., kns)")
    parser.add_argument("--max-dist", type=float, default=0.3,
                        help="Max normalized distance for reverse search (default: 0.3)")

    args = parser.parse_args()

    if args.build_cache:
        build_cache(top_n=args.top)
        return

    if args.reverse:
        top = max(args.top, 20)  # reverse search benefits from more results
        result = reverse_root_search(args.reverse, max_distance=args.max_dist, top_n=top)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_reverse_table(result))
        return

    if not args.transliteration:
        parser.error("transliteration is required (or use --build-cache / --reverse)")

    if args.skeleton:
        skel = extract_skeleton(args.transliteration)
        cv = extract_full(args.transliteration)
        print(f"Skeleton: {skel}")
        print(f"CV:       {' '.join(f'{c or ''}{v}' for c, v in cv)}")
        return

    result = search_cognates(args.transliteration, top_n=args.top, use_cache=not args.no_cache)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_table(result))


if __name__ == "__main__":
    main()
