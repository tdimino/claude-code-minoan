# Provider Matrix (September 2026)

Wired providers: **fal genmedia CLI** (stills + video) and **Retro Diffusion v2** (pixel art). PixelLab is documented, not wired. Every wrapper defaults to a free dry run; credits are spent only with `--yes`.

## Setup

```bash
# fal (one-time). FAL_KEY lives in ~/.config/env/secrets.env
curl https://genmedia.sh/install -fsS | bash && genmedia setup --non-interactive --api-key "$FAL_KEY"
genmedia models "gpt-image-2.5" --json        # verify endpoint ids before trusting this table
genmedia schema openai/gpt-image-2.5/sunburst/edit   # exact param names
genmedia pricing alibaba/wan-3.0/image-to-video

# Retro Diffusion. Key from https://www.retrodiffusion.ai/app/devtools (prepaid, rdpk-...)
export RETRODIFFUSION_API_KEY=rdpk-...
python3 scripts/retro_diffusion.py balance
python3 scripts/retro_diffusion.py styles --tab tab:animation

# Optional MCP for interactive use (Tom's action, not the scripts')
claude mcp add --transport http retro-diffusion https://mcp.retrodiffusion.ai/mcp \
  --header "Authorization: Bearer rdpk-..."
```

## Stills and edits (fal, via `gen_image.py`)

| Job | Default endpoint | Alternate | Refs | Alpha | Notes |
|---|---|---|---|---|---|
| Identity anchor / HD still | `openai/gpt-image-2.5/sunburst` | `fal-ai/nano-banana-2` | edit variant takes `image_urls` | GPT Image: yes (`background=transparent`) | Sunburst = edit-fidelity tier; released 2026-09-08 |
| HD edit (pose, direction) | `openai/gpt-image-2.5/sunburst/edit` | `fal-ai/nano-banana-2/edit` | NB2: 10 object + 4 character + 3 style refs | NB2: **no**, use chroma `#00FF00` | NB2 Gemini id `gemini-3.1-flash-image-preview` |
| Cheap draft | `openai/gpt-image-2.5/flare` | `fal-ai/nano-banana-2` | | yes | ~50% lower latency than GPT Image 2 |

Endpoint spellings for GPT Image 2.5 were seen in a third-party commit, not fal docs. `gen_image.py` prints the command in dry-run mode; confirm with `genmedia models` before `--yes`.

## Video clips (fal, via `video_to_spritesheet.py --provider genmedia`)

| Job | Default endpoint | Alternates | First+last frame | Price | Notes |
|---|---|---|---|---|---|
| Walk / idle / attack loop | `alibaba/wan-3.0/image-to-video` | `bytedance/seedance-2.5/image-to-video`, `fal-ai/kling-video/v3/pro/image-to-video` | yes (`end_image_url`) | $0.05-0.20/s | Cheapest; up to 30 s |
| Identity-critical clip | `fal-ai/kling-video/v3/pro/image-to-video` | `bytedance/seedance-2.5/reference-to-video` (30 refs) | Kling: `@Element1` refs | $0.112/s, $0.224/s with Elements | 15 s max |
| Timecoded multi-action | `minimax/hailuo-03/image-to-video` | | yes | see `genmedia pricing` | `[0-2s] idle [2-4s] walk [4-6s] attack` prompt blocks |
| Legacy | `fal-ai/veo3.1/image-to-video` | | no | | March-2026 default, superseded |

All video models output a background; generate on flat `#00FF00` and key with `chroma_key.py`. Never rembg per frame (matte flicker).

## Pixel art (Retro Diffusion, via `retro_diffusion.py`)

| Need | Style | Size | Refs | Price | Subcommand |
|---|---|---|---|---|---|
| Pixel still, identity-locked | `rd_pro__default` (+ `painterly/fantasy/scifi/isometric/topdown/platformer`) | 12-256 | <= 9 | $0.18/img | `generate --ref` |
| 8-direction rotation | `rd_animation__8_dir_rotation` | 80x80 fixed | <= 5 | $0.25 | `rotate8` |
| 4-angle walk | `rd_animation__four_angle_walking[_idle]` | 48x48 | | $0.07 | `generate --style ... --frames` |
| Animate a start frame | `rd_advanced_animation__walking|idle|attack|jump|crouch|destroy` | 32-256, matches input | input_image required | $0.14 | `animate --action` |
| Any motion / ambient | `rd_advanced_animation__custom_action|subtle_motion` | same | | $0.25 | `animate --action custom_action --prompt` |
| Raster -> pixel art | `rd_pro__pixelate` | 16-256 | <= 9 | $0.18 | `pixelate` |
| Turnaround sheet (non-directional) | `rd_plus__character_turnaround` | 64-384 | | >= $0.025 | `generate` |
| Tiles | `rd_tile__tileset`, `rd_tile__single_tile` | 16-64 | | $0.10 | `generate` |

Free/cheap deterministic tools (`retro_diffusion.py tool <id>`): `pixel_correction`, `palette_converter --palette pal.png`, `k_centroid_downscale --field width=64 --field height=64`, `color_reducer --field color_count=16`, `rotate`, `background_remover` ($0.01). `image_edit`, `inpainting`, `outpainting` cost $0.18 and return `output_urls`, not base64 (handled).

Constraints: `input_image` must be RGB with no alpha (the script composites onto `--matte`, default `#00FF00`). Styles cap at 384 px, animations at 256. `negative` is ignored by current models. Prompts describe the subject only; never write "pixel art". Balance is charged before generation and refunded on failure. `check_cost: true` is free and is what the default dry run sends.

## PixelLab (documented, not wired)

- 8-rotations Pro: 168 px, 4 subject refs, bipedal/quadrupedal, low/high top-down or side view.
- Skeleton-driven animation and 4/8-direction walk tools.
- REST v2 at `api.pixellab.ai/v2` (subscription). The 61-tool community MCP wraps a private WebSocket API, so it is not scripted here.
- Use when RD's 80x80 rotation cap is too small and a subscription is acceptable.

## Choosing

1. Pixel art, any size <= 256: Retro Diffusion. Rotation: `rotate8`. Animation: `animate`.
2. HD/painted sprites: GPT Image 2.5 Sunburst for anchor + edits (true alpha), Nano Banana 2 when you need many typed refs.
3. Any multi-frame motion at HD: video model on chroma, then `video_to_spritesheet.py` with `align_frames.py`.
4. Deterministic palette-preserving scaling: `pixel_scale.py`, never a generative model.
