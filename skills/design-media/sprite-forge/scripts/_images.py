"""Shared image opening for sprite-forge scripts: one clean error line instead of a Pillow traceback."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)


def open_image(path: str | Path, mode: str | None = None) -> Image.Image:
    """Open `path`; exit with a one-line message when it is missing or not an image.

    `mode` converts on the way out (e.g. "RGBA"); None keeps the file's own mode so
    palette images stay palette images.
    """
    try:
        img = Image.open(path)
        img.load()
    except FileNotFoundError:
        sys.exit(f"not found: {path}")
    except (Image.UnidentifiedImageError, OSError) as exc:
        sys.exit(f"not an image: {path} ({exc.__class__.__name__})")
    return img.convert(mode) if mode and img.mode != mode else img
