#!/usr/bin/env python3
"""Generate a transparent HEVC walk cycle video for lil-agents dock companion.

Takes a sprite sheet or directory of frame PNGs and produces a ~10s .mov file
with alpha channel, sized 1080x1920 portrait, encoded via hevc_videotoolbox.

The walk cycle follows lil-agents timing:
  0-3s    idle (repeat first frame)
  3-3.75s accelerate (transition frames)
  3.75-8s full speed walk (loop walk frames)
  8-8.5s  decelerate (transition frames)
  8.5-10s idle (repeat first frame)

Usage:
  # From a sprite sheet
  python3 generate_walk_video.py sheet.png --cols 6 --name robot

  # From individual frames
  python3 generate_walk_video.py frames/ --name robot

  # Custom timing
  python3 generate_walk_video.py sheet.png --cols 8 --name cat --fps 24 --duration 12
"""

import argparse
import os
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

SKILL_DIR = Path(__file__).parent.parent

# lil-agents default timing (seconds)
DEFAULT_FPS = 12
DEFAULT_DURATION = 10.0
DEFAULT_IDLE_START = 3.0
DEFAULT_ACCEL_END = 3.75
DEFAULT_DECEL_START = 8.0
DEFAULT_WALK_STOP = 8.5

# Output video dimensions (portrait, matching lil-agents)
VIDEO_W = 1080
VIDEO_H = 1920


