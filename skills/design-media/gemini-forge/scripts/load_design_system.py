#!/usr/bin/env python3
"""
Load Design System: Bundle design tokens, Tailwind config, and brand briefs
into a single context string for Gemini 3.1 Pro's 1M token window.

This unlocks the key differentiator: loading an entire design system into context
before asking Gemini to generate components that stay on-system.

Usage:
    # Bundle tokens + brand brief
    python load_design_system.py --tokens tokens.css --brief brand.md --output context.txt

    # Bundle Tailwind config + tokens + brief
    python load_design_system.py --tokens tokens.css --tailwind tailwind.config.ts --brief brand.md

    # Bundle an entire directory of design system files
    python load_design_system.py --dir ./design-system --output context.txt

    # Then use with generate_ui.py
    python generate_ui.py "hero section" --design-context context.txt --thinking high
"""

import argparse
import sys
from pathlib import Path

# Approximate tokens per character (conservative estimate for code/CSS)
CHARS_PER_TOKEN = 3.5
MAX_CONTEXT_TOKENS = 200_000  # Leave 800K for task + generation
MAX_CONTEXT_CHARS = int(MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN)

# File extensions to include when scanning a directory
DESIGN_SYSTEM_EXTENSIONS = {
    ".css", ".scss", ".less",
    ".ts", ".tsx", ".js", ".jsx",
    ".json",
    ".md", ".mdx",
    ".yaml", ".yml",
    ".svg",
}

# Files to prioritize (loaded first, never truncated)
PRIORITY_PATTERNS = [
    "tokens", "variables", "theme", "colors", "typography",
    "tailwind.config", "design-tokens", "brand",
]


def load_file(path: Path) -> str:
    """Load a file and return its content with a header."""
    try:
        content = path.read_text(encoding="utf-8")
        return f"\n### {path.name}\n\n```{path.suffix.lstrip('.')}\n{content}\n```\n"
    except Exception as e:
        print(f"  Warning: Could not read {path}: {e}", file=sys.stderr)
        return ""


def is_priority(path: Path) -> bool:
    """Check if a file matches priority patterns."""
    name_lower = path.stem.lower()
    return any(pattern in name_lower for pattern in PRIORITY_PATTERNS)


def load_directory(dir_path: Path) -> str:
    """Load all design system files from a directory, prioritizing tokens."""
    files = sorted(
        [f for f in dir_path.rglob("*") if f.suffix in DESIGN_SYSTEM_EXTENSIONS and f.is_file()],
        key=lambda f: (0 if is_priority(f) else 1, f.name),
    )

    if not files:
        print(f"  Warning: No design system files found in {dir_path}", file=sys.stderr)
        return ""

    sections = []
    total_chars = 0

    for f in files:
        content = load_file(f)
        if total_chars + len(content) > MAX_CONTEXT_CHARS:
            remaining = MAX_CONTEXT_CHARS - total_chars
            if remaining > 500:
                content = content[:remaining] + "\n\n[TRUNCATED — context budget reached]\n"
                sections.append(content)
                skipped = len(files) - files.index(f) - 1  # f was partially included
            else:
                skipped = len(files) - files.index(f)  # f was fully skipped
            print(f"  Context budget reached at {f.name}. {skipped} files skipped.", file=sys.stderr)
            break
        sections.append(content)
        total_chars += len(content)

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(
        description="Bundle design system files into a context string for Gemini Forge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tokens", help="CSS tokens/variables file")
    parser.add_argument("--tailwind", help="Tailwind config file")
    parser.add_argument("--brief", help="Brand brief / design guidelines (Markdown)")
    parser.add_argument("--dir", help="Directory containing design system files")
    parser.add_argument(
        "--output", "-o",
        default="./output/design_context.txt",
        help="Output file path (default: ./output/design_context.txt)",
    )

    args = parser.parse_args()

    if not any([args.tokens, args.tailwind, args.brief, args.dir]):
        parser.error("Provide at least one input: --tokens, --tailwind, --brief, or --dir")

    sections = ["# Design System Context\n"]
    sections.append("Use these design tokens, configuration, and guidelines when generating components.\n")

    # Load individual files
    if args.brief:
        path = Path(args.brief).expanduser().resolve()
        if path.exists():
            sections.append("\n## Brand Guidelines\n")
            sections.append(load_file(path))
            print(f"  Loaded brief: {path.name}")
        else:
            print(f"  Warning: Brief not found: {path}", file=sys.stderr)

    if args.tokens:
        path = Path(args.tokens).expanduser().resolve()
        if path.exists():
            sections.append("\n## Design Tokens\n")
            sections.append(load_file(path))
            print(f"  Loaded tokens: {path.name}")
        else:
            print(f"  Warning: Tokens not found: {path}", file=sys.stderr)

    if args.tailwind:
        path = Path(args.tailwind).expanduser().resolve()
        if path.exists():
            sections.append("\n## Tailwind Configuration\n")
            sections.append(load_file(path))
            print(f"  Loaded Tailwind config: {path.name}")
        else:
            print(f"  Warning: Tailwind config not found: {path}", file=sys.stderr)

    # Load directory
    if args.dir:
        dir_path = Path(args.dir).expanduser().resolve()
        if dir_path.is_dir():
            sections.append("\n## Design System Files\n")
            sections.append(load_directory(dir_path))
            print(f"  Loaded directory: {dir_path}")
        else:
            print(f"  Warning: Directory not found: {dir_path}", file=sys.stderr)

    # Write output
    context = "\n".join(sections)
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(context, encoding="utf-8")

    # Stats
    approx_tokens = int(len(context) / CHARS_PER_TOKEN)
    print()
    print("=" * 60)
    print("  DESIGN SYSTEM CONTEXT BUNDLED")
    print("=" * 60)
    print(f"  Output: {output_path}")
    print(f"  Size: {len(context):,} chars (~{approx_tokens:,} tokens)")
    print(f"  Budget: {approx_tokens:,} / {MAX_CONTEXT_TOKENS:,} tokens ({approx_tokens * 100 // MAX_CONTEXT_TOKENS}%)")
    print()
    print("  Usage:")
    print(f'  uv run generate_ui.py "hero section" --design-context {output_path}')


if __name__ == "__main__":
    main()
