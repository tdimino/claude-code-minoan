# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build unified sign registry from 4 data sources.

Merges:
1. sigla-sign-map.json (334 LA signs: AB numbers, Unicode, SigLA images)
2. sign-evolution-map.json (20 signs: CH→LA→LB lineage, PS cognates, semantics)
3. gordon.json (60+ readings: polyphonic evidence, NWS connections)
4. lib/skeleton.py SIGN_DECOMPOSITION (47 CV mappings)

Output: data/sign-registry.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.skeleton import SIGN_DECOMPOSITION

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
ASSETS_DIR = SKILL_DIR / "assets" / "scripts"

PAPER_DIR = Path.home() / "Desktop/Thera-Knossos-Minos-Paper/images/scripts"

DEFAULT_SIGLA = ASSETS_DIR / "linear-a" / "sigla-sign-map.json"
DEFAULT_EVOLUTION = ASSETS_DIR / "sign-evolution-map.json"

FALLBACK_SIGLA = PAPER_DIR / "linear-a" / "sigla-sign-map.json"
FALLBACK_EVOLUTION = PAPER_DIR / "sign-evolution-map.json"

POLYPHONIC_SIGNS: list[dict] = [
    {
        "ab_number": "AB67",
        "primary": {"value": "ki", "consonant": "k", "vowel": "i"},
        "alternatives": [
            {
                "value": "ku",
                "consonant": "k",
                "vowel": "u",
                "source": "Gordon 1966 EML §163",
                "confidence": "MEDIUM",
                "implications": [
                    "KI-RO as *kuru* rather than *kiru*",
                    "Affects skeleton extraction for all AB67 occurrences",
                ],
            }
        ],
    },
    {
        "ab_number": "AB76",
        "primary": {"value": "ra2", "consonant": "l", "vowel": "a"},
        "alternatives": [
            {
                "value": "ra",
                "consonant": "r",
                "vowel": "a",
                "source": "Base sign RA; RA2 distinguished as /la/",
                "confidence": "HIGH",
                "implications": [
                    "l/r distinction in root extraction",
                    "Affects Semitic cognate matching for liquid consonants",
                ],
            }
        ],
    },
    {
        "ab_number": "AB16",
        "primary": {"value": "qa", "consonant": "q", "vowel": "a"},
        "alternatives": [
            {
                "value": "za",
                "consonant": "z",
                "vowel": "a",
                "source": "sign-values.md; emphatic/sibilant overlap",
                "confidence": "LOW",
                "implications": [
                    "Emphatic/sibilant confusion in Linear A script",
                    "Affects root identification for emphatic consonants",
                ],
            }
        ],
    },
    {
        "ab_number": "AB09",
        "primary": {"value": "se", "consonant": "s", "vowel": "e"},
        "alternatives": [
            {
                "value": "se2",
                "consonant": "s",
                "vowel": "e",
                "source": "Ferrara 2022; CH 007 branched to AB09, AB60, AB73",
                "confidence": "MEDIUM",
                "implications": [
                    "CH 007 is ancestor of three LA signs (AB09, AB60, AB73)",
                    "Functional differentiation unclear",
                ],
            }
        ],
    },
]


def _sign_name_to_key(name: str) -> str:
    """Convert sign name to SIGN_DECOMPOSITION lookup key."""
    return name.upper().replace(" ", "")


def _extract_ab_number(s: str) -> int | None:
    """Extract numeric part from AB number for sorting."""
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else None


def _build_readings(ab_number: str, name: str) -> list[dict]:
    """Build readings list from SIGN_DECOMPOSITION + polyphonic overrides."""
    readings = []

    key = _sign_name_to_key(name)
    decomp = SIGN_DECOMPOSITION.get(key)
    if decomp:
        consonant, vowel = decomp
        readings.append({
            "value": name.lower(),
            "consonant": consonant,
            "vowel": vowel,
            "source": "Ventris 1952 (projected via Linear B)",
            "confidence": "HIGH",
            "is_primary": True,
            "implications": [],
        })

    poly = next((p for p in POLYPHONIC_SIGNS if p["ab_number"] == ab_number), None)
    if poly:
        if not readings:
            p = poly["primary"]
            readings.append({
                "value": p["value"],
                "consonant": p["consonant"],
                "vowel": p["vowel"],
                "source": "Ventris 1952 (projected via Linear B)",
                "confidence": "HIGH",
                "is_primary": True,
                "implications": [],
            })
        for alt in poly["alternatives"]:
            readings.append({
                "value": alt["value"],
                "consonant": alt.get("consonant"),
                "vowel": alt.get("vowel", ""),
                "source": alt["source"],
                "confidence": alt.get("confidence", "MEDIUM"),
                "is_primary": False,
                "implications": alt.get("implications", []),
            })

    return readings


def _find_gordon_entries(gordon_data: dict, ab_number: str, name: str) -> list[str]:
    """Find Gordon lexicon entries that use this sign."""
    entries = []
    name_upper = name.upper()
    for section_key in ("gordon", "yasharMana", "scholarly"):
        section = gordon_data.get(section_key, {})
        for word_key in section:
            syllables = word_key.split("-")
            if name_upper in syllables:
                entries.append(word_key)
    return sorted(set(entries))


