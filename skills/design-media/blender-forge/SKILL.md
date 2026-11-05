---
name: blender-forge
description: "Generates and manipulates 3D objects by driving Blender headless (blender -b --python) with versioned bpy scripts: turned vessels and clay tablets with Linear A signs and numerals cut in (sign registry → Noto Sans Linear A → Boolean), scan and mesh cleanup (weld, fragments, holes, decimation), transparent turntable renders of any GLB/OBJ/PLY/STL (including site bakes with object-space normal + AO and groove-glow maps), 4-view contact sheets and mesh health reports for visual self-checking, and VP9-alpha / ProRes 4444 encoding with an overlay onto a recorded take. This skill should be used when making or editing a 3D object, carving or inscribing signs on a mesh, cleaning or decimating a scan, rendering a turntable or product shot, putting a turning 3D object into a video, checking a mesh (holes, loose parts, size), or choosing between Blender MCP servers. Triggers on Blender, bpy, 3D model, GLB, glTF, turntable, lathe, vessel, tablet, inscribe, carve signs, clean scan, decimate, 3D object beside my face, Blender MCP."
argument-hint: "[vessel | tablet | clean <mesh> | turntable <glb> | encode <frames-dir> | test | mcp]"
---

# Blender Forge

Headless Blender, driven by scripts that each write a result, a JSON report and renders to look at. Run, read
the report and the contact sheet, fix, run again. That loop is what makes agents good at Blender; one-shot code
is not. See `references/blender-mcp-and-research.md`.

**Arguments:**
- `vessel` → Make a vessel; `tablet` → Make a tablet; `clean <mesh>` → Clean a scan.
- `turntable <glb>` → Turntable; `encode <dir>` → Encode and overlay.
- `test` → `bash $S/test_forge.sh`; `mcp` → read `references/blender-mcp-and-research.md`.

## Requirements

- **Platform:** macOS. Linux works with `--font` pointing at a Noto Sans Linear A file; there the GPU backend
  falls back to CUDA, OptiX, HIP or the CPU.
- **Blender ≥ 5.1** (tested 5.2.3 LTS, `brew install --cask blender`; `blender` on PATH).
- **ffmpeg** with `libvpx-vp9` (alpha WebM) and `prores_ks`.
- **Font:** Noto Sans Linear A, which ships with macOS at
  `/System/Library/Fonts/Supplemental/NotoSansLinearA-Regular.ttf` (`--font` to change it).
- **Optional:** a sign registry, the linear-a-decipherment skill's `data/sign-registry.json` (`--registry`), for
  transliterated signs. Without it you can still cut numerals, and literal text with `--text` (vessel) or
  `--raw` (tablet). The `recordly` skill's X check is optional too.

```bash
S=~/.claude/skills/blender-forge/scripts
B="blender -b --factory-startup --python-exit-code 1 --python"
```

`--python-exit-code 1` matters. Without it, Blender exits 0 after an uncaught Python error. The scripts also
convert every exception to exit 1 themselves (`forge_common.run`).

## Text: signs and numerals

`--signs`, `--line` and `--back-line` take transliterations: hyphenated signs, words separated by spaces,
numbers as digits. For example `"KU-RO 65"`, `"JA-SA-SA-RA-ME"` or `"AB120 12"`.
- **Signs** resolve by sound value or AB number through the registry.
- **Numbers** (1–9999) are drawn the way Linear A writes them: units as vertical strokes, tens as horizontal
  strokes, hundreds as circles, thousands as circles with rays.
- **Words** keep a word gap between them.
- **Literal text:** `--text "…"` (vessel) or `--raw` (tablet lines) cuts characters exactly as given, in any
  `--font`, with no numerals.
- **The registry is read only when a line has signs.**

## Make a vessel

```bash
$B $S/make_vessel.py -- --out out/cup.glb --preset cup --signs "JA-SA-SA-RA-ME"
$B $S/make_vessel.py -- --out out/jar.glb --preset jar --band-z 45 --signs "KU-RO 65"
```

