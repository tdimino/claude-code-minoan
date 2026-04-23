#!/usr/bin/env python3
"""
Multi-turn conversational image generation/editing via OpenAI Responses API.
Maintains conversation state across turns for iterative editing.

Usage:
    python converse_image.py [options]              # Interactive REPL
    python converse_image.py "prompt" [options]     # Single-shot then exit

Interactive commands:
    /save [filename]     Save current images
    /action auto|generate|edit   Set action mode
    /model MODEL         Change orchestrator model
    /clear               Reset conversation
    /history             Show conversation history
    /help                Show commands
    /quit                Exit

Env: OPENAI_API_KEY
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from openai_images import GPTAtelierChat, VALID_QUALITIES, VALID_FORMATS


def print_help():
    print("""
Commands:
  /save [filename]           Save images from last response
  /action auto|generate|edit Set generation mode
  /model MODEL               Change orchestrator model
  /clear                     Reset conversation state
  /history                   Show conversation turns
  /help                      Show this help
  /quit                      Exit

Anything else is sent as a prompt to generate/edit images.
Attach images by prefixing paths: @photo.png Make this look vintage
""")


def parse_message(raw: str) -> tuple[str, list[str]]:
    """Extract @image paths from message text."""
    words = raw.split()
    images = []
    text_parts = []
    for w in words:
        if w.startswith("@") and len(w) > 1:
            path = w[1:]
            if Path(path).exists():
                images.append(path)
            else:
                print(f"Warning: file not found, treating as text: {w}", file=sys.stderr)
                text_parts.append(w)
        else:
            text_parts.append(w)
    return " ".join(text_parts), images


def run_interactive(chat: GPTAtelierChat, args):
    action = "auto"
    last_response = None
    output_format = args.output_format

    print("GPT Atelier — Multi-turn image session")
    print(f"Orchestrator: {chat.orchestrator}")
    print("Type /help for commands, /quit to exit\n")

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        if raw == "/quit":
            break
        elif raw == "/help":
            print_help()
            continue
        elif raw == "/clear":
            chat.reset()
            last_response = None
            print("Conversation cleared.")
            continue
        elif raw == "/history":
            for i, h in enumerate(chat.history):
                print(f"  [{i+1}] {h['role']}: {h['message'][:80]}")
            if not chat.history:
                print("  (empty)")
            continue
        elif raw.startswith("/save"):
            if not last_response:
                print("No images to save yet.", file=sys.stderr)
                continue
            parts = raw.split(maxsplit=1)
            fname = parts[1].replace("/", "_").replace("\\", "_") if len(parts) > 1 else "converse"
            saved = chat.save_images(last_response, args.output, fname, output_format)
            for p in saved:
                print(f"Saved: {p}")
            continue
        elif raw.startswith("/action"):
            parts = raw.split()
            if len(parts) > 1 and parts[1] in ("auto", "generate", "edit"):
                action = parts[1]
                print(f"Action set to: {action}")
            else:
                print(f"Current action: {action}  (options: auto, generate, edit)")
            continue
        elif raw.startswith("/model"):
            parts = raw.split()
            if len(parts) > 1:
                chat.orchestrator = parts[1]
                print(f"Orchestrator set to: {chat.orchestrator}")
            else:
                print(f"Current orchestrator: {chat.orchestrator}")
            continue

        message, images = parse_message(raw)
        if not message:
            print("Empty prompt.", file=sys.stderr)
            continue

        print("Generating...", file=sys.stderr)
        try:
            last_response = chat.send(
                message=message,
                image_paths=images if images else None,
                action=action,
                quality=args.quality,
                size=args.size,
                output_format=output_format,
            )
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            continue

        gen_images = chat.extract_images(last_response)
        text = chat.extract_text(last_response)

        if text:
            print(text)
        if gen_images:
            print(f"[{len(gen_images)} image(s) generated — /save to write to disk]")
        elif not text:
            print("[No images generated — the model may have declined or returned text only]",
                  file=sys.stderr)

        if gen_images and args.auto_save:
                saved = chat.save_images(last_response, args.output, "converse", output_format)
                for p in saved:
                    print(f"Auto-saved: {p}")


def run_single(chat: GPTAtelierChat, prompt: str, args):
    message, images = parse_message(prompt)
    print(f"Orchestrator: {chat.orchestrator}", file=sys.stderr)
    print("Generating...", file=sys.stderr)

    try:
        response = chat.send(
            message=message,
            image_paths=images if images else None,
            quality=args.quality,
            size=args.size,
            output_format=args.output_format,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    text = chat.extract_text(response)
    if text:
        print(text)

    saved = chat.save_images(response, args.output, args.filename, args.output_format)
    for p in saved:
        print(f"Saved: {p}")

    if not saved and not text:
        print("No output returned", file=sys.stderr)
        sys.exit(1)

    print(f"Response ID: {response.id}")


def main():
    parser = argparse.ArgumentParser(description="Multi-turn image generation via Responses API")
    parser.add_argument("prompt", nargs="?", help="Single-shot prompt (omit for interactive)")
    parser.add_argument("--orchestrator", default="gpt-5.4", help="Orchestrator model")
    parser.add_argument("--thinking", action="store_true",
                        help="Use gpt-5.4-thinking orchestrator (slower, better composition)")
    parser.add_argument("--pro", action="store_true",
                        help="Use gpt-5.4-pro orchestrator (highest quality, most expensive)")
    parser.add_argument("--size", default=None, help="Image size")
    parser.add_argument("--quality", default="high", choices=VALID_QUALITIES)
    parser.add_argument("--format", dest="output_format", default="png", choices=VALID_FORMATS)
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--filename", default="converse", help="Base filename (single-shot)")
    parser.add_argument("--auto-save", action="store_true", help="Auto-save images each turn")
    parser.add_argument("--api-key", help="API key (or use OPENAI_API_KEY env)")
    args = parser.parse_args()

    if args.thinking:
        args.orchestrator = "gpt-5.4-thinking"
    elif args.pro:
        args.orchestrator = "gpt-5.4-pro"

    try:
        chat = GPTAtelierChat(api_key=args.api_key, orchestrator=args.orchestrator)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.prompt:
        run_single(chat, args.prompt, args)
    else:
        run_interactive(chat, args)


if __name__ == "__main__":
    main()
