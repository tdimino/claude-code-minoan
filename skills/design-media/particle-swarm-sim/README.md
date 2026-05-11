# particle-swarm-sim

Generate massive particle swarm simulations (20,000+) with a clean separation of concerns: a **sandbox runtime** handles Three.js rendering, camera, input, gesture recognition, and security — the AI writes only a **behavior function body** that positions and colors particles per frame.

Distilled from [particles.casberry.in](https://particles.casberry.in/).

## Why This Exists

Most creative coding tools require the AI to generate complete applications — scene setup, rendering pipeline, input handling, animation loop, and the actual creative logic all interleaved in one file. This makes the output fragile, hard to iterate, and impossible to validate independently.

This skill inverts that: the runtime is pre-built and battle-tested. The AI generates only a function body — pure math that maps particle index to position and color. The runtime handles everything else. The function body is sandboxed: no DOM access, no network, no prototype manipulation. If it throws, the runtime catches it and shows the error. If it produces NaN, the runtime skips the bad values.

## Two Modes

### Mode: sandbox

Generate the complete host runtime HTML.

```
/particle-swarm-sim --mode sandbox dark theme, 30K particles, gesture controls
```

Output: a self-contained HTML file with Three.js scene, camera controls (mouse/touch/gesture), code injection textarea, security validator, dynamic controls UI, and HUD.

### Mode: sim

Generate a behavior function body from a creative concept.

```
/particle-swarm-sim --mode sim aurora borealis — curtains of light along magnetic field lines
```

Output: a JS function body that follows the sandbox API contract. Paste it into the sandbox's code editor, or inject it programmatically.

## The API Contract

The function body receives these variables as named parameters:

| Variable | Type | Access |
|----------|------|--------|
| `i` | Integer | Read — particle index (0 to count-1) |
| `count` | Integer | Read — total particles |
| `time` | Float | Read — simulation time in seconds |
| `THREE` | Object | Read — safe subset (Vector3, Color, MathUtils) |
| `target` | THREE.Vector3 | Write — `target.set(x, y, z)` |
| `color` | THREE.Color | Write — `color.setHSL(h, s, l)` |

Helpers: `addControl(id, label, min, max, initial)`, `setInfo(title, desc)`, `annotate(id, x, y, z, label)`.

## Quick Start

```bash
# Generate a sandbox runtime
python3 scripts/swarm_generator.py --mode sandbox --particles 25000 --gesture --output sandbox.html

# Generate a sim from preset
python3 scripts/swarm_generator.py --mode sim --preset galaxy-spiral --output galaxy.js

# Validate a sim function body
python3 scripts/validate_sim.py galaxy.js

# Validate a sandbox HTML
python3 scripts/validate_sandbox.py sandbox.html

# List available presets
python3 scripts/swarm_generator.py --mode sim --list
```

## Presets

| Preset | Description |
|--------|-------------|
| `galaxy-spiral` | Logarithmic arms with density wave theory |
| `dna-helix` | Double helix with base pair connections |
| `flocking-murmuration` | Boids via phase-shifted oscillators (no arrays) |

## Gesture OS

Optional hand gesture camera controls via MediaPipe Hands:

| Gesture | Action |
|---------|--------|
| One finger | Camera rotation |
| Open palm | Zoom |
| Peace sign | Simulation speed |
| Fist | Pause/resume |

Falls back to mouse/touch when camera is unavailable.

## Security Model

The sandbox validates all injected code before execution:

1. **Regex scan** — Forbidden patterns (DOM, network, eval, prototypes, constructors, infinite loops)
2. **Syntax check** — Compiled via `new Function()` with named parameters
3. **Dry-run** — Executed with mock values for 3 frames with 500ms time budget
4. **Runtime protection** — Non-finite values skipped, frame-level error catching

The `THREE` object passed to sims is a frozen safe subset (Vector3, Color, MathUtils only) — FileLoader, ImageLoader, and other I/O classes are excluded.

## Performance Rules

The function runs 20,000 times per frame (1.2M calls/sec). Key constraints:

- Zero allocations (`target.set()` not `new Vector3()`)
- Math over logic (no if/else for particle grouping)
- Epsilon guards for all divisions (`/ (x + 0.0001)`)
- All variables declared (`const`/`let`)

## File Structure

```
particle-swarm-sim/
├── SKILL.md                          # Skill entry point
├── README.md                         # This file
├── assets/
│   ├── templates/
│   │   ├── sandbox-runtime.html      # Full runtime: gesture, editor, security
│   │   └── sandbox-minimal.html      # Stripped: mouse/touch only, embeddable
│   └── sims/
│       ├── galaxy-spiral.js          # Reference: logarithmic spiral arms
│       ├── dna-helix.js              # Reference: double helix + base pairs
│       └── flocking-murmuration.js   # Reference: Boids without neighbor search
├── references/
│   ├── api-contract.md               # Full API specification
│   ├── sandbox-architecture.md       # Runtime internals, scene graph, frame loop
│   ├── gesture-os.md                 # MediaPipe Hands integration
│   ├── security-sandbox.md           # Threat model, validation pipeline
│   ├── performance-patterns.md       # Zero-alloc patterns, math idioms
│   └── sim-gallery.md               # 10 annotated behavior patterns
└── scripts/
    ├── validate_sim.py               # Static validator for function bodies
    ├── validate_sandbox.py           # Structural validator for runtime HTML
    └── swarm_generator.py            # Generator: --mode sandbox|sim
```

## Attribution

Architecture distilled from [particles.casberry.in](https://particles.casberry.in/) by [Casberry](https://casberry.in/).
