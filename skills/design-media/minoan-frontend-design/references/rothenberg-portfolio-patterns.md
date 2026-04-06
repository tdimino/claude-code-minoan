# Rothenberg Portfolio Patterns

Design patterns distilled from mattrothenberg.com — a dark editorial portfolio that achieves distinction through typography alone. No hero images, no cards, no gradient buttons. Text is the design. Complements `stripe-signature-techniques.md` (light premium) and `mintlify-signature-techniques.md` (dark-first docs) as a third brand exemplar archetype.

**Archetype**: Dark Editorial Portfolio
**When to apply**: Portfolio sites, freelancer pages, personal brand sites, "about me" pages, writer/developer profiles, agency landing pages. Any context where the person's words and credentials are the product.

---

## Text-As-Hero Philosophy

The entire page is set in editorial serif at 32-40px body size. No images appear above the fold. No illustrations, no screenshots, no decorative SVGs. The typography carries all visual weight, making the page feel like a well-set editorial spread rather than a website.

**Key rules:**
- Body text at 2-2.5rem (32-40px) — dramatically larger than typical web body (16px)
- Italic serif for identity words that define the person: "*designer*, *developer*, *serial tinkerer*"
- No images needed — if the writing is strong, the type does the work
- Single-column layout, ~700px max-width, generous vertical rhythm (48-64px between sections)
- The constraint of no images forces premium through type selection and spacing

**When to apply:** Any portfolio where the person's background and voice matter more than visual artifacts. Especially effective for engineers, writers, and designers whose work lives in other contexts (GitHub, published articles, client sites).

---

## Warm OKLCH Tinted Neutrals

The palette uses exactly 5 tokens — all OKLCH with warm hue tinting (hue 56-74, low chroma 0.006-0.013). No pure black, no pure white, no accent colors. The warmth comes from consistent hue tinting across the entire lightness range.

```css
:root {
  --bg:        oklch(0.216 0.006 56);    /* dark warm brown */
  --text:      oklch(0.97  0.001 106);   /* off-white, warm tint */
  --muted:     oklch(0.444 0.011 74);    /* section labels, metadata */
  --border:    oklch(0.374 0.010 68);    /* subtle dividers, badge outlines */
  --secondary: oklch(0.553 0.013 58);    /* older content, de-emphasized text */
}
```

**Key traits:**
- Background is oklch 0.216 (≈ 22% lightness), not pure black — warm brown undertone
- Text is oklch 0.97, not pure white — slight cream/parchment cast
- All intermediate values (muted, border, secondary) share the same warm hue family (56-74)
- No accent color at all — hierarchy comes from lightness alone
- The restricted palette creates cohesion without trying

**When to apply:** Dark-mode portfolios, editorial layouts, any design where restraint signals confidence. Pair with warm serif typography.

---

## Typography Pairing: Editorial Serif + Monospace Labels

Three font roles, no sans-serif anywhere in the body:

| Role | Font | Fallback | Usage |
|------|------|----------|-------|
| Body prose | PP Editorial New | Georgia, serif | All running text at 32-40px |
| Section labels | PP Fraktion Mono | ui-monospace, monospace | Uppercase micro-headlines |
| Metadata | PP Supply Mono | ui-monospace, monospace | Years, dates, nav items |

**Italic as semantic emphasis:** Italic is reserved for words that define identity — role titles, descriptors, qualities. Not for visual decoration.

**Section labels as monospace wayfinding:**
```css
.section-label {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--muted);
  margin-bottom: 1.5rem;
}
```

These function as wayfinding markers ("I'M EMPLOYABLE", "I FREELANCE", "I WRITE WORDS"), not as heading hierarchy. They orient the reader without demanding attention.

---

## Component Patterns

### 1. Inline Brand Badge

A pill-shaped badge with company logo + name that sits *inside* flowing prose text. The sentence reads naturally: "I work at [Cloudflare] as a Principal Engineer."

