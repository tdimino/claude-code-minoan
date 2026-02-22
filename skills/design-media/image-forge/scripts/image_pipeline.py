#!/usr/bin/env python3
"""Build and execute ImageMagick pipelines from JSON specs.

The core innovation of image-forge: Claude writes a declarative JSON spec,
this script builds a single chained `magick` command. No intermediate files,
no fragile shell pipelines.

Usage:
    python image_pipeline.py <spec.json>
    python image_pipeline.py <spec.json> --dry-run
    echo '{"input":"in.jpg","output":"out.jpg","steps":[{"op":"resize","width":800}]}' | python image_pipeline.py -

Spec format:
{
    "input": "photo.jpg",
    "output": "result.png",
    "steps": [
        {"op": "resize", "width": 800, "height": 600},
        {"op": "crop", "w": 600, "h": 400, "gravity": "center"},
        {"op": "brightness_contrast", "brightness": 10, "contrast": 20},
        {"op": "annotate", "text": "Title", "gravity": "South", "pointsize": 36, "fill": "white"},
        {"op": "composite", "overlay": "watermark.png", "gravity": "SouthEast", "opacity": 30},
        {"op": "quality", "value": 85},
        {"op": "strip"}
    ]
}
"""

import argparse
import json
import os
import shlex
import subprocess
import sys


def build_resize(step: dict) -> list[str]:
    """Build resize arguments."""
    w = step.get("width", "")
    h = step.get("height", "")
    mode = step.get("mode", "fit")  # fit, fill, exact, shrink, enlarge, percent

    if not w and not h:
        raise ValueError("resize requires width and/or height")
    if mode == "fill" and not (w and h):
        raise ValueError("resize mode='fill' requires both width and height")

    geometry = f"{w}x{h}" if h else f"{w}"

    suffix = {
        "fit": "",
        "fill": "^",
        "exact": "!",
        "shrink": ">",
        "enlarge": "<",
        "percent": "%",
    }.get(mode, "")

    args = ["-resize", f"{geometry}{suffix}"]

    # Fill mode: also center-crop to exact size
    if mode == "fill" and w and h:
        args += ["-gravity", "center", "-extent", f"{w}x{h}"]

    filt = step.get("filter")
    if filt:
        args = ["-filter", filt] + args

    return args


def build_crop(step: dict) -> list[str]:
    """Build crop arguments."""
    w = step.get("w") or step.get("width")
    h = step.get("h") or step.get("height")
    x = step.get("x", 0)
    y = step.get("y", 0)
    gravity = step.get("gravity")

    if not w or not h:
        raise ValueError("crop requires w and h (or width and height)")

    args = []
    if gravity:
        args += ["-gravity", gravity]
        args += ["-crop", f"{w}x{h}+{x}+{y}", "+repage"]
    else:
        args += ["-crop", f"{w}x{h}+{x}+{y}", "+repage"]

    return args


def build_annotate(step: dict) -> list[str]:
    """Build text annotation arguments."""
    text = step.get("text", "")
    if not text:
        raise ValueError("annotate requires text")

    args = []

    font = step.get("font")
    if font:
        args += ["-font", font]

    pointsize = step.get("pointsize", 36)
    args += ["-pointsize", str(pointsize)]

    fill = step.get("fill", "white")
    args += ["-fill", fill]

    stroke = step.get("stroke")
    strokewidth = step.get("strokewidth")

    gravity = step.get("gravity")
    if gravity:
        args += ["-gravity", gravity]

    x = step.get("x", 0)
    y = step.get("y", 0)

    # Outlined text: draw stroke first, then fill
    if stroke:
        strokewidth = strokewidth or 2
        args += [
            "-stroke", stroke, "-strokewidth", str(strokewidth),
            "-fill", "none", "-annotate", f"+{x}+{y}", text,
            "-stroke", "none", "-fill", fill, "-annotate", f"+{x}+{y}", text,
        ]
    else:
        args += ["-annotate", f"+{x}+{y}", text]

    return args


