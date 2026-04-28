#!/usr/bin/env python3
"""
Badge Forge — Transform images into web-ready transparent PNG badges.

Removes background via corner-flood transparency, trims, resizes, and
centers the subject on a transparent canvas. Forces PNG32 (8-bit RGBA)
output for smooth alpha edges.

Requires: ImageMagick 7+ (`magick` command)

Usage:
    python badge_forge.py source.jpg -o output.png
    python badge_forge.py source.jpg --preset icon
    python badge_forge.py *.jpg --batch -o ./badges/
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

PRESETS = {
    "badge":  {"size": 200, "padding": 18, "fuzz": 18},
    "icon":   {"size": 64,  "padding": 8,  "fuzz": 18},
    "avatar": {"size": 128, "padding": 12, "fuzz": 15},
    "logo":   {"size": 300, "padding": 24, "fuzz": 20},
    "hero":   {"size": 512, "padding": 32, "fuzz": 15},
}


def get_image_dimensions(magick: str, source: Path) -> Tuple[int, int]:
    result = subprocess.run(
        [magick, "identify", "-format", "%w %h", str(source)],
        capture_output=True, text=True, check=True
    )
    w, h = result.stdout.strip().split()
    return int(w), int(h)


def get_corner_coords(width: int, height: int, corners: str) -> List[Tuple[int, int]]:
    all_corners = {
        "tl": (0, 0),
        "tr": (width - 1, 0),
        "bl": (0, height - 1),
        "br": (width - 1, height - 1),
    }
    if corners == "all":
        return list(all_corners.values())
    elif corners == "top":
        return [all_corners["tl"], all_corners["tr"]]
    elif corners == "bottom":
        return [all_corners["bl"], all_corners["br"]]
    else:
        selected = [c.strip() for c in corners.split(",")]
        return [all_corners[c] for c in selected if c in all_corners]


def forge_badge(
    source: Path,
    output: Path,
    magick: str,
    size: int = 200,
    padding: int = 18,
    fuzz: float = 18.0,
    corners: str = "all",
    feather: float = 0.0,
    dry_run: bool = False,
) -> Path:
    width, height = get_image_dimensions(magick, source)
    inner_size = size - (2 * padding)
    corner_coords = get_corner_coords(width, height, corners)

    cmd = [magick, str(source)]

    for x, y in corner_coords:
        cmd.extend([
            "-fuzz", f"{fuzz}%",
            "-fill", "none",
            "-draw", f"alpha {x},{y} floodfill"
        ])

    if feather > 0:
        cmd.extend([
            "(", "+clone", "-alpha", "extract",
            "-blur", f"0x{feather}",
            "-level", "50%,100%",
            ")", "-compose", "CopyOpacity", "-composite"
        ])

    cmd.extend([
        "-trim", "+repage",
        "-resize", f"{inner_size}x{inner_size}",
        "-gravity", "center",
        "-extent", f"{size}x{size}",
        f"PNG32:{output}"
    ])

    if dry_run:
        print(" ".join(cmd))
        return output

    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ImageMagick failed: {result.stderr}")

    # Verify alpha depth
    verify = subprocess.run(
        [magick, "identify", "-verbose", str(output)],
        capture_output=True, text=True
    )
    if "Alpha: 1-bit" in verify.stdout:
        print(
            f"  ⚠ {output.name} has 1-bit alpha. Try --fuzz {int(fuzz) + 5} "
            f"or --feather 0.5 for softer edges.",
            file=sys.stderr
        )

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Badge Forge — Transform images into transparent PNG badges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Presets:
  badge   200px canvas, 18px padding, 18%% fuzz (default)
  icon     64px canvas,  8px padding, 18%% fuzz
  avatar  128px canvas, 12px padding, 15%% fuzz
  logo    300px canvas, 24px padding, 20%% fuzz
  hero    512px canvas, 32px padding, 15%% fuzz

Examples:
  python badge_forge.py source.jpg
  python badge_forge.py source.jpg --preset icon -o icon.png
  python badge_forge.py *.jpg --batch -o ./badges/
  python badge_forge.py source.jpg --fuzz 25 --corners top
        """
    )

    parser.add_argument("sources", nargs="+", help="Source image(s)")
    parser.add_argument("-o", "--output", help="Output path (file or directory with --batch)")
    parser.add_argument("--batch", action="store_true", help="Batch mode: output is a directory")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), default="badge",
                       help="Size preset (default: badge)")
    parser.add_argument("--size", type=int, help="Override canvas size in pixels")
    parser.add_argument("--padding", type=int, help="Override padding in pixels")
    parser.add_argument("--fuzz", type=float, help="Override fuzz tolerance %%")
    parser.add_argument("--corners", default="all",
                       help="Corners to flood: all|top|bottom|tl,tr,bl,br (default: all)")
    parser.add_argument("--feather", type=float, default=0.0,
                       help="Alpha edge feathering radius in pixels (default: 0)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print ImageMagick command without executing")

    args = parser.parse_args()

    magick = shutil.which("magick")
    if not magick:
        print("Error: ImageMagick 7+ not found. Install via: brew install imagemagick",
              file=sys.stderr)
        sys.exit(1)

    preset = PRESETS[args.preset]
    size = args.size or preset["size"]
    padding = args.padding if args.padding is not None else preset["padding"]
    fuzz = args.fuzz if args.fuzz is not None else preset["fuzz"]

    sources = [Path(s) for s in args.sources]

    print(f"🔨 Badge Forge — {args.preset} preset ({size}px, {fuzz}% fuzz)")

    if args.batch or len(sources) > 1:
        output_dir = Path(args.output) if args.output else Path("./badges")
        for source in sources:
            if not source.exists():
                print(f"  ⚠ Skipping {source} (not found)")
                continue
            out = output_dir / f"{source.stem}_badge.png"
            try:
                forge_badge(source, out, magick, size, padding, fuzz,
                           args.corners, args.feather, args.dry_run)
                print(f"  ✓ {source.name} → {out}")
            except RuntimeError as e:
                print(f"  ✗ {source.name}: {e}", file=sys.stderr)
    else:
        source = sources[0]
        if not source.exists():
            print(f"Error: {source} not found", file=sys.stderr)
            sys.exit(1)

        if args.output:
            output = Path(args.output)
        else:
            output = source.parent / f"{source.stem}_badge.png"

        try:
            result = forge_badge(source, output, magick, size, padding, fuzz,
                                args.corners, args.feather, args.dry_run)
            print(f"  ✓ {result}")
        except RuntimeError as e:
            print(f"  ✗ {e}", file=sys.stderr)
            sys.exit(1)

    print("\n✅ Done")


if __name__ == "__main__":
    main()
