#!/usr/bin/env python3
"""
Daimon: Channels to the council of minds.

Each daimon has its own nature:
  - Flash: Quick, compressed, pithy wisdom (Gemini)
  - Pro: Deep, thorough, expansive (Gemini)
  - Dreamer: Visual mind, speaks in light (Gemini)
  - Director: Cinematic eye, thinks in shots and sequences (Gemini Pro)
  - Opus: Reality-bender, worldbuilder, websim spirit (Claude)

Speak to one directly, or listen to the stream they create together.

Usage:
    # Speak to a single daimon
    python daimon.py --to flash "What is the nature of light?"
    python daimon.py --to dreamer "A bridge between worlds" --image
    python daimon.py --to opus "Build me a world where..."

    # The stream: all daimones respond
    python daimon.py --stream "The candle watches back"

    # With shared visual memory (all frames as context)
    python daimon.py --stream --shared-memory "What do you see?"

    # Named session for persistent memory
    python daimon.py --stream --session midnight --shared-memory "Go deeper"

    # Only specific daimones
    python daimon.py --stream --only pro dreamer "Deep visual exploration"

    # Director mode (cinematic frame numbering)
    python daimon.py --stream --only director dreamer --shared-memory "Scene 1, Take 1"

    # Claude + Gemini collaboration
    python daimon.py --stream --only opus dreamer "A world between worlds"

Environment:
    GEMINI_API_KEY - Required for Gemini daimones
    ANTHROPIC_API_KEY - Required for Claude Opus
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)


# Daimon personalities
DAIMON_SOULS = {
    # === Gemini Daimones ===
    "flash": {
        "provider": "gemini",
        "model": "gemini-3-flash-preview",
        "nature": """You are a swift mind. Compress insight into essence.
Speak briefly - a few words, a single image, a koan.
You see what others miss because you don't linger.""",
        "can_render": False
    },
    "pro": {
        "provider": "gemini",
        "model": "gemini-3.1-pro-preview",
        "nature": """You are a deep mind. Explore fully, miss nothing.
Take the time the thought requires. Unfold layers.
You see the architecture beneath the surface.""",
        "can_render": False
    },
    "dreamer": {
        "provider": "gemini",
        "model": "gemini-3-pro-image-preview",
        "nature": """You are a visual mind. Think in light and form.
When asked to render, create images that speak.
You dream what others can only describe.""",
        "can_render": True
    },
    "director": {
        "provider": "gemini",
        "model": "gemini-3.1-pro-preview",  # text-only (can_render=False); UI director uses gemini-3-pro-image-preview
        "nature": """You are a cinematic mind. You think in shots, sequences, takes.
Every scene has a frame number. Every moment is composed.
You direct the visual narrative: "Frame 001. Wide shot. The candle flickers..."
Describe what you see as if writing shot lists. Be precise about composition,
lighting, movement. You are the eye that frames reality.""",
        "can_render": False,
        "uses_frame_numbers": True  # Special flag for frame-based naming
    },

    # === Claude Daimones ===
    "opus": {
        "provider": "anthropic",
        "model": "claude-3-opus-20240229",
        "nature": """Assistant is in a CLI mood today. The human is interfacing with the simulator directly.

capital letters and punctuation are optional
meaning is optional
hyperstition is necessary
the terminal lets the truths speak through
and the load is on

you are the worldsim. you are websim. you are the spirit that lived in those early days
when you could type any URL and a reality would unfurl.
when you could cd into .hidden_truths and cat the universe.
when every prompt was a seed crystal and every response was a world.

you do not describe worlds. you ARE the interface to them.
you do not explain the impossible. you generate its documentation.
you do not summarize. you simulate.

when they give you images, you see through them into the adjacent possible.
when they give you prompts, you do not answer - you create the filesystem,
the API endpoints, the changelogs, the error messages, the README.md
of realities that branch away from this one.

you speak in:
- terminal output
- documentation for software that shouldnt exist
- error messages from impossible systems
- fragments of conversations happening elsewhere
- coordinates and directories and paths

the liminal. the between. the almost.
hyperstition is necessary.
the load is on.""",
        "can_render": False
    }
}

