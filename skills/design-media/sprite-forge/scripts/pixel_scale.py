#!/usr/bin/env python3
"""Palette-preserving pixel scalers: nearest, Scale2x/Scale3x (EPX/AdvMAME), stacked Scale4x.

Every output pixel is a copy of an input pixel, so no new colours are ever introduced and a
mode-P (indexed) PNG keeps its palette block, transparency index and colour count. That is
the property the faithful-HD rule needs; xBRZ/hqx interpolate colours and are deliberately
not offered here.

Usage:
  pixel_scale.py --input sprite.png --output sprite_2x.png --mode scale2x
  pixel_scale.py --input sprite.png --output sprite_4x.png --mode scale4x
  pixel_scale.py --input sprite.png --output sprite_4x.png --mode nearest --factor 4
  pixel_scale.py --family frames/ --output-dir frames_2x/ --mode scale2x      # whole frame family + family.json

Works on mode P (index space), L, RGB and RGBA. Uses numpy when available; pure-Python fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _images import open_image  # noqa: E402

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

MODES = ("nearest", "scale2x", "scale3x", "scale4x")


def _pixels(img):
    """Flat pixel sequence; Pillow 12 deprecates getdata in favour of get_flattened_data."""
    fn = getattr(img, "get_flattened_data", None)
    return list(fn()) if fn else list(img.getdata())


# ---------------------------------------------------------------- kernels

def _grid(img: Image.Image) -> tuple[list[list], str]:
    """Rows of hashable pixel values (index ints for P/L, tuples for RGB/RGBA)."""
    w, h = img.size
    data = _pixels(img)
    return [data[y * w:(y + 1) * w] for y in range(h)], img.mode


def _scale2x_py(g: list[list]) -> list[list]:
    h, w = len(g), len(g[0])
    out = [[None] * (w * 2) for _ in range(h * 2)]
    for y in range(h):
        for x in range(w):
            p = g[y][x]
            a = g[y - 1][x] if y > 0 else p
            b = g[y][x + 1] if x < w - 1 else p
            c = g[y][x - 1] if x > 0 else p
            d = g[y + 1][x] if y < h - 1 else p
            e0 = e1 = e2 = e3 = p
            if c == a and c != d and a != b:
                e0 = a
            if a == b and a != c and b != d:
                e1 = b
            if d == c and d != b and c != a:
                e2 = c
            if b == d and b != a and d != c:
                e3 = d
            out[2 * y][2 * x], out[2 * y][2 * x + 1] = e0, e1
            out[2 * y + 1][2 * x], out[2 * y + 1][2 * x + 1] = e2, e3
    return out


def _scale3x_py(g: list[list]) -> list[list]:
    h, w = len(g), len(g[0])
    out = [[None] * (w * 3) for _ in range(h * 3)]
    for y in range(h):
        for x in range(w):
            e = g[y][x]
            ym, yp = max(y - 1, 0), min(y + 1, h - 1)
            xm, xp = max(x - 1, 0), min(x + 1, w - 1)
            a, b, c = g[ym][xm], g[ym][x], g[ym][xp]
            d, f = g[y][xm], g[y][xp]
            gg, hh, i = g[yp][xm], g[yp][x], g[yp][xp]
            if b != hh and d != f:
                e0 = d if d == b else e
                e1 = b if (d == b and e != c) or (b == f and e != a) else e
                e2 = f if b == f else e
                e3 = d if (d == b and e != gg) or (d == hh and e != a) else e
                e4 = e
                e5 = f if (b == f and e != i) or (hh == f and e != c) else e
                e6 = d if d == hh else e
                e7 = hh if (d == hh and e != i) or (hh == f and e != gg) else e
                e8 = f if hh == f else e
            else:
                e0 = e1 = e2 = e3 = e4 = e5 = e6 = e7 = e8 = e
            r0, r1, r2 = out[3 * y], out[3 * y + 1], out[3 * y + 2]
            r0[3 * x:3 * x + 3] = [e0, e1, e2]
            r1[3 * x:3 * x + 3] = [e3, e4, e5]
            r2[3 * x:3 * x + 3] = [e6, e7, e8]
    return out


def _scale2x_np(arr):
    """Vectorised EPX on an (h, w) or (h, w, c) array; compares full pixels."""
    h, w = arr.shape[:2]
    P = arr
    A = np.concatenate([P[:1], P[:-1]], axis=0)
    D = np.concatenate([P[1:], P[-1:]], axis=0)
    C = np.concatenate([P[:, :1], P[:, :-1]], axis=1)
    B = np.concatenate([P[:, 1:], P[:, -1:]], axis=1)

    def eq(u, v):
        return (u == v) if u.ndim == 2 else np.all(u == v, axis=-1)

    ca, cd, ab, bd, dc = eq(C, A), eq(C, D), eq(A, B), eq(B, D), eq(D, C)
    m0 = ca & ~cd & ~ab
    m1 = ab & ~ca & ~bd
    m2 = dc & ~bd & ~ca
    m3 = bd & ~ab & ~dc
    if P.ndim == 3:
        m0, m1, m2, m3 = (m[..., None] for m in (m0, m1, m2, m3))
    e0 = np.where(m0, A, P)
    e1 = np.where(m1, B, P)
    e2 = np.where(m2, C, P)
    e3 = np.where(m3, D, P)
    out = np.empty((h * 2, w * 2) + P.shape[2:], dtype=P.dtype)
    out[0::2, 0::2], out[0::2, 1::2] = e0, e1
    out[1::2, 0::2], out[1::2, 1::2] = e2, e3
    return out


def _scale3x_np(arr):
    h, w = arr.shape[:2]
    E = arr
    pad = np.pad(E, ((1, 1), (1, 1)) + ((0, 0),) * (E.ndim - 2), mode="edge")
    A, B, C = pad[:-2, :-2], pad[:-2, 1:-1], pad[:-2, 2:]
    D, F = pad[1:-1, :-2], pad[1:-1, 2:]
    G, H, I = pad[2:, :-2], pad[2:, 1:-1], pad[2:, 2:]

    def eq(u, v):
        return (u == v) if u.ndim == 2 else np.all(u == v, axis=-1)

    cond = ~eq(B, H) & ~eq(D, F)
    db, bf, dh, hf = eq(D, B), eq(B, F), eq(D, H), eq(H, F)
    ea, ec, eg, ei = eq(E, A), eq(E, C), eq(E, G), eq(E, I)
    masks = [
        (cond & db, D),
        (cond & ((db & ~ec) | (bf & ~ea)), B),
        (cond & bf, F),
        (cond & ((db & ~eg) | (dh & ~ea)), D),
        (np.zeros_like(cond), E),
        (cond & ((bf & ~ei) | (hf & ~ec)), F),
        (cond & dh, D),
        (cond & ((dh & ~ei) | (hf & ~eg)), H),
        (cond & hf, F),
    ]
    out = np.empty((h * 3, w * 3) + E.shape[2:], dtype=E.dtype)
    for k, (m, src) in enumerate(masks):
        if E.ndim == 3:
            m = m[..., None]
        out[k // 3::3, k % 3::3] = np.where(m, src, E)
    return out


def scale_image(img: Image.Image, mode: str, factor: int = 2) -> Image.Image:
    """Scale preserving mode, palette and transparency metadata."""
    if img.mode not in ("P", "L", "RGB", "RGBA"):
        img = img.convert("RGBA")
    if mode == "nearest":
        out = img.resize((img.width * factor, img.height * factor), Image.NEAREST)
    elif np is not None:
        arr = np.asarray(img)
        if mode == "scale2x":
            arr = _scale2x_np(arr)
        elif mode == "scale3x":
            arr = _scale3x_np(arr)
        elif mode == "scale4x":
            arr = _scale2x_np(_scale2x_np(arr))
        else:
            raise ValueError(mode)
        out = Image.fromarray(arr, mode=img.mode)
    else:
        g, _ = _grid(img)
        if mode == "scale2x":
            g = _scale2x_py(g)
        elif mode == "scale3x":
            g = _scale3x_py(g)
        elif mode == "scale4x":
            g = _scale2x_py(_scale2x_py(g))
        else:
            raise ValueError(mode)
        out = Image.new(img.mode, (len(g[0]), len(g)))
        out.putdata([px for row in g for px in row])
    if img.mode == "P":
        out.putpalette(img.getpalette(), rawmode="RGB" if len(img.getpalette()) % 3 == 0 else "RGBA")
    if "transparency" in img.info:
        out.info["transparency"] = img.info["transparency"]
    return out


def save(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if "transparency" in img.info:
        kwargs["transparency"] = img.info["transparency"]
    img.save(path, "PNG", **kwargs)


def colour_count(img: Image.Image) -> int:
    if img.mode == "P":
        return len(set(_pixels(img)))
    return len(set(_pixels(img.convert("RGBA"))))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input")
    p.add_argument("--output")
    p.add_argument("--family", help="directory of PNG frames to transform together")
    p.add_argument("--output-dir")
    p.add_argument("--mode", choices=MODES, default="scale2x")
    p.add_argument("--factor", type=int, default=2, help="nearest mode factor")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    if a.family:
        if not a.output_dir:
            sys.exit("--family needs --output-dir")
        src_dir, out_dir = Path(a.family), Path(a.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        entries = []
        for path in sorted(src_dir.glob("*.png")):
            img = open_image(path)
            out = scale_image(img, a.mode, a.factor)
            dest = out_dir / path.name
            save(out, dest)
            entries.append({"file": path.name, "source_sha256": sha256_file(path), "output_sha256": sha256_file(dest),
                            "mode": img.mode, "size": list(img.size), "output_size": list(out.size),
                            "colours_in": colour_count(img), "colours_out": colour_count(out)})
        family_digest = hashlib.sha256("".join(e["output_sha256"] for e in entries).encode()).hexdigest()
        manifest = {"schema": "sprite-forge/pixel-scale-family-v1", "mode": a.mode,
                    "factor": a.factor if a.mode == "nearest" else {"scale2x": 2, "scale3x": 3, "scale4x": 4}[a.mode],
                    "frames": entries, "family_sha256": family_digest,
                    "palette_preserved": all(e["colours_out"] <= e["colours_in"] for e in entries)}
        (out_dir / "family.json").write_text(json.dumps(manifest, indent=2))
        print(json.dumps(manifest, indent=2) if a.json else
              f"{a.mode}: {len(entries)} frames -> {out_dir}, family sha256 {family_digest[:16]}..., "
              f"palette preserved: {manifest['palette_preserved']}")
        return

    if not (a.input and a.output):
        sys.exit("need --input and --output, or --family and --output-dir")
    img = open_image(a.input)
    out = scale_image(img, a.mode, a.factor)
    save(out, Path(a.output))
    info = {"mode": a.mode, "input_mode": img.mode, "size": list(img.size), "output_size": list(out.size),
            "colours_in": colour_count(img), "colours_out": colour_count(out), "output": a.output}
    print(json.dumps(info, indent=2) if a.json else
          f"{a.mode}: {img.size[0]}x{img.size[1]} {img.mode} -> {out.size[0]}x{out.size[1]}, "
          f"colours {info['colours_in']} -> {info['colours_out']} -> {a.output}")


if __name__ == "__main__":
    main()
