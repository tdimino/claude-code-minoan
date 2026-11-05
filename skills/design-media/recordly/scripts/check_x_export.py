#!/usr/bin/env python3
"""Check a video against X's upload rules, and optionally write an X-ready copy.

Usage:
  python3 check_x_export.py FILE [--premium] [--fix]

Rules, read 2026-11-05:
  help.x.com/en/using-x/x-videos (web upload): free accounts 140 s and 512 MB; Premium under 4 h and 16 GB.
  docs.x.com/x-api/media/quickstart/best-practices.md: H.264 High, YUV 4:2:0, 1:1 pixel aspect, progressive,
    at most 60 fps, aspect between 1:3 and 3:1, AAC-LC (HE-AAC rejected), mono or stereo, at least 0.5 s;
    unsubscribed accounts play back at 720p. The developer docs give larger caps (20 min / 8 GB) than the Help Center;
    the stricter Help Center figures apply here. Open GOP is not checked; --fix encodes with closed GOPs.

Exit codes: 0 no FAIL (warnings allowed), 1 at least one FAIL, 2 usage or tool error.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

TIERS = {
    "free": {"max_seconds": 140, "max_bytes": 512 * 1000 * 1000, "playback_short_side": 720},
    "premium": {"max_seconds": 4 * 3600, "max_bytes": 16 * 1000 * 1000 * 1000, "playback_short_side": 1080},
}
MIN_SECONDS = 0.5
MAX_FPS = 60
MIN_ASPECT, MAX_ASPECT = Fraction(1, 3), Fraction(3, 1)
HIGH_PROFILES = {"High", "Constrained High", "Progressive High"}
AUDIO_BITRATE_FLOOR = 128_000
AUDIO_BITRATE_TOLERANCE = 0.95  # encoders report a 128k target as ~127 kbps


@dataclass
class Result:
    level: str  # PASS, WARN or FAIL
    rule: str
    detail: str
    fixable: bool = False


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe could not read {path}: {out.stderr.strip()}")
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError as err:
        raise RuntimeError(f"ffprobe returned unreadable output for {path}: {err}") from err


def pick_video(streams: list[dict]) -> dict | None:
    """First real video stream; embedded cover art (attached_pic) is skipped."""
    return next((s for s in streams if s.get("codec_type") == "video"
                 and not s.get("disposition", {}).get("attached_pic")), None)


def rotation(video: dict) -> int:
    for side in video.get("side_data_list") or []:
        if "rotation" in side:
            return int(float(side["rotation"]))
    return int(float(video.get("tags", {}).get("rotate", 0) or 0))


def sample_aspect(video: dict) -> Fraction:
    sar = video.get("sample_aspect_ratio")
    if sar in (None, "N/A", "0:1"):
        return Fraction(1)
    num, _, den = sar.partition(":")
    return Fraction(int(num), int(den))


def displayed_size(video: dict) -> tuple[int, int]:
    """Width and height as a viewer sees them: pixel aspect applied, then rotation."""
    width = round(int(video.get("width") or 0) * sample_aspect(video))
    height = int(video.get("height") or 0)
    if abs(rotation(video)) % 180 == 90:
        width, height = height, width
    return width, height


def frame_rate(video: dict) -> float | None:
    avg = rate(video.get("avg_frame_rate"))
    if avg:
        return avg
    fallback = rate(video.get("r_frame_rate"))
    return fallback if fallback and fallback <= 240 else None  # VFR files can report r_frame_rate 1000/1


def rate(value: str | None) -> float | None:
    if not value or value in ("0/0", "N/A"):
        return None
    num, _, den = value.partition("/")
    try:
        return float(num) / float(den or 1) if float(den or 1) else None
    except ValueError:
        return None


def check(info: dict, tier: str) -> list[Result]:
    caps = TIERS[tier]
    fmt = info.get("format", {})
    streams = info.get("streams", [])
    video = pick_video(streams)
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    results: list[Result] = []
    add = results.append

    names = fmt.get("format_name", "")
    if "mp4" in names or "mov" in names:
        add(Result("PASS", "container", names))
    else:
        add(Result("FAIL", "container", f"{names or 'unknown'}; X takes MP4 or MOV", fixable=video is not None))

    if video is None:
        add(Result("FAIL", "video", "no video stream"))
        return results

    codec, profile = video.get("codec_name"), video.get("profile", "")
    if codec != "h264":
        add(Result("FAIL", "video codec", f"{codec}; X needs H.264", fixable=True))
    elif profile not in HIGH_PROFILES:
        add(Result("FAIL", "H.264 profile", f"{profile}; X needs High", fixable=True))
    else:
        add(Result("PASS", "video codec", f"h264 {profile}"))

    pix = video.get("pix_fmt")
    if pix == "yuv420p":
        add(Result("PASS", "pixel format", pix))
    elif pix == "yuvj420p":
        add(Result("WARN", "pixel format", "yuvj420p (full range); X expects 4:2:0, --fix converts to yuv420p", fixable=True))
    else:
        add(Result("FAIL", "pixel format", f"{pix}; X takes only YUV 4:2:0", fixable=True))

    sar = video.get("sample_aspect_ratio")
    if sar in (None, "N/A", "0:1", "1:1"):
        add(Result("PASS", "pixel aspect", "1:1"))
    else:
        add(Result("FAIL", "pixel aspect", f"{sar}; X needs square pixels", fixable=True))

    field = video.get("field_order")
    if field in (None, "progressive", "unknown"):
        add(Result("PASS", "scan", "progressive"))
    else:
        add(Result("FAIL", "scan", f"{field}; X needs progressive", fixable=True))

    fps = frame_rate(video)
    if fps is None:
        add(Result("WARN", "frame rate", "unreadable"))
    elif fps > MAX_FPS + 0.01:
        add(Result("FAIL", "frame rate", f"{fps:.2f} fps; X allows at most {MAX_FPS}", fixable=True))
    else:
        add(Result("PASS", "frame rate", f"{fps:.2f} fps"))

    width, height = displayed_size(video)
    if width and height:
        aspect = Fraction(width, height)
        label = f"{width}x{height} ({float(aspect):.3f}:1)"
        if MIN_ASPECT <= aspect <= MAX_ASPECT:
            add(Result("PASS", "aspect", label))
        else:
            add(Result("FAIL", "aspect", f"{label}; X allows 1:3 to 3:1, so recrop or change the aspect preset"))
        short = min(width, height)
        if short > caps["playback_short_side"]:
            add(Result("WARN", "resolution",
                       f"short side {short}; a {tier} account plays back at {caps['playback_short_side']}p, "
                       f"--fix scales to {caps['playback_short_side']} on the short side", fixable=True))
        else:
            add(Result("PASS", "resolution", f"short side {short}"))

    if not audio:
        add(Result("WARN", "audio", "no audio track"))
    else:
        if len(audio) > 1:
            add(Result("WARN", "audio", f"{len(audio)} audio tracks; X uses the first, --fix keeps only it", fixable=True))
        a = audio[0]
        a_codec, a_profile = a.get("codec_name"), a.get("profile", "")
        if a_codec == "aac" and a_profile == "LC":
            add(Result("PASS", "audio codec", "aac LC"))
        else:
            add(Result("FAIL", "audio codec", f"{a_codec} {a_profile}".strip() + "; X needs AAC-LC", fixable=True))
        channels = int(a.get("channels") or 0)
        if channels > 2:
            add(Result("FAIL", "audio channels", f"{channels}; X takes mono or stereo", fixable=True))
        else:
            add(Result("PASS", "audio channels", str(channels)))
        a_rate = int(a.get("bit_rate") or 0)
        if a_rate and a_rate < AUDIO_BITRATE_FLOOR * AUDIO_BITRATE_TOLERANCE:
            add(Result("WARN", "audio bitrate", f"{a_rate // 1000} kbps; X recommends at least 128", fixable=True))

    raw_duration = fmt.get("duration") or video.get("duration")
    duration = float(raw_duration) if raw_duration not in (None, "N/A") else None
    if duration is None:
        add(Result("WARN", "duration", "unreadable; check the length by hand"))
    elif duration < MIN_SECONDS:
        add(Result("FAIL", "duration", f"{duration:.2f} s; X needs at least {MIN_SECONDS}"))
    elif duration > caps["max_seconds"]:
        add(Result("FAIL", "duration",
                   f"{duration:.1f} s; a {tier} account allows {caps['max_seconds']} s, so trim "
                   f"{duration - caps['max_seconds']:.1f} s"))
    else:
        add(Result("PASS", "duration", f"{duration:.1f} s"))

    size = int(fmt.get("size") or 0)
    if size > caps["max_bytes"]:
        add(Result("FAIL", "file size", f"{size / 1e6:.1f} MB; a {tier} account allows {caps['max_bytes'] / 1e6:.0f} MB",
                   fixable=True))
    else:
        add(Result("PASS", "file size", f"{size / 1e6:.1f} MB"))

    return results


def report(path: Path, results: list[Result]) -> bool:
    print(path)
    for r in results:
        print(f"  {r.level:<4}  {r.rule}: {r.detail}")
    failed = any(r.level == "FAIL" for r in results)
    print("  => " + ("FAIL" if failed else "ready for X"))
    return failed


def fix(src: Path, info: dict, tier: str) -> Path:
    dst = src.with_name(src.stem + ".x.mp4")
    if dst.resolve() == src.resolve():
        raise RuntimeError("refusing to overwrite the input")
    if dst.exists():
        raise RuntimeError(f"{dst} already exists; move or delete it first")

    video = pick_video(info["streams"])
    audio = [s for s in info["streams"] if s.get("codec_type") == "audio"]
    cap = TIERS[tier]["playback_short_side"]
    filters = []
    if video.get("field_order") not in (None, "progressive", "unknown"):
        filters.append("yadif")
    # ffmpeg applies the rotation before -vf, so the filters see the displayed orientation.
    width, height = displayed_size(video)
    if min(width, height) > cap:
        factor = cap / min(width, height)
        width, height = width * factor, height * factor
    width, height = max(2, round(width / 2) * 2), max(2, round(height / 2) * 2)  # yuv420p needs even sizes
    filters += [f"scale={width}:{height}", "setsar=1"]
    fps = frame_rate(video)
    if fps and fps > MAX_FPS + 0.01:
        filters.append(f"fps={MAX_FPS}")
    filters.append("format=yuv420p")

    cmd = ["ffmpeg", "-v", "error", "-n", "-i", str(src), "-map", f"0:{video['index']}"]
    if audio:
        cmd += ["-map", "0:a:0"]
    cmd += ["-vf", ",".join(filters),
            "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", "20"]
    if audio:
        channels = min(int(audio[0].get("channels") or 2), 2)
        cmd += ["-c:a", "aac", "-profile:a", "aac_low", "-b:a", "128k", "-ar", "48000", "-ac", str(channels)]
    cmd += ["-movflags", "+faststart", str(dst)]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        dst.unlink(missing_ok=True)  # dst did not exist before this run, so only a partial file is removed
        raise RuntimeError(f"ffmpeg failed: {done.stderr.strip()}")
    return dst


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a video against X's upload rules.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--premium", action="store_true", help="use X Premium caps (under 4 h, 16 GB, 1080p)")
    parser.add_argument("--fix", action="store_true", help="write FILE.x.mp4 with every fixable issue fixed")
    args = parser.parse_args()

    for tool in ("ffprobe", "ffmpeg"):
        if shutil.which(tool) is None:
            print(f"{tool} not found; install it with: brew install ffmpeg", file=sys.stderr)
            return 2
    if not args.file.is_file():
        print(f"no such file: {args.file}", file=sys.stderr)
        return 2

    tier = "premium" if args.premium else "free"
    try:
        info = probe(args.file)
        results = check(info, tier)
        failed = report(args.file, results)
        if not args.fix:
            return 1 if failed else 0
        has_video = pick_video(info.get("streams", [])) is not None
        if not has_video or not any(r.fixable and r.level in ("FAIL", "WARN") for r in results):
            print("  nothing to fix")
            return 1 if failed else 0
        dst = fix(args.file, info, tier)
        print(f"\nwrote {dst}")
        return 1 if report(dst, check(probe(dst), tier)) else 0
    except Exception as err:  # report any failure as a usage/tool error, never a traceback
        print(f"{type(err).__name__}: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
