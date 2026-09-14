# Frame Alignment and Jitter Control

Why sprites "wobble": each generated frame has its own crop, scale, halo and shadow, so the alpha bounding box moves even when the character does not. Aligning on the bbox propagates that noise into the sheet. Align on the **feet line** and **character height** instead.

## Feet-line algorithm (`align_frames.py`)

1. Solid mask: alpha > 127 (`--alpha-threshold`). Anti-aliased halos and soft shadows fall below it.
2. Bbox of the solid mask gives `bbox_w`.
3. **Feet line** = lowest row with at least 5% of `bbox_w` solid pixels (`--min-row-fraction`). A one-pixel drip or a thin hard shadow does not count; a foot does.
4. **Head line** = highest such row. `height = feet - head + 1`.
5. Reference frame = the frame with the median height (or `--ref-frame N`).
6. Per frame: `scale = ref_height / height` (disable with `--no-scale` for pixel art that must stay exact), resize, then **re-measure** the feet line on the resized frame and use `offset_y = target_feet - feet_resized` (re-measuring absorbs the rounding that `feet * scale` would leave), horizontal anchor on the reference bbox centre (`--anchor-x ref|center|none`).
7. Canvas: `--cell WxH` when given; otherwise the reference frame's size, grown to the largest resized frame so nothing is clipped.
7. Canvas: source size preserved, or `--cell WxH` with the feet placed 5% above the bottom (`--feet-at` overrides).

Output `alignment.json` reports feet-line variance and range after alignment; a good sheet has variance < 1 px^2.

## Canvas contract (LayrKits rule)

Never trim frames to their bbox before packing. Pack every frame in the **same cell** with the **same origin**, so the engine's sprite origin stays fixed and the animation reads as motion of limbs, not of the whole body. `stitch_spritesheet.py` pastes frames at cell origin and records `anchor.feet_y` and `anchor.pivot` in manifest v2; it does not centre or rescale when a manifest is requested.

## Dedup and loops

- `--dedup N`: consecutive frames whose dHash distance is below N are dropped (video models at 24 fps yield many near-identical frames; 12 fps extraction plus `--dedup 6` gives 6-10 distinct walk frames).
- `--loop-check`: reports dHash distance between the first and last kept frame. Distance <= 4 means the last frame duplicates the first: drop it. Larger distance: generate with a first+last-frame model (`--end-frame anchor.png` in `video_to_spritesheet.py`) so the clip returns to the start pose.

## Matte consistency

`perimeter_cv` in the summary is the coefficient of variation of the alpha-edge perimeter across frames, and `solid_flip_max` the largest fraction of solid pixels that flip between consecutive frames. Translation barely moves the perimeter; holes, halo width changes and ragged edges do. A `perimeter_cv` above 0.15 means the matte itself is flickering, which is what per-frame `rembg` does on video. Fix at the source: render on flat `#00FF00`, key once with `chroma_key.py --despill`, then align. Reserve `rembg` for single stills.

## Checklist before shipping a sheet

- feet-line variance < 1 px^2 and height range within 2 px
- every cell the same size, origin at (0,0), pivot recorded
- frame count matches the target (walk 6-8, idle 4-6, attack 5-8)
- first/last frame either identical (dropped) or an explicit return-to-pose
- alpha edges stable (`perimeter_cv` < 0.15)
- pixel art: `--no-scale`, nearest resampling only, palette count unchanged (`pixel_scale.py` reports it)

Sources: hey.paris "Leo sprite alignment" (2026-05), LayrKits/Sprite-Pipeline fixed-cell packing, aldegad/sprite-gen curation stage, aispritesheet.com wobble notes.
