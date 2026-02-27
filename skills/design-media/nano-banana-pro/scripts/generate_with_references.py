#!/usr/bin/env python3
"""
Generate images with style reference images using Gemini 3 Pro Image.

Uses up to 14 reference images to guide style consistency in generated images.
Based on official Gemini API documentation.

Usage:
    python generate_with_references.py "prompt" ref1.png ref2.jpg --output ./out --filename result
    python generate_with_references.py "prompt" ref1.png ref2.jpg --aspect-ratio 1:1 --resolution 2K

Requirements:
    pip install google-genai pillow
"""

import argparse
import base64
import os
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Generate images with style references using Gemini 3 Pro Image"
    )
    parser.add_argument("prompt", help="Text prompt describing the image to generate")
    parser.add_argument("references", nargs="+", help="Reference image paths (up to 14)")
    parser.add_argument("--api-key", help="Gemini API key (or use GEMINI_API_KEY env var)")
    parser.add_argument("--model", default="gemini-3-pro-image-preview",
                       help="Model ID (default: gemini-3-pro-image-preview). "
                            "Use gemini-3.1-flash-image-preview for faster generation")
    parser.add_argument("--fast", action="store_true",
                       help="Use Nano Banana 2 (gemini-3.1-flash-image-preview) for faster generation")
    parser.add_argument("--output", "-o", default="./output", help="Output directory")
    parser.add_argument("--filename", "-f", default="generated", help="Output filename (without extension)")
    parser.add_argument(
        "--aspect-ratio",
        choices=["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        default="1:1",
        help="Output aspect ratio"
    )
    parser.add_argument(
        "--resolution",
        choices=["1K", "2K", "4K"],
        default="2K",
        help="Output resolution"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable or --api-key required")
        sys.exit(1)

    # Validate reference images
    if len(args.references) > 14:
        print("Error: Maximum 14 reference images allowed")
        sys.exit(1)

    ref_paths = []
    for ref in args.references:
        ref_path = Path(ref)
        if not ref_path.exists():
            print(f"Error: Reference image not found: {ref}")
            sys.exit(1)
        ref_paths.append(ref_path)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from google import genai
        from google.genai import types
        from PIL import Image
    except ImportError as e:
        print(f"Error: Missing required package: {e}")
        print("Install with: pip install google-genai pillow")
        sys.exit(1)

    # Configure client
    client = genai.Client(api_key=api_key)

    model = "gemini-3.1-flash-image-preview" if args.fast else args.model
    print(f"🎨 Generating with {len(ref_paths)} reference images...")
    print(f"   Model: {model}")
    print(f"   Aspect Ratio: {args.aspect_ratio}")
    print(f"   Resolution: {args.resolution}")
    if args.verbose:
        print(f"   Prompt: {args.prompt[:100]}...")
        for i, ref in enumerate(ref_paths):
            print(f"   Reference {i+1}: {ref.name}")
    print()

    # Build contents: prompt + reference images
    contents = [args.prompt]
    for ref_path in ref_paths:
        img = Image.open(ref_path)
        contents.append(img)

    # Generate
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
            )
        )
    except Exception as e:
        print(f"❌ API Error: {e}")
        sys.exit(1)

    # Save results
    saved_files = []
    image_count = 0

    # Navigate response structure: response.candidates[0].content.parts
    if not response.candidates:
        print("⚠️ No candidates in response")
        sys.exit(1)

    for candidate in response.candidates:
        if not candidate.content or not candidate.content.parts:
            continue
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                if args.verbose:
                    print(f"Model response: {part.text[:200]}...")
            elif hasattr(part, 'inline_data') and part.inline_data:
                try:
                    # Get image data from inline_data.data
                    image_data = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"
                    ext = "png" if "png" in mime_type else "jpg"
                    output_path = output_dir / f"{args.filename}_{image_count}.{ext}"

                    # Write binary data directly
                    with open(output_path, "wb") as f:
                        f.write(image_data)

                    saved_files.append(output_path)
                    image_count += 1
                except Exception as e:
                    if args.verbose:
                        print(f"Warning: Could not save image part: {e}")

    if saved_files:
        print(f"✅ Success! Generated {len(saved_files)} image(s)")
        for f in saved_files:
            print(f"   Saved: {f}")
    else:
        print("⚠️ No images were generated. The model may have declined the request.")
        if args.verbose:
            print(f"   Response: {response}")


if __name__ == "__main__":
    main()
