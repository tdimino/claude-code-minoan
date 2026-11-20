# First world

Paint a place in code: a 3D scene rendered entirely as brushstrokes on a 2D canvas, in one HTML file, that a person can look around or walk through. The brushwork is the subject. It should read as an oil or gouache painting that breathes, not as a 3D engine with a filter on it.

The user message gives the mode and the brief. Everything below holds for every brief.

## Output

Return one complete HTML document and nothing else. Start with `<!doctype html>` and end with `</html>`. No markdown fence, no commentary before or after.

## Hard limits

- One file. Inline CSS and one inline script.
- Canvas 2D only: `getContext('2d')`. No WebGL, no WebGPU, no libraries.
- No network and no external resources: no `<script src>`, stylesheets, images, fonts, `fetch`, workers, `eval` or `new Function`. The page is opened under a Content-Security-Policy that blocks all of them.
- Sound, if the brief asks for it, is synthesized with Web Audio and starts on the first user gesture.

## Method

- A software camera projects world points to the screen. Every visible surface is laid down as layered brushstrokes: a soft under-shadow, the body of the stroke, a darker streak, a lit ridge.
- Every stroke has a stable, non-negative integer id, unique in view. Its jitter is hashed from `(id, epoch)` where `epoch = floor((frame + id % hold) / hold)`, so each stroke rests for `hold` frames and then re-rolls once, on its own schedule. Never take an id from a per-frame array index or a screen position.
- No `Math.random()` and no clock in anything a still frame can see. Generate the world from hashes of world coordinates and a fixed seed, so the same URL paints the same pixels on every load.
- Repaint at 12 fps and simulate movement every animation frame. At 12 fps the re-rolls read as animation drawn on twos, and faster turns them into noise.
- Ground strokes lie in perspective: project both ends of each stroke and derive its angle, length and width from the projected points. Skip a stroke whose far end is behind the camera.
- Fill first, stroke second: a polygon in the base color under the brushwork, so there are no holes.
- Clip polygons against the near plane before projecting anything the camera can pass over.
- There is no depth buffer. Build one draw list and sort it far to near. Sort a ground quad behind its farthest corner, with ground paint just above it and standing objects slightly forward.
- One fog function for every layer, fading toward the sky's horizon color, resampled each frame.
- Store colors as HSL, mix them in RGB. Shadows go violet, never gray. Lit edges go warmer and lighter.
- Every color passes through the same chain: base color, time-of-day grade, fog by depth.
- Finish each frame with a canvas weave and a vignette in `multiply`, which binds separate strokes into one surface.
- Stay under 20,000 calls to the context's `stroke()` method per frame at a 960 px long edge.

## Test contract

The page is verified by loading these URLs, so each parameter must work exactly as described.

| Parameter | Behavior |
|---|---|
| `?frame=N` | Paint frame N once, deterministically, then stop: no loop, no input |
| `?tod=0..1` | Time of day. 0.5 is noon, 0.74 dusk, 0.95 night |
| `?px=`, `?pz=` | Camera position in world meters |
| `?yaw=`, `?pitch=` | Camera angles in radians |
| `?stats=1` | Set `window.__paintStats = {frame, stroke, fill}`: calls to the context's `stroke()` and `fill()` in the last painted frame |

Under `prefers-reduced-motion: reduce`, paint one frame and rest.

## Composition

The first frame is a picture. Choose the spawn pose, the time of day and the shape of the land near the origin so the opening view has a foreground, a middle distance and a horizon, a focal point, and light from one direction. Spawn on dry land.

Controls where the mode has them: drag to look, WASD or arrows to walk, Q and E to turn. Clear held keys on blur.

## Ambition

Spend the effort on paint quality and on the place: varied stroke direction and length by material, broken color, water that moves, vegetation that answers wind, a sky with weather in it, landmarks worth walking to. A smaller world painted well beats a large one painted thinly.
