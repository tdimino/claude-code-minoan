#!/usr/bin/env python3
"""
Interactive multi-turn image generation and refinement with Nano Banana Pro.

This script provides an interactive CLI for iterative image creation and editing.
Perfect for progressive refinement, exploring variations, and conversational
image development workflows.

Usage:
    python multi_turn_chat.py [--output-dir DIR] [--aspect-ratio RATIO]

Interactive Commands:
    /save [filename]    - Save current image (auto-saves after each generation)
    /load <path>        - Load an existing image into conversation
    /clear              - Start fresh conversation (reset history)
    /history            - Show conversation history
    /help               - Show available commands
    /quit or /exit      - Exit the program

Workflow:
    1. Start chat: python multi_turn_chat.py
    2. Generate initial image: "Create a logo for 'Acme Corp'"
    3. Refine iteratively: "Make the text bolder"
    4. Continue refining: "Add a blue gradient background"
    5. Save manually: /save my_logo.png
    6. Start fresh: /clear

Examples:
    # Logo design workflow
    You: Create a minimalist logo for a coffee shop called 'Daily Grind'
    AI: [generates logo]
    You: Make the text larger and use a darker brown
    AI: [refines logo]
    You: Add a coffee bean icon above the text
    AI: [adds icon]
    You: /save daily_grind_final.png

    # Photo editing workflow
    You: /load vacation_photo.jpg
    You: Make the sky more vibrant and blue
    You: Add some birds flying in the distance
    You: Enhance the colors to make it more dramatic

Environment variables:
    GEMINI_API_KEY - API key (required)
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Import shared library
try:
    from gemini_images import NanoBananaProClient, ImageChat
except ImportError:
    print("Error: gemini_images library not found in same directory", file=sys.stderr)
    print("Make sure gemini_images.py is in the scripts/ folder", file=sys.stderr)
    sys.exit(1)


class InteractiveChat:
    """Interactive CLI for multi-turn image generation."""

    def __init__(
        self,
        api_key: str,
        output_dir: Path,
        aspect_ratio: str = "16:9",
        temperature: float = 0.7,
        model: str = None
    ):
        self.client = NanoBananaProClient(api_key, model=model)
        self.chat = ImageChat(self.client)
        self.output_dir = output_dir
        self.aspect_ratio = aspect_ratio
        self.temperature = temperature
        self.image_counter = 0

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("🎨 Nano Banana Pro - Interactive Image Chat")
        print("=" * 50)
        print(f"   Output directory: {self.output_dir.absolute()}")
        print(f"   Default aspect ratio: {self.aspect_ratio}")
        print(f"   Temperature: {self.temperature}")
        print()
        print("Commands: /save, /load, /clear, /history, /help, /quit")
        print("=" * 50)
        print()

    def run(self):
        """Start the interactive chat loop."""
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Goodbye!")
                break

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                if not self._handle_command(user_input):
                    break  # Exit if command returns False
                continue

            # Process as generation/edit instruction
            try:
                self._process_message(user_input)
            except Exception as e:
                print(f"\n❌ Error: {e}")

    def _handle_command(self, command: str) -> bool:
        """
        Handle slash commands.

        Returns:
            False to exit, True to continue
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd in ["/quit", "/exit", "/q"]:
            print("\n👋 Goodbye!")
            return False

        elif cmd == "/help":
            self._show_help()

        elif cmd == "/save":
            self._save_current(arg)

        elif cmd == "/load":
            if not arg:
                print("❌ Usage: /load <image_path>")
            else:
                self._load_image(arg)

        elif cmd == "/clear":
            self._clear_history()

        elif cmd == "/history":
            self._show_history()

        else:
            print(f"❌ Unknown command: {cmd}")
            print("   Type /help for available commands")

        return True

    def _show_help(self):
        """Show help information."""
        print("\n📖 Available Commands:")
        print("   /save [filename]  - Save current image (optional custom filename)")
        print("   /load <path>      - Load existing image for editing")
        print("   /clear            - Reset conversation and start fresh")
        print("   /history          - Show conversation history")
        print("   /help             - Show this help message")
        print("   /quit or /exit    - Exit the program")
        print()
        print("💡 Tips:")
        print("   - Images auto-save after each generation")
        print("   - Be specific with edit instructions")
        print("   - Use 'Make X more Y' for adjustments")
        print("   - Use 'Add X to Y location' for additions")
        print("   - Chain multiple refinements for best results")

    def _save_current(self, filename: str = None):
        """Save the current image."""
        if not self.chat.history:
            print("❌ No image to save (generate one first)")
            return

        try:
            if filename:
                # Use provided filename
                output_path = self.output_dir / filename
            else:
                # Auto-generate filename
                self.image_counter += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.output_dir / f"image_{timestamp}_{self.image_counter}.png"

            saved = self.chat.save_current(output_path)

            if saved["image"]:
                print(f"✅ Image saved: {saved['image']}")
            if saved["text"]:
                print(f"   Text saved: {saved['text']}")

        except Exception as e:
            print(f"❌ Save failed: {e}")

    def _load_image(self, path: str):
        """Load an existing image."""
        image_path = Path(path)

        if not image_path.exists():
            print(f"❌ Image not found: {path}")
            return

        try:
            self.chat.current_image = image_path
            print(f"✅ Loaded: {image_path.name}")
            print("   You can now describe edits to apply to this image")
        except Exception as e:
            print(f"❌ Load failed: {e}")

    def _clear_history(self):
        """Clear conversation history."""
        self.chat.reset()
        self.image_counter = 0
        print("✅ Conversation cleared. Starting fresh!")

    def _show_history(self):
        """Show conversation history."""
        if not self.chat.history:
            print("📝 No conversation history yet")
            return

        print(f"\n📝 Conversation History ({len(self.chat.history)} messages):")
        print("=" * 50)

        for idx, entry in enumerate(self.chat.history, 1):
            print(f"\n[{idx}] {entry['message']}")
            if entry['image_path']:
                print(f"    With image: {entry['image_path']}")

        print("=" * 50)

    def _process_message(self, message: str):
        """Process a generation/edit message."""
        print("\n🎨 Generating...")

        # Send message
        response = self.chat.send(
            message,
            aspect_ratio=self.aspect_ratio,
            temperature=self.temperature
        )

        # Auto-save
        self.image_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"image_{timestamp}_{self.image_counter}.png"

        saved = self.chat.save_current(output_path)

        # Show result
        print()
        if saved["image"]:
            print(f"✅ Image generated: {saved['image']}")
        else:
            print("⚠️  No image in response")

        # Show any text response
        if saved["text"]:
            try:
                with open(saved["text"], "r") as f:
                    text_content = f.read()
                if text_content.strip():
                    print(f"\n💭 AI: {text_content}")
            except:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Interactive multi-turn image generation with Nano Banana Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example Session:

    $ python multi_turn_chat.py --output-dir ./my_images

    💬 You: Create a logo for a tech startup called 'CloudSync'
    🎨 Generating...
    ✅ Image generated: ./my_images/image_20250123_143022_1.png

    💬 You: Make the text bolder and more modern
    🎨 Generating...
    ✅ Image generated: ./my_images/image_20250123_143045_2.png

    💬 You: Add a subtle cloud icon above the text
    🎨 Generating...
    ✅ Image generated: ./my_images/image_20250123_143109_3.png

    💬 You: /save cloudsync_logo_final.png
    ✅ Image saved: ./my_images/cloudsync_logo_final.png

    💬 You: /quit
    👋 Goodbye!

Tips:
  - Be specific with instructions ("Make the sky more vibrant blue")
  - Chain refinements for best results
  - Use /load to edit existing images
  - Images auto-save - use /save for custom names
  - Use /history to review your conversation
        """
    )

    parser.add_argument(
        "--output-dir", "-o",
        default="./output",
        help="Directory to save generated images (default: ./output)"
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model ID (default: gemini-3-pro-image-preview). "
             "Use gemini-3.1-flash-image-preview for faster generation"
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
        help="Default aspect ratio (default: 16:9)"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Creativity level 0.0-1.0 (default: 0.7)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: API key required. Use --api-key or set GEMINI_API_KEY environment variable",
              file=sys.stderr)
        sys.exit(1)

    try:
        # Resolve model
        model = NanoBananaProClient.FLASH_MODEL if args.fast else args.model

        # Start interactive chat
        chat = InteractiveChat(
            api_key=api_key,
            output_dir=Path(args.output_dir),
            aspect_ratio=args.aspect_ratio,
            temperature=args.temperature,
            model=model
        )
        chat.run()

    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
