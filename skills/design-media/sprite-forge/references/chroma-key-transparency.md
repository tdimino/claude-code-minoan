# Chroma Key & Model Transparency

## Model Capabilities

| Model | True Alpha | Recommended Approach |
|-------|-----------|---------------------|
| GPT Image 1.5 | Yes | `--background transparent` |
| Nano Banana 2 | No | Chroma key #00FF00 |
| Nano Banana Pro | No | Chroma key #00FF00 |

## The Problem

Nano Banana 2 and Pro produce faux-transparent dark backdrops when asked for transparency. The output looks transparent in the API response but contains near-black or dark-gray pixels instead of true alpha.

## The Solution: Chroma Key Green

Request exact flat `#00FF00` background in prompts, then remove it deterministically with `chroma_key.py`.

### Prompt Pattern
```
Use an exact flat chroma green background #00FF00 across the entire image,
with no gradient, no shadows on background, no texture, no green spill on subject.
```

### Removal
```bash
python3 scripts/chroma_key.py --input sprite.png --output sprite_alpha.png --despill
```

## Why NOT Magenta

`#FF00FF` (magenta) seems like a safe alternative, but it contaminates warm red/purple costume elements at edges. Red scarves, brown leather, purple cloaks all bleed into magenta during chroma keying. Green is safer because game characters rarely contain pure #00FF00.

## chroma_key.py Parameters

| Flag | Default | Purpose |
|------|---------|---------|
| `--color` | 00FF00 | Key color hex |
| `--tolerance` | 30 | Euclidean RGB distance threshold |
| `--despill` | off | Reduce green channel bias on edge pixels |
| `--feather` | 1 | Gaussian blur radius on alpha channel |

### Tolerance Tuning
- **20-30**: Tight — preserves green costume elements but may leave green fringe
- **30-50**: Normal — good for most sprites
- **50+**: Aggressive — may eat into green-adjacent colors

### Edge Cases
- Green in character costumes: use narrower tolerance (20) or manual mask
- Dark green shadows on bg: increase tolerance to 50
- Alternative: use `rembg` for photorealistic images (ML-based, handles any background)

## rembg Alternative

For photorealistic images or complex backgrounds where chroma key isn't practical:

```bash
rembg i input.png output.png
# or via pip: uv pip install rembg
```

rembg uses U2-Net for ML-based background removal. Slower but handles arbitrary backgrounds.
