#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Generate a 3D model from a reference image via Meshy image-to-3D API.

Usage:
    uv run meshy_image_to_3d.py ./reference.png
    uv run meshy_image_to_3d.py https://example.com/image.jpg --format glb
    uv run meshy_image_to_3d.py photo.jpg --model-type lowpoly --output ./models
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from _meshy_utils import MeshyClient, log_event


def resolve_image(image_arg: str) -> str:
    """Convert local file path to base64 data URI, or pass URL through."""
    if image_arg.startswith(("http://", "https://")):
        return image_arg

    path = Path(image_arg)
    if not path.exists():
        print(f"ERROR: Image file not found: {image_arg}", file=sys.stderr)
        sys.exit(1)

    suffix = path.suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime = mime_map.get(suffix, "image/png")

    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


def main():
    parser = argparse.ArgumentParser(description="Generate 3D model from image")
    parser.add_argument("image", help="Image file path or URL")
    parser.add_argument("--model-type", default="lowpoly", choices=["standard", "lowpoly"],
                        help="Model type (default: lowpoly)")
    parser.add_argument("--topology", default="", choices=["", "triangle", "quad"],
                        help="Mesh topology")
    parser.add_argument("--target-polycount", type=int, default=None, help="Target polygon count")
    parser.add_argument("--format", default="glb", choices=["glb", "gltf", "usdz", "fbx"],
                        help="Output format (default: glb)")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="", help="Output filename (no extension)")
    parser.add_argument("--api-key", help="Override MESHY_API_KEY")
    parser.add_argument("--poll-interval", type=int, default=5, help="Seconds between polls")
    parser.add_argument("--timeout", type=int, default=600, help="Max wait seconds")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    client = MeshyClient(api_key=args.api_key)
    output_dir = Path(args.output)
    image_url = resolve_image(args.image)
    output_name = args.filename or Path(args.image).stem

    if not args.quiet and not args.json:
        source = args.image if len(args.image) < 60 else f"...{args.image[-50:]}"
        print(f"Meshy Image-to-3D")
        print(f"  Source: {source}")
        print(f"  Model type: {args.model_type}")
        print()

    # Submit
    if not args.quiet:
        print(f"  Submitting image-to-3D task...")
    task_id = client.create_image_to_3d(
        image_url,
        model_type=args.model_type,
        topology=args.topology,
        target_polycount=args.target_polycount,
    )
    if not args.quiet:
        print(f"  Task: {task_id}")

    # Poll
    task = client.poll_task(
        task_id,
        endpoint="image-to-3d",
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        quiet=args.quiet or args.json,
        label=output_name,
    )

    if task.get("status") != "SUCCEEDED":
        if args.json:
            print(json.dumps({"success": False, "task_id": task_id, "status": task.get("status")}))
        else:
            print("Generation failed.", file=sys.stderr)
        sys.exit(1)

    # Download
    path = client.download_model(
        task,
        output_dir=output_dir,
        filename=output_name,
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