```css
.brand-badge {
  display: inline-flex;
  align-items: baseline;    /* stays on the text baseline */
  gap: 0.4em;
  padding: 0.05em 0.7em;
  border: 1px solid var(--border);
  border-radius: 9999px;    /* max-round pill */
  text-decoration: none;
  font: inherit;            /* matches surrounding prose */
}

.brand-badge img {
  width: 1em;
  height: 1em;
  vertical-align: -0.1em;   /* optical alignment with text */
}
```

**Key insight:** `align-items: baseline` keeps the badge text on the same baseline as the surrounding sentence. `font: inherit` prevents the badge from breaking typographic rhythm.

**When to use:** Employment history, client mentions, tool references — anywhere a brand name appears inline in narrative prose. Alternative to underlined links when the brand identity (logo) adds information.

### 2. Editorial Link

Links that don't break typographic rhythm. The only affordance is a 2px underline at reduced opacity:

```css
.editorial-link {
  color: inherit;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 0.15em;
  text-decoration-color: oklch(0.97 0.001 106 / 0.4);
  transition: text-decoration-color 200ms ease-out;
}

.editorial-link:hover {
  text-decoration-color: oklch(0.97 0.001 106 / 0.8);
}
```

**Key insight:** No color change. The underline opacity is the only affordance — rising from 40% to 80% on hover. This keeps the page feeling like a typeset document rather than a hyperlinked website.

### 3. Monochrome Logo Grid

A grid of client/partner logos displayed as desaturated marks — no labels, no cards, no hover effects:

```css
.logo-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;                          /* hairline dividers via background */
  background: var(--border);         /* gap becomes visible border */
}

.logo-grid a {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--bg);
  aspect-ratio: 3 / 2;
}

.logo-grid img {
  max-width: 120px;
  max-height: 48px;
  filter: grayscale(1) brightness(0.7) contrast(1.2);
  opacity: 0.6;
  transition: opacity 200ms ease-out;
}

.logo-grid a:hover img {
  opacity: 0.9;
}
```

**Key insight:** The `gap: 1px` with `background: var(--border)` creates visible hairline dividers without adding border properties to each cell. Logos are desaturated via CSS filter, not pre-processed images.

**When to use:** Freelance client lists, partner grids, "as seen in" sections. The monochrome treatment signals volume without overwhelming — the logos support the narrative, they don't compete with it.

### 4. Timeline Article List

A minimal publication/writing list with border-separated rows, title left, year right:

```css
.article-list {
  list-style: none;
  padding: 0;
}

.article-list li {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0.75rem 0;
  border-top: 1px solid var(--border);
}

.article-list .title {
  font-family: var(--font-serif);
  color: var(--text);
}

.article-list .year {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--muted);
  flex-shrink: 0;
  margin-left: 2rem;
}
```

**Key insight:** No bullet points, no cards, no descriptions. Just title + year with `justify-content: space-between`. The border-top (not bottom) means the first item gets a top border too, creating a clean ruled-line effect. Older entries fade via reduced text opacity.

**When to use:** Publication lists, talk histories, project timelines, changelog entries.

### 5. Text-Only CTA

A call-to-action that relies entirely on editorial voice — no button chrome, no gradients, no icons:

```html
<a href="mailto:hello@example.com" class="text-cta">
  I'd love to hear about your project.<br>
  <em>Let's work together</em> &rarr;
</a>
```

```css
.text-cta {
  display: block;
  font-family: var(--font-serif);
  font-size: 2rem;
  line-height: 1.3;
  color: var(--text);
  text-decoration: none;
  padding: 3rem 0;
}

.text-cta em {
  font-style: italic;
  text-decoration: underline;
  text-decoration-color: oklch(0.97 0.001 106 / 0.4);
  text-underline-offset: 0.15em;
}

.text-cta:hover em {
  text-decoration-color: oklch(0.97 0.001 106 / 0.8);
}
```

