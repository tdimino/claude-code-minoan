#!/usr/bin/env python3
"""Transcribe one audio file to stdout with Parakeet (MLX).

Thin wrapper over batch_transcribe.py for the `/parakeet <file>` shortcut.
Extra flags pass through, e.g. `--engine qwen3` or `--beam 4`.

Usage:
    transcribe.py <audio-file> [batch_transcribe flags]
"""

import os
import shutil
import sys
from pathlib import Path

BATCH = Path(__file__).with_name("batch_transcribe.py")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(1)
    uv = shutil.which("uv")
    if uv is None:
        sys.exit("error: uv not found (brew install uv)")
    args = sys.argv[1:]
    if not any(arg == "--engine" or arg.startswith("--engine=") for arg in args):
        args += ["--engine", "parakeet"]
    os.execv(uv, [uv, "run", "--quiet", "--script", str(BATCH), *args, "--text"])


if __name__ == "__main__":
    main()
