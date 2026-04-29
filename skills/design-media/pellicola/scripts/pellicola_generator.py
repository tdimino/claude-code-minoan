#!/usr/bin/env python3
"""
Pellicola Generator

Generate cinematic case study pages from templates with customizable metadata.

Usage:
    python pellicola_generator.py --mode case-study --title "Taboo" --output taboo.html
    python pellicola_generator.py --mode hero --title "Ana Maxim" --output hero.html
    python pellicola_generator.py --mode credits --output credits.html
    python pellicola_generator.py --mode gallery --output gallery.html
"""

import argparse
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "assets" / "templates"

MODES = {
    "case-study": "case-study.html",
    "hero": "hero-section.html",
    "credits": "credits-grid.html",
    "gallery": "footage-gallery.html",
}


def apply_metadata(content: str, args) -> str:
    """Replace placeholder metadata in template with user-specified values."""

    if args.title:
        content = content.replace("Taboo", args.title)
        content = content.replace("Film Title", args.title)

    if args.director:
        content = content.replace("Shauly Melamed", args.director)

    if args.genre:
        content = content.replace("Documentary", args.genre)
        content = content.replace("DOCUMENTARY", args.genre.upper())

    if args.year:
        content = content.replace(">2024<", f">{args.year}<")

    if args.runtime:
        content = content.replace("93 min", args.runtime)

    # Update <title> tag
    title_parts = [args.title or "Film"]
    if args.mode == "case-study" and args.director:
        title_parts.append(f"A {args.genre or 'Film'} by {args.director}")
    elif args.mode == "hero":
        title_parts.append("Hero")
    elif args.mode == "credits":
        title_parts.append("Credits")
    elif args.mode == "gallery":
        title_parts.append("Gallery")

    new_title = " — ".join(title_parts)
    content = re.sub(r"<title>.*?</title>", f"<title>{new_title}</title>", content)

    return content


def generate(args) -> str:
    """Load template and apply customizations."""

    template_name = MODES.get(args.mode)
    if not template_name:
        print(f"Error: Unknown mode '{args.mode}'. Available: {', '.join(MODES.keys())}")
        sys.exit(1)

    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        print(f"Error: Template not found: {template_path}")
        print(f"Available templates: {', '.join(f.name for f in TEMPLATES_DIR.glob('*.html'))}")
        sys.exit(1)

    content = template_path.read_text(encoding="utf-8")
    content = apply_metadata(content, args)

    return content


def main():
    parser = argparse.ArgumentParser(
        description="Generate pellicola cinematic case study pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode case-study --title "Taboo" --director "Shauly Melamed" --output taboo.html
  %(prog)s --mode hero --title "Ana Maxim" --genre "Short Film" --output hero.html
  %(prog)s --mode credits --director "Jane Doe" --output credits.html
  %(prog)s --mode gallery --output gallery.html
        """,
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=list(MODES.keys()),
        help="Output mode: case-study, hero, credits, gallery",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Film title (default: template placeholder)",
    )
    parser.add_argument(
        "--director",
        default=None,
        help="Director name",
    )
    parser.add_argument(
        "--genre",
        default=None,
        help="Genre label (e.g., Documentary, Short Film, Feature)",
    )
    parser.add_argument(
        "--year",
        default=None,
        help="Release year",
    )
    parser.add_argument(
        "--runtime",
        default=None,
        help="Runtime (e.g., '93 min')",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()
    content = generate(args)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"Generated: {output_path} ({len(content):,} bytes)")
    else:
        print(content)


if __name__ == "__main__":
    main()
