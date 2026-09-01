#!/usr/bin/env python3
"""
Conductor Motion Generator Smoke Test

Every documented flag must change the generated output — a flag that
produces byte-identical HTML is a dead flag, which is a bug.

Usage:
    python3 test_generator.py            # run all cases
    python3 test_generator.py --verbose  # show each case
"""

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "conductor_motion_generator.py"

MODES = [
    "typewriter", "progress", "file-review", "stagger-reveal",
    "terminal", "lottie-compose", "streaming-text", "top-layer",
    "full-page", "catalog",
]

# (mode, extra flags) — each must differ from the same mode generated with defaults
FLAG_CASES = [
    ("typewriter", ["--no-loop"]),
    ("typewriter", ["--hold-duration", "2500"]),
    ("typewriter", ["--typing-variance", "5"]),
    ("typewriter", ["--pacing", "fast"]),
    ("typewriter", ["--words", "alpha,beta"]),
    ("progress", ["--progress-duration", "9000"]),
    ("progress", ["--start-percent", "12"]),
    ("progress", ["--easing", "quart"]),
    ("progress", ["--easing", "linear"]),
    ("progress", ["--accent", "#FF6B6B"]),
    ("progress", ["--color-scheme", "light"]),
    ("file-review", ["--files", "a.pdf,b.csv"]),
    ("file-review", ["--review-speed", "3000"]),
    ("stagger-reveal", ["--easing", "quart"]),
    ("terminal", ["--no-timestamps"]),
    ("terminal", ["--status-items", "one,two,three"]),
    ("lottie-compose", ["--lottie-src", "https://example.com/a.json"]),
    ("lottie-compose", ["--no-lottie-loop"]),
    ("lottie-compose", ["--no-lottie-autoplay"]),
    ("lottie-compose", ["--lottie-cdn"]),
    ("streaming-text", ["--prompt", "Hello there"]),
    ("streaming-text", ["--response", "One.||Two."]),
    ("top-layer", ["--toast-messages", "Saved,Copied"]),
]


def generate(mode, flags, out):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", mode, "--output", str(out), *flags],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return r.stderr.strip() or r.stdout.strip()
    return None


def main():
    verbose = "--verbose" in sys.argv
    failures = []

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        for mode in MODES:
            err = generate(mode, [], td / f"{mode}-base.html")
            if err:
                failures.append(f"{mode} (default): {err}")
                continue
            if verbose:
                print(f"  gen   {mode}")

        for mode, flags in FLAG_CASES:
            base = td / f"{mode}-base.html"
            if not base.exists():
                continue
            var = td / "variant.html"
            err = generate(mode, flags, var)
            label = f"{mode} {' '.join(flags)}"
            if err:
                failures.append(f"{label}: {err}")
            elif var.read_bytes() == base.read_bytes():
                failures.append(f"{label}: flag had no effect on output")
            elif verbose:
                print(f"  flag  {label}")

    print(f"\nModes: {len(MODES)}  Flag cases: {len(FLAG_CASES)}  Failures: {len(failures)}")
    for f in failures:
        print(f"  [x] {f}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
