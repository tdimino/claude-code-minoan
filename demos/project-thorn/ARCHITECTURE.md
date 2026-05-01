# ARCHITECTURE — PROJECT THORN

This document describes the structure of `index.html` and the reasoning behind it. It follows [matklad's ARCHITECTURE.md guidelines](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html): it tells you where to look, not what the code does.

Use this as a template guide. Swap the transcript content, audio cues, and visual identity to produce a different SW-themed terminal without touching the engine.

---

## Bird's Eye View

A single HTML file (2674 lines, ~98 KB) performing an Imperial Intelligence intercept of a Bothan informant. No build step, no bundler, no npm, no server required—`open index.html` is the full deployment pipeline.

Three systems share the file:

| System | Lines | Role |
|--------|-------|------|
| CSS atmosphere + chrome | 13–1253 | Visual identity: phosphor palette, CRT effects, layout, animation states |
| HTML transcript + chrome | 1255–1542 | Pre-rendered content: character data, dossier modal, terminal UI |
| JS engine | 1544–2648 | State machine, Aurebesh decrypt animation, Web Audio API, terminal commands |

The systems are coupled at DOM boundaries: CSS classes toggled by JS (`revealed`, `decrypted`, `signal-lost`, `vhs-on`), element IDs targeted by JS (`transcript`, `intercept-stream`, `dossier`, `prompt-input`), and `data-block`/`data-text` attributes on `<article>` elements that drive the animation engine.

---

## Codemap

Line ranges are verified against the 2674-line file.

### CSS — Head, Fonts, Variables (1–64)

`@font-face` declarations for Departure Mono (self-hosted woff2) and Aurebesh (self-hosted woff2). Google Fonts `<link>` for Major Mono Display (ORA name display only). `:root` block defines the entire color system and animation timing constants.

**Extension point**: all visual tuning lives here. See _Extension Points_ below.

### CSS — Atmosphere (80–126)

Four fixed-position overlays stacked via `z-index`: `.vignette` (radial + linear gradient edges), `.glow` (ambient green phosphor pulse), `.flicker` (opacity-step CRT flicker at 7s intervals), `.scanlines` (repeating-linear-gradient scanlines, multiply blend). The `.scanlines` element does not appear in the HTML—VHS mode is handled by a `body.vhs-on .scanlines` rule that regenerates the overlay at higher intensity (line 2655).

### CSS — Terminal Frame / Chrome (127–383)

`.terminal` is a CSS Grid container: `grid-template-areas` maps chrome, status, transcript+ticker, and prompt into a two-column layout (`1fr 200px`). The chrome header (`.chrome`) holds the portrait frame, sigil block (name/role/counters), classification title, and control buttons. Portrait frame receives `cursor: pointer` from JS at init; click triggers dossier open.

### CSS — Holographic Dossier Modal (384–622)

`<dialog>` element styled as a holographic datapad: `backdrop-filter: blur`, scan-line pseudo-elements, a `.dossier__sweep` animation on `::before`. Uses native `<dialog>` API (`showModal()`, `close()`). All dossier fields are static HTML—no JS writes to the dossier body.

### CSS — Live Log Panel (623–684)

`.log-panel` is a fixed-position overlay toggled by `body.log-visible`. Scrollable `#log-entries` receives one `div.log-entry` per JS log call. Three tag variants: `info`, `warn`, `alert`.

### CSS — Status Strip (685–793)

`.status` is a dense Bloomberg-style data row. Static fields (Asset, Cover, Origin, Handler, Cell, Status) rendered as `<dl>` cells. `#intercept-stream` is an inline flex container that receives event chips injected by JS on a pre-scored millisecond schedule.

### CSS — Transcript (794–959)

`.transcript` scrolls independently (`overflow-y: auto`). Each line is `.line` with a type modifier: `line--system`, `line--dialogue`, `line--emote`, `line--action`, `line--credit`, `line--narrative`, `line--interrupt`, `line--signal-lost`. Lines start with `.pre-reveal` (opacity 0, slight y-offset) and transition to `.revealed` when the animation engine reaches their block. Inline tokens: `.person` and `.thorn` gain underlines only after `.decoded` is added.

### CSS — Decrypt Animation (960–970)

Three animation states for `.char` spans: initial (Aurebesh glyph, no fill class), `.filled` (character present), `.decrypted` (Latin character revealed, color transition). `.scrambling` triggers a brief Aurebesh substitution. Underlines for `.person` and `.thorn` tokens are suppressed until `.decoded` is added to the element.

### CSS — Ticker (971–1014)

`.ticker` is the right-column aside (200px wide). `.ticker__inner` contains two identical sets of `<dl>` rows and animates upward via `@keyframes scroll-up` for a seamless telemetry loop. Halts on `body.signal-lost`.

### CSS — Prompt (1015–1096)

`.prompt` footer holds the `θ-7@imp-int:~$` sigil, `#prompt-input` text field, a key-hint span, and `#prompt-errors` for command output display. The prompt is always visible and interactive regardless of `state.phase`.

### CSS — Tooltips (1097–1124)

`.person` and `.thorn` elements display `data-tip` attribute content via CSS `::after` pseudo-elements on hover. Tooltips appear only after `.decoded` removes the `pointer-events: none` suppression.

### CSS — End-State / Signal Lost (1125–1179)

`body.signal-lost` rules: `.signal-flash` is a full-screen white flash element appended and removed by JS. Ticker animation pauses. `#signal-lost-marker` fades in. The base audio track degrades through a 200Hz lowpass filter—purely handled in JS, not CSS.

### CSS — Reduced Motion (1180–1192)

`@media (prefers-reduced-motion: reduce)`: all animations set to `none`/`0s`. JS reads this media query in `buildAnimation()` and skips the decrypt loop entirely, revealing all text immediately and disabling audio.

### CSS — Responsive (1193–1253)

Three breakpoints. At `≤1024px`: ticker hidden, grid collapses to single column, status strip gains horizontal scroll. At `≤768px`: chrome shrinks to 72px, title bar hidden, keyboard shortcut hints hidden, status strip hides cells 4+ (Handler, Cell, Status), dossier goes full-screen. At `≤480px`: chrome shrinks to 56px, controls become icon-only, timestamps hidden, prompt gets 44px touch targets.

---

### HTML — Atmosphere Overlays (1257–1260)

Three fixed divs: `.glow`, `.vignette`, `.flicker`. The `.scanlines` overlay is injected by VHS mode via CSS, not an HTML element.

### HTML — Terminal Grid (1261–1455)

`.terminal` div contains the four grid areas:

- `<header class="chrome">` (1264–1309): portrait frame, sigil, controls
- `<dl class="status">` (1312–1323): static fields + `#intercept-stream`
- `<main class="transcript" id="transcript">` (1326–1406): all transcript lines
- `<aside class="ticker">` (1409–1445): telemetry rows (duplicated for loop)
- `<footer class="prompt">` (1448–1453): input + error output

### HTML — Transcript Blocks (1328–1405)

Nine blocks of `<article class="line line--{type}" data-block="{n}">` elements. Each line carries `data-text="{content}"` on its `.line__body` child—the raw string that `buildAnimation()` wraps into `<span class="char">` elements. Block numbers:

| Block | Lines | Content |
|-------|-------|---------|
| 1 | 1328–1347 | System boot: channel establish, key exchange, bio-sig verify |
| 2 | 1348–1351 | Line break (separator) |
| 3 | 1352–1356 | Ora's first spoken line |
| 4 | 1357–1366 | Glance-over-shoulder emote + first dialogue |
| 5 | 1367–1371 | Credit transfer (6,000 IC) |
| 6 | 1372–1391 | Cover name revealed, player action, Ora's beard-stroke setup |
| 7 | 1392–1396 | Ora's full monologue (`¶` paragraph breaks in `data-text`) |
| 8 | 1397–1401 | Interrupt / transmission cut mid-sentence |
| 9 | 1402–1405 | SIGNAL LOST marker (`#signal-lost-marker`) |

Inline token syntax in `data-text`:
- `§Name§` — wraps in `<span class="person" data-tip="...">` with tooltip
- `¤Text¤` — wraps in `<span class="thorn" data-tip="...">` (red classified marker)
- `¶` — becomes a visible `<br>` paragraph break inside narrative blocks

### HTML — Dossier Dialog (1458–1536)

`<dialog id="dossier">` with six sections (Identity, Operational History, Financial, Contact Profile, Assessment, Classification). All fields are static. The `.dossier__sweep` animation runs on `::before` via CSS. Open/close wired to portrait click and `#dossier-close` button in JS (lines 2565–2591).

### HTML — Live Log Panel (1538–1542)

`<div id="log-panel">` fixed overlay with `#log-entries` container. `toggleLog()` in JS adds/removes `body.log-visible`.

---

### JS — State Machine + Animation Engine (1544–2351)

**Live logger** (1548–1569): `log(tag, msg)` appends timestamped entries to `#log-entries` and `console.log`. Tags: `init`, `state`, `user`, `audio`, `alert`.

**Tooltips** (1571–1579): `TOOLTIPS` object maps person names to dossier-style descriptions. Used by `buildAnimation()` when wrapping `§Name§` tokens.

**Intercept log** (1581–1630): `INTERCEPT_LOG` — 18 surveillance events each with `atMs`, `text`, `sev`. `scheduleInterceptLog()` uses `setTimeout` against this array. `flushInterceptLog()` shows all remaining events immediately on BURST.

**Aurebesh decrypt engine** (1632–1670): constants (`FILL_MS=10`, `DECRYPT_MS=28`, `SCRAMBLE_FRAMES=3`, `SCRAMBLE_FRAME_MS=45`) and per-block pause table (`BLOCK_PAUSE`). Scroll-tracking listener on `#transcript`.

**State object** (1655–1669):

```js
const state = {
  blocks: [],          // array of block descriptors built by buildAnimation()
  charSpans: [],       // flat array of all <span class="char"> elements
  charMeta: [],        // parallel array: { targetChar, isLetter, blockIdx }
  fillFrontier: 0,     // index of next char to fill (Aurebesh)
  decryptFrontier: 0,  // index of next char to decrypt (Latin)
  fillStartTime: 0,    // performance.now() when fill phase began
  decryptStartTime: 0, // performance.now() when decrypt phase began
  blockIdx: 0,
  phase: 'idle',       // 'idle' | 'running' | 'done'
  rafId: null,
  blockTimerId: null,
  scrambleTimers: [],
  lineRevealTimers: [],
};
```

`state.phase` transitions: `idle` (initial) → `running` (set by `buildAnimation()` at first `beginBlock` call) → `done` (set when all blocks exhaust, or immediately by `skipAll()`). State never mutates outside the animation loop or control functions.

**Audio engine** (1672–1955): see JS: Audio Engine section below.

**`buildAnimation()`** (2137–2206): walks all `.line` elements, groups by `data-block`, parses `data-text` into `<span class="char">` elements (with `§...§` and `¤...¤` token handling), populates `state.blocks`, `state.charSpans`, `state.charMeta`. Checks `prefers-reduced-motion`—if reduced, calls `revealAllImmediate()` and returns without starting the RAF loop.

**`beginBlock(blockIdx)`** (2207–2238): entry point for each block. Staggered `setTimeout` reveals `.line` elements (80ms/line). Computes fill headstart (30% of block char count). Fires `audioCueEngine.onBlockStart()`. Starts RAF loop if not already running.

**`animationTick(timestamp)`** (2240–2339): the hot path. On each frame: advances `fillFrontier` based on elapsed time and `FILL_MS`, advances `decryptFrontier` similarly. When a char transitions fill→scramble→decrypt, schedules scramble `setTimeout` calls against `state.scrambleTimers`. When both frontiers reach block end: cancels RAF, schedules next block via `setTimeout(beginBlock, BLOCK_PAUSE[n])`. Calls `audioCueEngine.tick()` every frame.

**`revealAllImmediate()`** (2310–2350): sets all chars to target content, removes animation classes, adds `.decoded` to `.person`/`.thorn` elements. Used by BURST and reduced-motion path.

### JS — Audio Engine (1672–1955)

Web Audio API object (`audio`), lazily initialized on first user gesture. Three tracks:

| Track | Loaded from | Role |
|-------|-------------|------|
| Base | `sfx-base.mp3` | Persistent transmission hum, looped. Volume arc follows narrative. |
| Accent A | `sfx-accent-a.mp3` | Data stream bursts. Fired at cue table moments. |
| Accent B | `sfx-accent-b.mp3` | Telemetry pings. Fired at cue table moments. |

Signal chain: `AudioContext` → `master GainNode` → `BiquadFilterNode` (lowpass, cutoff starts at 20000Hz, sweeps to 200Hz on signal lost) → `destination`. Each accent playback creates a new `AudioBufferSourceNode` and its own `GainNode`; base track reuses a single source with looping.

Key methods:

- `audio.init()` — fetches and decodes all three buffers, wires the signal chain. Returns a Promise. Called once on first user gesture if `state.phase === 'running'`.
- `audio.startBase(fadeSeconds)` — starts the looping base track with a volume fade-in.
- `audio.fireAccent(which, vol, jitter)` — fires Accent A or B after a random jitter delay (up to `jitter` ms).
- `audio.setBaseVol(target, fadeMs)` — ramps base gain to `target` over `fadeMs` using `linearRampToValueAtTime`.
- `audio.onSignalLost(immediate)` — sweeps lowpass from 20kHz → 200Hz over 3s, ramps base volume to 0.03. If `immediate` (BURST), collapse happens instantly.
- `audio.playTerminalAck()` — plays a 0.4s slice of `audio-candidates/01-scifi-computer-terminal-unfa.mp3` at a random offset. Valid command feedback.
- `audio.playTerminalDeny()` — synthesizes a 220Hz → 160Hz square-wave double-beep via `OscillatorNode`. Denied/unrecognized command feedback.
- `audio.playDossierOpen()` — ascending sine sweep (400 → 1200 → 800Hz, 0.6s).
- `audio.playDossierClose()` — descending sine sweep (800 → 300Hz, 0.4s).
- `audio.toggleMute()` — suspends/resumes `AudioContext`, persists to `localStorage('thorn-muted')`.

### JS — Cue-Based Audio Choreography (1957–2072)

**`AUDIO_CUES`** (1959–1979): 19 scored moments, each an object:

```js
{ id, blockIdx, trigger, accent, vol, jitter, baseVol, baseFade }
```

`trigger` values: `'blockStart'`, `'blockEnd'`, `'charFraction:0.33'` (float 0–1 of block chars revealed), `'afterMs:2000'` (wall-clock ms after block start).

**`audioCueEngine`** object (1981–2072): tracks which cues have fired (`fired` Set), current block elapsed time, and char fraction. `onBlockStart(idx)` fires blockStart cues. `tick(blockIdx, charFraction)` called every animation frame—evaluates charFraction and afterMs triggers. `reset()` clears the fired set on replay.

### JS — Intercept Stream + Dossier + Controls (2073–2461)

**`scheduleInterceptLog()`** (2073–2079): iterates `INTERCEPT_LOG`, schedules `renderInterceptEvent()` via `setTimeout` for each entry. All timer IDs pushed to `interceptTimers[]` for cancellation on replay.

**`flushInterceptLog()`** (2080–2088): clears all pending timers, renders all unseen events immediately. Called by `skipAll()`.

**`skipAll()`** (2354–2372): BURST handler. Sets `state.phase = 'done'`, cancels RAF and all pending timers, calls `revealAllImmediate()`, `flushInterceptLog()`, `triggerSignalLost(true)`.

**`triggerSignalLost(immediate)`** (2374–2383): adds `body.signal-lost`, appends and removes `.signal-flash`, calls `audio.onSignalLost()`.

**`replay()`** (2385–2460): RE-DECRYPT handler. Cancels all timers, re-encrypts all chars back to Aurebesh, removes `.revealed`/`.decoded` classes, removes `signal-lost` state, clears intercept stream, resets audio and cue engine, calls `beginBlock(0)`.

**`toggleVHS()`** (2453–2460): toggles `body.vhs-on`. CSS handles the visual effect.

**`toggleLog()`** (2443–2451): toggles `body.log-visible`. CSS handles panel visibility.

Dossier wiring (2564–2591): portrait click → `dossier.showModal()` + `audio.playDossierOpen()`. Close button + backdrop click → `dossier.close()` + `audio.playDossierClose()`.

### JS — Terminal Command System (2462–2554)

**`TERMINAL_CMDS`** (2464–2490): plain object mapping command strings to response strings. Multi-line responses use `\n`. Supports exact matches (`'cat intercept.log'`) and prefix-only matches (`'ping'` catches `ping chimera`).

**`TERMINAL_FALLBACK`** (2491–2505): 13 atmospheric error strings for unrecognized commands. Randomly selected, never repeats consecutively.

**`DENIED_CMDS`** (2522): `Set(['sudo','rm','kill','exit','decrypt','man'])`. Matched commands play `audio.playTerminalDeny()` even though they return a response (not undefined).

Input event on `#prompt-input` (2511–2553): Enter key → normalize to lowercase → look up in `TERMINAL_CMDS` → render output block in `#prompt-errors` → play ack or deny audio. `e.stopPropagation()` on all key events prevents global keydown from intercepting while focused.

### JS — Init (2556–2647)

Button event bindings (2558–2562). Dossier open/close wiring (2564–2591). Global keydown handler (2593–2608): R → `replay()`, Space → `skipAll()`, V → `toggleVHS()`, L → `toggleLog()`, M → `audio.toggleMute()`. Guards: skips if target is input/textarea/contenteditable, skips if modifier key held, skips Space when a button has focus (prevents double-fire).

Session state restore (2611–2623): reads `sessionStorage` for VHS/log state persisted before replay. `audio.loadMuteState()` (2625) reads `localStorage`.

`buildAnimation()` (2628) and `scheduleInterceptLog()` (2629) called in sequence. Audio gate (2632–2646): registers one-shot click+keydown listeners that call `audio.init().then(startBase)` on first user gesture, then remove themselves.

---

## State Machine

```
             ┌─────────┐
     init    │  idle   │
   ─────────►│         │
             └────┬────┘
                  │ buildAnimation() calls beginBlock(0)
                  ▼
             ┌─────────┐
             │ running │◄──── beginBlock(n+1) after BLOCK_PAUSE[n]
             │         │
             └────┬────┘
                  │ blockIdx >= blocks.length
                  │ OR skipAll()
                  ▼
             ┌─────────┐
             │  done   │
             └─────────┘
```

RE-DECRYPT resets to `idle` and calls `beginBlock(0)` → `running`.

Within `running`, the animation tick runs a sub-state per block:

```
fill frontier advances → scramble timers fire → decrypt frontier advances → block complete → pause → next block
```

The RAF loop runs only when `state.rafId !== null`. `beginBlock` starts it; block completion cancels it and restarts it after the inter-block pause.

---

## Extension Points

These are the four surfaces to modify when building a new terminal from this template.

### 1. Color System — `:root` (lines 36–64)

All colors and timing constants. Swap the phosphor palette here to change from Imperial green to Rebel amber, corporate blue, etc.

```css
:root {
  --bg: #050a07;
  --amber: #7ce5a0;      /* primary phosphor */
  --red: #ff3030;        /* classified / alert */
  --cyan: #6ad8ff;       /* action lines */
  --char-stagger: 22ms;  /* animation feel */
}
```

### 2. Transcript Content — HTML `data-text` nodes (lines 1328–1405)

Each `<article class="line line--{type}" data-block="{n}">` with a `<div class="line__body" data-text="...">` is one content line. Change the `data-text` values, `line--{type}` class, and `data-block` grouping to replace the intercept narrative entirely.

`data-block` numbers must be sequential starting at 1. The `BLOCK_PAUSE` table in JS (line 1640) maps block numbers to inter-block delays—add entries for new blocks.

Token syntax:
- `§Person Name§` → tooltip-enabled person span (add entry to `TOOLTIPS` at line 1571)
- `¤Classified Text¤` → red classified marker
- `¶` → paragraph break in narrative blocks

### 3. Audio Cue Score — `AUDIO_CUES` (lines 1959–1979)

Each entry fires an accent track at a specific narrative moment. Adjust `blockIdx`, `trigger`, `vol`, and `baseVol` to rescore the audio for different content. Add entries freely—the engine handles duplicates and skipped blocks. The three audio files (`sfx-base.mp3`, `sfx-accent-a.mp3`, `sfx-accent-b.mp3`) are the only source material; swap them for a different sonic register.

### 4. Terminal Commands — `TERMINAL_CMDS` (lines 2464–2490)

Plain object—add key/value pairs. Multi-line responses use `\n`. Prefix matching is automatic: if `cmd.split(' ')[0]` matches a key, that response fires. Add entries to `DENIED_CMDS` (line 2522) for commands that should play the deny sound.

### 5. Dossier Modal — `<dialog id="dossier">` (lines 1458–1536)

Replace the `<section>` content inside `.dossier__body` to change the asset profile. The modal frame, sweep animation, scan-line overlay, and open/close audio are all reusable without modification.

---

## Invariants

- **No build step.** No bundler, no transpiler, no npm. The file runs directly from disk in any modern browser.
- **All assets by relative path.** `bothan-ora_image_0_0.jpg`, `DepartureMono-Regular.woff2`, `Aurebesh.woff2`, `sfx-*.mp3`—all siblings of `index.html`. Moving the file requires moving all assets with it.
- **`AudioContext` created lazily.** Browser autoplay policy requires a user gesture before audio can start. `audio.init()` is called inside a one-shot click/keydown listener. The listener removes itself after firing.
- **`prefers-reduced-motion` disables animation and audio.** `buildAnimation()` checks `window.matchMedia('(prefers-reduced-motion: reduce)')`. If matched: all chars revealed immediately, audio never initialized.
- **State never mutates outside the animation loop or control functions.** `state.phase`, `state.fillFrontier`, `state.decryptFrontier` are only written by `beginBlock`, `animationTick`, `skipAll`, and `replay`. No event listener writes to state directly.
- **JS is wrapped in an IIFE.** `(function() { 'use strict'; ... })()` — no globals leaked.
- **Mute state persists across page loads.** `localStorage('thorn-muted')`. VHS and log-panel state persist across RE-DECRYPT replays via `sessionStorage` (cleared after reading).

---

## Key Files Reference

| File | Size | Purpose |
|------|------|---------|
| `index.html` | 98 KB | The entire terminal—CSS, HTML, JS |
| `DepartureMono-Regular.woff2` | 22 KB | Period-correct CRT monospace (Helena Zhang, SIL OFL) |
| `Aurebesh.woff2` | 12 KB | Star Wars script glyph font for decrypt animation |
| `bothan-ora_image_0_0.jpg` | 650 KB | Bothan informant portrait (painterly, AI-generated) |
| `bothan-ora-dossier_image_0_0.jpg` | 739 KB | Dossier portrait variant |
| `bothan-ora-seal.png` | 20 KB | Bothan seal sigil |
| `sfx-base.mp3` | 505 KB | 60s looping transmission hum (Freesound CC0/CC-BY) |
| `sfx-accent-a.mp3` | 307 KB | 42s data stream bursts |
| `sfx-accent-b.mp3` | 281 KB | 32s telemetry pings |
| `audio-candidates/01-scifi-computer-terminal-unfa.mp3` | 71 KB | Terminal command ACK sound (Freesound CC0) |
| `imperial-favicon/` | ~23 KB | Imperial cog favicon (ICO + 32px + 48px PNG) |
| `DepartureMono-LICENSE.txt` | 4 KB | SIL OFL license for Departure Mono |
| `audio-candidates/` | — | Candidate audio files from Freesound research phase |
| `_*.png`, `preview-*.png`, `screenshot-*.png` | — | Development screenshots and preview images (not served) |
| `README.md` | 10 KB | User-facing documentation |
| `ARCHITECTURE.md` | this file | Developer orientation |

---

## Where to Start

- **Swap the narrative**: edit `data-text` attributes in `index.html` lines 1328–1405
- **Rescore audio**: edit `AUDIO_CUES` at line 1959
- **Change the color palette**: edit `:root` at line 36
- **Add terminal commands**: edit `TERMINAL_CMDS` at line 2464
- **Understand the animation loop**: read `beginBlock` (2207) → `animationTick` (2240)
- **Understand audio initialization**: read `audio.init` (line 1722) → `audio.startBase` (line 1796)
- **Debug what's happening**: press `L` to open the TRACE panel (live log of all state transitions, user actions, and audio events)
