#!/usr/bin/env python3
"""
Generate images from text prompts using OpenAI GPT Image models.

Usage:
    python generate_image.py "prompt text" [options]

Env: OPENAI_API_KEY
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from openai_images import (
    GPTAtelierClient, resolve_model, resolve_size, save_images,
    SIZE_PRESETS, VALID_QUALITIES, VALID_FORMATS,
)


def main():
    parser = argparse.ArgumentParser(description="Generate images with GPT Image models")
    parser.add_argument("prompt", help="Text description of the image to generate")
    parser.add_argument("--model", help="Model ID override")
    parser.add_argument("--fast", action="store_true", help="Use gpt-image-1.5 (faster, cheaper)")
    parser.add_argument("--mini", action="store_true", help="Use gpt-image-1-mini (cheapest)")
    parser.add_argument("--size", default=None,
                        help=f"Image size: WxH or preset ({', '.join(SIZE_PRESETS.keys())})")
    parser.add_argument("--quality", default="high", choices=VALID_QUALITIES)
    parser.add_argument("--n", type=int, default=1, help="Number of images (1-8)")
    parser.add_argument("--format", dest="output_format", default="png", choices=VALID_FORMATS)
    parser.add_argument("--compression", type=int, help="JPEG/WebP compression 0-100")
    parser.add_argument("--background", choices=["opaque", "transparent", "auto"])
    parser.add_argument("--moderation", choices=["auto", "low"])
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="generated", help="Base filename")
    parser.add_argument("--api-key", help="API key (or use OPENAI_API_KEY env)")
    parser.add_argument("--verbose", action="store_true", help="Show full API response")
    args = parser.parse_args()

    model = resolve_model(args.model, args.fast, args.mini)
    try:
        client = GPTAtelierClient(api_key=args.api_key, model=model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Model: {model}", file=sys.stderr)
    print(f"Generating...", file=sys.stderr)

    response = client.generate(
        prompt=args.prompt,
        size=args.size,
        quality=args.quality,
        n=args.n,
        output_format=args.output_format,
        output_compression=args.compression,
        background=args.background,
        moderation=args.moderation,
    )

    if args.verbose:
        print(json.dumps({"model": model, "created": response.created}, indent=2), file=sys.stderr)

    saved = save_images(response, args.output, args.filename, args.output_format)

    for path in saved:
        print(f"Saved: {path}")

    if not saved:
        print("No images returned", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
