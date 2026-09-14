#!/usr/bin/env python3
"""Align animation frames to a shared feet line and character height (anti-jitter).

Naive alpha-bbox alignment fails on anti-aliased halos and baked shadows. This uses the
practitioner rule: the feet line is the lowest row where at least --min-row-fraction of the
bbox width is solidly opaque (alpha > --alpha-threshold); the head line is the symmetric
top row. Every frame is scaled so its character height matches the reference frame, then
offset so its feet line lands on the reference feet line. The canvas is preserved at the
source size (or forced with --cell WxH) so scale never drifts between frames.

Also: --dedup drops consecutive near-duplicate frames (dHash), --loop-check reports how
close the last frame is to the first, and the matte-consistency check reports solid-pixel
flips and alpha-edge perimeter variation between frames (matting flicker moves the perimeter).

Usage:
  align_frames.py --input-dir frames/ --output-dir aligned/
  align_frames.py --input-dir frames/ --output-dir aligned/ --cell 128x128 --dedup 6 --loop-check
  align_frames.py --input-dir frames/ --output-dir aligned/ --no-scale --ref-frame 0

Writes aligned/alignment.json with per-frame feet/head/scale/offset and summary stats.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _images import open_image  # noqa: E402

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)

EXTS = {".png", ".webp", ".gif", ".bmp"}


def _pixels(img):
    """Flat pixel sequence; Pillow 12 deprecates getdata in favour of get_flattened_data."""
    fn = getattr(img, "get_flattened_data", None)
    return list(fn()) if fn else list(img.getdata())


# ------------------------------------------------------------- measurement

def alpha_rows(img: Image.Image, threshold: int) -> tuple[list[int], int, int]:
    """Per-row solid-pixel counts plus bbox x-extent of solid pixels."""
    w, h = img.size
    data = img.getchannel("A").tobytes()
    counts = [0] * h
    xmin, xmax = w, -1
    for y in range(h):
        row = data[y * w:(y + 1) * w]
        n = 0
        for x, a in enumerate(row):
            if a > threshold:
                n += 1
                if x < xmin:
                    xmin = x
                if x > xmax:
                    xmax = x
        counts[y] = n
    return counts, xmin, xmax


def measure(img: Image.Image, alpha_threshold: int, min_row_fraction: float) -> dict | None:
    """Feet line, head line, solid bbox. Returns None for empty frames."""
    counts, xmin, xmax = alpha_rows(img, alpha_threshold)
    if xmax < 0:
        return None
    bbox_w = xmax - xmin + 1
    need = max(1, int(round(bbox_w * min_row_fraction)))
    feet = next((y for y in range(len(counts) - 1, -1, -1) if counts[y] >= need), None)
    head = next((y for y in range(len(counts)) if counts[y] >= need), None)
    if feet is None or head is None or feet < head:
        return None
    # Solid-column extent restricted to the head..feet band (ignores shadow spread below feet).
    return {"feet": feet, "head": head, "height": feet - head + 1,
            "xmin": xmin, "xmax": xmax, "cx": (xmin + xmax) / 2.0}


def dhash(img: Image.Image, size: int = 8) -> int:
    """Difference hash over luminance premultiplied by alpha; 64-bit int."""
    rgba = img.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
    bg.alpha_composite(rgba)
    g = bg.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = _pixels(g)
    bits = 0
    for y in range(size):
        for x in range(size):
            bits = (bits << 1) | (1 if px[y * (size + 1) + x] > px[y * (size + 1) + x + 1] else 0)
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def edge_mask(img: Image.Image, threshold: int) -> set[tuple[int, int]]:
    """Set of (x, y) alpha-edge pixels: solid pixels with a non-solid 4-neighbour."""
    w, h = img.size
    a = img.getchannel("A").tobytes()
    solid = [v > threshold for v in a]
    edges = set()
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if not solid[i]:
                continue
            if (x == 0 or not solid[i - 1] or x == w - 1 or not solid[i + 1]
                    or y == 0 or not solid[i - w] or y == h - 1 or not solid[i + w]):
                edges.add((x, y))
    return edges


# -------------------------------------------------------------- alignment

def collect(inputs: list[str] | None, input_dir: str | None) -> list[Path]:
    if inputs:
        return [Path(p) for p in inputs]
    if input_dir:
        return sorted(p for p in Path(input_dir).iterdir() if p.suffix.lower() in EXTS)
    return []


def align(frames: list[Path], out_dir: Path, *, alpha_threshold: int, min_row_fraction: float,
          cell: tuple[int, int] | None, scale_enabled: bool, ref_index: int | None,
          anchor_x: str, dedup: int | None, loop_check: bool, feet_at: float | None) -> dict:
    images = [open_image(p, "RGBA") for p in frames]
    metrics = [measure(im, alpha_threshold, min_row_fraction) for im in images]
    valid = [i for i, m in enumerate(metrics) if m]
    if not valid:
        sys.exit("no frame has solid pixels above the alpha threshold")

    if ref_index is None:
        heights = sorted((metrics[i]["height"], i) for i in valid)
        ref_index = heights[len(heights) // 2][1]  # median height frame
    ref = metrics[ref_index]
    if ref is None:
        sys.exit(f"reference frame {ref_index} is empty")

    # Scale every frame to the reference height first so the canvas can hold the largest result.
    scaled: list[tuple[Image.Image, dict | None, float]] = []
    for src, m in zip(images, metrics):
        if m is None:
            scaled.append((src, None, 1.0))
            continue
        scale = (ref["height"] / m["height"]) if scale_enabled else 1.0
        if abs(scale - 1.0) > 1e-6:
            new_size = (max(1, int(round(src.width * scale))), max(1, int(round(src.height * scale))))
            resample = Image.NEAREST if src.width <= 256 else Image.LANCZOS
            work = src.resize(new_size, resample)
            m2 = measure(work, alpha_threshold, min_row_fraction) or m
        else:
            work, m2 = src, m
        scaled.append((work, m2, scale))

    if cell:
        canvas = cell
    else:
        # Reference size, grown to fit any frame that scaled up past it, so nothing is clipped.
        canvas = (max([images[ref_index].width] + [w.width for w, m2, _ in scaled if m2]),
                  max([images[ref_index].height] + [w.height for w, m2, _ in scaled if m2]))
    cw, ch = canvas
    # Where the reference feet line lands on the output canvas.
    if feet_at is not None:
        target_feet = int(round(ch * feet_at))
    elif cell:
        target_feet = ch - max(1, int(round(ch * 0.05)))  # keep a small margin below the feet
    else:
        target_feet = ref["feet"]
    target_cx = cw / 2.0 if (cell or anchor_x == "center") else ref["cx"]

    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    kept: list[tuple[int, Image.Image, int]] = []
    prev_hash = None
    for i, (m, (work, m2, scale)) in enumerate(zip(metrics, scaled)):
        rec = {"index": i, "source": frames[i].name}
        if m is None or m2 is None:
            rec.update({"dropped": "empty"})
            records.append(rec)
            continue
        offset_y = int(round(target_feet - m2["feet"]))
        offset_x = int(round(target_cx - m2["cx"])) if anchor_x != "none" else 0
        out = Image.new("RGBA", canvas, (0, 0, 0, 0))
        out.paste(work, (offset_x, offset_y), work)
        h = dhash(out)
        rec.update({"feet": m["feet"], "head": m["head"], "height": m["height"], "scale": round(scale, 4),
                    "offset": [offset_x, offset_y], "dhash": f"{h:016x}"})
        if dedup is not None and prev_hash is not None and hamming(h, prev_hash) < dedup:
            rec["dropped"] = f"duplicate (dhash distance {hamming(h, prev_hash)} < {dedup})"
            records.append(rec)
            continue
        prev_hash = h
        name = f"frame_{len(kept):04d}.png"
        out.save(out_dir / name)
        rec["output"] = name
        kept.append((i, out, h))
        records.append(rec)

    # Post-alignment verification on the written frames.
    post = [measure(im, alpha_threshold, min_row_fraction) for _, im, _ in kept]
    feet_lines = [p["feet"] for p in post if p]
    heights = [p["height"] for p in post if p]
    # Matte consistency: fraction of solid pixels that flip between consecutive frames, and the
    # variation of the alpha-edge perimeter (holes/halo changes move it, plain translation does not).
    flips, perimeters = [], []
    prev_solid = None
    for _, im, _ in kept:
        solid = {i for i, v in enumerate(im.getchannel("A").tobytes()) if v > alpha_threshold}
        perimeters.append(len(edge_mask(im, alpha_threshold)))
        if prev_solid is not None:
            flips.append(round(len(solid ^ prev_solid) / max(1, len(solid | prev_solid)), 4))
        prev_solid = solid
    perim_cv = (statistics.pstdev(perimeters) / statistics.mean(perimeters)) if len(perimeters) > 1 and statistics.mean(perimeters) else 0.0
    summary = {
        "reference_index": ref_index, "canvas": list(canvas), "target_feet": target_feet,
        "kept": len(kept), "dropped": len(frames) - len(kept),
        "feet_line_variance": round(statistics.pvariance(feet_lines), 4) if len(feet_lines) > 1 else 0.0,
        "feet_line_range": [min(feet_lines), max(feet_lines)] if feet_lines else None,
        "height_range": [min(heights), max(heights)] if heights else None,
        "solid_flip_mean": round(statistics.mean(flips), 4) if flips else 0.0,
        "solid_flip_max": max(flips) if flips else 0.0,
        "perimeter_cv": round(perim_cv, 4),
    }
    if loop_check and len(kept) > 1:
        summary["loop_dhash_distance"] = hamming(kept[0][2], kept[-1][2])
        summary["loop_note"] = ("first and last frames are near-identical; drop the last frame "
                                "for a seamless loop" if summary["loop_dhash_distance"] <= 4 else
                                "first/last differ; a first+last-frame video model or an explicit "
                                "return-to-pose frame closes the loop")
    result = {"schema": "sprite-forge/alignment-v1", "summary": summary, "frames": records}
    (out_dir / "alignment.json").write_text(json.dumps(result, indent=2))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inputs", nargs="+")
    p.add_argument("--input-dir")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--cell", help="force output canvas WxH (default: preserve source canvas)")
    p.add_argument("--alpha-threshold", type=int, default=127, help="solid pixel = alpha > this (default 127)")
    p.add_argument("--min-row-fraction", type=float, default=0.05,
                   help="row counts as body when >= this fraction of bbox width is solid (default 0.05)")
    p.add_argument("--no-scale", action="store_true", help="only translate; never rescale frames")
    p.add_argument("--ref-frame", type=int, help="reference frame index (default: median character height)")
    p.add_argument("--anchor-x", choices=("center", "ref", "none"), default="ref",
                   help="horizontal alignment: canvas centre, reference bbox centre, or none")
    p.add_argument("--feet-at", type=float, help="place feet line at this fraction of canvas height (0-1)")
    p.add_argument("--dedup", type=int, help="drop consecutive frames with dHash distance below N (try 4-8)")
    p.add_argument("--loop-check", action="store_true")
    p.add_argument("--json", action="store_true", help="print the full alignment.json to stdout")
    a = p.parse_args()

    frames = collect(a.inputs, a.input_dir)
    if not frames:
        sys.exit("no frames found; use --inputs or --input-dir")
    cell = None
    if a.cell:
        w, h = a.cell.lower().split("x")
        cell = (int(w), int(h))
    result = align(frames, Path(a.output_dir), alpha_threshold=a.alpha_threshold,
                   min_row_fraction=a.min_row_fraction, cell=cell, scale_enabled=not a.no_scale,
                   ref_index=a.ref_frame, anchor_x=a.anchor_x, dedup=a.dedup, loop_check=a.loop_check,
                   feet_at=a.feet_at)
    s = result["summary"]
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Aligned {s['kept']} frames (dropped {s['dropped']}) on {s['canvas'][0]}x{s['canvas'][1]}; "
              f"feet line variance {s['feet_line_variance']} px^2, range {s['feet_line_range']}, "
              f"solid flip mean {s['solid_flip_mean']} max {s['solid_flip_max']}, perimeter cv {s['perimeter_cv']}"
              + (f", loop distance {s['loop_dhash_distance']}" if "loop_dhash_distance" in s else ""))
        if s["perimeter_cv"] > 0.15:
            print("  warning: alpha-edge perimeter varies >15% between frames; the matte is inconsistent "
                  "(per-frame rembg?). Regenerate on chroma and key once with chroma_key.py.", file=sys.stderr)


if __name__ == "__main__":
    main()
