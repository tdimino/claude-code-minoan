"""Render a transparent turntable (RGBA PNG frames) and a 4-view contact sheet of a GLB, glTF, OBJ, PLY or STL.

    blender -b --factory-startup --python turntable.py -- --glb obj.glb --out DIR [options]

--material auto   use the baked maps (normal-ao.webp, groove.webp) when they sit beside the GLB, else the GLB's own
                  material. "baked" requires them, "gltf" ignores them.
--frames 0        renders only the contact sheet (a quick look before a full turn).

Writes DIR/frame_0001.png …, DIR/contact.png (0°, 90°, 180°, 270°) and DIR/report.json. Frames already in DIR
from an earlier run are deleted first, so an encode never picks up stale ones.
"""

import argparse
import math
import sys
import time
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forge_common as fc  # noqa: E402

GLOW_COLOR = (0.807, 0.776, 0.723)  # #e8e4dc in linear: a warm white for lit strokes


def baked_material(obj: bpy.types.Object, normal_ao: Path, groove: Path, glow: float, ao_mix: float) -> None:
    """Rebuild a baked look (a bake folder: GLB + normal-ao.webp + groove.webp) as a Principled BSDF.

    normal-ao.webp holds an object-space normal in RGB (glTF frame, encoded n * 0.5 + 0.5) and occlusion in alpha.
    glTF is Y-up and the importer turns it Z-up, so a glTF normal (x, y, z) is (x, -z, y) in Blender object space.
    groove.webp marks where a stroke may glow; it drives emission.
    """
    old = obj.active_material
    albedo_img = None
    if old and old.node_tree:
        for node in old.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                albedo_img = node.image
                break
    if albedo_img is None:
        fc.fail("the GLB has no embedded albedo texture")

    mat = bpy.data.materials.new("forge_baked")
    if mat.node_tree is None:  # Blender < 5 needs this; 5.x materials always have nodes
        mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.78
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = obj.data.uv_layers[0].name

    def tex(image: bpy.types.Image, non_color: bool) -> bpy.types.Node:
        node = nodes.new("ShaderNodeTexImage")
        node.image = image
        node.interpolation = "Linear"
        if non_color:
            image.colorspace_settings.name = "Non-Color"
        links.new(uv.outputs["UV"], node.inputs["Vector"])
        return node

    albedo = tex(albedo_img, non_color=False)
    nao_img = bpy.data.images.load(str(normal_ao))
    nao_img.alpha_mode = "CHANNEL_PACKED"  # the alpha is data (occlusion), not coverage
    nao = tex(nao_img, non_color=True)

    # Base colour = albedo darkened by the baked occlusion (the cut floors).
    ao_mul = nodes.new("ShaderNodeMix")
    ao_mul.data_type = "RGBA"
    ao_mul.blend_type = "MULTIPLY"
    ao_mul.inputs["Factor"].default_value = ao_mix
    links.new(albedo.outputs["Color"], ao_mul.inputs["A"])
    links.new(nao.outputs["Alpha"], ao_mul.inputs["B"])
    links.new(ao_mul.outputs["Result"], bsdf.inputs["Base Color"])

    # Normal: decode, swap glTF axes to Blender's, object → world.
    decode = nodes.new("ShaderNodeVectorMath")
    decode.operation = "MULTIPLY_ADD"
    decode.inputs[1].default_value = (2.0, 2.0, 2.0)
    decode.inputs[2].default_value = (-1.0, -1.0, -1.0)
    links.new(nao.outputs["Color"], decode.inputs[0])
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(decode.outputs["Vector"], sep.inputs["Vector"])
    neg_z = nodes.new("ShaderNodeMath")
    neg_z.operation = "MULTIPLY"
    neg_z.inputs[1].default_value = -1.0
    links.new(sep.outputs["Z"], neg_z.inputs[0])
    comb = nodes.new("ShaderNodeCombineXYZ")
    links.new(sep.outputs["X"], comb.inputs["X"])
    links.new(neg_z.outputs["Value"], comb.inputs["Y"])
    links.new(sep.outputs["Y"], comb.inputs["Z"])
    to_world = nodes.new("ShaderNodeVectorTransform")
    to_world.vector_type = "NORMAL"
    to_world.convert_from = "OBJECT"
    to_world.convert_to = "WORLD"
    links.new(comb.outputs["Vector"], to_world.inputs["Vector"])
    norm = nodes.new("ShaderNodeVectorMath")
    norm.operation = "NORMALIZE"
    links.new(to_world.outputs["Vector"], norm.inputs[0])
    links.new(norm.outputs["Vector"], bsdf.inputs["Normal"])

    # Stroke glow.
    if glow > 0 and groove.is_file():
        gimg = bpy.data.images.load(str(groove))
        gtex = tex(gimg, non_color=True)
        bsdf.inputs["Emission Color"].default_value = (*GLOW_COLOR, 1.0)
        strength = nodes.new("ShaderNodeMath")
        strength.operation = "MULTIPLY"
        strength.inputs[1].default_value = glow
        links.new(gtex.outputs["Color"], strength.inputs[0])
        links.new(strength.outputs["Value"], bsdf.inputs["Emission Strength"])

    obj.data.materials.clear()
    obj.data.materials.append(mat)


