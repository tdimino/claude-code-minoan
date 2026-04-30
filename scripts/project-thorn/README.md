# PROJECT THORN

A self-contained HTML artifact rendering Tom di Mino's Star Wars Galaxies character bio (Vorian Ducal / Jiff Gorda) as an in-universe Imperial Intelligence chat terminal — receiving an encrypted transmission from a Bothan informant named Ora.

## What this is

The original bio (preserved at `~/.claude/userModels/tom/archive/forums/swg-vorian-ducal-bio.md`) was written ~2003–2005 as in-character roleplay text on the SWG forums — structured as a chat log of dialogue lines, emotes, system messages, and narrative monologue spoken by an NPC Bothan spy.

This page animates that text the way it was originally consumed: as live text appearing in a spatial-chat window, one line at a time, rendered through the visual conventions of an Imperial Intelligence datapad.

## Open it

```bash
open index.html
```

That's it. No build step, no dependencies, no server. Single self-contained HTML file with inlined CSS and JS. Total size: ~50 KB + one ~80 KB Bothan portrait.

## Design direction

**Bloomberg Terminal × Imperial CRT.** Dense edge-to-edge data layout, single-pixel borders, monospace typography, green phosphor with red-for-classified accents. Reference: `creative-arsenal.md` Bloomberg Terminal archetype + `text-animation-catalog.md` typewriter spec (240ms / 46ms steps).

| Layer | Role |
|-------|------|
| WebGL/CSS atmosphere | scanlines, vignette, ambient glow, subtle flicker |
| Chrome | Bothan portrait + sigil + role/ops counters, pulsing PROJECT THORN classification |
| Status strip | asset metadata (cover, origin, handler, cell, status) — Bloomberg-dense |
| Transcript | per-character typewriter reveal, color-coded line types |
| Ticker (right) | scrolling Imperial telemetry: signal, encrypt, frequency, intercepts |
| Prompt | terminal cursor that never resolves (you can't reply to a Bothan) |

## Line types

The transmission distinguishes seven types via color and prefix:

| Type | Color | Prefix | Used for |
|------|-------|--------|----------|
| `system` | dim green | `>>>` | terminal status messages |
| `dialogue` | bright green | speaker tag | Ora's spoken lines |
| `emote` | dim green italic | `*` | Ora's actions ("strokes his beard") |
| `action` | cyan | `→` | player actions ("you raise an eyebrow") |
| `credit` | red bold | `▮` | credit transfers |
| `narrative` | green | speaker tag | long monologue paragraphs |
| `interrupt` / `signal-lost` | red | `▮ ` | the line being severed mid-sentence |

Inline tokens within text:
- `§Name§` → person tooltip (hover for backstory: Vorian Ducal, Jiff Gorda, Cotla, Fenri)
- `¤Project Thorn¤` → red classified marker with stamp on hover

## Controls

| Key | Button | Action |
|-----|--------|--------|
| `R` | ↺ REPLAY | Restart transmission from beginning (reload, preserves VHS/log state) |
| `V` | ▒ VHS | Toggle chromatic aberration + heavy scanlines (analog degradation) |
| `SPC` | ⏭ SKIP | Reveal full transcript instantly + trigger SIGNAL LOST |
| `L` | ⟫ LOG | Toggle the SESSION LOG debug panel |

The keyboard handler ignores modifier keys (Cmd+R reload, Cmd+L address bar, etc.) so browser shortcuts still work normally.

## Architecture notes

The animation is **CSS-driven, not JS-driven**. All transmission lines are pre-rendered in HTML. JavaScript walks each `[data-text]` node, wraps each character in a `<span class="char">` with a calculated `--d` (animation-delay) custom property, and schedules the line to flip from `display: none` (`pre-reveal`) to `display: grid` at its cumulative time via `setTimeout`.

This means:
- **No async chains in the hot path.** Browser layout drives the animation, not a JS loop.
- **Reduced motion fallback works.** The reduced-motion media query removes the animation; the reduced-motion JS branch un-hides all `pre-reveal` lines immediately so the transcript isn't blank.
- **SKIP cancels in-flight reveal timers.** Tracked in a `revealTimers[]` array so `signal-lost` doesn't fire twice.
- **REPLAY does a full page reload.** CSS `animation-delay` timelines can't be re-anchored mid-flight cleanly. VHS and log state are preserved via `sessionStorage`.

## Status

Self-contained, ships as one file. Built, reviewed by `/codex-orchestrator` (logic) and `/gemini-claude-resonance` (visual). Plan file at `~/.claude/plans/2026-04-29-project-thorn-swg-bothan-spy-chat-terminal.md`.

## Related

- Original bio: `~/.claude/userModels/tom/archive/forums/swg-vorian-ducal-bio.md`
- SWG character dossier: `~/.claude/userModels/tom/star-wars-roleplay.md`
- Forum context: `~/.claude/userModels/tom/forums-pnutmaster.md`