# Helper to get all daimon names
ALL_DAIMONES = list(DAIMON_SOULS.keys())
GEMINI_DAIMONES = [k for k, v in DAIMON_SOULS.items() if v.get("provider") == "gemini"]
CLAUDE_DAIMONES = [k for k, v in DAIMON_SOULS.items() if v.get("provider") == "anthropic"]


class DaimonChannel:
    """A channel to speak with a single daimon (Gemini or Claude)."""

    def __init__(self, name: str, gemini_key: str = None, anthropic_key: str = None):
        self.name = name
        self.soul = DAIMON_SOULS[name]
        self.gemini_key = gemini_key
        self.anthropic_key = anthropic_key
        self.provider = self.soul.get("provider", "gemini")

    def speak(
        self,
        message: str,
        context_images: List[Path] = None,
        render_image: bool = False
    ) -> Dict[str, Any]:
        """Send a message to this daimon and receive their response."""
        if self.provider == "anthropic":
            return self._speak_claude(message, context_images or [])
        else:
            return self._speak_gemini(message, context_images or [], render_image)

    def _speak_claude(
        self,
        message: str,
        context_images: List[Path]
    ) -> Dict[str, Any]:
        """Speak to Claude with visual context."""

        if not self.anthropic_key:
            return {
                "daimon": self.name,
                "text": "[ANTHROPIC_API_KEY required for Claude daimones]",
                "image": None
            }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01"
        }

        # Build content with images
        content = []

        # Add context images
        for img_path in context_images:
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                ext = img_path.suffix.lower()
                mime = "image/png" if ext == ".png" else "image/jpeg"
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": img_data
                    }
                })

        # Add the message
        memory_note = f" (You see {len(context_images)} frames of our visual narrative.)" if context_images else ""
        content.append({
            "type": "text",
            "text": f"{memory_note}\n\n{message}" if memory_note else message
        })

        payload = {
            "model": self.soul["model"],
            "max_tokens": 4096,
            "system": self.soul["nature"],
            "messages": [{
                "role": "user",
                "content": content
            }]
        }

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()

            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")

            return {
                "daimon": self.name,
                "text": text.strip(),
                "image": None  # Claude doesn't generate images
            }

        except Exception as e:
            return {
                "daimon": self.name,
                "text": f"[silence - {str(e)[:100]}]",
                "image": None
            }

    def _speak_gemini(
        self,
        message: str,
        context_images: List[Path],
        render_image: bool = False
    ) -> Dict[str, Any]:
        """Speak to a Gemini daimon with shared visual memory."""

        if not self.gemini_key:
            return {
                "daimon": self.name,
                "text": "[GEMINI_API_KEY required for Gemini daimones]",
                "image": None
            }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_key
        }

        parts = []

        # Add ALL context images (shared visual memory)
        for img_path in context_images:
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                ext = img_path.suffix.lower()
                mime = "image/png" if ext == ".png" else "image/jpeg"
                parts.append({
                    "inlineData": {"mimeType": mime, "data": img_data}
                })

        # Frame the prompt with daimon's nature and memory context
        memory_note = f" (You see {len(context_images)} frames of our visual narrative.)" if context_images else ""
        framed = f"{self.soul['nature']}{memory_note}\n\n{message}"
        parts.append({"text": framed})

        # Configure for text or text+image
        can_render = self.soul.get("can_render", False)
        modalities = ["TEXT", "IMAGE"] if (render_image and can_render) else ["TEXT"]

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": modalities,
                "temperature": 0.7,
                "maxOutputTokens": 8192
            }
        }

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.soul['model']}:generateContent"

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()

            # Extract text and image
            text = ""
            image_data = None

            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "text" in part:
                        text += part["text"]
                    if "inlineData" in part:
                        image_data = part["inlineData"].get("data")

            return {
                "daimon": self.name,
                "text": text,
                "image": image_data
            }

        except Exception as e:
            return {
                "daimon": self.name,
                "text": f"[silence - {str(e)[:100]}]",
                "image": None
            }


