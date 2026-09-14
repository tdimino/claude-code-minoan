# 8-Direction Turnaround

Two routes, one script: `scripts/turnaround.py`.

## Pixel route (default for pixel art)

`rd_animation__8_dir_rotation` returns all eight directions from one prompt plus up to five reference images, 80x80, $0.25, identity-locked by the refs. It replaces the March-2026 practice of coaxing eight views out of a general image model.

```bash
python3 scripts/turnaround.py --mode pixel --prompt "astromech droid, blue and white dome" --ref droid.png --out ./turn
python3 scripts/turnaround.py --mode pixel ... --yes      # after the cost check
```

Output: `turn/turnaround.png` + `turnaround.json` (atlas v2, `directions: [S,SE,E,NE,N,NW,W,SW]`). If RD's sheet layout differs from 8 columns, pass `--rd-cols`. Larger pixel rotations (168 px) exist on PixelLab's 8-rotations Pro; see `provider-matrix.md`.

## HD route (painted / high-res sprites)

Cardinals first, then diagonals: the two-phase rule from chongdashu's pipeline still holds because a single "all eight" edit drifts. What changed is the model: GPT Image 2.5 Sunburst edits keep identity across eight separate edits and return true alpha, so each direction is one clean edit instead of a 2x2 sheet to split and curate.

1. Anchor: full body, front view, neutral pose, feet visible (`gen_image.py --job anchor --transparent`), or supply `--anchor`.
2. Cardinals S/E/N/W: one edit each, prompt keeps "same proportions, same height, feet on the same ground line".
3. Diagonals SE/NE/NW/SW: one edit each with three refs (anchor + the two neighbouring cardinals), "exactly between those two views".
4. `chroma_key.py` if `--chroma` (Nano Banana 2 route), `align_frames.py --anchor-x center` to remove the 16-30 px scale drift that diagonals still show, then `stitch_spritesheet.py --atlas v2 --directions 8`.

```bash
python3 scripts/turnaround.py --mode hd --anchor anchor.png --desc "young adventurer, red scarf" --out ./turn --yes
python3 scripts/turnaround.py --mode hd --anchor anchor.png --model fal-ai/nano-banana-2/edit --chroma --out ./turn --yes
```

## Prompt fragments that matter

- Identity: "Use image 1 as the identity, costume, rendering-style and scale anchor."
- Scale lock: "same proportions and same height as image 1, feet on the same ground line, centered."
- Diagonal derivation: "Image 2 shows the character facing right; image 3 facing the viewer. Draw it facing down-right, exactly between those two views."
- Background: `Transparent background` (GPT Image) or the exact `#00FF00` chroma sentence (`chroma-key-transparency.md`).
- Never: "isometric" unless you want the tilted 3/4 camera; "pixel art" in RD prompts (styling comes from the style id).

## Known behaviours

- Diagonals come out shorter than cardinals; do not skip the align step.
- Nano Banana 2 ignores "exactly one character" now and then; regenerate that direction with a new seed rather than cropping.
- Video walk cycles per direction: generate one clip per direction with `video_to_spritesheet.py --provider genmedia --start-frame turn/dirs/E.png --end-frame ...`, then stitch with `--directions 8 --state walk:12:loop`.

Source lineage: github.com/chongdashu/vibe-isometric-sprites (Mar 2026) for the cardinal-then-diagonal rule; Retro Diffusion llms.txt (2026-09) for the rotation style.
