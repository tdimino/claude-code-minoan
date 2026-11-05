#!/usr/bin/env python3
"""Encode turntable frames with alpha, and optionally lay the turntable over a recorded take.

    python3 encode_turntable.py FRAMES_DIR [--fps 30] [--prores] [--over take.mp4 --height 0.6 --side right]

Writes FRAMES_DIR/turntable.webm (VP9, yuva420p) and, with --prores, turntable.mov (ProRes 4444, yuva444p10le).
With --over, writes <take>.turntable.mp4 next to the take: H.264 High yuv420p, audio copied, the turntable
looped for the whole take. Run recordly's check_x_export.py on that before posting to X.

ffmpeg's built-in VP9 decoder drops WebM alpha (trac #8344), so the overlay forces libvpx-vp9 on the input.
Exit codes: 0 ok, 1 ffmpeg or verification failure, 2 usage error.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+ " + " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-2000:], file=sys.stderr)
        raise SystemExit(1)


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("frames", type=Path, help="directory holding frame_0001.png …")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--crf", type=int, default=30, help="VP9 quality, lower is better")
    p.add_argument("--prores", action="store_true", help="also write ProRes 4444 for editors")
    p.add_argument("--over", type=Path, help="a recorded take to overlay the turntable on")
    p.add_argument("--height", type=float, default=0.6, help="turntable height as a fraction of the take's")
    p.add_argument("--side", choices=["right", "left", "center"], default="right")
    p.add_argument("--inset", type=float, default=0.04, help="gap from the side, fraction of the take's width")
    a = p.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("encode_turntable: ffmpeg and ffprobe are required", file=sys.stderr)
        return 2
    pattern = a.frames / "frame_%04d.png"
    if not (a.frames / "frame_0001.png").is_file():
        print(f"encode_turntable: no frame_0001.png in {a.frames}", file=sys.stderr)
        return 2
    if a.over and not a.over.is_file():
        print(f"encode_turntable: no such take: {a.over}", file=sys.stderr)
        return 2
    if not 0.05 <= a.height <= 1.0:
        print("encode_turntable: --height must be between 0.05 and 1", file=sys.stderr)
        return 2

    webm = a.frames / "turntable.webm"
    run(["ffmpeg", "-y", "-framerate", str(a.fps), "-i", str(pattern), "-c:v", "libvpx-vp9",
         "-pix_fmt", "yuva420p", "-crf", str(a.crf), "-b:v", "0", "-row-mt", "1", "-auto-alt-ref", "0", str(webm)])
    tags = probe(webm)["streams"][0].get("tags", {})
    if tags.get("alpha_mode") != "1" and tags.get("ALPHA_MODE") != "1":
        print("encode_turntable: turntable.webm has no alpha channel", file=sys.stderr)
        return 1
    print(f"wrote {webm} (VP9 with alpha)")

    if a.prores:
        mov = a.frames / "turntable.mov"
        run(["ffmpeg", "-y", "-framerate", str(a.fps), "-i", str(pattern), "-c:v", "prores_ks",
             "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(mov)])
        print(f"wrote {mov} (ProRes 4444 with alpha)")

    if a.over:
        take = probe(a.over)
        video = next((s for s in take["streams"] if s["codec_type"] == "video"), None)
        if video is None:
            print(f"encode_turntable: {a.over} has no video stream", file=sys.stderr)
            return 2
        has_audio = any(s["codec_type"] == "audio" for s in take["streams"])
        h = int(video["height"])
        obj_h = int(h * a.height) // 2 * 2
        inset = f"W*{a.inset}"
        x = {"right": f"W-w-{inset}", "left": inset, "center": "(W-w)/2"}[a.side]
        out = a.over.with_suffix(".turntable.mp4")
        cmd = ["ffmpeg", "-y", "-i", str(a.over), "-stream_loop", "-1", "-c:v", "libvpx-vp9", "-i", str(webm),
               "-filter_complex",
               f"[1:v]scale=-2:{obj_h}[obj];[0:v][obj]overlay={x}:(H-h)/2:shortest=1:format=auto,format=yuv420p[v]",
               "-map", "[v]"]
        if has_audio:
            cmd += ["-map", "0:a:0", "-c:a", "copy"]
        cmd += ["-c:v", "libx264", "-profile:v", "high", "-crf", "18", "-preset", "medium",
                "-movflags", "+faststart", str(out)]
        run(cmd)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
