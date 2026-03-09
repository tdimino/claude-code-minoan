#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Generate a 3D model from a text prompt via Meshy text-to-3D API.

Usage:
    uv run meshy_text_to_3d.py "a stealth fighter jet, delta wings"
    uv run meshy_text_to_3d.py "a red cube" --skip-refine --format glb --output ./models
    uv run meshy_text_to_3d.py "military drone UAV" --model-type lowpoly --filename drone
"""

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from _meshy_utils import MeshyClient


def main():
    parser = argparse.ArgumentParser(description="Generate 3D model from text prompt")
    parser.add_argument("prompt", help="Text description of the 3D model")
    parser.add_argument("--negative-prompt", default="", help="What to avoid")
    parser.add_argument("--model-type", default="lowpoly", choices=["standard", "lowpoly", "ai_model"],
                        help="Model type (default: lowpoly)")
    parser.add_argument("--skip-refine", action="store_true", help="Preview only (saves credits)")
    parser.add_argument("--enable-pbr", action="store_true", default=True, help="Enable PBR textures in refine (default)")
    parser.add_argument("--no-pbr", dest="enable_pbr", action="store_false", help="Disable PBR textures")
    parser.add_argument("--format", default="glb", choices=["glb", "gltf", "usdz", "fbx"],
                        help="Output format (default: glb)")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="", help="Output filename (no extension)")
    parser.add_argument("--api-key", help="Override MESHY_API_KEY")
    parser.add_argument("--poll-interval", type=int, default=5, help="Seconds between polls (default: 5)")
    parser.add_argument("--timeout", type=int, default=600, help="Max wait seconds (default: 600)")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    args = parser.parse_args()

    client = MeshyClient(api_key=args.api_key)
    output_dir = Path(args.output)
    output_name = args.filename or args.prompt[:40].replace(" ", "-").replace(",", "").lower()

    if not args.quiet and not args.json:
        mode = "preview only" if args.skip_refine else "preview + refine"
        print(f"Meshy Text-to-3D ({mode})")
        print(f"  Prompt: {args.prompt[:80]}...")
        print(f"  Model type: {args.model_type}")
        print(f"  Output: {output_dir}/{output_name}.{args.format}")
        print()

    success, output_path = client.generate_full(
        args.prompt,
        negative_prompt=args.negative_prompt,
        model_type=args.model_type,
        skip_refine=args.skip_refine,
        output_dir=output_dir,
        output_name=output_name,
        format=args.format,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        quiet=args.quiet or args.json,
        enable_pbr=args.enable_pbr,
    )

    if args.json:
        print(json.dumps({
            "success": success,
            "output": str(output_path) if output_path else None,
            "format": args.format,
            "prompt": args.prompt,
        }))
    elif not args.quiet:
        if success and output_path:
            size_kb = output_path.stat().st_size / 1024
            print(f"\nDone! {output_path} ({size_kb:.0f} KB)")
        else:
            print("\nGeneration failed.", file=sys.stderr)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
