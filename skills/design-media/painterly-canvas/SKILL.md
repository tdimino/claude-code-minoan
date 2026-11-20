---
name: painterly-canvas
description: Build interactive painterly 3D scenes and walkable worlds in one HTML file with Canvas 2D only—no WebGL, no libraries. A layered brushstroke engine whose jitter is hashed from stable stroke ids and frame epochs, so paint breathes at 12 fps without flicker. Scripts have Gemini 4 Neon or a sibling (Hydrogen, Carbon, Argon) paint and revise a first draft through OpenRouter. This skill should be used when code must render a scene as live brushwork: an impressionist or oil-painted landscape or village to look around or walk through, a breathing painted view, impasto strokes in canvas, brushstrokes that flicker or pulse, a world painted by Gemini Neon, or extending the Endless Painted World template. Not for still-image generation or style transfer (nano-banana-pro, gpt-atelier), three.js or GLSL painterly shaders (webgpu-threejs-tsl, rocaille-shader) or scroll-driven painted backdrops (scroll-cinema). Triggers on painterly canvas, painted world, living painting, brushstroke renderer, stroke-based rendering.
argument-hint: "[--mode still|scene|world|extend] [--model neon|hydrogen|carbon|argon] [subject]"
---

# Painterly Canvas

Paint a navigable 3D scene with brushstrokes, on a plain 2D canvas, in one HTML file. The method is distilled from George Kenwright's *Endless Painted World* (`assets/genesis/`), a 7,397-line single-file world with villages, walk-in interiors, weather and sound.

The whole look rests on one idea: **every brushstroke carries a stable integer id, and its jitter is hashed from `(id, frame epoch)`**. The stroke holds still for a few frames, then re-rolls once, on its own schedule. Paint appears alive and hand-laid, neither flickering nor frozen.

## When Canvas 2D is the wrong tool

Use `threejs-particle-canvas` or `webgpu-threejs-tsl` when the brief needs real meshes, textures, depth-correct intersections or 60 fps motion, `scroll-cinema` for a painted shader backdrop driven by scroll, `rocaille-shader` for GLSL effects, and an image-generation skill for a still picture in a painter's style. This technique has no depth buffer and a ceiling of 20,000 canvas stroke calls per frame. Use it when the brushwork is the subject and a single dependency-free file is wanted.

## Modes

| Mode | Output | Start from |
|---|---|---|
| `still` | One composed view, breathing in place, no input | Starter with the loop kept, input and chunk streaming removed: build the chunks around the fixed pose once at boot |
| `scene` | A bounded place with look and walk | Starter as is, terrain and content replaced |
| `world` | Endless terrain with regions and landmarks | Starter plus `references/world-pipeline.md` §3–6 |
| `extend` | New content inside a finished world | A copy of `assets/worlds/se-to-i-ja.html`, navigated by `references/se-to-i-ja-map.md`; or, when the genesis is named, a copy of the genesis file, navigated by `references/genesis-map.md` |

Choose from the brief: a page hero or background with no controls is `still` (add drag-to-look if asked), a place to look or walk around is `scene`, an endless or explorable world is `world`, and a request to add to SE-TO-I-JA, the Zakros world, Endless Painted World or the genesis is `extend`. A `--mode` argument overrides the choice. Default to `scene`.

**The two `extend` targets carry different rights.** SE-TO-I-JA is ours: its output may be published, with the credits in its ledger kept. **`extend` output from the genesis is a modified copy of an unlicensed third-party work.** Say so in the final message: it is fine for private study and prototyping, and it needs George Kenwright's permission before being published, deployed or committed to a public repository. If `assets/genesis/endless-painted-world.html` is absent, fetch it and verify the checksum with the commands in `assets/genesis/PROVENANCE.md` before reading it.

## Workflow

1. **Copy the starter.** `assets/painterly-starter.html` is a tested 545-line kernel: surfaces, hashing, color, day state, terrain, camera, stroke engine, chunks, far layer, sorted near layer, post, loop. Copy it into the project and edit. Do not rebuild the kernel from memory, because its failure modes are subtle and already solved there.
2. **Compose before detailing.** Set the spawn pose, time of day and the terrain shaping near the origin so the first frame is a picture. An endless world still needs a composed opening view.
3. **Add content as data plus a painter.** Each new thing is a record created in `buildChunk` (position, size, color, a stable `id`) and a branch on `it.kind` in the sorted draw loop that paints it with `stroke()`. Keep generation and painting separate: chunks hold static data, motion is computed from `t` at draw time.
4. **Route every color through the chain**: base HSL → `grade(col, ds)` → `mix(col, ds.fog, fogAt(depth))`. Anything that skips it stays noon-bright at dusk.
5. **Verify in a browser.** Render deterministic stills with `agent-browser` and read the screenshots:
   ```bash
   agent-browser open "file:///abs/path/scene.html?frame=5&tod=0.5"
   agent-browser errors
   agent-browser screenshot /abs/path/shots/noon.png
   ```
   Check noon (`tod=0.5`), dusk (`0.74`) and night (`0.95`), a pose that looks across water if the scene has any, and a second `frame` value: the strokes should shift slightly while the picture stays the same.
