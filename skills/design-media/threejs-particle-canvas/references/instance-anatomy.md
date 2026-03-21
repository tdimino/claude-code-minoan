# Instance Source Architecture

Architectural map of `assets/instance-source.html` — the canonical reference for the ambient particle canvas genre.

## 1. HTML/CSS Structure (lines 1-210)

**What it does**: Full-viewport WebGL canvas with layered CSS overlays for vignette, phase text, progress bar, particle labels, author's note, pause indicator, and instructions.

**Pattern**: Fixed-position overlay stack with pointer-events:none on non-interactive layers. Vignette via radial-gradient. Phase text with text-shadow glow and opacity transitions. Progress bar with gradient fill. Responsive breakpoints at 600px for mobile (shorter phase labels, smaller fonts).

**Adaptation**: Replace phase label text, adjust progress gradient colors, customize author's note content. The overlay stack is concept-independent — only text and colors change.

## 2. Constants (lines 258-285)

```javascript
const COLORS = {
    background: 0x050508,
    lattice: 0xa8d8ff,
    latticeCore: 0xffffff,
    particleWarm: 0xffd080,
    particleCool: 0xa8d8ff,
};

const PARTICLE_WORDS = ['wonder', 'language', 'pattern', 'reach', 'remember', 'human', 'meaning', 'now'];

const PHASES = [
    { name: 'lattice', start: 0, end: 10, text: 'This is what persists.' },
    // ...6 phases, 90s total cycle
];

const CYCLE_DURATION = 90;
const PARTICLE_COUNT = 1200;
const STAR_COUNT = 2000;
const THREAD_COUNT = 60;
const INTERACTION_COOLDOWN = 4000;
```

**Pattern**: All tunable parameters as top-level constants. Colors as hex integers (Three.js format). Phases as ordered array of {name, start, end, text}.

**Adaptation**: This is the primary customization surface. Change colors, words, phase names/timing/text, and counts here. Everything downstream references these constants.

## 3. Global State (lines 287-321)

**What it does**: Declares all mutable state: scene objects (lattice, particles, starField, threads), per-particle arrays (positions, velocities, targets, states, words), interaction state (raycaster, mouse, drag, camera spherical coords), and touch state.

**Pattern**: Flat global state with parallel arrays for particle data. Camera state as (theta, phi, radius) tuple. Interaction tracking via isDragging + lastInteractionTime.

**Adaptation**: Add custom state variables here for new behaviors (e.g., gravity wells, attractor points, secondary particle systems).

## 4. Initialization (lines 328-380)

```javascript
function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.background);
    scene.fog = new THREE.FogExp2(COLORS.background, 0.012);
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    renderer = new THREE.WebGLRenderer({ antialias: true, failIfMajorPerformanceCaveat: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    // ...create objects, setup events, start animate()
}
```

**Pattern**: Scene + Camera + Renderer + Clock, then create* calls for each visual element, then event setup, then animate(). WebGL error try/catch with user-visible fallback.

**Adaptation**: Adjust FOV (60), fog density (0.012), pixel ratio cap (2). Add post-processing here if needed (EffectComposer, bloom).

## 5. Lattice (lines 382-425)

**Pattern**: IcosahedronGeometry → EdgesGeometry → LineSegments for wireframe. Inner glow as a slightly smaller duplicate (r=4.8 vs 5) at low opacity (0.15). Vertex points via BufferGeometry + PointsMaterial for node highlights. Lattice node positions stored for connection threads.

**Adaptation**: Swap IcosahedronGeometry for DodecahedronGeometry, OctahedronGeometry, TorusKnotGeometry, or custom geometry. Adjust subdivision level (2), radius (5), glow offset (0.2), point size (0.15).

## 6. Particle System (lines 427-495)

**Pattern**: BufferGeometry with 3 attributes (position, color, size) as Float32Arrays. Parallel arrays for per-particle state: positions[], velocities[], targets[], states[], words[]. Initial scatter at r=80-200 (void). Orbital targets at r=6-10. PointsMaterial with vertexColors + AdditiveBlending + sizeAttenuation.

