#!/usr/bin/env python3
"""
Edit images using Nano Banana Pro's multi-turn editing capabilities.

Usage:
    python edit_image.py "edit instruction" input.png --api-key YOUR_KEY [options]

Environment variables:
    GEMINI_API_KEY - API key (can override --api-key flag)
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


class ImageEditor:
    """Client for Nano Banana Pro image editing."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-3-pro-image-preview"
    FLASH_MODEL = "gemini-3.1-flash-image-preview"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self.endpoint = f"{self.BASE_URL}/{model}:generateContent"

    def encode_image(self, image_path: Path) -> tuple:
        """
        Encode image to base64 and determine MIME type.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (base64_data, mime_type)
        """
        # Determine MIME type from extension
        ext_to_mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp"
        }

        ext = image_path.suffix.lower()
        mime_type = ext_to_mime.get(ext, "image/png")

        # Read and encode
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        return image_base64, mime_type

    def edit_image(
        self,
        prompt: str,
        image_path: Path,
        aspect_ratio: str = "16:9",
        temperature: float = 0.7,
        max_output_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Edit an image based on text instructions.

        Args:
            prompt: Text instruction for editing (e.g., "Make the sky blue")
            image_path: Path to input image
            aspect_ratio: Output aspect ratio
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Maximum tokens in response

        Returns:
            API response dictionary containing edited image
        """
        # Encode image
        image_data, mime_type = self.encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_data
                        }
                    }
                ]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
                "imageConfig": {
                    "aspectRatio": aspect_ratio
                }
            }
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=200
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = json.dumps(error_data, indent=2)
            except:
                error_detail = e.response.text

            raise Exception(f"API request failed: {e}\n{error_detail}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    def multi_turn_edit(
        self,
        edits: List[tuple],
        initial_image: Optional[Path] = None,
        aspect_ratio: str = "16:9",
        temperature: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform multiple sequential edits on an image.

        Args:
            edits: List of (prompt, image_path) tuples for each edit step
            initial_image: Optional initial image (if first edit doesn't provide one)
            aspect_ratio: Output aspect ratio
            temperature: Sampling temperature

        Returns:
            List of API responses for each edit
        """
        responses = []
        current_image = initial_image

        for idx, (prompt, image_path) in enumerate(edits, 1):
            if image_path:
                current_image = Path(image_path)

            if not current_image:
                raise ValueError(f"Step {idx}: No image provided and no previous image available")

            print(f"\n🔄 Edit step {idx}/{len(edits)}: {prompt}")

            response = self.edit_image(
                prompt=prompt,
                image_path=current_image,
                aspect_ratio=aspect_ratio,
                temperature=temperature
            )

            responses.append(response)

            # Save intermediate result for next step
            if idx < len(edits):
                # Extract image from response for next iteration
                # (In practice, you'd save it and use the saved path)
                pass

        return responses

    def save_images_from_response(
        self,
        response: Dict[str, Any],
        output_dir: Path,
        base_filename: str = "edited"
    ) -> list:
        """Save images from API response."""
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = []

        try:
            candidates = response.get("candidates", [])

            for candidate_idx, candidate in enumerate(candidates):
                content = candidate.get("content", {})
                parts = content.get("parts", [])

                for part_idx, part in enumerate(parts):
                    # Extract text
                    if "text" in part:
                        text_file = output_dir / f"{base_filename}_response_{candidate_idx}_{part_idx}.txt"
                        with open(text_file, "w") as f:
                            f.write(part["text"])
                        saved_files.append(str(text_file))
                        print(f"✓ Saved text: {text_file}")

                    # Extract images
                    if "inlineData" in part:
                        inline_data = part["inlineData"]
                        image_data = inline_data.get("data", "")
                        mime_type = inline_data.get("mimeType", "image/png")

                        ext_map = {
                            "image/png": "png",
                            "image/jpeg": "jpg",
                            "image/jpg": "jpg",
                            "image/webp": "webp"
                        }
                        ext = ext_map.get(mime_type, "png")

                        image_file = output_dir / f"{base_filename}_image_{candidate_idx}_{part_idx}.{ext}"
                        image_bytes = base64.b64decode(image_data)

                        with open(image_file, "wb") as f:
                            f.write(image_bytes)

                        saved_files.append(str(image_file))
                        print(f"✓ Saved image: {image_file}")

            return saved_files

        except Exception as e:
            raise Exception(f"Failed to save images: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Edit images using Nano Banana Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic editing
  python edit_image.py "Make the sky blue" input.jpg

  # Specific changes
  python edit_image.py "Add flying birds to the background" landscape.png

  # Localized editing
  python edit_image.py "Change the car to red" photo.jpg --aspect-ratio 16:9

  # Creative transforms
  python edit_image.py "Convert to night scene with stars" day.png --temperature 0.9
        """
    )

    parser.add_argument("prompt", help="Text instruction for editing the image")
    parser.add_argument("image", type=Path, help="Path to input image")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--model", default=ImageEditor.DEFAULT_MODEL,
                       help=f"Model ID (default: {ImageEditor.DEFAULT_MODEL}). "
                            f"Use {ImageEditor.FLASH_MODEL} for faster/cheaper editing")
    parser.add_argument("--fast", action="store_true",
                       help=f"Use Nano Banana 2 ({ImageEditor.FLASH_MODEL}) for faster editing")
    parser.add_argument("--aspect-ratio", default="16:9",
                       choices=["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
                       help="Output aspect ratio (default: 16:9)")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="Sampling temperature 0.0-1.0 (default: 0.7)")
    parser.add_argument("--output", default="./output",
                       help="Output directory (default: ./output)")
    parser.add_argument("--filename", default="edited",
                       help="Base filename (default: edited)")
    parser.add_argument("--verbose", action="store_true",
                       help="Show full API response")

    args = parser.parse_args()

    # Validate image exists
    if not args.image.exists():
        print(f"Error: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    # Get API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: API key required. Use --api-key or set GEMINI_API_KEY environment variable",
              file=sys.stderr)
        sys.exit(1)

    # Initialize editor
    model = ImageEditor.FLASH_MODEL if args.fast else args.model
    editor = ImageEditor(api_key, model)

    print(f"✏️  Editing image with Nano Banana Pro...")
    print(f"   Model: {model}")
    print(f"   Input: {args.image}")
    print(f"   Instruction: {args.prompt}")
    print(f"   Aspect Ratio: {args.aspect_ratio}")
    print()

    try:
        # Edit image
        response = editor.edit_image(
            prompt=args.prompt,
            image_path=args.image,
            aspect_ratio=args.aspect_ratio,
            temperature=args.temperature
        )

        if args.verbose:
            print("Full API Response:")
            print(json.dumps(response, indent=2))
            print()

        # Save results
        output_dir = Path(args.output)
        saved_files = editor.save_images_from_response(response, output_dir, args.filename)

        print()
        print(f"✅ Success! Saved {len(saved_files)} file(s)")
        print(f"   Output directory: {output_dir.absolute()}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
