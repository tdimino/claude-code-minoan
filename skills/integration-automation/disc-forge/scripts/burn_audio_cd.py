#!/usr/bin/env python3
"""
burn_audio_cd.py — Master orchestrator for disc-forge.

Two modes:

AUDIO CD (default, Red Book — plays in any CD player):
    1. preflight.py        — verify cdrdao, ffmpeg, drive, blank disc
    2. stage_tracks.py     — optional: pull files via tar-over-SSH
    3. check_duration.py   — abort if album overruns 80 min
    4. convert_to_wav.py   — parallel MP3 -> 44.1/16/stereo PCM
    5. build_toc.py        — cdrdao TOC with CD-Text from source ID3 tags
    6. cdrdao write        — actual burn
    7. cleanup             — delete WAV staging (keep MP3 staging for re-burns)

MP3 DATA CD (--mp3-disc — plays in MP3-capable stereos, 700 MB capacity):
    1. preflight.py        — same
    2. stage_tracks.py     — same
    3. check_mp3_size      — abort if payload overruns 700 MB (inline)
    4. build_data_toc.py   — hdiutil makehybrid -> ISO + cdrdao data TOC
    5. cdrdao write        — same burn command, different TOC
    6. cleanup             — delete ISO (keep MP3 staging)

--dry-run skips the cdrdao write step so the full pipeline can be validated.

Usage:
    # Audio CD from Hoodrat HDD
    burn_audio_cd.py --source "mac-mini-ts:/Volumes/Hoodrat HDD/Musica/BSG.S1 - OST/" --name BSG-S1

    # MP3 data CD (modern car stereos)
    burn_audio_cd.py --source ~/burn-staging/mantras --name mantras --mp3-disc

    # Dry run (everything except the cdrdao write)
    burn_audio_cd.py --source ~/burn-staging/BSG-S1 --name BSG-S1 --dry-run

    # Pop-album-style 2-sec gaps instead of gapless (audio CD only)
    burn_audio_cd.py --source ~/burn-staging/DSOTM --name DSOTM --gaps

    # Slower, more reliable burn speed
    burn_audio_cd.py --source ... --name ... --speed 10
"""
from __future__ import annotations

import argparse
import signal
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_STAGING_ROOT = Path.home() / "burn-staging"


def run_step(name: str, cmd: list[str]) -> int:
    """Run a pipeline step in the foreground; stream its output. Return exit code."""
    print(f"\n=== {name} ===")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"\nstep failed: {name} (exit {r.returncode})", file=sys.stderr)
    return r.returncode


def skip_step(name: str, reason: str) -> None:
    """Print a stage header for a skipped step, matching run_step() format."""
    print(f"\n=== {name} (skipped: {reason}) ===")


