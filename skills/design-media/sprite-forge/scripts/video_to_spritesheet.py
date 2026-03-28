#!/usr/bin/env python3
"""Convert a video into a game-ready sprite sheet with atlas metadata.

Extracts frames via ffmpeg, optionally removes backgrounds, resizes to uniform
cell dimensions, and stitches into a sprite sheet with JSON or XML atlas.

Usage:
  python3 video_to_spritesheet.py --input walk.mp4 --fps 12 --cell-size 64x64 --atlas json
  python3 video_to_spritesheet.py --input idle.mp4 --fps 8 --remove-bg rembg --cols 4
  python3 video_to_spritesheet.py --input run.mp4 --start 1.0 --end 3.5 --cell-size 128x128
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)


def extract_frames(video: str, fps: int, start: float, end: float, out_dir: Path) -> list:
    cmd = ["ffmpeg"]
    # Place -ss before -i for fast demuxer-level seeking on large videos
    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", video]
    if end is not None:
        cmd += ["-to", str(end)]
    cmd += ["-vf", f"fps={fps}", str(out_dir / "frame_%04d.png")]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    return sorted(out_dir.glob("frame_*.png"))


def remove_bg_rembg(frames: list):
    for f in frames:
        result = subprocess.run(["rembg", "i", str(f), str(f)],
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f"rembg warning on {f.name}: {result.stderr}", file=sys.stderr)


def remove_bg_chroma(frames: list, color: str):
    chroma_script = Path(__file__).parent / "chroma_key.py"
    for f in frames:
        subprocess.run(["python3", str(chroma_script),
                        "--input", str(f), "--output", str(f),
                        "--color", color, "--despill"],
                       capture_output=True, text=True)


def resize_frames(frames: list, cell_w: int, cell_h: int):
    for f in frames:
        img = Image.open(f).convert("RGBA")
        img = img.resize((cell_w, cell_h), Image.LANCZOS)
        img.save(f)


def main():
    parser = argparse.ArgumentParser(description="Convert video to sprite sheet")
    parser.add_argument("--input", required=True, help="Input video file")
    parser.add_argument("--fps", type=int, default=12, help="Frame extraction rate (default: 12)")
    parser.add_argument("--start", type=float, default=None, help="Start time in seconds")
    parser.add_argument("--end", type=float, default=None, help="End time in seconds")
    parser.add_argument("--cell-size", default="64x64", help="Output frame size WxH (default: 64x64)")
    parser.add_argument("--remove-bg", choices=["rembg", "chroma", "none"], default="none",
                        help="Background removal method")
    parser.add_argument("--chroma-color", default="00FF00", help="Chroma key color (default: 00FF00)")
    parser.add_argument("--cols", type=int, help="Columns in output sheet")
    parser.add_argument("--output", default="spritesheet.png", help="Output file")
    parser.add_argument("--atlas", choices=["json", "xml", "none"], default="json",
                        help="Atlas metadata format")
    parser.add_argument("--keep-frames", action="store_true", help="Keep extracted frames")
    args = parser.parse_args()

    # Check ffmpeg
    if not shutil.which("ffmpeg"):
        print("ffmpeg required but not found in PATH", file=sys.stderr)
        sys.exit(1)

    cell_parts = args.cell_size.lower().split("x")
    cell_w, cell_h = int(cell_parts[0]), int(cell_parts[1])

    # Extract frames to temp dir
    tmp_dir = Path(tempfile.mkdtemp(prefix="sprite_forge_"))
    frames = extract_frames(args.input, args.fps, args.start, args.end, tmp_dir)

    if not frames:
        print("No frames extracted from video", file=sys.stderr)
        sys.exit(1)

    # Remove background
    if args.remove_bg == "rembg":
        remove_bg_rembg(frames)
    elif args.remove_bg == "chroma":
        remove_bg_chroma(frames, args.chroma_color)

    # Resize
    resize_frames(frames, cell_w, cell_h)

    # Stitch via sibling script
    stitch_script = Path(__file__).parent / "stitch_spritesheet.py"
    stitch_cmd = ["python3", str(stitch_script),
                  "--input-dir", str(tmp_dir),
                  "--cell-size", args.cell_size,
                  "--atlas", args.atlas,
                  "-o", args.output]
    if args.cols:
        stitch_cmd += ["--cols", str(args.cols)]

    stitch_ok = False
    result = subprocess.run(stitch_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Stitch error: {result.stderr}", file=sys.stderr)
    else:
        stitch_ok = True
        print(result.stdout.strip())

    # Cleanup
    if not args.keep_frames:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        print(f"Frames kept at {tmp_dir}")

    if not stitch_ok:
        print(f"Extracted {len(frames)} frames but stitching failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
