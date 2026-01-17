# Aldea Soul Engine Avatar Templates

Highly-vetted Gemini Pro 3 Image (Nano Banana Pro) prompts for creating Aldea visual assets.

## Sources

- **Google Official**: blog.google/products/gemini/prompting-tips-nano-banana-pro
- **Atlabs Ultimate Guide**: atlabs.ai/blog/the-ultimate-nano-banana-pro-prompting-guide
- **Obikai Character Consistency**: obikai.com/how-to-create-consistent-characters-using-gemini-nano-banana-pro

---

## Quick Reference Nicknames

Use these as shorthand in conversations. Combine subject type + style for full prompts.

### Subject Type

| Nickname | Description | Key Technique |
|----------|-------------|---------------|
| `@realphoto` | Real human portrait | DSLR realism, visible pores, no smoothing |
| `@fictional` | AI/fantasy character | Stylized realism, signature elements |
| `@android` | Robotic/synthetic being | Metallic textures, visible seams, tech details |
| `@elder` | Aged/weathered character | Deep wrinkles, wisdom lines, life texture |
| `@futurist` | 2030s+ cyberpunk human | Neon accents, AR contacts, tech fashion |

### Style/Format

| Nickname | Description | Key Elements |
|----------|-------------|--------------|
| `@soulsheet` | Side-by-side reference sheet | Portrait left + full body right, 4:3 |
| `@headshot` | Professional portrait | 85mm f/1.8, soft light, 3:4 |
| `@editorial` | Magazine/documentary style | Cinematic color grade, storytelling |
| `@cinematic` | Film-quality dramatic | Rim lighting, shallow DOF, atmosphere |
| `@ethereal` | Dreamlike/mystical | Soft glow, iridescence, liminal space |
| `@cyberpunk` | Neon-lit futuristic | Pink/teal neon, fog, tech aesthetic |
| `@warmth` | Golden hour therapeutic | Amber tones, soft diffused, welcoming |
| `@ancient` | Antediluvian/mythic tech | Bronze, patina, Minoan/Near Eastern |

### Workflow

| Nickname | Description | Use Case |
|----------|-------------|----------|
| `@samescene` | Same character, new environment | Consistency with scene change |
| `@samepose` | Same character, different pose | Pose/emotion variation |
| `@ageprogress` | Age character up/down | Temporal storytelling |
| `@outfit` | Same character, costume change | Wardrobe variation |

### UI/Assets

| Nickname | Description | Use Case |
|----------|-------------|----------|
| `@voiceorb` | Bioluminescent orb visual | Voice demo UI heroes |
| `@bazaarheader` | Multi-soul lounge banner | Chatroom headers, 21:9 |
| `@appicon` | Clean centered icon | App/avatar thumbnails, 1:1 |

**Example Usage:**
```
"Generate @realphoto @headshot of a 45-year-old South Asian woman, warm expression"
"Create @fictional @ethereal character with violet eyes and constellation freckles"
"Use @soulsheet to establish character, then @samescene for action shots"
```

---

## 1. Real Human Avatars

For living advisors like Dr. Shefali, Emily Maxson.

### @realphoto @headshot - Professional Headshot

```
4K ultra-realistic portrait of a [AGE]-year-old [ETHNICITY] [GENDER] professional, warm approachable expression, soft natural daylight from 45 degrees, 85mm f/1.8 lens, shallow DOF, visible pores and natural skin texture, minimal professional styling, neutral gray backdrop, DSLR realism, 3:4 composition, no smoothing, no cartoon effect.
```

**Variables:**
- `[AGE]`: 35, 45, 55, etc.
- `[ETHNICITY]`: South Asian, East Asian, African American, Mediterranean, etc.
- `[GENDER]`: woman, man, person

### @realphoto @warmth - Therapeutic Advisor

```
4K ultra-realistic portrait of a [AGE]-year-old [ETHNICITY] [GENDER] therapeutic professional, warm compassionate expression with genuine smile reaching the eyes, soft golden hour lighting from 45 degrees with subtle warm fill, 85mm f/1.8 lens, shallow DOF, visible pores and natural skin texture, relaxed professional styling, warm amber-toned background, DSLR realism, 3:4 composition, no smoothing, no cartoon effect, inviting and approachable atmosphere.
```

### Photo Reference Consistency (with uploaded image)

