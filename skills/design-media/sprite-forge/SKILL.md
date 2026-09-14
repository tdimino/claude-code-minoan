---
name: sprite-forge
description: "Generate game sprites, 8-direction turnarounds, walk-cycle sprite sheets, SVG characters, ASCII art and animated mascots from images or descriptions, with September 2026 providers: Retro Diffusion (pixel art, 8-dir rotation, frame animation, free palette tools), fal genmedia (GPT Image 2.5, Nano Banana 2, Kling 3, Seedance 2.5, Wan 3, Hailuo 03). Deterministic utilities: feet-line frame alignment, palette-preserving Scale2x/3x/4x pixel scaler, atlas manifest v2 with states/fps/loop/anchor, Aseprite JSON, pipeline profiles. Triggers on sprite, pixel art, sprite sheet, spritesheet, turnaround, 8-direction, walk cycle, atlas manifest, frame alignment, pixel scaler, Retro Diffusion, genmedia, SVG character, ASCII art, mascot, game asset, sprite pipeline profile."
argument-hint: "[description or image path] [--mode turnaround|sheet|scale|svg|ascii|mascot]"
---

# Sprite Forge

Game-ready sprites from images or text, September 2026 edition. Five pipelines, two wired providers (Retro Diffusion, fal `genmedia`), and a profile runner so a project can declare its own pipeline.

**Cost rule:** every provider script is a free dry run until you pass `--yes`. Retro Diffusion runs `check_cost`; genmedia prints the exact command and price. Never add `--yes` on a user's behalf without stating the estimate.

## When to use

- Pixel-art characters, 8-direction rotations, animated frames from a start image
- Walk/idle/attack sprite sheets from video (first+last-frame loops)
- HD painted turnarounds via GPT Image 2.5 edits
- Upscaling indexed sprites without new colours (faithful-HD rule)
- Atlas metadata with states, fps, loop, anchor (Phaser/Godot/Flame/Aseprite)
- SVG mascots with GSAP, ASCII art, lil-agents dock videos (unchanged niche)

Not for: 3D generation (meshy skill), photoreal image editing (nano-banana-pro skill), generated sprites where original assets exist and parity is required (see `references/pipelines/open-rebellion.md`).

Work sequentially inside a pipeline; parallel agents only for independent characters.

## Quick start

```bash
S=~/.claude/skills/sprite-forge/scripts
# 8-direction pixel sprite (one Retro Diffusion call, $0.25)
python3 $S/turnaround.py --mode pixel --prompt "astromech droid" --ref droid.png --out ./turn   # add --yes
# Walk cycle: Wan 3 clip on chroma -> key -> feet-align -> atlas v2 (+ Aseprite JSON)
python3 $S/video_to_spritesheet.py --provider genmedia --start-frame hero.png --end-frame hero.png \
  --prompt "side-view walk cycle in place, flat #00FF00 background" --duration 4 --cell-size 128x128 \
  --dedup 6 --state walk:12:loop --aseprite-json -o walk.png                                   # add --yes
# Indexed sprite 4x with the same palette
python3 $S/pixel_scale.py --input sprite.png --output sprite_4x.png --mode scale4x
# Frames -> sheet with manifest v2
python3 $S/stitch_spritesheet.py --input-dir frames/ --atlas v2 --state idle:8:loop --cols 8 -o idle.png
# Profile
python3 $S/run_pipeline.py ~/.claude/skills/sprite-forge/pipelines/example.json --dry-run
```

## Pipeline 1: Turnaround (`turnaround.py`)

- `--mode pixel`: `rd_animation__8_dir_rotation` (80x80, <= 5 refs) -> split -> `stitch --atlas v2 --directions 8`. One paid call.
- `--mode hd`: anchor -> 4 cardinal edits -> 4 diagonal edits (anchor + two neighbours as refs) -> key if `--chroma` -> `align_frames` -> stitch. Default model `openai/gpt-image-2.5/sunburst/edit` (true alpha); `--model fal-ai/nano-banana-2/edit --chroma` for typed refs.
- Order in the sheet: S, SE, E, NE, N, NW, W, SW. See `references/turnaround.md`.

## Pipeline 2: Video -> sprite sheet (`video_to_spritesheet.py`)

`[genmedia clip] -> ffmpeg -> chroma_key (once) -> align_frames (feet line, dedup, loop check) -> stitch v2`. Default model `alibaba/wan-3.0/image-to-video` with `--end-frame` = start frame for a seamless loop; alternates Seedance 2.5, Kling 3 (`@Element` identity), Hailuo 03 (timecoded multi-state). Per-frame `rembg` on video is refused (matte flicker) unless `--allow-rembg-video`. Recipe and model table: `references/video-to-spritesheet.md`; jitter rules: `references/frame-alignment.md`.

## Pipeline 3: Pixel scaling and palette (deterministic)

- `pixel_scale.py --mode nearest|scale2x|scale3x|scale4x`, mode-P in, mode-P out, palette block and transparency kept, colour count never grows. `--family dir/ --output-dir out/` transforms a frame family and writes `family.json` with a family sha256.
- Retro Diffusion free tools for the generative side: `retro_diffusion.py tool k_centroid_downscale --input-image in.png --field width=64 --field height=64`, `tool palette_converter --palette pal.png`, `tool color_reducer --field color_count=16`, `tool pixel_correction`; `pixelate` (`rd_pro__pixelate`, $0.18) turns any raster into native pixel art.
- `pixel_art_generator.py` survives only for the SVG `<rect>` mascot path (Pipeline 4).

