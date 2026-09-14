#!/usr/bin/env python3
"""Combine frames into a sprite sheet with atlas metadata.

Atlas formats:
  --atlas json      legacy Phaser-style {frames: {frame_000: {x,y,w,h}}, meta}
  --atlas xml       TextureAtlas XML (Unity/TexturePacker style)
  --atlas v2        sprite-forge/atlas-v2 manifest: cell, directions, states {fps, loop, frames},
                    anchor {feet_y, pivot}, provenance (input/config sha256). Frames are pasted at
                    cell origin (no centring/rescale) so the canvas contract from align_frames.py holds.
  --aseprite-json   additionally write the Aseprite/Phaser array format (frames[], meta.frameTags[])

Usage:
  stitch_spritesheet.py --input-dir frames/ --cols 8 --atlas json -o sheet.png
  stitch_spritesheet.py --input-dir aligned/ --atlas v2 --state walk:12:loop --cols 8 -o walk.png
  stitch_spritesheet.py --input-dir dirs/ --atlas v2 --directions 8 --cols 8 -o turnaround.png
  stitch_spritesheet.py --input-dir frames/ --atlas v2 --state idle:8:loop --state attack:12:once \
      --state-frames idle=0-5 --state-frames attack=6-13 --aseprite-json -o hero.png
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _images import open_image  # noqa: E402

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)

DIRECTIONS_8 = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
DIRECTIONS_4 = ["S", "E", "N", "W"]


def collect_frames(inputs: list | None, input_dir: str | None) -> list[Path]:
    if inputs:
        return [Path(f) for f in inputs]
    if input_dir:
        d = Path(input_dir)
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
        return sorted(f for f in d.iterdir() if f.suffix.lower() in exts)
    return []


def parse_size(s: str) -> tuple[int, int]:
    parts = s.lower().split("x")
    return int(parts[0]), int(parts[1])


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stitch(frames: list[Path], cols: int, rows: int, cell_w: int, cell_h: int,
           padding: int, fit: bool, background=(0, 0, 0, 0)) -> Image.Image:
    """fit=True (legacy) rescales and centres each frame; fit=False pastes at the cell origin."""
    sheet_w = cols * cell_w + padding * (cols - 1)
    sheet_h = rows * cell_h + padding * (rows - 1)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), background)
    for i, frame_path in enumerate(frames):
        r, c = divmod(i, cols)
        if r >= rows:
            break
        img = open_image(frame_path, "RGBA")
        if img.width == 0 or img.height == 0:
            continue
        x0, y0 = c * (cell_w + padding), r * (cell_h + padding)
        if fit and (img.width, img.height) != (cell_w, cell_h):
            rw = min(cell_w / img.width, cell_h / img.height)
            new_w, new_h = max(1, int(img.width * rw)), max(1, int(img.height * rw))
            resample = Image.NEAREST if max(img.size) <= 256 else Image.LANCZOS
            img = img.resize((new_w, new_h), resample)
            x0 += (cell_w - new_w) // 2
            y0 += (cell_h - new_h) // 2
        elif not fit and (img.width > cell_w or img.height > cell_h):
            img = img.crop((0, 0, min(img.width, cell_w), min(img.height, cell_h)))
        sheet.paste(img, (x0, y0), img)
    return sheet


def frame_rects(n: int, cols: int, cell_w: int, cell_h: int, padding: int) -> list[list[int]]:
    return [[c * (cell_w + padding), r * (cell_h + padding), cell_w, cell_h]
            for r, c in (divmod(i, cols) for i in range(n))]


def write_json_atlas(n, cols, cell_w, cell_h, padding, sheet_w, sheet_h, output) -> Path:
    atlas = {"frames": {}, "meta": {"image": Path(output).name, "size": {"w": sheet_w, "h": sheet_h},
                                    "format": "RGBA8888", "scale": 1}}
    for i, (x, y, w, h) in enumerate(frame_rects(n, cols, cell_w, cell_h, padding)):
        atlas["frames"][f"frame_{i:03d}"] = {"x": x, "y": y, "w": w, "h": h}
    atlas_path = Path(output).with_suffix(".json")
    atlas_path.write_text(json.dumps(atlas, indent=2))
    return atlas_path


def write_xml_atlas(n, cols, cell_w, cell_h, padding, output) -> Path:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', f'<TextureAtlas imagePath="{Path(output).name}">']
    for i, (x, y, w, h) in enumerate(frame_rects(n, cols, cell_w, cell_h, padding)):
        lines.append(f'  <SubTexture name="frame_{i:03d}" x="{x}" y="{y}" width="{w}" height="{h}"/>')
    lines.append("</TextureAtlas>")
    atlas_path = Path(output).with_suffix(".xml")
    atlas_path.write_text("\n".join(lines))
    return atlas_path


def parse_states(state_specs: list[str] | None, frame_specs: list[str] | None, n: int) -> dict:
    """--state name:fps[:loop|once]  and  --state-frames name=a-b (inclusive) or name=a,b,c."""
    states: dict[str, dict] = {}
    for spec in state_specs or []:
        parts = spec.split(":")
        name = parts[0]
        fps = int(parts[1]) if len(parts) > 1 and parts[1] else 12
        loop = (parts[2] if len(parts) > 2 else "loop") != "once"
        states[name] = {"fps": fps, "loop": loop, "indices": None}
    for spec in frame_specs or []:
        name, _, rng = spec.partition("=")
        if name not in states:
            states[name] = {"fps": 12, "loop": True, "indices": None}
        if "-" in rng:
            a, b = rng.split("-")
            states[name]["indices"] = list(range(int(a), int(b) + 1))
        else:
            states[name]["indices"] = [int(v) for v in rng.split(",") if v]
    if not states:
        states["default"] = {"fps": 12, "loop": True, "indices": None}
    unassigned = [s for s in states.values() if s["indices"] is None]
    if unassigned:
        if len(unassigned) > 1:
            sys.exit("more than one --state without --state-frames; give explicit ranges")
        used = {i for s in states.values() if s["indices"] for i in s["indices"]}
        unassigned[0]["indices"] = [i for i in range(n) if i not in used]
    for name, s in states.items():
        bad = [i for i in s["indices"] if i < 0 or i >= n]
        if bad:
            sys.exit(f"state {name} references frames outside 0..{n - 1}: {bad}")
    return states


def detect_feet_y(frames: list[Path], alpha_threshold: int = 127, min_row_fraction: float = 0.05) -> int | None:
    """Reuse align_frames.measure when available for the manifest anchor."""
    try:
        from align_frames import measure  # type: ignore
    except ImportError:
        return None
    feet = []
    for f in frames:
        m = measure(open_image(f, "RGBA"), alpha_threshold, min_row_fraction)
        if m:
            feet.append(m["feet"])
    if not feet:
        return None
    feet.sort()
    return feet[len(feet) // 2]


def write_v2_manifest(frames, rects, cols, rows, cell, directions, states, output, generator,
                      config, feet_y, extra) -> Path:
    manifest = {
        "schema": "sprite-forge/atlas-v2",
        "image": Path(output).name,
        "size": [cols * cell[0] + config["padding"] * (cols - 1), rows * cell[1] + config["padding"] * (rows - 1)],
        "cell": list(cell),
        "grid": [cols, rows],
        "padding": config["padding"],
        "directions": directions,
        "states": {name: {"fps": s["fps"], "loop": s["loop"], "frames": [rects[i] for i in s["indices"]],
                          "indices": s["indices"]} for name, s in states.items()},
        "anchor": {"feet_y": feet_y, "pivot": [0.5, 1.0]},
        "frames": [{"index": i, "source": f.name, "rect": rects[i], "sha256": sha256_file(f)}
                   for i, f in enumerate(frames)],
        "provenance": {
            "generator": generator,
            "inputs_sha256": [sha256_file(f) for f in frames],
            "config": config,
            "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        },
    }
    if extra:
        manifest["provenance"].update(extra)
    path = Path(output).with_suffix(".json")
    path.write_text(json.dumps(manifest, indent=2))
    return path


def write_aseprite_json(frames, rects, cell, states, output, sheet_size) -> Path:
    """Aseprite 'array' export shape consumed by Phaser, Flame, Godot importers."""
    fps_default = next(iter(states.values()))["fps"]
    data = {
        "frames": [{"filename": f"frame_{i:03d}", "frame": {"x": x, "y": y, "w": w, "h": h},
                    "rotated": False, "trimmed": False,
                    "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
                    "sourceSize": {"w": cell[0], "h": cell[1]},
                    "duration": int(round(1000 / fps_default))}
                   for i, (x, y, w, h) in enumerate(rects)],
        "meta": {"app": "sprite-forge", "version": "2", "image": Path(output).name, "format": "RGBA8888",
                 "size": {"w": sheet_size[0], "h": sheet_size[1]}, "scale": "1",
                 "frameTags": [{"name": name, "from": min(s["indices"]), "to": max(s["indices"]),
                                "direction": "forward", "repeat": None if s["loop"] else 1}
                               for name, s in states.items()]},
    }
    for name, s in states.items():
        for i in s["indices"]:
            data["frames"][i]["duration"] = int(round(1000 / s["fps"]))
    path = Path(output).with_name(Path(output).stem + ".aseprite.json")
    path.write_text(json.dumps(data, indent=2))
    return path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--inputs", nargs="+", help="Frame image files")
    p.add_argument("--input-dir", help="Directory of frame images (sorted)")
    p.add_argument("--cols", type=int, help="Columns (default: auto)")
    p.add_argument("--rows", type=int, help="Rows (default: auto)")
    p.add_argument("--layout", choices=["strip", "grid"], help="Layout mode")
    p.add_argument("--cell-size", help="Cell size WxH (default: largest frame)")
    p.add_argument("--padding", type=int, default=0, help="Pixels between frames")
    p.add_argument("--fit", choices=["scale", "origin"], help="scale: legacy centre+rescale; origin: paste at (0,0). "
                                                              "Default: origin for --atlas v2, scale otherwise")
    p.add_argument("-o", "--output", default="spritesheet.png", help="Output file")
    p.add_argument("--atlas", choices=["json", "xml", "v2", "none"], default="json", help="Atlas metadata format")
    p.add_argument("--directions", help="v2: 8, 4, or a comma list like S,SE,E,... (frames ordered by direction)")
    p.add_argument("--state", action="append", help="v2: name:fps[:loop|once]; repeatable")
    p.add_argument("--state-frames", action="append", help="v2: name=a-b or name=a,b,c frame indices")
    p.add_argument("--feet-y", type=int, help="v2: anchor feet row within the cell (default: measured)")
    p.add_argument("--generator", default="sprite-forge/stitch_spritesheet.py", help="v2 provenance label")
    p.add_argument("--provenance", action="append", help="v2: extra key=value recorded in provenance")
    p.add_argument("--aseprite-json", action="store_true", help="also write <stem>.aseprite.json")
    a = p.parse_args()

    frames = collect_frames(a.inputs, a.input_dir)
    if not frames:
        sys.exit("No frames found. Use --inputs or --input-dir.")
    n = len(frames)

    if a.cell_size:
        cell_w, cell_h = parse_size(a.cell_size)
    else:
        sizes = [open_image(f).size for f in frames]
        cell_w, cell_h = max(s[0] for s in sizes), max(s[1] for s in sizes)

    directions = None
    if a.directions:
        directions = (DIRECTIONS_8 if a.directions == "8" else DIRECTIONS_4 if a.directions == "4"
                      else [d.strip() for d in a.directions.split(",")])
        if n % len(directions) != 0:
            sys.exit(f"{n} frames is not a multiple of {len(directions)} directions")

    if a.cols:
        cols = a.cols
        rows = a.rows or math.ceil(n / cols)
    elif a.rows:
        rows = a.rows
        cols = math.ceil(n / rows)
    elif directions and n > len(directions):
        cols = n // len(directions)   # one row per direction
        rows = len(directions)
    elif a.layout == "strip" or (a.layout is None and n <= 8):
        cols, rows = n, 1
    else:
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

    fit = (a.fit or ("origin" if a.atlas == "v2" else "scale")) == "scale"
    sheet = stitch(frames, cols, rows, cell_w, cell_h, a.padding, fit)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.output)

    atlas_path = None
    extra_paths = []
    if a.atlas == "json":
        atlas_path = write_json_atlas(n, cols, cell_w, cell_h, a.padding, sheet.width, sheet.height, a.output)
    elif a.atlas == "xml":
        atlas_path = write_xml_atlas(n, cols, cell_w, cell_h, a.padding, a.output)
    elif a.atlas == "v2":
        rects = frame_rects(n, cols, cell_w, cell_h, a.padding)
        states = parse_states(a.state, a.state_frames, n)
        if directions and not a.state:
            per = n // len(directions)
            states = {d: {"fps": 12, "loop": True, "indices": list(range(k * per, (k + 1) * per))}
                      for k, d in enumerate(directions)}
        feet_y = a.feet_y if a.feet_y is not None else detect_feet_y(frames)
        config = {"cols": cols, "rows": rows, "cell": [cell_w, cell_h], "padding": a.padding, "fit": a.fit or "origin",
                  "directions": directions, "states": {k: {"fps": v["fps"], "loop": v["loop"]} for k, v in states.items()}}
        extra = dict(kv.partition("=")[::2] for kv in (a.provenance or []))
        atlas_path = write_v2_manifest(frames, rects, cols, rows, (cell_w, cell_h), directions, states, a.output,
                                       a.generator, config, feet_y, extra)
        if a.aseprite_json:
            extra_paths.append(write_aseprite_json(frames, rects, (cell_w, cell_h), states, a.output, sheet.size))
    elif a.aseprite_json:
        rects = frame_rects(n, cols, cell_w, cell_h, a.padding)
        extra_paths.append(write_aseprite_json(frames, rects, (cell_w, cell_h), parse_states(a.state, a.state_frames, n),
                                               a.output, sheet.size))

    msg = f", atlas: {atlas_path}" if atlas_path else ""
    if extra_paths:
        msg += ", " + ", ".join(str(x) for x in extra_paths)
    print(f"Stitched {n} frames -> {cols}x{rows} grid ({sheet.width}x{sheet.height}){msg}")


if __name__ == "__main__":
    main()
