# Vellum Component Catalog

Copy-paste HTML snippets for all 35 components. Organized by functional role.

---

## Layout Components

### Breadcrumb

```html
<!-- Landing page (no link) -->
<nav class="breadcrumb" aria-label="Breadcrumb">
  <span>Project Name &middot; Section</span>
</nav>

<!-- Sub-page (with back link) -->
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="index.html">Home</a> &rsaquo; <span>Page Title</span>
</nav>
```

### Page Nav

Navigation strip linking between pages. Mark current page with `aria-current="page"`.

```html
<nav class="page-nav" aria-label="Deep dive pages">
  <a href="index.html">Overview</a>
  <a href="features.html" aria-current="page">Features</a>
  <a href="roadmap.html">Roadmap</a>
  <a href="index.html#glossary">Glossary</a>
</nav>
```

CSS: `_components.css`. Active state: subq-colored text, tinted bg, bold weight. Touch targets: 44px min-height.

### Header

```html
<!-- Landing page -->
<header>
  <img src="logos/icon.svg" alt="Project" class="header__icon">
  <p class="header__tag" aria-hidden="true">Category Label</p>
  <h1>Main Headline</h1>
  <p>Subtitle in italic body font.</p>
</header>

<!-- Sub-page -->
<header>
  <img src="logos/page.jpg" alt="" class="header__logo">
  <p class="header__tag" aria-hidden="true">Category Label</p>
  <h1>Page Headline</h1>
  <p>Page description.</p>
</header>
```

`header__icon`: 80x80px SVG. `header__logo`: 120x120px circular image with border and shadow.

### Section with Ghost Number

```html
<section id="section-id">
  <span class="section-num" aria-hidden="true">01</span>
  <h2><i class="ph ph-cube" aria-hidden="true"></i> Section Title</h2>
  <p class="lead">Lead paragraph. <strong>Bold</strong> renders in display font italic.</p>
</section>
```

### Footer

```html
<footer>
  <nav class="footer__nav">
    <a href="index.html">Home</a>
    <a href="features.html">Features</a>
  </nav>
  <p><em>Project Name</em> &mdash; Organization &copy; 2026</p>
</footer>
```

---

## Card Components

### State Card

Status indicator card with colored top-bar accent. 9 variants.

```html
<div class="states-grid">
  <div class="state-card state-card--dealbreaker">
    <h4>DEALBREAKER</h4>
    <h5><i class="ph ph-warning" aria-hidden="true"></i> Card Title</h5>
    <p>Description text.</p>
    <div class="state-card__verbs">
      <span class="verb-chip">tag-one</span>
      <span class="verb-chip">tag-two</span>
    </div>
  </div>
  <!-- more cards -->
</div>
```

**Variants:** `--dealbreaker`, `--high`, `--moderate`, `--subq`, `--claude`, `--cursor`, `--codex`, `--critical`, `--omp`

**Grid:** `states-grid` (2-col), `states-grid--3col` (3-col), `states-grid--featured` (first card spans full width)

**Interactive:** Hover shows border + shadow. `:active` scales to 0.96. `:focus-visible` shows copper outline.

### Hook Card

Lifecycle hook or feature cards in auto-fit grid.

```html
<div class="hook-grid">
  <div class="hook-card">
    <h4><span class="hook-card__icon"><i class="ph ph-gear" aria-hidden="true"></i></span> Hook Name</h4>
    <p>Description of the hook or feature.</p>
    <p class="hook-card__verb">Related verb or action</p>
  </div>
</div>
```

**Variants:** `hook-card--dealbreaker` (h4 color), `hook-card--high` (bg + border tint)

### Cap Panel

Capability or feature panels.

```html
<div class="caps-grid">
  <div class="cap-panel">
    <h4>CATEGORY</h4>
    <h5>Panel Title</h5>
    <p>Description text.</p>
  </div>
  <div class="cap-panel cap-panel--primary">
    <h4>PRIMARY</h4>
    <h5>Highlighted Panel</h5>
    <p>Description with tinted background.</p>
  </div>
</div>
```

