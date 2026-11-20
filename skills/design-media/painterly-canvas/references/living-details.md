# Living Details

Weather, wind, walk-in rooms, things to click, and sound: the systems the genesis layers on top of its landscape. Each is optional and independent, so add them one at a time on top of a working kernel. The starter has none of them. Line numbers refer to the genesis, `assets/genesis/endless-painted-world.html`.

## Contents

1. Atmosphere: cloud shadow, wind, rain
2. Interiors
3. Interaction
4. Player and collision
5. Soundscape
6. URL parameters and presets
7. Rare events

## 1. Atmosphere

All three are functions of world position and time, sampled wherever a color or an angle is computed. None stores state per object.

**Cloud shadow** (283–296). Two octaves of value noise at about 0.009 cycles per meter, scrolled by `t`, thresholded with `smoothstep(0.46, 0.74, n)`. The result darkens any color toward indigo-violet, scaled by `dayFactor` and reduced under rain. It is applied to ground quads, ground strokes, anchors and far-horizon cells alike, so one shadow band visibly sweeps from the horizon to the player's feet. Water takes it at about half strength.

**Wind** (298–306). Two sine wave fronts crossing diagonally give `{ gust, crest }`. `gust` (signed) leans grass tips and rotates ground strokes by a few hundredths of a radian. `crest` (positive part) lightens and yellows the tips of anything it passes, in daylight only. Without the lightening the lean reads as jitter, not wind.

**Rain** (264–281, 1057). A scalar on a schedule: a 42–60 s shower roughly every 150–210 s, eased in over the first 22% and out over the last 24%, peaking at 0.82, and never in the first 85 s so the opening view is clear. `?weather=rain` holds it at 0.86. It feeds `sampleDayState`, which grays the sky, which grays the fog, which grays everything. Layered over that:

- `round(145 + rain × 210)` slanted streak lines in screen space, positioned by hash so they do not boil, every second one with a shadow line beside it
- a faint full-frame vertical gray gradient (1078–1083)
- ripple rings spawned on nearby water (309, 1034)
- darker paths and cobbles
- a filtered noise layer in the audio

## 2. Interiors

Eight room types (café, bakery, bookshop, home, church, chalet, winery, studio) plus the circular lighthouse and windmill. The method (3686–4912):

**Local frames.** `makeRoomTransform(x, z, floorY, yaw)` (827) returns `pt(lx, ly, lz)` and `vec(nx, ny, nz)`, mapping room-local coordinates to world. Every room is authored as if axis-aligned at the origin. `makeRoomCtx` (3686) wraps that with short methods (`R.box`, `R.poly`, `R.lseg`, `R.wall`, `R.dab`) that pre-bind the camera, lighting, fog and an id base, so furnishing code reads as a list of placements.

**Three passes per building** (`drawEnterableBuilding`, 3772).

1. Inward-facing shell (3813): floor, ceiling, walls seen from inside.
2. Depth-sorted furniture (4131): each prop registers a closure with `R.addProp(lx, ly, lz, fn)`, and `flushProps()` sorts by camera depth and runs them.
3. Outward-facing shell (4835): thick exterior walls and roof, visible only from outside. This pass is the exterior of every enterable building, churches and chalets included.

Back-face culling in `drawPaintedPoly3D` decides which shell appears, so one function draws the building from either side.

**Openings are real holes.** `emitWallWithOpenings` (3470) splits each wall into rectangles around its doors and windows (`buildOpenings`, 3736). Nothing is drawn in the gaps.

**Order does the compositing.** The building the player stands in is skipped in the main draw list and painted last (6286), over the finished outdoor frame. Through its holes the already-painted world, rain included, shows as the view outside. No stencil, no second camera.

**Seen from outside**, rectangular buildings show their real interior through their real openings. Detail scales with distance: full furnishing when inside or within 22 m, reduced within 56 m, shell only beyond (3782–3784). The round towers work differently: `drawTowerPeekDoor` (5630) fills the lighthouse or windmill doorway with a mid-tone, clips to it, and paints a simplified glimpse of the room inside the clip.

