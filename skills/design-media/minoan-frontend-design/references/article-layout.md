# Long-form Article Layout

Page template for research papers, white papers, blog posts, and case studies with a sticky table of contents sidebar, inline data visualizations, block quotes, and citation system. Modeled on Contra Labs research, Stripe Press, and academic journal layouts.

---

## Page Structure

```
┌──────────────────────────────────────────────────────────────┐
│ Header / Nav                                                 │
├────────────┬─────────────────────────────────────────────────┤
│            │                                                 │
│  TOC       │  Article Title (H1)                             │
│  sidebar   │  Metadata (author · date · read time)           │
│  (sticky)  │                                                 │
│            │  ## 1.0 Introduction                            │
│  1.0 Intro │  Paragraph text...                              │
│  2.0 Meth  │                                                 │
│  3.0 Find  │  > "Block quote from expert"                    │
│  4.0 Limit │  > — Attribution, Title                         │
│  5.0 Impl  │                                                 │
│            │  ┌────────────────────────────┐                 │
│            │  │  Figure: bar chart / viz   │                 │
│            │  │  Caption text below        │                 │
│            │  └────────────────────────────┘                 │
│            │                                                 │
│            │  ## 2.0 Methodology                             │
│            │  ...                                            │
│            │                                                 │
│            │  ## References                                  │
│            │  [1] Author, Title, Year                        │
│            │  [2] ...                                        │
│            │                                                 │
├────────────┴─────────────────────────────────────────────────┤
│ Footer                                                       │
└──────────────────────────────────────────────────────────────┘
```

## Tailwind Implementation

### Page Container

```html
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="lg:grid lg:grid-cols-[220px_1fr] lg:gap-12 xl:grid-cols-[260px_1fr]">
    <!-- Sidebar TOC -->
    <aside class="hidden lg:block">
      <nav class="sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto"
           aria-label="Table of contents">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-4">
          Contents
        </h2>
        <ol class="space-y-2 text-sm">
          <li>
            <a href="#introduction"
               class="block text-zinc-400 hover:text-white transition-colors
                      data-[active]:text-white data-[active]:font-medium">
              1.0 Introduction
            </a>
          </li>
          <li>
            <a href="#methodology"
               class="block text-zinc-400 hover:text-white transition-colors">
              2.0 Methodology
            </a>
          </li>
          <!-- More sections... -->
        </ol>
      </nav>
    </aside>

    <!-- Article content -->
    <article class="max-w-prose">
      <!-- Title block -->
      <header class="mb-12">
        <h1 class="text-3xl sm:text-4xl font-bold text-white leading-tight">
          The Human Creativity Benchmark
        </h1>
        <div class="mt-4 flex flex-wrap items-center gap-3 text-sm text-zinc-500">
          <span>Contra Labs</span>
          <span aria-hidden="true">·</span>
          <time datetime="2026-04-30">April 30, 2026</time>
          <span aria-hidden="true">·</span>
          <span>31 min read</span>
        </div>
      </header>

      <!-- Prose content -->
      <div class="prose prose-zinc prose-invert prose-lg
                  prose-headings:scroll-mt-24
                  prose-a:text-amber-400 prose-a:no-underline hover:prose-a:underline
                  prose-strong:text-white
                  prose-blockquote:border-l-amber-500 prose-blockquote:text-zinc-300
                  prose-figcaption:text-zinc-500 prose-figcaption:text-sm">
        <!-- Content sections here -->
      </div>
    </article>
  </div>
</div>
```

## Scroll-Spy for Active TOC Item

```js
const sections = document.querySelectorAll('article h2[id]');
const tocLinks = document.querySelectorAll('nav a[href^="#"]');

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        tocLinks.forEach((link) => delete link.dataset.active);
        const active = document.querySelector(`nav a[href="#${entry.target.id}"]`);
        if (active) active.dataset.active = '';
      }
    });
  },
  { rootMargin: '-20% 0px -60% 0px' }
);

sections.forEach((section) => observer.observe(section));
```

## Block Quote Styling

