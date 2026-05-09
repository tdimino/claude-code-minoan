# Vellum Page Architecture

Six page patterns and shared structural elements.

## HTML Head (shared)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{PAGE_TITLE}}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,700;1,400;1,500&family=Inconsolata:wght@400;500;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2/src/regular/style.css">
  <link rel="stylesheet" href="_shared.css">
  <link rel="stylesheet" href="_components.css">
</head>
```

## Body Open (shared)

```html
<body>
<a href="#main" class="skip-link">Skip to main content</a>
<script src="_auth.js"></script>  <!-- omit if no auth -->
```

## Landing Page Pattern

Used for index/home pages. No breadcrumb back link. Uses `header__icon` instead of `header__logo`.

```html
<nav class="breadcrumb" aria-label="Breadcrumb">
  <span>Project Name &middot; Section</span>
</nav>

<nav class="page-nav" aria-label="Deep dive pages">
  <a href="page-one.html">Page One</a>
  <a href="page-two.html">Page Two</a>
  <a href="#glossary">Glossary</a>
</nav>

<header>
  <img src="logos/icon.svg" alt="Project Name" class="header__icon">
  <p class="header__tag" aria-hidden="true">Tagline or Category</p>
  <h1>Main Headline</h1>
  <p>Subtitle or description in italic body font.</p>
</header>

<main id="main">
  <section id="section-name">
    <span class="section-num" aria-hidden="true">01</span>
    <h2><i class="ph ph-icon-name" aria-hidden="true"></i> Section Title</h2>
    <p class="lead">Lead paragraph text.</p>
    <!-- components here -->
  </section>

  <!-- more sections -->
</main>
```

## Deep-Dive Page Pattern

Used for sub-pages. Breadcrumb includes a back link. Uses `header__logo` (circular image). Includes TOC.

```html
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="index.html">Home</a> &rsaquo; <span>Page Title</span>
</nav>

<nav class="page-nav" aria-label="Deep dive pages">
  <a href="page-one.html" aria-current="page">Page One</a>
  <a href="page-two.html">Page Two</a>
  <a href="index.html#glossary">Glossary</a>
</nav>

<header>
  <img src="logos/page-logo.jpg" alt="" class="header__logo">
  <p class="header__tag" aria-hidden="true">Category Label</p>
  <h1>Page Headline</h1>
  <p>Page subtitle or description.</p>
</header>

<main id="main">
  <!-- Editorial TOC -->
  <nav class="toc" aria-label="On this page">
    <ol class="toc-list">
      <a href="#section-1" class="toc-item">
        <span class="toc-item__num">01</span>
        <span class="toc-item__body">
          <span class="toc-item__title">Section Title</span>
          <span class="toc-item__desc">One-line description of the section.</span>
        </span>
        <span class="toc-item__arrow" aria-hidden="true">&rarr;</span>
      </a>
      <!-- more toc-items -->
    </ol>
  </nav>

  <section id="section-1">
    <span class="section-num" aria-hidden="true">01</span>
    <h2>
      <a href="#section-1" class="deep-link">
        <i class="ph ph-icon-name" aria-hidden="true"></i> Section Title
      </a>
    </h2>
    <p class="lead">Lead paragraph text.</p>
    <!-- components here -->
  </section>
</main>
```

## Section Pattern

Every section follows this structure:

```html
<section id="kebab-case-id">
  <span class="section-num" aria-hidden="true">01</span>
  <h2>
    <i class="ph ph-icon-name" aria-hidden="true"></i> SECTION TITLE
  </h2>
  <p class="lead">Introductory paragraph. <strong>Bold text</strong> uses display font italic.</p>
  <p class="lead spaced-sm">Second paragraph with top spacing.</p>

  <!-- Component blocks follow -->
</section>
```

Section numbers (`section-num`) are ghost-styled Bodoni numerals positioned absolutely behind the heading.

## Glossary Pattern

Semantic `<dl>` in a 2-column CSS grid with row-based zebra striping.

```html
<section id="glossary">
  <span class="section-num" aria-hidden="true">07</span>
  <h2><i class="ph ph-book-open" aria-hidden="true"></i> Glossary</h2>

  <dl class="glossary">
    <div class="glossary__entry">
      <dt class="glossary__term">TERM</dt>
      <dd class="glossary__def">Definition text.</dd>
    </div>
    <!-- more entries -->
  </dl>
</section>
```

Zebra striping uses `nth-child(4n+3), nth-child(4n+4)` to stripe every other ROW in the 2-column grid. At mobile (single column), falls back to `nth-child(odd)`.

## Footer Pattern

```html
<footer>
  <nav class="footer__nav">
    <a href="index.html">Home</a>
    <a href="page-one.html">Page One</a>
  </nav>
  <p><em>Project Name</em> &mdash; Organization &copy; 2026</p>