**Variants:** default, `--primary` (subq bg+border), `--dealbreaker` (h4 color), `--claude` (h4 color), `--neutral` (ink h4)

### Further Card

"Read more" link cards with optional logo.

```html
<div class="further">
  <a href="page.html" class="further-card">
    <img src="logos/page.jpg" alt="" class="further-card__logo">
    <div class="further-card__head">
      <i class="ph ph-chart-bar" aria-hidden="true"></i>
      <span class="further-card__name">Page Name</span>
    </div>
    <p class="further-card__desc">One-line description.</p>
  </a>
</div>
```

Hover: border-color copper, shadow, translateY(-2px). Active: scale(0.96).

### Quote Card

```html
<div class="quote-card">
  <blockquote>Quote text in italic body font.</blockquote>
  <cite>— Attribution</cite>
</div>
```

### Req Card

Requirement cards with ID, body, and meta badges.

```html
<div class="req-card">
  <span class="req-card__id">R-01</span>
  <div class="req-card__body">
    <h5>Requirement Title</h5>
    <p>Requirement description.</p>
  </div>
  <div class="req-card__meta">
    <span class="tier-badge tier-badge--1">Tier 1</span>
    <span class="status-chip status-chip--shipped"><span class="status-dot status-dot--shipped"></span> Shipped</span>
  </div>
</div>
```

Responsive: 3-col → 2-col at 900px → 1-col at 640px.

---

## Data Display Components

### Matrix

Feature comparison grids. 14 column presets available.

```html
<div class="matrix matrix--3col">
  <div class="matrix__row matrix__row--head">
    <div class="matrix__cell"><span class="matrix__th"><i class="ph ph-grid-four" aria-hidden="true"></i> Feature</span></div>
    <div class="matrix__cell matrix__cell--center"><span class="matrix__th matrix__th--center">Tool A</span></div>
    <div class="matrix__cell matrix__cell--center"><span class="matrix__th matrix__th--center">Tool B</span></div>
  </div>
  <div class="matrix__row">
    <div class="matrix__cell"><span class="matrix__tool">Feature Name</span></div>
    <div class="matrix__cell matrix__cell--center"><span class="matrix__verdict matrix__verdict--yes">Yes</span></div>
    <div class="matrix__cell matrix__cell--center"><span class="matrix__verdict matrix__verdict--partial">Partial</span></div>
  </div>
</div>
```

**Column presets:** `--3col`, `--4col`, `--5col`, `--parity`, `--cost-ranking`, `--model-roles`, `--metrics`, `--trust`, `--risk`, `--pain`, `--supersession`, `--variant`, `--session-pain`, `--targets`

**Verdict badges:** `--dealbreaker`, `--high`, `--moderate`, `--subq`, `--claude`, `--cursor`, `--codex`, `--yes`, `--partial`, `--critical`, `--omp`

**Special rows:** `matrix__row--divider` (section divider), `matrix__row--total` (summary row)

### Matrix Note

Callout note below matrices.

```html
<div class="matrix-note">
  <strong>Note Label:</strong> Explanation text.
</div>
```

**Variants:** default (high), `--dealbreaker`, `--subq`, `--copper`, `--neutral`, `--critical`

### Glossary

2-column semantic definition list with row-based zebra striping.

```html
<dl class="glossary">
  <div class="glossary__entry">
    <dt class="glossary__term">TERM</dt>
    <dd class="glossary__def">Definition text.</dd>
  </div>
  <div class="glossary__entry">
    <dt class="glossary__term">NEXT</dt>
    <dd class="glossary__def">Another definition.</dd>
  </div>
</dl>
```

Striping: `nth-child(4n+3), nth-child(4n+4)` for row-based striping in 2-col grid. Mobile fallback: `nth-child(odd)`.

### Ring

Nested concentric information containers. 4 depth tiers.

