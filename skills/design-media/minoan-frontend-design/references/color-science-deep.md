# Color Science Foundations

Deep color theory that informs design decisions. Complements `impeccable-color-contrast.md` (practical CSS implementation) with the perceptual science underneath.

Source: synthesized from meodai/skill.color-expert (144 reference files, ~286K words of transcripts, papers, and tool documentation).

## Color Spaces — What to Use When

| Task | Use | Why |
|------|-----|-----|
| Perceptual color manipulation | **OKLCH** | Best uniformity for lightness, chroma, hue. Fixes CIELAB's blue problem. |
| CSS gradients & palettes | **OKLCH** or `color-mix(in oklab)` | No mid-gradient darkening like RGB/HSL |
| Gamut-aware color picking | **OKHSL / OKHSV** | Ottosson's picker spaces — cylindrical like HSL but perceptually grounded |
| Normalized saturation (0-100%) | **HSLuv** | CIELUV chroma normalized per hue/lightness. HPLuv for pastels. |
| Print workflows | **CIELAB D50** | ICC standard illuminant |
| Screen workflows | **CIELAB D65** or OKLAB | D65 = screen standard |
| Cross-media appearance matching | **CAM16 / CIECAM02** | Accounts for surround, adaptation, luminance, viewing conditions |
| HDR | **Jzazbz / ICtCp** | Designed for extended dynamic range |
| Pigment/paint mixing simulation | **Kubelka-Munk** (Spectral.js, Mixbox) | Spectral reflectance mixing, not RGB averaging |
| Color difference (precision) | **CIEDE2000** | Gold standard perceptual distance |
| Color difference (fast) | **Euclidean in OKLAB** | Good enough for most applications |
| Video/image compression | **YCbCr** | Luma+chroma separation enables chroma subsampling |

## Why HSL Lies

HSL isn't broken — it's a geometric rearrangement of RGB into a cylinder. Fine for quick tweaks. But its channels don't correspond to human perception:

- **Lightness (L):** Fully saturated yellow (`hsl(60,100%,50%)`) and fully saturated blue (`hsl(240,100%,50%)`) both have L=50% but vastly different perceived brightness. L is a math average, not a perceptual measurement.
- **Hue (H):** Non-uniform spacing. A 20deg shift near red is dramatic; the same 20deg near green is barely visible. Greens are compressed, reds stretched.
- **Saturation (S):** Doesn't correlate with perceived saturation. S=100% on a dark blue still looks muted.

**When HSL is fine:** Simple color pickers, quick CSS tweaks, cases where perceptual accuracy doesn't matter.

