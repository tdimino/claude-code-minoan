#!/usr/bin/env python3
"""
convert_to_wav.py — Transcode a staging directory of audio files to Red Book WAV.

cdrdao 1.2.6 rejects MP3 and AIFF input directly (the binary literally contains
"AIFF and MP3 not supported by cdrdao"). The TOC format requires WAV or raw PCM.
This script produces 44.1 kHz / 16-bit / stereo PCM WAVs — the exact Red Book
audio CD format — so cdrdao doesn't have to resample at burn time.

Parallelized across CPU cores because this is embarrassingly parallel and an
M4 Max can crunch 26 MP3s in well under a second.

Idempotent: skips WAVs that already exist and are newer than the source file.

Usage:
    convert_to_wav.py ~/burn-staging/BSG-S1
    convert_to_wav.py ~/burn-staging/BSG-S1 --jobs 8
    convert_to_wav.py ~/burn-staging/BSG-S1 --output ~/burn-staging/BSG-S1-wav
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

AUDIO_EXTS = {".mp3", ".flac", ".aiff", ".aif", ".m4a", ".ogg", ".opus", ".wav", ".wma"}


def needs_convert(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    return target.stat().st_mtime < source.stat().st_mtime


def convert_one(source: Path, target: Path) -> tuple[Path, bool, str]:
    """Convert a single file. Returns (source, ok, message)."""
    if not needs_convert(source, target):
        return (source, True, "skipped (up-to-date)")
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source),
        "-ar", "44100",
        "-ac", "2",
        "-sample_fmt", "s16",
        "-c:a", "pcm_s16le",
        str(target),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return (source, False, r.stderr.strip().splitlines()[-1] if r.stderr else "ffmpeg failed")
    return (source, True, "converted")


def main() -> int:
    ap = argparse.ArgumentParser(description="Transcode a staging dir to Red Book WAV")
    ap.add_argument("staging_dir", type=Path)
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: <staging_dir>-wav)",
    )
    ap.add_argument(
        "--jobs",
        type=int,
        default=os.cpu_count() or 4,
        help="Parallel ffmpeg jobs (default: CPU count)",
    )
    args = ap.parse_args()

    if not args.staging_dir.is_dir():
        print(f"error: not a directory: {args.staging_dir}", file=sys.stderr)
        return 1

    output = args.output or args.staging_dir.with_name(args.staging_dir.name + "-wav")
    output.mkdir(parents=True, exist_ok=True)

    audio_files = sorted(
        f for f in args.staging_dir.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS
    )
    if not audio_files:
        print(f"error: no audio files in {args.staging_dir}", file=sys.stderr)
        return 1

    # Case-insensitive stem collisions would cause two ffmpeg jobs to race
    # on the same output WAV file. Abort cleanly before launching workers.
    stems_seen: dict[str, Path] = {}
    for f in audio_files:
        key = f.stem.lower()
        if key in stems_seen:
            print(
                f"error: output stem collision: {stems_seen[key].name!r} and "
                f"{f.name!r} both map to {f.stem}.wav",
                file=sys.stderr,
            )
            return 1
        stems_seen[key] = f

    print(f"converting {len(audio_files)} files to {output} with {args.jobs} workers")

    failures: list[tuple[Path, str]] = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(convert_one, f, output / (f.stem + ".wav")): f
            for f in audio_files
        }
        for fut in as_completed(futures):
            source, ok, msg = fut.result()
            mark = "OK " if ok else "FAIL"
            print(f"  [{mark}] {source.name} — {msg}")
            if not ok:
                failures.append((source, msg))

    wavs = sorted(output.glob("*.wav"))
    total_bytes = sum(w.stat().st_size for w in wavs)
    print(f"\nwavs: {len(wavs)} files, {total_bytes / 1_048_576:.0f} MiB in {output}")

    if failures:
        print(f"\n{len(failures)} failure(s):", file=sys.stderr)
        for f, msg in failures:
            print(f"  {f.name}: {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
