# Sprite Generation Landscape (September 2026)

What changed since the March 2026 survey, and what it means for the pipelines in this skill.

## 1. Pixel-art specialists became agent-native

| Provider | Access | What it does best | Limits |
|---|---|---|---|
| **Retro Diffusion v2** | REST (`X-RD-Token`), official 18-tool MCP, `llms.txt` | RD Pro stills with <= 9 refs; `8_dir_rotation`; `advanced_animation__*` from a start frame; free `pixel_correction`, `palette_converter`, `k_centroid_downscale`, `color_reducer` | 384 px stills, 256 px animations, rotation fixed at 80x80, prepaid |
| **PixelLab** | REST v2 (subscription), community MCP over a private WebSocket API | 8-rotations Pro at 168 px with 4 subject refs, skeleton-driven animation | Not scriptable without the subscription; MCP unofficial |
| **Scenario / others** | Platform | Style-locked model training | Platform lock-in |

Consequence: hand-rolling eight directions through a general image model is the worst option for pixel art. `turnaround.py --mode pixel` is one RD call.

## 2. Video-first animation consolidated onto fal

`genmedia` (fal's agent-first CLI) runs every current model from the shell with `--json`, `--async`, `--download` templating and `genmedia upload` for local refs. The models that matter for sprites:

| Model | Endpoint | Sprite-relevant feature |
|---|---|---|
| Wan 3.0 | `alibaba/wan-3.0/image-to-video` | First+last frame, 30 s, cheapest per second |
| Seedance 2.5 | `bytedance/seedance-2.5/image-to-video`, `/reference-to-video` | First+last frame, up to 30 image refs |
| Kling 3 Pro | `fal-ai/kling-video/v3/pro/image-to-video` | `@Element` multi-image identity lock, 15 s |
| MiniMax Hailuo 03 | `minimax/hailuo-03/image-to-video` | Timecoded prompt blocks (one clip, several states) |
| Veo 3.1 | `fal-ai/veo3.1/image-to-video` | March default; no first+last frame |
| GPT Image 2.5 Flare / Sunburst | `openai/gpt-image-2.5/{flare,sunburst}[/edit]` | Released 2026-09-08; true transparency; Sunburst is the edit-fidelity tier |
| Nano Banana 2 | `fal-ai/nano-banana-2[/edit]` | 10 object + 4 character + 3 style refs; still no alpha |

Consequence: `video_to_spritesheet.py` generates the clip itself (first+last frame for loops), keys once on chroma, aligns, and emits atlas v2.

## 3. Open-source pipelines converged on "state row + manifest"

| Project | Takeaway adopted here |
|---|---|
| aldegad/sprite-gen (765 stars) | `prepare -> gen-set -> extract -> compose-atlas -> curation`; manifest with per-state fps/loop; Aseprite JSON export -> atlas v2 + `--aseprite-json` |
| LayrKits/Sprite-Pipeline (584 stars) | Fixed cells preserving the source canvas so scale never drifts -> `--fit origin` under v2, `align_frames --cell` |
| gykim80/perfectpixel-studio | Deterministic post-pass with bounded corrective regenerations -> the free RD tools plus `pixel_scale.py` |
| ybuild-ai skill | Vertical slice first, provider stub, dry-run before spend -> `--yes` gating everywhere |
| hey.paris (2026-05) | Feet-line detection instead of alpha bbox -> `align_frames.py` |

## 4. Blender pre-rendering

`extensions.blender.org` Sprite Sheet Generator 2.2.3 handles 4 angles only; Maghwyn/blender_directional_spritesheets does 4/8/16/32 with a Rust packer. For project-owned meshes, a headless `bpy` script with an ortho camera per direction plus `stitch_spritesheet.py --directions` is smaller and auditable (see `pipelines/open-rebellion.md`).

## 5. Still true

- Image models have no temporal coherence; animation comes from video models or RD's animation styles.
- Nano Banana still cannot emit alpha; chroma `#00FF00` and key.
- Standard specs: power-of-two cells, 4-16 colours for retro, walk 6-8 frames at 60-120 ms.

## Retired from this skill

`isometric_pipeline.py` (Nano-Banana-Pro edit chain), the March model-selection table, SEELE/Ludo/SpriteCook/AutoSprite comparisons (no longer decide anything), and per-frame `rembg` on video.

Sources: Retro Diffusion `llms.txt` and MCP README; PixelLab docs; fal learn (genmedia guide, Wan 3, Seedance 2.5, Kling 3, Hailuo 03); unite.ai/decrypt.co on ChatGPT Images 2.5; router.one on Nano Banana 2; sorceress.games video-to-sprite (2026-09-04); the repositories named above. Fetched 2026-09-14.
