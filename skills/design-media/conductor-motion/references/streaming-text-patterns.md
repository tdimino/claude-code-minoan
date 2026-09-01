# Streaming Text Patterns

The AI-response simulation: text arrives in chunks under a blinking cursor, the way an LLM answer streams into a chat panel. This is the dominant product-demo pattern of the AI era — and the one most often built wrong, because streaming breaks three things at once: scroll position, layout stability, and screen-reader behavior.

## Timing Constants (medium pacing)

```
FLUSH_MS         = 90ms   (interval between chunk flushes)
CHARS_PER_FLUSH  = 7      (minimum chars per flush, extended to word boundary)
THINKING_MS      = 700ms  (status shows "thinking" before first token)
CURSOR_BLINK     = 530ms  (step-end, matches typewriter patterns)
```

## Chunk Flushing, Not Per-Character Typing

The typewriter pattern types character by character because it simulates a human. Streaming simulates a model — models emit tokens in bursts, and per-character rendering reflows mid-word so line wraps shimmer as words break and re-break.

Buffer to word boundaries:

```javascript
let next = Math.min(pos + CHARS_PER_FLUSH, para.length);
while (next < para.length && para[next] !== ' ') next += 1;
p.textContent = para.slice(0, next);
```

Each flush lands a whole word (or several). Line wrapping only ever moves forward. ~90ms flushes read as "fast model," 150ms+ as "deliberate" — scale with the pacing multiplier like every other timing constant.

## Scroll Anchoring

Two rules, split across container and content:

```css
.stream-messages { overflow-y: auto; overflow-anchor: auto; }
.msg-assistant   { overflow-anchor: none; }
```

The container keeps the browser's native scroll anchoring; the growing message opts out so browser anchoring never fights programmatic pinning. Then pin manually — but only when the reader is already at the bottom:

```javascript
function isPinned() {
  return el.scrollHeight - el.scrollTop - el.clientHeight < 40;
}
const wasPinned = isPinned();
p.textContent = para.slice(0, next);
if (wasPinned) el.scrollTop = el.scrollHeight;
```

Read pinned-state *before* the write, apply after. A reader who scrolled up to re-read is never yanked back down — the single most common streaming-UI failure.

## Screen Readers: Announce Completion, Not Chunks

`aria-live` on the streaming container narrates every flush — a screen reader user hears the response stutter out fragment by fragment. Instead:

```html
<span class="visually-hidden" aria-live="polite" id="stream-announce"></span>
```

```javascript
announceEl.textContent = 'Response complete. ' + wordCount(totalText) + ' words.';
```

One polite announcement when the stream ends (or stops). `polite`, never `assertive` — assertive interrupts whatever the reader is in the middle of hearing.

## Cursor Through Pauses

The cursor blinks continuously — including during the thinking phase and mid-stream pauses. A cursor that stops blinking reads as a hang; a blinking cursor over still text reads as "working." Same `blink 530ms step-end` keyframe as the typewriter patterns, `aria-hidden="true"`, removed when the paragraph completes.

## Stop and Regenerate

Streaming interfaces need an interrupt affordance — demos included, because viewers notice its absence:

```
idle ──▶ thinking ──▶ streaming ──▶ done
                          │
                        stop ──▶ idle ("stopped")
```

One button, relabeled by state (`Stop` while running, `Regenerate` otherwise). Stopping halts mid-word and leaves the partial text standing — that's what real streams do.

## Static Markup Is the Source

The template ships the *finished* response in markup; JS captures it, clears the container, and streams it back:

```javascript
const paragraphs = Array.from(responseEl.querySelectorAll('p')).map(p => p.textContent);
```

This makes no-JS and reduced-motion cases free — the final state is already there. Reduced motion skips streaming entirely and renders all paragraphs at once.

## Visibility

Pause between flushes while `document.hidden`, resume where the stream left off. Streaming to a hidden tab wastes cycles and means the viewer returns to a finished animation they never saw.

## Combines With

| Pattern | Composition |
|---------|-------------|
| Terminal display | Stream into a terminal chrome instead of a chat bubble — status typing above, streamed output below |
| Progress simulation | Token/word counter in the footer doubles as the progress signal |
| File review | Tool-call rows (file scanned → finding) interleaved between streamed paragraphs |
| Top layer | "Response complete" toast on finish |