def _is_local_path(source: str) -> bool:
    """True if source looks like a local path, not an ssh-style host:/path."""
    if ":" not in source:
        return True
    host, path = source.split(":", 1)
    # A remote source has a hostname with no slashes and a path starting with / or ~
    if "/" not in host and (path.startswith("/") or path.startswith("~")):
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(
        description="End-to-end audio CD burn via cdrdao",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--source",
        required=True,
        help="Source path: local directory OR ssh-style host:/path (e.g. mac-mini-ts:/Volumes/...)",
    )
    ap.add_argument(
        "--name",
        required=True,
        help="Staging subdirectory name (and burn job name)",
    )
    ap.add_argument(
        "--staging-root",
        type=Path,
        default=DEFAULT_STAGING_ROOT,
        help=f"Parent dir for staging (default: {DEFAULT_STAGING_ROOT})",
    )
    ap.add_argument(
        "--format",
        default="mp3",
        help="Source audio format to filter (default: mp3)",
    )
    ap.add_argument(
        "--speed",
        type=int,
        default=16,
        help="cdrdao write speed multiplier (default: 16)",
    )
    ap.add_argument(
        "--ceiling",
        type=int,
        default=80,
        help="CD capacity in minutes for the fit check (default: 80)",
    )
    ap.add_argument(
        "--gaps",
        action="store_true",
        help="Insert 2-sec gaps between tracks (pop album style); default is gapless",
    )
    ap.add_argument(
        "--keep-wavs",
        action="store_true",
        help="Keep WAV staging dir after burn (default: delete on success)",
    )
    ap.add_argument(
        "--mp3-disc",
        action="store_true",
        help="Burn an MP3 data CD (ISO9660+Joliet, ~700 MB) instead of a Red Book audio CD. "
             "Requires an MP3-capable stereo (most 2005+ car head units).",
    )
    ap.add_argument(
        "--data-ceiling",
        type=int,
        default=700,
        help="MP3 data disc capacity in MB (default: 700, used only with --mp3-disc)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Run preflight + stage + check + convert + TOC, but skip cdrdao write",
    )
    args = ap.parse_args()

    staging_dir = args.staging_root / args.name
    wav_dir = args.staging_root / f"{args.name}-wav"
    iso_path = args.staging_root / f"{args.name}.iso"
    toc_path = args.staging_root / f"{args.name}.toc"
    args.staging_root.mkdir(parents=True, exist_ok=True)

    if args.mp3_disc and args.gaps:
        print("--gaps is only meaningful for audio CDs; ignored in --mp3-disc mode", file=sys.stderr)

    py = sys.executable

    # Step 1: preflight
    if run_step("preflight", [py, str(SCRIPT_DIR / "preflight.py")]) != 0:
        return 1

    # Step 2: stage (skip if source is already the staging dir or already populated)
    source_is_local = _is_local_path(args.source)
    source_is_staging = (
        source_is_local
        and Path(args.source).expanduser().resolve() == staging_dir.resolve()
    )
    if source_is_staging:
        skip_step("stage", "source IS staging dir")
    elif staging_dir.exists() and any(staging_dir.glob(f"*.{args.format}")):
        skip_step("stage", f"{staging_dir} already populated")
    else:
        stage_cmd = [
            py, str(SCRIPT_DIR / "stage_tracks.py"),
            "--source", args.source,
            "--dest", args.name,
            "--format", args.format,
            "--staging-root", str(args.staging_root),
        ]
        if run_step("stage", stage_cmd) != 0:
            return 1

    if args.mp3_disc:
        # Step 3 (data mode): size check against 700 MB
        print(f"\n=== size check (MP3 data CD, ceiling {args.data_ceiling} MB) ===")
        total_bytes = sum(f.stat().st_size for f in staging_dir.rglob("*") if f.is_file())
        total_mb = total_bytes / (1024 * 1024)
        print(f"payload: {total_mb:.1f} MB across {sum(1 for _ in staging_dir.rglob('*.mp3'))} mp3 files")
        if total_mb > args.data_ceiling:
            print(f"overruns {args.data_ceiling} MB; aborting", file=sys.stderr)
            return 1

        # Step 4 (data mode): build ISO + data TOC
        if run_step(
            "build ISO + data TOC",
            [
                py, str(SCRIPT_DIR / "build_data_toc.py"),
                "--source-dir", str(staging_dir),
                "--volume-label", args.name,
                "--iso-output", str(iso_path),
                "--toc-output", str(toc_path),
            ],
        ) != 0:
            return 1
    else:
        # Step 3 (audio mode): duration check
        if run_step(
            "duration check",
            [
                py, str(SCRIPT_DIR / "check_duration.py"),
                str(staging_dir),
                "--ceiling", str(args.ceiling),
            ],
        ) != 0:
            print("album overruns CD capacity; aborting", file=sys.stderr)
            return 1

        # Step 4 (audio mode): convert to WAV
        if run_step(
            "convert to WAV",
            [
                py, str(SCRIPT_DIR / "convert_to_wav.py"),
                str(staging_dir),
                "--output", str(wav_dir),
            ],
        ) != 0:
            return 1

        # Step 5 (audio mode): build TOC
        toc_cmd = [
            py, str(SCRIPT_DIR / "build_toc.py"),
            "--wav-dir", str(wav_dir),
            "--source-dir", str(staging_dir),
            "--output", str(toc_path),
        ]
        if args.gaps:
            toc_cmd.append("--gaps")
        if run_step("build TOC", toc_cmd) != 0:
            return 1

    # Step 6: burn (or skip on dry run)
    if args.dry_run:
        print("\n=== burn (SKIPPED: --dry-run) ===")
        print(f"TOC ready at {toc_path}")
        print(f"To burn manually: cdrdao write --speed {args.speed} --eject {toc_path}")
        print(f"To validate TOC:  cdrdao show-toc {toc_path}")
        return 0

    print(f"\n=== burn: cdrdao write --speed {args.speed} ===")
    print("cdrdao will count down ~10 seconds before committing; Ctrl-C aborts safely.")
    proc = subprocess.Popen(
        ["cdrdao", "write", "--speed", str(args.speed), "--eject", str(toc_path)],
    )
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGTERM)
        proc.wait()
        print("\nburn aborted by user", file=sys.stderr)
        return 1
    if proc.returncode != 0:
        print(f"\ncdrdao write failed (exit {proc.returncode})", file=sys.stderr)
        if args.mp3_disc:
            print(f"ISO preserved at {iso_path} for debugging", file=sys.stderr)
        else:
            print(f"WAV staging preserved at {wav_dir} for debugging", file=sys.stderr)
        return proc.returncode

    # Step 7: cleanup
    if args.keep_wavs:
        skip_step("cleanup", "--keep-wavs")
        if args.mp3_disc:
            print(f"ISO preserved at {iso_path}")
        else:
            print(f"WAV staging preserved at {wav_dir}")
    else:
        print(f"\n=== cleanup ===")
        if args.mp3_disc:
            iso_path.unlink(missing_ok=True)
            print(f"removed {iso_path}")
        else:
            shutil.rmtree(wav_dir, ignore_errors=True)
            print(f"removed {wav_dir}")
        print(f"source staging preserved at {staging_dir} (useful for re-burns)")

    print("\ndisc-forge: burn complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
