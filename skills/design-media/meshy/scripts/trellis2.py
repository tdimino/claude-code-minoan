#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Trellis 2 (3D AI Studio) — image-to-3D generation with poly count control.

Produces .glb models with optional PBR textures. Supports decimation_target
for precise polygon budget control (1K-16M faces).

Cost: 15-55 credits depending on resolution + textures.

Usage:
  # Basic (geometry only, 1024 resolution)
  uv run trellis2.py ./photo.png --output ./models

  # Low-poly for games (5000 faces)
  uv run trellis2.py ./photo.png --decimation 5000 --filename tank

  # High-quality with textures
  uv run trellis2.py ./photo.png --textures --texture-size 2048 --resolution 1024

  # Minimal geometry for concept validation
  uv run trellis2.py ./photo.png --resolution 512 --decimation 1000 --json
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from _provider_base import (
    ProviderError,
    download_file,
    get_api_key,
    log_event,
    resolve_image_input,
)

PROVIDER = "trellis2"
API_BASE = "https://api.3daistudio.com"

DEFAULT_RESOLUTION = "1024"
DEFAULT_DECIMATION = 1_000_000
DEFAULT_POLL_INTERVAL = 10
DEFAULT_TIMEOUT = 300


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def generate(
    api_key: str,
    image: str,
    resolution: str = DEFAULT_RESOLUTION,
    textures: bool = False,
    texture_size: int = 2048,
    decimation_target: int = DEFAULT_DECIMATION,
    seed: int | None = None,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
    quiet: bool = False,
) -> str:
    """
    Generate a 3D model from an image via Trellis 2.
    Returns the GLB download URL.
    """
    headers = _headers(api_key)

    # Build payload — use image_url for URLs, image for data URIs
    payload: dict = {
        "resolution": resolution,
        "textures": textures,
        "decimation_target": decimation_target,
        "generate_thumbnail": False,
    }
    if textures:
        payload["texture_size"] = texture_size
    if seed is not None:
        payload["seed"] = seed

    if image.startswith("data:"):
        payload["image"] = image
    else:
        payload["image_url"] = image

    if not quiet:
        print(f"  Submitting to Trellis 2 (res={resolution}, faces={decimation_target}, tex={textures})...")

    log_event({
        "action": "trellis2_submit",
        "resolution": resolution,
        "decimation_target": decimation_target,
        "textures": textures,
    })

    resp = requests.post(
        f"{API_BASE}/v1/3d-models/trellis2/generate/",
        json=payload,
        headers=headers,
        timeout=30,
    )
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("detail", resp.text)
        except (json.JSONDecodeError, ValueError):
            msg = resp.text
        raise ProviderError(PROVIDER, resp.status_code, str(msg))

    task_id = resp.json().get("task_id")
    if not task_id:
        raise ProviderError(PROVIDER, 500, "No task_id in response")

    if not quiet:
        print(f"  Task: {task_id}")

    # Poll
    start = time.time()
    last_status = ""
    last_progress = -1

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise ProviderError(PROVIDER, 408, f"Task {task_id} timed out after {timeout}s", task_id)

        time.sleep(poll_interval)

        r = requests.get(
            f"{API_BASE}/v1/generation-request/{task_id}/status/",
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        d = r.json()
        status = d.get("status", "UNKNOWN")
        progress = d.get("progress", 0)

        if (status != last_status or progress != last_progress) and not quiet:
            print(f"  Status: {status} {progress}% ({elapsed:.0f}s)")
            last_status = status
            last_progress = progress

        if status == "FINISHED":
            results = d.get("results", [])
            if not results:
                raise ProviderError(PROVIDER, 500, "No results in completed response", task_id)
            glb_url = results[0].get("asset")
            if not glb_url:
                raise ProviderError(PROVIDER, 500, "No asset URL in results", task_id)
            log_event({"action": "trellis2_complete", "task_id": task_id})
            return glb_url

        if status == "FAILED":
            reason = d.get("failure_reason", "unknown")
            raise ProviderError(PROVIDER, 500, f"Generation failed: {reason}", task_id)


def main():
    parser = argparse.ArgumentParser(description="Trellis 2 (3D AI Studio) — 3D generation with poly control")
    parser.add_argument("image", help="Image file path or URL")
    parser.add_argument("--resolution", default=DEFAULT_RESOLUTION, choices=["512", "1024", "1536"], help="Voxel grid resolution")
    parser.add_argument("--textures", action="store_true", help="Generate PBR textures (costs more credits)")
    parser.add_argument("--texture-size", type=int, default=2048, choices=[1024, 2048, 4096], help="Texture map resolution")
    parser.add_argument("--decimation", type=int, default=DEFAULT_DECIMATION, help=f"Target face count (default: {DEFAULT_DECIMATION})")
    parser.add_argument("--seed", type=int, help="Seed for reproducibility")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="", help="Output filename without extension")
    parser.add_argument("--api-key", help="Override THREEDAI_API_KEY")
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL, help="Poll interval in seconds")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Max wait in seconds")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--json", action="store_true", help="Output GLB URL as JSON")
    args = parser.parse_args()

    api_key = get_api_key("THREEDAI_API_KEY", args.api_key)
    image_input = resolve_image_input(args.image)

    glb_url = generate(
        api_key, image_input,
        resolution=args.resolution,
        textures=args.textures,
        texture_size=args.texture_size,
        decimation_target=args.decimation,
        seed=args.seed,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        quiet=args.quiet,
    )

    if args.json:
        print(json.dumps({"glb": glb_url}, indent=2))
        return

    filename = args.filename or "model"
    output_dir = Path(args.output)
    output_path = download_file(glb_url, output_dir, f"{filename}.glb", quiet=args.quiet)

    if not args.quiet:
        print(f"\n  Model: {output_path}")
        print(f"  (Results expire in 24 hours from 3D AI Studio)")


if __name__ == "__main__":
    main()
