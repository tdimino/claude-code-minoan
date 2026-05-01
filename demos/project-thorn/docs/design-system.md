# Design System

Bloomberg Terminal meets Imperial CRT. Edge-to-edge data, single-pixel borders, monospace, amber phosphor with red for classified.

## Color System

All colors defined in `:root` (lines 36–64 of `index.html`). Never hardcode hex values—use the variables.

### Core Palette

| Variable | Value | Role |
|----------|-------|------|
| `--bg` | `#050a07` | Terminal background |
| `--surface` | `#0a1410` | Panel/header/prompt background |
| `--amber` | `#7ce5a0` | Primary phosphor—dialogue, names, controls |
| `--amber-dim` | `#4a9968` | Secondary text—emotes, metadata |
| `--amber-mute` | `#2e7050` | Tertiary—prefixes, labels |
| `--amber-faint` | `#1a4a35` | Quaternary—timestamps, rules |
| `--red` | `#ff3030` | Classified, alerts, credit lines |
| `--red-dim` | `#cc2828` | Red prefix markers |
| `--cyan` | `#6ad8ff` | Action lines, dossier accent |
| `--cyan-dim` | `#4a98b8` | Action prefixes |

### Border System

| Variable | Value | Usage |
|----------|-------|-------|
| `--rule` | `rgba(92, 255, 144, 0.12)` | Subtle internal borders |
| `--rule-bright` | `rgba(92, 255, 144, 0.25)` | Section boundaries |

## Typography

| Font | Source | Usage |
|------|--------|-------|
| Departure Mono | Self-hosted woff2 (22 KB) | All terminal text, monospace base |
| Aurebesh | Self-hosted woff2 (12 KB) | Encrypted text during decrypt animation |
| Major Mono Display | Google Fonts `<link>` | ORA name display only |

## Layer Model

Six visual layers from back to front:

| Layer | z-index | Elements |
|-------|---------|----------|
| Atmosphere | 1–5 | `.vignette`, `.glow`, `.flicker`, `.scanlines` |
| Terminal | 10 | `.terminal` grid |
| Tooltips | 200 | `.person::after`, `.thorn::after`, `.chrome__btn::after` |
| Log panel | 150 | `#log-panel` |
| Dossier | 300 | `<dialog id="dossier">` |
| Signal flash | 9999 | `.signal-flash` (transient) |

## Atmosphere Effects

Four fixed-position overlays create CRT texture:

| Effect | Technique |
|--------|-----------|
| Vignette | Radial + linear gradient edges |
| Glow | Pulsing green ambient (4s cycle) |
| Flicker | Opacity step animation (7s, irregular) |
| Scanlines | 2px repeating-linear-gradient, multiply blend |

VHS mode (`body.vhs-on`) activates chromatic aberration via CSS `filter` and intensifies scanlines.

## Responsive Tiers

| Breakpoint | Changes |
|------------|---------|
| ≤1024px | Ticker hidden, single column, status strip scrollable |
| ≤768px | Chrome 72px, title hidden, controls prioritized, status cells 4+ hidden |
| ≤480px | Chrome 56px, icon-only controls, timestamps hidden, 44px touch targets |

## Status Strip Cells

Bloomberg-style dense data row. Cells progressively hide at smaller viewports:

| Cell | Always Visible | Hidden at |
|------|---------------|-----------|
| Asset | yes | — |
| Cover | yes | — |
| Origin | yes | ≤480px |
| Handler | no | ≤768px |
| Cell | no | ≤768px |
| Status | no | ≤768px |
| Intercept | yes | — |