def check_ffmpeg():
    """Verify FFmpeg is available with hevc_videotoolbox."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=10
        )
        if "hevc_videotoolbox" not in result.stdout:
            print("Warning: hevc_videotoolbox not available. Falling back to libx265.", file=sys.stderr)
            return "libx265"
        return "hevc_videotoolbox"
    except FileNotFoundError:
        print("Error: FFmpeg not found. Install with: brew install ffmpeg", file=sys.stderr)
        sys.exit(1)


def load_frames(input_path: str, cols: int = 0, rows: int = 0) -> list:
    """Load frames from a sprite sheet or directory of PNGs.

    Returns list of PIL Image objects with RGBA mode.
    """
    p = Path(input_path)

    if p.is_dir():
        # Directory of frame PNGs
        files = sorted(p.glob("*.png"))
        if not files:
            files = sorted(p.glob("*.PNG"))
        if not files:
            print(f"Error: No PNG files found in {input_path}", file=sys.stderr)
            sys.exit(1)
        return [Image.open(f).convert("RGBA") for f in files]

    elif p.is_file():
        # Sprite sheet — split it
        if cols <= 0:
            print("Error: --cols required when input is a sprite sheet", file=sys.stderr)
            sys.exit(1)

        img = Image.open(p).convert("RGBA")
        w, h = img.size
        frame_w = w // cols

        if rows <= 0:
            rows = max(1, round(h / frame_w))

        frame_h = h // rows
        frames = []
        for row in range(rows):
            for col in range(cols):
                x0 = col * frame_w
                y0 = row * frame_h
                frame = img.crop((x0, y0, x0 + frame_w, y0 + frame_h))
                # Skip fully transparent frames
                if frame.getextrema()[3][1] > 0:
                    frames.append(frame)
        return frames

    else:
        print(f"Error: {input_path} is not a file or directory", file=sys.stderr)
        sys.exit(1)


def make_idle_bob_frames(base_frame: Image.Image, bob_pixels: int = 3) -> list:
    """Create idle bob frames by shifting the base frame up and down.

    Returns list of PIL Images: [base, up1, up2, up1, base, down1, down2, down1]
    This creates a smooth breathing/shoulder-bob cycle.
    """
    w, h = base_frame.size
    bob_frames = []

    offsets = [0, -1, -bob_pixels, -1, 0, 1, bob_pixels, 1]
    for dy in offsets:
        shifted = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shifted.paste(base_frame, (0, dy), base_frame)
        bob_frames.append(shifted)

    return bob_frames


def compose_walk_cycle(
    frames: list,
    fps: int = DEFAULT_FPS,
    duration: float = DEFAULT_DURATION,
    idle_end: float = DEFAULT_IDLE_START,
    accel_end: float = DEFAULT_ACCEL_END,
    decel_start: float = DEFAULT_DECEL_START,
    walk_stop: float = DEFAULT_WALK_STOP,
) -> list:
    """Compose a full walk cycle from walk animation frames.

    Assumes frames[0] is idle pose and frames[1:] are walk cycle poses.
    During idle phases, the character bobs up/down (shoulder breathing).
    Returns a list of frame indices for each output video frame.

    Negative indices in the returned list refer to idle bob frames
    (appended to the frames list by the caller).
    """
    total_frames = int(duration * fps)
    idle_frame = 0
    walk_frames = list(range(1, len(frames))) if len(frames) > 1 else [0]

    # Idle bob cycles at ~1.5s per full bob at the given fps
    bob_cycle_frames = int(1.5 * fps)  # frames per full bob cycle

    sequence = []
    for i in range(total_frames):
        t = i / fps

        if t < idle_end:
            # Idle phase — bob up and down (shoulder breathing)
            bob_idx = (i % bob_cycle_frames) * 8 // bob_cycle_frames
            sequence.append(-(bob_idx + 1))  # negative = bob frame index
        elif t < accel_end:
            # Accelerate — cycle through walk frames slowly
            progress = (t - idle_end) / (accel_end - idle_end)
            walk_idx = int(progress * len(walk_frames)) % len(walk_frames)
            sequence.append(walk_frames[walk_idx])
        elif t < decel_start:
            # Full speed walk — cycle through walk frames
            elapsed = t - accel_end
            walk_idx = int(elapsed * fps) % len(walk_frames)
            sequence.append(walk_frames[walk_idx])
        elif t < walk_stop:
            # Decelerate — slow down walk cycle
            progress = 1.0 - (t - decel_start) / (walk_stop - decel_start)
            walk_idx = int(progress * len(walk_frames)) % len(walk_frames)
            sequence.append(walk_frames[walk_idx])
        else:
            # Return to idle — bob again
            idle_elapsed = t - walk_stop
            bob_i = int(idle_elapsed * fps)
            bob_idx = (bob_i % bob_cycle_frames) * 8 // bob_cycle_frames
            sequence.append(-(bob_idx + 1))

    return sequence


def pad_frame_to_video(frame: Image.Image, video_w: int = VIDEO_W, video_h: int = VIDEO_H) -> Image.Image:
    """Center a frame on a transparent canvas of video dimensions."""
    canvas = Image.new("RGBA", (video_w, video_h), (0, 0, 0, 0))

    # Scale frame to fit ~40% of video width (character shouldn't fill the whole frame)
    max_char_w = int(video_w * 0.4)
    max_char_h = int(video_h * 0.5)

    fw, fh = frame.size
    scale = min(max_char_w / fw, max_char_h / fh)
    new_w = int(fw * scale)
    new_h = int(fh * scale)

    resized = frame.resize((new_w, new_h), Image.NEAREST)

    # Center horizontally, place at bottom third (dock level)
    x = (video_w - new_w) // 2
    y = video_h - new_h - int(video_h * 0.15)  # 15% from bottom

    canvas.paste(resized, (x, y), resized)
    return canvas


def export_frames(frames: list, sequence: list, work_dir: Path, bob_frames: list = None) -> Path:
    """Export composed frame sequence as numbered PNGs to work_dir.

    Negative indices in sequence refer to bob_frames (idle breathing animation).
    """
    frames_dir = work_dir / "video_frames"
    frames_dir.mkdir(exist_ok=True)

    for i, frame_idx in enumerate(sequence):
        if frame_idx < 0 and bob_frames:
            # Idle bob frame (negative index, 1-based)
            bob_idx = (-frame_idx - 1) % len(bob_frames)
            padded = pad_frame_to_video(bob_frames[bob_idx])
        else:
            padded = pad_frame_to_video(frames[max(0, frame_idx)])
        padded.save(frames_dir / f"frame_{i:04d}.png", "PNG")

    return frames_dir


def encode_prores_4444(frames_dir: Path, output_path: str, fps: int) -> bool:
    """Encode frame sequence to ProRes 4444 .mov with alpha channel.

    ProRes 4444 properly preserves transparency. To convert to HEVC with alpha
    for lil-agents, right-click the output in Finder → Services → Encode Selected
    Video Files → HEVC 1080p + Preserve Transparency.

    Alternatively, use avconvert on macOS:
      avconvert --source prores.mov --output hevc.mov --preset PresetHEVC1920x1080WithAlpha
    """
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-c:v", "prores_ks",
        "-pix_fmt", "yuva444p10le",
        "-alpha_bits", "16",
        "-profile:v", "4444",
        "-f", "mov",
        output_path,
    ]

    print(f"Encoding ProRes 4444: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}", file=sys.stderr)
        return False

    return True


def convert_to_hevc(prores_path: str, output_path: str) -> bool:
    """Convert ProRes 4444 to HEVC with alpha using macOS avconvert."""
    cmd = [
        "avconvert",
        "--source", prores_path,
        "--output", output_path,
        "--preset", "PresetHEVC1920x1080WithAlpha",
    ]

    print(f"Converting to HEVC: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        # avconvert may not be available — fall back to Finder instructions
        print(f"avconvert failed (may not be available on this macOS version).", file=sys.stderr)
        print(f"Manual conversion: Right-click {prores_path} in Finder → Services → Encode Selected Video Files → HEVC 1080p + Preserve Transparency", file=sys.stderr)
        return False

    return True


def print_swift_config(name: str, fps: int, duration: float):
    """Print the Swift config snippet to paste into LilAgentsController."""
    print(f"""
