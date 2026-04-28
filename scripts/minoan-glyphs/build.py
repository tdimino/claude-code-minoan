#!/usr/bin/env python3
"""Build MinoanGlyphs.ttf from SVG outlines using fonttools.

Maps 14 Minoan pictographic glyphs to Private Use Area codepoints
U+E500–U+E50D for terminal rendering via Ghostty font cascade.

Usage:
    python3 build.py [--install]

With --install, copies the built font to ~/Library/Fonts/.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

try:
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
except ImportError:
    print("fonttools not found. Install with: uv pip install fonttools", file=sys.stderr)
    sys.exit(1)

UPM = 1024
ASCENT = 900
DESCENT = -124

GLYPH_MAP = {
    0xE500: ("horns", "HORNS OF CONSECRATION"),
    0xE501: ("labrys", "LABRYS"),
    0xE502: ("bull", "MINOAN BULL"),
    0xE503: ("dolphin", "KNOSSOS DOLPHIN"),
    0xE504: ("swallow", "AKROTIRI SWALLOW"),
    0xE505: ("cat", "SEATED CAT"),
    0xE506: ("sacral-knot", "SACRAL KNOT"),
    0xE507: ("lily", "MINOAN LILY"),
    0xE508: ("spiral", "RUNNING SPIRAL"),
    0xE509: ("octopus", "OCTOPUS"),
    0xE50A: ("wave", "WAVE BAND"),
    0xE50B: ("shield", "FIGURE-EIGHT SHIELD"),
    0xE50C: ("goddess", "MINOAN GODDESS"),
    0xE50D: ("crocus", "CROCUS"),
}


def parse_svg_paths(svg_file: Path) -> list[str]:
    """Extract d= path data from an SVG file."""
    content = svg_file.read_text()
    return re.findall(r'd="([^"]+)"', content)


def path_data_to_commands(d: str) -> list:
    """Parse SVG path d-attribute into a list of (command, args) tuples."""
    tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)', d)
    commands = []
    current_cmd = None
    args = []

    for token in tokens:
        if token.isalpha():
            if current_cmd is not None:
                commands.append((current_cmd, args))
            current_cmd = token
            args = []
        else:
            args.append(float(token))

    if current_cmd is not None:
        commands.append((current_cmd, args))

    return commands


def draw_svg_path_to_pen(path_data: str, pen, y_offset=0):
    """Draw SVG path data to a fonttools pen, flipping Y axis for font coordinates."""
    commands = path_data_to_commands(path_data)
    cx, cy = 0.0, 0.0
    start_x, start_y = 0.0, 0.0

    def flip_y(y):
        return UPM - y + y_offset

    for cmd, args in commands:
        if cmd == 'M':
            i = 0
            while i < len(args):
                x, y = args[i], args[i + 1]
                if i == 0:
                    pen.moveTo((x, flip_y(y)))
                    start_x, start_y = x, y
                else:
                    pen.lineTo((x, flip_y(y)))
                cx, cy = x, y
                i += 2
        elif cmd == 'L':
            i = 0
            while i < len(args):
                x, y = args[i], args[i + 1]
                pen.lineTo((x, flip_y(y)))
                cx, cy = x, y
                i += 2
        elif cmd == 'Q':
            i = 0
            while i < len(args):
                x1, y1, x, y = args[i], args[i + 1], args[i + 2], args[i + 3]
                pen.qCurveTo((x1, flip_y(y1)), (x, flip_y(y)))
                cx, cy = x, y
                i += 4
        elif cmd == 'C':
            i = 0
            while i < len(args):
                x1, y1, x2, y2, x, y = args[i:i + 6]
                pen.curveTo((x1, flip_y(y1)), (x2, flip_y(y2)), (x, flip_y(y)))
                cx, cy = x, y
                i += 6
        elif cmd == 'Z' or cmd == 'z':
            pen.closePath()
            cx, cy = start_x, start_y
        elif cmd == 'H':
            for x in args:
                pen.lineTo((x, flip_y(cy)))
                cx = x
        elif cmd == 'V':
            for y in args:
                pen.lineTo((cx, flip_y(y)))
                cy = y

    return cx, cy


def build_font(svg_dir: Path, output: Path):
    """Build the MinoanGlyphs TTF from SVG files."""
    glyph_names = [".notdef"]
    cmap = {}
    glyph_order = [".notdef"]

    for codepoint, (filename, name) in sorted(GLYPH_MAP.items()):
        glyph_name = filename.replace("-", "_")
        glyph_names.append(glyph_name)
        glyph_order.append(glyph_name)
        cmap[codepoint] = glyph_name

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)

    cmap_table = fb.font["cmap"]
    from fontTools.ttLib.tables._c_m_a_p import cmap_format_12
    for plat_id, enc_id in [(0, 4), (3, 10)]:
        subtable = cmap_format_12(12)
        subtable.platEncID = enc_id
        subtable.platformID = plat_id
        subtable.format = 12
        subtable.reserved = 0
        subtable.length = 0
        subtable.language = 0
        subtable.groups = []
        subtable.cmap = dict(cmap)
        cmap_table.tables.append(subtable)

    name_table = {
        "familyName": "Minoan Glyphs",
        "styleName": "Regular",
        "uniqueFontIdentifier": "1.0;MinoanGlyphs-Regular",
        "fullName": "Minoan Glyphs Regular",
        "version": "Version 1.0",
        "psName": "MinoanGlyphs-Regular",
    }
    fb.setupNameTable(name_table)

    metrics = {}
    metrics[".notdef"] = (UPM, 0)
    for codepoint, (filename, name) in sorted(GLYPH_MAP.items()):
        glyph_name = filename.replace("-", "_")
        metrics[glyph_name] = (UPM, 0)

    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0)

    os2 = fb.font["OS/2"]
    os2.ulUnicodeRange2 |= 0x02000000
    os2.panose.bFamilyType = 5

    fb.setupGlyf({})

    glyphs = {}
    for glyph_name in glyph_order:
        pen = TTGlyphPen(None)
        if glyph_name == ".notdef":
            pen.moveTo((100, 0))
            pen.lineTo((100, 700))
            pen.lineTo((500, 700))
            pen.lineTo((500, 0))
            pen.closePath()
            pen.moveTo((150, 50))
            pen.lineTo((450, 50))
            pen.lineTo((450, 650))
            pen.lineTo((150, 650))
            pen.closePath()
        else:
            filename = glyph_name.replace("_", "-")
            svg_file = svg_dir / f"{filename}.svg"
            if svg_file.exists():
                paths = parse_svg_paths(svg_file)
                for path_d in paths:
                    draw_svg_path_to_pen(path_d, pen)
            else:
                print(f"  Warning: {svg_file} not found, using empty glyph", file=sys.stderr)
                pen.moveTo((0, 0))
                pen.lineTo((0, 0))
                pen.closePath()

        glyphs[glyph_name] = pen.glyph()

    fb.setupGlyf(glyphs)
    fb.setupPost()

    fb.font.save(str(output))
    print(f"Built {output} ({len(cmap)} glyphs)")
    return output


def main():
    parser = argparse.ArgumentParser(description="Build MinoanGlyphs.ttf")
    parser.add_argument("--install", action="store_true", help="Install to ~/Library/Fonts/")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    svg_dir = script_dir / "svgs"
    output = script_dir / "MinoanGlyphs.ttf"

    if not svg_dir.exists():
        print(f"SVG directory not found: {svg_dir}", file=sys.stderr)
        sys.exit(1)

    build_font(svg_dir, output)

    if args.install:
        fonts_dir = Path.home() / "Library" / "Fonts"
        fonts_dir.mkdir(exist_ok=True)
        dest = fonts_dir / "MinoanGlyphs.ttf"
        shutil.copy2(output, dest)
        print(f"Installed to {dest}")


if __name__ == "__main__":
    main()
