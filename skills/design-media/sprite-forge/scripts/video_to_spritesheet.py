#!/usr/bin/env python3
"""Video (or a generated clip) -> aligned, keyed, game-ready sprite sheet with manifest v2.

Pipeline:  [generate clip via fal genmedia]  ->  ffmpeg frames  ->  chroma key  ->  align_frames
           ->  stitch_spritesheet (atlas v2 + optional Aseprite JSON)

Generation (optional): --provider genmedia --start-frame anchor.png [--end-frame anchor.png]
  Default model alibaba/wan-3.0/image-to-video (first+last frame => seamless loop, cheapest/s).
  Alternates: bytedance/seedance-2.5/image-to-video, fal-ai/kling-video/v3/pro/image-to-video,
  minimax/hailuo-03/image-to-video, fal-ai/veo3.1/image-to-video. Dry run unless --yes.

Background removal: generate on flat #00FF00 and key once (--remove-bg chroma, the default when
a clip is generated). --remove-bg rembg is for stills; on video it flickers the matte, so it is
only allowed with --allow-rembg-video and the aligner's edge-drift check will report it.

Usage:
  video_to_spritesheet.py --input walk.mp4 --fps 12 --cell-size 128x128 --remove-bg chroma --state walk:12:loop
  video_to_spritesheet.py --provider genmedia --start-frame hero.png --end-frame hero.png \
      --prompt "walk cycle in place, side view, flat #00FF00 background" --duration 4 --fps 12 \
      --cell-size 128x128 --dedup 6 --state walk:12:loop --aseprite-json -o walk.png --yes
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _images import open_image  # noqa: E402

SCRIPTS = Path(__file__).parent
DEFAULT_VIDEO_MODEL = "alibaba/wan-3.0/image-to-video"
END_FRAME_FIELD = {
    "alibaba/wan-3.0/image-to-video": "end_image_url",
    "bytedance/seedance-2.5/image-to-video": "end_image_url",
    "fal-ai/kling-video/v3/pro/image-to-video": "tail_image_url",
    "minimax/hailuo-03/image-to-video": "end_image_url",
}


def run(cmd: list[str], what: str) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{what} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r


def generate_clip(a, out_dir: Path) -> Path | None:
    from gen_image import run_genmedia
    model = a.model or DEFAULT_VIDEO_MODEL
    params = {"prompt": a.prompt or "character animation cycle in place, flat #00FF00 chroma background, "
                                    "no camera motion, no background elements"}
    if a.duration:
        params["duration"] = a.duration
    if a.end_frame:
        params[END_FRAME_FIELD.get(model, "end_image_url")] = f"<upload:{a.end_frame}>"
    for kv in a.param or []:
        k, _, v = kv.partition("=")
        params[k] = v
    if a.yes and a.end_frame:
        from gen_image import genmedia_upload
        params[END_FRAME_FIELD.get(model, "end_image_url")] = genmedia_upload(a.end_frame)
    summary = run_genmedia(model, params, [a.start_frame], a.image_field, out_dir, "clip", a.yes, a.json,
                           run_async=True)
    if summary.get("dry_run"):
        return None
    vids = [Path(f) for f in summary.get("files", []) if f.lower().endswith((".mp4", ".webm", ".mov"))]
    if not vids:
        sys.exit("genmedia finished but no video file was downloaded; check genmedia status")
    return vids[0]


def extract_frames(video: str, fps: int, start, end, out_dir: Path) -> list[Path]:
    cmd = ["ffmpeg", "-loglevel", "error"]
    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", video]
    if end is not None:
        cmd += ["-to", str(end)]
    cmd += ["-vf", f"fps={fps}", str(out_dir / "frame_%04d.png")]
    run(cmd, "ffmpeg")
    return sorted(out_dir.glob("frame_*.png"))


def remove_bg(frames: list[Path], method: str, color: str, tolerance: int):
    if method == "chroma":
        for f in frames:
            run(["python3", str(SCRIPTS / "chroma_key.py"), "--input", str(f), "--output", str(f),
                 "--color", color, "--tolerance", str(tolerance), "--despill"], "chroma_key")
    elif method == "rembg":
        if not shutil.which("rembg"):
            sys.exit("rembg not found: uv pip install rembg")
        for f in frames:
            r = subprocess.run(["rembg", "i", str(f), str(f)], capture_output=True, text=True)
            if r.returncode != 0:
                print(f"rembg warning on {f.name}: {r.stderr}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_argument_group("source")
    src.add_argument("--input", help="Input video file (skip generation)")
    src.add_argument("--provider", choices=["genmedia"], help="generate the clip first")
    src.add_argument("--model", help=f"fal endpoint (default {DEFAULT_VIDEO_MODEL})")
    src.add_argument("--start-frame", help="first-frame image for image-to-video")
    src.add_argument("--end-frame", help="last-frame image (loop closure); same as start for a perfect loop")
    src.add_argument("--prompt")
    src.add_argument("--duration", help="seconds (model-specific allowed values)")
    src.add_argument("--image-field", help="override the model's first-frame field name")
    src.add_argument("--param", action="append", help="extra endpoint param key=value")
    src.add_argument("--yes", action="store_true", help="spend credits (default: dry run)")

    ex = p.add_argument_group("extraction and keying")
    ex.add_argument("--fps", type=int, default=12)
    ex.add_argument("--start", type=float)
    ex.add_argument("--end", type=float)
    ex.add_argument("--remove-bg", choices=["chroma", "rembg", "none"], help="default: chroma when generating, none otherwise")
    ex.add_argument("--chroma-color", default="00FF00")
    ex.add_argument("--chroma-tolerance", type=int, default=40)
    ex.add_argument("--allow-rembg-video", action="store_true", help="permit per-frame rembg (matte flicker risk)")

    al = p.add_argument_group("alignment")
    al.add_argument("--cell-size", default="128x128", help="output cell WxH")
    al.add_argument("--no-align", action="store_true", help="skip align_frames (plain resize like v1)")
    al.add_argument("--no-scale", action="store_true", help="align by translation only")
    al.add_argument("--dedup", type=int, help="drop near-duplicate consecutive frames (dHash distance < N)")
    al.add_argument("--max-frames", type=int, help="keep at most N frames after dedup (evenly sampled)")

    st = p.add_argument_group("sheet")
    st.add_argument("--cols", type=int)
    st.add_argument("--state", action="append", help="v2 state name:fps[:loop|once]")
    st.add_argument("--atlas", choices=["v2", "json", "xml", "none"], default="v2")
    st.add_argument("--aseprite-json", action="store_true")
    st.add_argument("-o", "--output", default="spritesheet.png")
    st.add_argument("--keep-frames", action="store_true")
    st.add_argument("--json", action="store_true")
    a = p.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg required but not found in PATH")
    if not a.input and not a.provider:
        sys.exit("give --input video.mp4 or --provider genmedia --start-frame image.png")
    if a.provider and not a.start_frame:
        sys.exit("--provider genmedia needs --start-frame")

    work = Path(tempfile.mkdtemp(prefix="sprite_forge_"))
    video = a.input
    if a.provider:
        clip = generate_clip(a, work / "clip")
        if clip is None:
            print("Dry run: no clip generated, nothing extracted. Re-run with --yes.")
            return
        video = str(clip)

    remove = a.remove_bg or ("chroma" if a.provider else "none")
    if remove == "rembg" and not a.allow_rembg_video:
        sys.exit("per-frame rembg flickers the matte on video. Generate on #00FF00 and use --remove-bg chroma, "
                 "or pass --allow-rembg-video to override.")

    raw = work / "raw"
    raw.mkdir()
    frames = extract_frames(video, a.fps, a.start, a.end, raw)
    if not frames:
        sys.exit("No frames extracted from video")
    remove_bg(frames, remove, a.chroma_color, a.chroma_tolerance)

    aligned = work / "aligned"
    if a.no_align:
        from PIL import Image
        aligned.mkdir()
        cw, ch = (int(v) for v in a.cell_size.lower().split("x"))
        for f in frames:
            open_image(f, "RGBA").resize((cw, ch), Image.LANCZOS).save(aligned / f.name)
    else:
        cmd = ["python3", str(SCRIPTS / "align_frames.py"), "--input-dir", str(raw), "--output-dir", str(aligned),
               "--cell", a.cell_size, "--loop-check"]
        if a.no_scale:
            cmd.append("--no-scale")
        if a.dedup:
            cmd += ["--dedup", str(a.dedup)]
        r = run(cmd, "align_frames")
        print(r.stdout.strip())
        if r.stderr.strip():
            print(r.stderr.strip(), file=sys.stderr)

    kept = sorted(aligned.glob("frame_*.png"))
    if a.max_frames and len(kept) > a.max_frames:
        step = len(kept) / a.max_frames
        keep = {kept[int(i * step)] for i in range(a.max_frames)}
        for f in kept:
            if f not in keep:
                f.unlink()
        kept = sorted(aligned.glob("frame_*.png"))

    stitch = ["python3", str(SCRIPTS / "stitch_spritesheet.py"), "--input-dir", str(aligned),
              "--cell-size", a.cell_size, "--atlas", a.atlas, "-o", a.output,
              "--generator", "sprite-forge/video_to_spritesheet.py"]
    if a.cols:
        stitch += ["--cols", str(a.cols)]
    for s in a.state or []:
        stitch += ["--state", s]
    if a.aseprite_json:
        stitch.append("--aseprite-json")
    if a.provider:
        stitch += ["--provenance", f"model={a.model or DEFAULT_VIDEO_MODEL}", f"source_video={video}"]
    elif a.input:
        stitch += ["--provenance", f"source_video={a.input}"]
    r = run(stitch, "stitch_spritesheet")
    print(r.stdout.strip())

    if a.keep_frames:
        print(f"Frames kept at {work}")
    else:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
