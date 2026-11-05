"""Make a clay tablet: a rounded slab with lines of Linear A signs and numerals cut into its face (and optionally
its back), exported as GLB.

    blender -b --factory-startup --python make_tablet.py -- --out ht.glb --width 60 --height 90 \
        --line "KU-RO 65" --line "PA-I-TO 12" [--back-line "…"] [--rules]

Units are millimetres. The tablet stands upright: width along X, height along Z, the face toward -Y (the camera
side in turntable.py), the back toward +Y. Lines run left to right from the top; back lines read correctly when
the tablet is turned around. Each --line is a transliteration (signs.py). Writes the GLB and <out>.json.
Exit 1 on any error, including text that does not fit.
"""

import argparse
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forge_common as fc  # noqa: E402
import signs  # noqa: E402


def build_slab(width: float, height: float, thickness: float, bevel: float, segments: int) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * width, v.co.y * thickness, v.co.z * height))
    bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=bevel, offset_type="OFFSET",
                    segments=segments, profile=0.5, affect="EDGES", clamp_overlap=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("tablet")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("tablet", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def place_line(line: signs.Line, x0: float, z_mid: float, face_y: float, depth: float, back: bool) -> bmesh.types.BMesh:
    """Map the flat line onto a face: x along the face, y up, unit extrusion from `depth` inside to 2 mm outside."""
    bm = bmesh.new()
    bm.from_mesh(line.mesh)
    for v in bm.verts:
        x, y, w = v.co.x, v.co.y, v.co.z
        into = depth - (w + 0.5) * (depth + 2.0)  # + = into the slab
        if back:
            v.co = Vector((-(x0 + x), face_y - into, z_mid + y))
        else:
            v.co = Vector((x0 + x, face_y + into, z_mid + y))
    return bm  # both mappings keep the glyphs' winding (determinant > 0), so no normals need fixing


def main() -> None:
    p = argparse.ArgumentParser(prog="make_tablet.py")
    p.add_argument("--out", type=Path, required=True, help="output .glb")
    p.add_argument("--width", type=float, default=60.0, help="mm")
    p.add_argument("--height", type=float, default=90.0, help="mm")
    p.add_argument("--thickness", type=float, default=14.0, help="mm")
    p.add_argument("--bevel", type=float, help="edge rounding, mm (default 35%% of the thickness)")
    p.add_argument("--line", action="append", default=[], help="a line of text for the face, top to bottom")
    p.add_argument("--back-line", action="append", default=[], help="a line for the back")
    p.add_argument("--raw", action="store_true", help="lines are literal characters in --font (no numerals)")
    p.add_argument("--registry", type=Path, default=signs.DEFAULT_REGISTRY)
    p.add_argument("--font", type=Path, default=signs.DEFAULT_FONT)
    p.add_argument("--sign-height", type=float, default=7.0, help="mm")
    p.add_argument("--line-pitch", type=float, help="mm between line centres (default 1.6 × sign height)")
    p.add_argument("--margin", type=float, default=6.0, help="mm from the edges to the text")
    p.add_argument("--depth", type=float, default=0.9, help="cut depth, mm")
    p.add_argument("--rules", action="store_true", help="cut ruling lines between text lines")
    p.add_argument("--color", default="0.36,0.25,0.17", help="linear RGB base colour (fired clay)")
    p.add_argument("--sharp-angle", type=float, default=35.0)
    a = fc.parse_args(p)

    bevel = a.bevel if a.bevel is not None else a.thickness * 0.35
    if not 0 < bevel < min(a.width, a.height, a.thickness) / 2:
        fc.fail(f"--bevel {bevel} mm must be above 0 and under half the smallest dimension")
    if a.margin < bevel:
        fc.fail(f"--margin {a.margin} mm is inside the rounded edge (--bevel {bevel:.1f} mm), where the cut would "
                f"miss the falling surface; raise --margin or lower --bevel")
    if a.depth >= a.thickness / 2:
        fc.fail(f"--depth {a.depth} mm would cut through a {a.thickness} mm tablet from both sides")
    pitch = a.line_pitch or a.sign_height * 1.6
    usable_w = a.width - 2 * a.margin
    fc.clear_scene()
    body = build_slab(a.width, a.height, a.thickness, bevel, 4)

    cutter_bm = bmesh.new()
    placed = {"face": [], "back": []}
    for side, lines in (("face", a.line), ("back", a.back_line)):
        if not lines:
            continue
        needed = (len(lines) - 1) * pitch + a.sign_height
        if needed > a.height - 2 * a.margin:
            fc.fail(f"{len(lines)} lines need {needed:.0f} mm on the {side}, but only "
                    f"{a.height - 2 * a.margin:.0f} mm fit inside the margins")
        top = a.height / 2 - a.margin - a.sign_height / 2
        face_y = -a.thickness / 2 if side == "face" else a.thickness / 2
        for i, text in enumerate(lines):
            try:
                line = signs.layout_line(text, a.sign_height, a.registry, a.font, raw_text=a.raw)
            except signs.SignError as exc:
                fc.fail(f"{side} line {i + 1}: {exc}")
            if line.width > usable_w:
                fc.fail(f"{side} line {i + 1} ({text!r}) is {line.width:.0f} mm wide; {usable_w:.0f} mm fit")
            z_mid = top - i * pitch
            part = place_line(line, -a.width / 2 + a.margin, z_mid, face_y, a.depth, side == "back")
            tmp = bpy.data.meshes.new("tmp")
            part.to_mesh(tmp)
            part.free()
            cutter_bm.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
            bpy.data.meshes.remove(line.mesh)
            placed[side].append({"line": text, "glyphs": line.glyphs, "width_mm": round(line.width, 1)})
            if a.rules and i < len(lines) - 1:  # a groove halfway to the next line
                zr = z_mid - pitch / 2
                ret = bmesh.ops.create_cube(cutter_bm, size=1.0)
                for v in ret["verts"]:
                    x = (usable_w / 2) * (1 if v.co.x > 0 else -1)
                    zz = zr + (0.3 if v.co.z > 0 else -0.3)
                    inside = 0.4 if v.co.y > 0 else -2.0  # 0.4 mm deep, 2 mm proud
                    y = face_y + inside if side == "face" else face_y - inside
                    v.co = Vector((x, y, zz))
                # On the back the box's local y is mirrored; it is a closed box, so recalculating is safe.
                bmesh.ops.recalc_face_normals(cutter_bm, faces=list({f for v in ret["verts"] for f in v.link_faces}))

    solver = None
    if cutter_bm.verts:
        mesh = bpy.data.meshes.new("cutter")
        cutter_bm.to_mesh(mesh)
        cutter = bpy.data.objects.new("cutter", mesh)
        bpy.context.scene.collection.objects.link(cutter)
        solver = fc.boolean_difference(body, cutter)
        bpy.data.objects.remove(cutter, do_unlink=True)
    cutter_bm.free()

    fc.shade_smooth_by_angle(body, a.sharp_angle)
    fc.stone_material(body, tuple(float(c) for c in a.color.split(",")), roughness=0.85)
    fc.export_glb(body, a.out)
    fc.write_report(a.out.with_suffix(".json"), {
        "out": str(a.out),
        "size_mm": [a.width, a.thickness, a.height],
        "lines": placed,
        "boolean_solver": solver,
        "mesh": fc.mesh_report(body),
    })


fc.run(main)
