#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Apply textures to an existing 3D model via Meshy text-to-texture API.

Usage:
    uv run meshy_texture.py https://cdn.meshy.ai/.../model.glb --prompt "Military olive drab paint"
    uv run meshy_texture.py MODEL_URL --prompt "Worn metal, rust patches" --enable-pbr
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
    parser = argparse.ArgumentParser(description="Apply texture to 3D model")
    parser.add_argument("model_url", help="URL of existing 3D model")
    parser.add_argument("--prompt", required=True, help="Texture description")
    parser.add_argument("--negative-prompt", default="", help="What to avoid")
    parser.add_argument("--art-style", default="", help="Art style hint")
    parser.add_argument("--enable-pbr", action="store_true", default=True, help="Enable PBR (default)")
    parser.add_argument("--no-pbr", dest="enable_pbr", action="store_false", help="Disable PBR")
    parser.add_argument("--format", default="glb", choices=["glb", "gltf", "usdz", "fbx"],
                        help="Output format (default: glb)")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="textured", help="Output filename (no extension)")
    parser.add_argument("--api-key", help="Override MESHY_API_KEY")
    parser.add_argument("--poll-interval", type=int, default=5, help="Seconds between polls")
    parser.add_argument("--timeout", type=int, default=600, help="Max wait seconds")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    client = MeshyClient(api_key=args.api_key)
    output_dir = Path(args.output)

    if not args.quiet and not args.json:
        print(f"Meshy Text-to-Texture")
        print(f"  Model: {args.model_url[:60]}...")
        print(f"  Prompt: {args.prompt[:60]}")
        print()

    # Submit
    if not args.quiet:
        print(f"  Submitting texture task...")
    task_id = client.create_text_to_texture(
        args.model_url,
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        art_style=args.art_style,
        enable_pbr=args.enable_pbr,
    )
    if not args.quiet:
        print(f"  Task: {task_id}")

    # Poll
    task = client.poll_task(
        task_id,
        endpoint="text-to-texture",
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        quiet=args.quiet or args.json,
        label="texture",
    )

    if task.get("status") != "SUCCEEDED":
        if args.json:
            print(json.dumps({"success": False, "task_id": task_id, "status": task.get("status")}))
        else:
            print("Texturing failed.", file=sys.stderr)
        sys.exit(1)

    # Download
    path = client.download_model(
        task,
        output_dir=output_dir,
        filename=args.filename,
        format=args.format,
    )

    if args.json:
        print(json.dumps({"success": True, "output": str(path), "format": args.format}))
    elif path:
        size_kb = path.stat().st_size / 1024
        print(f"\nDone! {path} ({size_kb:.0f} KB)")

    sys.exit(0 if path else 1)


if __name__ == "__main__":
    main()