- **Presets:** `cup`, `bowl`, `ladle`, `jar`, `libation-table`.
- **Custom profile:** `--profile "r,z;…"` in millimetres, giving the outer wall from foot to rim with heights
  rising. The inner wall is the outer one moved in by `--wall` (4 mm), and the cavity floor is flat at
  foot + wall.
- **Signs:** cut `--depth` (1.2 mm) into the wall at `--band-z` (a fraction of the height above the foot, or mm
  if > 1), with
  `--sign-height` 9 mm and `--start`° (0 = front). They follow bulging and conical walls.
- **Refused with a message:**
  - the band doesn't fit around or up the wall;
  - the wall is thicker than the narrowest radius;
  - a segment above the floor leans more than 60°, where the wall would thin out;
  - the vessel is too short for its floor;
  - the cut would go through the wall;
  - a sign is unknown.

## Make a tablet

```bash
$B $S/make_tablet.py -- --out out/tab.glb --width 60 --height 90 --line "KU-RO 65" --line "PA-I-TO 12" \
  --back-line "JA-SA-SA-RA-ME" --rules
```

- **Shape:** a slab with rounded edges (`--bevel`, default 35% of `--thickness`), standing upright with the face
  toward the camera.
- **Text:** lines run from the top-left. Back lines read correctly when the tablet is turned round. `--rules`
  cuts ruling lines between lines. `--raw` takes literal characters in `--font`.
- **Refused with a message:**
  - a line wider than the space inside `--margin`;
  - more lines than the height holds;
  - a margin inside the rounded edge (`--margin` < `--bevel`);
  - a cut through the tablet.

## Clean a scan

```bash
$B $S/clean_scan.py -- --in scan.ply --out scan-clean.glb --triangles 100000
```

- **Input:** GLB/glTF, OBJ, PLY or STL.
- **Steps:**
  - welds split vertices; UVs are kept, because they live on face corners;
  - drops loose fragments under `--min-part` (1%) of the largest part;
  - fills holes up to `--max-hole` (64) edges;
  - makes normals consistent;
  - decimates toward `--triangles`.
- **Report:** before and after each step.
- **The input is never overwritten.** A cleaned restricted scan is still restricted.

## Turntable

```bash
$B $S/turntable.py -- --glb obj.glb --out out/turn --frames 0     # contact sheet only (seconds)
$B $S/turntable.py -- --glb obj.glb --out out/turn --frames 360 --glow 3
```

- **Input:** any supported mesh format.
- **Output:** RGBA `frame_0001.png …`, `contact.png` (0°/90°/180°/270°) and `report.json`.
- **Output folder:** old frames in it are deleted first, so an encode never mixes runs.
- **What it does:**
  - normalises the object to a unit bounding sphere (the report keeps the original size);
  - fits the camera so every vertex stays in frame through the whole turn;
  - lights it with key, fill and rim lights;
  - renders in Cycles on the GPU (Metal) with a transparent film.
- **Bake folders:** a GLB with an embedded albedo, plus `normal-ao.webp` (object-space normal in the glTF frame
  in RGB, occlusion in alpha) and `groove.webp` (where strokes glow) beside it. `--material auto` rebuilds that
  baked look, and `--glow` lights the carved strokes.
- **Options:** `--elevation` (18°), `--tilt`, `--start`, `--light` (0.4), `--ao`, `--size` (1080),
  `--samples` (48), `--contact-size` (512), `--engine eevee`, `--view Standard|AgX`, `--opaque`.

## Encode, overlay, optimise

```bash
python3 $S/encode_turntable.py out/turn --prores                       # turntable.webm (+ .mov)
python3 $S/encode_turntable.py out/turn --over take.mp4 --height 0.6   # take.turntable.mp4, object on the right
python3 ~/.claude/skills/recordly/scripts/check_x_export.py take.turntable.mp4 --fix
npx @gltf-transform/cli optimize in.glb out.glb --compress meshopt --texture-compress webp   # for the web
```