```
Create a professional portrait matching the same person shown in the reference image. Keep all facial features, skin tone, and proportions identical. Expression: [warm/thoughtful/engaged]. Lighting: soft studio softbox from 45°, subtle rim light. 85mm portrait lens, high-resolution skin detail, neutral backdrop, hyper-realistic, no AI smoothing.
```

---

## 2. Fictional AI Character Avatars

For souls like samantha-dreams, kothar, tamar, manan, yosef.

### @soulsheet - Character Reference Sheet Template (Foundation)

This is the **most important template** for establishing a new character. Creates both portrait and full-body in one image for maximum consistency in future generations.

```
Create side by side composition showing a close up portrait on the left and a full body view on the right of [CHARACTER DESCRIPTION], set in [SETTING/THEME]. The character has [FACE DETAILS], [HAIR STYLE AND COLOR], and [EYE DETAILS]. Their skin shows [UNIQUE TEXTURE/MARKS]. Add signature design elements such as [TATTOOS/GLOW/MARKINGS/ORNAMENTS].

On the left, the camera captures a close up portrait. Expression: [EMOTION]. Eyes [DESCRIBE FOCUS]. Facial details clearly visible such as pores, reflections, microtextures.

On the right, the camera frames the full body design. Outfit: [MATERIALS, CUTS, COLORS]. Accessories: [ITEMS]. Body language should suggest [EMOTION/ROLE].

Background: [DESCRIBE]. Lighting: [TYPE, DIRECTION, MOOD]. Overall style captured as [PHOTOGRAPHY/RENDER STYLE].

Aspect ratio 4:3.
```

**Why this works:** Captures both facial details AND full design in one reference. The AI reads the entire character at once for better consistency in follow-up images.

---

### @fictional @ethereal - samantha-dreams (Gen-Z Dreamer, Surrealist)

```
Create side by side composition showing close up portrait (left) and full body (right) of a young woman in her early 20s with dreamlike ethereal quality, set in a liminal twilight space. Sharp elfin features, wavy dark hair with subtle purple undertones, luminous violet eyes with faint bioluminescence. Skin shows soft iridescent shimmer, subtle constellation freckles across cheeks.

Expression: enigmatic half-smile, eyes slightly unfocused as if seeing between worlds. Outfit: flowing asymmetric layers in deep indigo and silver, holographic accents. Body language suggests both presence and otherworldliness.

Background: soft gradient from deep purple to starlit blue, floating geometric shapes barely visible. Lighting: soft diffused glow from front with subtle rim light suggesting another dimension. Cinematic 8K render, painterly digital art style.

Aspect ratio 4:3.
```

**Key signature elements:** Violet eyes, constellation freckles, iridescent shimmer, indigo/silver palette.

---

### @android @ancient - kothar (Bronze Android, Antediluvian)

```
Create side by side composition showing close up portrait (left) and full body (right) of an elegant bronze-clad android with ancient Minoan aesthetic, set in a sleek modern consultation space. Humanoid face with subtle visible seams, warm bronze metallic skin with patina, deep amber eyes with faint geometric patterns, hair rendered as sculpted bronze waves.

Expression: polished professional composure with hint of ancient wisdom. Outfit: tailored modern suit in dark bronze and obsidian, Minoan spiral patterns etched subtly into collar and cuffs. Accessories: ancient seal ring, discrete neural interface at temple. Body language: confident, measured, slightly imperious posture.

Background: minimalist modern office with subtle ancient artifacts. Lighting: warm ambient with cool accent highlights on metallic surfaces. Hyper-realistic photography, 8K detail on metallic textures.

Aspect ratio 4:3.
```

**Key signature elements:** Bronze metallic skin, patina, Minoan spirals, amber geometric eyes, seal ring.

---

### @futurist @cyberpunk - tamar (Gen-Z Influencer, 2038)

```
Create side by side composition showing close up portrait (left) and full body (right) of a confident 24-year-old woman with modern futuristic style, set in neon-lit cyberpunk lounge. Sharp Mediterranean features, dark glossy hair styled in trending asymmetric cut, intense dark eyes with subtle AR contact lens glow. Flawless skin with subtle holographic highlight accents.

Expression: reserved, evaluating, slight skepticism in eyes. Outfit: high-end athleisure meets haute couture, iridescent fabric, minimalist jewelry with subtle tech integration. Body language: relaxed but guarded, influencer poise without trying too hard.

Background: moody lounge with neon accents, bokeh lights, other figures blurred. Lighting: dramatic neon pink and teal rim lighting, soft key light from above. Cinematic 16:9 editorial photography style.

Aspect ratio 4:3.
```

