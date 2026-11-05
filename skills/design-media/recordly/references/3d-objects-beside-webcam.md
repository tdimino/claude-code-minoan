# 3D objects beside the webcam

How to put a turning 3D object to the right of the user's face in a clip for X. Researched 2026-11-05 (sources
at the end). The steps marked **verified** were run on this setup. The rest is documented behaviour from the cited
sources and needs a first test before a real take.

## First gate: may this asset be published?

A post on X publishes every frame, including a glimpse in the background. Before recording, settle each asset's
licence and write its credit line into the post text.

**Example asset repository: a Linear A inscription viewer** (Vite + three.js). It holds two model sets with opposite
rules, and the split is typical of cultural-heritage work:

| Set | What it is | In a public clip? |
|---|---|---|
| Template objects | Generated in the browser from code: lathe-swept tables and cups, clay tablets, signs cut from the Noto Sans Linear A font, CC0 photo textures from ambientCG. Opened with `?set=template&open=<id>`. | Yes, once the viewer itself is public. They are what its production build shows. |
| Scanned originals (INSCRIBE, University of Bologna) | Photogrammetry meshes served by the dev server only | **No.** The data licence allows scientific, non-profit use and forbids publishing without INSCRIBE's written permission. Keep them out of every frame. |

The template objects are not files. They exist only as meshes with a custom three.js `ShaderMaterial`, and
`GLTFExporter` does not export custom shader materials, so an exported GLB would lose the carved glow and the
procedural stone. **Film the viewer instead of exporting from it.** If the viewer is unreleased, clear it with its
owner first.

**Other sources:** museum scans on Sketchfab carry a licence per model. The Fitzwilliam Museum's Minoan double axe,
for example, is CC BY 4.0, which means credit "Fitzwilliam Museum, CC BY 4.0" in the post. Read each model's
licence line. Skip NC (non-commercial) and ND (no-derivatives) licences unless the use clearly fits them. Download
glTF/GLB, the format the browser routes below load directly.

## Pick a route by how large the face should be

| Route | Face | Object | Tools | When |
|---|---|---|---|---|
| A. Recordly screen + webcam bubble | Round bubble, left | The recorded browser window, right | Recordly only | Default. The user can turn the object while talking. |
| B. OBS live composite | Full camera frame, or its left half | Browser source composited on the right | OBS Studio | The face should dominate. |
| C. Overlay after recording | As recorded | A transparent turntable laid over the right side | ffmpeg | The object should float over the camera image with no panel. |

All three end the same way: `check_x_export.py clip.mp4 --fix` before posting.

## Route A: Recordly

1. **Serve the object.**
   - Template from the example viewer: run its dev server (`npm run dev`) and open
     `http://localhost:5173/?set=template&open=<template-id>`.
   - A GLB from any source: a page with Google's `<model-viewer>`:

     ```html
     <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.4.0/model-viewer.min.js"></script>
     <style>html,body{margin:0;height:100%;background:#111}
       model-viewer{position:absolute;right:0;top:0;width:50%;height:100%;background-color:transparent}</style>
     <model-viewer src="object.glb" auto-rotate camera-controls disable-zoom interaction-prompt="none"
       camera-orbit="30deg 75deg auto" shadow-intensity="1"></model-viewer>
     ```

     The right half holds the object and the left half stays empty for the bubble. `auto-rotate` turns it,
     `interaction-prompt="none"` hides the hand icon, and `camera-orbit` sets the opening angle. Version 4.4.0 was
     current on npm and served by the CDN on 2026-11-05.
2. **HUD** (agent, through `driving-with-agent-desktop.md`): set the source to that browser window, turn on
   microphone and webcam, and turn on **Hide HUD from recording**. The user records.
3. **Editor:** Webcam tab → position **←** (left middle), raise Webcam Width and Height, set roundness. Frame at
   **16:9**. At 1:1 the bubble and the object compete for the same space.
4. Export and check. **Verified:** Recordly's webcam grid and 16:9/1:1 presets and the export path (pilot,
   2026-11-05).

## Route B: OBS live composite

OBS renders a web page as a **Browser Source** and composites it with alpha: whatever the page leaves transparent
shows the scene beneath. The page must not paint a background.

1. Scene: **Video Capture Device** (the camera) filling the frame, or its left half.
2. **Browser Source** at 1920×1080 on the page from Route A, with `body{background:transparent}` instead of
   `#111`. The `<model-viewer>` canvas is transparent when its `background-color` is. OBS layers the turning object
   over the camera on the right.
