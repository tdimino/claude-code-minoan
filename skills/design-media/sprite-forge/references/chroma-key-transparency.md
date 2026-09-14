# Chroma Key & Model Transparency (September 2026)

## Model capabilities

| Model / route | True alpha | Do this |
|---|---|---|
| GPT Image 2.5 Flare / Sunburst (fal `openai/gpt-image-2.5/...`) | Yes | `gen_image.py --transparent` (`background=transparent`, PNG) |
| Retro Diffusion (any style) | Yes via `remove_bg: true`; edit tool `background_remover` ($0.01) | `retro_diffusion.py generate --remove-bg` |
| Nano Banana 2 / Pro (fal or Gemini) | **No** (faux dark backdrops) | Prompt exact `#00FF00`, then `chroma_key.py --despill` |
| Every video model (Wan 3, Seedance 2.5, Kling 3, Hailuo 03, Veo 3.1) | **No** | Generate on flat `#00FF00`, key once per frame set with `chroma_key.py`; never `rembg` per frame |
| Blender headless renders | Yes (`film_transparent`) | Nothing to key |

## The chroma sentence

```
Use an exact flat chroma green background #00FF00 across the entire image,
no gradient, no shadow on the background, no texture, no green spill on the subject.
```

## Removal

```bash
python3 scripts/chroma_key.py --input frame.png --output frame.png --despill            # stills
python3 scripts/video_to_spritesheet.py --input clip.mp4 --remove-bg chroma ...           # clips (keys every frame with one setting)
```

`chroma_key.py` flags: `--color` (default `00FF00`), `--tolerance` (Euclidean RGB distance, default 30; video frames with compression noise want 40-60), `--despill` (clamp green on edge pixels), `--feather` (alpha blur radius, default 1; use 0 for pixel art).

## Why not magenta

`#FF00FF` bleeds into red scarves, brown leather and purple cloaks at the edges. Game characters rarely contain pure `#00FF00`; green costumes are the one case to lower `--tolerance` to 20 or mask by hand.

## Why not rembg on video

Each frame gets its own matte (halo width, holes, hairline decisions), so the outline flickers at 12 fps even when the character is still. `align_frames.py` reports this as `perimeter_cv` > 0.15. `rembg` remains the right tool for photographic single stills with arbitrary backgrounds.

## Pixel-art specifics

- Retro Diffusion inputs must be RGB with no alpha; `retro_diffusion.py` composites transparent inputs onto `--matte` (default `#00FF00`) so the result can be keyed again.
- Key with `--feather 0` and `--tolerance 10-20`; pixel art has no anti-aliased edge to soften.
- After keying, `retro_diffusion.py tool pixel_correction` (free) snaps stray semi-transparent pixels back to the grid.
