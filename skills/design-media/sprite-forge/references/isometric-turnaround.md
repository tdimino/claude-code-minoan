# Isometric 8-Way Turnaround

Based on chongdashu's FFT-style pipeline (github.com/chongdashu/vibe-isometric-sprites, Mar 2026). 1.2M views, 8,672 bookmarks on X.

## The 7-Step Pipeline

1. **Reference → Full-body asset** — GPT Image 1.5 edit with identity anchor prompt
2. **Full-body → Isometric anchor** — ¾ isometric idle pose, facing down-right
3. **Transparency handling** — Chroma key #00FF00 for Nano Banana; true alpha for GPT Image 1.5
4. **Generate 4 cardinal directions** (N/E/S/W) as 2×2 sheet from anchor
5. **Generate 4 diagonals** (NE/NW/SE/SW) from anchor + cardinal sheet
6. **Walk cycle via video** — Veo 3.1 generates video, extract frames with ffmpeg
7. **Normalize and export** — fix scale drift, stitch into final 8-direction sheet

## Core Insight

Never generate all 8 directions at once. Results are inconsistent. Two-phase approach: cardinals first, then diagonals referencing both the anchor and the cardinal sheet.

## Prompt Templates

### Full-Body Asset
```
Use image 1 as the identity anchor. Create a full-body 2D fantasy RPG game sprite-style
character cutout of {character_desc}. Show the whole body from head to boots in one neutral
standing pose, centered, readable silhouette, arms and legs fully visible, feet not cropped.
Preserve the character design, palette family, and clothing details, simplified into a clean
game-ready character asset. {bg_instruction}. No text, no extra characters, no cropped limbs.
```

### Isometric Anchor
```
Use image 1 as identity and costume reference. Transform into a sprite-ready classic isometric
tactical JRPG unit sprite inspired by late-1990s strategy RPGs. Change pose into a clean
three-quarter isometric standing idle pose, facing down-right, with compact game-sprite
proportions, simplified readable forms, crisp silhouette. Show full body from head to boots.
{bg_instruction}. No environment, no text, no frame.
```

### Cardinal Sheet (2×2)
```
Use image 1 as identity, costume, rendering-style, and scale anchor. Create a single 2x2
character spritesheet in four cardinal directions with maximum consistency. Layout:
top-left=North (back), top-right=East (right), bottom-left=South (front),
bottom-right=West (left). Each panel: full-body standing idle, isometric style.
{bg_instruction}. No text, no labels, no borders.
```

### Diagonal Sheet (2×2)
```
Image 1 = cardinal direction sheet for consistency. Image 2 = isometric identity anchor.
Create a 2x2 spritesheet of four diagonal directions. Layout: top-left=NW, top-right=NE,
bottom-left=SW, bottom-right=SE. Match scale, style, and rendering of the cardinal sheet.
{bg_instruction}. No text, no labels.
```

## Model Selection

| Step | Best Model | Why |
|------|-----------|-----|
| Full-body + Anchor | GPT Image 1.5 | Best identity preservation across edits |
| Cardinal/Diagonal sheets | Nano Banana 2 | Good isometric style, cheaper |
| Walk cycles | Veo 3.1 (video) | Image models have no temporal coherence |

## Known Behaviors

- Nano Banana 2 **repeatedly ignores "exactly four poses"** and returns 8-pose sheets. Curate the best subset.
- Cardinals and diagonals have **real scale drift** — diagonals 16-30px shorter. Fix with post-processing normalization (shared visible height + shared bottom anchor).
- GPT Image 1.5 is the only model that reliably produces true transparent backgrounds.

## Background Handling

- **Nano Banana 2/Pro**: Use exact flat `#00FF00` chroma green. No gradients, no shadows on bg.
- **GPT Image 1.5**: Use `--background transparent` directly.
- **Never use magenta** (#FF00FF) — contaminates warm red/purple costume elements.

## Post-Processing

1. Split 2×2 sheets into individual direction frames with `split_spritesheet.py --cols 2 --rows 2`
2. Normalize all 8 frames to shared visible height and bottom anchor
3. Assemble in rotation order: N → NE → E → SE → S → SW → W → NW
4. Stitch into final sprite sheet with `stitch_spritesheet.py`

## Source

- Public repo: github.com/chongdashu/vibe-isometric-sprites
- Video: youtube.com/watch?v=03Xsy18Hsdo
- Prompts file: `prompts/2026-03-27-005038-tictac-adventurer-8way-turntable-prompts.md`