## Pipeline 4: SVG characters and GSAP mascots

Gemini SVG-as-code for clean vectors (`references/gemini-svg-generation.md`); `pixel_art_generator.py --grid 16-24 --colors 4-6 --merge` for rect-based pixel mascots (`references/pixel-art-svgs.md`); `animation_builder.py --preset idle|bounce|lean|wave|walk|walk-and-bounce|walk-and-wave|typing` for GSAP timelines (`references/gsap-timeline-patterns.md`, `references/ayotomcs-deconstruction.md`); `generate_walk_video.py sheet.png --cols 6 --name robot` for lil-agents HEVC-alpha dock videos (`references/lil-agents-character-spec.md`). Trim AI images first: `magick in.png -fuzz 15% -trim +repage out.png`.

## Pipeline 5: ASCII

`image_to_ascii.py img.png --mode gray|color|jp2a --width 80` for static art (`references/ascii-art-techniques.md`); frame-based React components and the asciistudio catalog in `references/ascii-animation-components.md` and `references/animated-ascii-sprites.md`; template `assets/ascii-animation-template.tsx`.

## Profiles (`pipelines/`)

A profile (`pipelines/schema.json`) is an ordered list of stages over these scripts with `${var}` substitution. `run_pipeline.py profile.json [--dry-run] [--yes] [--stage name] [--from name] [--force]` writes `<output_root>/run/<id>/manifest.json` with per-stage commands and input/output sha256 and skips unchanged stages. `pipelines/example.json` is the generic character profile; project profiles live in their repos (Open Rebellion: `references/pipelines/open-rebellion.md`).

## Provider matrix (short)

| Need | Use | Alpha |
|---|---|---|
| Pixel still / identity | RD `rd_pro__default` + `--ref` (<= 9), $0.18 | `--remove-bg` |
| 8 directions, pixel | RD `rotate8`, $0.25 | yes |
| Animate a start frame | RD `animate --action walking|idle|attack|jump|crouch|custom_action` | key on `--matte` |
| HD anchor / edits | `openai/gpt-image-2.5/sunburst[/edit]` via `gen_image.py` | yes |
| Many typed refs | `fal-ai/nano-banana-2/edit` | no, chroma |
| Loops | `alibaba/wan-3.0/image-to-video` first+last | no, chroma |
| Identity-critical clip | `fal-ai/kling-video/v3/pro/image-to-video` `@Element1` | no, chroma |

Full table, prices, setup commands and PixelLab notes: `references/provider-matrix.md`. Setup: `genmedia` CLI (`curl https://genmedia.sh/install -fsS | bash`, then `genmedia setup --non-interactive --api-key "$FAL_KEY"`), `RETRODIFFUSION_API_KEY` in `~/.config/env/secrets.env`; optional RD MCP `claude mcp add --transport http retro-diffusion https://mcp.retrodiffusion.ai/mcp --header "Authorization: Bearer rdpk-..."`.

## Gotchas

- **Feet line, not bbox.** Halos and shadows move the bbox; `align_frames.py` scans for the lowest row with >= 5% solid width. Check `feet_line_variance < 1`.
- **One matte per clip.** Chroma-key video frames with one setting; per-frame `rembg` flickers (`perimeter_cv > 0.15`).
- **RD limits.** Styles cap at 384 px, animations at 256 and must match the start frame; `input_image` must be RGB without alpha (scripts composite onto `--matte`); `negative` is ignored; never write "pixel art" in RD prompts; balance is charged before generation.
- **genmedia.** Use `--async` for anything over ~5 s (the video script does); verify endpoint ids and field names with `genmedia models` / `genmedia schema`; the GPT Image 2.5 endpoint spelling came from a third-party commit.
- **Nano Banana 2 still has no alpha**; GPT Image 2.5 and RD do. Never key magenta on warm costumes.
- **Manifest v2 pastes at cell origin**; use `--fit scale` only for legacy sheets that need centring.
- **Pixel art through the aligner**: `--no-scale`, and the scaler uses nearest below 256 px.
- **Turnarounds:** cardinals, then diagonals; diagonals come out shorter, so never skip the align step.

## Dependencies

Pillow (numpy optional, speeds `pixel_scale.py`), ffmpeg, ImageMagick 7, `genmedia` CLI (fal), `rembg` (stills only), jp2a (optional), GSAP 3 via CDN. Keys: `FAL_KEY`, `RETRODIFFUSION_API_KEY` (loaded by `scripts/_secrets.py` from env or `~/.config/env/secrets.env`).

## Reference

- `references/provider-matrix.md`, `references/landscape-2026-09.md` — endpoints, prices, what changed
- `references/turnaround.md`, `references/video-to-spritesheet.md`, `references/frame-alignment.md`, `references/chroma-key-transparency.md` — pipeline details
- `references/gemini-svg-generation.md`, `references/pixel-art-svgs.md`, `references/gsap-timeline-patterns.md`, `references/ayotomcs-deconstruction.md`, `references/lil-agents-character-spec.md` — SVG and mascot
- `references/ascii-art-techniques.md`, `references/ascii-animation-components.md`, `references/animated-ascii-sprites.md` — ASCII
- `references/pipelines/open-rebellion.md` — project profile pointer
- `tests/test_deterministic.py` — run `python3 tests/test_deterministic.py`
