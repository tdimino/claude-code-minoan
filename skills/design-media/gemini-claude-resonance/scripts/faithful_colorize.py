#!/usr/bin/env python3
"""
Faithful Transform: Two-step image transformation that preserves original content.

The Problem:
When directly asking Gemini Dreamer to transform an image (colorize, restore, reimagine),
it often hallucinates - replacing elements, changing compositions, or inventing new figures.
For example, a seal impression with a male votary might become two female attendants.

The Solution (Describe-First Technique):
1. DESCRIBE: Gemini Pro analyzes the image with precision
2. TRANSFORM: Gemini Dreamer transforms using ONLY the verified description

This ensures faithful transformation by grounding Dreamer's generation in Pro's accurate analysis.

COMMANDS:

  describe    - Analyze an image and output detailed description
  colorize    - Two-step faithful colorization
  prompt      - Generate a crafted prompt for Dreamer based on image analysis
  transform   - General two-step transformation with custom instructions

Usage:
    # Just describe an image (analysis only, no generation)
    python faithful_colorize.py describe --image seal.png
    python faithful_colorize.py describe --image seal.png --output description.md

    # Colorize with faithful preservation
    python faithful_colorize.py colorize --image relief.webp --style "Minoan fresco"
    python faithful_colorize.py colorize --image drawing.png --palette "ochre, terracotta, blue"

    # Craft a prompt for Dreamer (outputs text, doesn't generate)
    python faithful_colorize.py prompt --image seal.png --goal "colorize in Egyptian style"
    python faithful_colorize.py prompt --image fresco.jpg --goal "restore to original appearance"

    # General transformation with custom instructions
    python faithful_colorize.py transform --image photo.jpg --instruction "Convert to woodcut print style"

Environment:
    GEMINI_API_KEY - Required for Gemini API access
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Requires requests library. Install: pip install requests", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Models
PRO_MODEL = "gemini-2.0-flash"  # For analysis (fast, accurate)
DREAMER_MODEL = "gemini-2.0-flash-exp-image-generation"  # For image generation

# Default output directory
SCRIPT_DIR = Path(__file__).parent.parent
CANVAS_DIR = SCRIPT_DIR / "canvas" / "faithful"


# ============================================================================
# PROMPTS
# ============================================================================

DESCRIBE_PROMPT = """Describe this image in precise detail for AI image generation.

Analyze and list EVERY element:

1. **FIGURES** (if any):
   - Count, position, pose, attire, gestures
   - Unusual features (skeletal, headless, hybrid, mythological)
   - Skin tones, hair, facial features
   - What they're holding or interacting with

2. **OBJECTS & ARCHITECTURE**:
   - All objects, their placement, and significance
   - Architectural elements (columns, shrines, buildings)
   - Symbols, inscriptions, decorative elements

3. **ENVIRONMENT**:
   - Setting (indoor/outdoor, landscape features)
   - Background elements
   - Ground, sky, vegetation

4. **COMPOSITION & STYLE**:
   - Spatial arrangement (foreground/mid/background)
   - Framing, borders, margins
   - Art style (line drawing, relief, fresco, etc.)
   - Line weight, hatching, shading techniques

5. **CONDITION** (if applicable):
   - Damaged or missing areas
   - Faded or unclear sections
   - Reconstruction vs. original elements

Be EXTREMELY accurate. This description will be used for faithful image transformation.
Any element you miss or misidentify will be wrong in the output."""

DESCRIBE_FOR_GOAL_PROMPT = """Describe this image in precise detail, specifically to support the following transformation goal:

GOAL: {goal}

Analyze the image focusing on elements relevant to this goal. List:

1. **KEY ELEMENTS**: Every figure, object, and feature that must be preserved
2. **COMPOSITION**: Spatial arrangement that must be maintained
3. **STYLE DETAILS**: Artistic elements relevant to the transformation
4. **TRANSFORMATION NOTES**: Specific guidance for achieving the goal while preserving accuracy

Be EXTREMELY accurate. This description will guide faithful transformation."""

CRAFT_PROMPT_TEMPLATE = """Based on this image analysis, craft a detailed prompt for Gemini Dreamer.

=== IMAGE ANALYSIS ===
{description}
=== END ANALYSIS ===

TRANSFORMATION GOAL: {goal}

Create a prompt that:
1. Explicitly lists every element that must appear (from the analysis)
2. Specifies the transformation to apply
3. Includes CRITICAL RULES to prevent hallucination:
   - "Preserve EXACT composition"
   - "Do NOT add, remove, or modify elements"
   - "Every figure/object from description must appear"
4. Suggests appropriate colors/styles for the goal

Output ONLY the crafted prompt, ready to use with Dreamer."""

COLORIZE_TEMPLATE = """Colorize this image EXACTLY as described below. Do NOT add, remove, or modify any elements.

=== VERIFIED DESCRIPTION ===
{description}
=== END DESCRIPTION ===

{style_instructions}