6. **Measure if it grew.** Open the page with `?stats=1`, walk or turn, and read `window.__paintStats`. Its `stroke` field counts calls to the canvas context's `stroke()` method in the last painted frame (one brushstroke costs up to five). Stay under 20,000.

Read the genesis only for a specific technique, by line range. It is about 130,000 tokens, and `references/genesis-map.md` says where each system lives and maps starter names to genesis names.

## First draft from a Gemini 4 model

The genesis was built with Gemini 4 Neon. `scripts/first_world.py` asks Neon, or any model of its series, for the first draft of a new world through OpenRouter (`OPENROUTER_API_KEY`), and the session folder keeps every draft. Use it when the user asks for a model-made world, or wants several models' takes on one brief. Otherwise start from the starter as above.

Run the commands from the project directory, giving the script its full path inside this skill: drafts land in `./painted-worlds`, which should not be the skill folder. A call takes minutes, so run it in the background.

1. **Paint.** A bare model name resolves to `google/gemini-4-<name>`, checked against OpenRouter's live list (`models` prints it with prices).
   ```bash
   python3 scripts/first_world.py paint "A fishing village on a tidal estuary" --model neon --session estuary
   python3 scripts/first_world.py paint "Terraced olive hills" --only neon hydrogen carbon --session olives
   ```
   `--mode still|scene|world` sets the scope. `--seed none` (default) lets the model write its own engine, `starter` sends the kernel to build on, `full` adds the references. Each call prints a cost ceiling first and refuses to start above `--max-cost` (default $5). `--dry-run` prints the ceiling and calls nothing.
2. **Read the check.** Each world is saved as `painted-worlds/<session>/NNN_<model>.html` with a JSON sidecar (model, usage, cost, check result). The script runs `scripts/check_world.py` on it and exits 3 when the document is truncated or breaks a rule. Treat the file as untrusted code: it is saved with a no-network Content-Security-Policy, and a `check_world` error means do not open it.
3. **Look.** Run `python3 scripts/check_world.py <file> --browser`, which loads each pose twice in `agent-browser` and fails if the pixels differ (unseeded randomness in the paint path). Then render the stills of Workflow step 5 and read them.
4. **Revise or take over.** Send a critique and the screenshots back. The model answers with search-and-replace edits, which the script applies to the parent to make the next numbered draft. An edit whose search text is missing or ambiguous is rejected and listed, the script exits 3, and the draft is saved as `.partial.html` so the next revise does not start from it. `--model` may name a different model than the one that painted it.
   ```bash
   python3 scripts/first_world.py revise estuary "The far shore is flat fill. Water needs moving strokes." --shots shots/noon.png shots/dusk.png
   ```
   The series stops at 65,536 output tokens, reasoning included, so a whole-file rewrite only fits a world under about 1,200 lines (`--whole`). A model paints one bounded scene per call: build a larger world by hand from the kernel and use the models for studies of single subjects. After a round or two, edit the file by hand with the references.

`python3 scripts/check_world.py file.html` also works alone on any painterly page, as a static first pass before the browser.

## Fixing an existing painterly page

1. Add `?frame=N` if the page lacks it, so the fault reproduces deterministically.
2. Match the symptom in `references/stroke-engine.md` §9 or `references/world-pipeline.md` §12 before reading code.
3. Check, in order: where each stroke's id comes from, the epoch expression, any randomness reachable from the paint path (`Math.random` and aliases such as a destructured `random`), then the sort keys and fog curves.
4. Verify with two consecutive `?frame` stills and one still after moving the pose.

## As a page hero or background

The starter is a centered 16:10 card. For a full-bleed hero, set `W` and `H` from the container's aspect at boot, keeping the long edge near 960 logical pixels so stroke tuning holds, drop the card styling, and re-compose the spawn pose for the new framing. The starter already paints a single frame and rests under `prefers-reduced-motion: reduce`, since the re-rolls are motion. Stop the loop with an `IntersectionObserver` when the canvas scrolls out of view: thousands of stroke calls at 12 fps behind page content are wasted work.

## Rules the look depends on