```html
<div class="ring ring--claude">
  <h3>Outer Ring</h3>
  <p>Outer description.</p>
  <div class="ring ring--dealbreaker">
    <h3>Middle Ring</h3>
    <p>Middle description.</p>
    <div class="ring ring--subq">
      <h3>Inner Ring</h3>
      <p>Inner description.</p>
      <div class="ring ring--core">
        <h3>Core</h3>
        <p>Core description.</p>
      </div>
    </div>
  </div>
</div>
```

Each tier reduces horizontal margin. `ring--core` uses dashed border.

### Debugger Panel

Dark terminal-style code blocks with staggered line animation.

```html
<div class="debugger-panel">
  <div class="debugger-panel__header">
    <span class="debugger-panel__dot debugger-panel__dot--red"></span>
    <span class="debugger-panel__dot debugger-panel__dot--amber"></span>
    <span class="debugger-panel__dot debugger-panel__dot--green"></span>
    <span class="debugger-panel__title">Panel Title</span>
  </div>
  <div class="debugger-panel__body">
    <div class="console-line">
      <span class="console-verb console-verb--subq">verb.name</span>
      <span class="console-msg">Message text</span>
      <span class="console-state hide-mobile">STATE</span>
    </div>
    <!-- more lines, each animates in with staggered delay -->
  </div>
</div>
```

**Verb colors:** `--claude`, `--codex`, `--subq`, `--dealbreaker`, `--high`, `--copper`, `--market`, `--critical`, `--omp`

Lines animate in via `consoleSlideIn` with 0.15s–3.65s staggered delays (up to 12 lines). `console-state` hides on mobile.

### Diagram Panel

Container for inlined SVG diagrams generated by `beautiful-mermaid`. Optional label (copper mono) and caption (italic display font with top border).

```html
<!-- Basic diagram with label and caption -->
<figure class="diagram-panel">
  <p class="diagram-panel__label">Architecture Overview</p>
  <!-- Inline SVG from: node ~/.claude/skills/beautiful-mermaid/scripts/mermaid.mjs -f svg -t vellum --transparent "graph TD; A-->B" -->
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400">
    <!-- beautiful-mermaid SVG output -->
  </svg>
  <figcaption class="diagram-panel__caption">Data flow from ingestion to rendering</figcaption>
</figure>

<!-- Copper-accented variant -->
<figure class="diagram-panel diagram-panel--copper">
  <p class="diagram-panel__label">Decision Flow</p>
  <!-- SVG content -->
  <figcaption class="diagram-panel__caption">Routing logic for incoming requests</figcaption>
</figure>

<!-- Full-bleed variant (no padding, edge-to-edge SVG) -->
<figure class="diagram-panel diagram-panel--bleed">
  <!-- SVG content -->
  <figcaption class="diagram-panel__caption">Full-width diagram</figcaption>
</figure>
```

**Generation:** `printf 'graph TD\n  A --> B --> C' | node ~/.claude/skills/beautiful-mermaid/scripts/mermaid.mjs -f svg -t vellum --transparent -o diagram.svg -`

**Inline strategy:** Copy the SVG output directly into the HTML. Remove `width`/`height` attributes from the root `<svg>` element (keep `viewBox`) so it fills the container responsively. The `--transparent` flag omits the SVG background, letting the panel's `--bg-card` show through.

**Variants:** default, `--copper` (copper-tinted border + bg), `--bleed` (zero padding)

---

## Indicator Components

### Status Dot

```html
<span class="status-dot status-dot--shipped"></span>
```

**Variants:** `--planned`, `--building` (pulse animation), `--shipped`, `--blocked`, `--critical`

### Status Chip

```html
<span class="status-chip status-chip--building">
  <span class="status-dot status-dot--building"></span> Building
</span>
```

**Variants:** `--planned`, `--building`, `--shipped`, `--blocked`, `--critical`, `--high`

### Tier Badge

```html
<span class="tier-badge tier-badge--1">Tier 1</span>
```

**Variants:** `--1` (teal), `--2` (blue), `--3` (amber), `--4` (orange)

### Chip / Chip Grid

