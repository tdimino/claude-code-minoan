# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Extract Linear A corpus and Semitic lexicon from JS source files.

Parses LinearAInscriptions.js and semiticLexicon.js into structured JSON
for downstream analysis scripts.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.js_parser import parse_inscriptions, parse_lexicon

# Default source paths
LASHON_DIR = Path.home() / "Desktop/Programming/lashon-ha-kretan"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

INSCRIPTIONS_JS = LASHON_DIR / "LinearAInscriptions.js"
LEXICON_JS = LASHON_DIR / "semiticLexicon.js"
SEMITIC_JSON = LASHON_DIR / "etymology" / "Semitic.json"


def extract_corpus(args: argparse.Namespace) -> None:
    """Extract inscriptions and optionally lexicon data."""
    DATA_DIR.mkdir(exist_ok=True)

    inscriptions_path = Path(args.inscriptions) if args.inscriptions else INSCRIPTIONS_JS
    inscriptions = parse_inscriptions(inscriptions_path)
    print(f"Extracted {len(inscriptions)} inscriptions", file=sys.stderr)

    # Filter by site if requested
    if args.site:
        site_upper = args.site.upper()
        inscriptions = {
            k: v for k, v in inscriptions.items()
            if k.startswith(site_upper)
        }
        print(f"  Filtered to {len(inscriptions)} from site {args.site}", file=sys.stderr)

    output_path = Path(args.output) if args.output else DATA_DIR / "corpus.json"
    _write_output(inscriptions, output_path, args.format)
    print(f"Wrote {output_path}", file=sys.stderr)

    if args.with_gordon or args.all:
        _extract_lexicons(args)

    if args.all:
        _copy_semitic_roots(args)


def _extract_lexicons(args: argparse.Namespace) -> None:
    """Extract Gordon and YasharMana lexicons."""
    lexicon_path = Path(args.lexicon) if args.lexicon else LEXICON_JS

    gordon = parse_lexicon(lexicon_path, "gordon")
    print(f"Extracted {len(gordon)} Gordon entries", file=sys.stderr)

    ym = parse_lexicon(lexicon_path, "yasharMana")
    print(f"Extracted {len(ym)} YasharMana entries", file=sys.stderr)

    scholarly = parse_lexicon(lexicon_path, "scholarly")
    print(f"Extracted {len(scholarly)} scholarly entries", file=sys.stderr)

    combined = {"gordon": gordon, "yasharMana": ym, "scholarly": scholarly}
    output_path = DATA_DIR / "gordon.json"
    _write_output(combined, output_path, "json")
    print(f"Wrote {output_path}", file=sys.stderr)


def _copy_semitic_roots(args: argparse.Namespace) -> None:
    """Copy Proto-Semitic roots JSON to data dir."""
    src = Path(args.semitic) if args.semitic else SEMITIC_JSON
    if not src.exists():
        print(f"Warning: {src} not found, skipping Proto-Semitic roots", file=sys.stderr)
        return

    dst = DATA_DIR / "semitic_roots.json"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    # Count entries
    roots = json.loads(src.read_text(encoding="utf-8"))
    print(f"Copied {len(roots)} Proto-Semitic roots to {dst}", file=sys.stderr)


def _write_output(data: dict, path: Path, fmt: str) -> None:
    """Write data in requested format."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "jsonl":
        with open(path.with_suffix(".jsonl"), "w", encoding="utf-8") as f:
            for key, value in data.items():
                record = {"key": key, **value} if isinstance(value, dict) else {"key": key, "value": value}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    elif fmt == "csv":
        if not data:
            path.with_suffix(".csv").write_text("", encoding="utf-8")
            return
        first = next(iter(data.values()))
        if isinstance(first, dict):
            fieldnames = ["key"] + list(first.keys())
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=fieldnames)
            writer.writeheader()
            for key, value in data.items():
                writer.writerow({"key": key, **{k: str(v) for k, v in value.items()}})
            path.with_suffix(".csv").write_text(buf.getvalue(), encoding="utf-8")
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Linear A corpus from JS sources")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--site", help="Filter by site prefix (e.g., HT, ZA, PK)")
    parser.add_argument("--with-gordon", action="store_true", help="Also extract Gordon/YasharMana lexicon")
    parser.add_argument("--all", action="store_true", help="Extract everything: corpus + lexicons + Proto-Semitic")
    parser.add_argument("--format", choices=["json", "jsonl", "csv"], default="json")
    parser.add_argument("--inscriptions", help="Path to LinearAInscriptions.js")
    parser.add_argument("--lexicon", help="Path to semiticLexicon.js")
    parser.add_argument("--semitic", help="Path to Semitic.json")

    args = parser.parse_args()
    extract_corpus(args)


if __name__ == "__main__":
    main()
