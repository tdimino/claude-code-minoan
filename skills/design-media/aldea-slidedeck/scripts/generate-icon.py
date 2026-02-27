#!/usr/bin/env python3
"""
Generate blueprint-styled SVG icons for Aldea slide decks.

This script creates custom SVG icons matching Aldea's blueprint aesthetic
using either the SVGMaker API (if available) or a local fallback generator.

Usage:
    python3 generate-icon.py "neural network" --output icon.svg
    python3 generate-icon.py "audio waveform" --style minimal
    python3 generate-icon.py "brain" --size 48 --output brain.svg
"""

import argparse
import subprocess
import sys
import os
import re
from pathlib import Path

# Blueprint color palette
COLORS = {
    "cyan": "#00d4ff",
    "dark": "#0a0f1a",
    "grid": "#1e3a5f",
    "accent": "#60a5fa",
    "muted": "#6b7a8c",
}


def check_dependencies() -> dict[str, bool]:
    """Check which tools are available."""
    deps = {}

    # Check for ImageMagick
    try:
        subprocess.run(["magick", "--version"], capture_output=True, check=True)
        deps["imagemagick"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        deps["imagemagick"] = False

    # Check for Potrace
    try:
        subprocess.run(["potrace", "--version"], capture_output=True, check=True)
        deps["potrace"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        deps["potrace"] = False

    # Check for SVGO
    try:
        subprocess.run(["svgo", "--version"], capture_output=True, check=True)
        deps["svgo"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        deps["svgo"] = False

    return deps


def generate_simple_svg(subject: str, size: int = 24, style: str = "geometric") -> str:
    """
    Generate a simple placeholder SVG icon.

    This is a fallback when external APIs are not available.
    Creates a basic geometric representation based on keywords.
    """
    half = size // 2

    # Common icon patterns based on subject keywords
    patterns = {
        "network": f'''<circle cx="{half}" cy="{half}" r="{size//4}" fill="none" stroke="{COLORS['cyan']}" stroke-width="1.5"/>
    <circle cx="{size//4}" cy="{size//4}" r="2" fill="{COLORS['cyan']}"/>
    <circle cx="{3*size//4}" cy="{size//4}" r="2" fill="{COLORS['cyan']}"/>
    <circle cx="{half}" cy="{3*size//4}" r="2" fill="{COLORS['cyan']}"/>
    <line x1="{size//4}" y1="{size//4}" x2="{half}" y2="{half}" stroke="{COLORS['cyan']}" stroke-width="1"/>
    <line x1="{3*size//4}" y1="{size//4}" x2="{half}" y2="{half}" stroke="{COLORS['cyan']}" stroke-width="1"/>
    <line x1="{half}" y1="{3*size//4}" x2="{half}" y2="{half}" stroke="{COLORS['cyan']}" stroke-width="1"/>''',

        "brain": f'''<ellipse cx="{half}" cy="{half}" rx="{size//3}" ry="{size//2.5}" fill="none" stroke="{COLORS['cyan']}" stroke-width="1.5"/>
    <path d="M{half} {size//4} Q{size//3} {half} {half} {3*size//4}" fill="none" stroke="{COLORS['cyan']}" stroke-width="1"/>
    <path d="M{size//3} {size//3} Q{half} {size//2.5} {2*size//3} {size//3}" fill="none" stroke="{COLORS['cyan']}" stroke-width="1"/>''',

        "wave": f'''<path d="M{size//8} {half} Q{size//4} {size//4} {size//2} {half} T{7*size//8} {half}" fill="none" stroke="{COLORS['cyan']}" stroke-width="1.5" stroke-linecap="round"/>''',

        "audio": f'''<rect x="{size//6}" y="{size//3}" width="2" height="{size//3}" rx="1" fill="{COLORS['cyan']}"/>
    <rect x="{size//3}" y="{size//4}" width="2" height="{size//2}" rx="1" fill="{COLORS['cyan']}"/>
    <rect x="{half}" y="{size//6}" width="2" height="{2*size//3}" rx="1" fill="{COLORS['cyan']}"/>
    <rect x="{2*size//3}" y="{size//4}" width="2" height="{size//2}" rx="1" fill="{COLORS['cyan']}"/>
    <rect x="{5*size//6}" y="{size//3}" width="2" height="{size//3}" rx="1" fill="{COLORS['cyan']}"/>''',

        "chart": f'''<polyline points="{size//6},{3*size//4} {size//3},{half} {half},{2*size//3} {2*size//3},{size//4} {5*size//6},{size//3}" fill="none" stroke="{COLORS['cyan']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    <line x1="{size//8}" y1="{7*size//8}" x2="{7*size//8}" y2="{7*size//8}" stroke="{COLORS['muted']}" stroke-width="1"/>
    <line x1="{size//8}" y1="{size//8}" x2="{size//8}" y2="{7*size//8}" stroke="{COLORS['muted']}" stroke-width="1"/>''',

        "node": f'''<circle cx="{half}" cy="{half}" r="{size//3}" fill="none" stroke="{COLORS['cyan']}" stroke-width="1.5"/>
    <circle cx="{half}" cy="{half}" r="{size//6}" fill="{COLORS['cyan']}" fill-opacity="0.3"/>''',

        "flow": f'''<rect x="{size//8}" y="{size//3}" width="{size//4}" height="{size//3}" rx="2" fill="none" stroke="{COLORS['cyan']}" stroke-width="1.5"/>
    <line x1="{3*size//8}" y1="{half}" x2="{5*size//8}" y2="{half}" stroke="{COLORS['cyan']}" stroke-width="1.5" marker-end="url(#arrow)"/>
    <rect x="{5*size//8}" y="{size//3}" width="{size//4}" height="{size//3}" rx="2" fill="none" stroke="{COLORS['cyan']}" stroke-width="1.5"/>''',

        "default": f'''<rect x="{size//4}" y="{size//4}" width="{half}" height="{half}" rx="3" fill="none" stroke="{COLORS['cyan']}" stroke-width="1.5"/>
    <circle cx="{half}" cy="{half}" r="{size//8}" fill="{COLORS['cyan']}" fill-opacity="0.4"/>'''
    }

    # Match subject to pattern
    subject_lower = subject.lower()
    icon_content = patterns["default"]

    for key, content in patterns.items():
        if key in subject_lower:
            icon_content = content
            break

    # Generate SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}" fill="none">
  <defs>
    <marker id="arrow" markerWidth="4" markerHeight="4" refX="3" refY="2" orient="auto">
      <path d="M0,0 L4,2 L0,4 Z" fill="{COLORS['cyan']}"/>
    </marker>
  </defs>
  {icon_content}
</svg>'''

    return svg


def apply_blueprint_colors(svg_content: str) -> str:
    """Apply blueprint color palette to SVG content."""
    replacements = [
        (r'#000000', COLORS['dark']),
        (r'#ffffff', COLORS['cyan']),
        (r'#808080', COLORS['grid']),
        (r'black', COLORS['dark']),
        (r'white', COLORS['cyan']),
    ]

    result = svg_content
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def optimize_svg(input_path: Path, output_path: Path) -> bool:
    """Optimize SVG using SVGO if available."""
    try:
        subprocess.run(
            ["svgo", str(input_path), "-o", str(output_path)],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If SVGO fails, just copy the file
        output_path.write_text(input_path.read_text())
        return False


def vectorize_image(input_path: Path, output_path: Path) -> bool:
    """
    Convert a raster image to SVG using ImageMagick and Potrace.

    This is the full pipeline for converting AI-generated images to clean SVGs.
    """
    deps = check_dependencies()

    if not deps.get("imagemagick") or not deps.get("potrace"):
        print("Error: ImageMagick and Potrace are required for image vectorization")
        print("Install with: brew install imagemagick potrace")
        return False

    temp_dir = Path("/tmp/aldea-icon-gen")
    temp_dir.mkdir(exist_ok=True)

    try:
        # Step 1: Posterize and prepare image
        processed = temp_dir / "processed.png"
        subprocess.run([
            "magick", str(input_path),
            "-posterize", "4",
            "-colors", "4",
            "-resize", "512x512",
            str(processed)
        ], check=True)

        # Step 2: Create bitmap for potrace
        pbm_file = temp_dir / "input.pbm"
        subprocess.run([
            "magick", str(processed),
            "-threshold", "50%",
            str(pbm_file)
        ], check=True)

        # Step 3: Trace to SVG
        svg_file = temp_dir / "traced.svg"
        subprocess.run([
            "potrace", str(pbm_file),
            "-s", "-o", str(svg_file)
        ], check=True)

        # Step 4: Apply blueprint colors
        svg_content = svg_file.read_text()
        svg_content = apply_blueprint_colors(svg_content)

        # Step 5: Write and optionally optimize
        temp_output = temp_dir / "output.svg"
        temp_output.write_text(svg_content)

        if deps.get("svgo"):
            optimize_svg(temp_output, output_path)
        else:
            output_path.write_text(svg_content)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during vectorization: {e}")
        return False
    finally:
        # Cleanup temp files
        for f in temp_dir.glob("*"):
            f.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Generate blueprint-styled SVG icons for Aldea slide decks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "neural network"                    Generate network icon
  %(prog)s "audio waveform" --output wave.svg  Custom output path
  %(prog)s --from-image input.png -o icon.svg  Vectorize existing image
  %(prog)s "brain" --size 48                   Larger icon size

Icon Subjects (keywords for local generation):
  network, brain, wave, audio, chart, node, flow

For higher quality icons, use with Nano Banana Pro:
  1. Generate image: nano-banana-pro "minimalist icon of [subject], flat design,
     3 solid colors, cyan #00d4ff on dark #0a0f1a, geometric"
  2. Vectorize: %(prog)s --from-image output.png -o icon.svg
        """
    )

    parser.add_argument(
        "subject",
        nargs="?",
        help="Subject/description for the icon (e.g., 'neural network', 'audio wave')"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("icon.svg"),
        help="Output SVG file path (default: icon.svg)"
    )

    parser.add_argument(
        "--size",
        type=int,
        default=24,
        choices=[16, 24, 32, 48, 64],
        help="Icon size in pixels (default: 24)"
    )

    parser.add_argument(
        "--style",
        choices=["geometric", "minimal", "detailed"],
        default="geometric",
        help="Icon style (default: geometric)"
    )

    parser.add_argument(
        "--from-image",
        type=Path,
        help="Vectorize an existing raster image instead of generating"
    )

    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check available dependencies and exit"
    )

    parser.add_argument(
        "--list-colors",
        action="store_true",
        help="List blueprint color palette and exit"
    )

    args = parser.parse_args()

    # Handle info commands
    if args.check_deps:
        deps = check_dependencies()
        print("Available dependencies:")
        for name, available in deps.items():
            status = "OK" if available else "MISSING"
            print(f"  {name}: {status}")

        print("\nFor full functionality, install missing tools:")
        if not deps.get("imagemagick"):
            print("  brew install imagemagick")
        if not deps.get("potrace"):
            print("  brew install potrace")
        if not deps.get("svgo"):
            print("  npm install -g svgo")

        sys.exit(0)

    if args.list_colors:
        print("Blueprint Color Palette:")
        for name, color in COLORS.items():
            print(f"  {name:8} {color}")
        sys.exit(0)

    # Handle image vectorization
    if args.from_image:
        if not args.from_image.exists():
            print(f"Error: Input image not found: {args.from_image}")
            sys.exit(1)

        print(f"Vectorizing {args.from_image}...")
        if vectorize_image(args.from_image, args.output):
            print(f"Success! Output: {args.output}")
        else:
            sys.exit(1)
        sys.exit(0)

    # Generate icon from subject
    if not args.subject:
        parser.print_help()
        sys.exit(1)

    print(f"Generating '{args.subject}' icon ({args.size}px, {args.style} style)...")

    svg_content = generate_simple_svg(args.subject, args.size, args.style)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg_content)

    # Try to optimize if SVGO is available
    deps = check_dependencies()
    if deps.get("svgo"):
        temp_path = args.output.with_suffix(".temp.svg")
        args.output.rename(temp_path)
        if optimize_svg(temp_path, args.output):
            temp_path.unlink()
            print("Optimized with SVGO")
        else:
            temp_path.rename(args.output)

    print(f"Success! Output: {args.output}")
    print(f"\nTo use in slides:")
    print(f'  <img src="/images/custom-icons/{args.output.name}" className="w-8 h-8" />')


if __name__ == "__main__":
    main()