```html
<div class="chip-grid">
  <span class="chip chip--subq">Tag One</span>
  <span class="chip chip--dealbreaker">Tag Two</span>
  <span class="chip">Neutral Tag</span>
</div>
```

**Variants:** default (neutral), `--dealbreaker`, `--high`, `--moderate`, `--subq`, `--claude`, `--cursor`, `--codex`

### Verdict Badge (Matrix)

```html
<span class="matrix__verdict matrix__verdict--yes">Yes</span>
```

Used inside matrix cells. Same color variants as chips plus `--yes`, `--partial`, `--legend`, `--total`.

---

## Editorial Components

### TOC

Editorial table of contents with ghost numbers and descriptions.

```html
<nav class="toc" aria-label="On this page">
  <ol class="toc-list">
    <a href="#section-1" class="toc-item">
      <span class="toc-item__num">01</span>
      <span class="toc-item__body">
        <span class="toc-item__title">Section Title</span>
        <span class="toc-item__desc">One-line description.</span>
      </span>
      <span class="toc-item__arrow" aria-hidden="true">&rarr;</span>
    </a>
  </ol>
</nav>
```

Hover: padding-left shift + warm bg. Arrow appears on hover and focus-visible.

### Pullquote

```html
<blockquote class="pullquote">
  A striking statement that deserves visual emphasis.
</blockquote>
```

Display font, copper color, border-top and border-bottom, generous vertical padding (2rem).

### Savings Callout

Financial or metric highlight box.

```html
<div class="savings-callout">
  <div class="savings-callout__number">$47K</div>
  <div class="savings-callout__label">Annual Savings</div>
</div>
```

Subq-tinted border and background. Number in 3rem display font, label in mono uppercase.

### Supersession Arrow

Directional replacement indicator.

```html
<div class="supersession">
  <span class="supersession__from">Old Thing</span>
  <span class="supersession__arrow">&rarr;</span>
  <span class="supersession__to">New Thing</span>
</div>
```

"From" is struck-through with neutral styling. "To" is subq-colored with tinted background.

### Advantage Row

Inline benefit/advantage display.

```html
<div class="inline-advantages">
  <div class="advantage-row">
    <span class="advantage-row__icon"><i class="ph ph-check-circle" aria-hidden="true"></i></span>
    <span class="advantage-row__name">Feature Name</span>
    <span class="advantage-row__desc">What this advantage provides.</span>
  </div>
</div>
```

First row gets `border-top`. Name in subq-colored mono, 170px min-width.

### Phase Timeline

Horizontal timeline with numbered phase blocks.

```html
<div class="phase-timeline">
  <div class="phase-block">
    <div class="phase-block__num">1</div>
    <div class="phase-block__title">Phase Name</div>
    <div class="phase-block__weeks">Wk 1–2</div>
    <div class="phase-block__badges">
      <span class="tier-badge tier-badge--1">Tier 1</span>
    </div>
  </div>
  <!-- more phase blocks -->
</div>
```

6-column grid on desktop, 3-col at 900px, 2-col at 640px. Hover: copper border + shadow.

### Section Break

```html
<hr class="section-break">
```

Simple 1px border-top with 2.5rem vertical margin.

---

## Intelligence Components

### Entity Dossier

Full-width profile card with asymmetric hero (logo | content), ghost watermark, and 2-column fact grid. Use `data-watermark` for the ghost text. Secondary variant: lighter bg, reduced opacity, thinner border.

