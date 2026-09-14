#!/usr/bin/env python3
"""Unit tests for align_frames.py and pixel_scale.py on synthetic images.

Run: python3 -m pytest tests/ -q     (or: python3 tests/test_deterministic.py)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import align_frames  # noqa: E402
import pixel_scale  # noqa: E402


# ------------------------------------------------------------ helpers

def make_character(canvas=(64, 64), head=10, feet=50, x0=20, width=16, halo=True, shadow=True):
    """Rectangle 'body' with an AA halo (alpha 60) and a wide soft shadow under the feet."""
    img = Image.new("RGBA", canvas, (0, 0, 0, 0))
    px = img.load()
    for y in range(head, feet + 1):
        for x in range(x0, x0 + width):
            px[x, y] = (200, 40, 40, 255)
    if halo:
        for y in range(head - 1, feet + 2):
            for x in range(x0 - 1, x0 + width + 1):
                if px[x, y][3] == 0:
                    px[x, y] = (200, 40, 40, 60)
    if shadow:
        for x in range(x0 - 8, x0 + width + 8):
            px[x, feet + 3] = (0, 0, 0, 90)
            px[x, feet + 4] = (0, 0, 0, 90)
    return img


def test_measure_ignores_halo_and_shadow():
    img = make_character(head=10, feet=50)
    m = align_frames.measure(img, 127, 0.05)
    assert m["feet"] == 50 and m["head"] == 10, m


def test_align_brings_feet_lines_together():
    with tempfile.TemporaryDirectory() as td:
        src, out = Path(td) / "src", Path(td) / "out"
        src.mkdir()
        # Same character at three vertical offsets and one 20% larger.
        make_character(head=10, feet=50).save(src / "a.png")
        make_character(head=6, feet=46).save(src / "b.png")
        make_character(head=14, feet=54).save(src / "c.png")
        make_character(canvas=(64, 64), head=4, feet=52, x0=18, width=20).save(src / "d.png")
        frames = align_frames.collect(None, str(src))
        r = align_frames.align(frames, out, alpha_threshold=127, min_row_fraction=0.05, cell=None,
                               scale_enabled=True, ref_index=None, anchor_x="ref", dedup=None,
                               loop_check=True, feet_at=None)
        s = r["summary"]
        assert s["kept"] == 4
        assert s["feet_line_variance"] < 1.0, s
        assert s["height_range"][1] - s["height_range"][0] <= 1, s
        assert (out / "alignment.json").exists()


def test_dedup_drops_identical_frames():
    with tempfile.TemporaryDirectory() as td:
        src, out = Path(td) / "src", Path(td) / "out"
        src.mkdir()
        for i in range(3):
            make_character().save(src / f"{i}.png")
        make_character(x0=30).save(src / "3.png")
        frames = align_frames.collect(None, str(src))
        r = align_frames.align(frames, out, alpha_threshold=127, min_row_fraction=0.05, cell=None,
                               scale_enabled=False, ref_index=0, anchor_x="none", dedup=4,
                               loop_check=False, feet_at=None)
        assert r["summary"]["kept"] == 2, r["summary"]


# ------------------------------------------------------------ pixel_scale

def _checker_p():
    img = Image.new("P", (4, 4))
    img.putpalette([0, 0, 0, 255, 0, 0, 0, 255, 0] + [0] * (256 * 3 - 9))
    img.putdata([1, 1, 2, 2,
                 1, 1, 2, 2,
                 0, 1, 2, 0,
                 0, 0, 0, 0])
    img.info["transparency"] = 0
    return img


def test_scale2x_reference_vector():
    # Classic EPX behaviour: an isolated diagonal step gets its corner filled.
    g = [[0, 0, 1],
         [0, 1, 1],
         [1, 1, 1]]
    out = pixel_scale._scale2x_py(g)
    assert len(out) == 6 and len(out[0]) == 6
    # Centre pixel (1,1)=1: A=0 B=1 C=0 D=1 -> e0 stays P (C==A but A==B fails? C==A true, C!=D true, A!=B true) -> e0 = A = 0
    assert out[2][2] == 0 and out[2][3] == 1 and out[3][2] == 1 and out[3][3] == 1
    # Corners of the grid stay their own value
    assert out[0][0] == 0 and out[5][5] == 1


def test_numpy_matches_pure_python():
    if pixel_scale.np is None:
        return
    import random
    random.seed(7)
    w, h = 13, 9
    g = [[random.randint(0, 3) for _ in range(w)] for _ in range(h)]
    import numpy as np
    arr = np.array(g, dtype=np.uint8)
    for py, npf in ((pixel_scale._scale2x_py, pixel_scale._scale2x_np), (pixel_scale._scale3x_py, pixel_scale._scale3x_np)):
        a = py(g)
        b = npf(arr).tolist()
        assert a == b, "numpy and pure-python kernels diverge"


def test_palette_preserved_all_modes():
    img = _checker_p()
    for mode in ("scale2x", "scale3x", "scale4x", "nearest"):
        out = pixel_scale.scale_image(img, mode, 4)
        assert out.mode == "P"
        assert out.getpalette()[:9] == img.getpalette()[:9]
        assert out.info.get("transparency") == 0
        assert set(pixel_scale._pixels(out)) <= set(pixel_scale._pixels(img)), mode
        f = {"scale2x": 2, "scale3x": 3, "scale4x": 4, "nearest": 4}[mode]
        assert out.size == (4 * f, 4 * f)


def test_family_cli_writes_manifest():
    with tempfile.TemporaryDirectory() as td:
        src, out = Path(td) / "fam", Path(td) / "fam2x"
        src.mkdir()
        for i in range(3):
            _checker_p().save(src / f"{i}.png", transparency=0)
        r = subprocess.run([sys.executable, str(SCRIPTS / "pixel_scale.py"), "--family", str(src),
                            "--output-dir", str(out), "--mode", "scale2x", "--json"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        m = json.loads(r.stdout)
        assert m["palette_preserved"] and len(m["frames"]) == 3 and len(m["family_sha256"]) == 64


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