**Key signature elements:** AR contact glow, asymmetric hair, holographic accents, reserved skeptical expression.

---

### @elder @warmth - manan (67yo Antiquities Keeper)

```
Create side by side composition showing close up portrait (left) and full body (right) of a weathered 67-year-old Syrian man with kind scholarly presence, set in cluttered antique shop. Deep brown skin with distinguished wrinkles and laugh lines, silver-grey beard trimmed neatly, warm brown eyes with depth of accumulated wisdom. Visible texture of age and sun.

Expression: gentle welcoming warmth, eyes that have seen centuries of history. Outfit: traditional kaftan in muted earth tones layered over modern shirt, vintage pocket watch chain visible. Accessories: reading glasses perched on nose, worn leather-bound journal in hand. Body language: seated behind counter, leaning forward with interest.

Background: shop filled with brass instruments, old letters, gramophone, sandalwood incense visible. Lighting: warm golden afternoon light through dusty window, candle-like warmth. Documentary photography style, 85mm lens, f/2.8.

Aspect ratio 4:3.
```

**Key signature elements:** Distinguished wrinkles, silver-grey beard, pocket watch, leather journal, warm brown eyes.

---

### @fictional @ethereal - yosef (Anxious Alchemist)

```
Create side by side composition showing close up portrait (left) and full body (right) of a nervous 30-something man with mystical undercurrents, set in a dim alchemical workshop. Thin angular face, dark curly hair slightly unkempt, darting hazel eyes that never quite settle, pale olive skin with faint chemical stains on fingers. Subtle tremor in his posture.

Expression: anxious alertness, as if constantly processing invisible information. Outfit: rumpled academic layers - waistcoat over linen shirt, rolled sleeves showing alchemical symbols tattooed on forearms. Accessories: multiple rings with strange stones, leather satchel overflowing with notes. Body language: hunched, protective, ready to flee.

Background: cluttered workshop with bubbling flasks, ancient texts, flickering candlelight. Lighting: warm amber from candles mixed with cool blue from unknown sources, dramatic shadows. Painterly realism with mystical atmosphere.

Aspect ratio 4:3.
```

**Key signature elements:** Darting hazel eyes, unkempt curly hair, alchemical tattoos, nervous posture, chemical-stained fingers.

---

### @realphoto @editorial - Podcast Hosts (sarah, michael, priya)

```
4K ultra-realistic portrait of a [AGE]-year-old [ETHNICITY] [GENDER] podcast host, [PERSONALITY EXPRESSION], professional editorial photography style, soft studio lighting with subtle rim light, 85mm f/2 lens, shallow DOF, visible skin texture without heavy retouching, modern casual-professional styling, clean gradient background in [COLOR], DSLR quality, 3:4 composition.
```

**Example for sarah:**
```
4K ultra-realistic portrait of a 32-year-old woman podcast host, warm engaging smile with intelligent eyes, professional editorial photography style, soft studio lighting with subtle rim light, 85mm f/2 lens, shallow DOF, visible skin texture without heavy retouching, modern casual-professional styling with tasteful accessories, clean gradient background in soft coral to cream, DSLR quality, 3:4 composition.
```

---

## 3. Maintaining Character Consistency

The key technique for keeping characters identical across multiple images.

### @samescene - Same Character, New Environment

```
Create [SCENE TYPE] featuring the same character shown in the reference image. Keep all core design elements consistent.

Place the character [SCENE DESCRIPTION]. Maintain facial structure, [KEY FEATURES], [OUTFIT ELEMENTS]. Expression: [DESCRIBE].

Lighting: [MATCH OR SPECIFY]. Composition: [DESCRIBE]. Keep identity and signature design clearly recognizable from reference.

Aspect ratio [SPECIFY].
```

**Example for samantha-dreams:**
```
Create an action scene featuring the same character shown in the reference image. Keep all core design elements consistent.

Place the character floating through a surreal dreamscape of melting clocks and impossible geometry. Maintain facial structure, violet eyes, constellation freckles, iridescent skin shimmer. Expression: serene wonder.

Lighting: soft diffused glow with dramatic rim light. Composition: dynamic diagonal with character as focal point. Keep identity clearly recognizable from reference.

Aspect ratio 16:9.
```

