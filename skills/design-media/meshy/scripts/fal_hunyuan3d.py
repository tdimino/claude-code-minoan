#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
fal.ai Hunyuan3D v3.1 Pro — image-to-3D and text-to-3D generation.

Produces .glb models with PBR textures via fal.ai's queue API.
Cost: ~$0.225-$0.375 per model.

Usage:
  # Image-to-3D (primary use case)
  uv run fal_hunyuan3d.py ./photo.png --output ./models
  uv run fal_hunyuan3d.py https://example.com/image.jpg --filename tank

  # Text-to-3D (rapid mode, max 195 chars)
  uv run fal_hunyuan3d.py --text "a golden microphone, ornate design" --output ./models

  # Options
  uv run fal_hunyuan3d.py ./photo.png --face-count 100000 --no-pbr --json
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

# Resolve imports from skill scripts directory
sys.path.insert(0, str(Path(__file__).parent))
from _provider_base import (
    ProviderError,
    download_file,
    get_api_key,
    log_event,
    resolve_image_input,
)

PROVIDER = "fal.ai"
QUEUE_BASE = "https://queue.fal.run"
SYNC_BASE = "https://fal.run"

ENDPOINTS = {
    "image_to_3d": "fal-ai/hunyuan-3d/v3.1/pro/image-to-3d",
    "text_to_3d": "fal-ai/hunyuan-3d/v3.1/rapid/text-to-3d",
}

DEFAULT_FACE_COUNT = 500_000
DEFAULT_POLL_INTERVAL = 4
DEFAULT_TIMEOUT = 300


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Key {api_key}", "Content-Type": "application/json"}


def _submit_queue(api_key: str, endpoint_key: str, payload: dict) -> dict:
    """Submit a job to fal.ai's queue. Returns submit response with request_id."""
    ep = ENDPOINTS[endpoint_key]
    url = f"{QUEUE_BASE}/{ep}"
    resp = requests.post(url, headers=_headers(api_key), json=payload, timeout=30)
    if resp.status_code >= 400:
        try:
            err = resp.json()
            msg = err.get("detail", [{}])
            if isinstance(msg, list) and msg:
                msg = msg[0].get("msg", str(msg))
            elif isinstance(msg, str):
                pass
            else:
                msg = err.get("message", resp.text)
        except (json.JSONDecodeError, ValueError):
            msg = resp.text
        raise ProviderError(PROVIDER, resp.status_code, str(msg))
    return resp.json()


def _poll_queue(
    api_key: str,
    submit_data: dict,
    endpoint_key: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
    quiet: bool = False,
) -> dict:
    """Poll a fal.ai queue job until completion. Returns result dict."""
    request_id = submit_data["request_id"]
    ep = ENDPOINTS[endpoint_key]
    status_url = submit_data.get("status_url", f"{QUEUE_BASE}/{ep}/requests/{request_id}/status")
    response_url = submit_data.get("response_url", f"{QUEUE_BASE}/{ep}/requests/{request_id}")
    headers = _headers(api_key)

    start = time.time()
    last_status = ""

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise ProviderError(PROVIDER, 408, f"Job {request_id} timed out after {timeout}s", request_id)

        time.sleep(poll_interval)

        resp = requests.get(status_url, headers=headers, timeout=30)
        resp.raise_for_status()
        status_data = resp.json()
        status = status_data.get("status", "UNKNOWN")

        if status != last_status and not quiet:
            print(f"  Status: {status} ({elapsed:.0f}s)")
            last_status = status

        if status == "COMPLETED":
            result = requests.get(response_url, headers=headers, timeout=60)
            result.raise_for_status()
            return result.json()

        if status == "FAILED":
            error_detail = status_data.get("error") or status_data.get("detail") or "no detail"
            raise ProviderError(PROVIDER, 500, f"Generation failed: {error_detail}", request_id)


