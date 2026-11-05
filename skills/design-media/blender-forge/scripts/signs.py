"""Lay out a line of Linear A text as a flat cutter mesh. Runs inside Blender.

A line is written like a transliteration: words of signs joined by hyphens, separated by spaces, and numbers as
digits, e.g. "KU-RO 65" or "JA-SA-SA-RA-ME". Signs resolve through the sign registry (by sound value or AB number)
to Unicode glyphs drawn with a font; the registry is read only when a line has signs. Numbers (1–9999) are drawn
as Linear A writes them: units as vertical strokes, tens as horizontal strokes, hundreds as circles, thousands as
circles with four rays, largest first.

The mesh lies in the XY plane: x runs along the line from 0, y = 0 is the middle of the sign height, and z spans
[-0.5, 0.5] (a unit extrusion the caller maps to the cut depth). Numeral pieces are closed solids; font outlines
often are not, which is why the boolean falls back to the Exact solver.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import bmesh
import bpy

DEFAULT_REGISTRY = Path.home() / ".claude/skills/linear-a-decipherment/data/sign-registry.json"
DEFAULT_FONT = Path("/System/Library/Fonts/Supplemental/NotoSansLinearA-Regular.ttf")


class SignError(ValueError):
    pass


@dataclass
class Line:
    mesh: bpy.types.Mesh
    width: float
    glyphs: str = ""
    tokens: list[str] = field(default_factory=list)


def load_registry(path: Path) -> dict[str, str]:
    """Map lower-case sound value and AB number to the sign's Unicode glyph."""
    if not path.is_file():
        raise SignError(f"no sign registry at {path}")
    by_key: dict[str, str] = {}
    for s in json.loads(path.read_text())["signs"]:
        glyph = (s.get("rendering") or {}).get("unicode_glyph")
        if glyph:
            by_key.setdefault(s["name"].lower(), glyph)
            by_key.setdefault(s["ab_number"].lower(), glyph)
    return by_key


def resolve_word(word: str, registry: dict[str, str]) -> str:
    glyphs, missing = [], []
    for sign in word.split("-"):
        key = sign.strip().lower()
        if key in registry:
            glyphs.append(registry[key])
        else:
            missing.append(sign)
    if missing:
        raise SignError(f"not in the sign registry (or no Unicode glyph): {', '.join(missing)}")
    return "".join(glyphs)


def _font_mesh(text: str, font: bpy.types.VectorFont, size: float,
               spacing: float) -> tuple[bmesh.types.BMesh, float, float]:
    """Text → closed bmesh in XY (z in [-0.5, 0.5]); returns (bm, min_x, max_x)."""
    curve = bpy.data.curves.new("glyphs", type="FONT")
    curve.font = font
    curve.body = text
    curve.size = size
    curve.space_character = spacing
    curve.extrude = 0.5
    obj = bpy.data.objects.new("glyphs", curve)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.curves.remove(curve)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bpy.data.meshes.remove(mesh)
    if not bm.verts:
        bm.free()
        raise SignError(f"the font has no outlines for {text!r}")
    xs = [v.co.x for v in bm.verts]
    return bm, min(xs), max(xs)


def _box(bm: bmesh.types.BMesh, x0: float, y0: float, x1: float, y1: float) -> None:
    ret = bmesh.ops.create_cube(bm, size=1.0)
    for v in ret["verts"]:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = -0.5 if v.co.z < 0 else 0.5


def _bar(bm: bmesh.types.BMesh, x0: float, y0: float, x1: float, y1: float, stroke: float) -> None:
    """A closed stroke of width `stroke` from (x0, y0) to (x1, y1), at any angle."""
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    c, s = dx / length, dy / length
    ret = bmesh.ops.create_cube(bm, size=1.0)
    for v in ret["verts"]:
        u, w = v.co.x * length, v.co.y * stroke  # along, across
        v.co.x = (x0 + x1) / 2 + u * c - w * s
        v.co.y = (y0 + y1) / 2 + u * s + w * c
        # v.co.z stays at ±0.5


def _ring(bm: bmesh.types.BMesh, cx: float, cy: float, r: float, stroke: float, segments: int = 32) -> None:
    """Closed annulus: outer and inner circles bridged, then extruded to z in [-0.5, 0.5]."""
    ro, ri = r, max(r - stroke, r * 0.3)
    bottom_o = [bm.verts.new((cx + ro * math.cos(t), cy + ro * math.sin(t), -0.5))
                for t in (2 * math.pi * i / segments for i in range(segments))]
    bottom_i = [bm.verts.new((cx + ri * math.cos(t), cy + ri * math.sin(t), -0.5))
                for t in (2 * math.pi * i / segments for i in range(segments))]
    top_o = [bm.verts.new((v.co.x, v.co.y, 0.5)) for v in bottom_o]
    top_i = [bm.verts.new((v.co.x, v.co.y, 0.5)) for v in bottom_i]
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((bottom_o[j], bottom_o[i], bottom_i[i], bottom_i[j]))  # bottom
        bm.faces.new((top_o[i], top_o[j], top_i[j], top_i[i]))              # top
        bm.faces.new((bottom_o[i], bottom_o[j], top_o[j], top_o[i]))        # outer wall
        bm.faces.new((bottom_i[j], bottom_i[i], top_i[i], top_i[j]))        # inner wall