The overlay loops the turntable for the whole take and copies the take's audio. Exit codes: 0 ok, 1 ffmpeg or
verification failure, 2 usage error.

## The look-check loop (do not skip)

After every script, read the report and **look at `contact.png`** (`turntable.py --frames 0`) before saying the
object is right:
- `non_manifold_edges` and `boundary_edges` should be 0, and `loose_parts` 1, for a solid object;
- `size` should match the intent;
- the signs should read in the right order. When unsure of a glyph, render the string flat with Pillow and
  compare. Shapes are easy to misread.

## Tests

`bash $S/test_forge.sh` runs 52 tests in under a minute once the Cycles kernels are cached:
- the refusal paths listed above, each with its message;
- watertight results for vessels, bulging jars, raised feet and tablets with numerals, rules, a back and literal
  text, including the Boolean without a registry;
- a flat cavity floor, checked with ray casts;
- every vertex in frame through the turn;
- contact-sheet alpha, multi-mesh import, a synthetic bake;
- no stale frames, overlay alpha checked against the take's pixels, takes without video;
- scan cleanup near and far from the origin, and the exception wrapper.

Each fix was proved by a mutant that reverts it and fails its test.

Sign tests skip without the sign registry. `BAKE_DIR=<bake folder>` adds a test on a real bake. `SCRIPTS=<dir>` runs the suite against another copy of the scripts
(mutation checks).

## Gotchas

- **Units:** glTF from three.js projects is often in millimetres, and Blender reads the numbers as metres. Lights
  tuned for one scale look black at the other. `turntable.py` normalises; keep it.
- **Object-space normal maps in the glTF frame:** a glTF normal (x, y, z) is (x, −z, y) in Blender, and the alpha
  is data, so set `alpha_mode = 'CHANNEL_PACKED'`.
- **Exporters split vertices at UV seams.** Weld by position before counting holes or parts.
- **Lathe spin:** an edge lying on the spin axis spins into zero-area faces and a non-manifold pole. Spin an open
  profile whose two ends touch the axis.
- **Font outlines are not closed solids:**
  - the Manifold Boolean solver returns the mesh unchanged, so `boolean_difference` checks the face count and
    falls back to Exact (self-intersection on) on a fresh copy;
  - never run `recalc_face_normals` across font geometry, which flips pieces of it at random (the tablet's back
    failed this way). Recalculate only closed pieces such as the rule boxes.
- **Smooth shading smears cuts** into streaks. Mark edges over `--sharp-angle` (35°) as sharp.
- **Uncaught errors exit 0** unless Blender gets `--python-exit-code`. Always use `fc.run(main)`.
- **First Cycles render on Metal compiles kernels (~90 s).** Later runs take about 3 s per contact sheet.
  Renders that share the GPU slow each other down.
- **Blender 5.x:** `Material.use_nodes` is deprecated (new materials always have nodes), and `Action.fcurves` is
  gone, so turntables set the rotation per frame.
- **Recordly** freezes animated image annotations, so a turning object goes in with the overlay.

## Assets and licences

- **Licence-restricted scans (e.g. INSCRIBE photogrammetry) stay local:** never in a published render, never in an
  MCP session with telemetry, generation or upload tools, and never sent to Meshy, Rodin or Hunyuan.
- **A project with its own bake pipeline:** call that pipeline and never write its outputs by hand. This skill
  only reads its GLBs and maps.
- **Credit every third-party model** in the post or page that shows it.

## References

| File | Contents |
|---|---|
| `references/blender-mcp-and-research.md` | Official vs community Blender MCP, telemetry and safety, scan-cleanup and generation tools, the benchmarks behind the look-check loop |
| `scripts/forge_common.py` | Shared helpers: arguments after `--`, exception guard, scene reset, model import, normalise, mesh report, Boolean with fallback, smooth-by-angle, GLB export, GPU render setup, camera fit, light rig, contact sheet |
| `scripts/signs.py` | Line layout: registry look-up, font glyphs, Linear A numerals |

Licence: MIT, like the repository it ships in. Blender is GPL; the scripts only call it.
