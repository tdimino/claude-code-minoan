#!/usr/bin/env python3
"""
stage_tracks.py — Stage audio tracks into a local working directory for burning.

Two source modes:
    1. Remote: `--source mac-mini-ts:"/Volumes/Hoodrat HDD/Musica/Album/"`
       Uses tar-over-SSH because Apple's bundled rsync (openrsync 2.6.9)
       splits remote paths on spaces and is unusable against Hoodrat HDD.
    2. Local: `--source ~/Music/SomeAlbum/`
       Straight `cp` with a format filter.

Filters to a single audio format per track (default: mp3) to avoid the
MP3/WMA/M4A duplicates common on Hoodrat HDD. Skips Folder.jpg, AlbumArt*,
and desktop.ini cruft automatically.

Usage:
    stage_tracks.py --source "mac-mini-ts:/Volumes/Hoodrat HDD/Musica/BSG.S1 - OST/" --dest BSG-S1
    stage_tracks.py --source ~/Downloads/mixtape --dest my-mixtape --format mp3
    stage_tracks.py --source ... --dest ... --staging-root /custom/path
"""
from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_STAGING_ROOT = Path.home() / "burn-staging"
DEFAULT_FORMAT = "mp3"
SUPPORTED_FORMATS = ("mp3", "flac", "wav", "aiff", "m4a", "ogg")


def parse_remote(source: str) -> tuple[str, str] | None:
    """Return (host, remote_path) if source is ssh-style, else None."""
    if ":" not in source:
        return None
    host, path = source.split(":", 1)
    # Heuristic: a remote source has a host with no slashes and a path starting with /
    if "/" in host:
        return None
    if not path.startswith("/") and not path.startswith("~"):
        return None
    return host, path


def stage_remote(host: str, remote_path: str, dest: Path, fmt: str) -> int:
    """Pull files matching *.<fmt> from a remote path via tar-over-SSH."""
    # shlex.quote the remote path to prevent shell injection via album names
    # containing double-quotes or other metacharacters.
    safe_path = shlex.quote(remote_path.rstrip("/"))
    remote_cmd = f'cd {safe_path}/ && tar cf - *.{fmt}'
    print(f"  tar-over-SSH: {host}:{remote_path} ({fmt})", file=sys.stderr)
    ssh = subprocess.Popen(
        ["ssh", host, remote_cmd],
        stdout=subprocess.PIPE,
    )
    if ssh.stdout is None:
        print("error: failed to open SSH pipe", file=sys.stderr)
        return 1
    tar = subprocess.Popen(
        ["tar", "xf", "-", "-C", str(dest)],
        stdin=ssh.stdout,
    )
    ssh.stdout.close()  # allow ssh to receive SIGPIPE if tar exits
    ssh.wait()
    tar.wait()
    # Check ssh first — if the connection failed, tar may exit 0 from an empty pipe.
    if ssh.returncode != 0:
        print(f"error: ssh to {host} failed (exit {ssh.returncode})", file=sys.stderr)
        return ssh.returncode
    if tar.returncode != 0:
        return tar.returncode
    return 0


def stage_local(source: Path, dest: Path, fmt: str) -> int:
    """Copy files matching *.<fmt> from a local directory."""
    if not source.is_dir():
        print(f"error: source directory not found: {source}", file=sys.stderr)
        return 1
    matches = sorted(source.glob(f"*.{fmt}"))
    if not matches:
        print(f"error: no .{fmt} files found in {source}", file=sys.stderr)
        return 1
    print(f"  local copy: {source} ({len(matches)} files)", file=sys.stderr)
    for f in matches:
        shutil.copy2(f, dest / f.name)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage audio tracks for burning")
    ap.add_argument("--source", required=True, help="Source path (local or ssh-style host:/path)")
    ap.add_argument("--dest", required=True, help="Staging subdirectory name (under staging root)")
    ap.add_argument(
        "--format",
        default=DEFAULT_FORMAT,
        choices=SUPPORTED_FORMATS,
        help="Audio file extension to stage (filters duplicates like WMA/M4A siblings)",
    )
    ap.add_argument(
        "--staging-root",
        type=Path,
        default=DEFAULT_STAGING_ROOT,
        help=f"Parent directory for staging (default: {DEFAULT_STAGING_ROOT})",
    )
    args = ap.parse_args()

    dest_dir = args.staging_root / args.dest
    dest_dir.mkdir(parents=True, exist_ok=True)

    remote = parse_remote(args.source)
    if remote:
        host, remote_path = remote
        rc = stage_remote(host, remote_path, dest_dir, args.format)
    else:
        rc = stage_local(Path(args.source).expanduser(), dest_dir, args.format)

    if rc != 0:
        print(f"error: staging failed (exit {rc})", file=sys.stderr)
        return rc

    staged = sorted(dest_dir.glob(f"*.{args.format}"))
    print(f"staged {len(staged)} {args.format.upper()} files in {dest_dir}")
    return 0 if staged else 1


if __name__ == "__main__":
    sys.exit(main())
