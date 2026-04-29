#!/usr/bin/env python3
"""
Pellicola Validator

Validate HTML files against pellicola design rules.

Usage:
    python validate_pellicola.py output.html
    python validate_pellicola.py --strict output.html
"""

import argparse
import re
import sys
from pathlib import Path


REQUIRED_CHECKS = [
    ("viewport meta", r'<meta\s+name="viewport"'),
    ("--pel-* properties", r"--pel-"),
    ("no React/Vue/Svelte", None),
    ("cream background", r"--pel-cream"),
    ("prefers-reduced-motion", r"prefers-reduced-motion"),
    ("Google Fonts loaded", r"fonts\.googleapis\.com"),
    ("data-pel attributes", r"data-pel"),
    ("skip link", r"pel-skip-link"),
    ("semantic main element", r"<main"),
    ("semantic section elements", r"<section"),
]

OPTIONAL_CHECKS = [
    ("IntersectionObserver", r"IntersectionObserver"),
    ("requestAnimationFrame", r"requestAnimationFrame"),
    ("pel-frame class", r"pel-frame"),
    ("pel-credits grid", r"pel-credits"),
    ("pel-gallery section", r"pel-gallery"),
    ("pel-divider component", r"pel-divider"),
    ("pel-play button", r"pel-play"),
    ("OKLCH colors", r"oklch\("),
    ("CSS custom properties only", r"var\(--pel-"),
    ("aria-label on sections", r'aria-label='),
    ("passive scroll listener", r"passive:\s*true"),
    ("loading=lazy on images", r'loading="lazy"'),
]

ANTI_PATTERNS = [
    ("white background (#FFFFFF)", r"(?:background|bg).*?#(?:FFF(?:FFF)?|fff(?:fff)?)(?!\w)"),
    ("Inter font", r"['\"]Inter['\"]"),
    ("Roboto font", r"['\"]Roboto['\"]"),
    ("system-ui font", r"system-ui"),
    ("border-left accent stripe", r"border-left:\s*[2-9]\d*px\s+solid"),
    ("background-clip: text gradient", r"background-clip:\s*text"),
    ("React import", r"import\s+React|from\s+['\"]react['\"]"),
    ("Vue import", r"from\s+['\"]vue['\"]"),
    ("Svelte import", r"from\s+['\"]svelte['\"]"),
    ("setInterval for animation", r"setInterval\s*\("),
    ("height transition (use grid-template-rows)", r"transition:.*?height"),
    ("ease timing (use --pel-ease)", r"transition:[^;]*(?<!-)(?<!var\(--pel-)\bease\b(?![-\w])"),
]


def validate(filepath: str, strict: bool = False) -> tuple[int, int, int]:
    """Validate a pellicola HTML file. Returns (passed, warned, failed)."""

    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    content = path.read_text(encoding="utf-8")
    passed = 0
    warned = 0
    failed = 0

    print(f"\nValidating: {filepath}")
    print(f"File size: {len(content):,} bytes")
    print()

    # Required checks
    print("Required checks:")
    for name, pattern in REQUIRED_CHECKS:
        if name == "no React/Vue/Svelte":
            has_react = bool(re.search(r"import\s+React|from\s+['\"]react['\"]", content))
            has_vue = bool(re.search(r"from\s+['\"]vue['\"]", content))
            has_svelte = bool(re.search(r"from\s+['\"]svelte['\"]", content))
            if not has_react and not has_vue and not has_svelte:
                print(f"  ✓ {name}")
                passed += 1
            else:
                frameworks = []
                if has_react: frameworks.append("React")
                if has_vue: frameworks.append("Vue")
                if has_svelte: frameworks.append("Svelte")
                print(f"  ✗ {name} — found: {', '.join(frameworks)}")
                failed += 1
        elif pattern and re.search(pattern, content):
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name}")
            failed += 1

    print()

    # Optional checks
    print("Optional checks:")
    for name, pattern in OPTIONAL_CHECKS:
        if pattern and re.search(pattern, content):
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ~ {name}")
            warned += 1

    print()

    # Anti-pattern checks
    print("Anti-pattern scan:")
    for name, pattern in ANTI_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            print(f"  ✗ FOUND: {name} ({len(matches)} occurrence{'s' if len(matches) > 1 else ''})")
            if strict:
                failed += 1
            else:
                warned += 1
        else:
            print(f"  ✓ Clean: {name}")
            passed += 1

    print()
    print(f"Results: {passed} passed, {warned} warnings, {failed} failed")

    if failed > 0:
        print("FAIL")
    elif warned > 0:
        print("PASS (with warnings)")
    else:
        print("PASS")

    return passed, warned, failed


def main():
    parser = argparse.ArgumentParser(
        description="Validate pellicola HTML files against design rules",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="HTML file(s) to validate",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat anti-pattern matches as failures instead of warnings",
    )

    args = parser.parse_args()

    total_failed = 0
    for filepath in args.files:
        _, _, failed = validate(filepath, strict=args.strict)
        total_failed += failed

    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