**When to upgrade:**
- Generating palettes or scales: **OKLCH** (uniform lightness across hues)
- Creating gradients: **OKLAB** or `color-mix(in oklab)` (no mid-gradient mud)
- Gamut-aware picking with HSL-like UX: **OKHSL** (Ottosson's perceptual HSL)
- Normalized saturation 0-100%: **HSLuv** (CIELUV-based, no out-of-bounds)

See `impeccable-color-contrast.md` for OKLCH CSS syntax, dark mode token patterns, and tinted neutrals.

## Named Hue Ranges (HSL/HSV Degrees)

Practical lookup for constraining or generating colors by hue name:

| Name | Degrees |
|------|---------|
| **red** | 345-360, 0-15 |
| **orange** | 15-45 |
| **yellow** | 45-70 |
| **green** | 70-165 |
| **cyan** | 165-195 |
| **blue** | 195-260 |
| **purple** | 260-310 |
| **pink** | 310-345 |
| **warm** | 0-70 |
| **cool** | 165-310 |

Source: mrmrs / random-display-p3-color.

## Precise Definitions

These are distinct dimensions. Conflating them causes palette bugs:

- **Chroma** = colorfulness relative to a same-lightness neutral reference (distance from gray axis)
- **Saturation** = perceived colorfulness relative to the color's own brightness (angle from white)
- **Lightness** = perceived reflectance relative to a similarly lit white (contextual)
- **Brightness** = perceived intensity of light coming from a stimulus (absolute)

Same chroma does NOT equal same saturation. They are different dimensions.

## Color Harmony — Character Over Hue

### Hue-first harmony is weak on its own

Complementary, triadic, tetradic intervals are weak predictors of mood, legibility, or accessibility. Every hue plane has a different shape in perceptual space, so geometric hue intervals don't guarantee perceptual balance.

### Character-first harmony (Ellen Divers' research)

Organize by character (pale / muted / deep / vivid / dark), not hue. **Hue is usually a weaker predictor of emotional response than chroma and lightness** — a muted palette reads as calm across many hues. Relaxed vs intense is driven more by chroma + lightness than hue alone.

"Blue is calm" is an unreliable shortcut — mood depends on chroma, lightness, context, and composition more than hue.

### Legibility = lightness variation

Grayscale is a quick sanity check for lightness separation, not an accessibility proof. Same character + varied lightness is often more readable. Same lightness regardless of hue is usually illegible. Still verify with WCAG/APCA against text size, weight, polarity, and CVD.

## Accessibility — The Real Numbers

Of ~281 trillion hex color pairs (brute-force Rust computation by @mrmrs_):

| Threshold | % passing | Odds |
|-----------|-----------|------|
| WCAG 3:1 (large text) | 26.49% | ~1 in 4 |
| WCAG 4.5:1 (AA body text) | 11.98% | ~1 in 8 |
| WCAG 7:1 (AAA) | 3.64% | ~1 in 27 |
| APCA 60 | 7.33% | ~1 in 14 |
| APCA 75 (fluent reading) | 1.57% | ~1 in 64 |
| APCA 90 (preferred body) | **0.08%** | **~1 in 1,250** |

APCA is far more restrictive than WCAG at comparable readability levels. At APCA 90, only 239 billion of 281 trillion pairs work. JPEG compression exploits the same biology—chroma subsampling discards 4x color data invisibly because human vision resolves luminance at higher resolution than chrominance.

### Most accessible color axis

Orange-blue is the most accessible pair — works for BOTH red-green AND yellow-blue color blindness. The opponent process model explains why: 4 psychological primaries on 2 axes (red-green, yellow-blue). CVD loses one axis. Orange-blue survives both losses.

## Color Temperature

Temperature is NOT hue — it's a systematic shift of BOTH hue AND saturation, dependent on starting hue.

- **Spectral bias**: which end of the spectrum a light favors (short wavelengths = cool, long wavelengths = warm)
- **Cool daylight**: blue atmospheric scatter fills shadows; paint neutral highlights, blue shadows
- **Warm incandescent**: favors long wavelengths including infrared (literally felt as heat)
- **Green and purple** don't map cleanly to warm/cool — perceived temperature depends strongly on context

## Pigment Mixing in Code

RGB averaging produces brown mud. Real pigment mixing is non-linear:

- **Pigment mixing is "integrated mixing"** (Kuppers/Briggs) — a compromise between subtractive and additive averaging, not pure subtraction
- **CMY mixing paths curve outward** (retain chroma = vivid secondaries) — "extroverted octopus"
- **RGB mixing paths curve inward** (lose chroma = dull browns) — "introverted octopus"
- **Mixing is non-linear**: proportion of paint does NOT equal proportional hue change. You "turn a corner" at certain ratios
- **Blue to yellow is a LONG road**, red to yellow is SHORT. Traditional wheels massively misrepresent distances
- **Tinting strength varies**: blues are concentrated/strong, yellows are weak
- **White doesn't just lighten** — it shifts hue AND kills chroma

For spectral/Kubelka-Munk mixing in code: **Spectral.js** (open source, blue+yellow=green) or **Mixbox** (commercial).

## Color Naming Systems

| System | Register | Example |
|--------|----------|---------|
| ISCC-NBS | Scientific precision | "vivid yellowish green" |
| Munsell | Systematic notation | "5GY 7/10" |
| XKCD | Common perception | "ugly yellow", "hospital green" |
| Traditional Japanese | Cultural/poetic | "wasurenagusa-iro" (forget-me-not) |
| RAL | Industrial reproducibility | RAL 5002 |
| Ridgway (1912) | Ornithological | 1,115 named colors, public domain |
| CSS Named Colors | Web standard | 147 named colors |
| color-description lib | Emotional adjectives | "pale, delicate, glistening" |

`color-name-lists` npm package provides 18 naming systems in one import.

## Historical Corrections

Common color theory claims that are wrong, with corrections:

- **Moses Harris (1769)** was first to place RYB at equal 120deg — Newton, Boutet, Schiffermüller didn't. His own wheel needed a 4th pigment. The origin of bad color theory.
- **Von Bezold (1874)** killed "indigo" as a spectral color — Newton's "blue" is approximately modern cyan, Newton's "indigo" is approximately modern blue.
- **The word "magenta"** wasn't used for the subtractive primary until 1907 (Carl Gustav Zander). Before: "pink" (Benson 1868), "crimson," "purpur."
- **Amy Sawyer (1911)** patented a CMY wheel (primrose/rose/turquoise) decades before it became mainstream.
- **Elizabeth Lewis (1931)** married trichromatic + opponent process on one wheel, anticipating CIE Lab by 30 years.

---

**Deep source**: meodai/skill.color-expert — 145 reference files across `historical/`, `contemporary/`, and `techniques/` directories covering the full lineage from Newton to OKLCH.
