#!/usr/bin/env python3
"""
Screenshot-to-Code: Convert UI screenshots to React/HTML using describe-first pipeline.

Uses the faithful transformation technique from gemini-claude-resonance:
1. ANALYZE: Gemini describes the screenshot as a structured technical spec
2. GENERATE: Gemini implements the spec as code (not from the image directly)

This two-step approach prevents layout hallucination by grounding code generation
in a verified textual spec rather than direct image-to-code translation.

Usage:
    # Full pipeline: screenshot → spec → code
    python screenshot_to_code.py screenshot.png --framework react

    # Step 1 only: get the spec for inspection
    python screenshot_to_code.py screenshot.png --analyze-only

    # Step 2 only: generate from an existing or corrected spec
    python screenshot_to_code.py --from-spec spec.md --framework html

Environment:
    GEMINI_API_KEY - Required for Gemini API access
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gemini_text import GeminiForgeClient


ANALYZE_PROMPT = """Analyze this UI screenshot in precise detail for code implementation.

Produce a structured technical spec covering:

## Layout Structure
- Overall page layout (grid, flex, positioning)
- Section breakdown (header, hero, content areas, footer)
- Responsive behavior implied by the design

## Component Hierarchy
- List every distinct component visible
- Nesting relationships (parent → child)
- Repeated patterns (lists, grids, card collections)

## Visual Design
- Color palette: extract exact colors where possible (hex or approximate OKLCH)
- Typography: font families, sizes, weights, line-heights
- Spacing rhythm: padding/margin patterns
- Border radius, shadows, opacity values

## Interactive Elements
- Buttons, links, inputs, dropdowns
- Hover/active states if implied
- Navigation structure

## Content
- All visible text content (preserve exact wording)
- Image descriptions and placement
- Icon descriptions

## Technical Notes
- Anything that requires JavaScript (animations, interactions, state)
- Accessibility considerations
- Responsive breakpoint implications

Be EXTREMELY precise. This spec will be used to generate pixel-accurate code.
Any element you miss will be absent from the implementation."""

GENERATE_FROM_SPEC_TEMPLATE = """Implement the following UI spec as {framework_desc}.

=== UI SPECIFICATION ===
{spec}
=== END SPECIFICATION ===

REQUIREMENTS:
- Implement EVERY element described in the spec
- Match colors, typography, spacing, and layout as precisely as possible
- Use OKLCH colors, semantic HTML, and modern CSS patterns
- All content must be visible at initial paint (CSS-only, no JS-dependent visibility)
- Include all text content exactly as specified
- Use personality fonts (never Inter, Roboto, Arial, or system stacks)

{framework_instruction}"""

FRAMEWORK_CONFIGS = {
    "react": {
        "desc": "React + TypeScript + Tailwind CSS",
        "instruction": (
            "Generate as React TSX with Tailwind v4 classes. "
            "Include all imports. Assume Vite setup. "
            "For multi-component layouts, use file separators: // --- FILE: path ---"
        ),
    },
    "html": {
        "desc": "a single self-contained HTML file",
        "instruction": (
            "Generate as a single HTML file with inline <style> and minimal <script>. "
            "Use Google Fonts CDN for typography. Include all CSS inline."
        ),
    },
}


def cmd_analyze(client, image_path, output_dir):
    """Step 1: Analyze screenshot into a structured spec."""
    print("  Step 1: ANALYZE (describing screenshot...)")

    response = client.generate_with_image(
        ANALYZE_PROMPT,
        image_path,
        thinking="medium",
    )

    spec = client.extract_text(response)

    # Save spec
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    spec_path = output_dir / f"spec_{timestamp}.md"

    spec_path.write_text(
        f"# UI Spec: {Path(image_path).name}\n\n"
        f"Generated: {datetime.now().isoformat()}\n"
        f"Source: {image_path}\n\n---\n\n{spec}",
        encoding="utf-8",
    )

    print(f"  Spec saved: {spec_path}")
    return spec, str(spec_path)


def cmd_generate(client, spec, framework, output_dir, filename):
    """Step 2: Generate code from spec."""
    config = FRAMEWORK_CONFIGS[framework]

    prompt = GENERATE_FROM_SPEC_TEMPLATE.format(
        framework_desc=config["desc"],
        spec=spec,
        framework_instruction=config["instruction"],
    )

    print(f"  Step 2: GENERATE (implementing as {config['desc']}...)")

    response = client.generate(
        prompt,
        thinking="high",
        system_instruction=(
            "You are a world-class frontend engineer. Implement the UI spec precisely. "
            "Use OKLCH colors, personality fonts, Tailwind v4, semantic HTML. "
            "Return complete runnable code only."
        ),
    )

    saved = client.save_code(response, output_dir, filename)
    return saved


def main():
    parser = argparse.ArgumentParser(
        description="Convert screenshots to code via describe-first pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Screenshot image path (PNG, JPG, WebP)",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only run analysis step (output spec, skip generation)",
    )
    parser.add_argument(
        "--from-spec",
        help="Skip analysis; generate from an existing spec file",
    )
    parser.add_argument(
        "--framework",
        choices=["react", "html"],
        default="react",
        help="Output framework (default: react)",
    )
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--filename",
        default="screenshot_impl",
        help="Base filename for generated code (default: screenshot_impl)",
    )
    parser.add_argument("--api-key", help="API key (overrides GEMINI_API_KEY)")

    args = parser.parse_args()

    # Validate inputs
    if not args.from_spec and not args.image:
        parser.error("Either provide an image path or use --from-spec")

    image_path = None
    if args.image:
        image_path = Path(args.image).expanduser().resolve()
        if not image_path.exists():
            print(f"Error: Image not found: {image_path}", file=sys.stderr)
            sys.exit(1)

    client = GeminiForgeClient(api_key=args.api_key)

    print("=" * 60)
    print("  GEMINI FORGE — SCREENSHOT TO CODE")
    print("=" * 60)

    if args.from_spec:
        # Step 2 only: generate from existing spec
        spec_path = Path(args.from_spec).expanduser().resolve()
        if not spec_path.exists():
            print(f"Error: Spec not found: {spec_path}", file=sys.stderr)
            sys.exit(1)

        print(f"  Using spec: {spec_path.name}")
        spec = spec_path.read_text(encoding="utf-8")

        saved = cmd_generate(client, spec, args.framework, args.output, args.filename)

    elif args.analyze_only:
        # Step 1 only: analyze screenshot
        print(f"  Image: {image_path.name}")
        spec, spec_path = cmd_analyze(client, str(image_path), args.output)

        print()
        print("=" * 60)
        print("  ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"  Spec: {spec_path}")
        print()
        print("  Next: Review the spec, correct any misreadings, then run:")
        print(f"  python screenshot_to_code.py --from-spec {spec_path} --framework {args.framework}")
        return

    else:
        # Full pipeline: analyze then generate
        print(f"  Image: {image_path.name}")
        print(f"  Framework: {args.framework}")
        print()

        spec, spec_path = cmd_analyze(client, str(image_path), args.output)
        print()
        saved = cmd_generate(client, spec, args.framework, args.output, args.filename)

    print()
    print("=" * 60)
    print("  OUTPUT")
    print("=" * 60)
    for path in saved:
        print(f"  {path}")
    print()
    print("  Next: Read the output, then polish with minoan-frontend-design standards.")


if __name__ == "__main__":
    main()