**Wall brushwork.** For the room the player is in, or any within 22 m, walls are painted by `paintWallTapestry3D` (3359): dabs laid on a grid in the wall's own `(u, v)` coordinates, each projected to the screen and angled along the projected wall direction, so the brushwork is anchored to the wall and holds still as the camera moves. Spacing depends on the wall material (columns 0.56 m for plaster, 0.78 m for stone, 1.10 m for timber, rows 0.50–0.58 m), openings are skipped, and nearby room lights tint the dabs. Furniture, boxes, window reveals and the walls of more distant rooms use the screen-space staggered `paintFastDab` grid in `drawPaintedPoly3D` (3126–3142) with the five-note broken palette and optional cross-hatching.

**Indoor light.** `gradeIndoorCol` (2668) applies a per-room `indoorLight` factor that holds colors up against the night grade, so rooms glow warm after dark. Light spilling out of doorways onto the ground (`drawLightSpill3D`, 989) uses `screen` compositing. Window light pools on the floor (`drawWindowLightPool3D`, 2973) are an ordinary translucent fill with a grid of dabs over it.

Still-life props (bottles, vases, bread, sacks) are built from `paintRoundDab`. Paintings on the walls are small procedural pictures clipped to their frames (`paintArtSubject`, 3207).

## 3. Interaction

Clickable objects are picked in screen space (6559–6676).

- While painting a frame, anything clickable pushes `{ kind, sx, sy, r, ...payload }` onto `interactState.lastClickPts`, with its projected position and a radius scaled by depth and clamped, so far targets stay hittable and near ones do not swallow the screen. The array is cleared at the top of `renderWorld`.
- A click or tap finds the nearest entry within its radius. Touch widens radii by 1.6.
- Pointer movement runs the same lookup to toggle a pointer cursor.

Because targets are registered by the painter, they are exactly as visible as what was drawn: depth cutoffs and "only when inside" conditions carry over with no extra code.

Targets in the genesis: chairs (the player snaps to the seat facing the room and eye height eases down), the hearth (stoke: flames and audio surge, then decay), the church bell rope, the studio easel (each click adds a stroke where it landed, in the next of seven palette colors, kept per building up to 24), lighthouse stairs (jump to the lantern room and back), and rowboats and bicycles (board, with their own physics and a cockpit overlay drawn in screen space).

One fallback uses a ray: when a click hits no target and the player is outdoors, the camera ray is intersected with the water plane, and a hit between 2.5 m and 34 m throws a pebble there, a ripple ring plus a panned plop (6610–6629).

State that outlives a frame is small and explicit: `interactState` (316) and a few maps (`easelStrokes`, `movedBoats`). Generated data is static apart from rideable vehicles, which are moved in place, and `movedBoats` keeps a moved boat alive when its chunk or landmark is rebuilt.

## 4. Player and collision

`updatePhysics(dt)` (6919) runs every animation frame with `dt` clamped to 50 ms.

- Height comes from `walkSurfaceY` (664): terrain, a pier deck, an interior floor, or the lighthouse stair height. The eye sits 2.35 m above it (1.48 m seated or in a boat, 2.52 m on a bicycle), with a 0.14 m sine bob while walking. The tall eye lifts the horizon and shows more ground paint.
- Collision is a point test before committing a move: `hitsStructure(nx, nz)` (6858) checks rotated boxes (`hitsRotatedBox`, 6815) and cylinders for structures, and enterable buildings test against their walls with door gaps (`hitsEnterableBuilding`, 6820). X and Z are tried separately (7049–7050) so the player slides along walls.
- Look: drag on desktop, touch-drag with inertia on mobile (`exp(−dt · 8.5)` damping), pitch clamped to −0.58..0.64 rad.
- Mobile gets an on-screen arrow pad wired to the same key set (`#navPad`, `syncNavKeys` 6695).

Input rules the starter already follows, worth keeping in anything built from it: clear held keys on window `blur`, end a drag on `pointercancel` and `lostpointercapture` as well as `pointerup`, clamp pitch from URL parameters, and always accept a move that does not take the player deeper into water.

## 5. Soundscape

Everything is synthesized with Web Audio. There are no audio files (7101–7364).

**One noise buffer.** Four seconds of pink noise, generated once with Paul Kellet's filter (7131–7142) and looped.

**Continuous layers** are that buffer through a biquad filter into a gain node, optionally through a stereo panner (`addLoopLayer`, 7143):