</footer>
</body>
</html>
```

## Page-Nav Active State

Mark the current page with `aria-current="page"`:

```html
<a href="current-page.html" aria-current="page">Current Page</a>
```

This triggers the active styling: subq-colored text, tinted background, bold weight.

## Z-Index Layering

The crosshatch texture sits at `z-index: 0` via `body::before`. All visible content (breadcrumb, header, main, footer) uses `position: relative; z-index: 1` to layer above it.

## Section Hub Pattern

Landing page for a multi-page section. Uses sub-nav for section-internal navigation and a badge header.

```html
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="index.html">&larr; Overview</a> &rsaquo; <span>Section Name</span>
</nav>

<nav class="page-nav" aria-label="Pages">
  <a href="index.html">Overview</a>
  <a href="section.html" aria-current="page">Section</a>
</nav>

<nav class="sub-nav" aria-label="Section pages">
  <a href="section.html" aria-current="page">Hub</a>
  <a href="section-profiles.html">Profiles</a>
  <a href="section-comparison.html">Comparison</a>
  <a href="section-analysis.html">Analysis</a>
</nav>

<header>
  <img src="badges/section-badge.png" alt="" class="header__badge" width="120" height="120">
  <p class="header__tag" aria-hidden="true">Section &middot; Hub</p>
  <h1>Section Title</h1>
  <p>Section overview description.</p>
</header>

<main id="main">
  <section id="key-findings">
    <span class="section-num" aria-hidden="true">01</span>
    <h2><i class="ph ph-lightbulb" aria-hidden="true"></i> Key Findings</h2>
    <!-- State cards or further-cards grid -->
  </section>
</main>
```

The `header__badge` is a decorative image (120x120) used instead of `header__icon` or `header__logo` when the section has its own visual identity.

## Profile Dossier Pattern

Entity/company profiles with narrative hierarchy. Primary dossier gets full visual weight; secondary dossiers are diminished.

```html
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="index.html">&larr; Overview</a> &rsaquo; <a href="section.html">Section</a> &rsaquo; <span>Profiles</span>
</nav>

<nav class="page-nav" aria-label="Pages">
  <a href="index.html">Overview</a>
  <a href="section.html" aria-current="page">Section</a>
</nav>

<nav class="sub-nav" aria-label="Section pages">
  <a href="section.html">Hub</a>
  <a href="section-profiles.html" aria-current="page">Profiles</a>
  <a href="section-comparison.html">Comparison</a>
  <a href="section-analysis.html">Analysis</a>
</nav>

<header>
  <img src="badges/profiles-badge.png" alt="" class="header__badge" width="120" height="120">
  <p class="header__tag" aria-hidden="true">Section &middot; Profiles</p>
  <h1>Entity Profiles</h1>
  <p>Description of what's being profiled and why.</p>
</header>

<main id="main">
  <section id="profiles">
    <span class="section-num" aria-hidden="true">01</span>
    <h2><i class="ph ph-binoculars" aria-hidden="true"></i> Profiles</h2>
    <p class="lead">Introductory summary.</p>

    <!-- Editorial note (key cross-entity finding) -->
    <aside class="editorial-note" data-watermark="KEY FINDING">
      <!-- ... -->
    </aside>

    <div style="display: grid; gap: 1.4rem;">
      <!-- Primary dossier -->
      <article class="dossier" data-watermark="Primary">
        <!-- ... -->
      </article>

      <!-- Secondary dossiers -->
      <article class="dossier dossier--secondary" data-watermark="SecondaryA">
        <!-- ... -->
      </article>
      <article class="dossier dossier--secondary" data-watermark="SecondaryB">
        <!-- ... -->
      </article>
    </div>
  </section>

  <!-- Sources -->
  <footer class="sources" role="doc-endnotes">
    <!-- ... -->
  </footer>
</main>
```

Key structural rule: the editorial-note leads the section (key finding above individual profiles). Primary dossier first, secondary dossiers stacked below at reduced visual weight.

### Subject-Intro Variant

For person/handle profiles (as opposed to company entities), replace the `editorial-note` with a `subject-intro` component at the top of the main section. The subject-intro gives the handle its own visual lane:

```html
<main id="main">
  <section id="profile">
    <span class="section-num" aria-hidden="true">01</span>
    <h2><i class="ph ph-user" aria-hidden="true"></i> Profile</h2>

    <div class="subject-intro">
      <div class="subject-intro__handle">HandleName</div>
      <div class="subject-intro__text">
        <strong>Real Name</strong> is the person behind this handle&mdash;
        biographical context that flows freely.
      </div>
    </div>

    <!-- Hero image with lightbox follows -->
    <img src="archive/photo.jpg" alt="Description" class="hero-image"
         onclick="document.getElementById('lb-photo').classList.add('open')">
    <!-- Rest of profile content -->
  </section>
</main>
```

Use `editorial-note` for cross-entity analytical findings. Use `subject-intro` for biographical introductions where the handle/name is the primary identity anchor.

## Feature Comparison Pattern

Side-by-side feature/capability comparison with dimension grids and matrices.

```html
<!-- Same nav structure as Profile Dossier (breadcrumb + page-nav + sub-nav) -->

<header>
  <img src="badges/comparison-badge.png" alt="" class="header__badge" width="120" height="120">
  <p class="header__tag" aria-hidden="true">Section &middot; Comparison</p>
  <h1>Feature Comparison</h1>
  <p>What we're comparing and on what dimensions.</p>
