# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate training data for ML-based Linear A decipherment.

v1: gordon-pairs mode only (63 transliteration → reading pairs).
v2 (deferred): augmented, transfer modes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LASHON_DIR = Path.home() / "Desktop/Programming/lashon-ha-kretan"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


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


def gordon_pairs(preview_n: int | None = None) -> list[dict[str, Any]]:
    """Generate chat-format JSONL from Gordon + YasharMana lexicon entries."""
    gordon = load_gordon()
    ym = load_yashar_mana()

    pairs = []

    for translit, entry in gordon.items():
        semitic = entry.get("semitic", "")
        meaning = entry.get("meaning", "")
        category = entry.get("category", "")
        source = entry.get("source", "")
        gordon_translit = entry.get("gordonTranslit", translit)

        pair = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Linear A decipherment assistant trained on "
                        "Cyrus H. Gordon's Semitic hypothesis. Given a Linear A "
                        "transliteration, provide the Semitic reading, meaning, "
                        "and linguistic analysis."
                    ),
                },
                {
                    "role": "user",
                    "content": f"What is the Semitic reading of the Linear A word {translit}?",
                },
                {
                    "role": "assistant",
                    "content": (
                        f"Linear A {translit} (Gordon reads: {gordon_translit}) "
                        f"corresponds to Semitic {semitic}, meaning \"{meaning}\". "
                        f"Category: {category}. Source: {source}."
                    ),
                },
            ],
        }
        pairs.append(pair)

    # Add YasharMana entries
    for translit, entry in ym.items():
        semitic = entry.get("semitic", "")
        meaning = entry.get("meaning", "")
        source = entry.get("source", "")
        note = entry.get("note", "")

        pair = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Linear A decipherment assistant. Given a "
                        "Linear A transliteration, provide the Semitic reading "
                        "and linguistic analysis."
                    ),
                },
                {
                    "role": "user",
                    "content": f"What is the Semitic reading of the Linear A word {translit}?",
                },
                {
                    "role": "assistant",
                    "content": (
                        f"Linear A {translit} corresponds to Semitic {semitic}, "
                        f"meaning \"{meaning}\". Source: {source}."
                        + (f" Note: {note}" if note else "")
                    ),
                },
            ],
        }
        pairs.append(pair)

    if preview_n:
        return pairs[:preview_n]
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate fine-tuning training data")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_gordon = sub.add_parser("gordon-pairs", help="Gordon + YasharMana reading pairs")
    p_gordon.add_argument("--output", "-o", help="Output JSONL file")
    p_gordon.add_argument("--preview", type=int, help="Preview N entries to stdout")

    args = parser.parse_args()

    if args.mode == "gordon-pairs":
        pairs = gordon_pairs(preview_n=args.preview)

        if args.preview:
            for p in pairs:
                print(json.dumps(p, ensure_ascii=False, indent=2))
                print()
            return

        output = Path(args.output) if args.output else DATA_DIR / "gordon_pairs.jsonl"
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")

        print(f"Wrote {len(pairs)} pairs to {output}", file=sys.stderr)


if __name__ == "__main__":
    main()
