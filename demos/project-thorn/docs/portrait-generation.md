# Portrait Generation

Character portraits for Project Thorn are generated with [Nano Banana Pro](https://github.com/tdimino/claude-code-minoan/tree/main/skills/design-media/nano-banana-pro) (Google Gemini 3 Pro Image) using style-locked reference images and carefully structured prompts.

## Style Anchor

Every portrait is style-locked to the original Ora Bothan portrait (`bothan-ora_image_0_0.jpg`). This establishes the visual language: cinematic digital painting with visible painterly brushwork, warm amber rim lighting, atmospheric depth-of-field backgrounds, and high contrast. The Ora portrait and the approved v2 Jiff Gorda portrait are passed as reference images to every subsequent generation.

## Prompt Structure

The prompt formula that produces consistent results. All portraits share the same **green-tinted color temperature** to match Ora's cantina ambient, but backgrounds vary in scene content (different interiors, different blurred elements).

```
Cinematic digital painting portrait of [CHARACTER DESCRIPTION],
in the exact same painterly art style as the Bothan alien portrait reference.
[PHYSICAL FEATURES]. [CLOTHING]. Expression: [EMOTION/ATTITUDE].
[CAMERA ANGLE]. NOT a celebrity, NOT [SPECIFIC EXCLUSIONS].
Original fictional character.

Head and shoulders composition, square 1:1 framing.
Background: deep green-tinted [SCENE-SPECIFIC INTERIOR], [BLURRED ELEMENTS].
Painterly brush strokes with visible texture, warm amber highlights on skin,
cool green environment tones, dramatic rim lighting from behind-left
creating edge separation. High contrast with deep blacks.
Professional digital art matching the Bothan portrait reference exactly
in style, color palette, and brushwork quality. No photorealism,
no smooth digital rendering.
```

### Key Techniques

- **Negative celebrity direction**: Explicitly state "NOT a celebrity, NOT Harrison Ford" (or whoever the model gravitates toward). Without this, "smuggler" + "dark hair" collapses to Han Solo.
- **Physical features over archetypes**: "Short-cropped dark brown hair, sharp angular jawline, piercing blue eyes" beats "smuggler" every time. The archetype word carries too much visual baggage.
- **Camera angle variety**: Vary the gaze direction across characters — three-quarter, direct stare, profile, over-shoulder. Prevents the portraits from feeling like reskins.
- **Fewer references**: 2-3 reference images outperform 5+. Too many references confuse the style lock, especially if aspect ratios or art styles conflict.
- **Unified green temperature**: All backgrounds share the same olive/sage green color temperature (#233c25 average). Scene content varies (cantina, nightclub, intel bureau) but the green ambient is constant.

## Selected Portraits

### Jiff Gorda (`gen/jiff-gorda-final_0.jpg`)

```
Cinematic digital painting portrait of a young human male, early 20s,
in the exact same painterly art style as the Bothan alien portrait
reference. Short-cropped dark brown hair, sharp angular jawline,
piercing blue eyes, lean athletic build. Wearing a dark sleeveless
vest. Expression: wary, scanning the room. Three-quarter view looking
over his right shoulder toward the viewer. NOT a celebrity, NOT
Harrison Ford. Original fictional character. Head and shoulders
composition, square 1:1 framing. Background: deep green-tinted
atmospheric cantina interior, blurred alien patrons at a bar, hazy
smoke catching green ambient light, crude stone archways receding
into shadow. Painterly brush strokes with visible texture, warm amber
highlights on skin, cool green environment tones, dramatic rim
lighting from behind-left creating edge separation. High contrast
with deep blacks. Professional digital art matching the Bothan
portrait reference exactly in style, color palette, and brushwork
quality. No photorealism, no smooth digital rendering.
```

References: `bothan-ora_image_0_0.jpg` (style) + `gen/jiff-gorda-v2_0.jpg` (character).

### Fenri (`gen/fenri-final_0.jpg`)

```
Cinematic digital painting portrait of a human male, late 20s,
in the exact same painterly art style as the Bothan alien portrait
reference. Long braided dark hair, sharp aristocratic features,
amber-brown eyes, tall lean build. Wearing a crimson brocade jacket
with high collar. Expression: confident half-smile, direct knowing
stare. NOT a celebrity. Original fictional character. Head and
shoulders composition, square 1:1 framing. Background: deep
green-tinted upscale nightclub interior, blurred velvet booths and
chrome fixtures, warm green-gold ambient light filtering through
haze, silhouettes of well-dressed patrons in distance. Painterly
brush strokes with visible texture, warm amber highlights on skin,
cool green environment tones, dramatic rim lighting from behind-left
creating edge separation. High contrast with deep blacks. Professional
digital art matching the Bothan portrait reference exactly in style,
color palette, and brushwork quality. No photorealism, no smooth
digital rendering.
```

References: `bothan-ora_image_0_0.jpg` (style) + `gen/fenri-nightclub-v2_0.jpg` (character).

### Agent Cotla (`gen/cotla-final_0.jpg`)

```
Cinematic digital painting portrait of a human male, early 30s,
in the exact same painterly art style as the Bothan alien portrait
reference. Close-cropped black hair with slight wave, medium-brown
skin, dark watchful eyes, clean-shaven, sharp intelligent features.
Wearing a dark charcoal high-collar intelligence tunic. Expression:
quiet focus, absorbed in thought. Side view, chin slightly raised.
NOT a celebrity, NOT Oscar Isaac. Original fictional character. Head
and shoulders composition, square 1:1 framing. Background: deep
green-tinted intelligence bureau interior, blurred holographic data
screens casting green-blue light, rows of terminals receding into
shadow, cool green ambient glow on durasteel walls. Painterly brush
strokes with visible texture, warm amber highlights on skin, cool
green environment tones, dramatic rim lighting from behind-left
creating edge separation. High contrast with deep blacks. Professional
digital art matching the Bothan portrait reference exactly in style,
color palette, and brushwork quality. No photorealism, no smooth
digital rendering.
```

References: `bothan-ora_image_0_0.jpg` (style) + `gen/cotla-v3-male_0.jpg` (character).

### Vorian Ducal (`gen/vorian-ducal-final_0.jpg`)

Same face as Jiff Gorda, but in Imperial uniform on a Star Destroyer bridge.

```
Cinematic digital painting portrait of a young human male, early 20s,
in the exact same painterly art style as the Bothan alien portrait
reference. Short-cropped dark brown hair, sharp angular jawline,
piercing blue eyes, lean athletic build. Wearing a crisp grey Imperial
officer's uniform with rank insignia on chest, high collar. Expression:
cold composure, dutiful, a mask hiding something deeper. Direct stare
at viewer. NOT a celebrity, NOT Harrison Ford. Original fictional
character. Head and shoulders composition, square 1:1 framing.
Background: deep green-tinted Star Destroyer bridge interior, blurred
viewport showing star field, rows of green-lit control consoles
receding into shadow, cool green ambient glow on durasteel walls.
Painterly brush strokes with visible texture, warm amber highlights
on skin, cool green environment tones, dramatic rim lighting from
behind-left creating edge separation. High contrast with deep blacks.
Professional digital art matching the Bothan portrait reference
exactly in style, color palette, and brushwork quality. No
photorealism, no smooth digital rendering.
```

References: `bothan-ora_image_0_0.jpg` (style) + `gen/jiff-gorda-v2_0.jpg` (character — same person).

### Echo Cell (`gen/echo-cell-final_0.jpg`)

Rebel cell org chart — red holographic on dark datapad screen. Not a character portrait.

```
A holographic organizational chart displayed on a dark datapad screen
interface. The chart is rendered entirely in crimson and scarlet red
holographic lines and nodes against a black screen. Network diagram
showing 6 connected circular nodes arranged in a covert cell structure.
Each circular node contains a small wireframe portrait of a different
species: a Mon Calamari with large bulbous eyes, a human male, a
Rodian with a ridged snout, a Wookiee with shaggy fur, a Twi'lek
with head-tails, and a human female. Thin red glowing connection
lines between nodes. The word ECHO displayed at the top in red
monospace text. Each node has a short alphanumeric designation code
beneath it. Scan lines and slight static interference across the
display. Flat screen UI — no physical environment visible, just
the dark interface with the red holographic overlay. Thin red border
frame around the display. Square 1:1 framing. Digital art with
painterly texture. High contrast — deep blacks with vivid red glow.
No photorealism.
```

References: `bothan-ora_image_0_0.jpg` (style only).

### Project Thorn (`gen/project-thorn-final_0.jpg`)

Imperial operations chart — green holographic on dark datapad screen. Not a character portrait.

```
A holographic operations briefing chart displayed on a dark datapad
screen interface. The chart is rendered in olive green and sage green
holographic lines and text against a black screen. Hierarchical
flowchart showing operational phases flowing downward: RECRUITMENT
at top, then COVER CONSTRUCTION, then INFILTRATION, then ACTIVATION.
Each phase is a horizontal bar connected by vertical green glowing
lines. The words PROJECT THORN are displayed at the top in green
monospace text. Small Imperial insignia watermark in green. Scan
lines and slight static interference across the display. Flat screen
UI — no physical environment visible, just the dark interface with
the green holographic overlay. Thin green border frame around the
display. Square 1:1 framing. Digital art with painterly texture.
High contrast — deep blacks with muted olive-sage green glow matching
hex #233c25 color temperature. No photorealism.
```

References: `bothan-ora_image_0_0.jpg` (style only).

### Generation Command (all characters)

```bash
python3 ~/.claude/skills/nano-banana-pro/scripts/generate_with_references.py \
  "<prompt>" \
  bothan-ora_image_0_0.jpg \
  gen/<character-anchor>.jpg \
  --aspect-ratio 1:1 \
  --output ./gen \
  --filename <character>-green-bg
```

### SWG Source Material

The Jiff Gorda character design is derived from 2004 Star Wars Galaxies screenshots on the Starsider server. Three screenshots were used as initial character references during the v2 iteration that established the face.

## Iteration History

| Version | Issue | Fix |
|---------|-------|-----|
| v1 | Widescreen aspect, looked like Han Solo, too old | Reduced refs from 5→3, added negative celebrity direction, specified age and facial features explicitly |
| v2 (approved) | Green cantina baseline | Correct face, correct age, correct style lock |
| Locale set | Needed background variety and angle variation | Per-locale background descriptions + camera angle changes (profile, over-shoulder, low angle, upward gaze, direct stare) |

## Generating New Portraits

To add a new character to the set:

1. Write the character's physical description — face, hair, eyes, build, clothing
2. Pick 1-2 reference images: always include `bothan-ora_image_0_0.jpg` as style anchor, plus an approved portrait of the same character if one exists
3. Follow the prompt formula above
4. Add negative celebrity exclusions for any archetype the model might collapse to
5. Generate at `--aspect-ratio 1:1` with default resolution (2K)
6. If the face is wrong, iterate on physical features before trying locale variations

### Background Color Reference

All portraits use the same background: `deep green-tinted atmospheric interior`. The Ora portrait's background averages `#233c25` (R=35, G=61, B=37) — a muted olive/sage green, warm-leaning, not cyan or neon. Green channel sits ~25 points above red and blue.
