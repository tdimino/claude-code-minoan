# Chapter Structure

Scroll pacing, sticky sections, and narrative timing for scrollytelling chapter architecture.

## Chapter as Semantic Unit

Each chapter is a `<section>` with `data-chapter` index and color palette data. Minimum 100vh height. Contains: heading, body text, optional media.

```html
<section class="chapter" data-chapter="0" data-hue="250" data-chroma="0.15" data-lightness="0.25">
  <div class="chapter-content">
    <h2 class="chapter-title">Chapter One</h2>
    <p class="chapter-body">The story begins at dawn...</p>
  </div>
</section>
```

## Sticky Section Pattern

Chapter content sticks while scroll progress drives the animation timeline:

```css
.chapter {
  position: relative;
  min-height: var(--sc-chapter-height, 200vh);
}

.chapter-content {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--sc-chapter-padding, clamp(2rem, 5vw, 6rem));
}
```

The gap between `min-height` (200vh) and the sticky content (100vh) provides the scroll distance for animations. Scroll 100vh through each chapter = the animation's full duration.

## Scroll Pacing by Content Type

| Content Type | Scroll Height | Pacing | Rationale |
|-------------|--------------|--------|-----------|
| Hero / title card | 150vh | Short | Punchy entrance, don't linger |
| Narrative text | 200vh | Medium | Room for reading + animation sequence |
| Image / media reveal | 250vh | Long | Slow reveal builds anticipation |
| Data / statistics | 150vh | Short | Quick impact, digestible |
| Transition / palate cleanser | 100vh | Minimal | Brief breathing room between chapters |
| Finale / closing | 200vh | Medium | Lingering exit, let the story settle |

Apply pacing multiplier: `slow` = 1.5×, `medium` = 1.0×, `fast` = 0.6×.

## Section Entrance Patterns

### Fade Up (Default)

```js
gsap.from('.chapter-title', {
  y: 80,
  opacity: 0,
  duration: 1.4,
  ease: 'cinematicSilk',
  scrollTrigger: {
    trigger: '.chapter',
    start: 'top 80%',
    toggleActions: 'play none none reverse'
  }
});

gsap.from('.chapter-body', {
  y: 40,
  opacity: 0,
  duration: 1.0,
  delay: 0.3,
  ease: 'cinematicSmooth',
  scrollTrigger: {
    trigger: '.chapter',
    start: 'top 80%',
    toggleActions: 'play none none reverse'
  }
});
```

### Split Text

Each word enters with stagger — dramatic, use sparingly (one chapter at most):

```js
const words = element.textContent.split(' ');
element.innerHTML = '';
words.forEach(word => {
  const span = document.createElement('span');
  span.textContent = word + ' ';
  span.style.display = 'inline-block';
  element.appendChild(span);
});

gsap.from(element.children, {
  y: 40,
  opacity: 0,
  duration: 0.8,
  stagger: 0.08,
  ease: 'cinematicFlow',
  scrollTrigger: {
    trigger: element.closest('.chapter'),
    start: 'top 75%',
    toggleActions: 'play none none reverse'
  }
});
```

### Scale Reveal

```js
gsap.from('.chapter-media', {
  scale: 0.85,
  opacity: 0,
  duration: 1.2,
  ease: 'cinematicSmooth',
  scrollTrigger: {
    trigger: '.chapter',
    start: 'top 70%',
    toggleActions: 'play none none reverse'
  }
});
```

### Clip-Path Wipe

Cinematic curtain effect — like a scene transition in film:

```js
gsap.from('.chapter-content', {
  clipPath: 'inset(100% 0 0 0)',
  duration: 1.4,
  ease: 'cinematicFlow',
  scrollTrigger: {
    trigger: '.chapter',
    start: 'top 80%',
    toggleActions: 'play none none reverse'
  }
});
```

## Narrative Timing Rule

Entrance animations complete within the first 30% of the chapter's scroll distance. The reader never waits for animation to finish before content is readable.

For a 200vh chapter: animations fire within the first 60vh of scrolling. The remaining 140vh is for color transitions, shader evolution, and reading time.

## Typography

```css
.chapter-title {
  font-family: var(--sc-font-display);
  font-size: var(--sc-heading-size);
  font-weight: var(--sc-heading-weight);
  letter-spacing: var(--sc-heading-tracking);
  line-height: var(--sc-heading-leading);
  color: var(--sc-text-heading);
}

.chapter-body {
  font-family: var(--sc-font-body);
  font-size: var(--sc-body-size);
  font-weight: var(--sc-body-weight);
  line-height: var(--sc-body-leading);
  max-width: var(--sc-body-max-width);
  color: var(--sc-text);
}
```

## Responsive Layout

### Desktop (>1024px)
Chapters span full viewport, sticky content centered, full animation set.

### Tablet (768–1024px)
Reduce chapter scroll height by 25%. Maintain sticky pattern. Simplify split-text to fade-up.

### Mobile (<768px)
Reduce to minimum sticky (100vh per chapter). Replace clip-path wipe with simple fade. Reduce typography stagger count. Disable shader canvas or reduce to static gradient.

```css
@media (max-width: 768px) {
  .chapter {
    min-height: 150vh;
  }
  .chapter-title {
    font-size: clamp(1.8rem, 4vw, 2.5rem);
  }
}
```

## Accessibility

```html
<!-- Semantic structure -->
<main>
  <section class="chapter" aria-label="Chapter 1: Dawn">
    <div class="chapter-content">
      <h2 class="chapter-title">Dawn</h2>
      <p class="chapter-body">...</p>
    </div>
  </section>
</main>
```

All content readable without JavaScript. Animations are progressive enhancement. `prefers-reduced-motion` disables all entrance effects and shows final states.