- **No `Math.random()` while painting.** Use `jitter(id, epoch, k)` or a hash of world position. Random at draw time makes the image boil.
- **Ids are stable, non-negative and unique in view.** Give each chunk a block of ids packed from its coordinates, and reserve a sub-block per multi-stroke object. Never derive an id from a per-frame array index or screen position. Non-negative, because `%` keeps the sign and a negative id breaks the stagger.
- **Repaint at 12 fps, simulate every frame.** At 12 fps the re-rolls read as animation drawn on twos. Raising the rate turns them into noise.
- **Project both ends of a ground stroke.** Angle, length and width come from projected world points, so paint lies in perspective. Screen-space strokes float like stickers. Skip a stroke whose far end is behind the camera.
- **Fill first, stroke second.** A polygon in the base color goes under the brushwork, with a same-color 1.25 px outline to seal seams and a corner-to-corner gradient up close to hide the quad grid. Strokes alone leave holes.
- **Near-clip anything underfoot.** Use `clipPoly`, not bare `project`, for ground and walls. Unclipped polygons explode across the screen as the camera passes over them.
- **Sort ground behind its farthest corner.** Ground quads sort at `maxCz` plus a bias (`+ 4.5` in the starter), ground paint just above its position (`cz + 0.4`), standing objects slightly forward (`cz − 0.3`). Sorting quads on mean depth hides some strokes and slices the rest along straight lines.
- **One fog function for every layer.** Near and far layers with different curves leave a band where they meet.
- **Shadows go violet, never gray.** Mix toward hue 218–246 at saturation 20–55. Gray shadows read as mud, and a cool violet shade keeps the warm-light, cool-shadow split of impressionist color. Lit edges shift warm and lighter.
- **Mix colors through RGB, store as HSL.** Direct hue interpolation swings through unrelated colors.
- **Fog color is the sky's horizon color**, resampled every frame, so distance dissolves into the current sky.
- **Finish with weave and vignette** in `multiply`. The shared weave binds separate strokes into one surface.
- **Ship `?frame=N` and pose parameters** from the first version, because a painting that moves cannot be tested any other way.

## Dials

| Dial | Effect | Typical |
|---|---|---|
| `hold` | Frames a stroke rests between re-rolls | 2 water and flowers, 4 ground and walls, 6 interiors |
| `drift` | Hand wobble in px | 0.7 architecture, 1–1.8 plants, 2 ground |
| `impasto` | Paint thickness: under-shadow and lit ridge | 0.2 washes, 0.42 ground, 0.55 petals |
| Strokes per m² | Ground coverage | 0.4–0.7 |
| Stroke fade range | Where ground strokes dissolve and washes take over | 30–44 m |
| Paint rate | `STEP` | 1/12 s |

## References

| File | Read when |
|---|---|
| `references/stroke-engine.md` | Changing how marks look: layering, feathering, ids, broken color, painted polygons, and a symptom-to-cause table. Gives starter and genesis values side by side |
| `references/world-pipeline.md` | Changing what is drawn and in what order: fields, regions, chunks, far-horizon cache, draw list, quad washes, color chain, post, budgets |
| `references/living-details.md` | Adding cloud shadow, wind, rain, walk-in interiors, click targets, collision, synthesized audio, URL presets, rare events |
| `references/genesis-map.md` | Reading the genesis: the starter-to-genesis name map, a section-by-section line index and a technique lookup table |
| `references/se-to-i-ja-map.md` | Reading or extending the Zakros world: its modules and functions by line, its URL contract, and where each technique lives |

## Assets

- `assets/painterly-starter.html`: the kernel to copy. A compact reimplementation of the genesis's method, and its `stroke()` follows the layer recipe of the genesis's `paintedStroke`. Rendered and checked at noon, dusk shoreline and night. What it lacks against the genesis is tabled under "Known limitations and what to improve" in `README.md`.
- `assets/prompts/first-world.md`: the system brief `first_world.py` sends: output rules, the method and the URL test contract. Edit it to change what every model is asked for.
- `assets/worlds/se-to-i-ja.html`: a finished bounded world built on the starter, about 2,000 lines: Minoan Zakros with a palace, a gorge, creatures, a dance, sound, inscriptions written stroke by stroke and a ledger of sources. Ours to modify and publish. A worked example of buildings, figures, canvas labels, touch controls and quality tiers, and the `extend` target. Lines of embedded data are several thousand characters long: read by range from `references/se-to-i-ja-map.md`, never whole.
- `assets/genesis/endless-painted-world.html`: the source work, unmodified, for study and for `extend` mode. Not distributed with the skill: fetch it per `PROVENANCE.md` when absent. Supports `?at=<preset>` and `?frame=N`. Preset names are listed in `references/living-details.md` §6.
- `assets/genesis/PROVENANCE.md`: author, source URL, checksum, fetch command and rights. The genesis carries no license. Study it and write fresh code, and never copy its blocks into anything that ships without the author's permission.

## Scope

Keep additions proportional to the request. A hero background needs the kernel, a composed view and one or two content types, not weather, interiors and audio. Add a living-detail system only when the brief asks for it, one at a time, each verified with a still before the next.

## Attribution

- **Source work** — [*Endless Painted World — Living Impressions*](https://endless-painted-world.georgekenwright.workers.dev/) by **George Kenwright** ([@GeokenAI](https://x.com/GeokenAI)), 2026-11-18. Every technique documented here was learned by reading his file.
- **Model** — **Gemini 4 Neon** by Google DeepMind, the model he built the work with.
- **Starter kernel** — a simplified reimplementation of his method. Its brushstroke function is modeled on his `paintedStroke`, and the terrain, far layer and draw loop follow the architecture of his file at reduced scope.
- **Reference prose** — written for this skill from a reading of his code.
- **Pink noise filter** in the genesis soundscape — Paul Kellet's refined method.

When a scene built with this skill is published, credit George Kenwright's work as its source.