def image_to_3d(
    api_key: str,
    image: str,
    face_count: int = DEFAULT_FACE_COUNT,
    enable_pbr: bool = True,
    generate_type: str = "Normal",
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
    quiet: bool = False,
) -> dict:
    """Generate a 3D model from an image. Returns fal.ai result dict."""
    payload = {
        "input_image_url": image,
        "generate_type": generate_type,
        "face_count": face_count,
        "enable_pbr": enable_pbr,
    }

    if not quiet:
        print(f"  Submitting image-to-3D (face_count={face_count}, pbr={enable_pbr})...")

    log_event({"action": "fal_image_to_3d_submit", "face_count": face_count, "enable_pbr": enable_pbr})
    submit_data = _submit_queue(api_key, "image_to_3d", payload)
    request_id = submit_data["request_id"]

    if not quiet:
        print(f"  Queue job: {request_id}")

    result = _poll_queue(api_key, submit_data, "image_to_3d", poll_interval, timeout, quiet)
    log_event({"action": "fal_image_to_3d_complete", "request_id": request_id})
    return result


def text_to_3d(
    api_key: str,
    prompt: str,
    seed: int | None = None,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
    quiet: bool = False,
) -> dict:
    """Generate a 3D model from text. Returns fal.ai result dict."""
    if len(prompt) > 195:
        print(f"  Warning: prompt truncated from {len(prompt)} to 195 chars", file=sys.stderr)
        prompt = prompt[:195]

    payload = {"prompt": prompt}
    if seed is not None:
        payload["seed"] = seed

    if not quiet:
        print(f"  Submitting text-to-3D: \"{prompt[:60]}{'...' if len(prompt) > 60 else ''}\"")

    log_event({"action": "fal_text_to_3d_submit", "prompt": prompt[:100]})
    submit_data = _submit_queue(api_key, "text_to_3d", payload)
    request_id = submit_data["request_id"]

    if not quiet:
        print(f"  Queue job: {request_id}")

    result = _poll_queue(api_key, submit_data, "text_to_3d", poll_interval, timeout, quiet)
    log_event({"action": "fal_text_to_3d_complete", "request_id": request_id})
    return result


def extract_urls(result: dict) -> dict:
    """Extract model URLs from fal.ai result."""
    return {
        "glb": result.get("model_glb", {}).get("url") or result.get("model_urls", {}).get("glb", {}).get("url"),
        "obj": result.get("model_urls", {}).get("obj", {}).get("url"),
        "texture": result.get("model_urls", {}).get("texture", {}).get("url"),
        "thumbnail": result.get("thumbnail", {}).get("url"),
        "seed": result.get("seed"),
    }


def main():
    parser = argparse.ArgumentParser(description="fal.ai Hunyuan3D v3.1 Pro — 3D model generation")
    parser.add_argument("image", nargs="?", help="Image file path or URL (for image-to-3D)")
    parser.add_argument("--text", help="Text prompt (for text-to-3D, max 195 chars)")
    parser.add_argument("--face-count", type=int, default=DEFAULT_FACE_COUNT, help=f"Target face count (default: {DEFAULT_FACE_COUNT})")
    parser.add_argument("--no-pbr", action="store_true", help="Disable PBR textures")
    parser.add_argument("--seed", type=int, help="Seed for reproducibility (text-to-3D only)")
    parser.add_argument("--output", default="./output", help="Output directory (default: ./output)")
    parser.add_argument("--filename", default="", help="Output filename without extension")
    parser.add_argument("--api-key", help="Override FAL_KEY")
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL, help="Poll interval in seconds")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Max wait in seconds")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    if not args.image and not args.text:
        parser.error("Provide an image path/URL or --text prompt")

    api_key = get_api_key("FAL_KEY", args.api_key)

    if args.text:
        result = text_to_3d(
            api_key, args.text,
            seed=args.seed,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
            quiet=args.quiet,
        )
    else:
        image_input = resolve_image_input(args.image)
        result = image_to_3d(
            api_key, image_input,
            face_count=args.face_count,
            enable_pbr=not args.no_pbr,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
            quiet=args.quiet,
        )

    urls = extract_urls(result)

    if args.json:
        print(json.dumps(urls, indent=2))
        return

    # Download GLB
    glb_url = urls["glb"]
    if not glb_url:
        print("Error: no GLB URL in response", file=sys.stderr)
        sys.exit(1)

    filename = args.filename or "model"
    output_dir = Path(args.output)
    output_path = download_file(glb_url, output_dir, f"{filename}.glb", quiet=args.quiet)

    if not args.quiet:
        print(f"\n  Model: {output_path}")
        if urls["thumbnail"]:
            print(f"  Thumbnail: {urls['thumbnail']}")
        if urls["seed"] is not None:
            print(f"  Seed: {urls['seed']}")


if __name__ == "__main__":
    main()
