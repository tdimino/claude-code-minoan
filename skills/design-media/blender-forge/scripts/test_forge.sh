#!/usr/bin/env bash
# Edge-case and happy-path tests for blender-forge. Needs blender (>= 5.1), ffmpeg, ffprobe, python3.
#   bash test_forge.sh            # all tests (under a minute once Cycles kernels are cached)
#   SCRIPTS=/path/to/mutant bash test_forge.sh   # run against another copy of the scripts
#   BAKE_DIR=…/public/baked/<id> bash test_forge.sh   # also test the baked-material path
# Exit 0 when every test passes, 1 otherwise. Fixtures live in a temp dir that is removed afterwards.
set -u
SCRIPTS="${SCRIPTS:-$(cd "$(dirname "$0")" && pwd)}"
T="$(mktemp -d "${TMPDIR:-/tmp}/forge-test.XXXXXX")"
trap 'rm -rf "$T"' EXIT
B=(blender -b --factory-startup --python-exit-code 1 --python)
PASS=0; FAIL=0; SKIP=0
REGISTRY="$HOME/.claude/skills/linear-a-decipherment/data/sign-registry.json"
BAKE_DIR="${BAKE_DIR:-}"  # a bake folder <id>/ holding <id>.glb, normal-ao.webp, groove.webp (optional)

ok()   { PASS=$((PASS + 1)); printf '  PASS  %s\n' "$1"; }
bad()  { FAIL=$((FAIL + 1)); printf '  FAIL  %s\n' "$1"; [ -n "${2:-}" ] && printf '        %s\n' "$2"; }
skip() { SKIP=$((SKIP + 1)); printf '  SKIP  %s\n' "$1"; }
# if_ran NAME : true when the last run exited 0, else record NAME as failed
if_ran() { if [ "$RC" -eq 0 ]; then return 0; fi; bad "$1" "exit $RC: $(grep -m1 error "$T/$1.log" 2>/dev/null)"; return 1; }

# run NAME SCRIPT ARGS… : run a Blender script, keep its exit code in $RC and its output in $T/NAME.log
run() { local name=$1 script=$2; shift 2; "${B[@]}" "$SCRIPTS/$script" -- "$@" >"$T/$name.log" 2>&1; RC=$?; }
# expect_fail NAME MESSAGE SCRIPT ARGS… : the script must exit 1 and print MESSAGE
expect_fail() {
  local name=$1 msg=$2 script=$3; shift 3
  run "$name" "$script" "$@"
  if [ "$RC" -eq 1 ] && grep -q -- "$msg" "$T/$name.log"; then ok "$name"; else bad "$name" "exit $RC; wanted '$msg'"; fi
}
# jq-like check on a report: check NAME FILE PYTHON-EXPR (r is the report)
check() {
  local name=$1 file=$2 expr=$3
  if [ ! -f "$file" ]; then bad "$name" "no report $file"; return; fi
  if python3 -c "import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if ($expr) else 1)" "$file"; then ok "$name"
  else bad "$name" "$(python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['mesh'] if 'mesh' in json.load(open(sys.argv[1])) else '')[:300])" "$file" 2>/dev/null)"; fi
}
solid='r["mesh"]["non_manifold_edges"] == 0 and r["mesh"]["boundary_edges"] == 0 and r["mesh"]["loose_parts"] == 1'

echo "vessel"
if [ -f "$REGISTRY" ]; then
  run v_signs make_vessel.py --out "$T/cup.glb" --preset cup --signs "JA-SA-SA-RA-ME 12"
  if_ran v_signs && check v_signs_solid "$T/cup.json" "$solid and r['boolean_solver'] and r['inscription']['glyphs'] == '𐘱𐘞𐘞𐘴𐘋'"
  expect_fail v_unknown_sign "not in the sign registry" make_vessel.py --out "$T/x.glb" --signs "JA-QQQ"
  expect_fail v_band_too_long "circumference" make_vessel.py --out "$T/x.glb" --preset ladle --sign-height 12 \
    --signs "JA-SA-SA-RA-ME JA-SA-SA-RA-ME JA-SA-SA-RA-ME JA-SA-SA-RA-ME JA-SA-SA-RA-ME JA-SA-SA-RA-ME"
  run v_bulge make_vessel.py --out "$T/jar.glb" --preset jar --band-z 45 --signs "KU-RO 65"
  if_ran v_bulge && check v_bulge_solid "$T/jar.json" "$solid"
else
  skip "vessel sign tests (no sign registry at $REGISTRY)"
