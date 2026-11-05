"""Clean a scanned or downloaded mesh and export it as GLB: weld duplicate vertices, drop small loose fragments, fill
small holes, make normals consistent, and decimate to a triangle budget (UVs and textures are kept).

    blender -b --factory-startup --python clean_scan.py -- --in scan.ply --out scan-clean.glb \
        [--triangles 100000] [--min-part 0.01] [--max-hole 64] [--weld 1e-5]

Reads GLB/glTF, OBJ, PLY or STL. Writes the GLB and <out>.json with the mesh report before and after each step.
Everything runs locally; nothing is uploaded. Licence-restricted scans stay restricted after cleaning: never
publish the output, or a render of it, unless the licence allows. Exit 1 on any error.
"""

import argparse
import sys
from pathlib import Path

import bmesh
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forge_common as fc  # noqa: E402


def components(bm: bmesh.types.BMesh) -> list[list[bmesh.types.BMVert]]:
    bm.verts.ensure_lookup_table()
    seen: set[int] = set()
    parts = []
    for v in bm.verts:
        if v.index in seen:
            continue
        part, stack = [], [v]
        seen.add(v.index)
        while stack:
            cur = stack.pop()
            part.append(cur)
            for e in cur.link_edges:
                o = e.other_vert(cur)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        parts.append(part)
    return parts


def main() -> None:
    p = argparse.ArgumentParser(prog="clean_scan.py")
    p.add_argument("--in", dest="inp", type=Path, required=True, help="GLB/glTF, OBJ, PLY or STL")
    p.add_argument("--out", type=Path, required=True, help="output .glb")
    p.add_argument("--weld", type=float, default=1e-5, help="merge distance as a fraction of the bounding diagonal")
    p.add_argument("--min-part", type=float, default=0.01,
                   help="drop loose parts with fewer vertices than this fraction of the largest part (0 keeps all)")
    p.add_argument("--max-hole", type=int, default=64, help="fill holes bounded by at most this many edges (0 = none)")
    p.add_argument("--triangles", type=int, default=0, help="decimate to about this many triangles (0 = keep)")
    a = fc.parse_args(p)
    if a.out.resolve() == a.inp.resolve():
        fc.fail("--out must differ from --in (the input is never overwritten)")
    if a.triangles < 0 or a.max_hole < 0 or not 0 <= a.min_part < 1 or not 0 <= a.weld < 0.01:
        fc.fail("--triangles and --max-hole must be ≥ 0, --min-part in [0, 1) and --weld in [0, 0.01)")

    fc.clear_scene()
    obj = fc.import_model(a.inp)
    steps = {"input": fc.mesh_report(obj)}

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    diag = fc.bounds_diagonal(obj)  # the box's own diagonal; distance from the origin would over-weld far objects
    # Exporters split vertices at UV seams. Welding them is safe for the texture: UVs live on face corners, so each
    # corner keeps its own UV, and the seam stays a seam in the UV layout while the surface becomes connected.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=diag * a.weld)
    welded = len(obj.data.vertices) - len(bm.verts)

    dropped = 0
    if a.min_part > 0:
        parts = sorted(components(bm), key=len, reverse=True)
        limit = len(parts[0]) * a.min_part if parts else 0
        doomed = [v for part in parts[1:] if len(part) < limit for v in part]
        dropped = sum(1 for part in parts[1:] if len(part) < limit)
        bmesh.ops.delete(bm, geom=doomed, context="VERTS")

    filled = 0
    if a.max_hole > 0:
        boundary = [e for e in bm.edges if e.is_boundary]
        if boundary:
            ret = bmesh.ops.holes_fill(bm, edges=boundary, sides=a.max_hole)
            filled = len(ret["faces"])
            if ret["faces"]:
                bmesh.ops.triangulate(bm, faces=ret["faces"])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    steps["cleaned"] = fc.mesh_report(obj)

    if a.triangles and steps["cleaned"]["triangles"] > a.triangles:
        mod = obj.modifiers.new("decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = a.triangles / steps["cleaned"]["triangles"]
        mod.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        steps["decimated"] = fc.mesh_report(obj)

    fc.export_glb(obj, a.out)
    fc.write_report(a.out.with_suffix(".json"), {
        "in": str(a.inp),
        "out": str(a.out),
        "welded_vertices": welded,
        "dropped_parts": dropped,
        "filled_faces": filled,
        "steps": steps,
    })


fc.run(main)
