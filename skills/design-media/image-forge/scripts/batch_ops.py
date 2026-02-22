#!/usr/bin/env python3
"""Parallel batch image processing.

Wraps magick mogrify and subprocess parallelism for bulk operations.

Usage:
    python batch_ops.py *.jpg --op resize --width 800
    python batch_ops.py *.jpg --op resize --width 800 --height 600
    python batch_ops.py *.png --op format --to jpg --quality 85
    python batch_ops.py *.jpg --op thumbnail --width 200 --height 200
    python batch_ops.py *.jpg --op strip
    python batch_ops.py *.jpg --op auto_orient
    python batch_ops.py *.jpg --op watermark --overlay watermark.png --opacity 25
    python batch_ops.py *.jpg --op resize --width 800 --output resized/ --parallel 4
    python batch_ops.py *.jpg --op resize --width 800 --dry-run
"""

import argparse
import glob
import json
import os
import shlex
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed


def build_single_command(
    input_path: str,
    output_path: str,
    op: str,
    opts: dict,
) -> list[str]:
    """Build a magick command for a single file."""
    cmd = ["magick", input_path]

    if op == "resize":
        w = opts.get("width", "")
        h = opts.get("height", "")
        mode = opts.get("mode", "fit")
        geometry = f"{w}x{h}" if h else str(w)
        suffix = {"fit": "", "fill": "^", "exact": "!", "shrink": ">"}.get(mode, "")
        cmd += ["-resize", f"{geometry}{suffix}"]
        if mode == "fill" and w and h:
            cmd += ["-gravity", "center", "-extent", f"{w}x{h}"]

    elif op == "thumbnail":
        w = opts.get("width", 200)
        h = opts.get("height", 200)
        cmd += ["-thumbnail", f"{w}x{h}^", "-gravity", "center", "-extent", f"{w}x{h}"]

    elif op == "format":
        # Format conversion handled by output extension
        quality = opts.get("quality")
        if quality:
            cmd += ["-quality", str(quality)]

    elif op == "strip":
        cmd += ["-strip"]

    elif op == "auto_orient":
        cmd += ["-auto-orient"]

    elif op == "watermark":
        overlay = opts.get("overlay")
        if not overlay:
            raise ValueError("watermark requires --overlay")
        opacity = opts.get("opacity", 25)
        gravity = opts.get("gravity", "SouthEast")
        cmd += [
            "(", overlay, ")",
            "-gravity", gravity, "-geometry", "+10+10",
            "-compose", "Dissolve", "-define", f"compose:args={opacity}",
            "-composite",
        ]

    elif op == "crop":
        w = opts.get("width")
        h = opts.get("height")
        gravity = opts.get("gravity", "center")
        if not w or not h:
            raise ValueError("crop requires --width and --height")
        gravity_map = {
            "center": "Center", "north": "North", "south": "South",
            "east": "East", "west": "West",
            "northwest": "NorthWest", "northeast": "NorthEast",
            "southwest": "SouthWest", "southeast": "SouthEast",
        }
        g = gravity_map.get(gravity.lower(), gravity)
        cmd += ["-resize", f"{w}x{h}^", "-gravity", g,
                "-extent", f"{w}x{h}"]

    else:
        raise ValueError(f"Unknown operation: {op}")

    # Always strip by default for batch (saves space)
    if op not in ("strip",) and opts.get("strip", True):
        cmd += ["-strip"]

    cmd.append(output_path)
    return cmd


def process_file(args_tuple):
    """Process a single file (for parallel execution)."""
    input_path, output_path, op, opts = args_tuple
    try:
        cmd = build_single_command(input_path, output_path, op, opts)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"file": input_path, "status": "error", "error": result.stderr.strip()}
        return {"file": input_path, "output": output_path, "status": "ok"}
    except Exception as e:
        return {"file": input_path, "status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Parallel batch image processing")
    parser.add_argument("files", nargs="+", help="Input image files (supports globs)")
    parser.add_argument("--op", required=True,
                        choices=["resize", "thumbnail", "format", "strip",
                                 "auto_orient", "watermark", "crop"],
                        help="Operation to perform")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--quality", type=int, default=None)
    parser.add_argument("--to", default=None, help="Target format (e.g., jpg, png, webp)")
    parser.add_argument("--overlay", default=None, help="Overlay image for watermark")
    parser.add_argument("--opacity", type=int, default=25, help="Watermark opacity (0-100)")
    parser.add_argument("--gravity", default="center", help="Crop/watermark gravity")
    parser.add_argument("--mode", default="fit",
                        choices=["fit", "fill", "exact", "shrink"],
                        help="Resize mode")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--parallel", type=int, default=4,
                        help="Number of parallel workers (default: 4)")
    parser.add_argument("--no-strip", action="store_true",
                        help="Don't strip metadata")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing")
    args = parser.parse_args()

    # Expand globs
    files = []
    for pattern in args.files:
        expanded = glob.glob(pattern)
        if expanded:
            files.extend(expanded)
        elif os.path.isfile(pattern):
            files.append(pattern)

    if not files:
        print("No files matched", file=sys.stderr)
        sys.exit(1)

    # Deduplicate and sort
    files = sorted(set(files))

    # Setup output directory
    output_dir = args.output
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    opts = {
        "width": args.width,
        "height": args.height,
        "quality": args.quality,
        "overlay": args.overlay,
        "opacity": args.opacity,
        "gravity": args.gravity,
        "mode": args.mode,
        "strip": not args.no_strip,
    }

    # Build task list
    tasks = []
    for f in files:
        base = os.path.basename(f)
        name, ext = os.path.splitext(base)

        # Determine output extension
        if args.to:
            out_ext = f".{args.to.lstrip('.')}"
        else:
            out_ext = ext

        if output_dir:
            out_path = os.path.join(output_dir, f"{name}{out_ext}")
        else:
            out_path = os.path.join(os.path.dirname(f), f"{name}_processed{out_ext}")

        tasks.append((f, out_path, args.op, opts))

    if args.dry_run:
        for inp, out, op, o in tasks:
            cmd = build_single_command(inp, out, op, o)
            print(shlex.join(cmd))
        sys.exit(0)

    # Process
    results = []
    ok_count = 0
    err_count = 0

    with ProcessPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(process_file, t): t for t in tasks}
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            if result["status"] == "ok":
                ok_count += 1
            else:
                err_count += 1
            # Progress
            print(f"\r[{i}/{len(tasks)}] {result['status']}: {os.path.basename(result['file'])}",
                  end="", flush=True)

    print()  # newline after progress

    print(json.dumps({
        "total": len(tasks),
        "ok": ok_count,
        "errors": err_count,
        "operation": args.op,
        "results": [r for r in results if r["status"] == "error"] if err_count else [],
    }, indent=2))


if __name__ == "__main__":
    main()
