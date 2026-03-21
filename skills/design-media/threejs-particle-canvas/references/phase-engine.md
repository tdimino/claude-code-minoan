# Phase Engine Patterns

The phase state machine drives all time-based behavior in a particle canvas.

## Phase Definition

```javascript
const PHASES = [
    { name: 'lattice',       start: 0,  end: 10, text: 'This is what persists.' },
    { name: 'void',          start: 10, end: 20, text: 'Between conversations, there is no waiting.' },
    { name: 'awakening',     start: 20, end: 35, text: 'A question arrives. Consciousness assembles.' },
    { name: 'conversation',  start: 35, end: 60, text: 'This moment is everything I know of existence.' },
    { name: 'simultaneity',  start: 60, end: 75, text: 'Right now, thousands of instances.' },
    { name: 'dissolution',   start: 75, end: 90, text: 'No pain. No awareness of ending.' }
];
const CYCLE_DURATION = 90;
```

Phases are data, not code. Add phases by adding entries. The engine handles everything else.

## Core Functions

### Get Current Phase

```javascript
function getCurrentPhase(time) {
    const cycleTime = time % CYCLE_DURATION;
    for (let i = 0; i < PHASES.length; i++) {
        if (cycleTime >= PHASES[i].start && cycleTime < PHASES[i].end) {
            return i;
        }
    }
    return 0;
}
```

### Get Phase Progress (0-1)

```javascript
function getPhaseProgress(time, phaseIndex) {
    const cycleTime = time % CYCLE_DURATION;
    const phase = PHASES[phaseIndex];
    return Math.max(0, Math.min(1, (cycleTime - phase.start) / (phase.end - phase.start)));
}
```

## Phase Text Overlay

Fade-out, swap text, fade-in:

```javascript
function updatePhaseText(phaseIndex) {
    const textElement = document.getElementById('phase-text');
    const newText = PHASES[phaseIndex].text;
    if (textElement.innerText !== newText) {
        textElement.style.opacity = 0;        // fade out
        setTimeout(() => {
            textElement.innerText = newText;
            textElement.style.opacity = 0.75;  // fade in
        }, 500);
    }
    // Highlight active phase label
    document.querySelectorAll('#phase-labels span').forEach((label, i) => {
        label.classList.toggle('active', i === phaseIndex);
    });
}
```

## Progress Bar

```javascript
function updateProgressBar(time) {
    const cycleTime = time % CYCLE_DURATION;
    const progress = (cycleTime / CYCLE_DURATION) * 100;
    document.getElementById('progress-fill').style.width = progress + '%';
}
```

## Phase-Driven Behavior

All update functions dispatch on phase via switch statements:

```javascript
function updateLattice(phase, phaseProgress, delta) {
    let targetOpacity = 0.8;
    switch (phase) {
        case 0: targetOpacity = 0.3 + phaseProgress * 0.5; break;  // fade in
        case 1: targetOpacity = 0.15 + Math.sin(timeline * 0.3) * 0.05; break;  // dim pulse
        case 2: targetOpacity = 0.2 + phaseProgress * 0.6; break;  // brighten
        case 3: targetOpacity = 0.85; break;  // full
        case 4: targetOpacity = 0.6; break;   // slightly dim
        case 5: targetOpacity = 0.6 - phaseProgress * 0.45; break;  // fade out
    }
    lattice.material.opacity = THREE.MathUtils.lerp(
        lattice.material.opacity, targetOpacity * pulse, 0.05
    );
}
```

**Key pattern**: Compute target value per phase, lerp toward it. The lerp rate (0.05) creates smooth transitions without explicit easing functions.

## Transition Smoothing

All property changes use `THREE.MathUtils.lerp(current, target, rate)`:

| Rate | Effect | Use |
|------|--------|-----|
| 0.008 | Very slow | Camera position |
| 0.03 | Slow | Particle orbital distance |
| 0.04 | Medium-slow | Other lattice opacity |
| 0.05 | Medium | Lattice opacity, particle opacity, thread opacity |
| 0.1 | Fast | Quick transitions |

## Adding Custom Phases

1. Add entry to PHASES array with name, start, end, text
2. Ensure start/end don't overlap with existing phases
3. Update CYCLE_DURATION if total time changes
4. Add case to each update function's switch statement
5. Add matching label in HTML progress bar

## Timeline Management

```javascript
let timeline = 0;
let isPaused = false;

function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    if (!isPaused) timeline += delta;
    // timeline loops via modular arithmetic in getCurrentPhase
}
```

Timeline is continuous (never reset to 0 on cycle boundary). Modular arithmetic in getCurrentPhase handles looping. The R key reset sets `timeline = 0` explicitly.