def build_composite(step: dict) -> list[str]:
    """Build compositing arguments."""
    overlay = step.get("overlay")
    if not overlay:
        raise ValueError("composite requires overlay path")

    args = ["(", overlay]

    resize = step.get("resize")
    if resize:
        args += ["-resize", resize]

    args += [")"]

    gravity = step.get("gravity")
    if gravity:
        args += ["-gravity", gravity]

    x = step.get("x", 0)
    y = step.get("y", 0)
    args += ["-geometry", f"+{x}+{y}"]

    opacity = step.get("opacity")
    compose = step.get("compose", "Over")

    if opacity is not None and opacity < 100:
        args += ["-compose", "Dissolve", "-define", f"compose:args={opacity}"]
    else:
        args += ["-compose", compose]

    args += ["-composite"]
    return args


def build_command(spec: dict) -> list[str]:
    """Build the full magick command from a spec."""
    input_path = spec.get("input")
    output_path = spec.get("output")
    steps = spec.get("steps", [])

    if not input_path:
        raise ValueError("Spec requires 'input' path")
    if not output_path:
        raise ValueError("Spec requires 'output' path")

    cmd = ["magick", input_path]

    for step in steps:
        op = step.get("op")
        if not op:
            raise ValueError(f"Step missing 'op': {step}")

        if op == "resize":
            cmd += build_resize(step)

        elif op == "crop":
            cmd += build_crop(step)

        elif op == "trim":
            fuzz = step.get("fuzz")
            if fuzz:
                cmd += ["-fuzz", f"{fuzz}%"]
            cmd += ["-trim", "+repage"]

        elif op == "annotate":
            cmd += build_annotate(step)

        elif op == "composite":
            cmd += build_composite(step)

        elif op == "rotate":
            angle = step.get("angle", 0)
            bg = step.get("background", "none")
            cmd += ["-background", bg, "-rotate", str(angle)]

        elif op == "blur":
            sigma = step.get("sigma", 3)
            radius = step.get("radius", 0)
            cmd += ["-blur", f"{radius}x{sigma}"]

        elif op == "sharpen":
            sigma = step.get("sigma", 1)
            radius = step.get("radius", 0)
            cmd += ["-sharpen", f"{radius}x{sigma}"]

        elif op == "unsharp":
            sigma = step.get("sigma", 0.5)
            radius = step.get("radius", 0)
            amount = step.get("amount", 1)
            threshold = step.get("threshold", 0.05)
            cmd += ["-unsharp", f"{radius}x{sigma}+{amount}+{threshold}"]

        elif op == "modulate":
            b = step.get("brightness", 100)
            s = step.get("saturation", 100)
            h = step.get("hue", 100)
            cmd += ["-modulate", f"{b},{s},{h}"]

        elif op == "brightness_contrast":
            b = step.get("brightness", 0)
            c = step.get("contrast", 0)
            cmd += ["-brightness-contrast", f"{b}x{c}"]

        elif op == "levels":
            black = step.get("black", "0%")
            white = step.get("white", "100%")
            gamma = step.get("gamma")
            level_str = f"{black},{white}"
            if gamma:
                level_str += f",{gamma}"
            cmd += ["-level", level_str]

        elif op == "gamma":
            cmd += ["-gamma", str(step.get("value", 1.0))]

        elif op == "sigmoidal_contrast":
            strength = step.get("strength", 5)
            midpoint = step.get("midpoint", "50%")
            cmd += ["-sigmoidal-contrast", f"{strength}x{midpoint}"]

        elif op == "colorize":
            color = step.get("color", "#000000")
            amount = step.get("amount", 30)
            cmd += ["-fill", color, "-colorize", f"{amount}%"]

        elif op == "sepia":
            threshold = step.get("threshold", 80)
            cmd += ["-sepia-tone", f"{threshold}%"]

        elif op == "grayscale":
            cmd += ["-colorspace", "Gray"]

        elif op == "negate":
            cmd += ["-negate"]

        elif op == "auto_level":
            cmd += ["-auto-level"]

        elif op == "normalize":
            cmd += ["-normalize"]

        elif op == "auto_orient":
            cmd += ["-auto-orient"]

        elif op == "flip":
            cmd += ["-flip"]

        elif op == "flop":
            cmd += ["-flop"]

        elif op == "transpose":
            cmd += ["-transpose"]

        elif op == "transverse":
            cmd += ["-transverse"]

        elif op == "border":
            color = step.get("color", "#000000")
            size = step.get("size", 10)
            size_str = f"{size}x{size}" if isinstance(size, int) else size
            cmd += ["-bordercolor", color, "-border", size_str]

        elif op == "extent":
            w = step.get("width") or step.get("w")
            h = step.get("height") or step.get("h")
            bg = step.get("background", "white")
            gravity = step.get("gravity", "center")
            cmd += ["-gravity", gravity, "-background", bg, "-extent", f"{w}x{h}"]

        elif op == "shadow":
            opacity = step.get("opacity", 60)
            sigma = step.get("sigma", 5)
            x = step.get("x", 5)
            y = step.get("y", 5)
            cmd += ["(", "+clone", "-background", "black",
                    "-shadow", f"{opacity}x{sigma}+{x}+{y}", ")",
                    "+swap", "-background", "none",
                    "-layers", "merge", "+repage"]

        elif op == "transparent":
            color = step.get("color", "white")
            fuzz = step.get("fuzz", 10)
            cmd += ["-fuzz", f"{fuzz}%", "-transparent", color]

        elif op == "alpha_remove":
            bg = step.get("background", "white")
            cmd += ["-background", bg, "-alpha", "remove"]

        elif op == "alpha_set":
            cmd += ["-alpha", "set"]

        elif op == "quality":
            cmd += ["-quality", str(step.get("value", 85))]

        elif op == "strip":
            cmd += ["-strip"]

        elif op == "density":
            cmd += ["-density", str(step.get("value", 300))]

        elif op == "draw":
            primitive = step.get("primitive", "")
            if not primitive:
                raise ValueError("draw requires 'primitive' string")
            fill = step.get("fill")
            stroke = step.get("stroke")
            strokewidth = step.get("strokewidth")
            draw_args = []
            if fill:
                draw_args += ["-fill", fill]
            if stroke:
                draw_args += ["-stroke", stroke]
            if strokewidth:
                draw_args += ["-strokewidth", str(strokewidth)]
            draw_args += ["-draw", primitive]
            cmd += draw_args

        elif op == "raw":
            # Escape hatch: pass raw magick arguments
            raw_args = step.get("args", [])
            if isinstance(raw_args, str):
                raw_args = shlex.split(raw_args)
            cmd += raw_args

        else:
            raise ValueError(f"Unknown operation: {op}")

    cmd.append(output_path)
    return cmd


def main():
    parser = argparse.ArgumentParser(
        description="Build and execute ImageMagick pipelines from JSON specs"
    )
    parser.add_argument("spec", help="Path to JSON spec file, or '-' for stdin")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the command without executing")
    args = parser.parse_args()

    # Load spec
    if args.spec == "-":
        spec = json.load(sys.stdin)
    else:
        with open(args.spec) as f:
            spec = json.load(f)

    try:
        cmd = build_command(spec)
    except ValueError as e:
        print(f"Spec error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        # Print shell-escaped command
        print(shlex.join(cmd))
        sys.exit(0)

    # Ensure output directory exists
    output_path = spec.get("output", "")
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        print("ImageMagick not found. Install with: brew install imagemagick", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        print(f"magick failed: {result.stderr.strip()}", file=sys.stderr)
        print(f"Command: {shlex.join(cmd)}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "status": "ok",
        "output": os.path.abspath(output_path),
        "command": shlex.join(cmd),
    }, indent=2))


if __name__ == "__main__":
    main()
