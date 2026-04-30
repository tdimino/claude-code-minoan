# PROJECT THORN

A 2003-era Star Wars Galaxies character bio (Vorian Ducal / Jiff Gorda), animated as an Imperial Intelligence chat terminal receiving an encrypted transmission from a Bothan informant named Ora. Single self-contained HTML file.

## What this is

The original bio was written ~2003–2005 on the SWG forums as in-character roleplay text. Chat-log structure: dialogue, emotes, system messages, narrative monologue, the player tipping 6,000 Imperial credits to a Bothan spy on Tatooine.

This page performs that text the way it was originally consumed — live, one line at a time, in the spatial-chat window of an Imperial datapad.

## Open it

```bash
open index.html
```

No build, no server, no dependencies. ~52 KB index.html, 22 KB Departure Mono woff2, 22 KB Bothan seal PNG.

## Design

Bloomberg Terminal × Imperial CRT. Edge-to-edge data layout, single-pixel borders, monospace, green phosphor with red for classified.

| Layer | Role |
|-------|------|
| Atmosphere | Vignette, ambient glow, screen flicker. No global scanlines — they live only on the avatar. |
| Chrome | Bothan **seal** (two-tone phosphor on void), role/ops counters, pulsing PROJECT THORN classification |
| Status strip | Asset metadata (cover, origin, handler, cell, status) plus the live **intercept stream** |
| Transcript | Per-character typewriter reveal, color-coded line types |
| Ticker | Imperial telemetry on the right edge: signal, encrypt, frequency, intercepts |
| Prompt | Cursor that never resolves (you can't reply to a Bothan) |

### The intercept stream

The status strip's right cell logs what the Empire's surveillance system notices about the conversation. Each event says something the dialogue itself doesn't say:

- `BIO-SIG MATCH 99.7% · ORA VERIFIED`
- `CREDIT TX OBSERVED · 6,000 IC · ACK` (red)
- `CODENAME UTTERED · PROJECT THORN · MANDATORY LOG` (red)
- `COUNTERMEASURE DETECTED · UNKNOWN ORIGIN` — the moment Ora goes silent

Eighteen events, scheduled to absolute milliseconds from page load and aligned with the transcript's typewriter timing. Severity drives color: info green, warn amber, alert red.

## Line types

Seven types, each colored and prefixed for self-teaching:

| Type | Color | Prefix | Used for |
|------|-------|--------|----------|
| `system` | dim green | `>>>` | terminal status messages |
| `dialogue` | bright green | speaker tag | Ora's spoken lines |
| `emote` | dim green italic | `*` | Ora's actions ("strokes his beard") |
| `action` | cyan | `→` | player actions |
| `credit` | red | `▮` | credit transfers |
| `narrative` | green | speaker tag | long monologue paragraphs |
| `interrupt` / `signal-lost` | red | `▮` | the line being severed mid-sentence |

Inline tokens within text:

- `§Name§` → person tooltip with backstory (Vorian Ducal, Jiff Gorda, Cotla, Fenri)
- `¤Project Thorn¤` → red classified marker, stamp on hover

## Controls

In-universe labels. No museum placards on the relic.

| Key | Button | Action |
|-----|--------|--------|
| `R` | ↺ RE-DECRYPT | Re-decrypt the channel from the initial intercept (full reload, preserves DEGRADE/TRACE state) |
| `V` | ▒ DEGRADE | Apply analog feed degradation: chromatic aberration plus heavier scanlines |
| `SPC` | ⏭ BURST | Burst-decode the entire intercept, jump to SIGNAL LOST |
| `L` | ⟫ TRACE | Show the signal-trace diagnostic overlay |

Modifier keys (Cmd+R reload, Cmd+L address bar, etc.) pass through to the browser unchanged.

## Architecture

CSS-driven, not JS-driven. All transmission lines are pre-rendered in HTML. JavaScript walks each `[data-text]` node, wraps every character in a `<span class="char">` with a calculated `--d` (animation-delay) custom property, and schedules the line to flip from `display: none` to `display: grid` at its cumulative time via `setTimeout`.

- Browser layout drives the animation. No async chains in the hot path.
- Reduced motion handled inside `buildAnimation()`: if `prefers-reduced-motion: reduce`, lines never receive `pre-reveal`, timers are skipped, signal-lost styling applies immediately.
- BURST cancels in-flight reveal timers from the tracked `revealTimers[]` array, then un-hides all remaining `pre-reveal` lines. SIGNAL LOST fires once.
- RE-DECRYPT does a full page reload — CSS animation-delay timelines can't be re-anchored mid-flight cleanly. DEGRADE and TRACE state are preserved via `sessionStorage` with try/catch for Safari private mode.

## Fonts

- `DepartureMono-Regular.woff2` (Helena Zhang, SIL Open Font License) — bundled, see `DepartureMono-LICENSE.txt`
- Major Mono Display (Google Fonts, OFL) — loaded via `<link>` for the ORA name only
