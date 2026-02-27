#!/usr/bin/env python3
"""
Compose multiple images into a new image using Nano Banana Pro.

This script allows you to combine, blend, or arrange multiple reference images
based on natural language instructions. Perfect for creating collages, group photos,
style transfers, and complex compositions.

Usage:
    python compose_images.py "instruction" image1.png image2.png [image3.png ...] [options]

Examples:
    # Create group photo from individual portraits
    python compose_images.py "Create a group photo of these people in an office" person1.png person2.png person3.png

    # Style transfer
    python compose_images.py "Apply the art style from the first image to the scene in the second" style_ref.png photo.png

    # Character composition
    python compose_images.py "Put the cat from the first image on the couch from the second" cat.png couch.png

    # Complex scene building
    python compose_images.py "Combine these landscape elements into a cohesive scene" sky.png mountains.png lake.png trees.png

Environment variables:
    GEMINI_API_KEY - API key (can override --api-key flag)

Limitations:
    - Maximum 14 reference images
    - Works best with Nano Banana Pro (default model)
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Import shared library
try:
    from gemini_images import NanoBananaProClient
except ImportError:
    print("Error: gemini_images library not found in same directory", file=sys.stderr)
    print("Make sure gemini_images.py is in the scripts/ folder", file=sys.stderr)
    sys.exit(1)


def compose_images(
    instruction: str,
    image_paths: list,
    output_path: str,
    api_key: str,
    aspect_ratio: str = "16:9",
    temperature: float = 0.7,
    verbose: bool = False,
    model: str = None
):
    """
    Compose multiple images based on instructions.

    Args:
        instruction: Text describing how to combine images
        image_paths: List of input image paths
        output_path: Where to save the result
        api_key: API key for authentication
        aspect_ratio: Output aspect ratio
        temperature: Creativity level (0.0-1.0)
        verbose: Show full API response
        model: Model ID (default: gemini-3-pro-image-preview)

    Returns:
        Dictionary with saved file paths
    """
    # Validate all images exist
    for img_path in image_paths:
        if not Path(img_path).exists():
            raise FileNotFoundError(f"Image not found: {img_path}")

    # Initialize client
    client = NanoBananaProClient(api_key, model=model) if model else NanoBananaProClient(api_key)

    print(f"🎨 Composing {len(image_paths)} images with Nano Banana Pro...")
    print(f"   Instruction: {instruction}")
    print(f"   Input images:")
    for idx, img in enumerate(image_paths, 1):
        print(f"     {idx}. {Path(img).name}")
    print(f"   Aspect Ratio: {aspect_ratio}")
    print(f"   Temperature: {temperature}")
    print()

    # Generate composed image
    response = client.compose_images(
        instruction=instruction,
        image_paths=image_paths,
        aspect_ratio=aspect_ratio,
        temperature=temperature
    )

    if verbose:
        print("Full API Response:")
        print(json.dumps(response, indent=2))
        print()

    # Save result
    saved_paths = client.save_response(output_path, response)

    return saved_paths


def main():
    parser = argparse.ArgumentParser(
        description="Compose multiple images using Nano Banana Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Group photo composition
  python compose_images.py "Create a professional group photo" person1.png person2.png person3.png

  # Style transfer (2 images)
  python compose_images.py "Apply the style of image 1 to image 2" style.png photo.png

  # Scene building (multiple elements)
  python compose_images.py "Combine into a cohesive landscape" sky.png mountains.png lake.png

  # Product showcase
  python compose_images.py "Arrange these products in a catalog layout" product1.png product2.png product3.png

  # With custom settings
  python compose_images.py "Create a collage" img1.png img2.png img3.png \\
      --aspect-ratio 1:1 \\
      --temperature 0.9 \\
      --output ./composed.png

Tips:
  - First image often serves as primary reference
  - Be specific about spatial relationships ("on the left", "in the background")
  - Up to 14 images supported
  - Higher temperature (0.8-0.9) for creative interpretations
  - Lower temperature (0.4-0.6) for literal compositions
        """
    )

    parser.add_argument(
        "instruction",
        help="Text instruction describing how to combine the images"
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="Input image paths (2-14 images, space-separated)"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output/composed.png",
        help="Output file path (default: ./output/composed.png)"
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model ID (default: gemini-3-pro-image-preview). "
             "Use gemini-3.1-flash-image-preview for faster/cheaper generation"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use Nano Banana 2 (gemini-3.1-flash-image-preview) for faster generation"
    )
    parser.add_argument(
        "--aspect-ratio", "-a",
        default="16:9",
        choices=["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        help="Output aspect ratio (default: 16:9)"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Creativity level 0.0-1.0 (default: 0.7)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full API response"
    )

    args = parser.parse_args()

    # Validate image count
    if len(args.images) > 14:
        print("❌ Error: Maximum 14 images supported", file=sys.stderr)
        sys.exit(1)

    if len(args.images) < 1:
        print("❌ Error: At least 1 image required", file=sys.stderr)
        sys.exit(1)

    # Get API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: API key required. Use --api-key or set GEMINI_API_KEY environment variable",
              file=sys.stderr)
        sys.exit(1)

    try:
        # Compose images
        model = NanoBananaProClient.FLASH_MODEL if args.fast else args.model
        saved_paths = compose_images(
            instruction=args.instruction,
            image_paths=args.images,
            output_path=args.output,
            api_key=api_key,
            aspect_ratio=args.aspect_ratio,
            temperature=args.temperature,
            verbose=args.verbose,
            model=model
        )

        print()
        print("✅ Success! Composed image created")
        if saved_paths["image"]:
            print(f"   Image: {saved_paths['image']}")
        if saved_paths["text"]:
            print(f"   Text: {saved_paths['text']}")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
