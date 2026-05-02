#!/usr/bin/env python3
"""
Generate images using Google's Nano Banana Pro (Gemini 3 Pro Image) API.

Usage:
    python generate_image.py "prompt text" --api-key YOUR_KEY [options]

Environment variables:
    GEMINI_API_KEY - API key (can override --api-key flag)
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


class NanoBananaProClient:
    """Client for Nano Banana Pro (Gemini 3 Pro Image) API."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-3-pro-image-preview"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self.endpoint = f"{self.BASE_URL}/{model}:generateContent"

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
        response_modalities: list = None
    ) -> Dict[str, Any]:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate
            aspect_ratio: Image aspect ratio (1:1, 3:4, 4:3, 9:16, 16:9)
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Maximum tokens in response
            response_modalities: List of modalities (defaults to ["TEXT", "IMAGE"])

        Returns:
            API response dictionary containing generated image data
        """
        if response_modalities is None:
            response_modalities = ["TEXT", "IMAGE"]

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseModalities": response_modalities,
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens
            }
        }

        # Add aspect ratio if generating images
        if "IMAGE" in response_modalities:
            payload["generationConfig"]["imageConfig"] = {
                "aspectRatio": aspect_ratio
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

    def save_images_from_response(
        self,
        response: Dict[str, Any],
        output_dir: Path,
        base_filename: str = "generated",
        debug: bool = False
    ) -> list:
        """
        Extract and save images from API response.

        Args:
            response: API response dictionary
            output_dir: Directory to save images
            base_filename: Base name for saved files
            debug: Print debug information

        Returns:
            List of saved file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = []

        try:
            candidates = response.get("candidates", [])
            if debug:
                print(f"[DEBUG] Found {len(candidates)} candidate(s)")

            for candidate_idx, candidate in enumerate(candidates):
                if debug:
                    print(f"[DEBUG] Processing candidate {candidate_idx}")

                content = candidate.get("content", {})
                parts = content.get("parts", [])

                if debug:
                    print(f"[DEBUG] Found {len(parts)} part(s) in candidate {candidate_idx}")

                for part_idx, part in enumerate(parts):
                    if debug:
                        print(f"[DEBUG] Processing part {part_idx}, keys: {list(part.keys())}")

                    # Extract text responses
                    if "text" in part:
                        try:
                            text_file = output_dir / f"{base_filename}_response_{candidate_idx}_{part_idx}.txt"
                            with open(text_file, "w", encoding="utf-8") as f:
                                f.write(part["text"])
                            saved_files.append(str(text_file))
                            print(f"✓ Saved text response: {text_file}")
                        except Exception as e:
                            print(f"⚠ Warning: Failed to save text response: {e}")
                            if debug:
                                import traceback
                                traceback.print_exc()

                    # Extract images
                    if "inlineData" in part:
                        try:
                            inline_data = part["inlineData"]
                            image_data = inline_data.get("data", "")
                            mime_type = inline_data.get("mimeType", "image/png")

                            if debug:
                                print(f"[DEBUG] Image data length: {len(image_data)} chars")
                                print(f"[DEBUG] MIME type: {mime_type}")

                            # Determine file extension
                            ext_map = {
                                "image/png": "png",
                                "image/jpeg": "jpg",
                                "image/jpg": "jpg",
                                "image/webp": "webp"
                            }
                            ext = ext_map.get(mime_type, "png")

                            image_file = output_dir / f"{base_filename}_image_{candidate_idx}_{part_idx}.{ext}"

                            # Decode and save with better error handling
                            if not image_data:
                                print(f"⚠ Warning: Empty image data for part {part_idx}")
                                continue

                            image_bytes = base64.b64decode(image_data)

                            if debug:
                                print(f"[DEBUG] Decoded {len(image_bytes)} bytes")

                            with open(image_file, "wb") as f:
                                f.write(image_bytes)

                            saved_files.append(str(image_file))
                            print(f"✓ Saved image: {image_file}")

                        except base64.binascii.Error as e:
                            print(f"⚠ Warning: Base64 decode error for part {part_idx}: {e}")
                            if debug:
                                import traceback
                                traceback.print_exc()
                        except IOError as e:
                            print(f"⚠ Warning: File write error for part {part_idx}: {e}")
                            if debug:
                                import traceback
                                traceback.print_exc()
                        except Exception as e:
                            print(f"⚠ Warning: Unexpected error saving image part {part_idx}: {e}")
                            if debug:
                                import traceback
                                traceback.print_exc()

            return saved_files

        except KeyError as e:
            raise Exception(f"Failed to parse response structure: missing key {e}")
        except Exception as e:
            raise Exception(f"Failed to save images: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Nano Banana Pro (Gemini 3 Pro Image)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic generation
  python generate_image.py "A futuristic cityscape at sunset"

  # With custom aspect ratio
  python generate_image.py "Portrait of a cat" --aspect-ratio 9:16

  # Higher creativity
  python generate_image.py "Abstract art" --temperature 0.9

  # Custom output location
  python generate_image.py "Mountain landscape" --output ./my_images --filename mountain
        """
    )

    parser.add_argument("prompt", help="Text prompt describing the image to generate")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--model", default=NanoBananaProClient.DEFAULT_MODEL,
                       help=f"Model to use (default: {NanoBananaProClient.DEFAULT_MODEL})")
    parser.add_argument("--aspect-ratio", default="16:9",
                       choices=["1:1", "3:4", "4:3", "9:16", "16:9"],
                       help="Image aspect ratio (default: 16:9)")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="Sampling temperature 0.0-1.0 (default: 0.7)")
    parser.add_argument("--max-tokens", type=int, default=1024,
                       help="Maximum output tokens (default: 1024)")
    parser.add_argument("--output", default="./output",
                       help="Output directory (default: ./output)")
    parser.add_argument("--filename", default="generated",
                       help="Base filename for saved files (default: generated)")
    parser.add_argument("--verbose", action="store_true",
                       help="Show full API response")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: API key required. Use --api-key or set GEMINI_API_KEY environment variable",
              file=sys.stderr)
        sys.exit(1)

    # Initialize client
    client = NanoBananaProClient(api_key, args.model)

    print(f"🎨 Generating image with Nano Banana Pro...")
    print(f"   Model: {args.model}")
    print(f"   Prompt: {args.prompt}")
    print(f"   Aspect Ratio: {args.aspect_ratio}")
    print()

    try:
        # Generate image
        response = client.generate_image(
            prompt=args.prompt,
            aspect_ratio=args.aspect_ratio,
            temperature=args.temperature,
            max_output_tokens=args.max_tokens
        )

        if args.verbose:
            print("Full API Response:")
            print(json.dumps(response, indent=2))
            print()

        # Save images
        output_dir = Path(args.output)
        saved_files = client.save_images_from_response(
            response,
            output_dir,
            args.filename,
            debug=args.verbose
        )

        print()
        print(f"✅ Success! Generated {len(saved_files)} file(s)")
        print(f"   Output directory: {output_dir.absolute()}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
