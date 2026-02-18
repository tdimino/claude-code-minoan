# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Statistical analysis of sign patterns across the Linear A corpus."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LASHON_DIR = Path.home() / "Desktop/Programming/lashon-ha-kretan"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_corpus() -> dict[str, dict[str, Any]]:
    """Load inscription corpus."""
    cached = DATA_DIR / "corpus.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))

    from lib.js_parser import parse_inscriptions
    return parse_inscriptions(LASHON_DIR / "LinearAInscriptions.js")


def get_all_words(corpus: dict) -> list[str]:
    """Extract all transliterated words from corpus."""
    words = []
    for entry in corpus.values():
        tw = entry.get("transliteratedWords", [])
        if isinstance(tw, list):
            words.extend(tw)
    return words


def get_all_signs(words: list[str]) -> list[str]:
    """Split words into individual signs."""
    signs = []
    for w in words:
        signs.extend(w.split("-"))
    return signs


def cmd_frequency(args: argparse.Namespace) -> None:
    """Sign frequency analysis."""
    corpus = load_corpus()
    words = get_all_words(corpus)
    signs = get_all_signs(words)

    counter = Counter(signs)
    top_n = args.top or 30

    if args.format == "json":
        print(json.dumps(counter.most_common(top_n), indent=2))
        return

    print(f"Sign Frequency (top {top_n} of {len(counter)} unique signs)")
    print(f"Total sign tokens: {len(signs)}")
    print()
    print(f"{'Sign':<10} {'Count':>8} {'%':>8}")
    print("-" * 28)
    for sign, count in counter.most_common(top_n):
        pct = count / len(signs) * 100
        print(f"{sign:<10} {count:>8} {pct:>7.2f}%")


def cmd_words(args: argparse.Namespace) -> None:
    """Word frequency analysis."""
    corpus = load_corpus()
    words = get_all_words(corpus)
    counter = Counter(words)
    top_n = args.top or 30

    if args.format == "json":
        print(json.dumps(counter.most_common(top_n), indent=2))
        return

    print(f"Word Frequency (top {top_n} of {len(counter)} unique words)")
    print(f"Total word tokens: {len(words)}")
    print()

    # Count hapax legomena
    hapax = sum(1 for c in counter.values() if c == 1)
    print(f"Hapax legomena: {hapax} ({hapax/len(counter)*100:.1f}% of vocabulary)")
    print()

    print(f"{'Word':<25} {'Count':>8}")
    print("-" * 35)
    for word, count in counter.most_common(top_n):
        print(f"{word:<25} {count:>8}")


def cmd_cooccurrence(args: argparse.Namespace) -> None:
    """Sign co-occurrence analysis."""
    corpus = load_corpus()
    words = get_all_words(corpus)

    if args.signs:
        target_signs = [s.upper() for s in args.signs.split(",")]
    else:
        # Default: top 10 most frequent signs
        signs = get_all_signs(words)
        counter = Counter(signs)
        target_signs = [s for s, _ in counter.most_common(10)]

    # Build co-occurrence matrix
    cooccur: dict[str, Counter] = {s: Counter() for s in target_signs}
    for word in words:
        word_signs = word.split("-")
        for i, s1 in enumerate(word_signs):
            if s1 in cooccur:
                for j, s2 in enumerate(word_signs):
                    if i != j:
                        cooccur[s1][s2] += 1

    if args.format == "json":
        print(json.dumps({k: dict(v.most_common(10)) for k, v in cooccur.items()}, indent=2))
        return

    print(f"Co-occurrence (within same word)")
    for sign in target_signs:
        top = cooccur[sign].most_common(args.top or 5)
        if top:
            pairs = ", ".join(f"{s}({c})" for s, c in top)
            print(f"  {sign}: {pairs}")


def cmd_position(args: argparse.Namespace) -> None:
    """Positional analysis — sign distribution in initial/medial/final position."""
    corpus = load_corpus()
    words = get_all_words(corpus)

    initial: Counter = Counter()
    medial: Counter = Counter()
    final: Counter = Counter()

    for word in words:
        signs = word.split("-")
        if len(signs) >= 1:
            initial[signs[0]] += 1
        if len(signs) >= 2:
            final[signs[-1]] += 1
        for s in signs[1:-1]:
            medial[s] += 1

    top_n = args.top or 15

    if args.format == "json":
        print(json.dumps({
            "initial": initial.most_common(top_n),
            "medial": medial.most_common(top_n),
            "final": final.most_common(top_n),
        }, indent=2))
        return

    print(f"Positional Distribution (top {top_n})")
    for label, counter in [("Initial", initial), ("Medial", medial), ("Final", final)]:
        print(f"\n  {label}:")
        for sign, count in counter.most_common(top_n):
            print(f"    {sign:<8} {count:>6}")


def cmd_distribution(args: argparse.Namespace) -> None:
    """Site distribution analysis."""
    corpus = load_corpus()

    sites: Counter = Counter()
    site_words: dict[str, int] = {}

    for name, entry in corpus.items():
        # Extract site prefix (e.g., HT from HT1, ZA from ZA1)
        site = ""
        for ch in name:
            if ch.isalpha():
                site += ch
            else:
                break
        sites[site] += 1
        tw = entry.get("transliteratedWords", [])
        word_count = len(tw) if isinstance(tw, list) else 0
        site_words[site] = site_words.get(site, 0) + word_count

    if args.format == "json":
        print(json.dumps({
            "sites": sites.most_common(),
            "words_per_site": dict(sorted(site_words.items(), key=lambda x: -x[1])),
        }, indent=2))
        return

    print(f"Site Distribution ({len(sites)} sites)")
    print()
    print(f"{'Site':<8} {'Inscriptions':>14} {'Words':>8}")
    print("-" * 32)
    for site, count in sites.most_common():
        wc = site_words.get(site, 0)
        print(f"{site:<8} {count:>14} {wc:>8}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Linear A sign pattern analysis")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, func, help_text in [
        ("frequency", cmd_frequency, "Sign frequency analysis"),
        ("words", cmd_words, "Word frequency and hapax legomena"),
        ("cooccurrence", cmd_cooccurrence, "Sign co-occurrence within words"),
        ("position", cmd_position, "Sign positional distribution (initial/medial/final)"),
        ("distribution", cmd_distribution, "Inscription distribution by site"),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(func=func)
        p.add_argument("--top", "-n", type=int, help="Number of results")
        p.add_argument("--format", choices=["table", "json"], default="table")
        if name == "cooccurrence":
            p.add_argument("--signs", help="Comma-separated signs to analyze")

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