fi
run v_plain make_vessel.py --out "$T/plain.glb" --preset libation-table
if_ran v_plain && check v_plain_solid "$T/plain.json" "$solid and r['boolean_solver'] is None"
expect_fail v_profile_falls "rise strictly" make_vessel.py --out "$T/x.glb" --profile "30,0;35,20;34,10"
expect_fail v_wall_too_thick "not thinner" make_vessel.py --out "$T/x.glb" --profile "3,0;20,30" --wall 4
expect_fail v_depth_through_wall "cut through" make_vessel.py --out "$T/x.glb" --wall 2 --depth 2 --text "AB" \
  --font /System/Library/Fonts/Supplemental/Arial.ttf
expect_fail v_band_off_vessel "does not fit" make_vessel.py --out "$T/x.glb" --band-z 2 --text "AB" \
  --font /System/Library/Fonts/Supplemental/Arial.ttf
expect_fail v_bad_profile "bad --profile" make_vessel.py --out "$T/x.glb" --profile "30;40"

echo "tablet"
if [ -f "$REGISTRY" ]; then
  run t_full make_tablet.py --out "$T/tab.glb" --line "KU-RO 65" --line "PA-I-TO 1234" --line "A-DU 7" \
    --back-line "JA-SA-SA-RA-ME" --rules
  if_ran t_full && check t_full_solid "$T/tab.json" "$solid and len(r['lines']['face']) == 3 and len(r['lines']['back']) == 1"
  expect_fail t_line_too_wide "fit" make_tablet.py --out "$T/x.glb" --width 30 --line "JA-SA-SA-RA-ME JA-SA-SA-RA-ME"
  expect_fail t_too_many_lines "fit inside the margins" make_tablet.py --out "$T/x.glb" --height 30 \
    --line "KU" --line "KU" --line "KU" --line "KU"
  expect_fail t_number_range "numbers must be" make_tablet.py --out "$T/x.glb" --line "KU-RO 100000"
fi
expect_fail t_bevel "bevel" make_tablet.py --out "$T/x.glb" --thickness 10 --bevel 6

echo "turntable"
run r_contact turntable.py --glb "$T/plain.glb" --out "$T/plain-look" --frames 0 --contact-size 96
if [ "$RC" -eq 0 ] && python3 - "$T/plain-look/contact.png" <<'EOF'
import struct, sys
data = open(sys.argv[1], "rb").read(32)
w, h, depth, ctype = struct.unpack(">IIBB", data[16:26])
sys.exit(0 if (w, h, ctype) == (384, 96, 6) else 1)  # 4 views side by side, RGBA
EOF
then ok r_contact_png; else bad r_contact_png "exit $RC or wrong contact.png size/alpha"; fi
check r_report "$T/plain-look/report.json" "r['material'] == 'gltf' and r['frames'] == 0"
cat >"$T/two.py" <<'EOF'
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); bpy.ops.mesh.primitive_uv_sphere_add(location=(4, 0, 0))
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB")
EOF
"${B[@]}" "$T/two.py" -- "$T/two.glb" >/dev/null 2>&1
run r_multi turntable.py --glb "$T/two.glb" --out "$T/two-look" --frames 0 --contact-size 64
if_ran r_multi && check r_multi_joined "$T/two-look/report.json" "r['mesh']['loose_parts'] == 2"
run r_frames turntable.py --glb "$T/plain.glb" --out "$T/turn" --frames 4 --size 96 --contact-size 32 --samples 4
if [ "$RC" -eq 0 ] && [ "$(ls "$T/turn" | grep -c '^frame_')" -eq 4 ]; then ok r_frames; else bad r_frames "exit $RC"; fi
if [ -n "$BAKE_DIR" ] && [ -f "$BAKE_DIR/$(basename "$BAKE_DIR").glb" ]; then
  run r_baked turntable.py --glb "$BAKE_DIR/$(basename "$BAKE_DIR").glb" --out "$T/baked" --frames 0 --contact-size 64
  if_ran r_baked && check r_baked_material "$T/baked/report.json" "r['material'] == 'baked' and $solid"
else
  skip "r_baked (set BAKE_DIR to a real bake folder; a synthetic bake is tested below)"
fi
expect_fail r_missing "no such file" turntable.py --glb "$T/nope.glb" --out "$T/x"
expect_fail r_format "unsupported format" turntable.py --glb "$T/two.py" --out "$T/x"