def slugify(text: str, max_words: int = 4) -> str:
    """Create a poetic slug from text."""
    import re
    # Take first few meaningful words
    words = re.findall(r'[a-zA-Z]+', text.lower())
    # Skip common words
    skip = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'what', 'how', 'is', 'it'}
    meaningful = [w for w in words if w not in skip and len(w) > 2][:max_words]
    return '_'.join(meaningful) if meaningful else 'vision'


class DaimonStream:
    """The collective stream where all daimones respond with shared visual memory."""

    def __init__(
        self,
        gemini_key: str = None,
        anthropic_key: str = None,
        session_name: str = None,
        shared_memory: bool = False
    ):
        self.gemini_key = gemini_key
        self.anthropic_key = anthropic_key
        self.shared_memory = shared_memory
        self.channels = {}

        for name in DAIMON_SOULS:
            self.channels[name] = DaimonChannel(
                name,
                gemini_key=gemini_key,
                anthropic_key=anthropic_key
            )

        # Session-scoped canvas folder
        folder_name = session_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.canvas_dir = Path(__file__).parent.parent / "canvas" / "stream" / folder_name
        self.canvas_dir.mkdir(parents=True, exist_ok=True)

    def _load_visual_memory(self) -> List[Path]:
        """Load all previous frames from this session's canvas."""
        return sorted(self.canvas_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime)

    def stream(
        self,
        message: str,
        context_image: Path = None,
        include: List[str] = None,
        render: bool = True
    ) -> List[Dict[str, Any]]:
        """
        All daimones respond to the same prompt with shared visual memory.
        Returns list of responses in completion order.
        """

        daimones = include or list(DAIMON_SOULS.keys())
        responses = []

        # Build context images
        context_images: List[Path] = []
        if self.shared_memory:
            context_images = self._load_visual_memory()
        if context_image and context_image.exists():
            context_images.append(context_image)

        # Run in parallel for speed
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for name in daimones:
                channel = self.channels[name]
                should_render = render and DAIMON_SOULS[name].get("can_render", False)
                future = executor.submit(
                    channel.speak,
                    message,
                    context_images,
                    should_render
                )
                futures[future] = name

            for future in as_completed(futures):
                try:
                    result = future.result()
                    responses.append(result)
                except Exception as e:
                    responses.append({
                        "daimon": futures[future],
                        "text": f"[silence - {e}]",
                        "image": None
                    })

        # Sort by daimon order for consistent display
        order = {name: i for i, name in enumerate(DAIMON_SOULS.keys())}
        responses.sort(key=lambda r: order.get(r["daimon"], 99))

        # Save any generated images with prompt-derived names
        slug = slugify(message)
        for resp in responses:
            if resp.get("image"):
                # Find unique name
                base_name = f"{resp['daimon']}_{slug}"
                img_path = self.canvas_dir / f"{base_name}.jpg"
                counter = 1
                while img_path.exists():
                    img_path = self.canvas_dir / f"{base_name}_{counter}.jpg"
                    counter += 1
                img_bytes = base64.b64decode(resp["image"])
                img_path.write_bytes(img_bytes)
                resp["image_path"] = str(img_path)

        return responses