```html
<!-- Primary dossier -->
<article class="dossier" data-watermark="CompanyName" id="company-profile" role="region" aria-label="Company profile">
  <div class="dossier__hero">
    <div class="dossier__mark">
      <img src="logos/company.svg" alt="Company logo" width="128" height="128">
      <span class="dossier__tag">B2B &middot; Category</span>
      <div class="stat-stack">
        <div class="stat-stack__item">
          <div class="stat-stack__label">Founded</div>
          <div class="stat-stack__value">2023</div>
        </div>
        <div class="stat-stack__item">
          <div class="stat-stack__label">Users</div>
          <div class="stat-stack__value stat-stack__value--warn">Undisclosed</div>
        </div>
      </div>
    </div>
    <div class="dossier__summary">
      <div class="dossier__kicker">Primary profile</div>
      <h3 class="dossier__name">Company Name</h3>
      <p class="dossier__subtitle">The Editorial Judgment</p>
      <p>Summary paragraph about what this entity is and why it matters.</p>
    </div>
  </div>
  <div class="dossier__grid">
    <div class="dossier__column">
      <!-- Fact blocks go here -->
    </div>
    <div class="dossier__column">
      <!-- Secondary facts / utterances go here -->
    </div>
  </div>
</article>

<!-- Secondary (diminished) dossier -->
<article class="dossier dossier--secondary" data-watermark="OtherCo" id="other-profile" role="region" aria-label="Other profile">
  <div class="dossier__hero">
    <div class="dossier__mark">
      <img src="logos/other.png" alt="Other logo" width="128" height="128">
      <span class="dossier__tag">B2C &middot; Category</span>
    </div>
    <div class="dossier__summary">
      <div class="dossier__kicker">Absorbed — redirects to primary</div>
      <h3 class="dossier__name">Other Co</h3>
      <p class="dossier__subtitle">The Concierge Illusion</p>
      <p>Brief summary of what happened to this entity.</p>
    </div>
  </div>
  <div class="dossier__grid">
    <div class="dossier__column"><!-- facts --></div>
    <div class="dossier__column"><!-- facts --></div>
  </div>
</article>
```

Primary: 1.5px `border-strong`, box-shadow, full opacity. Secondary: 1px border, no shadow, 0.92 opacity, smaller typography.

### Stat Stack

Centered label/value pairs below a logo or mark. Values support color variants.

```html
<div class="stat-stack">
  <div class="stat-stack__item">
    <div class="stat-stack__label">Founded</div>
    <div class="stat-stack__value">2021</div>
  </div>
  <div class="stat-stack__item">
    <div class="stat-stack__label">Traction</div>
    <div class="stat-stack__value stat-stack__value--warn">Waitlist only</div>
  </div>
  <div class="stat-stack__item">
    <div class="stat-stack__label">Status</div>
    <div class="stat-stack__value stat-stack__value--dead">Dead</div>
  </div>
</div>
```

Variants: `--warn` (amber, uses `--high`), `--dead` (red, uses `--dealbreaker`), `--good` (green, uses `--shipped`).

### Utterance Block

Icon avatar + monospace quoted text in a tinted row. AI variant uses claude colors.

```html
<!-- Brand utterance -->
<div class="utterance utterance--brand">
  <i class="ph ph-seal-check" aria-hidden="true"></i>
  <p>&ldquo;We handle everything from booking to loyalty integration.&rdquo;</p>
</div>

<!-- AI utterance -->
<div class="utterance utterance--ai">
  <i class="ph ph-robot" aria-hidden="true"></i>
  <p>&ldquo;Analysis: this claim contradicts the technical evidence.&rdquo;</p>
</div>
```

Default: warm bg + copper icon. `--ai`: claude-bg + claude-colored icon. `--brand`: explicit warm bg (same as default, use for semantic clarity).

### Editorial Note

Full-width 2-column asymmetric block with strong top/bottom borders and ghost watermark. Use for key findings that should lead a section.

```html
<aside class="editorial-note" data-watermark="KEY FINDING" aria-label="Key finding">
  <div>
    <div class="editorial-note__kicker">April 2026 Finding</div>
    <h3>All three now resolve to one operating entity.</h3>
    <p>Explanation of the finding with inline references and context.</p>
  </div>
  <div class="entity-flow" aria-label="Entity relationships">
    <!-- Entity nodes here -->
  </div>
</aside>
```

The secondary slot (right column) can contain an entity-flow, stat-stack, or any other component.

### Entity Flow

Vertical list showing entities with logos, labels, and status. Use inside editorial-note secondary slots or standalone.

