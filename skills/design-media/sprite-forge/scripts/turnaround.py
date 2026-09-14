#!/usr/bin/env python3
"""8-direction character turnaround (replaces isometric_pipeline.py, March 2026).

Two routes:
  --mode pixel   Retro Diffusion rd_animation__8_dir_rotation (80x80, up to 5 refs, $0.25) ->
                 split -> stitch --atlas v2 --directions 8. One paid call.
  --mode hd      GPT Image 2.5 Sunburst edits (true alpha) or Nano Banana 2 edits (chroma) via
                 gen_image.py: anchor -> 4 cardinals (each an edit of the anchor) -> 4 diagonals
                 (each an edit referencing the anchor + two neighbouring cardinals) -> key ->
                 align_frames (fixes the 16-30 px diagonal scale drift) -> stitch v2. Eight paid edits.

Both routes are dry runs unless --yes. Direction order in the sheet: S, SE, E, NE, N, NW, W, SW.

Usage:
  turnaround.py --mode pixel --prompt "astromech droid, blue and white" --ref droid.png --out ./turn
  turnaround.py --mode hd --anchor anchor.png --desc "astromech droid" --out ./turn --yes
  turnaround.py --mode hd --anchor anchor.png --model fal-ai/nano-banana-2/edit --chroma --out ./turn --yes
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent
ORDER = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
CARDINALS = ["S", "E", "N", "W"]
DIAGONALS = {"SE": ("S", "E"), "NE": ("N", "E"), "NW": ("N", "W"), "SW": ("S", "W")}
FACING = {
    "S": "facing the viewer (front view)",
    "E": "facing right (right side view)",
    "N": "facing away from the viewer (back view)",
    "W": "facing left (left side view)",
    "SE": "facing down-right (front three-quarter, right)",
    "NE": "facing up-right (back three-quarter, right)",
    "NW": "facing up-left (back three-quarter, left)",
    "SW": "facing down-left (front three-quarter, left)",
}
BG_ALPHA = "Transparent background, nothing behind the character."
BG_CHROMA = ("Use an exact flat chroma green background #00FF00 across the entire image, "
             "no gradient, no shadow on the background, no texture, no green spill on the subject.")


def sh(cmd: list[str], dry: bool) -> subprocess.CompletedProcess | None:
    print("  $ " + " ".join(c if " " not in c else repr(c) for c in cmd), file=sys.stderr)
    if dry:
        return None
    r = subprocess.run(cmd, text=True)
    if r.returncode != 0:
        sys.exit(f"step failed ({cmd[1] if len(cmd) > 1 else cmd[0]})")
    return r


def newest_png(d: Path, stem: str) -> Path:
    files = sorted(d.glob(f"{stem}*.png"), key=lambda p: p.stat().st_mtime)
    if not files:
        sys.exit(f"expected an output starting with {stem} in {d}")
    return files[-1]


def cardinal_prompt(desc: str, d: str, bg: str) -> str:
    return (f"Use image 1 as the identity, costume, rendering-style and scale anchor. Redraw the same "
            f"{desc} as a full-body standing idle game sprite, {FACING[d]}, same proportions and same "
            f"height as image 1, feet on the same ground line, centered. {bg} No text, no labels, no borders.")


def diagonal_prompt(desc: str, d: str, bg: str) -> str:
    a, b = DIAGONALS[d]
    return (f"Image 1 is the identity anchor. Image 2 shows the character {FACING[a]}; image 3 shows it "
            f"{FACING[b]}. Draw the same {desc} {FACING[d]}, exactly between those two views, same scale, "
            f"style, proportions and ground line as images 2 and 3. {bg} No text, no labels, no borders.")


def route_pixel(a, out: Path, dry: bool):
    rd = str(SCRIPTS / "retro_diffusion.py")
    cmd = ["python3", rd, "rotate8", "--prompt", a.prompt, "--spritesheet", "--out", str(out / "rd"),
           "--stem", "rotate8"]
    if not a.chroma:
        cmd.append("--remove-bg")
    for r in a.ref or []:
        cmd += ["--ref", r]
    if a.seed is not None:
        cmd += ["--seed", str(a.seed)]
    if not dry:
        cmd.append("--yes")
    sh(cmd, False)   # rotate8 itself dry-runs without --yes, so always execute it
    if dry:
        print("\nDry run: rotate8 cost check above. Next steps would be split -> stitch v2 (free).")
        return
    sheet = newest_png(out / "rd", "rotate8")
    frames = out / "frames"
    sh(["python3", str(SCRIPTS / "split_spritesheet.py"), str(sheet), "--cols", str(a.rd_cols),
        "--output", str(frames)], False)
    if a.chroma:
        for f in sorted(frames.glob("*.png")):
            sh(["python3", str(SCRIPTS / "chroma_key.py"), "--input", str(f), "--output", str(f), "--despill"], False)
    stitch(a, frames, out, "retro_diffusion/rd_animation__8_dir_rotation")


def route_hd(a, out: Path, dry: bool):
    gen = str(SCRIPTS / "gen_image.py")
    bg = BG_CHROMA if a.chroma else BG_ALPHA
    desc = a.desc or "character"
    dirs = out / "dirs"
    dirs.mkdir(parents=True, exist_ok=True)
    anchor = a.anchor
    yes = [] if dry else ["--yes"]
    model = ["--model", a.model] if a.model else []
    transparent = [] if a.chroma else ["--transparent"]

    if not anchor:
        if not a.prompt:
            sys.exit("--mode hd needs --anchor image or --prompt to generate one")
        sh(["python3", gen, "--job", "anchor", "--prompt",
            f"Full-body 2D game sprite of {a.prompt}, neutral standing pose, facing the viewer, centered, "
            f"feet visible, readable silhouette. {bg}", "--out", str(out / "anchor"), "--stem", "anchor"]
           + transparent + yes, False)
        if dry:
            anchor = "<anchor.png>"
        else:
            anchor = str(newest_png(out / "anchor", "anchor"))

    paths: dict[str, str] = {}
    for d in CARDINALS:
        sh(["python3", gen, "--job", "edit", "--prompt", cardinal_prompt(desc, d, bg), "--image", anchor,
            "--out", str(dirs), "--stem", d] + model + transparent + yes, False)
        paths[d] = f"<{d}.png>" if dry else str(newest_png(dirs, d))
    for d, (p, q) in DIAGONALS.items():
        sh(["python3", gen, "--job", "edit", "--prompt", diagonal_prompt(desc, d, bg), "--image", anchor,
            "--image", paths[p], "--image", paths[q], "--out", str(dirs), "--stem", d] + model + transparent + yes, False)
        paths[d] = f"<{d}.png>" if dry else str(newest_png(dirs, d))
    if dry:
        print("\nDry run: 1 anchor (if generated) + 8 edits shown above. Then: chroma key (if --chroma) -> "
              "align_frames -> stitch --atlas v2 --directions 8. Re-run with --yes.")
        return

    ordered = out / "ordered"
    ordered.mkdir(exist_ok=True)
    for i, d in enumerate(ORDER):
        src = Path(paths[d])
        dst = ordered / f"{i}_{d}.png"
        dst.write_bytes(src.read_bytes())
        if a.chroma:
            sh(["python3", str(SCRIPTS / "chroma_key.py"), "--input", str(dst), "--output", str(dst), "--despill"], False)
    aligned = out / "aligned"
    cmd = ["python3", str(SCRIPTS / "align_frames.py"), "--input-dir", str(ordered), "--output-dir", str(aligned),
           "--anchor-x", "center"]
    if a.cell:
        cmd += ["--cell", a.cell]
    sh(cmd, False)
    stitch(a, aligned, out, a.model or "openai/gpt-image-2.5/sunburst/edit")


def stitch(a, frames: Path, out: Path, generator: str):
    cmd = ["python3", str(SCRIPTS / "stitch_spritesheet.py"), "--input-dir", str(frames), "--atlas", "v2",
           "--directions", "8", "--cols", "8", "-o", str(out / "turnaround.png"),
           "--generator", f"sprite-forge/turnaround.py ({generator})", "--aseprite-json"]
    if a.cell:
        cmd += ["--cell-size", a.cell]
    sh(cmd, False)
    print(json.dumps({"sheet": str(out / "turnaround.png"), "manifest": str(out / "turnaround.json"),
                      "order": ORDER}, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mode", choices=("pixel", "hd"), required=True)
    p.add_argument("--prompt", help="subject description (pixel route: required; hd: used to generate an anchor)")
    p.add_argument("--desc", help="hd: short character description used in every edit prompt")
    p.add_argument("--anchor", help="hd: identity anchor image (full body, front view)")
    p.add_argument("--ref", action="append", help="pixel: reference images (<= 5)")
    p.add_argument("--model", help="hd: fal edit endpoint (default openai/gpt-image-2.5/sunburst/edit)")
    p.add_argument("--chroma", action="store_true", help="generate on #00FF00 and key (required for Nano Banana 2)")
    p.add_argument("--cell", help="output cell WxH (default: frame size)")
    p.add_argument("--rd-cols", type=int, default=8, help="pixel: columns in the RD spritesheet (default 8)")
    p.add_argument("--seed", type=int)
    p.add_argument("--out", default="./turnaround")
    p.add_argument("--yes", action="store_true", help="spend credits (default: dry run)")
    a = p.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.mode == "pixel":
        if not a.prompt:
            sys.exit("--mode pixel needs --prompt")
        route_pixel(a, out, not a.yes)
    else:
        route_hd(a, out, not a.yes)


if __name__ == "__main__":
    main()
