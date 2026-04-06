#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
WaveSpeedAI Rapid — budget Hunyuan3D v3.1 image-to-3D generation.

Produces .glb models at $0.0225/model (16x cheaper than fal.ai Pro).
Single parameter: image URL or local file path.

Usage:
  uv run wavespeed_rapid.py ./photo.png --output ./models
  uv run wavespeed_rapid.py https://example.com/image.jpg --filename tank
  uv run wavespeed_rapid.py ./photo.png --json
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

PROVIDER = "wavespeed"
API_BASE = "https://api.wavespeed.ai/api/v3"

DEFAULT_POLL_INTERVAL = 5
DEFAULT_TIMEOUT = 300


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def generate(
    api_key: str,
    image: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
    quiet: bool = False,
) -> str:
    """
    Generate a 3D model from an image via WaveSpeedAI Rapid.
    Returns the GLB download URL.
    """
    headers = _headers(api_key)

    # Submit
    if not quiet:
        print("  Submitting to WaveSpeedAI Rapid...")

    log_event({"action": "wavespeed_submit"})
    resp = requests.post(
        f"{API_BASE}/wavespeed-ai/hunyuan-3d-v3.1/image-to-3d-rapid",
        json={"image": image},
        headers=headers,
        timeout=30,
    )
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("message", resp.text)
        except (json.JSONDecodeError, ValueError):
            msg = resp.text
        raise ProviderError(PROVIDER, resp.status_code, msg)

    body = resp.json()
    data = body.get("data", body)
    task_id = data.get("id")
    if not task_id:
        raise ProviderError(PROVIDER, 500, "No task ID in response")

    if not quiet:
        print(f"  Task: {task_id}")

    # Poll
    poll_url = data.get("urls", {}).get("get", f"{API_BASE}/predictions/{task_id}/result")
    start = time.time()
    last_status = ""

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise ProviderError(PROVIDER, 408, f"Task {task_id} timed out after {timeout}s", task_id)

        time.sleep(poll_interval)

        r = requests.get(poll_url, headers=headers, timeout=30)
        r.raise_for_status()
        body = r.json()
        d = body.get("data", body)
        status = d.get("status", "unknown")

        if status != last_status and not quiet:
            print(f"  Status: {status} ({elapsed:.0f}s)")
            last_status = status

        if status == "completed":
            outputs = d.get("outputs", [])
            if not outputs:
                raise ProviderError(PROVIDER, 500, "No outputs in completed response", task_id)
            glb_url = outputs[0]
            log_event({"action": "wavespeed_complete", "task_id": task_id})
            return glb_url

        if status == "failed":
            error = d.get("error", "unknown error")
            raise ProviderError(PROVIDER, 500, f"Generation failed: {error}", task_id)


def main():
    parser = argparse.ArgumentParser(description="WaveSpeedAI Rapid — budget 3D generation ($0.0225/model)")
    parser.add_argument("image", help="Image file path or URL")
    parser.add_argument("--output", default="./output", help="Output directory (default: ./output)")
    parser.add_argument("--filename", default="", help="Output filename without extension")
    parser.add_argument("--api-key", help="Override WAVESPEED_API_KEY")
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL, help="Poll interval in seconds")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Max wait in seconds")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--json", action="store_true", help="Output GLB URL as JSON")
    args = parser.parse_args()

    api_key = get_api_key("WAVESPEED_API_KEY", args.api_key)
    image_input = resolve_image_input(args.image)

    glb_url = generate(
        api_key, image_input,
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


if __name__ == "__main__":
    main()
