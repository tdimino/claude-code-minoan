#!/usr/bin/env python3
"""
Analyze: Multi-image style analysis for prompting purposes.

Send 2-5 reference images to Gemini for detailed style analysis.
Returns text-only descriptions useful for AI image generation prompting.

Usage:
    # Analyze multiple images for style extraction
    python analyze.py --images ref1.jpg ref2.png ref3.webp --prompt "Describe the shared artistic style"

    # Analyze for specific purpose (avatar generation, etc.)
    python analyze.py --images kathor.webp samantha.jpg yosef.png \
        --prompt "Analyze for prompting fantasy portraits of: Sarah (anxious mother), Michael (father), Priya (cultural expectations)"

    # Use Flash for quick analysis, Pro for thorough
    python analyze.py --images *.jpg --model flash --prompt "Quick style summary"
    python analyze.py --images *.jpg --model pro --prompt "Comprehensive style analysis"

    # Save analysis to file
    python analyze.py --images ref/*.jpg --prompt "Style guide" --output style_guide.md

Environment:
    GEMINI_API_KEY - Required for Gemini API access
"""

import argparse
import base64
import os
import sys
from pathlib import Path
from typing import List

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)


# Model configurations - Gemini 3 (never use Gemini 2)
MODELS = {
    "flash": "gemini-3-flash-preview",
    "pro": "gemini-3-pro-preview",
}

# MIME type mapping
MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def load_image(path: Path) -> dict:
    """Load an image file and return as inline_data dict."""
    suffix = path.suffix.lower()
    mime_type = MIME_TYPES.get(suffix, "image/jpeg")

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return {
        "inline_data": {
            "mime_type": mime_type,
            "data": data
        }
    }


def analyze_images(
    images: List[Path],
    prompt: str,
    model: str = "flash",
    api_key: str = None,
    temperature: float = 0.7
) -> str:
    """
    Send multiple images to Gemini for text-only analysis.

    Args:
        images: List of image file paths (2-5 images)
        prompt: Analysis prompt describing what to extract
        model: "flash" for quick analysis, "pro" for thorough
        api_key: Gemini API key
        temperature: Generation temperature (0.0-1.0)

    Returns:
        Text analysis from Gemini
    """
    if not api_key:
        raise ValueError("GEMINI_API_KEY required")

    if len(images) < 1:
        raise ValueError("At least 1 image required")
    if len(images) > 10:
        raise ValueError("Maximum 10 images supported")

    # Build parts list with all images
    parts = []
    for img_path in images:
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")
        parts.append(load_image(img_path))

    # Add the prompt
    parts.append({"text": prompt})

    # API request
    model_id = MODELS.get(model, MODELS["flash"])
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    payload = {
        "contents": [{
            "parts": parts
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 8192,
            "responseModalities": ["TEXT"]  # Text-only, no image generation
        }
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()

    # Extract text from response
    text = ""
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                text += part["text"]

    return text.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Multi-image style analysis for prompting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze reference images for style extraction
  python analyze.py --images ref1.jpg ref2.png ref3.webp \\
      --prompt "Describe the shared artistic style for AI prompting"

  # Quick analysis with Flash
  python analyze.py --images *.jpg --model flash --prompt "Style summary"

  # Thorough analysis with Pro
  python analyze.py --images *.jpg --model pro --prompt "Comprehensive analysis"

  # Save to file
  python analyze.py --images ref/*.jpg --prompt "Style guide" --output guide.md
        """
    )

    parser.add_argument(
        "--images", "-i",
        nargs="+",
        type=Path,
        required=True,
        help="Image files to analyze (2-10 images)"
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Analysis prompt describing what to extract"
    )
    parser.add_argument(
        "--model", "-m",
        choices=["flash", "pro"],
        default="flash",
        help="Model to use: flash (quick) or pro (thorough)"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Generation temperature (0.0-1.0, default: 0.7)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Save analysis to file"
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API key (or use GEMINI_API_KEY env)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY required. Set environment variable or use --api-key", file=sys.stderr)
        sys.exit(1)

    # Validate images exist
    valid_images = []
    for img in args.images:
        if img.exists():
            valid_images.append(img)
        else:
            print(f"Warning: Image not found, skipping: {img}", file=sys.stderr)

    if not valid_images:
        print("Error: No valid images found", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    print(f"\n{'='*60}")
    print(f"  MULTI-IMAGE ANALYSIS")
    print(f"{'='*60}")
    print(f"\n  Model: {args.model.upper()}")
    print(f"  Images: {len(valid_images)}")
    for img in valid_images:
        print(f"    - {img.name}")
    print(f"\n  Analyzing...\n")

    try:
        result = analyze_images(
            images=valid_images,
            prompt=args.prompt,
            model=args.model,
            api_key=api_key,
            temperature=args.temperature
        )

        print(f"{'='*60}")
        print(f"  ANALYSIS RESULT")
        print(f"{'='*60}\n")
        print(result)
        print()

        # Save to file if requested
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                f.write(f"# Style Analysis\n\n")
                f.write(f"**Images analyzed**: {', '.join(img.name for img in valid_images)}\n\n")
                f.write(f"**Model**: {args.model}\n\n")
                f.write(f"---\n\n")
                f.write(result)
            print(f"  Saved to: {args.output}\n")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
