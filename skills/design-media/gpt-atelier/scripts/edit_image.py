#!/usr/bin/env python3
"""
Edit images using OpenAI GPT Image models. Supports mask-based inpainting
and full-image re-rendering.

Usage:
    python edit_image.py "edit instruction" input.png [options]
    python edit_image.py "Replace car with bicycle" photo.png --mask mask.png

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


def ensure_mask_alpha(mask_path: Path) -> Path:
    """Convert B&W mask to RGBA with alpha channel if needed."""
    try:
        from PIL import Image
    except ImportError:
        print("Warning: Pillow not installed — mask will NOT be auto-converted to RGBA.\n"
              "If the API rejects your mask, install Pillow: pip install Pillow",
              file=sys.stderr)
        return mask_path

    try:
        mask = Image.open(mask_path)
    except Exception as e:
        print(f"Error: Could not open mask image '{mask_path}': {e}", file=sys.stderr)
        sys.exit(1)

    if mask.mode == "RGBA":
        return mask_path

    gray = mask.convert("L")
    rgba = gray.convert("RGBA")
    rgba.putalpha(gray)

    out_path = mask_path.parent / f"{mask_path.stem}_alpha.png"
    rgba.save(out_path, format="PNG")
    print(f"Converted mask to RGBA: {out_path}", file=sys.stderr)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Edit images with GPT Image models")
    parser.add_argument("prompt", help="Edit instruction")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("--images", nargs="*", help="Additional reference images")
    parser.add_argument("--mask", help="Mask image (transparent regions = edit area)")
    parser.add_argument("--model", help="Model ID override")
    parser.add_argument("--fast", action="store_true", help="Use gpt-image-1.5")
    parser.add_argument("--mini", action="store_true", help="Use gpt-image-1-mini")
    parser.add_argument("--size", default=None,
                        help=f"Output size: WxH or preset ({', '.join(SIZE_PRESETS.keys())})")
    parser.add_argument("--quality", default="high", choices=VALID_QUALITIES)
    parser.add_argument("--n", type=int, default=1, help="Number of variations (1-4)")
    parser.add_argument("--format", dest="output_format", default="png", choices=VALID_FORMATS)
    parser.add_argument("--compression", type=int, help="JPEG/WebP compression 0-100")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="edited", help="Base filename")
    parser.add_argument("--api-key", help="API key (or use OPENAI_API_KEY env)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    all_images = [str(image_path)]
    if args.images:
        for p in args.images:
            if not Path(p).exists():
                print(f"Error: Reference image not found: {p}", file=sys.stderr)
                sys.exit(1)
            all_images.append(p)

    mask_path = None
    if args.mask:
        mp = Path(args.mask)
        if not mp.exists():
            print(f"Error: Mask not found: {mp}", file=sys.stderr)
            sys.exit(1)
        mask_path = str(ensure_mask_alpha(mp))

    model = resolve_model(args.model, args.fast, args.mini)
    try:
        client = GPTAtelierClient(api_key=args.api_key, model=model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Model: {model}", file=sys.stderr)
    print(f"Input: {image_path} (+{len(all_images)-1} refs)" if len(all_images) > 1
          else f"Input: {image_path}", file=sys.stderr)
    if mask_path:
        print(f"Mask: {mask_path}", file=sys.stderr)
    if model == "gpt-image-2" and not mask_path:
        print("\n⚠  gpt-image-2 reference-image editing often produces yellow tint "
              "and poor prompt adherence.\n"
              "   For design-final work, generate fresh instead of editing.\n"
              "   Use --fast (gpt-image-1.5) for better edit results.\n",
              file=sys.stderr)
    print(f"Editing...", file=sys.stderr)

    response = client.edit(
        prompt=args.prompt,
        image_paths=all_images,
        mask_path=mask_path,
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
