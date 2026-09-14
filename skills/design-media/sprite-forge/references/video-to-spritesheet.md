# Video-to-Spritesheet Pipeline (September 2026)

## Why video-first

Image models still have no temporal coherence: each frame is an independent sample, so limbs change length and poses teleport. Video models produce continuous motion, and the September 2026 models add **first+last-frame conditioning**, which is what makes a seamless loop possible: give the same anchor as first and last frame and the clip returns to its start pose.

## The pipeline

```
[anchor.png] -> genmedia (Wan 3 / Seedance 2.5 / Kling 3) on flat #00FF00
             -> ffmpeg fps=12 -> chroma_key.py --despill (once, deterministic)
             -> align_frames.py --cell 128x128 --dedup 6 --loop-check
             -> stitch_spritesheet.py --atlas v2 --state walk:12:loop [--aseprite-json]
```

One command:

```bash
python3 scripts/video_to_spritesheet.py --provider genmedia \
  --start-frame hero.png --end-frame hero.png \
  --prompt "side-view walk cycle in place, feet stay on one line, flat #00FF00 background, no camera motion" \
  --duration 4 --fps 12 --cell-size 128x128 --dedup 6 --state walk:12:loop --aseprite-json -o walk.png
# prints the exact genmedia command and price; add --yes to spend
```

From an existing clip:

```bash
python3 scripts/video_to_spritesheet.py --input walk.mp4 --fps 12 --cell-size 128x128 \
  --remove-bg chroma --dedup 6 --state walk:12:loop -o walk.png
```

## Loop recipe

1. Anchor still with the character mid-stance (contact pose), flat `#00FF00` background, no shadow on the ground.
2. Same image as `--start-frame` and `--end-frame`. Prompt "in place", "no camera motion", "feet stay on one line".
3. Extract at 12 fps; a 4 s clip gives 48 frames, `--dedup 6` collapses holds to 8-14 distinct frames; `--max-frames 8` samples evenly if you need exactly 8.
4. `alignment.json` -> `loop_dhash_distance <= 4` means the last frame duplicates the first: drop it (`--max-frames` or by hand).
5. Feet-line variance must be < 1 px^2 before stitching. If not, raise `--min-row-fraction` (thin shadow counted as feet) or check the matte.

## Model choice

| Model | First+last | Refs | Why |
|---|---|---|---|
| `alibaba/wan-3.0/image-to-video` | yes | | Default: cheapest per second, 30 s max, clean loops |
| `bytedance/seedance-2.5/image-to-video` | yes | up to 30 (`reference-to-video`) | Best multi-ref identity |
| `fal-ai/kling-video/v3/pro/image-to-video` | `tail_image_url` | `@Element1` | Strongest identity lock, priciest |
| `minimax/hailuo-03/image-to-video` | yes | | Timecoded prompts: `[0-2s] idle [2-4s] walk [4-6s] attack` then split with `--start/--end` per state |
| `fal-ai/veo3.1/image-to-video` | no | | Legacy default from March 2026 |

Field names (`end_image_url`, `tail_image_url`) are the script's defaults per model; verify with `genmedia schema <endpoint>` and override with `--param`.

## Background rule

Video models never emit alpha. Generate on flat chroma green and key once. Per-frame `rembg` produces a different matte per frame (halo width, holes) and the sheet flickers; the aligner reports this as `edge_drift_max > 0.5`. `rembg` stays useful for single stills.

## Multi-state sheets

Generate one clip per state (or one timecoded Hailuo clip cut with `--start/--end`), align each with the same `--cell`, then stitch once:

```bash
python3 scripts/stitch_spritesheet.py --input-dir all_frames/ --atlas v2 --cols 8 \
  --state idle:8:loop --state-frames idle=0-5 \
  --state walk:12:loop --state-frames walk=6-13 \
  --state attack:12:once --state-frames attack=14-21 --aseprite-json -o hero.png
```

## Manifest v2

```json
{ "schema": "sprite-forge/atlas-v2", "image": "walk.png", "cell": [128,128], "grid": [8,1],
  "directions": null,
  "states": { "walk": { "fps": 12, "loop": true, "frames": [[0,0,128,128], ...], "indices": [0,1,...] } },
  "anchor": { "feet_y": 121, "pivot": [0.5, 1.0] },
  "frames": [{ "index": 0, "source": "frame_0000.png", "rect": [0,0,128,128], "sha256": "..." }],
  "provenance": { "generator": "sprite-forge/video_to_spritesheet.py", "inputs_sha256": ["..."],
                  "config": {...}, "config_sha256": "...", "model": "alibaba/wan-3.0/image-to-video" } }
```

`--aseprite-json` writes the Aseprite array format (`frames[]` with `duration`, `meta.frameTags[]`) that Phaser, Flame and Godot importers consume. Legacy `--atlas json|xml` remain for old projects.

## Standard frame counts

| Animation | Frames | ms/frame |
|---|---|---|
| Walk | 6-8 | 60-120 |
| Run | 6-8 | 60-80 |
| Idle | 4-6 | 100-200 |
| Attack | 5-8 | 60-100 |
| Jump | 4-6 | 80-120 |
