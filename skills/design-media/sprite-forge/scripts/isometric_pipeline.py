#!/usr/bin/env python3
"""Orchestrate the chongdashu 7-step isometric turnaround pipeline.

Takes a single reference image and produces an 8-way directional sprite
using the nano-banana-pro or GPT Image editing APIs.

Based on: github.com/chongdashu/vibe-isometric-sprites (Mar 2026)

Usage:
  python3 isometric_pipeline.py --reference portrait.png --output-dir ./iso/
  python3 isometric_pipeline.py --reference char.png --character-desc "pirate with red bandana" --chroma-key
  python3 isometric_pipeline.py --reference char.png --steps cardinals,diagonals
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# --- Prompt Templates ---
# {character_desc} and {bg_instruction} are filled at runtime

FULL_BODY_PROMPT = """Use image 1 as the identity anchor. Create a full-body 2D fantasy RPG game sprite-style \
character cutout of {character_desc}. Show the whole body from head to boots in one neutral standing pose, \
centered, readable silhouette, arms and legs fully visible, feet not cropped. Preserve the character design, \
palette family, and clothing details, simplified into a clean game-ready character asset. {bg_instruction}. \
No text, no extra characters, no cropped limbs, no dramatic perspective."""

ISOMETRIC_ANCHOR_PROMPT = """Use image 1 as identity and costume reference. Transform into a sprite-ready \
classic isometric tactical JRPG unit sprite inspired by late-1990s strategy RPGs. Change pose into a clean \
three-quarter isometric standing idle pose, facing down-right, with compact game-sprite proportions, \
simplified readable forms, crisp silhouette, controlled shading, and clean edge definition suitable for \
sprite extraction and later downscaling. Show full body from head to boots. {bg_instruction}. \
No environment, no text, no frame, no glow, no cast shadow."""

CARDINAL_SHEET_PROMPT = """Use image 1 as identity, costume, rendering-style, and scale anchor. Create a \
single 2x2 character spritesheet showing the same character in four cardinal directions with maximum \
consistency between panels. Layout: top-left=North (facing away), top-right=East (facing right), \
bottom-left=South (facing viewer), bottom-right=West (facing left). Each panel shows full-body standing \
idle in isometric style. {bg_instruction}. No text, no labels, no borders."""

DIAGONAL_SHEET_PROMPT = """Image 1 = cardinal direction sheet reference for character consistency and \
direction logic. Image 2 = isometric identity, rendering style, and diagonal angle anchor. Create a single \
2x2 character spritesheet showing the same character in four diagonal directions with maximum consistency. \
Layout: top-left=NW (back-left diagonal), top-right=NE (back-right diagonal), bottom-left=SW (front-left \
diagonal), bottom-right=SE (front-right diagonal). Match scale, style, proportions, and rendering of the \
cardinal sheet. {bg_instruction}. No text, no labels, no borders."""


def get_bg_instruction(chroma_key: bool) -> str:
    if chroma_key:
        return "Use an exact flat chroma green background #00FF00 across the entire image, with no gradient, no shadows on background, no texture"
    return "Transparent background"


def run_edit(prompt: str, image_path: str, output_path: str, extra_images: list = None) -> bool:
    """Call nano-banana-pro edit_image.py for image-to-image generation."""
    script = os.path.expanduser("~/.claude/skills/nano-banana-pro/scripts/edit_image.py")
    if not os.path.exists(script):
        print(f"nano-banana-pro edit script not found at {script}", file=sys.stderr)
        print("Install the nano-banana-pro skill first.", file=sys.stderr)
        return False

    cmd = ["python3", script, prompt, "--image", str(image_path), "--output", str(output_path)]
    if extra_images:
        for img in extra_images:
            cmd += ["--image", str(img)]

    print(f"  Running: {Path(image_path).name} → {Path(output_path).name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr[:200]}", file=sys.stderr)
        return False
    print(f"  Done: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Isometric 8-way turnaround pipeline")
    parser.add_argument("--reference", required=True, help="Input reference image")
    parser.add_argument("--output-dir", default="./isometric-output", help="Output directory")
    parser.add_argument("--character-desc", default="the same character",
                        help="Character description for prompts")
    parser.add_argument("--chroma-key", action="store_true",
                        help="Use #00FF00 chroma key (recommended for Nano Banana)")
    parser.add_argument("--skip-walk", action="store_true",
                        help="Skip walk cycle video generation (requires Veo 3.1 API access)")
    parser.add_argument("--steps", default="all",
                        help="Comma-separated steps: all,full-body,anchor,cardinals,diagonals")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    bg = get_bg_instruction(args.chroma_key)
    steps = args.steps.split(",") if args.steps != "all" else ["full-body", "anchor", "cardinals", "diagonals"]

    ref = args.reference
    print(f"Isometric Pipeline: {ref} → {out}/")
    print(f"  Chroma key: {args.chroma_key}")
    print(f"  Steps: {steps}")
    print()

    # Step 1: Full-body asset
    full_body = out / "step1_full_body.png"
    if "full-body" in steps:
        print("Step 1: Reference → Full-body asset")
        prompt = FULL_BODY_PROMPT.format(character_desc=args.character_desc, bg_instruction=bg)
        if not run_edit(prompt, ref, str(full_body)):
            print("Step 1 failed. Continuing with reference image.", file=sys.stderr)
            full_body = Path(ref)
    elif full_body.exists():
        print("Step 1: Using existing full-body asset")
    else:
        full_body = Path(ref)

    # Step 2: Isometric anchor
    anchor = out / "step2_isometric_anchor.png"
    if "anchor" in steps:
        print("\nStep 2: Full-body → Isometric anchor")
        prompt = ISOMETRIC_ANCHOR_PROMPT.format(bg_instruction=bg)
        if not run_edit(prompt, str(full_body), str(anchor)):
            print("Step 2 failed.", file=sys.stderr)
            return
    elif not anchor.exists():
        anchor = full_body

    # Step 3: Cardinal directions (N/E/S/W)
    cardinals = out / "step3_cardinals_2x2.png"
    if "cardinals" in steps:
        print("\nStep 3: Anchor → 4 Cardinal directions (2x2 sheet)")
        prompt = CARDINAL_SHEET_PROMPT.format(bg_instruction=bg)
        if not run_edit(prompt, str(anchor), str(cardinals)):
            print("Step 3 failed.", file=sys.stderr)
            return

    # Step 4: Diagonal directions (NE/NW/SE/SW)
    diagonals = out / "step4_diagonals_2x2.png"
    if "diagonals" in steps:
        print("\nStep 4: Anchor + Cardinals → 4 Diagonal directions (2x2 sheet)")
        prompt = DIAGONAL_SHEET_PROMPT.format(bg_instruction=bg)
        if cardinals.exists():
            if not run_edit(prompt, str(cardinals), str(diagonals), extra_images=[str(anchor)]):
                print("Step 4 failed.", file=sys.stderr)
                return
        else:
            print("  No cardinal sheet found, using anchor only", file=sys.stderr)
            if not run_edit(prompt, str(anchor), str(diagonals)):
                print("Step 4 failed.", file=sys.stderr)
                return

    # Step 5: Chroma key removal (if applicable)
    if args.chroma_key:
        print("\nStep 5: Removing chroma key backgrounds")
        chroma_script = Path(__file__).parent / "chroma_key.py"
        for img in [cardinals, diagonals]:
            if img.exists():
                alpha_path = img.with_name(img.stem + "_alpha.png")
                result = subprocess.run(["python3", str(chroma_script),
                                "--input", str(img), "--output", str(alpha_path),
                                "--despill"], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"  Warning: chroma key failed for {img.name}: {result.stderr[:100]}", file=sys.stderr)
                else:
                    print(f"  {img.name} → {alpha_path.name}")

    print(f"\nPipeline complete. Outputs in {out}/")
    print("Next steps:")
    print("  - Split 2x2 sheets into individual direction frames")
    print("  - Normalize frame sizes (cardinals and diagonals may have scale drift)")
    print("  - Stitch all 8 directions into final sprite sheet")
    print("  - Optionally generate walk cycle via video model (Veo 3.1)")


if __name__ == "__main__":
    main()
