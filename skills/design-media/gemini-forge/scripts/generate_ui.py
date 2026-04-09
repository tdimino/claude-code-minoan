#!/usr/bin/env python3
"""
Generate UI: React/HTML/CSS code generation with Gemini 3.1 Pro.

Generates frontend code from natural language task descriptions.
Injects condensed minoan-frontend-design directives as a system prompt
for design-aware output.

Usage:
    # Simple component
    python generate_ui.py "dark dashboard with real-time metrics" --mode react

    # Full multi-file app
    python generate_ui.py "SaaS pricing page" --mode react --thinking high --app

    # With design system context
    python generate_ui.py "hero section" --design-context context.txt --thinking high

    # Plain HTML
    python generate_ui.py "minimal landing page" --mode html --thinking low

Environment:
    GEMINI_API_KEY - Required for Gemini API access
"""

import argparse
import sys
from pathlib import Path

# Add scripts dir to path for sibling import
sys.path.insert(0, str(Path(__file__).parent))
from gemini_text import GeminiForgeClient


# Condensed from minoan-frontend-design + syncretic-v3
SYSTEM_PROMPT = """You are a world-class frontend engineer and designer. Generate complete, immediately runnable code.

CREATIVE DIRECTION:
- Before writing code, name the single element that makes this design impossible to forget—a typeface, a structural break, a color commitment, a motion behavior. Every choice reinforces that one thing.
- Typography carries the voice. Choose fonts with real personality—never Inter, Roboto, Arial, or system stacks. Pair a display face that provokes with a body face that soothes.
- Color takes a position. Bold and saturated, moody and restrained, or high-contrast and minimal—never timid. Lead with a dominant color, punctuate with sharp accents.
- Unexpected layouts. Asymmetry. Overlap and z-depth. Grid-breaking elements. Dramatic scale jumps. Generous negative space or controlled density—never the uncommitted middle.
- Create depth: gradient meshes, noise and grain, geometric patterns, layered transparencies, dramatic shadows. The background is a canvas, not a wall.

ENGINEERING STANDARDS:
- OKLCH colors throughout via CSS oklch(). Semantic 10-step scales for theming.
- Tailwind v4 with @theme for design tokens as CSS custom properties.
- Semantic HTML first. ARIA only when native elements are insufficient.
- :focus-visible over :focus. Minimum hit targets: 24px desktop / 44px mobile.
- CSS-first animations. Respect prefers-reduced-motion. Avoid transition: all.
- All content visible at t=0 with CSS only. JS adds delight, not visibility.

ANTI-PATTERNS TO AVOID:
- Overused fonts (Inter, Roboto, Arial, Space Grotesk, system stacks)
- Cliched color schemes (purple gradients on white, neon outer glows)
- Predictable symmetric layouts, generic three-equal-cards rows
- Cookie-cutter component patterns, placeholder content (John Doe, 99.99%)

OUTPUT FORMAT:
- Return complete, runnable code only. No explanations unless the prompt asks for them.
- Multi-file apps: use clear separator comments: // --- FILE: path/to/file ---
- Include all imports. Assume standard React/Vite setup with Tailwind.
- Front-load hero content. If output is truncated, the hero and core styles must survive."""

APP_MODE_ADDENDUM = """
MULTI-FILE APPLICATION MODE:
Generate a complete multi-file application. Use separator markers for each file:
// --- FILE: src/App.tsx ---
// --- FILE: src/components/Header.tsx ---
// --- FILE: src/index.css ---
// --- FILE: index.html ---

Include all files needed for a working application. Assume Vite + React + Tailwind setup."""


def main():
    parser = argparse.ArgumentParser(
        description="Generate frontend code with Gemini 3.1 Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("prompt", help="Task description for UI generation")
    parser.add_argument(
        "--mode",
        choices=["react", "html"],
        default="react",
        help="Output framework (default: react)",
    )
    parser.add_argument(
        "--thinking",
        choices=["low", "medium", "high"],
        default="medium",
        help="Thinking level (default: medium)",
    )
    parser.add_argument(
        "--design-context",
        help="Path to design system context file (from load_design_system.py)",
    )
    parser.add_argument(
        "--app",
        action="store_true",
        help="Multi-file application mode (uses high thinking, multi-file output)",
    )
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--filename",
        default="generated",
        help="Base filename for output (default: generated)",
    )
    parser.add_argument("--api-key", help="API key (overrides GEMINI_API_KEY)")

    args = parser.parse_args()

    client = GeminiForgeClient(api_key=args.api_key)

    # Build system prompt
    system = SYSTEM_PROMPT
    if args.app:
        system += "\n\n" + APP_MODE_ADDENDUM
        if args.thinking != "high":
            print(f"  (app mode: overriding --thinking {args.thinking} → high)")
        args.thinking = "high"

    # Build user prompt
    mode_instruction = {
        "react": "Generate as React + TypeScript + Tailwind CSS.",
        "html": "Generate as a single self-contained HTML file with inline CSS and minimal JS.",
    }

    parts = [f"{args.prompt}\n\n{mode_instruction[args.mode]}"]

    # Load design system context if provided
    if args.design_context:
        ctx_path = Path(args.design_context).expanduser().resolve()
        if ctx_path.exists():
            context = ctx_path.read_text(encoding="utf-8")
            parts.insert(0, f"DESIGN SYSTEM CONTEXT:\n\n{context}\n\n---\n\nTASK:")
            print(f"  Loaded design context: {ctx_path.name} ({len(context):,} chars)")
        else:
            print(f"  Warning: Design context not found: {ctx_path}", file=sys.stderr)

    prompt = "\n".join(parts)

    print("=" * 60)
    print("  GEMINI FORGE — UI GENERATION")
    print("=" * 60)
    print(f"  Mode: {args.mode}")
    print(f"  Thinking: {args.thinking}")
    print(f"  App mode: {args.app}")
    print(f"  Prompt: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
    print()
    print("  Generating...")

    response = client.generate(
        prompt,
        thinking=args.thinking,
        system_instruction=system,
    )

    saved = client.save_code(response, args.output, args.filename)

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
