"""Make a turned vessel (lathe profile spun into a watertight solid), optionally with a band of Linear A signs and
numerals cut into its outer wall, and export it as GLB.

    blender -b --factory-startup --python make_vessel.py -- --out cup.glb [--preset cup | --profile "r,z;r,z;…"]
        [--signs "JA-SA-SA-RA-ME" | --text "𐘱𐘞𐘞𐘴𐘋"] [--band-z 0.7] [--sign-height 9] [--depth 1.2]

Units are millimetres. The profile is the OUTER wall from the foot (first point, on the base) to the rim (last
point); the inner wall is the outer one offset by --wall, with a floor --wall thick. --signs is a transliteration
(see signs.py: words of hyphenated signs, numbers as digits). Writes the GLB and <out>.json (mesh report, the
glyphs placed, the boolean solver used). Exit 1 on any error.
"""

import argparse
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forge_common as fc  # noqa: E402
import signs  # noqa: E402

PRESETS = {
    # Outer profiles (radius, height) in mm, foot to rim.
    "cup": [(22, 0), (24, 3), (30, 20), (36, 42), (40, 60)],          # conical cup
    "bowl": [(20, 0), (28, 4), (44, 16), (54, 30), (57, 40)],         # shallow bowl
    "ladle": [(14, 0), (20, 6), (30, 16), (36, 26), (38, 32)],        # ladle cup (without the handle)
    "jar": [(30, 0), (40, 12), (52, 45), (50, 80), (36, 100), (28, 108), (30, 114)],
    "libation-table": [(46, 0), (48, 6), (46, 10), (42, 14), (44, 30), (52, 36), (54, 40)],
}


def parse_profile(text: str) -> list[tuple[float, float]]:
    points = []
    for pair in text.split(";"):
        values = pair.split(",")
        try:
            if len(values) != 2:
                raise ValueError
            points.append((float(values[0]), float(values[1])))
        except ValueError:
            fc.fail(f'bad --profile {text!r}: expected "r,z;r,z;…" in mm, got {pair!r}')
    return points


def check_profile(profile: list[tuple[float, float]], wall: float) -> None:
    if len(profile) < 2 or any(len(p) != 2 for p in profile):
        fc.fail("the profile needs at least two (r, z) points")
    if any(z1 <= z0 for (_, z0), (_, z1) in zip(profile, profile[1:])):
        fc.fail("profile heights must rise strictly from foot to rim")
    if min(r for r, _ in profile) <= wall:
        fc.fail(f"--wall {wall} mm is not thinner than the narrowest radius {min(r for r, _ in profile)} mm")
    if profile[-1][1] - profile[0][1] <= 2 * wall:
        fc.fail(f"the vessel is {profile[-1][1] - profile[0][1]} mm tall: too short for a {wall} mm floor and wall")
    # The inner wall is the outer one moved inward by `wall` (radially). Across a segment tilted θ from vertical
    # that leaves wall·cos θ of material, so refuse segments above the floor tilted more than 60° (a ledge).
    floor = profile[0][1] + wall
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        if z1 > floor:
            cos_t = (z1 - z0) / math.hypot(r1 - r0, z1 - z0)
            if cos_t < 0.5:
                fc.fail(f"profile segment ({r0},{z0})→({r1},{z1}) is too flat: the wall there would be "
                        f"{wall * cos_t:.2f} mm thick; add points so no segment above the floor leans more than 60°")


def wall_radius(profile: list[tuple[float, float]], z: float) -> float:
    """Outer radius at height z, linear between profile points."""
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return profile[-1][0] if z > profile[-1][1] else profile[0][0]