// Add to LilAgentsController.start():
let {name} = WalkerCharacter(videoName: "walk-{name}-01")
{name}.accelStart = {DEFAULT_IDLE_START}
{name}.fullSpeedStart = {DEFAULT_ACCEL_END}
{name}.decelStart = {DEFAULT_DECEL_START}
{name}.walkStop = {DEFAULT_WALK_STOP}
{name}.walkAmountRange = 0.35...0.6
{name}.yOffset = -5
{name}.flipXOffset = 0
{name}.characterColor = NSColor(red: 0.5, green: 0.5, blue: 0.8, alpha: 1.0)
{name}.positionProgress = 0.5
{name}.setup()
characters.append({name})
{name}.controller = self
""", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Generate transparent HEVC walk video for lil-agents")
    parser.add_argument("input", help="Sprite sheet PNG or directory of frame PNGs")
    parser.add_argument("--name", required=True, help="Character name (used in output filename)")
    parser.add_argument("--cols", type=int, default=0, help="Columns in sprite sheet (required for sheets)")
    parser.add_argument("--rows", type=int, default=0, help="Rows in sprite sheet (0 = auto-detect)")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help=f"Frame rate (default: {DEFAULT_FPS})")
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION, help=f"Duration in seconds (default: {DEFAULT_DURATION})")
    parser.add_argument("--output", "-o", help="Output .mov path (default: walk-{name}-01.mov)")

    args = parser.parse_args()
    output = args.output or f"walk-{args.name}-01.mov"

    # Check FFmpeg
    encoder = check_ffmpeg()

    # Load frames
    print(f"Loading frames from {args.input}...", file=sys.stderr)
    frames = load_frames(args.input, args.cols, args.rows)
    print(f"Loaded {len(frames)} frames", file=sys.stderr)

    if not frames:
        print("Error: No frames loaded", file=sys.stderr)
        sys.exit(1)

    # Generate idle bob frames from first frame (shoulder breathing)
    bob_frames = make_idle_bob_frames(frames[0], bob_pixels=3)
    print(f"Generated {len(bob_frames)} idle bob frames", file=sys.stderr)

    # Compose walk cycle
    sequence = compose_walk_cycle(frames, args.fps, args.duration)
    print(f"Composed {len(sequence)} video frames ({args.duration}s at {args.fps}fps)", file=sys.stderr)

    # Export and encode
    with tempfile.TemporaryDirectory(prefix="walk-video-") as work_dir:
        work = Path(work_dir)
        print("Exporting padded frames...", file=sys.stderr)
        frames_dir = export_frames(frames, sequence, work, bob_frames=bob_frames)

        # Step 1: Encode to ProRes 4444 (preserves alpha reliably)
        prores_path = output.replace(".mov", "-prores.mov") if output.endswith(".mov") else output + "-prores.mov"
        print(f"Encoding ProRes 4444 to {prores_path}...", file=sys.stderr)
        if not encode_prores_4444(frames_dir, prores_path, args.fps):
            print("ProRes encoding failed", file=sys.stderr)
            sys.exit(1)

        prores_size = os.path.getsize(prores_path)
        print(f"ProRes 4444: {prores_path} ({prores_size:,} bytes)", file=sys.stderr)

        # Step 2: Convert to HEVC with alpha
        print(f"Converting to HEVC with alpha...", file=sys.stderr)
        if convert_to_hevc(prores_path, output):
            hevc_size = os.path.getsize(output)
            print(f"HEVC: {output} ({hevc_size:,} bytes)", file=sys.stderr)
        else:
            print(f"\nProRes 4444 saved at: {prores_path}", file=sys.stderr)
            print(f"Convert to HEVC manually via Finder → Services → Encode Selected Video Files", file=sys.stderr)

        print_swift_config(args.name, args.fps, args.duration)


if __name__ == "__main__":
    main()