```html
<blockquote class="border-l-2 border-amber-500 pl-6 my-8 not-prose">
  <p class="text-lg text-zinc-300 italic leading-relaxed">
    "The Claude version stood out because the sections felt more intentional
    and not just dropped into generic blocks."
  </p>
  <footer class="mt-3 text-sm text-zinc-500">
    <cite class="not-italic">
      <span class="font-medium text-zinc-400">Blake Steven</span>, Creative Director
    </cite>
  </footer>
</blockquote>
```

## Figure with Caption

```html
<figure class="my-10 not-prose">
  <!-- Inline chart, image, or data viz -->
  <div class="rounded-xl overflow-hidden bg-zinc-800/50 p-6">
    <!-- Visualization content here (see inline-dataviz.md) -->
  </div>
  <figcaption class="mt-3 text-sm text-zinc-500 text-center">
    Convergence by scalar question and domain. Prompt adherence and usability
    produce higher agreement than visual appeal.
  </figcaption>
</figure>
```

## Citation System

### Inline References (Footnote Style)

```html
<p>
  Standard evaluation approaches treat evaluator disagreement as something
  to resolve<a href="#ref-3" class="text-amber-400 text-xs align-super
  no-underline hover:underline" id="cite-3">[3]</a><a href="#ref-4"
  class="text-amber-400 text-xs align-super no-underline hover:underline"
  id="cite-4">[4]</a>.
</p>
```

### References Section

```html
<section class="mt-16 pt-8 border-t border-zinc-800" id="references">
  <h2 class="text-xl font-semibold text-white mb-6">References</h2>
  <ol class="space-y-3 text-sm text-zinc-400 list-none">
    <li id="ref-1" class="pl-8 -indent-8">
      <span class="text-zinc-500">[1]</span> Amabile, T.M. (1982).
      Social psychology of creativity: A consensual assessment technique.
      <em>Journal of Personality and Social Psychology</em>, 43(5), 997–1013.
      <a href="#cite-1" class="text-amber-500/60 hover:text-amber-400 ml-1">↩</a>
    </li>
    <!-- More references... -->
  </ol>
</section>
```

### Copy Citation Block

```html
<div class="mt-8 rounded-lg bg-zinc-800/50 p-4 text-sm">
  <p class="text-xs uppercase tracking-wider text-zinc-500 mb-2">Cite as</p>
  <p class="text-zinc-300 font-mono text-xs leading-relaxed">
    Contra Labs. (2026). The Human Creativity Benchmark.
    Contra Labs Research, No. 01.
  </p>
  <div class="mt-3 flex gap-2">
    <button class="text-xs text-amber-400 hover:text-amber-300">Copy APA</button>
    <button class="text-xs text-amber-400 hover:text-amber-300">Copy BibTeX</button>
  </div>
</div>
```

## Mobile TOC (Collapsed)

On `lg:hidden`, render the TOC as a collapsible dropdown at the top of the article:

```html
<details class="lg:hidden mb-8 rounded-lg bg-zinc-800/50 p-4">
  <summary class="text-sm font-medium text-zinc-300 cursor-pointer">
    Contents
  </summary>
  <ol class="mt-3 space-y-2 text-sm text-zinc-400">
    <li><a href="#introduction">1.0 Introduction</a></li>
    <!-- ... -->
  </ol>
</details>
```

## Accessibility

- TOC `<nav>` with `aria-label="Table of contents"`
- Section headings have `id` attributes for anchor linking
- `scroll-mt-24` on headings to clear sticky header when jumping
- Citation back-links (`↩`) allow keyboard navigation between reference and inline cite
- Block quotes use `<blockquote>` with `<cite>` in `<footer>`
- Figures use `<figure>` + `<figcaption>` for semantic image/chart association

## Responsive Behavior

| Breakpoint | TOC | Content Width | Typography |
|-----------|-----|--------------|------------|
| Desktop (lg+) | Sticky sidebar | `max-w-prose` (~65ch) | `prose-lg` |
| Tablet (md) | Collapsed `<details>` at top | Full width minus padding | `prose-base` |
| Mobile (sm) | Collapsed `<details>` | Full width | `prose-base`, tighter spacing |
