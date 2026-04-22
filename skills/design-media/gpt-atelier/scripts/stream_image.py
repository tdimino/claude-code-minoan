#!/usr/bin/env python3
"""
Streaming image generation with partial image delivery.
Outputs partial images as they generate, then the final image.

Usage:
    python stream_image.py "A scenic mountain landscape" --partials 2
    python stream_image.py "prompt" --partials 3 --output ./output

Env: OPENAI_API_KEY
"""

import argparse
import base64
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from openai_images import (
    resolve_model, resolve_size,
    SIZE_PRESETS, VALID_QUALITIES, VALID_FORMATS,
)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai library not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)


def stream_generate(client: OpenAI, prompt: str, model: str, partials: int,
                    size: str = None, quality: str = "high",
                    output_format: str = "png"):
    """Stream image generation, yielding (kind, idx, bytes) tuples."""
    kwargs = {
        "prompt": prompt,
        "model": model,
        "stream": True,
        "partial_images": partials,
    }
    if size:
        kwargs["size"] = resolve_size(size)
    if quality:
        kwargs["quality"] = quality
    if output_format:
        kwargs["output_format"] = output_format

    event = None
    final = None

    stream = client.images.generate(**kwargs)
    for event in stream:
        if event.type == "image_generation.partial_image":
            idx = event.partial_image_index
            img_bytes = base64.b64decode(event.b64_json)
            yield ("partial", idx, img_bytes)
        elif event.type == "image_generation.image":
            img_bytes = base64.b64decode(event.b64_json)
            final = img_bytes
            yield ("final", 0, img_bytes)

    if final is None:
        if event is None:
            print("Warning: Stream produced zero events", file=sys.stderr)
        elif hasattr(event, "data") and event.data:
            for img in event.data:
                if img.b64_json:
                    yield ("final", 0, base64.b64decode(img.b64_json))
        else:
            print("Warning: Stream completed without a final image", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Streaming image generation with partial delivery")
    parser.add_argument("prompt", help="Text description")
    parser.add_argument("--partials", type=int, default=2, help="Number of partial images (0-3)")
    parser.add_argument("--model", help="Model ID override")
    parser.add_argument("--fast", action="store_true", help="Use gpt-image-1.5")
    parser.add_argument("--mini", action="store_true", help="Use gpt-image-1-mini")
    parser.add_argument("--size", default=None,
                        help=f"Image size: WxH or preset ({', '.join(SIZE_PRESETS.keys())})")
    parser.add_argument("--quality", default="high", choices=VALID_QUALITIES)
    parser.add_argument("--format", dest="output_format", default="png", choices=VALID_FORMATS)
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="streamed", help="Base filename")
    parser.add_argument("--save-partials", action="store_true", help="Save partial images too")
    parser.add_argument("--api-key", help="API key (or use OPENAI_API_KEY env)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    model = resolve_model(args.model, args.fast, args.mini)
    client = OpenAI(api_key=api_key)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")

    print(f"Model: {model}", file=sys.stderr)
    print(f"Streaming with {args.partials} partial(s)...", file=sys.stderr)

    saved = []
    for kind, idx, img_bytes in stream_generate(
        client, args.prompt, model, args.partials,
        args.size, args.quality, args.output_format
    ):
        if kind == "partial":
            print(f"  Partial {idx} received ({len(img_bytes)} bytes)", file=sys.stderr)
            if args.save_partials:
                path = out / f"{args.filename}_partial{idx}_{ts}.{args.output_format}"
                path.write_bytes(img_bytes)
                saved.append(path)
                print(f"  Saved: {path}")
        elif kind == "final":
            path = out / f"{args.filename}_{ts}.{args.output_format}"
            path.write_bytes(img_bytes)
            saved.append(path)
            print(f"Saved: {path}")

    if not saved:
        print("No images received", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
