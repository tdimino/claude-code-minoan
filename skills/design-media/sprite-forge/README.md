# Sprite Forge

Game-ready sprites, turnarounds, sprite sheets, SVG characters, ASCII art and animated mascots from images or text. September 2026 edition: Retro Diffusion and fal `genmedia` providers, deterministic alignment and scaling, atlas manifest v2, pipeline profiles.

## Pipelines

| Pipeline | Produces | Entry script |
|---|---|---|
| Turnaround | 8-direction sheet + atlas v2 (pixel via Retro Diffusion rotate8, HD via GPT Image 2.5 edits) | `turnaround.py` |
| Video -> sheet | Feet-aligned, keyed walk/idle/attack sheets with states, fps, loop, anchor; Aseprite JSON | `video_to_spritesheet.py` |
| Pixel scaling | Nearest / Scale2x / Scale3x / Scale4x with the palette preserved; RD free palette tools | `pixel_scale.py`, `retro_diffusion.py tool` |
| SVG + mascot | Gemini SVG-as-code, rect pixel mascots, GSAP timelines, lil-agents videos | `pixel_art_generator.py`, `animation_builder.py`, `generate_walk_video.py` |
| ASCII | Static ASCII/Unicode art, animated React components | `image_to_ascii.py` |
| Profiles | Declarative multi-stage runs with run manifests and skip-on-unchanged | `run_pipeline.py` + `pipelines/*.json` |

Every provider call is a free dry run until `--yes`.

## Quick start

```bash
S=~/.claude/skills/sprite-forge/scripts
python3 $S/turnaround.py --mode pixel --prompt "astromech droid" --ref droid.png --out ./turn
python3 $S/video_to_spritesheet.py --provider genmedia --start-frame hero.png --end-frame hero.png \
  --prompt "side-view walk cycle in place, flat #00FF00 background" --duration 4 --cell-size 128x128 \
  --dedup 6 --state walk:12:loop --aseprite-json -o walk.png
python3 $S/pixel_scale.py --input sprite.png --output sprite_4x.png --mode scale4x
python3 $S/stitch_spritesheet.py --input-dir frames/ --atlas v2 --state idle:8:loop -o idle.png
python3 $S/run_pipeline.py ~/.claude/skills/sprite-forge/pipelines/example.json --dry-run
```

## Inventory

**14 scripts** (+2 shared modules: secrets, images) | **16 references** | **2 templates** | **1 asset** | **2 pipeline files** | **1 test module** | **1 eval set**

### Scripts

| Script | Purpose |
|---|---|
| `retro_diffusion.py` | Retro Diffusion v2 client: `generate`, `animate`, `rotate8`, `pixelate`, `tool`, `styles`, `balance`; `check_cost` dry runs |
| `gen_image.py` | Still-image router: GPT Image 2.5 / Nano Banana 2 through `genmedia`, or RD Pro; uploads refs, prints price |
| `turnaround.py` | 8-direction sheets: pixel route (RD rotate8) or HD route (cardinals then diagonals) |
| `video_to_spritesheet.py` | Generate or ingest a clip -> ffmpeg -> chroma key -> align -> atlas v2 |
| `align_frames.py` | Feet-line and height alignment, canvas contract, dHash dedup, loop check, matte consistency |
| `pixel_scale.py` | Nearest / Scale2x / Scale3x / Scale4x on index arrays; `--family` with family sha256 |
| `stitch_spritesheet.py` | Frames -> sheet; atlas `json`, `xml`, `v2` (states, directions, anchor, provenance); `--aseprite-json` |
| `split_spritesheet.py` | Sheet -> frames |
| `chroma_key.py` | `#00FF00` removal with despill and feather |
| `run_pipeline.py` | Executes `pipelines/*.json` profiles with run manifests |
| `pixel_art_generator.py` | Image -> pixel-art SVG rects with body-part grouping (mascot path only) |
| `animation_builder.py` | GSAP presets and frame switchers (HTML/React/SVG) |
| `generate_walk_video.py` | HEVC-alpha walk video for lil-agents |
| `image_to_ascii.py` | Grayscale / colour half-block / jp2a ASCII |
| `_secrets.py` | Key lookup (flag, env, `~/.config/env/secrets.env`); copied from the meshy skill |
| `_images.py` | Shared `open_image()`: one-line error for a missing or non-image path instead of a traceback |

### References

| File | Topic |
|---|---|
| `provider-matrix.md` | Endpoints, prices, ref limits, alpha support, setup, PixelLab notes |
| `landscape-2026-09.md` | What changed since March 2026 and what was retired |
| `turnaround.md` | Pixel and HD 8-direction routes, prompt fragments |
| `video-to-spritesheet.md` | Loop recipe, model table, multi-state sheets, manifest v2 |
| `frame-alignment.md` | Feet-line algorithm, canvas contract, jitter checklist |
| `chroma-key-transparency.md` | Which models give alpha; chroma sentence; why not rembg on video |
| `gemini-svg-generation.md`, `pixel-art-svgs.md`, `gsap-timeline-patterns.md`, `ayotomcs-deconstruction.md`, `lil-agents-character-spec.md` | SVG and mascot |
| `ascii-art-techniques.md`, `ascii-animation-components.md`, `animated-ascii-sprites.md` | ASCII |
| `pipelines/open-rebellion.md` | Pointer to the Open Rebellion repo profile |

### Pipelines, tests, evals

- `pipelines/schema.json` (profile schema), `pipelines/example.json` (generic 8-dir character)
- `tests/test_deterministic.py` (aligner + scaler on synthetic frames): `python3 tests/test_deterministic.py`
- `evals/evals.json` (four trigger/behaviour cases, all dry-run)

## Dependencies

Pillow (+ numpy optional), ffmpeg, ImageMagick 7, `genmedia` (`curl https://genmedia.sh/install -fsS | bash`), `rembg` (stills), jp2a (optional), GSAP 3 via CDN. Keys: `FAL_KEY`, `RETRODIFFUSION_API_KEY`.

## History

- Mar 25 2026: `svg-mascot-animator` (image -> pixel SVG -> GSAP).
- Mar 27 2026: renamed `sprite-forge`, five modes, chongdashu isometric pipeline, Veo 3.1 walk cycles.
- Sep 14 2026: v2. Retired `isometric_pipeline.py` and the nano-banana-pro dependency; added Retro Diffusion v2 and fal `genmedia` providers, `turnaround.py`, `align_frames.py`, `pixel_scale.py`, atlas manifest v2 + Aseprite JSON, pipeline profiles; rembg demoted to stills. Research: Exa + Keenable, ~40 sources (see `references/landscape-2026-09.md`).
