#!/usr/bin/env python3
"""
Generate SVG: Animated SVG generation with Gemini 3.1 Pro's physics reasoning.

Modes:
    animate  - Add animations to an existing SVG
    create   - Generate an animated SVG from description
    physics  - Physics-simulation SVGs (particles, springs, fluid)
    logo     - Animated logo/icon generation

Output is pure SVG with no external dependencies. Includes prefers-reduced-motion
fallbacks for accessibility.

Usage:
    # Animate existing SVG
    python generate_svg.py --mode animate logo.svg --description "draw-on stroke, 1.2s"

    # Create animated SVG
    python generate_svg.py --mode create --description "orbiting dots with spring connections"

    # Physics simulation
    python generate_svg.py --mode physics --description "particle system, 20 nodes"

    # Animated logo
    python generate_svg.py --mode logo --description "double-axe labrys, slow rotation"

Environment:
    GEMINI_API_KEY - Required for Gemini API access
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gemini_text import GeminiForgeClient


SVG_SYSTEM_PROMPT = """You are an expert SVG animator and generative artist. Generate pure SVG code.

REQUIREMENTS:
- Output ONLY valid SVG markup. No HTML wrapper unless explicitly asked.
- Use SMIL animations (<animate>, <animateTransform>, <animateMotion>) for path-based motion.
- Use CSS animations via <style> for opacity, color, and transform effects.
- CSS custom properties for parameterized timings and colors.
- Include a prefers-reduced-motion media query that disables non-essential animations.
- No external dependencies—everything self-contained in the SVG.
- Use viewBox for responsive scaling.
- Optimize: minimize redundant groups, use <defs> for reusable elements.

ANIMATION PRINCIPLES:
- Easing: use cubic-bezier or named easings, never linear for organic motion.
- Stagger: offset animation delays for cascading effects.
- Physics: when simulating physics, use realistic spring constants and damping.
- Loops: use repeatCount="indefinite" sparingly—finite loops with intentional endings feel more crafted.

OUTPUT FORMAT:
Return the complete SVG element starting with <svg and ending with </svg>.
No markdown fences, no explanation, just the SVG."""

MODE_PROMPTS = {
    "animate": (
        "Add animation to this existing SVG. Preserve all original elements and structure.\n\n"
        "EXISTING SVG:\n{svg_content}\n\n"
        "ANIMATION: {description}\n\n"
        "Add animations while keeping all original paths, shapes, and attributes intact."
    ),
    "create": (
        "Create an animated SVG from this description:\n\n"
        "{description}\n\n"
        "Generate a complete, self-contained animated SVG. "
        "Use rich colors, thoughtful composition, and smooth animations."
    ),
    "physics": (
        "Create a physics-simulation SVG:\n\n"
        "{description}\n\n"
        "Simulate realistic physics using SVG animations. Consider: "
        "gravity, spring tension, damping, collision boundaries, velocity inheritance. "
        "Use JavaScript within <script> tags ONLY if SMIL cannot achieve the simulation. "
        "Prefer SMIL/CSS for simple physics; use JS for complex particle systems."
    ),
    "logo": (
        "Create an animated logo/icon SVG:\n\n"
        "{description}\n\n"
        "Design a distinctive logo with an entrance animation. The logo should: "
        "1. Be recognizable as a static image (animation adds delight, not meaning) "
        "2. Use a sophisticated entrance animation (draw-on, morph, reveal, assemble) "
        "3. Settle into a subtle idle state or stop cleanly "
        "4. Work at sizes from 32px to 512px (use viewBox)"
    ),
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate animated SVGs with Gemini 3.1 Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["animate", "create", "physics", "logo"],
        required=True,
        help="Generation mode",
    )
    parser.add_argument(
        "svg_file",
        nargs="?",
        help="Existing SVG file (required for animate mode)",
    )
    parser.add_argument(
        "--description", "-d",
        required=True,
        help="Description of the animation or SVG to generate",
    )
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--filename",
        help="Output filename (default: auto-generated from mode)",
    )
    parser.add_argument(
        "--thinking",
        choices=["low", "medium", "high"],
        default="high",
        help="Thinking level (default: high — SVG benefits from deep reasoning)",
    )
    parser.add_argument("--api-key", help="API key (overrides GEMINI_API_KEY)")

    args = parser.parse_args()

    # Validate animate mode requires SVG file
    if args.mode == "animate" and not args.svg_file:
        parser.error("animate mode requires an SVG file argument")

    client = GeminiForgeClient(api_key=args.api_key)

    # Build prompt
    template = MODE_PROMPTS[args.mode]
    svg_content = ""

    if args.mode == "animate":
        svg_path = Path(args.svg_file).expanduser().resolve()
        if not svg_path.exists():
            print(f"Error: SVG not found: {svg_path}", file=sys.stderr)
            sys.exit(1)
        svg_content = svg_path.read_text(encoding="utf-8")

    prompt = template.format(
        description=args.description,
        svg_content=svg_content,
    )

    print("=" * 60)
    print("  GEMINI FORGE — SVG ANIMATION")
    print("=" * 60)
    print(f"  Mode: {args.mode}")
    print(f"  Thinking: {args.thinking}")
    print(f"  Description: {args.description[:80]}{'...' if len(args.description) > 80 else ''}")
    if args.mode == "animate":
        print(f"  Source SVG: {svg_path.name}")
    print()
    print("  Generating...")

    response = client.generate(
        prompt,
        thinking=args.thinking,
        system_instruction=SVG_SYSTEM_PROMPT,
    )

    # Extract and save SVG
    text = client.extract_text(response)

    # Strip markdown fences using shared utility
    from gemini_text import _strip_code_fences
    text = _strip_code_fences(text)

    # Extract SVG element if embedded in other text
    if not text.lstrip().startswith("<svg") and "<svg" in text and "</svg>" in text:
        start = text.index("<svg")
        end = text.rindex("</svg>") + len("</svg>")
        text = text[start:end]

    # Warn if output doesn't look like SVG
    if not text.lstrip().startswith("<svg"):
        print("  Warning: Output does not appear to be valid SVG.", file=sys.stderr)
        print(f"  First 200 chars: {text[:200]}", file=sys.stderr)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = args.filename or f"{args.mode}_svg"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"{filename}_{timestamp}.svg"
    out_path.write_text(text, encoding="utf-8")

    print()
    print("=" * 60)
    print(f"  Output: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