echo "encode"
E="$SCRIPTS/encode_turntable.py"
python3 "$E" "$T" >/dev/null 2>&1; [ $? -eq 2 ] && ok e_no_frames || bad e_no_frames
python3 "$E" "$T/turn" --over "$T/none.mp4" >/dev/null 2>&1; [ $? -eq 2 ] && ok e_no_take || bad e_no_take
python3 "$E" "$T/turn" --height 3 >/dev/null 2>&1; [ $? -eq 2 ] && ok e_height || bad e_height
ffmpeg -v error -f lavfi -i testsrc2=s=320x240:d=1 -f lavfi -i sine=d=1 -c:v libx264 -c:a aac -shortest \
  "$T/take.mp4" </dev/null
if python3 "$E" "$T/turn" --over "$T/take.mp4" >"$T/encode.log" 2>&1; then
  alpha=$(ffprobe -v error -show_entries stream_tags=alpha_mode -of csv=p=0 "$T/turn/turntable.webm")
  [ "$alpha" = "1" ] && ok e_webm_alpha || bad e_webm_alpha "alpha_mode=$alpha"
  streams=$(ffprobe -v error -show_entries stream=codec_name,profile -of csv=p=0 "$T/take.turntable.mp4" | tr '\n' ' ')
  case "$streams" in *"h264,High"*"aac"*) ok e_overlay_streams ;; *) bad e_overlay_streams "$streams" ;; esac
else
  bad e_encode "$(tail -3 "$T/encode.log")"
fi

echo "clean_scan"
cat >"$T/damaged.py" <<'EOF'
import bpy, bmesh, sys
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=50)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > 48], context="FACES")
frag = bmesh.ops.create_cube(bm, size=2)
bmesh.ops.translate(bm, verts=frag["verts"], vec=(80, 0, 0))
me = bpy.data.meshes.new("d"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("d", me); bpy.context.scene.collection.objects.link(ob)
bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True)
bpy.ops.wm.ply_export(filepath=out, export_selected_objects=True)
EOF
"${B[@]}" "$T/damaged.py" -- "$T/damaged.ply" >/dev/null 2>&1
run c_clean clean_scan.py --in "$T/damaged.ply" --out "$T/clean.glb" --triangles 1500
if_ran c_clean && check c_clean_result "$T/clean.json" \
  "r['dropped_parts'] == 1 and r['steps']['input']['boundary_edges'] > 0 and r['steps']['decimated']['boundary_edges'] == 0 and r['steps']['decimated']['loose_parts'] == 1 and r['steps']['decimated']['triangles'] <= 1500" \
 
expect_fail c_same_path "never overwritten" clean_scan.py --in "$T/clean.glb" --out "$T/clean.glb"

echo "error handling"
cat >"$T/raise.py" <<EOF
import sys; sys.path.insert(0, "$SCRIPTS"); import forge_common as fc
def main(): raise RuntimeError("boom")
fc.run(main)
EOF
blender -b --factory-startup --python "$T/raise.py" >"$T/raise.log" 2>&1  # note: no --python-exit-code
[ $? -eq 1 ] && grep -q "RuntimeError: boom" "$T/raise.log" && ok x_exception_exits_1 || bad x_exception_exits_1

echo "registry-free text, numerals and geometry"
ARIAL=/System/Library/Fonts/Supplemental/Arial.ttf
NOREG="$T/no-registry.json"
run v_text_boolean make_vessel.py --out "$T/arial.glb" --text "AB" --font "$ARIAL"
if_ran v_text_boolean && check v_text_boolean_solid "$T/arial.json" "$solid and r['boolean_solver']"
run t_numerals_no_registry make_tablet.py --out "$T/num.glb" --registry "$NOREG" --line "65" --line "1234"
if_ran t_numerals_no_registry && check t_numerals_solid "$T/num.json" "$solid"
run t_raw_text make_tablet.py --out "$T/raw.glb" --raw --font "$ARIAL" --line "ABC" --back-line "XYZ"
if_ran t_raw_text && check t_raw_text_solid "$T/raw.json" "$solid and r['lines']['back'][0]['line'] == 'XYZ'"
expect_fail n_ten_thousand "1–9999" make_tablet.py --out "$T/x.glb" --registry "$NOREG" --line "10000"
expect_fail n_zero "1–9999" make_tablet.py --out "$T/x.glb" --registry "$NOREG" --line "0"
expect_fail t_margin_under_bevel "margin" make_tablet.py --out "$T/x.glb" --thickness 20 --registry "$NOREG" --line "5"
expect_fail t_depth_through "cut through" make_tablet.py --out "$T/x.glb" --thickness 4 --bevel 1 --depth 2
expect_fail v_flat_ledge "too flat" make_vessel.py --out "$T/x.glb" --profile "20,0;20,10;60,10.5;60,50"
expect_fail v_too_short "too short" make_vessel.py --out "$T/x.glb" --profile "30,0;32,6"
expect_fail v_one_point "two" make_vessel.py --out "$T/x.glb" --profile "30,0"
run v_band_from_foot make_vessel.py --out "$T/raised.glb" --profile "30,10;34,40;38,70" --band-z 0.5 --text "AB" --font "$ARIAL"
if_ran v_band_from_foot && check v_band_from_foot_z "$T/raised.json" "abs(r['inscription']['band_z_mm'] - 40) < 0.01"
# The cavity floor must be flat at foot + wall: cast rays straight down inside the cup.
cat >"$T/floor.py" <<'EOF'
import bpy, sys
from mathutils import Vector
glb = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=glb)
ob = next(o for o in bpy.context.scene.objects if o.type == "MESH")
dg = bpy.context.evaluated_depsgraph_get()
hits = []
for r in (0.5, 10.0, 18.0):  # mm read as m; the cup's inner wall at the floor is ~20 mm from the axis
    ok, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((r, 0.0, 59.0)), Vector((0, 0, -1)))
    hits.append(round(loc.z, 2) if ok else None)
