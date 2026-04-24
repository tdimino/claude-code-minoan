# Vellum Page Architecture

Two page patterns and shared structural elements.

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

## Accessibility

- Skip link: always first element after `<body>` open
- `aria-label` on all `<nav>` elements (Breadcrumb, Deep dive pages, On this page)
- `aria-hidden="true"` on decorative elements (icons, section numbers)
- `role="dialog"` and `aria-label` on auth overlay
- Focus-visible outlines on all interactive elements (2px solid copper, 2px offset)
- Reduced motion media query disables all animations