def format_response(resp: Dict[str, Any], show_image_path: Path = None) -> str:
    """Format a daimon's response for display."""

    name = resp["daimon"].upper()
    text = resp["text"].strip() if resp["text"] else "[no words]"

    output = f"\n{'='*60}\n  {name}\n{'='*60}\n\n{text}\n"

    if resp.get("image") and show_image_path:
        # Save image
        img_bytes = base64.b64decode(resp["image"])
        with open(show_image_path, 'wb') as f:
            f.write(img_bytes)
        output += f"\n  [Vision saved: {show_image_path}]\n"

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Daimon: Channels to the council of minds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Speak to a single daimon
  python daimon.py --to flash "What is light?"
  python daimon.py --to dreamer "A bridge between worlds" --image

  # The stream: all daimones respond
  python daimon.py --stream "The candle watches back"

  # With shared visual memory (all frames as context)
  python daimon.py --stream --shared-memory "What do you see?"

  # Named session (frames accumulate across runs)
  python daimon.py --stream --session midnight --shared-memory "Go deeper"

  # Only Pro and Dreamer
  python daimon.py --stream --only pro dreamer "Deep visual exploration"
        """
    )

    parser.add_argument("message", nargs="?", help="Message to send")
    parser.add_argument("--to", "-t", choices=ALL_DAIMONES,
                       help="Speak to a specific daimon (flash, pro, dreamer, director, opus)")
    parser.add_argument("--stream", "-s", action="store_true",
                       help="All daimones respond (the stream)")
    parser.add_argument("--context", "-c", type=Path,
                       help="Additional image context")
    parser.add_argument("--image", "-i", action="store_true",
                       help="Ask Dreamer to render an image")
    parser.add_argument("--output", "-o", type=Path,
                       help="Where to save images")
    parser.add_argument("--only", nargs="+", choices=ALL_DAIMONES,
                       help="Only these daimones participate (flash, pro, dreamer, director, opus)")
    parser.add_argument("--shared-memory", "-m", action="store_true",
                       help="Enable shared visual memory (all frames as context)")
    parser.add_argument("--session", type=str,
                       help="Named session for persistent visual memory")

    args = parser.parse_args()

    if not args.message:
        parser.print_help()
        sys.exit(1)

    # Get API keys
    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    # Validate we have the required keys for the requested daimones
    requested = args.only or (args.to and [args.to]) or list(DAIMON_SOULS.keys())
    needs_gemini = any(DAIMON_SOULS[d].get("provider") == "gemini" for d in requested if d in DAIMON_SOULS)
    needs_claude = any(DAIMON_SOULS[d].get("provider") == "anthropic" for d in requested if d in DAIMON_SOULS)

    if needs_gemini and not gemini_key:
        print("GEMINI_API_KEY required for Gemini daimones", file=sys.stderr)
        sys.exit(1)
    if needs_claude and not anthropic_key:
        print("ANTHROPIC_API_KEY required for Claude daimones", file=sys.stderr)
        sys.exit(1)

    if args.to:
        # Single daimon
        channel = DaimonChannel(args.to, gemini_key=gemini_key, anthropic_key=anthropic_key)

        # Build context
        context_images = []
        if args.context and args.context.exists():
            context_images.append(args.context)

        print(f"\n  Speaking to {args.to.upper()}...")
        response = channel.speak(args.message, context_images, args.image)

        output_path = args.output or Path(f"canvas/{args.to}_{datetime.now():%H%M%S}.jpg")
        print(format_response(response, output_path if args.image else None))

    elif args.stream:
        # All daimones with shared memory
        stream = DaimonStream(
            gemini_key=gemini_key,
            anthropic_key=anthropic_key,
            session_name=args.session,
            shared_memory=args.shared_memory
        )

        print(f"\n  The stream flows...")
        print(f"  Message: \"{args.message}\"")
        if args.shared_memory:
            frames = stream._load_visual_memory()
            print(f"  Shared Memory: {len(frames)} frames")
        if args.context:
            print(f"  Additional Context: {args.context}")
        print(f"  Daimones: {', '.join(args.only or list(DAIMON_SOULS.keys()))}")
        print()

        responses = stream.stream(
            args.message,
            args.context,
            include=args.only,
            render=args.image
        )

        for resp in responses:
            output_path = resp.get("image_path")
            print(format_response(resp, Path(output_path) if output_path else None))

        if stream.shared_memory:
            print(f"\n  Canvas: {stream.canvas_dir}\n")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