| Layer | Filter | Driven by |
|---|---|---|
| Wind | bandpass 340 Hz, Q 1.6 | Always on. Cutoff and gain follow a slow gust cycle, altitude and cycling speed, cut to 20% indoors |
| Running water | bandpass 720 Hz | Nearness to the water level, a waterfall, or a town fountain, panned toward the source |
| Surf | lowpass 420 Hz | The sea field at the player's position, with a slow swell on gain and cutoff |
| Hearth | bandpass 540 Hz | Inside a room with a fire. Crackle modulation, boosted when stoked, panned to the fireplace |
| Rain | bandpass 2200 Hz | Rain intensity, sheltered indoors |
| Bicycle roll | bandpass 920 Hz | Riding speed. Cutoff changes with the surface under the wheels |

Oscillator layers add a 78 Hz triangle for windmill creak, two sines near 4.2 kHz amplitude-modulated at 6.2 Hz for crickets at night, and a five-note chord pad for the aurora.

**One-shots** come from two helpers: `playNoiseBurst` (a filtered slice of the buffer with an attack/decay envelope: footsteps per surface, splashes, brush on canvas) and `playTone` (an oscillator with frequency ramps: bird chirps, gull calls, bells).

**Stereo placement** is a single dot product (`computePan`, 7112): the direction to the source against the player's right vector, clamped to ±0.92, fed to a `StereoPannerNode`. Loudness comes from a separate proximity term per layer.

**Rules.**

- Create the `AudioContext` on the first pointer or key event, because browsers block it before a gesture. Start muted with a visible toggle, and never unmute over an explicit user mute (`userMuted`, 7216).
- Change gains with `setTargetAtTime`, never by assigning `.value`: assignment clicks.
- Idle layers sit at gain 0.0001, not 0, so exponential ramps stay valid.
- `updateAudio` (7282) runs every frame. For the continuous layers it only sets targets and creates no nodes. It also schedules the timed one-shots (birds, gulls, bells, footsteps), each of which creates short-lived nodes.

## 6. URL parameters and presets

| Parameter | Effect |
|---|---|
| `?frame=N` | Paint frame N once at `t = N / 12` and stop: no loop, no input. Deterministic |
| `?at=<name>` | Jump to a named preset: position, facing and time of day (`PRESETS`, 6325) |
| `?px= &pz= &yaw= &pitch=` | Explicit pose, overriding the preset |
| `?tod=0..1` | Time of day: 0 midnight, 0.25 dawn, 0.5 noon, 0.75 dusk |
| `?weather=rain\|clear` | Force or forbid rain |
| `?event=aurora\|rainbow\|comet\|balloon` | Force a rare event. It fades by a sine of elapsed time and is visible only while `t < 15 s`, so with `?frame=N` use N below 180 (peak near N = 36) |
| `?mobile=1` | Preview the touch layout on desktop |

Preset names: `meadow`, `town`, `seaside`, `lighthouse`, `mountains`, `aqueduct`, `vineyard`, `cafe`, `seaside-cafe`, `bakery`, `bookshop`, `home`, `seaside-bakery`, `seaside-bookshop`, `church`, `chalet`, `winery`, `studio`, `lighthouse-inside`, `lighthouse-top`, `windmill`, `windmill-inside`, `sheep`, `rowboat`, `bicycle`, `riding`, `rain`, `fireflies`.

A browser opened from the shell needs a full `file://` URL to carry these: `agent-browser open "file:///abs/path/endless-painted-world.html?at=town&frame=5"`. macOS `open` treats `?at=…` as part of the file name and fails.

Build presets and `?frame` into any new scene from the first version. A headless browser checks the work through them, and a specific view is shared through them.

## 7. Rare events

`updateRareEvents` (6895): the first check comes 26–46 s in, then every 28–58 s a 34% roll starts one event from a pool chosen by time of day (comet or aurora at night, balloon or rainbow by day). A comet lasts 14 s, the others 22 s, and each is placed near the player's facing so it is likely to be seen. After an event ends the next check waits 36–70 s. An active event forces the far cache to repaint every frame, and a forced `?event=` never clears, so it costs that for the whole session. The aurora adds a `screen`-composited green gradient over the whole frame, a `lighter` curtain in the sky, and its own chord in the audio.