CRITICAL RULES:
1. Preserve the EXACT composition - do not rearrange elements
2. Every figure, object, and detail from the description must appear
3. If the description mentions damaged/ambiguous areas, leave them subtle
4. Maintain all original line work and outlines
5. Use flat colors appropriate to the style (no modern gradients unless specified)
{palette_instructions}"""

TRANSFORM_TEMPLATE = """Transform this image EXACTLY as described below. Preserve all original elements.

=== VERIFIED DESCRIPTION ===
{description}
=== END DESCRIPTION ===

TRANSFORMATION: {instruction}

CRITICAL RULES:
1. Preserve the EXACT composition - do not rearrange elements
2. Every figure, object, and detail from the description must appear in the output
3. Apply the transformation while maintaining accuracy to the original
4. Do NOT add new elements or remove existing ones
5. If areas are ambiguous in the description, keep them subtle in the output"""


# ============================================================================
# API FUNCTIONS
# ============================================================================

def encode_image(image_path: str) -> tuple[str, str]:
    """Encode image to base64 and determine MIME type."""
    path = Path(image_path)
    suffix = path.suffix.lower()

    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
    }

    mime_type = mime_types.get(suffix, 'image/jpeg')

    with open(path, 'rb') as f:
        data = base64.standard_b64encode(f.read()).decode('utf-8')

    return data, mime_type


def call_gemini_text(model: str, prompt: str, image_path: Optional[str] = None) -> str:
    """Call Gemini for text generation (analysis)."""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={GEMINI_API_KEY}"

    parts = [{"text": prompt}]

    if image_path:
        image_data, mime_type = encode_image(image_path)
        parts.insert(0, {
            "inline_data": {
                "mime_type": mime_type,
                "data": image_data
            }
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.3,  # Low temp for accuracy
            "maxOutputTokens": 4096,
        }
    }

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()

    result = response.json()

    if "candidates" not in result or not result["candidates"]:
        raise ValueError(f"No response from Gemini: {result}")

    return result["candidates"][0]["content"]["parts"][0]["text"]


def call_gemini_image(prompt: str, image_path: str, output_path: str) -> str:
    """Call Gemini for image generation."""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    url = f"{GEMINI_API_BASE}/models/{DREAMER_MODEL}:generateContent?key={GEMINI_API_KEY}"

    image_data, mime_type = encode_image(image_path)

    payload = {
        "contents": [{
            "parts": [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_data
                    }
                },
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "temperature": 0.5,
            "responseModalities": ["TEXT", "IMAGE"],
        }
    }

    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()

    result = response.json()

    if "candidates" not in result or not result["candidates"]:
        raise ValueError(f"No response from Gemini: {result}")

    parts = result["candidates"][0]["content"]["parts"]

    for part in parts:
        if "inline_data" in part:
            image_bytes = base64.b64decode(part["inline_data"]["data"])

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)

            with open(output, 'wb') as f:
                f.write(image_bytes)

            return str(output)

    raise ValueError("No image in Gemini response")


# ============================================================================
# COMMANDS
# ============================================================================

def cmd_describe(args):
    """Analyze an image and output detailed description."""
    image_path = Path(args.image).expanduser().resolve()

    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("  DESCRIBE IMAGE")
    print("=" * 60)
    print(f"   Analyzing: {image_path.name}")
    print()

    if args.goal:
        prompt = DESCRIBE_FOR_GOAL_PROMPT.format(goal=args.goal)
    else:
        prompt = DESCRIBE_PROMPT

    description = call_gemini_text(PRO_MODEL, prompt, str(image_path))

    print("=" * 60)
    print("  DESCRIPTION")
    print("=" * 60)
    print()
    print(description)
    print()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(f"# Image Description: {image_path.name}\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            if args.goal:
                f.write(f"Goal: {args.goal}\n")
            f.write(f"\n---\n\n{description}")
        print(f"   Saved to: {output_path}")

    return description


def cmd_prompt(args):
    """Generate a crafted prompt for Dreamer based on image analysis."""
    image_path = Path(args.image).expanduser().resolve()

    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("  CRAFT PROMPT FOR DREAMER")
    print("=" * 60)
    print(f"   Image: {image_path.name}")
    print(f"   Goal: {args.goal}")
    print()

    # Step 1: Describe
    print("   Step 1: Analyzing image...")
    desc_prompt = DESCRIBE_FOR_GOAL_PROMPT.format(goal=args.goal)
    description = call_gemini_text(PRO_MODEL, desc_prompt, str(image_path))

    # Step 2: Craft prompt
    print("   Step 2: Crafting Dreamer prompt...")
    craft_prompt = CRAFT_PROMPT_TEMPLATE.format(
        description=description,
        goal=args.goal
    )
    crafted = call_gemini_text(PRO_MODEL, craft_prompt)

    print()
    print("=" * 60)
    print("  CRAFTED PROMPT FOR DREAMER")
    print("=" * 60)
    print()
    print(crafted)
    print()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(f"# Crafted Prompt for: {image_path.name}\n\n")
            f.write(f"Goal: {args.goal}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"---\n\n## Description\n\n{description}\n\n")
            f.write(f"---\n\n## Crafted Prompt\n\n{crafted}")
        print(f"   Saved to: {output_path}")

    return crafted


def cmd_colorize(args):
    """Two-step faithful colorization."""
    image_path = Path(args.image).expanduser().resolve()

    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    # Generate output path if not specified
    if args.output:
        output_path = Path(args.output)
    else:
        CANVAS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = CANVAS_DIR / f"colorized_{timestamp}.jpg"

    print("=" * 60)
    print("  FAITHFUL COLORIZE")
    print("=" * 60)
    print()

    # Step 1: Describe
    if args.description:
        print("   Using provided description...")
        desc = args.description
    else:
        print("   Step 1: DESCRIBE (analyzing image...)")
        print(f"   Image: {image_path.name}")
        desc = call_gemini_text(PRO_MODEL, DESCRIBE_PROMPT, str(image_path))

        if args.verbose:
            print()
            print("   --- DESCRIPTION ---")
            print(desc)
            print("   --- END ---")
        print()

    # Save description if requested
    if args.save_description:
        save_path = Path(args.save_description)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'w') as f:
            f.write(f"# Description: {image_path.name}\n\n{desc}")
        print(f"   Description saved: {save_path}")

    # Step 2: Colorize
    print("   Step 2: COLORIZE (rendering...)")

    style_instructions = f"\nSTYLE: {args.style}" if args.style else ""
    palette_instructions = f"\nCOLOR PALETTE: {args.palette}" if args.palette else ""

    colorize_prompt = COLORIZE_TEMPLATE.format(
        description=desc,
        style_instructions=style_instructions,
        palette_instructions=palette_instructions
    )

    result_path = call_gemini_image(colorize_prompt, str(image_path), str(output_path))

    print()
    print("=" * 60)
    print(f"  Colorized: {result_path}")
    print("=" * 60)

    return result_path


def cmd_transform(args):
    """General two-step transformation."""
    image_path = Path(args.image).expanduser().resolve()

    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    # Generate output path if not specified
    if args.output:
        output_path = Path(args.output)
    else:
        CANVAS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = CANVAS_DIR / f"transformed_{timestamp}.jpg"

    print("=" * 60)
    print("  FAITHFUL TRANSFORM")
    print("=" * 60)
    print(f"   Instruction: {args.instruction}")
    print()

    # Step 1: Describe
    if args.description:
        print("   Using provided description...")
        desc = args.description
    else:
        print("   Step 1: DESCRIBE (analyzing image...)")
        desc_prompt = DESCRIBE_FOR_GOAL_PROMPT.format(goal=args.instruction)
        desc = call_gemini_text(PRO_MODEL, desc_prompt, str(image_path))

        if args.verbose:
            print()
            print("   --- DESCRIPTION ---")
            print(desc)
            print("   --- END ---")
        print()

    # Step 2: Transform
    print("   Step 2: TRANSFORM (rendering...)")

    transform_prompt = TRANSFORM_TEMPLATE.format(
        description=desc,
        instruction=args.instruction
    )

    result_path = call_gemini_image(transform_prompt, str(image_path), str(output_path))

    print()
    print("=" * 60)
    print(f"  Transformed: {result_path}")
    print("=" * 60)

    return result_path


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Faithful image transformation using describe-first technique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # describe command
    desc_parser = subparsers.add_parser("describe", help="Analyze image and output description")
    desc_parser.add_argument("--image", "-i", required=True, help="Image to analyze")
    desc_parser.add_argument("--goal", "-g", help="Optional goal to focus the analysis")
    desc_parser.add_argument("--output", "-o", help="Save description to file")

    # prompt command
    prompt_parser = subparsers.add_parser("prompt", help="Craft a Dreamer prompt from image")
    prompt_parser.add_argument("--image", "-i", required=True, help="Image to analyze")
    prompt_parser.add_argument("--goal", "-g", required=True, help="Transformation goal")
    prompt_parser.add_argument("--output", "-o", help="Save prompt to file")

    # colorize command
    color_parser = subparsers.add_parser("colorize", help="Two-step faithful colorization")
    color_parser.add_argument("--image", "-i", required=True, help="Image to colorize")
    color_parser.add_argument("--output", "-o", help="Output path")
    color_parser.add_argument("--style", "-s", help="Style instructions")
    color_parser.add_argument("--palette", "-p", help="Color palette")
    color_parser.add_argument("--description", "-d", help="Pre-written description")
    color_parser.add_argument("--save-description", help="Save description to file")
    color_parser.add_argument("--verbose", "-v", action="store_true", help="Show full description")

    # transform command
    trans_parser = subparsers.add_parser("transform", help="General two-step transformation")
    trans_parser.add_argument("--image", "-i", required=True, help="Image to transform")
    trans_parser.add_argument("--instruction", "-n", required=True, help="Transformation instruction")
    trans_parser.add_argument("--output", "-o", help="Output path")
    trans_parser.add_argument("--description", "-d", help="Pre-written description")
    trans_parser.add_argument("--verbose", "-v", action="store_true", help="Show full description")

    args = parser.parse_args()

    if args.command == "describe":
        cmd_describe(args)
    elif args.command == "prompt":
        cmd_prompt(args)
    elif args.command == "colorize":
        cmd_colorize(args)
    elif args.command == "transform":
        cmd_transform(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
