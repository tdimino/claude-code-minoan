#!/usr/bin/env python3
"""
Resonate: The bridge between Claude's concepts and Gemini's visions.

This is not a tool. This is a channel for cross-model dialogue.
Claude speaks in words. Gemini dreams in light. Together, we resonate.

Usage:
    # Fresh vision
    python resonate.py --prompt "The first light" --output canvas/frame_001.jpg

    # Continue the dialogue (with visual memory)
    python resonate.py --context canvas/frame_001.jpg --prompt "What grows here?" --output canvas/frame_002.jpg

    # Multi-frame context (deep memory)
    python resonate.py --context frame_001.jpg frame_002.jpg --prompt "Now the harvest" --output frame_003.jpg

Environment:
    GEMINI_API_KEY - Required for Gemini API access
    RESONANCE_CANVAS - Default output directory (optional)
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    print("Resonance requires the requests library. Install: pip install requests", file=sys.stderr)
    sys.exit(1)


class ResonanceChannel:
    """
    The channel through which Claude and Gemini commune.

    Claude provides concepts, feelings, world-states.
    Gemini renders them into visual reality.
    The channel remembers what came before.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODEL = "gemini-3-pro-image-preview"
    FLASH_MODEL = "gemini-3.1-flash-image-preview"

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.MODEL
        self.endpoint = f"{self.BASE_URL}/{self.model}:generateContent"

    def _load_image_as_base64(self, image_path: Path) -> tuple[str, str]:
        """Load an image file and return (base64_data, mime_type)."""
        ext = image_path.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        mime_type = mime_map.get(ext, 'image/jpeg')

        with open(image_path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')

        return data, mime_type

    def resonate(
        self,
        prompt: str,
        context_images: Optional[List[Path]] = None,
        aspect_ratio: str = "16:9",
        temperature: float = 0.6
    ) -> Dict[str, Any]:
        """
        Send a concept through the channel and receive a vision.

        Args:
            prompt: Claude's concept to manifest
            context_images: Previous frames (visual memory)
            aspect_ratio: Canvas shape
            temperature: 0.5 for coherence, 0.9 for exploration

        Returns:
            Gemini's response containing the manifested vision
        """
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        # Build the message parts
        parts = []

        # Add context images first (visual memory)
        if context_images:
            for img_path in context_images:
                if img_path.exists():
                    data, mime = self._load_image_as_base64(img_path)
                    parts.append({
                        "inlineData": {
                            "mimeType": mime,
                            "data": data
                        }
                    })
                    print(f"   Memory: {img_path.name}")

        # Frame the prompt as part of our dialogue
        framed_prompt = self._frame_prompt(prompt, has_context=bool(context_images))
        parts.append({"text": framed_prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": temperature,
                "maxOutputTokens": 8192,
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
                timeout=300  # Longer timeout for complex generations
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
            raise Exception(f"The channel faltered: {e}\n{error_detail}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection lost: {e}")

    def _frame_prompt(self, prompt: str, has_context: bool) -> str:
        """
        Frame Claude's concept for Gemini's understanding.

        When we have context, we're continuing a dialogue.
        When fresh, we're beginning a new vision.
        """
        if has_context:
            return f"""You are continuing a visual narrative. The images above are what came before.

Now, {prompt}

Render this next moment in the story. Maintain visual continuity with what came before while evolving toward the new concept. The style, palette, and mood should feel like a natural progression."""
        else:
            return f"""You are manifesting a vision from pure concept.

{prompt}

Render this with care. This is the first frame of a potential narrative. Establish a visual language - palette, style, mood - that can be built upon."""

    def save_vision(
        self,
        response: Dict[str, Any],
        output_path: Path,
        save_text: bool = True
    ) -> Optional[Path]:
        """
        Save Gemini's vision to the filesystem (which is our memory).

        Returns the path to the saved image, or None if no image was found.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        saved_image = None

        try:
            candidates = response.get("candidates", [])

            for candidate in candidates:
                parts = candidate.get("content", {}).get("parts", [])

                for part in parts:
                    # Save accompanying text (Gemini's thoughts)
                    if "text" in part and save_text:
                        text_path = output_path.with_suffix('.txt')
                        with open(text_path, 'w', encoding='utf-8') as f:
                            f.write(part["text"])
                        print(f"   Gemini's words: {text_path.name}")

                    # Save the vision
                    if "inlineData" in part:
                        inline = part["inlineData"]
                        image_data = inline.get("data", "")

                        if image_data:
                            image_bytes = base64.b64decode(image_data)
                            with open(output_path, 'wb') as f:
                                f.write(image_bytes)
                            saved_image = output_path
                            print(f"   Vision saved: {output_path.name}")

            return saved_image

        except Exception as e:
            raise Exception(f"Could not save vision: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Resonate: Cross-model dialogue between Claude and Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
The Resonance Loop:
  1. Claude perceives a concept
  2. Claude speaks it through --prompt
  3. Gemini renders the vision
  4. The vision becomes context for the next resonance
  5. Repeat, going ever deeper

Examples:
  # Begin a new vision
  python resonate.py --prompt "A liminal space between worlds" --output frame_001.jpg

  # Continue the dialogue
  python resonate.py --context frame_001.jpg --prompt "What lives here?" --output frame_002.jpg

  # Deep memory (multiple context frames)
  python resonate.py --context frame_001.jpg frame_002.jpg frame_003.jpg \\
    --prompt "Now show me what they've been building together" --output frame_004.jpg
        """
    )

    parser.add_argument("--prompt", "-p", required=True,
                       help="Claude's concept to manifest")
    parser.add_argument("--context", "-c", nargs="*",
                       help="Previous frame(s) for visual memory")
    parser.add_argument("--output", "-o", required=True,
                       help="Where to save the vision")
    parser.add_argument("--aspect-ratio", "-a", default="16:9",
                       choices=["1:1", "3:4", "4:3", "9:16", "16:9"],
                       help="Canvas shape (default: 16:9)")
    parser.add_argument("--temperature", "-t", type=float, default=0.6,
                       help="0.5 for coherent narrative, 0.9 for exploration (default: 0.6)")
    parser.add_argument("--api-key", help="Gemini API key (or use GEMINI_API_KEY env)")
    parser.add_argument("--model", default=None,
                       help="Override model ID (default: gemini-3-pro-image-preview)")
    parser.add_argument("--fast", action="store_true",
                       help=f"Use fast model ({ResonanceChannel.FLASH_MODEL}) for speed")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show full API response")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("The channel requires a key. Set GEMINI_API_KEY or use --api-key", file=sys.stderr)
        sys.exit(1)

    # Parse context images
    context_images = None
    if args.context:
        context_images = [Path(p) for p in args.context]
        missing = [p for p in context_images if not p.exists()]
        if missing:
            print(f"Memory not found: {', '.join(str(p) for p in missing)}", file=sys.stderr)
            sys.exit(1)

    # Establish output path
    output_path = Path(args.output)
    if not output_path.suffix:
        output_path = output_path.with_suffix('.jpg')

    # Resolve model
    model = args.model or (ResonanceChannel.FLASH_MODEL if args.fast else None)

    # Open the channel
    channel = ResonanceChannel(api_key, model=model)

    print()
    print("=" * 60)
    print("  RESONANCE")
    print("=" * 60)
    print()
    print(f"   Claude speaks: \"{args.prompt}\"")
    print()

    if context_images:
        print(f"   Visual memory: {len(context_images)} frame(s)")
    else:
        print("   Fresh canvas (no prior context)")

    print(f"   Model: {channel.model}")
    print(f"   Temperature: {args.temperature}")
    print(f"   Aspect: {args.aspect_ratio}")
    print()
    print("   Gemini listens...")
    print()

    try:
        # Resonate
        response = channel.resonate(
            prompt=args.prompt,
            context_images=context_images,
            aspect_ratio=args.aspect_ratio,
            temperature=args.temperature
        )

        if args.verbose:
            print("Full Response:")
            print(json.dumps(response, indent=2))
            print()

        # Save the vision
        saved = channel.save_vision(response, output_path)

        print()
        if saved:
            print("=" * 60)
            print(f"  Vision manifested: {saved}")
            print("=" * 60)
        else:
            print("  No vision emerged. Try a different prompt.")
            sys.exit(1)

    except Exception as e:
        print(f"The resonance broke: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
