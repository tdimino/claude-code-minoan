#!/usr/bin/env python3
"""
Compile quotation markdown files into themed documents for ANE research.
Organizes by 5 themes: Thera, Knossos, Minos, Palestine, Linguistics.

Usage:
    python3 compile_quotations.py [input_dir] [output_file]

Examples:
    python3 compile_quotations.py ~/Desktop/Thera-Knossos-Minos-Paper/quotations
    python3 compile_quotations.py ./snippets ./compiled_quotations.md
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import re
import json


# Theme keywords for auto-categorization
THEME_KEYWORDS: Dict[str, List[str]] = {
    "Thera": [
        "thera", "akrotiri", "santorini", "volcanic", "eruption", "tempest stela",
        "aegean", "cyclades", "bronze age collapse", "minoan eruption", "calliste"
    ],
    "Knossos": [
        "knossos", "labyrinth", "palace", "minoan", "crete", "evans", "linear b",
        "mycenaean", "lustral basin", "fresco", "throne room", "bull leaping",
        "snake goddess", "priestess", "peak sanctuary", "horns of consecration"
    ],
    "Minos": [
        "minos", "minotaur", "daedalus", "ariadne", "theseus", "king minos",
        "thalassocracy", "zeus", "europa", "pasiphae", "cretan", "dikta", "dikte",
        "kadmos", "membliaros", "euphemos", "bezalel", "moses"
    ],
    "Palestine": [
        "palestine", "israel", "judah", "jerusalem", "biblical", "hebrew", "aramaic",
        "canaanite", "philistine", "gaza", "asherah", "yahweh", "temple", "solomon",
        "david", "deuteronomy", "chronicles", "isaiah", "psalms", "targum", "talmud",
        "ugarit", "syria", "lebanon", "phoenician", "genesis", "exodus", "tehom",
        "tiamat", "gnostic", "sethian", "orphic"
    ],
    "Linguistics": [
        "etymology", "linguistic", "semitic", "indo-european", "phonetic", "morphology",
        "cognate", "root", "prefix", "suffix", "comparative", "historical linguistics",
        "phonological", "semantic", "lexical", "grammatical", "syntax", "phoneme",
        "consonant", "vowel", "derivation", "borrowing", "loanword", "astour", "gordon",
        "begadkephat", "tip'eret", "purpura", "kaphtor"
    ]
}


def extract_metadata(file_path: Path) -> Tuple[str, str, str]:
    """Extract title, content, and explicit category from a markdown file."""
    try:
        content = file_path.read_text(encoding='utf-8').strip()
        title = file_path.stem
        category = ""

        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        for line in lines:
            if line.strip().startswith('**Category**:'):
                category = line.split(':', 1)[1].strip()
                break

        return title, content, category
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return file_path.stem, f"Error: {e}", ""


def categorize_by_content(title: str, content: str) -> str:
    """Auto-categorize based on keyword matching."""
    search_text = (title + " " + content).lower()

    scores = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in search_text)
        if score > 0:
            scores[theme] = score

    return max(scores, key=lambda x: scores[x]) if scores else "Uncategorized"


def organize_by_theme(quotations: List[Tuple[str, str, str, str]]) -> Dict[str, List[Tuple[str, str, str]]]:
    """Organize quotations into themed buckets."""
    themes = {theme: [] for theme in THEME_KEYWORDS.keys()}
    themes["Uncategorized"] = []

    for title, content, category, filename in quotations:
        target = None

        if category:
            for theme in themes:
                if theme.lower() in category.lower():
                    target = theme
                    break

        if not target:
            target = categorize_by_content(title, content)

        themes[target].append((title, content, filename))

    return {k: v for k, v in themes.items() if v}


def compile_to_markdown(themes: Dict[str, List[Tuple[str, str, str]]]) -> str:
    """Generate final compiled markdown document."""
    output = []

    # Header
    output.append("---")
    output.append("title: 'ANE Research Quotations'")
    output.append(f"date: '{datetime.now().strftime('%B %d, %Y')}'")
    output.append("---\n")
    output.append("# Ancient Near East Research: Compiled Quotations\n")

    # TOC
    output.append("## Table of Contents\n")
    for i, (theme, items) in enumerate(themes.items(), 1):
        if items:
            anchor = theme.lower().replace(' ', '-')
            output.append(f"{i}. [{theme}](#{anchor}) ({len(items)} sources)")
    output.append("\n---\n")

    # Content
    section = 1
    for theme, items in themes.items():
        if not items:
            continue

        anchor = theme.lower().replace(' ', '-')
        output.append(f"# {section}. {theme} {{#{anchor}}}\n")

        for title, content, filename in sorted(items, key=lambda x: x[0].lower()):
            output.append(f"## {title}\n")
            output.append(f"*Source: {filename}*\n")

            # Strip title from content if present
            lines = content.split('\n')
            if lines and lines[0].startswith('# '):
                content = '\n'.join(lines[1:]).strip()

            output.append(content + "\n")
            output.append("---\n")

        section += 1

    return '\n'.join(output)


def main():
    # Default paths
    input_dir = Path("~/Desktop/Thera-Knossos-Minos-Paper/quotations").expanduser()
    output_file = Path("compiled_quotations.md")

    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1]).expanduser()
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2]).expanduser()

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        sys.exit(1)

    print(f"Scanning: {input_dir}")

    # Collect all markdown files
    quotations = []
    for md_file in input_dir.glob("**/*.md"):
        title, content, category = extract_metadata(md_file)
        quotations.append((title, content, category, str(md_file.relative_to(input_dir))))

    # Also check for JSON database
    json_files = list(input_dir.glob("**/*.json"))
    for json_file in json_files:
        try:
            data = json.loads(json_file.read_text())
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and 'text' in entry:
                        title = entry.get('source', entry.get('title', 'Unknown'))
                        content = entry.get('text', '')
                        category = entry.get('category', '')
                        quotations.append((title, content, category, json_file.name))
        except Exception as e:
            print(f"Warning: Could not parse {json_file}: {e}")

    if not quotations:
        print("No quotation files found!")
        sys.exit(1)

    print(f"Found {len(quotations)} sources")

    # Organize and compile
    themes = organize_by_theme(quotations)

    print("\nTheme distribution:")
    for theme, items in themes.items():
        if items:
            print(f"  {theme}: {len(items)}")

    compiled = compile_to_markdown(themes)
    output_file.write_text(compiled, encoding='utf-8')

    print(f"\nOutput: {output_file}")
    print(f"Size: {output_file.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