3. The example viewer clears its canvas to opaque black (`renderer.setClearColor(0x000000, 1)`) and paints a CSS
   background, so it cannot float over the camera as it stands. Use it as an opaque panel on the right (crop the
   source), or ask its owner for a transparent mode (renderer `alpha: true`, `setClearColor(0x000000, 0)`, no page
   background) behind a URL flag. A chroma or colour key on black would also eat the dark stone, so don't use one.
4. Record to MP4 with H.264 and AAC, then run the check.

## Route C: transparent turntable over the recording

Browsers cannot record alpha directly. Chrome's `MediaRecorder` has no transparency option, and its WebCodecs
`VideoEncoder` rejects `alpha: 'keep'` for every codec. Capture PNG frames and let ffmpeg encode them.

1. **Frames.** Render with a transparent clear (`alpha: true`, `setClearColor(0x000000, 0)`,
   `preserveDrawingBuffer: true`). Step the rotation by a fixed angle per frame rather than by time, so every frame is
   captured. Save `canvas.toDataURL('image/png')` per frame (agent-browser `eval`, or Playwright). For
   `<model-viewer>`, set `camera-orbit` per frame and save `modelViewer.toBlob()`. A 12-second loop at 30 fps is
   360 frames, at 30° a second.
2. **Encode with alpha.** This ffmpeg build has `libvpx-vp9` and `prores_ks`:

   ```bash
   ffmpeg -framerate 30 -i frame_%04d.png -c:v libvpx-vp9 -pix_fmt yuva420p -crf 30 -b:v 0 turntable.webm
   # or, for editors: -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le turntable.mov
   ```

3. **Overlay.** ffmpeg's built-in VP9 decoder ignores WebM alpha (ffmpeg ticket #8344), so name the `libvpx-vp9`
   decoder **before** the WebM input:

   ```bash
   ffmpeg -i take.mp4 -stream_loop -1 -c:v libvpx-vp9 -i turntable.webm \
     -filter_complex "[1:v]scale=-2:640[obj];[0:v][obj]overlay=W-w-60:(H-h)/2:shortest=1" \
     -c:v libx264 -profile:v high -pix_fmt yuv420p -c:a copy composite.mp4
   python3 ~/.claude/skills/recordly/scripts/check_x_export.py composite.mp4 --fix
   ```

   `-stream_loop -1` repeats the turntable for the whole take, and `shortest=1` ends with the take.

**Inside Recordly instead (untested):** image annotations accept JPG, PNG, GIF and WebP. An animated WebP keeps full
alpha, but this ffmpeg build has no WebP encoder (use `img2webp` from Google's `webp` tools). GIF alpha is one bit
with 256 colours, which bands on stone. Whether Recordly's export plays animated annotations has not been checked.

## Composition for X

- Free accounts play back at 720p, so give the object at least a third of the frame height, or the signs blur. In
  the example viewer, the glow on carved strokes helps them read.
- Rotate slowly. A full turn in 12 seconds or more lets a viewer read a face of the object before it turns away.
- Face left and object right reads naturally. Keep the object's best face toward the camera while speaking about it.
- Credit every licensed asset in the post text.

## Sources (read 2026-11-05)

- OBS browser sources and transparency: reactorstudio.ch/guides/obs-browser-source-effects (Firecrawl).
- ffmpeg drops VP9 alpha with its native decoder, so force `libvpx`: Blender PR #132795, which cites
  trac.ffmpeg.org/ticket/8344 (Firecrawl).
- Chrome cannot encode alpha (MediaRecorder, WebCodecs `alpha: 'keep'` rejected): 9io.ai/blog/transparent-webm-webcodecs-vp9-alpha
  (2026-09-25, Firecrawl), and stackoverflow.com/questions/42146396 (Exa).
- `<model-viewer>` transparent background since v0.9.0 (PR #975): github.com/google/model-viewer/issues/874; camera
  and `auto-rotate` attributes: modelviewer.dev/examples/staging-and-camera-control.html (Firecrawl).
- `GLTFExporter` does not export `ShaderMaterial`: discourse.threejs.org/t/why-doesnt-gltfexporter-support-shadermaterials/21382
  and three.js issue #22163 (Exa).
- Licence example: sketchfab.com/3d-models/minoan-double-axe-420f3f0eb81a4510a9ee16916c9e8ed7, CC BY 4.0 (Firecrawl).
- Recordly image annotation formats: Recordly `src/i18n/locales/en/editor.json` (`annotations.supportedFormats`).
