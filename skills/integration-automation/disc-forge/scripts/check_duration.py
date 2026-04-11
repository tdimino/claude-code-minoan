#!/usr/bin/env python3
"""
check_duration.py — Verify a staging directory fits on a Red Book audio CD.

Runs ffprobe on every audio file in the directory, totals the runtime,
reports the headroom against the 80-minute Red Book ceiling, and prints a
format histogram so leftover duplicates (MP3+WMA, MP3+M4A) surface loudly.

Exits 0 if the album fits, 1 if it overruns capacity or has no audio files.

Red Book audio CD capacity:
    Standard 74-minute disc: 74:00 (333000 sectors)
    Standard 80-minute disc: 79:59:74 (359848 sectors) — the modern default.
We use 80 min as the ceiling. cdrdao will do the exact sector math at burn time.

Usage:
    check_duration.py ~/burn-staging/BSG-Miniseries
    check_duration.py ~/burn-staging/BSG-S1 --ceiling 74
    check_duration.py ~/burn-staging/my-mixtape --json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

AUDIO_EXTS = {".mp3", ".flac", ".wav", ".aiff", ".aif", ".m4a", ".ogg", ".opus", ".wma"}


def ffprobe_duration(path: Path) -> tuple[float | None, str]:
    """Return (duration_seconds, error_message). error_message is empty on success."""
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        err = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "ffprobe failed"
        return None, err
    try:
        return float(r.stdout.strip()), ""
    except ValueError:
        return None, f"unparseable duration: {r.stdout.strip()!r}"


def format_mmss(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Check if a staging dir fits on a Red Book CD")
    ap.add_argument("staging_dir", type=Path)
    ap.add_argument(
        "--ceiling",
        type=int,
        default=80,
        help="CD capacity in minutes (74 or 80; default 80)",
    )
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    args = ap.parse_args()

    if not args.staging_dir.is_dir():
        print(f"error: not a directory: {args.staging_dir}", file=sys.stderr)
        return 1

    audio_files = sorted(
        f for f in args.staging_dir.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS
    )
    if not audio_files:
        print(f"error: no audio files in {args.staging_dir}", file=sys.stderr)
        return 1

    histogram: Counter[str] = Counter()
    durations: list[tuple[Path, float]] = []
    total = 0.0
    for f in audio_files:
        d, err = ffprobe_duration(f)
        if d is None:
            print(f"warning: ffprobe failed on {f.name}: {err}", file=sys.stderr)
            continue
        durations.append((f, d))
        histogram[f.suffix.lower().lstrip(".")] += 1
        total += d

    ceiling_sec = args.ceiling * 60
    headroom = ceiling_sec - total
    fits = headroom >= 0

    if args.json:
        print(json.dumps({
            "staging_dir": str(args.staging_dir),
            "track_count": len(durations),
            "total_seconds": round(total, 2),
            "total_mmss": format_mmss(total),
            "ceiling_minutes": args.ceiling,
            "headroom_seconds": round(headroom, 2),
            "fits": fits,
            "format_histogram": dict(histogram),
        }, indent=2))
    else:
        print(f"staging: {args.staging_dir}")
        print(f"tracks:  {len(durations)}")
        print(f"runtime: {format_mmss(total)} ({total/60:.1f} min)")
        print(f"ceiling: {args.ceiling}:00 ({args.ceiling} min)")
        if fits:
            print(f"headroom: {format_mmss(headroom)} — FITS")
        else:
            print(f"overrun:  {format_mmss(-headroom)} — DOES NOT FIT")
        fmt_line = ", ".join(f"{fmt}: {n}" for fmt, n in histogram.most_common())
        print(f"formats: {fmt_line}")
        if len(histogram) > 1:
            print("warning: multiple formats present; likely duplicate tracks")

    return 0 if fits else 1


if __name__ == "__main__":
    sys.exit(main())