def main() -> None:
    p = argparse.ArgumentParser(prog="turntable.py")
    p.add_argument("--glb", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--material", choices=["auto", "baked", "gltf"], default="auto")
    p.add_argument("--frames", type=int, default=360, help="frames per full turn; 0 = contact sheet only")
    p.add_argument("--size", type=int, default=1080, help="square frame size in px")
    p.add_argument("--contact-size", type=int, default=512)
    p.add_argument("--engine", choices=["cycles", "eevee"], default="cycles")
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--elevation", type=float, default=18.0, help="camera elevation, degrees")
    p.add_argument("--tilt", type=float, default=0.0, help="tip the object toward the camera, degrees")
    p.add_argument("--start", type=float, default=0.0, help="starting turn, degrees")
    p.add_argument("--glow", type=float, default=0.0, help="stroke glow strength (baked material), e.g. 2")
    p.add_argument("--ao", type=float, default=0.85, help="how strongly the baked occlusion darkens the albedo")
    p.add_argument("--light", type=float, default=0.4, help="multiplier on the light rig")
    p.add_argument("--view", default="AgX", help="view transform: AgX, Standard, Filmic …")
    p.add_argument("--opaque", action="store_true", help="render the world background instead of alpha")
    a = fc.parse_args(p)

    t0 = time.time()
    a.out.mkdir(parents=True, exist_ok=True)
    for old in a.out.glob("frame_[0-9][0-9][0-9][0-9].png"):  # frames from an earlier, longer run
        old.unlink()
    fc.clear_scene()
    obj = fc.import_model(a.glb)
    units = fc.normalize(obj)

    normal_ao = a.glb.parent / "normal-ao.webp"
    groove = a.glb.parent / "groove.webp"
    use_baked = a.material == "baked" or (a.material == "auto" and normal_ao.is_file())
    if use_baked:
        if not normal_ao.is_file():
            fc.fail(f"--material baked needs {normal_ao}")
        baked_material(obj, normal_ao, groove, a.glow, a.ao)
    if not obj.data.polygons[0].use_smooth:
        obj.data.shade_smooth()  # baked GLBs carry no normals; the importer would make them flat

    # A pivot empty carries the turn, so tilt and turn compose cleanly.
    pivot = bpy.data.objects.new("forge_pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    obj.parent = pivot
    obj.rotation_euler.x = math.radians(-a.tilt)

    engine = fc.setup_render(a.engine, a.samples, a.size, not a.opaque, a.view)
    cam = fc.frame_camera(pivot.children[0], a.elevation)
    lo, hi = fc.world_bounds(obj)
    fc.light_rig((hi - lo).length / 2, a.light)
    scene = bpy.context.scene

    def render_at(deg: float, path: Path) -> None:
        pivot.rotation_euler.z = math.radians(a.start + deg)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)

    # Contact sheet first: a cheap look before a full turn.
    scene.render.resolution_x = scene.render.resolution_y = a.contact_size
    views = []
    for deg in (0, 90, 180, 270):
        path = a.out / f"contact_{deg:03d}.png"
        render_at(deg, path)
        views.append(path)
    fc.contact_sheet(views, a.out / "contact.png")
    for v in views:
        v.unlink()
    t_contact = time.time() - t0

    scene.render.resolution_x = scene.render.resolution_y = a.size
    for i in range(a.frames):
        render_at(360.0 * i / a.frames, a.out / f"frame_{i + 1:04d}.png")

    report = {
        "glb": str(a.glb),
        "material": "baked" if use_baked else "gltf",
        "engine": engine,
        "frames": a.frames,
        "size": a.size,
        "camera": {"lens_mm": cam.data.lens, "elevation_deg": a.elevation},
        "mesh": fc.mesh_report(obj),
        "normalized": units,
        "seconds": {"contact": round(t_contact, 1), "total": round(time.time() - t0, 1)},
        "outputs": {"contact": str(a.out / "contact.png"), "frames": f"{a.out}/frame_%04d.png" if a.frames else None},
    }
    fc.write_report(a.out / "report.json", report)


fc.run(main)
