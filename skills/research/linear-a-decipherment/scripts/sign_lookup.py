# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Look up Linear A signs from the unified sign registry.

Subcommands:
  sign_lookup.py AB67                    # by AB number
  sign_lookup.py --phonetic ki           # by sound value
  sign_lookup.py --unicode U+10633       # by codepoint
  sign_lookup.py --polyphonic            # list all polyphonic signs
  sign_lookup.py AB67 --evolution        # show CH→LA→LB chain
  sign_lookup.py AB67 --reading ku       # show implications of alt reading
  sign_lookup.py AB67 --format json      # JSON output
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REGISTRY_FILE = DATA_DIR / "sign-registry.json"


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        print(f"Error: {REGISTRY_FILE} not found. Run build_registry.py first.", file=sys.stderr)
        sys.exit(1)
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def build_indices(signs: list[dict]) -> tuple[dict, dict, dict]:
    """Build lookup indices: by ab_number, by phonetic value, by unicode."""
    by_ab: dict[str, dict] = {}
    by_phonetic: dict[str, list[dict]] = {}
    by_unicode: dict[str, dict] = {}

    for sign in signs:
        ab = sign["ab_number"]
        by_ab[ab] = sign

        for reading in sign.get("readings", []):
            val = reading["value"]
            by_phonetic.setdefault(val, []).append(sign)

        unicode_val = sign.get("rendering", {}).get("unicode")
        if unicode_val:
            by_unicode[unicode_val] = sign

    return by_ab, by_phonetic, by_unicode


def format_sign(sign: dict, show_evolution: bool = False, reading_filter: str | None = None) -> str:
    lines = [
        f"{'='*60}",
        f"  {sign['ab_number']}  —  {sign['name']}",
        f"{'='*60}",
    ]

    rendering = sign.get("rendering", {})
    if rendering.get("unicode"):
        lines.append(f"  Unicode: {rendering['unicode']}")
    if rendering.get("sigla_image"):
        lines.append(f"  SigLA:   {rendering['sigla_image']}")
    lines.append(f"  Tier:    {rendering.get('tier', 'unknown')}")
    lines.append("")

    readings = sign.get("readings", [])
    if readings:
        lines.append("  Readings:")
        for r in readings:
            primary = " (primary)" if r.get("is_primary") else ""
            cv = f"{r.get('consonant') or '∅'}{r['vowel']}"
            lines.append(f"    /{r['value']}/ [{cv}] — {r['confidence']}{primary}")
            lines.append(f"      Source: {r['source']}")
            if r.get("implications"):
                for imp in r["implications"]:
                    lines.append(f"      → {imp}")
        lines.append("")

    if reading_filter:
        target = [r for r in readings if r["value"] == reading_filter]
        if target:
            r = target[0]
            lines.append(f"  Reading /{reading_filter}/ details:")
            lines.append(f"    Confidence: {r['confidence']}")
            lines.append(f"    Source: {r['source']}")
            if r.get("implications"):
                lines.append("    Implications:")
                for imp in r["implications"]:
                    lines.append(f"      • {imp}")
            lines.append("")
        else:
            lines.append(f"  No reading /{reading_filter}/ found for {sign['ab_number']}")
            lines.append("")

    gordon = sign.get("gordon_entries", [])
    if gordon:
        lines.append(f"  Gordon entries ({len(gordon)}):")
        lines.append(f"    {', '.join(gordon)}")
        lines.append("")

    if show_evolution and "evolution" in sign:
        evo = sign["evolution"]
        lines.append("  Evolution (CH → LA → LB):")

        ch = evo.get("cretan_hieroglyphic")
        if ch:
            lines.append(f"    CH: {ch.get('sign_number', '?')} — {ch.get('pictographic_ancestor', '?')}")
            if ch.get("font_codepoint_hex"):
                lines.append(f"        Font: PUA 0x{ch['font_codepoint_hex']}")

        lines.append(f"    LA: {sign['ab_number']} — /{sign['name']}/")

        lb = evo.get("linear_b")
        if lb:
            lines.append(f"    LB: {lb.get('sign_number', '?')} — /{lb.get('value', '?')}/")

        cm = evo.get("cypro_minoan")
        if cm:
            lines.append(f"    CM: {cm.get('sign_number', '?')} — /{cm.get('value', '?')}/")

        ps = evo.get("proto_sinaitic")
        if ps:
            lines.append(f"    PS: {ps.get('letter', '?')} — {ps.get('meaning', '?')}")
            lines.append(f"        Connection: {ps.get('connection_type', '?')}")

        tendencies = evo.get("graphic_tendencies", [])
        if tendencies:
            lines.append(f"    Graphic tendencies: {', '.join(tendencies)}")

        lines.append("")

    ctx = sign.get("semantic_context")
    if ctx and show_evolution:
        lines.append("  Semantic context:")
        if ctx.get("pictograph"):
            lines.append(f"    Pictograph: {ctx['pictograph']}")
        if ctx.get("cultic_significance"):
            lines.append(f"    Cultic: {ctx['cultic_significance']}")
        if ctx.get("nws_connections"):
            lines.append(f"    NWS: {ctx['nws_connections']}")
        lines.append("")

    return "\n".join(lines)


