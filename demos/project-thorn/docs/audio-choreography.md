# Audio Choreography

Three audio tracks layered via Web Audio API. Accents are not random—a cue table scores 19 moments to narrative progress.

## Tracks

| Track | File | Duration | Role |
|-------|------|----------|------|
| Base | `sfx-base.mp3` | 60s, loops | Persistent transmission hum—always on, survives SIGNAL LOST |
| Accent A | `sfx-accent-a.mp3` | 42s | Data stream bursts—fired at narrative cue points |
| Accent B | `sfx-accent-b.mp3` | 32s | Telemetry pings—fired at surveillance events |

## Volume Arc

The base volume follows a narrative contour:

```
0.08 (boot) → 0.15 (operational) → 0.19 (peak monologue) → 0.14 (pre-severance dip) → 0.05 (channel collapse) → 0.03 (signal lost, muffled through 200Hz lowpass sweep)
```

The base never stops—it degrades. After SIGNAL LOST, a lowpass filter sweeps from 2000Hz to 200Hz over 3 seconds, creating a muffled, distant hum.

## Cue Table (`AUDIO_CUES`)

Each entry fires an accent track at a specific block index and character-fraction threshold:

| Block | Fraction | Track | Volume | Narrative Moment |
|-------|----------|-------|--------|-----------------|
| 1 | 0.0 | B | 0.04 | Boot: telemetry handshake |
| 1 | 0.30 | A | 0.04 | Channel establishing |
| 3 | — | — | — | Silence: first words land clean |
| 5 | 0.10 | A | 0.10 | Credit transfer: data burst (loudest pre-monologue) |
| 5 | 0.60 | B | 0.05 | Transaction confirmation |
| 7 | 0.05 | A | 0.06 | Monologue begins |
| 7 | 0.15 | B | 0.04 | "Vorian Ducal" named |
| 7 | 0.30 | A | 0.08 | "Project Thorn" uttered (first hit) |
| 7 | 0.30 | B | 0.06 | "Project Thorn" uttered (second hit—double accent) |
| 7 | 0.40–0.55 | — | — | Silence: audience absorbs the mission objective |
| 7 | 0.60 | A | 0.07 | Assassination revealed |
| 7 | 0.75 | B | 0.04 | Pre-severance tension |
| 7 | 0.85 | — | — | Volume dip before cut |
| 8 | 0.0 | A | 0.12 | Alarm burst (peak volume) |
| 8 | 0.0 | — | — | `kill` command cuts all active sources |

## Terminal Command SFX

| Sound | Source | Trigger |
|-------|--------|---------|
| ACK beep | `01-scifi-computer-terminal-unfa.mp3` | Valid command recognized |
| DENY tone | Square-wave oscillator (220Hz → 160Hz) | Forbidden or unrecognized command |
| Dossier open | Ascending sine sweep (400→1200→800Hz) | Portrait click |
| Dossier close | Descending sine sweep (800→300Hz) | Close button or backdrop click |

## Scored Silence

Silence is intentional, not accidental:
- Block 3: first spoken words land without interference
- Block 7 fraction 0.40–0.55: audience processes "Project Thorn" mission objective after the double-hit accent
