"""Shared helpers for blender-forge scripts. Runs inside Blender (bpy), not plain Python.

Every script is run as:
    blender -b --factory-startup --python <script.py> -- <args>
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def parse_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    """Parse only the arguments after Blender's `--` separator."""
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(argv)


def fail(message: str) -> None:
    """Print an error and exit Blender with status 1."""
    print(f"blender-forge: error: {message}", file=sys.stderr)
    sys.stdout.flush()
    sys.exit(1)


def run(main) -> None:
    """Run a script's main. Blender exits 0 after an uncaught Python exception unless started with
    --python-exit-code, so turn every exception into exit 1 here."""
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - report anything, then fail the process
        import traceback

        traceback.print_exc()
        fail(f"{type(exc).__name__}: {exc}")


def boolean_difference(body: bpy.types.Object, cutter: bpy.types.Object) -> str:
    """Subtract `cutter` from `body`. Tries the Manifold solver, which is fast but leaves the mesh unchanged when
    the cutter is not a closed solid (font outlines often aren't), then Exact with self-intersection on a fresh
    copy. Returns the solver that cut cleanly; fails if neither did."""
    original = body.data.copy()
    before = len(original.polygons)
    for solver in ("MANIFOLD", "EXACT"):
        body.modifiers.clear()
        mod = body.modifiers.new("cut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        try:
            mod.solver = solver
        except TypeError:  # older Blender without this solver
            continue
        if solver == "EXACT":
            mod.use_self = True
            mod.use_hole_tolerant = True
        mod.object = cutter
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.modifier_apply(modifier=mod.name)
        report = mesh_report(body)
        if len(body.data.polygons) != before and report["non_manifold_edges"] == 0:
            bpy.data.meshes.remove(original)
            return solver
        print(f"blender-forge: {solver} boolean: {report['non_manifold_edges']} non-manifold edges, "
              f"{len(body.data.polygons) - before:+d} faces; trying the next solver", file=sys.stderr)
        failed = body.data
        body.data = original.copy()
        bpy.data.meshes.remove(failed)
    fail("no boolean solver cut cleanly (check the cutter geometry, depth and sign height)")


def shade_smooth_by_angle(obj: bpy.types.Object, sharp_deg: float) -> None:
    """Smooth faces, but mark edges whose faces meet at more than `sharp_deg` as sharp, so cut walls and box edges
    stay crisp. glTF export splits normals along them."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    limit = math.radians(sharp_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (e.is_manifold and e.calc_face_angle(0.0) > limit)
    bm.to_mesh(obj.data)
    bm.free()


def export_glb(obj: bpy.types.Object, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True)


def stone_material(obj: bpy.types.Object, color: tuple[float, float, float], roughness: float = 0.8) -> None:
    mat = bpy.data.materials.new("stone")
    if mat.node_tree is None:  # Blender < 5 needs this; 5.x materials always have nodes
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def clear_scene() -> None:
    """Remove every object, mesh, material, light and camera from the factory scene."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images):
        for block in list(coll):
            coll.remove(block)


IMPORTERS = {
    ".glb": lambda p: bpy.ops.import_scene.gltf(filepath=p),
    ".gltf": lambda p: bpy.ops.import_scene.gltf(filepath=p),
    ".obj": lambda p: bpy.ops.wm.obj_import(filepath=p),
    ".ply": lambda p: bpy.ops.wm.ply_import(filepath=p),
    ".stl": lambda p: bpy.ops.wm.stl_import(filepath=p),
}


def import_model(path: Path) -> bpy.types.Object:
    """Import a GLB/glTF, OBJ, PLY or STL and join its meshes into one object. Y-up formats become Z-up."""
    if not path.is_file():
        fail(f"no such file: {path}")
    importer = IMPORTERS.get(path.suffix.lower())
    if importer is None:
        fail(f"unsupported format {path.suffix!r}; use one of {', '.join(sorted(IMPORTERS))}")
    importer(str(path))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        fail(f"no mesh in {path}")
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    # Drop empties the importer made, keeping the mesh's world transform.
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in list(bpy.context.scene.objects):
        if o.type == "EMPTY":
            bpy.data.objects.remove(o, do_unlink=True)
    return obj


def bounds_diagonal(obj: bpy.types.Object) -> float:
    """Length of the bounding box's diagonal in object space (not the distance from the origin, which would make
    tolerances huge for objects far from it)."""
    corners = [Vector(c) for c in obj.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return (hi - lo).length or 1.0


def vertex_array(obj: bpy.types.Object):
    """All vertex positions in world space as an (n, 3) numpy array."""
    import numpy as np

    co = np.empty(len(obj.data.vertices) * 3, dtype=np.float64)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    m = np.array(obj.matrix_world)
    return co @ m[:3, :3].T + m[:3, 3]


def world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return lo, hi


def normalize(obj: bpy.types.Object) -> dict:
    """Centre the object's bounding box on the world origin and scale it to a bounding sphere of radius 1,
    so lights, camera clipping and render times don't depend on the file's units (glTF from three.js projects is often in
    millimetres, which the importer reads as metres). Returns the original size and the scale applied."""
    bpy.context.view_layer.update()
    lo, hi = world_bounds(obj)
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2
    obj.location -= centre
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")  # cursor is at world origin in a factory scene
    obj.scale *= 1.0 / radius
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    size = hi - lo
    return {"original_size": [round(size.x, 3), round(size.y, 3), round(size.z, 3)], "scale": 1.0 / radius}


def mesh_report(obj: bpy.types.Object) -> dict:
    """Counts and health checks: triangles, non-manifold edges, loose parts, bounds."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    # Exporters split vertices at UV seams; weld by position (in this copy only) so seams don't count as
    # holes or separate parts.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=bounds_diagonal(obj) * 1e-6)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    # Loose parts: connected components over edges.
    seen: set[int] = set()
    parts = 0
    for v in bm.verts:
        if v.index in seen:
            continue
        parts += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            cur = stack.pop()
            for e in cur.link_edges:
                other = e.other_vert(cur)
                if other.index not in seen:
                    seen.add(other.index)
                    stack.append(other)
    bm.free()
    bpy.context.view_layer.update()
    lo, hi = world_bounds(obj)
    size = hi - lo
    return {
        "vertices": len(obj.data.vertices),
        "triangles": tris,
        "non_manifold_edges": non_manifold,
        "boundary_edges": boundary,
        "loose_parts": parts,
        "size": [round(size.x, 3), round(size.y, 3), round(size.z, 3)],
        "uv_layers": [uv.name for uv in obj.data.uv_layers],
    }


def setup_render(engine: str, samples: int, size: int, transparent: bool, view: str) -> str:
    """Configure engine, resolution, alpha and colour management. Returns the engine id used."""
    scene = bpy.context.scene
    if engine == "cycles":
        scene.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        gpu = False
        for backend in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = backend
            except TypeError:
                continue
            prefs.get_devices()
            devices = [d for d in prefs.devices if d.type == backend]
            if devices:
                for d in prefs.devices:
                    d.use = d.type == backend
                gpu = True
                break
        scene.cycles.device = "GPU" if gpu else "CPU"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        engine_id = f"CYCLES ({'GPU ' + prefs.compute_device_type if gpu else 'CPU'})"
    else:
        ids = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
        scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in ids else "BLENDER_EEVEE_NEXT"
        scene.eevee.taa_render_samples = samples
        engine_id = scene.render.engine
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = view
    scene.view_settings.look = "None"
    return engine_id


def frame_camera(obj: bpy.types.Object, elevation_deg: float, lens_mm: float = 85.0, margin: float = 1.08) -> bpy.types.Object:
    """Camera on the -Y side, raised by `elevation_deg`, aimed at the origin, as close as it can be while every
    vertex stays inside the frame (times `margin`) at every turn about world Z in 10° steps."""
    import numpy as np

    bpy.context.view_layer.update()
    pts = vertex_array(obj)  # every vertex: a sampled subset can miss a thin spike
    el = math.radians(elevation_deg)
    view = np.array([0.0, math.cos(el), -math.sin(el)])  # camera looks along +Y and down
    up = np.array([0.0, math.sin(el), math.cos(el)])
    right = np.array([1.0, 0.0, 0.0])
    tan_half = 36.0 / 2 / lens_mm
    need = 0.0
    for deg in range(0, 360, 10):
        t = math.radians(deg)
        rot = np.array([[math.cos(t), -math.sin(t), 0], [math.sin(t), math.cos(t), 0], [0, 0, 1]])
        p = pts @ rot.T
        # Camera at -dist * view: a point's depth is dist + p·view, so it fits when
        # |lateral| / (dist + p·view) <= tan_half / margin.
        depth_offset = p @ view
        lateral = np.maximum(np.abs(p @ right), np.abs(p @ up))
        need = max(need, float(np.max(lateral * margin / tan_half - depth_offset)))
    dist = need
    cam_data = bpy.data.cameras.new("forge_camera")
    cam_data.lens = lens_mm
    cam_data.sensor_width = 36.0
    cam_data.clip_start = 0.01
    cam_data.clip_end = dist * 10
    cam = bpy.data.objects.new("forge_camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector((0.0, -dist * math.cos(el), dist * math.sin(el)))
    direction = Vector((0, 0, 0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def light_rig(radius: float, key_energy: float = 1.0) -> None:
    """Key, fill and rim area lights sized to the object, plus a dim neutral world. Calibrated for an object
    normalised to a bounding sphere of radius 1 (`normalize`); watts scale with radius squared otherwise."""
    scale = radius * radius
    rig = [
        ("key", (-1.6, -2.2, 2.2), 900.0, 1.6),
        ("fill", (2.4, -1.4, 0.6), 260.0, 2.4),
        ("rim", (0.6, 2.6, 1.8), 520.0, 1.2),
    ]
    for name, pos, watts, size in rig:
        data = bpy.data.lights.new(f"forge_{name}", type="AREA")
        data.energy = watts * key_energy * scale
        data.size = radius * size
        light = bpy.data.objects.new(f"forge_{name}", data)
        light.location = Vector(pos) * radius
        direction = Vector((0, 0, 0)) - light.location
        light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.collection.objects.link(light)
    world = bpy.context.scene.world or bpy.data.worlds.new("forge_world")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.16, 0.16, 0.17, 1.0)
        bg.inputs["Strength"].default_value = 0.6


def contact_sheet(paths: list[Path], out: Path) -> None:
    """Tile same-size RGBA PNGs left to right into one PNG using Blender's own image API."""
    import numpy as np

    tiles = []
    for p in paths:
        img = bpy.data.images.load(str(p))
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        tiles.append(px.reshape(h, w, 4))
        bpy.data.images.remove(img)
    sheet = np.concatenate(tiles, axis=1)
    h, w = sheet.shape[:2]
    out_img = bpy.data.images.new("forge_contact", width=w, height=h, alpha=True)
    out_img.pixels.foreach_set(sheet.ravel())
    out_img.filepath_raw = str(out)
    out_img.file_format = "PNG"
    out_img.save()
    bpy.data.images.remove(out_img)


def write_report(path: Path, report: dict) -> None:
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"blender-forge: report {path}")
