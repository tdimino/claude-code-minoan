# GPT Image Prompting Guide

## Prompt Structure

Follow this formula for best results. **First words carry highest visual weight** — lead with scene and style, not subject:

```
[Scene/Style/Intended Use] + [Subject] + [Details/Lighting] + [Camera/Composition] + [Constraints/Dimensions]
```

Specify the intended use (ad, UI mockup, infographic, editorial photo, social post) so the model picks the right polish level. The model reasons through prompts — front-load context and intent.

Example:
```
Editorial food photography for magazine feature | Hands cutting a blood orange
on a weathered butcher block | Morning kitchen light, Kodak Portra 400 | 50mm
prime, f/2.8, shallow DOF | One stray seed, a juice bead on the thumbnail
```

Not:
```
Hands cutting a blood orange | Food photography | Kitchen light | 50mm lens | Editorial quality
```

## Text Rendering (~99% accuracy on gpt-image-2)

**Always quote exact text in double quotes.** This is the single highest-leverage text-rendering technique — it engages the high-accuracy rendering engine. Even for single words.

1. **Quote exact text**: `render the text "HELLO WORLD" in bold serif`
2. **Keep text short** — under 10 words per text element
3. **Specify font style** — "monospace", "serif", "sans-serif", "handwritten", "bold condensed"
4. **Specify color** — use named colors or hex: `in phosphor green (#2dd4bf)`
5. **Specify position** — "centered at top", "bottom-left corner", "on the banner"
6. **Non-Latin scripts** — gpt-image-2 handles Hebrew, Japanese, Arabic, Cyrillic significantly better than competitors

Example:
```
A vintage book cover with the title "ΘΗΡΑ ΚΑΙ ΚΝΩΣΟΣ" in gold serif at the top,
author name "T. di Mino" in small caps at the bottom, dark navy background with
a Minoan bull-leaper illustration in the center
```

## Aspect Ratio & Dimensions

The API `size` parameter alone fails ~90% of the time for non-standard ratios. **Embed exact pixel dimensions in the prompt text** for reliable aspect-ratio adherence:

```
... Output in exactly 1774px x 887px (2:1 ratio) resolution landscape format.
```

The `inject_size_hint()` function in `openai_images.py` does this automatically for gpt-image-2 when a size preset or `WxH` is specified. For custom ratios not covered by presets, add the dimension string manually.

## Photorealism

gpt-image-2 excels at photorealistic output. Key techniques:

- **Camera metadata**: "shot on iPhone 15 Pro", "Canon EOS R5, 24-70mm f/2.8"
- **Film stocks**: "Kodak Portra 400", "Fuji Velvia 50"
- **Lighting specifics**: "golden hour", "overcast diffused", "single key light from 45 left"
- **Lens effects**: "shallow depth of field", "lens flare", "bokeh in background"
- **Environmental details**: coordinates, time of day, weather conditions
- **Believable imperfections**: describe specific details ("a stray seed, a juice bead on the thumbnail, a single breadcrumb") — describe the photograph, not the fantasy

## Complex Compositions

gpt-image-2 reasons about layout before generating — it plans, searches for references, critiques its own output, and iterates before rendering. Prompts can carry far more context than previous image models.

- Describe **spatial relationships** explicitly: "the cat sits on the left chair, the dog on the right"
- List **elements in order of importance** — the model allocates attention proportionally
- For **infographics/diagrams**: describe the structure first, content second
- For **UI mockups**: specify layout grid, then populate elements
- For **complex multi-element scenes**: use `--thinking` orchestrator in `converse_image.py` for significantly better results

## Multi-Image Consistency

Request up to 8 images with `--n 8`. Consistency tips:

- **Describe the character once** with specific features, then reference by name
- **Specify "consistent style across all images"** in the prompt
- **Manga/storyboard**: describe the full sequence, including panel transitions
- **Product photography**: describe the product once, vary angles/backgrounds
- **Character sheets**: one prompt, one sheet, multiple poses/contexts — gpt-image-2 can maintain identity across a full sheet without seeds, LoRAs, or ControlNet

## Editing Prompts

For `edit_image.py` and mask-based editing:

- **Be specific about what to change AND what to preserve**: "Change the shirt color to red. Keep the face, pose, and background identical."
- **Use action verbs**: Add, Remove, Replace, Change, Make, Convert
- **Positional language**: "in the upper right", "behind the subject", "along the horizon"
- **Without mask**: the model edits the whole image. With mask: only the transparent region.

## Quality/Cost Ladder

| Phase | Quality | Cost | Use Case |
|-------|---------|------|----------|
| Ideation | `low` | ~$0.006 | Quick drafts, exploring concepts |
| Iteration | `medium` | ~$0.05 | Refining composition, checking layout |
| Final | `high` | ~$0.21 | Production assets, print-ready |

Start low, graduate to high. Low-quality is surprisingly good for drafts.

## Format Optimization

- **jpeg** with `--compression 85`: 3-4x faster response than png. Use for iteration.
- **png**: Lossless. Use for final assets or when you need transparency (gpt-image-1.5 only).
- **webp**: Good compression with quality. Use for web delivery.

## Style Keywords

gpt-image-2 responds well to:
- **Photography**: macro, telephoto, wide-angle, aerial, underwater, infrared
- **Art styles**: oil painting, watercolor, charcoal, pencil sketch, digital illustration
- **Genres**: pixel art, manga, anime, film noir, vaporwave, Art Nouveau, Art Deco
- **Moods**: dramatic, ethereal, gritty, serene, melancholic, vibrant

## Content Policy

- `--moderation low` for less restrictive filtering
- Avoid explicit violence, sexual content, real person likeness without consent
- "Cinematic", "professional", "dramatic" are safe alternatives to "military", "war", "combat"
- Content policy is stricter than Nano Banana Pro — for dark/artistic themes, consider using NB Pro instead

## Known Limitations

- **Reference-image editing**: gpt-image-2 often produces yellow tint and loses prompt adherence when editing from reference images (no mask). Generate fresh for design-final work. Use `--fast` (gpt-image-1.5) for better edit results.
- **Custom aspect ratios**: API `size` param alone unreliable — dimensions must also appear in prompt text (handled automatically by `inject_size_hint()`).
- **Complex multi-element scenes**: Use the Thinking orchestrator (`--thinking` in `converse_image.py`) for compositions with many elements, precise layouts, or multiple text regions.
