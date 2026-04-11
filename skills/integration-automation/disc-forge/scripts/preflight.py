#!/usr/bin/env python3
"""
preflight.py — Verify disc-forge can burn an audio CD on this Mac right now.

Checks: cdrdao + ffmpeg on PATH, at least one burner detected, cdrdao can talk
to it, blank writable media inserted. Exits 0 on all-clear, 1 on any failure,
and prints the remediation for each failure.

Usage:
    python3 preflight.py
    python3 preflight.py --json     # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    fix: str = ""


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def check_binary(name: str, install_hint: str) -> Check:
    path = shutil.which(name)
    if path:
        return Check(name, True, path)
    return Check(name, False, "not on PATH", install_hint)


def check_drutil_list() -> Check:
    r = run(["drutil", "list"])
    if r.returncode != 0:
        return Check("drutil list", False, r.stderr.strip() or "drutil failed", "Ensure a USB burner is plugged in")
    # drutil list prints a header + at least one row if a drive is present.
    rows = [ln for ln in r.stdout.splitlines() if ln.strip() and "Vendor" not in ln]
    if not rows:
        return Check("drutil list", False, "no burners detected", "Plug in a USB CD/DVD burner")
    return Check("drutil list", True, rows[0].strip())


def check_cdrdao_drive() -> Check:
    r = run(["cdrdao", "drive-info"])
    if r.returncode != 0:
        return Check(
            "cdrdao drive-info",
            False,
            r.stderr.strip().splitlines()[-1] if r.stderr else "cdrdao failed",
            "Try a different USB port, or run `cdrdao scanbus` to debug",
        )
    cdtext = "CD-TEXT writing is supported" in r.stdout
    detail = "drive responds; CD-Text: " + ("YES" if cdtext else "NO")
    return Check("cdrdao drive-info", True, detail)


def check_blank_media() -> Check:
    r = run(["drutil", "status"])
    if r.returncode != 0:
        return Check("drutil status", False, "command failed", "Insert a blank CD-R or CD-RW")
    out = r.stdout
    if "Media Is Not Present" in out or "Type: None" in out:
        return Check("drutil status", False, "no disc inserted", "Insert a blank CD-R or CD-RW")
    if "Type: Media Is Busy" in out:
        return Check("drutil status", False, "drive reports busy", "Wait a moment or eject+reinsert the disc")
    writability_line = next((ln for ln in out.splitlines() if "Writability" in ln), "")
    if "blank" not in writability_line:
        return Check(
            "drutil status",
            False,
            "media is not blank",
            "Insert a blank disc, or erase a CD-RW with `drutil erase quick`",
        )
    # Pull the capacity estimate if we can.
    free_line = next((ln for ln in out.splitlines() if "Space Free" in ln), "")
    return Check("drutil status", True, f"blank writable media ready ({free_line.strip()})")


def print_support_level_note() -> None:
    """Informational only: drutil's SupportLevel label is not a gate for cdrdao.

    cdrdao talks to the drive via IOKit SCSI passthrough and bypasses Apple's
    DiscRecording framework entirely, so an "Unsupported" label only affects
    GUI tools (Finder, Music.app, Burn.app), not this pipeline.
    """
    r = run(["drutil", "info"])
    if r.returncode != 0:
        return
    for line in r.stdout.splitlines():
        if "SupportLevel" in line:
            level = line.split(":", 1)[1].strip()
            if "Unsupported" in level:
                print(f"  (note) drutil reports '{level}' — cdrdao bypasses DiscRecording, safe to ignore")
            return


def main() -> int:
    ap = argparse.ArgumentParser(description="Preflight checks for disc-forge")
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    args = ap.parse_args()

    checks: list[Check] = [
        check_binary("cdrdao", "brew install cdrdao"),
        check_binary("ffmpeg", "brew install ffmpeg"),
        check_binary("ffprobe", "brew install ffmpeg"),
        check_drutil_list(),
        check_cdrdao_drive(),
        check_blank_media(),
    ]

    if args.json:
        print(json.dumps([c.__dict__ for c in checks], indent=2))
    else:
        print("disc-forge preflight:")
        for c in checks:
            mark = "OK " if c.ok else "FAIL"
            print(f"  [{mark}] {c.name}: {c.detail}")
            if not c.ok and c.fix:
                print(f"         fix: {c.fix}")
        print_support_level_note()

    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