**Key insight:** The arrow (→) is just a Unicode character, not an SVG icon. The italic emphasis on "Let's work together" IS the button — no background, no border, no padding. This only works when the surrounding page has built enough trust through content that the CTA feels natural rather than missing.

**When to use:** Personal portfolios, freelancer sites, any context where a button would feel commercial and the tone should feel like a conversation.

### 6. Breadcrumb-Style Nav

Navigation as a simple text path with slash separators:

```css
.site-nav {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}

.site-nav a {
  color: var(--text);
  text-decoration: none;
}

.site-nav .separator {
  margin: 0 0.5em;
  color: var(--border);
}
```

Renders as: `MATTROTHENBERG.COM / HOME / EXPERIMENTS / NOTES`

**When to use:** Simple portfolios with 2-4 pages. The breadcrumb format signals navigability without a full nav bar, keeping the page feeling like a document.

---

## Page Structure

```
┌─────────────────────────────────────────┐
│  SITE.COM / HOME / EXPERIMENTS / NOTES  │  Breadcrumb nav (monospace, muted)
├─────────────────────────────────────────┤
│                                         │
│  I'm [Name], a [location]-based        │  Hero text (serif, 36-40px)
│  *designer*, *developer*, and          │  Italics for identity words
│  *serial tinkerer*.                    │
│                                         │
│  [casual one-liner about personality]   │  Supporting text (same size, warm)
│                                         │
├─────────────────────────────────────────┤
│  ᴍᴏɴᴏ SECTION LABEL                    │  Monospace micro-headline
│                                         │
│  I work at [🔸 Brand] as a...          │  Prose with inline brand badges
│  I used to work at [⬡ Brand] where... │  Employment narrative
│                                         │
├─────────────────────────────────────────┤
│  ᴍᴏɴᴏ SECTION LABEL                    │
│                                         │
│  ┌──────┬──────┬──────┬──────┐         │  Monochrome logo grid
│  │ Logo │ Logo │ Logo │ Logo │         │  4-column, desaturated
│  ├──────┼──────┼──────┼──────┤         │
│  │ Logo │ Logo │ Logo │ Logo │         │
│  └──────┴──────┴──────┴──────┘         │
│                                         │
├─────────────────────────────────────────┤
│  ᴍᴏɴᴏ SECTION LABEL                    │
│                                         │
│  I'd love to hear about your project.  │  Text-only CTA
│  *Let's work together* →               │  Italic + arrow, no button
│                                         │
├─────────────────────────────────────────┤
│  ᴍᴏɴᴏ SECTION LABEL                    │
│  ─────────────────────────────── 2023  │  Timeline article list
│  Article Title                    2022  │  Border-separated rows
│  ─────────────────────────────── 2019  │
│                                         │
├─────────────────────────────────────────┤
│  ᴍᴏɴᴏ SECTION LABEL                    │
│                                         │
│  GitHub  Twitter  LinkedIn  Email      │  Social links (serif, underlined)
│                                         │
├─────────────────────────────────────────┤
│  ████ ASCII ART FOOTER ████            │  Pixel-art text w/ opacity cascade
│  ████ ASCII ART FOOTER ████            │  Playful coda
└─────────────────────────────────────────┘
```

---

## What Makes This Distinctive

1. **Zero visual dependencies** — No images, icons, illustrations, or SVGs needed. A text editor is the only design tool.
2. **Typography IS the design system** — Font selection, size, weight, and italics create all hierarchy. Color only modulates importance within a monochromatic warm range.
3. **Prose as interface** — The page reads like a letter, not a website. Employment history is narrated, not listed. Client work is shown via a logo grid, not case study cards.
4. **Restraint as confidence** — The absence of decoration signals that the person's work speaks for itself. Every portfolio with gradients, animations, and card carousels is implicitly saying the content isn't enough.
5. **Anti-portfolio tropes** — No "hero section with background image," no "three-column skills grid," no "testimonial carousel," no "animated statistics counter." These are replaced by typography, whitespace, and honest writing.