</header>

<main id="main">
  <!-- TOC -->
  <nav class="toc" aria-label="On this page">
    <ol class="toc-list">
      <!-- toc-items for each dimension -->
    </ol>
  </nav>

  <section id="dimension-1">
    <span class="section-num" aria-hidden="true">01</span>
    <h2><i class="ph ph-scales" aria-hidden="true"></i> Dimension Name</h2>
    <p class="lead">What this dimension measures.</p>

    <!-- Matrix component for structured comparison -->
    <div class="matrix matrix--3col">
      <!-- matrix rows -->
    </div>
    <div class="matrix-note matrix-note--neutral">
      <strong>Note:</strong> Contextual interpretation.
    </div>
  </section>

  <!-- More dimension sections -->

  <footer class="sources" role="doc-endnotes">
    <!-- ... -->
  </footer>
</main>
```

## Analysis / Implications Pattern

Strategic analysis with gap identification, advantage rows, and recommendations.

```html
<!-- Same nav structure as Profile Dossier (breadcrumb + page-nav + sub-nav) -->

<header>
  <img src="badges/analysis-badge.png" alt="" class="header__badge" width="120" height="120">
  <p class="header__tag" aria-hidden="true">Section &middot; Analysis</p>
  <h1>Strategic Analysis</h1>
  <p>What the comparison data means for strategy.</p>
</header>

<main id="main">
  <nav class="toc" aria-label="On this page">
    <ol class="toc-list">
      <!-- toc-items -->
    </ol>
  </nav>

  <section id="gaps">
    <span class="section-num" aria-hidden="true">01</span>
    <h2><i class="ph ph-magnifying-glass" aria-hidden="true"></i> Competitive Gaps</h2>
    <p class="lead">Where the opportunity lies.</p>

    <!-- State cards grid for gap items -->
    <div class="states-grid states-grid--3col">
      <!-- state-card components -->
    </div>
  </section>

  <section id="advantages">
    <span class="section-num" aria-hidden="true">02</span>
    <h2><i class="ph ph-trophy" aria-hidden="true"></i> Strategic Advantages</h2>

    <div class="inline-advantages">
      <!-- advantage-row components -->
    </div>
  </section>

  <section id="recommendations">
    <span class="section-num" aria-hidden="true">03</span>
    <h2><i class="ph ph-compass" aria-hidden="true"></i> Recommendations</h2>
    <!-- Pullquote + prose + req-cards -->
  </section>

  <footer class="sources" role="doc-endnotes">
    <!-- ... -->
  </footer>
</main>
```

## Inline Page-Specific Style Convention

Pages with entity-specific content (watermark text, custom grid ratios) embed a `<style>` block in `<head>` after the CSS links:

```html
<link rel="stylesheet" href="_components.css">
<style>
  /* Page: [page-name] — entity-specific overrides */
  .custom-class { /* ... */ }
</style>
```

Use sparingly — only for overrides that don't generalize across pages.

## Hero Image + Lightbox Integration

Hero images go inside sections, typically below the h2 heading. Each hero image pairs with a lightbox overlay.

```html
<section id="archive">
  <span class="section-num" aria-hidden="true">01</span>
  <h2><i class="ph ph-image" aria-hidden="true"></i> The Archive</h2>

  <img src="archive/hero.jpg" alt="Description" class="hero-image"
       onclick="document.getElementById('lb-hero').classList.add('open')">

  <div class="hero-lightbox" id="lb-hero" onclick="this.classList.remove('open')">
    <button class="hero-lightbox__close" aria-label="Close">&times;</button>
    <img src="archive/hero.jpg" alt="Full size">
  </div>

  <p class="lead">Content continues below the hero image.</p>
</section>
```

The `section h2 + .hero-image` rule adds `margin-top: 1rem` for tight spacing when the image directly follows a heading. When images appear deeper in a section, they get the default `margin-top: 1.75rem`.

## Audio Player Placement

The audio player is injected by `_audio-player.js` as a fixed-position element. Load the script at the end of `<body>`:

```html
  <!-- Before closing body tag -->
  <script src="_audio-player.js"></script>
</body>
```

Position: fixed top-right on desktop, bottom-right on mobile (640px breakpoint). The player auto-plays after auth gate clears via the `vellum:authenticated` event, and persists playback state across page navigations via `sessionStorage`.

For dark themes, the player background uses `oklch(0.14 0.02 265 / 0.85)` with `backdrop-filter: blur(12px)`. For warm themes, use `oklch(0.96 0.008 80 / 0.85)`.

## Accessibility

- Skip link: always first element after `<body>` open
- `aria-label` on all `<nav>` elements (Breadcrumb, Deep dive pages, Section pages, On this page)
- `aria-hidden="true"` on decorative elements (icons, section numbers, badges)
- `role="dialog"` and `aria-label` on auth overlay
- `role="region"` and `aria-label` on dossier articles
- `role="doc-endnotes"` on sources footer, `role="doc-noteref"` on footnote links
- Focus-visible outlines on all interactive elements (2px solid copper, 2px offset)
- Reduced motion media query disables all animations