```html
<div class="entity-flow" aria-label="Entity flow">
  <div class="entity-node">
    <img src="logos/company-a.png" alt="" width="28" height="28">
    <span class="entity-node__label">Company A</span>
    <span class="entity-node__status">redirected</span>
  </div>
  <div class="entity-node">
    <img src="logos/company-b.svg" alt="" width="28" height="28">
    <span class="entity-node__label">Company B</span>
    <span class="entity-node__status">survivor</span>
  </div>
</div>
```

Logo: 1.8rem square. Borders between rows, no border on last child.

### Fact Block

Icon + monospace label + body paragraph. Warning/critical variants get colored border and background.

```html
<!-- Standard fact -->
<div class="fact-block">
  <div class="fact-block__label">
    <i class="ph ph-code" aria-hidden="true"></i>
    Technical Stack
  </div>
  <p>Built on Spotnana GDS with NDC integration for direct airline content.</p>
</div>

<!-- Warning fact -->
<div class="fact-block fact-block--warning">
  <div class="fact-block__label">
    <i class="ph ph-warning" aria-hidden="true"></i>
    Red Flag
  </div>
  <p>No public API documentation despite claiming an open platform.</p>
</div>

<!-- Critical fact -->
<div class="fact-block fact-block--critical">
  <div class="fact-block__label">
    <i class="ph ph-skull" aria-hidden="true"></i>
    Critical
  </div>
  <p>Domain 301-redirects to competitor. Product is dead.</p>
</div>
```

Stack in `.dossier__column` elements. First child has no top border.

### Sub-Navigation

Secondary sticky nav below page-nav. Smaller font, sticks below the page-nav at `top: 3.5rem`.

```html
<nav class="sub-nav" aria-label="Section pages">
  <a href="section.html">Hub</a>
  <a href="section-profiles.html" aria-current="page">Profiles</a>
  <a href="section-comparison.html">Comparison</a>
  <a href="section-analysis.html">Analysis</a>
</nav>
```

Active state: copper text, tinted bg, bold weight. Adjusts `scroll-margin-top` for anchored content below.

### Source List

Footnote superscripts with copper hover, endnote list with backlinks and source-type tags.

```html
<!-- Inline footnote reference -->
<sup><a class="fn-ref" href="#src-1" role="doc-noteref">1</a></sup>

<!-- Endnotes section -->
<footer class="sources" role="doc-endnotes">
  <h2><i class="ph ph-books" aria-hidden="true"></i> Sources</h2>
  <ol>
    <li id="src-1">
      Company About page, accessed April 2026.
      <span class="sources__tag sources__tag--press">PRESS</span>
      <a href="#" target="_blank" rel="noopener">Link &rarr;</a>
    </li>
    <li id="src-2">
      Internal analysis of redirect chain.
      <span class="sources__tag sources__tag--finding">FINDING</span>
    </li>
    <li id="src-3">
      &ldquo;Quoted statement from source.&rdquo;
      <span class="sources__tag sources__tag--quote">QUOTE</span>
    </li>
    <li id="src-4">
      Market data: 2.4M monthly visits.
      <span class="sources__tag sources__tag--stat">STAT</span>
    </li>
  </ol>
</footer>
```

Tag variants: `--stat` (subq green), `--quote` (cursor purple), `--finding` (amber), `--press` (neutral muted).

---

## Media Components

### Subject Intro

Two-column callout with a prominent handle/name in the left cell and descriptive text in the right. Uses CSS grid with `auto | 1fr` columns. The handle gets its own visual lane, preventing text orphaning.

```html
<div class="subject-intro">
  <div class="subject-intro__handle">Handle Name</div>
  <div class="subject-intro__text">
    <strong>Real Name</strong> is the person behind this handle&mdash;description text
    that can flow freely without orphaning the handle.
  </div>
</div>
```

