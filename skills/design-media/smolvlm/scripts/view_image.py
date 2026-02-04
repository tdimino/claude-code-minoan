#!/usr/bin/env python3
"""SmolVLM image analysis using mlx-vlm.

Usage:
    python view_image.py <image_path> [prompt]
    python view_image.py <image_path> --detailed

Examples:
    python view_image.py photo.png
    python view_image.py screenshot.png "Extract all text exactly as shown"
    python view_image.py ui.png --detailed
"""

import argparse
import sys
from pathlib import Path

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_TOKENS_LIMIT = 2048


def main():
    parser = argparse.ArgumentParser(description="Analyze images with SmolVLM")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("prompt", nargs="?", default="Describe this image.",
                        help="Question or instruction about the image")
    parser.add_argument("--detailed", action="store_true",
                        help="Generate detailed description")
    parser.add_argument("--max-tokens", type=int, default=512,
                        help="Maximum tokens to generate (1-2048)")
    parser.add_argument("--temp", type=float, default=0.0,
                        help="Temperature (0.0 for deterministic)")
    args = parser.parse_args()

    # Validate max-tokens bounds
    if args.max_tokens < 1 or args.max_tokens > MAX_TOKENS_LIMIT:
        parser.error(f"--max-tokens must be between 1 and {MAX_TOKENS_LIMIT}")

    # Validate image exists
    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    # Check supported formats
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    if image_path.suffix.lower() not in valid_extensions:
        print(f"Error: Unsupported format. Use: {', '.join(valid_extensions)}",
              file=sys.stderr)
        sys.exit(1)

    # Check file size to prevent OOM
    file_size = image_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        print(f"Error: Image too large ({file_size // (1024*1024)}MB). Max: 50MB.",
              file=sys.stderr)
        sys.exit(1)

    # Build prompt
    if args.detailed:
        prompt = "Describe this image in detail, including colors, composition, objects, text, and any notable features."
    else:
        prompt = args.prompt

    try:
        from mlx_vlm import load, generate
        from mlx_vlm.prompt_utils import apply_chat_template
        from mlx_vlm.utils import load_config

        # Load model (cached after first load)
        model_path = "HuggingFaceTB/SmolVLM-Instruct"
        print("Loading SmolVLM model...", file=sys.stderr)
        model, processor = load(model_path)
        config = load_config(model_path)
        print("Model loaded.", file=sys.stderr)

        # Format prompt with chat template
        formatted_prompt = apply_chat_template(
            processor, config, prompt, num_images=1
        )

        # Generate response (image as list per mlx-vlm API)
        result = generate(
            model,
            processor,
            formatted_prompt,
            image=[str(image_path)],
            max_tokens=args.max_tokens,
            temp=args.temp,
            verbose=False
        )

        # Extract text from GenerationResult or string
        if hasattr(result, 'text'):
            text = result.text
        elif isinstance(result, str):
            text = result
        else:
            print(f"Error: Unexpected result type: {type(result)}", file=sys.stderr)
            sys.exit(1)

        print(text.strip())

    except ImportError:
        print("Error: mlx-vlm not installed. Run: uv pip install mlx-vlm --system",
              file=sys.stderr)
        sys.exit(1)
    except MemoryError:
        print("Error: Out of memory. Close other applications and try again.",
              file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
