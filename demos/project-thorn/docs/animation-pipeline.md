# Animation Pipeline

## Aurebesh Decrypt

Characters render in three phases:

1. **Fill**: Aurebesh glyphs appear via `@font-face` at `FILL_MS` (10ms/char)
2. **Scramble**: `SCRAMBLE_FRAMES` (3) frames of random Aurebesh substitution at `SCRAMBLE_FRAME_MS` (45ms/frame)
3. **Decrypt**: Final Latin character revealed at `DECRYPT_MS` (28ms/char)

Each character starts as a `<span class="char">` with `opacity: 0` and `font-family: Aurebesh`. The fill phase adds `.filled` (opacity 1). Scramble adds `.scrambling` with random Aurebesh codepoints. Decrypt adds `.decrypted` and swaps `font-family` to Departure Mono.

## Block Transitions

Transcript lines are grouped by `data-block` attribute (blocks 1–9). Animation processes one block at a time. Inter-block pauses create dramatic rhythm:

| Block | Pause (ms) | Content |
|-------|-----------|---------|
| 1 | 200 | System boot messages |
| 2 | 400 | TRANSMISSION BEGINS separator |
| 3 | 600 | First spoken line |
| 4 | 400 | Emote + dialogue |
| 5 | 600 | Credit transfer |
| 6 | 800 | Cover name reveal |
| 7 | 1400 | Monologue (longest pause—narrative weight) |
| 8 | 200 | Interrupt |
| 9 | — | SIGNAL LOST (terminal state) |

## State Machine

```
idle → running → done
  ↑                │
  └── replay() ────┘
```

Within `running`, per block:
```
fill frontier advances → scramble timers fire → decrypt frontier advances → block complete → pause → next block
```

## Inline Tokens

Recognized during `buildAnimation()` character wrapping:

| Token | Rendered As | Behavior |
|-------|------------|----------|
| `§Name§` | `<span class="person" data-tip="...">` | Underline appears only after `.decoded` added |
| `¤Text¤` | `<span class="thorn" data-tip="...">` | Red classified marker, stamp on hover |
| `¶` | `<br class="para-break">` | Visible paragraph break in Block 7 monologue |

## Controls

| Key | Button | Action |
|-----|--------|--------|
| `R` | RE-DECRYPT | Re-encrypt all chars, replay from block 0 |
| `V` | DEGRADE | Chromatic aberration + heavy scanlines |
| `Space` | BURST | Instant-reveal everything, jump to SIGNAL LOST |
| `L` | TRACE | Signal-trace diagnostic log overlay |
| `M` | AUDIO | Mute/unmute (persists via localStorage) |

## Reduced Motion

`prefers-reduced-motion: reduce` skips the entire animation pipeline. All text reveals immediately in Latin script. Audio never initializes.
