#!/usr/bin/env python3
"""
Compose a new image from multiple reference images using GPT Image models.
Uses the edits endpoint with multiple images and no mask — the model
creates a new composition incorporating all references.

Usage:
    python compose_images.py "Create a gift basket with these items" img1.png img2.png img3.png

Env: OPENAI_API_KEY
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from openai_images import (
    GPTAtelierClient, resolve_model, save_images,
    SIZE_PRESETS, VALID_QUALITIES, VALID_FORMATS,
)


def main():
    parser = argparse.ArgumentParser(description="Compose images from multiple references")
    parser.add_argument("prompt", help="Composition instruction")
    parser.add_argument("images", nargs="+", help="Reference image paths (2+)")
    parser.add_argument("--model", help="Model ID override")
    parser.add_argument("--fast", action="store_true", help="Use gpt-image-1.5")
    parser.add_argument("--mini", action="store_true", help="Use gpt-image-1-mini")
    parser.add_argument("--size", default=None,
                        help=f"Output size: WxH or preset ({', '.join(SIZE_PRESETS.keys())})")
    parser.add_argument("--quality", default="high", choices=VALID_QUALITIES)
    parser.add_argument("--n", type=int, default=1, help="Number of variations")
    parser.add_argument("--format", dest="output_format", default="png", choices=VALID_FORMATS)
    parser.add_argument("--compression", type=int, help="JPEG/WebP compression 0-100")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="composed", help="Base filename")
    parser.add_argument("--api-key", help="API key (or use OPENAI_API_KEY env)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    for p in args.images:
        if not Path(p).exists():
            print(f"Error: Image not found: {p}", file=sys.stderr)
            sys.exit(1)

    if len(args.images) < 2:
        print("Error: compose requires at least 2 reference images", file=sys.stderr)
        sys.exit(1)

    model = resolve_model(args.model, args.fast, args.mini)
    try:
        client = GPTAtelierClient(api_key=args.api_key, model=model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Model: {model}", file=sys.stderr)
    print(f"Composing from {len(args.images)} references...", file=sys.stderr)

    response = client.edit(
        prompt=args.prompt,
        image_paths=args.images,
        mask_path=None,
        size=args.size,
        quality=args.quality,
        n=args.n,
        output_format=args.output_format,
        output_compression=args.compression,
    )

    saved = save_images(response, args.output, args.filename, args.output_format)
    for path in saved:
        print(f"Saved: {path}")

    if not saved:
        print("No images returned", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