def _find_evolution(evolution_signs: list[dict], ab_number: str) -> dict | None:
    """Find evolution entry for a given AB number."""
    for sign in evolution_signs:
        la = sign.get("linear_a", {})
        if la and la.get("ab_number") == ab_number:
            return sign
    return None


def _rendering_tier(ab_number: str) -> str:
    """Determine rendering tier for a sign."""
    return "unicode_native"


def build_registry(
    sigla_path: Path,
    evolution_path: Path,
    gordon_path: Path,
) -> list[dict]:
    """Build the unified sign registry."""
    sigla_data = json.loads(sigla_path.read_text(encoding="utf-8"))
    sigla_signs = sigla_data.get("signs", [])

    evolution_data = json.loads(evolution_path.read_text(encoding="utf-8"))
    evolution_signs = evolution_data.get("signs", [])

    gordon_data = json.loads(gordon_path.read_text(encoding="utf-8"))

    registry = []

    for sigla_sign in sigla_signs:
        ab_number = sigla_sign["ab_number"]
        name = sigla_sign.get("name", "")

        readings = _build_readings(ab_number, name)

        gordon_entries = _find_gordon_entries(gordon_data, ab_number, name)

        evo = _find_evolution(evolution_signs, ab_number)

        entry: dict = {
            "ab_number": ab_number,
            "name": name,
            "readings": readings,
            "rendering": {
                "unicode": sigla_sign.get("unicode"),
                "font": "NotoSansLinearA-Regular.ttf",
                "sigla_image": sigla_sign.get("image_file"),
                "sigla_url": sigla_sign.get("image_url"),
                "tier": _rendering_tier(ab_number),
            },
            "gordon_entries": gordon_entries,
        }

        if evo:
            entry["evolution"] = {
                "id": evo.get("id"),
                "cretan_hieroglyphic": evo.get("cretan_hieroglyphic"),
                "linear_b": evo.get("linear_b"),
                "cypro_minoan": evo.get("cypro_minoan"),
                "proto_sinaitic": evo.get("proto_sinaitic"),
                "graphic_tendencies": evo.get("graphic_tendencies", []),
            }
            entry["semantic_context"] = evo.get("semantic_context")

        registry.append(entry)

    registry.sort(key=lambda e: _extract_ab_number(e["ab_number"]) or 9999)

    return registry


def _resolve_path(primary: Path, fallback: Path, label: str) -> Path:
    """Resolve path: prefer skill-local assets, fall back to paper repo."""
    if primary.exists():
        return primary
    if fallback.exists():
        print(f"  {label}: using fallback {fallback}", file=sys.stderr)
        return fallback
    print(f"Error: {label} not found at {primary} or {fallback}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build unified sign registry")
    parser.add_argument(
        "--sigla-map", type=Path, default=None,
        help="Path to sigla-sign-map.json",
    )
    parser.add_argument(
        "--evolution-map", type=Path, default=None,
        help="Path to sign-evolution-map.json",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=DATA_DIR / "sign-registry.json",
        help="Output path",
    )
    args = parser.parse_args()

    sigla = args.sigla_map or _resolve_path(DEFAULT_SIGLA, FALLBACK_SIGLA, "SigLA map")
    evolution = args.evolution_map or _resolve_path(DEFAULT_EVOLUTION, FALLBACK_EVOLUTION, "Evolution map")

    if args.sigla_map and not args.sigla_map.exists():
        print(f"Error: SigLA map not found at {args.sigla_map}", file=sys.stderr)
        sys.exit(1)
    if args.evolution_map and not args.evolution_map.exists():
        print(f"Error: Evolution map not found at {args.evolution_map}", file=sys.stderr)
        sys.exit(1)

    gordon_path = DATA_DIR / "gordon.json"
    if not gordon_path.exists():
        print(f"Error: {gordon_path} not found. Run corpus_extract.py --all first.", file=sys.stderr)
        sys.exit(1)

    registry = build_registry(sigla, evolution, gordon_path)

    polyphonic_count = sum(1 for e in registry if len(e["readings"]) > 1)
    evolution_count = sum(1 for e in registry if "evolution" in e)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "metadata": {
            "description": "Unified Linear A sign registry",
            "sources": [
                "sigla-sign-map.json (SigLA tablet photographs)",
                "sign-evolution-map.json (CH→LA→LB cross-script lineage)",
                "gordon.json (Gordon/YasharMana/scholarly readings)",
                "skeleton.py SIGN_DECOMPOSITION (CV phonetic values)",
            ],
            "total_signs": len(registry),
            "polyphonic_signs": polyphonic_count,
            "signs_with_evolution": evolution_count,
        },
        "signs": registry,
    }

    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    size_kb = args.output.stat().st_size / 1024
    print(f"Wrote {args.output} ({size_kb:.0f}KB)", file=sys.stderr)
    print(f"  {len(registry)} signs total", file=sys.stderr)
    print(f"  {polyphonic_count} polyphonic signs", file=sys.stderr)
    print(f"  {evolution_count} signs with evolution data", file=sys.stderr)
    print(f"  {sum(len(e['gordon_entries']) for e in registry)} Gordon cross-references", file=sys.stderr)


if __name__ == "__main__":
    main()