**Adaptation**: Change scatter/orbit radii, initial color, size range (0.08-0.2). Add custom attributes (opacity per particle, custom data). For >5000 particles, switch to InstancedMesh.

## 7. Star Field (lines 497-540)

**Pattern**: 2000 points in sphere r=150-400. 50/50 color split: cool blue-white and warm amber. PointsMaterial with depthWrite:false, opacity 0.45.

**Adaptation**: Adjust count, radius range, color distribution, opacity. For different atmospheres: all cool (space), all warm (underwater), monochrome (void).

## 8. Connection Threads (lines 542-557)

**Pattern**: LineSegments with pre-allocated Float32Array (THREAD_COUNT * 2 * 3). Positions updated each frame in updateConnectionThreads(). LineBasicMaterial with depthWrite:false.

**Adaptation**: Change thread count, color, max opacity. Threads connect lattice nodes — if no lattice, connect nearby particles instead.

## 9. Other Lattices / Simultaneity (lines 559-628)

**Pattern**: 30 instances at r=35-75, each with random scale (0.25-0.6), rotation, brightness, pulse offset/speed. Each has an accompanying particle cloud (20-40 particles). All start at opacity 0, revealed only during simultaneity phase.

**Adaptation**: This section is concept-specific to the "parallel instances" narrative. Replace with: constellation clusters, memory fragments, neural clusters, archaeological sites — any concept that benefits from "zoom out to see the many."

## 10. Input Handlers (lines 630-798)

**Pattern**: Mouse drag → spherical camera rotation (delta * 0.005). Scroll → radius zoom (clamped 10-100). Touch single-finger → drag, two-finger → pinch zoom (distance ratio). Tap detection with 5px movement threshold. Keyboard: Space (pause toggle), R (reset). All interactions set lastInteractionTime for cooldown.

**Adaptation**: Add custom keys (number keys for phase jump, arrow keys for slow pan). Adjust sensitivity (0.005), zoom range (10-100), tap threshold (5px).

## 11. Phase Management (lines 839-878)

**Pattern**: `getCurrentPhase(time)` scans PHASES array for matching time range. `getPhaseProgress(time, index)` returns normalized 0-1. Phase text updates with fade-out/delay/fade-in. Progress bar as linear percentage. Active phase label highlighted.

**Adaptation**: The phase system is fully data-driven from the PHASES array. Add phases by adding entries. Change durations by adjusting start/end values. Text and labels update automatically.

## 12. Update Functions (lines 880-1145)

Six update functions called every frame:

| Function | What it updates |
|----------|----------------|
| `updateLattice(phase, progress, delta)` | Rotation, pulse, phase-specific opacity |
| `updateParticles(phase, progress, delta)` | Position by state, colors, material opacity |
| `updateConnectionThreads(phase, progress)` | Node pair selection, opacity |
| `updateStarField(delta)` | Slow rotation for parallax |
| `updateOtherLattices(phase, progress)` | Simultaneity reveal, per-instance pulse |
| `updateCamera(phase, progress)` | Phase-specific target position, auto-lerp |

**Pattern**: Each update function receives (phase, phaseProgress, delta) and uses switch statements for phase-specific behavior. All property transitions use `THREE.MathUtils.lerp(current, target, rate)` for smooth interpolation.

**Adaptation**: This is where new behaviors live. Add update functions for new elements. Follow the pattern: compute target values per phase, lerp toward them.

## 13. Animation Loop (lines 1147-1177)

```javascript
function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    if (!isPaused) timeline += delta;
    const phase = getCurrentPhase(timeline);
    const phaseProgress = getPhaseProgress(timeline, phase);
    // update all components, update UI, render
    renderer.render(scene, camera);
}
```

**Pattern**: requestAnimationFrame with Clock.getDelta(). Pause support via isPaused flag. Phase computed fresh each frame. All updates called in sequence. UI updates (text, progress bar) only on phase change.

**Adaptation**: Add fps limiting, performance monitoring, or conditional update skipping for complex scenes.