```css
.subject-intro {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0 1.5rem;
  background: var(--era-name-bg);
  border: 1px solid var(--era-name-border);
  border-radius: 6px;
  padding: 1.25rem 1.5rem;
  margin: 0 0 1.25rem;
  align-items: center;
}
.subject-intro__handle {
  font-family: var(--display);
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  font-style: italic;
  font-weight: 500;
  color: var(--era-name);
  line-height: 1.1;
  white-space: nowrap;
  padding-right: 1.5rem;
  border-right: 1px solid var(--era-name-border);
}
.subject-intro__text {
  font-family: var(--body);
  font-size: 0.95rem;
  font-style: italic;
  line-height: 1.6;
  color: var(--ink);
}
.subject-intro__text strong {
  font-style: normal;
  color: var(--era-name);
}
@media (max-width: 480px) {
  .subject-intro { grid-template-columns: 1fr; gap: 0.75rem 0; }
  .subject-intro__handle {
    border-right: none;
    border-bottom: 1px solid var(--era-name-border);
    padding-right: 0;
    padding-bottom: 0.75rem;
  }
}
```

Use as a replacement for `editorial-note` when the primary subject is a person or handle rather than a finding. Swap `--era-name` for the appropriate era/entity color.

### Stat Bar

Compact horizontal row of key/value stat cells. Cells flex-wrap at narrow widths, stacking vertically on mobile.

```html
<div class="stat-bar">
  <div class="stat-bar__item">
    <div class="stat-bar__val">827</div>
    <div class="stat-bar__label">SALVAGED FILES</div>
  </div>
  <div class="stat-bar__item">
    <div class="stat-bar__val">42</div>
    <div class="stat-bar__label">AIM TRANSCRIPTS</div>
  </div>
  <div class="stat-bar__item">
    <div class="stat-bar__val">2003–07</div>
    <div class="stat-bar__label">ACTIVE YEARS</div>
  </div>
</div>
```

CSS: flex row with `flex: 1; min-width: 100px` per item. Values use `var(--display)` at 1.4rem with `tabular-nums`. Labels use `var(--mono)` at 0.62rem uppercase with `var(--text-label)`. Items separated by `border-right: 1px solid var(--border)`. Collapses to vertical stack at 640px.

### Hero Image

Full-width image with click-to-lightbox. Fits inside sections below h2 headings.

```html
<img src="archive/screenshot.jpg" alt="Description" class="hero-image"
     onclick="document.getElementById('lb-screenshot').classList.add('open')">

<div class="hero-lightbox" id="lb-screenshot"
     onclick="this.classList.remove('open')">
  <button class="hero-lightbox__close" aria-label="Close">&times;</button>
  <img src="archive/screenshot.jpg" alt="Description (full size)">
</div>
```

```css
section h2 + .hero-image { margin-top: 1rem; }
.hero-image {
  width: 100%; border-radius: 6px;
  border: 1px solid var(--border);
  margin-top: 1.75rem; margin-bottom: 2rem;
  object-fit: cover; max-height: 320px;
  cursor: pointer;
}
.hero-lightbox {
  display: flex; position: fixed; inset: 0; z-index: 200;
  background: oklch(0.15 0.02 270 / 0.92);
  align-items: center; justify-content: center; padding: 2rem;
  opacity: 0; pointer-events: none;
  transition: opacity 300ms cubic-bezier(0.25, 1, 0.5, 1);
}
.hero-lightbox.open { opacity: 1; pointer-events: auto; }
.hero-lightbox img {
  max-width: 92vw; max-height: 90vh;
  object-fit: contain; border-radius: 6px;
  box-shadow: 0 8px 40px oklch(0 0 0 / 0.4);
  transform: scale(0.95);
  transition: transform 300ms cubic-bezier(0.25, 1, 0.5, 1);
}
.hero-lightbox.open img { transform: scale(1); }
.hero-lightbox__close {
  position: absolute; top: 1.5rem; right: 1.5rem;
  font-size: 2rem; color: oklch(0.9 0 0);
  background: none; border: none; cursor: pointer; line-height: 1;
}
```

On dark themes, the lightbox overlay uses `oklch(0.15 0.02 270 / 0.92)`. On warm themes, use `oklch(0.22 0.04 270 / 0.85)` for a softer overlay. Mobile caps `max-height: 200px`.