def build_body(profile: list[tuple[float, float]], wall: float, segments: int) -> bpy.types.Object:
    """Half-section (axis → outer wall → rim → inner wall → floor → axis), spun 360° about Z. The section is an
    open polyline with both ends on the axis: spinning it closes the solid. A closing edge along the axis would
    spin into zero-area faces and a non-manifold pole edge."""
    floor = profile[0][1] + wall
    outer = [(0.0, profile[0][1])] + profile
    # Inner wall from the rim down to the floor, ending exactly on the floor so the cavity's floor is flat at
    # foot + wall (going straight from the last point above the floor to the axis would make it a cone).
    inner = [(r - wall, z) for r, z in reversed(profile) if z > floor]
    inner.append((wall_radius(profile, floor) - wall, floor))
    section = outer + inner + [(0.0, floor)]
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0.0, z)) for r, z in section]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=segments,
                   use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)  # the axis points collapse to poles
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("vessel")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("vessel", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def wrap_cutter(line: signs.Line, profile, band_z: float, depth: float, start_deg: float) -> bpy.types.Object:
    """Wrap the flat line onto the outer wall: x along the line becomes an angle (centred on `start_deg`, 0 = the
    -Y front), y becomes height, and the unit extrusion runs radially from `depth` inside the wall to 2 mm outside.
    The radius is taken per vertex at its own height, so bulging and conical walls are followed."""
    r_band = wall_radius(profile, band_z)
    circumference = 2 * math.pi * r_band
    if line.width > circumference * 0.95:
        fc.fail(f"the band is {line.width:.0f} mm long but the wall's circumference at {band_z:.0f} mm is "
                f"{circumference:.0f} mm; shorten the text or lower --sign-height")
    a0 = math.radians(start_deg)
    for v in line.mesh.vertices:
        u, h, w = v.co.x - line.width / 2, v.co.y, v.co.z  # w in [-0.5, 0.5]
        z = band_z + h
        radial = wall_radius(profile, z) - depth + (w + 0.5) * (depth + 2.0)
        ang = a0 + u / r_band
        v.co = Vector((radial * math.sin(ang), -radial * math.cos(ang), z))
    cutter = bpy.data.objects.new("cutter", line.mesh)
    bpy.context.scene.collection.objects.link(cutter)
    return cutter


def main() -> None:
    p = argparse.ArgumentParser(prog="make_vessel.py")
    p.add_argument("--out", type=Path, required=True, help="output .glb")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--preset", choices=sorted(PRESETS), default="cup")
    g.add_argument("--profile", help='outer profile "r,z;r,z;…" in mm, foot to rim')
    p.add_argument("--wall", type=float, default=4.0, help="wall and floor thickness, mm")
    p.add_argument("--segments", type=int, default=192, help="steps around the axis")
    t = p.add_mutually_exclusive_group()
    t.add_argument("--signs", help="transliteration, e.g. 'JA-SA-SA-RA-ME' or 'KU-RO 65'")
    t.add_argument("--text", help="characters to cut as they are (any font; no numerals)")
    p.add_argument("--registry", type=Path, default=signs.DEFAULT_REGISTRY)
    p.add_argument("--font", type=Path, default=signs.DEFAULT_FONT)
    p.add_argument("--band-z", type=float, default=0.7, help="band centre: fraction of the height above the foot, or mm if > 1")
    p.add_argument("--sign-height", type=float, default=9.0, help="mm")
    p.add_argument("--depth", type=float, default=1.2, help="cut depth into the wall, mm")
    p.add_argument("--spacing", type=float, default=1.15, help="character spacing factor")
    p.add_argument("--start", type=float, default=0.0, help="angle of the band's centre, degrees (0 = front, -Y)")
    p.add_argument("--color", default="0.27,0.26,0.24", help="linear RGB base colour (grey stone)")
    p.add_argument("--sharp-angle", type=float, default=35.0, help="edges sharper than this stay hard, degrees")
    a = fc.parse_args(p)

    profile = parse_profile(a.profile) if a.profile else PRESETS[a.preset]
    check_profile(profile, a.wall)
    if a.depth >= a.wall:
        fc.fail(f"--depth {a.depth} mm would cut through the {a.wall} mm wall")
    fc.clear_scene()
    body = build_body(profile, a.wall, a.segments)
    foot, rim = profile[0][1], profile[-1][1]
    band_z = foot + a.band_z * (rim - foot) if a.band_z <= 1 else a.band_z  # a fraction counts from the foot
    if not foot + a.sign_height / 2 <= band_z <= rim - a.sign_height / 2:
        fc.fail(f"a {a.sign_height} mm band at {band_z:.1f} mm does not fit between the foot ({foot} mm) "
                f"and the rim ({rim} mm)")

    placed, solver = None, None
    if a.signs or a.text:
        try:
            line = signs.layout_line(a.text or a.signs, a.sign_height, a.registry, a.font, raw_text=bool(a.text),
                                     letter_spacing=a.spacing)
        except signs.SignError as exc:
            fc.fail(str(exc))
        cutter = wrap_cutter(line, profile, band_z, a.depth, a.start)
        solver = fc.boolean_difference(body, cutter)
        bpy.data.objects.remove(cutter, do_unlink=True)
        placed = {"line": a.text or a.signs, "glyphs": line.glyphs, "band_z_mm": round(band_z, 2),
                  "band_length_mm": round(line.width, 2), "sign_height_mm": a.sign_height, "depth_mm": a.depth}

    fc.shade_smooth_by_angle(body, a.sharp_angle)
    fc.stone_material(body, tuple(float(c) for c in a.color.split(",")))
    fc.export_glb(body, a.out)
    fc.write_report(a.out.with_suffix(".json"), {
        "out": str(a.out),
        "profile_mm": profile,
        "wall_mm": a.wall,
        "inscription": placed,
        "boolean_solver": solver,
        "mesh": fc.mesh_report(body),
    })


fc.run(main)