def _number(bm: bmesh.types.BMesh, n: int, x: float, h: float) -> float:
    """Draw n at x; return the advance. Each order of magnitude is a group, largest first, with up to 5 marks per
    row in two rows (as on the tablets: 7 = 4 over 3)."""
    if not 1 <= n <= 9999:
        raise SignError(f"numbers must be 1–9999, got {n}")
    stroke = h * 0.11
    gap = h * 0.18
    start = x
    digits = [(n // 1000) % 10, (n // 100) % 10, (n // 10) % 10, n % 10]
    kinds = ["thousand", "hundred", "ten", "unit"]
    for count, kind in zip(digits, kinds):
        if not count:
            continue
        top = math.ceil(count / 2) if count > 1 else 1
        rows = [top, count - top] if count > 1 else [1]
        if kind == "unit":
            pitch = stroke * 2.4
            row_h = (h - gap * 0.5) / 2 if len(rows) > 1 else h * 0.8
            for r, k in enumerate(rows):
                y1 = (h / 2 if len(rows) > 1 else row_h / 2) - r * (row_h + gap * 0.5)
                for i in range(k):
                    _box(bm, x + i * pitch, y1 - row_h, x + i * pitch + stroke, y1)
            x += max(rows) * pitch
        elif kind == "ten":
            pitch = stroke * 2.4
            length = h * 0.38
            for c, k in enumerate(rows):  # tens stack vertically, in up to two columns, centred on y = 0
                stack = (rows[0] - 1) * pitch + stroke
                for i in range(k):
                    y1 = stack / 2 - i * pitch
                    _box(bm, x + c * (length + stroke), y1 - stroke, x + c * (length + stroke) + length, y1)
            x += len(rows) * (length + stroke)
        else:
            r = h * 0.17
            # A thousand's rays reach 1.7 r along the diagonals (1.2 r across), so space thousands wider.
            reach = r * 1.7 * math.cos(math.pi / 4) + stroke / 2 if kind == "thousand" else r
            pitch = 2 * reach + stroke
            n_rows = math.ceil(count / 3)
            block = n_rows * 2 * reach + (n_rows - 1) * stroke
            for i in range(count):
                cx = x + reach + (i % 3) * pitch
                cy = block / 2 - reach - (i // 3) * pitch
                _ring(bm, cx, cy, r, stroke)
                if kind == "thousand":
                    for t in range(4):  # four diagonal rays from the ring outward
                        a = math.pi / 4 + t * math.pi / 2
                        _bar(bm, cx + math.cos(a) * (r - stroke / 2), cy + math.sin(a) * (r - stroke / 2),
                             cx + math.cos(a) * r * 1.7, cy + math.sin(a) * r * 1.7, stroke)
            x += min(count, 3) * pitch - stroke
        x += gap
    return x - start - gap


def layout_line(line: str, sign_height: float, registry_path: Path = DEFAULT_REGISTRY,
                font_path: Path = DEFAULT_FONT, raw_text: bool = False, word_gap: float = 0.55,
                letter_spacing: float = 1.1) -> Line:
    """Build the cutter mesh for one line. With raw_text, `line` is drawn as it is (any characters, no numbers)."""
    if not font_path.is_file():
        raise SignError(f"no font at {font_path}")
    font = bpy.data.fonts.load(str(font_path), check_existing=True)
    registry = None  # loaded on the first sign word: numeral-only lines need no registry
    tokens = [line] if raw_text else line.split()
    if not tokens:
        raise SignError("empty line")
    glyph_bm, number_bm = bmesh.new(), bmesh.new()
    number_h = sign_height * 0.8  # numerals as tall as the glyphs' ink, not their em box
    x = 0.0
    glyphs_all = []
    for idx, token in enumerate(tokens):
        if idx:
            x += sign_height * word_gap
        if not raw_text and token.isdigit():
            x += _number(number_bm, int(token), x, number_h)
            continue
        if not raw_text and registry is None:
            registry = load_registry(registry_path)
        text = token if raw_text else resolve_word(token, registry)
        glyphs_all.append(text)
        bm, lo, hi = _font_mesh(text, font, sign_height, letter_spacing)
        for v in bm.verts:
            v.co.x += x - lo
        tmp = bpy.data.meshes.new("tmp")
        bm.to_mesh(tmp)
        bm.free()
        glyph_bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        x += hi - lo
    # Centre all glyphs together on y = 0 (one baseline for the line); numerals are drawn centred already.
    if glyph_bm.verts:
        ys = [v.co.y for v in glyph_bm.verts]
        dy = -(min(ys) + max(ys)) / 2
        for v in glyph_bm.verts:
            v.co.y += dy
    mesh = bpy.data.meshes.new("line")
    for part in (number_bm,):
        tmp = bpy.data.meshes.new("tmp")
        part.to_mesh(tmp)
        glyph_bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    glyph_bm.to_mesh(mesh)
    glyph_bm.free()
    number_bm.free()
    return Line(mesh=mesh, width=x, glyphs=" ".join(glyphs_all), tokens=tokens)