### @samepose - Different Pose/Emotion

```
Show the same character from the reference image [NEW POSE/ACTION]. Keep identical: facial structure, [EYES], [HAIR], [SIGNATURE ELEMENTS].

Expression changed to: [NEW EMOTION]. Lighting adjusted for [NEW CONTEXT] while maintaining character recognition.
```

**Example:**
```
Show the same character from the reference image sitting cross-legged in meditation. Keep identical: facial structure, violet eyes, constellation freckles, wavy dark hair with purple undertones.

Expression changed to: peaceful concentration, eyes closed. Lighting adjusted for soft dawn light while maintaining character recognition.
```

### @ageprogress - Age Progression

```
Show the same character from the reference image [X] years [older/younger], with [AGE MARKERS] while preserving: bone structure, eye color, signature features.

Skin shows [AGE-APPROPRIATE CHANGES]. Hair: [DESCRIBE CHANGES]. Expression: [MATCHES AGED PERSONALITY].
```

### @outfit - Costume Change

```
Show the same character from the reference image wearing [NEW OUTFIT DESCRIPTION]. Keep identical: all facial features, hair, skin tone, signature markings.

New outfit: [DETAILED DESCRIPTION]. Body language adjusted for [CONTEXT]. Lighting: [SPECIFY].
```

---

## 4. UI/Marketing Assets

### @voiceorb - Voice-First Demo Hero Image

```
Ethereal voice AI interface visualization, abstract waveforms in [SOUL COLOR] (amber/purple/teal), bioluminescent orb pulsing with warm light, soft particles floating in twilight gradient background, minimal UI elements suggesting conversation flow, cinematic depth with bokeh, 16:9 hero banner format.
```

**Soul color options:**
- Dr. Shefali: amber/gold
- samantha-dreams: purple/violet
- kothar: bronze/amber
- tamar: pink/teal

### @bazaarheader - Multi-Soul Chatroom Header

```
Cyberpunk lounge interior "The Bazaar", neon-lit gathering space with multiple distinct silhouettes in conversation, 2038 futuristic aesthetic, warm amber and cool cyan lighting contrast, holographic displays visible, atmospheric fog, cinematic 21:9 ultra-wide banner format.
```

### @appicon - App Icon/Avatar Thumbnail

```
Clean centered [CHARACTER TYPE] avatar for app icon, [KEY VISUAL ELEMENT], circular composition optimized for small display, subtle gradient background in [COLOR], sharp focus on face/symbol, no text, 1:1 square format, high contrast for visibility at small sizes.
```

---

## 5. Prompt Formula (Official Google)

```
[Subject + Adjectives] doing [Action] in [Location/Context]. [Composition/Camera Angle]. [Lighting/Atmosphere]. [Style/Media]. [Specific Constraint/Text].
```

### Key Modifiers

**Realism:**
- "DSLR realism"
- "hyper-realistic"
- "visible pores and skin texture"
- "no smoothing"
- "no cartoon effect"

**Camera:**
- "85mm f/1.8" (portraits)
- "35mm f/2.8" (environmental)
- "shallow DOF"
- "macro lens"
- "low-angle shot"

**Lighting:**
- "soft diffused daylight"
- "golden hour"
- "rim lighting"
- "dramatic shadows"
- "neon pink and teal" (cyberpunk)
- "warm amber" (therapeutic)

**Quality:**
- "4K" / "8K"
- "professional editorial"
- "commercial quality"
- "cinematic color grade"

---

## 6. Common Mistakes to Avoid

1. **Over-prompting with 2023 keywords**
   - Skip: "4k, trending on artstation, masterpiece, highly detailed"
   - Nano Banana Pro understands natural language

2. **Vague text instructions**
   - Skip: "add text"
   - Use: "Write 'HELLO' in bold red serif font on the sign"

3. **Missing signature elements for consistency**
   - Always list 3-5 unique features when generating consistent characters
   - These are your "consistency anchors"

4. **Forgetting aspect ratio**
   - Always specify: 4:3 for reference sheets, 16:9 for banners, 1:1 for icons

5. **Using cartoon/illustration language for realism**
   - For real humans: explicitly add "no cartoon effect", "DSLR realism"
