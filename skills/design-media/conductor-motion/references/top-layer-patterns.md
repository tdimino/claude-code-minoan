# Top Layer Patterns

Popover, dialog, and toast lifecycles — entry *and* exit animation with the browser owning the timing. One family covers all transient chrome; don't build separate popover/dialog/toast pattern sets, they share the same three CSS primitives.

## The Three Primitives

```
@starting-style                      → the state an element transitions FROM on first
                                       render or display:none → block
transition-behavior: allow-discrete  → lets display and overlay participate in
                                       transitions instead of snapping
overlay transition                   → holds the element in the top layer until its
                                       exit transition finishes
```

Support: `@starting-style` Chrome 117+ / Safari 17.5+ / Firefox 129+; Popover API and `allow-discrete` Baseline 2024. Older browsers get instant show/hide — content intact, animation absent. That is the correct fallback; no JS shim.

## Popover: Zero-JS Lifecycle

```html
<button popovertarget="menu">Open</button>
<div id="menu" popover>…</div>
```

```css
.layer-popover {
  opacity: 1;
  transform: translateY(0);
  transition:
    opacity 240ms var(--cm-ease-out-cubic),
    transform 240ms var(--cm-ease-out-cubic),
    overlay 240ms allow-discrete,
    display 240ms allow-discrete;
}

.layer-popover:not(:popover-open) {
  opacity: 0;
  transform: translateY(6px);
}

@starting-style {
  .layer-popover:popover-open {
    opacity: 0;
    transform: translateY(6px);
  }
}
```

Read it as three states: `@starting-style` is where entry begins, the resting rule is where it lands, `:not(:popover-open)` is where exit goes. The browser also gives you light-dismiss, focus handling, and top-layer stacking for free — `popovertarget` needs no JavaScript at all, which is why the popover keeps working with JS disabled.

## Dialog: Same Recipe Plus Backdrop

`<dialog>` swaps `:popover-open` for `[open]`, adds `dialog.showModal()` / `dialog.close()` as the only JS, and animates its `::backdrop` with the identical pattern (background-color from transparent, `overlay`/`display` allow-discrete). Backdrop and panel animate on the same duration token — a backdrop that lingers after its dialog reads as a rendering bug.

Scale from 0.96, not smaller. Dialogs that zoom from 0.8 feel like toys; 4% is enough to read as arrival.

## Toast: The One That Still Needs JS

Toasts stack in normal flow (a fixed-position flex column), not the top layer, so `overlay` doesn't apply. Entry is still pure CSS — `@starting-style` fires on `appendChild`:

```css
@starting-style {
  .layer-toast { opacity: 0; transform: translateX(12px); }
}
.layer-toast.is-leaving { opacity: 0; transform: translateX(12px); }
```

Exit is one class plus one timeout (`is-leaving`, then `remove()` after the transition duration). The stack container carries `aria-live="polite"` so each toast announces itself once.

### Freeze Lifetimes on Hidden Tabs

A toast that expires while the tab is hidden was never seen. Track remaining lifetime per toast and pause the clock:

```javascript
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    timers.forEach(t => { clearTimeout(t.id); t.remaining -= performance.now() - t.startedAt; });
  } else {
    timers.forEach((t, toast) => {
      t.startedAt = performance.now();
      t.id = setTimeout(() => dismiss(toast), Math.max(0, t.remaining));
    });
  }
});
```

## Gotchas

- **`display` must be in the transition list.** Without `display … allow-discrete`, the element vanishes the instant it closes and the exit transition never renders. This is the mistake that makes people give up and reach for JS timing.
- **`overlay` must also be listed** for popover/dialog — otherwise the browser pulls the element out of the top layer at close, and it drops behind page content mid-exit.
- **`@starting-style` loses to `animation-fill-mode: both`.** Keyframe animations sit in a higher cascade origin; a `both` fill on the same element silently kills the entry transition. Use transitions for lifecycle, keyframes for ambient motion, and never both on one element.
- **Don't animate `::backdrop` blur.** `backdrop-filter` transitions repaint the full viewport every frame. Animate background-color opacity only.
- **Reduced motion:** `transition: none !important` on all four selectors (popover, dialog, backdrop, toast). State changes still happen — instantly.

## Combines With

| Pattern | Composition |
|---------|-------------|
| File review | Approval dialog gating the reviewed → approved state change |
| Streaming text | "Response complete" toast; stop-confirmation dialog |
| Terminal display | Command palette popover above a terminal panel |
| Stagger reveal | Toast stack entries are already staggered by arrival time — don't add artificial delay |