### Gallery (Masonry Grid)

Multi-column image grid with CSS columns and click-to-lightbox. Each item scales on hover.

```html
<div class="masonry-grid">
  <div class="masonry-grid__item"
       onclick="document.getElementById('lb-1').classList.add('open')">
    <img src="archive/img-1.jpg" alt="Description">
  </div>
  <div class="masonry-grid__item"
       onclick="document.getElementById('lb-2').classList.add('open')">
    <img src="archive/img-2.jpg" alt="Description">
  </div>
  <!-- more items -->
</div>

<!-- Lightboxes for each image -->
<div class="hero-lightbox" id="lb-1" onclick="this.classList.remove('open')">
  <button class="hero-lightbox__close" aria-label="Close">&times;</button>
  <img src="archive/img-1.jpg" alt="Full size">
</div>
```

```css
.masonry-grid {
  columns: 3 220px; column-gap: 1rem;
}
.masonry-grid__item {
  break-inside: avoid; margin-bottom: 1rem;
  border-radius: 4px; overflow: hidden;
  cursor: pointer; position: relative;
}
.masonry-grid__item img {
  width: 100%; display: block;
  transition: transform 300ms cubic-bezier(0.25, 1, 0.5, 1);
}
.masonry-grid__item:hover img { transform: scale(1.03); }
```

Gallery shares the `hero-lightbox` component for full-size viewing. Responsive: 3 columns at desktop, 2 at 640px. Pair with `stagger-in` class for load animation (see `advanced-patterns.md`).

### Audio Player

Fixed ambient audio control with Web Audio API frequency-reactive visualization bars. Position fixed in top-right corner.

```html
<!-- In _audio-player.js (loaded at end of body) -->
<!-- Generates this markup dynamically: -->
<div class="audio-player">
  <audio id="site-audio" src="archive/track.mp3" preload="metadata" loop></audio>
  <button class="audio-player__btn" id="audio-toggle" title="Play — Track Name">
    <span class="audio-player__pulse"></span>
    <i class="ph ph-speaker-high" id="audio-icon"></i>
  </button>
  <div class="audio-player__bars">
    <span class="audio-player__bar"></span>
    <span class="audio-player__bar"></span>
    <span class="audio-player__bar"></span>
    <span class="audio-player__bar"></span>
    <span class="audio-player__bar"></span>
  </div>
  <input type="range" class="audio-player__volume" id="audio-volume"
         min="0" max="100" value="40" title="Volume">
  <span class="audio-player__label">Track Name</span>
</div>
```

**Key architecture:**
- `_audio-player.js` creates the player element on `DOMContentLoaded`
- Web Audio API `AnalyserNode` (fftSize: 64, smoothing: 0.8) drives 5 frequency bars via `requestAnimationFrame`
- Bars transition height with `60ms linear` — JS sets `style.height` per frame
- Falls back gracefully: if `AudioContext` unavailable, audio plays without visualization
- `sessionStorage` saves/restores playback state (time, volume, playing) for cross-page continuity
- Listens for `vellum:authenticated` custom event to auto-play after auth gate clears
- Use `preload="metadata"` (not `"auto"`) to avoid downloading the full file per page load

**CSS:** Fixed position, `backdrop-filter: blur(12px)`, pill-shaped border-radius (20px). Label expands on hover/playing via `max-width` transition. Pulse animation on the play button when active. See `_shared.css` audio section.

---

## Utility Classes

| Class | Effect |
|-------|--------|
| `.spaced` | `margin-top: 1.25rem` |
| `.spaced-sm` | `margin-top: 1rem` |
| `.gap-below` | `margin-bottom: 1.5rem` |
| `.gap-below-md` | `margin-bottom: 1.25rem` |
| `.gap-below-sm` | `margin-bottom: 1rem` |
| `.flush` | `margin-bottom: 0` |
| `.hide-mobile` | Hidden at 640px and below |
| `.lead` | Body text with italic bold in display font |
| `.code--copper` | Inline code in copper color |