def cmd_lookup(args: argparse.Namespace) -> None:
    data = load_registry()
    signs = data["signs"]
    by_ab, by_phonetic, by_unicode = build_indices(signs)

    if args.polyphonic:
        poly = [s for s in signs if len(s.get("readings", [])) > 1]
        if args.format == "json":
            print(json.dumps(poly, ensure_ascii=False, indent=2))
        else:
            print(f"Polyphonic Signs ({len(poly)} found)")
            print(f"{'='*60}")
            for s in poly:
                readings_str = " / ".join(f"/{r['value']}/" for r in s["readings"])
                print(f"  {s['ab_number']:<8} {s['name']:<8} → {readings_str}")
                for r in s["readings"]:
                    if not r.get("is_primary") and r.get("implications"):
                        for imp in r["implications"]:
                            print(f"           → {imp}")
            print()
            print("⚠ DISCLAIMER: All readings are hypothetical. Linear A remains undeciphered.")
        return

    if args.phonetic:
        matches = by_phonetic.get(args.phonetic.lower(), [])
        if not matches:
            print(f"No signs found with phonetic value /{args.phonetic}/", file=sys.stderr)
            sys.exit(1)
        if args.format == "json":
            print(json.dumps(matches, ensure_ascii=False, indent=2))
        else:
            for s in matches:
                print(format_sign(s, show_evolution=args.evolution))
        return

    if args.unicode:
        sign = by_unicode.get(args.unicode.upper())
        if not sign:
            print(f"No sign found with Unicode {args.unicode}", file=sys.stderr)
            sys.exit(1)
        if args.format == "json":
            print(json.dumps(sign, ensure_ascii=False, indent=2))
        else:
            print(format_sign(sign, show_evolution=args.evolution, reading_filter=args.reading))
        return

    if args.ab_number:
        ab = args.ab_number.upper()
        if not ab.startswith("AB"):
            ab = f"AB{ab}"
        sign = by_ab.get(ab)
        if not sign:
            print(f"No sign found with AB number {ab}", file=sys.stderr)
            sys.exit(1)
        if args.format == "json":
            print(json.dumps(sign, ensure_ascii=False, indent=2))
        else:
            print(format_sign(sign, show_evolution=args.evolution, reading_filter=args.reading))
        return

    print("Specify an AB number, --phonetic, --unicode, or --polyphonic", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up Linear A signs from registry")
    parser.add_argument("ab_number", nargs="?", help="AB number (e.g., AB67 or 67)")
    parser.add_argument("--phonetic", "-p", help="Look up by phonetic value (e.g., ki)")
    parser.add_argument("--unicode", "-u", help="Look up by Unicode codepoint (e.g., U+10633)")
    parser.add_argument("--polyphonic", action="store_true", help="List all polyphonic signs")
    parser.add_argument("--evolution", "-e", action="store_true", help="Show CH→LA→LB evolution chain")
    parser.add_argument("--reading", "-r", help="Show details for a specific reading (e.g., ku)")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text")

    args = parser.parse_args()
    cmd_lookup(args)


if __name__ == "__main__":
    main()