print("FLOOR", hits)
sys.exit(0 if all(h is not None and abs(h - 4.0) < 0.3 for h in hits) else 1)
EOF
"${B[@]}" "$SCRIPTS/make_vessel.py" -- --out "$T/plain-cup.glb" --preset cup >/dev/null 2>&1
if "${B[@]}" "$T/floor.py" -- "$T/plain-cup.glb" >"$T/floor.log" 2>&1; then ok v_floor_flat
else bad v_floor_flat "$(grep FLOOR "$T/floor.log")"; fi

echo "frames, framing and alpha"
# alpha_check PNG TILES : every tile has some opaque pixels and a fully transparent 1-px border
alpha_check() {
  ffmpeg -v error -i "$1" -f rawvideo -pix_fmt rgba - 2>/dev/null | python3 -c '
import sys
data = sys.stdin.buffer.read(); tiles = int(sys.argv[1]); w, h = map(int, sys.argv[2].split("x"))
a = lambda x, y: data[(y * w + x) * 4 + 3]
tw = w // tiles
for t in range(tiles):
    xs = range(t * tw, (t + 1) * tw)
    border = [a(x, 0) for x in xs] + [a(x, h - 1) for x in xs] + [a(t * tw, y) for y in range(h)] + [a((t + 1) * tw - 1, y) for y in range(h)]
    if max(border) > 0 or max(a(x, y) for x in xs for y in range(h)) == 0:
        sys.exit(1)
' "$2" "$(ffprobe -v error -show_entries stream=width,height -of csv=s=x:p=0 "$1")"
}
alpha_check "$T/plain-look/contact.png" 4 && ok r_contact_alpha || bad r_contact_alpha "an empty tile, or the object touches the frame"
# frame_camera must keep EVERY vertex in frame through the turn: an uncentred grid with one far spike on an odd
# index (a sampler that skips vertices misses it), checked with Blender's own projection at every 10°.
cat >"$T/spike.py" <<EOF
import bpy, bmesh, math, sys
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, "$SCRIPTS"); import forge_common as fc
fc.clear_scene()
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=100, y_segments=100, size=1.0)   # 10,201 vertices around the origin
bm.verts.ensure_lookup_table()
bm.verts[len(bm.verts) - 2].co.x = 6.0                                # one far spike, odd index
me = bpy.data.meshes.new("spike"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("spike", me); bpy.context.scene.collection.objects.link(ob)
scene = bpy.context.scene
scene.render.resolution_x = scene.render.resolution_y = 100
cam = fc.frame_camera(ob, 18.0)
worst = 0.0
for deg in range(0, 360, 10):
    ob.rotation_euler.z = math.radians(deg)
    bpy.context.view_layer.update()
    for v in ob.data.vertices:
        p = world_to_camera_view(scene, cam, ob.matrix_world @ v.co)
        worst = max(worst, abs(p.x - 0.5), abs(p.y - 0.5))
print("WORST", round(worst, 3))
sys.exit(0 if worst <= 0.5 else 1)
EOF
if "${B[@]}" "$T/spike.py" >"$T/spike.log" 2>&1; then ok r_spike_in_frame; else bad r_spike_in_frame "$(grep WORST "$T/spike.log")"; fi
run r_stale_a turntable.py --glb "$T/plain.glb" --out "$T/stale" --frames 4 --size 64 --contact-size 32 --samples 2
run r_stale_b turntable.py --glb "$T/plain.glb" --out "$T/stale" --frames 2 --size 64 --contact-size 32 --samples 2
n=$(ls "$T/stale" | grep -c '^frame_'); [ "$n" -eq 2 ] && ok r_no_stale_frames || bad r_no_stale_frames "$n frames left"
# The overlay keeps the take visible where the turntable is transparent (alpha survived the decode).
ffmpeg -v error -y -i "$T/take.mp4" -frames:v 1 -f rawvideo -pix_fmt rgb24 "$T/take.rgb" 2>/dev/null
ffmpeg -v error -y -i "$T/take.turntable.mp4" -frames:v 1 -f rawvideo -pix_fmt rgb24 "$T/over.rgb" 2>/dev/null
if python3 - "$T/take.rgb" "$T/over.rgb" <<'EOF'
import sys
take, over = open(sys.argv[1], "rb").read(), open(sys.argv[2], "rb").read()
w = 320  # the 320x240 take; the 144-px turntable box starts at x≈163, y=48, and its corner is transparent
for x, y in ((167, 52), (170, 55), (305, 52)):
    i = (y * w + x) * 3
    if max(abs(take[i + c] - over[i + c]) for c in range(3)) > 40:
        sys.exit(1)
EOF
then ok e_overlay_alpha; else bad e_overlay_alpha "the turntable box hides the take"; fi
ffmpeg -v error -y -f lavfi -i sine=d=1 -c:a aac "$T/audio.m4a" </dev/null
python3 "$E" "$T/turn" --over "$T/audio.m4a" >/dev/null 2>&1; [ $? -eq 2 ] && ok e_take_without_video || bad e_take_without_video

echo "baked material (synthetic bake)"
cat >"$T/bake.py" <<'EOF'
import bpy, sys
from pathlib import Path
d = Path(sys.argv[sys.argv.index("--") + 1]); d.mkdir(parents=True, exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.object
def img(name, rgba, alpha):
    im = bpy.data.images.new(name, 16, 16, alpha=alpha)
    im.pixels = list(rgba) * 256
    return im
albedo = img("albedo", (0.5, 0.45, 0.4, 1.0), False)
albedo.pack()
mat = bpy.data.materials.new("m")
tex = mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = albedo
bsdf = mat.node_tree.nodes["Principled BSDF"]
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
ob.data.materials.append(mat)
bpy.ops.export_scene.gltf(filepath=str(d / f"{d.name}.glb"), export_format="GLB")
for name, rgba in (("normal-ao", (0.5, 1.0, 0.5, 1.0)), ("groove", (0.0, 0.0, 0.0, 1.0))):
    im = img(name, rgba, True)
    im.filepath_raw = str(d / f"{name}.webp"); im.file_format = "WEBP"; im.save()
EOF
"${B[@]}" "$T/bake.py" -- "$T/bake-fix" >"$T/bake-fix.log" 2>&1
run r_baked_synthetic turntable.py --glb "$T/bake-fix/bake-fix.glb" --out "$T/bake-look" --frames 0 --contact-size 48 --glow 2
if_ran r_baked_synthetic && check r_baked_synthetic_material "$T/bake-look/report.json" "r['material'] == 'baked'"
expect_fail r_baked_needs_maps "needs" turntable.py --glb "$T/plain.glb" --out "$T/x" --material baked
mkdir -p "$T/noalb" && cp "$T/plain.glb" "$T/noalb/" && cp "$T/bake-fix/normal-ao.webp" "$T/noalb/"
expect_fail r_no_albedo "no embedded albedo" turntable.py --glb "$T/noalb/plain.glb" --out "$T/x"
expect_fail c_bad_ranges "must be" clean_scan.py --in "$T/damaged.ply" --out "$T/x.glb" --triangles -1

cat >"$T/far.py" <<'EOF'
import bpy, bmesh, sys
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.1)
bmesh.ops.translate(bm, verts=bm.verts, vec=(1000.0, 0.0, 0.0))     # a small object far from the origin
me = bpy.data.meshes.new("far"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("far", me); bpy.context.scene.collection.objects.link(ob)
bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True)
bpy.ops.wm.ply_export(filepath=out, export_selected_objects=True)
EOF
"${B[@]}" "$T/far.py" -- "$T/far.ply" >/dev/null 2>&1
run c_far clean_scan.py --in "$T/far.ply" --out "$T/far.glb"
if_ran c_far && check c_far_intact "$T/far.json" \
  "r['welded_vertices'] == 0 and r['steps']['cleaned']['vertices'] == r['steps']['input']['vertices'] and r['steps']['cleaned']['non_manifold_edges'] == 0"

echo
echo "$PASS passed, $FAIL failed, $SKIP skipped"
[ "$FAIL" -eq 0 ]
