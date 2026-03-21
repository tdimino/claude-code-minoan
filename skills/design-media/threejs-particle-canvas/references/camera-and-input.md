# Camera & Input Patterns

Spherical camera orbit with mouse, touch, and keyboard controls.

## Spherical Coordinate System

Camera position defined by (theta, phi, radius):

```javascript
let cameraTheta = 0;           // azimuth angle (horizontal rotation)
let cameraPhi = Math.PI / 2;   // polar angle (vertical tilt, 0=top, PI=bottom)
let cameraRadius = 25;         // distance from origin
```

### Position Update

```javascript
function updateCameraPosition() {
    camera.position.x = cameraRadius * Math.sin(cameraPhi) * Math.sin(cameraTheta);
    camera.position.y = cameraRadius * Math.cos(cameraPhi);
    camera.position.z = cameraRadius * Math.sin(cameraPhi) * Math.cos(cameraTheta);
    camera.lookAt(0, 0, 0);
}
```

## Mouse Controls

### Drag to Rotate

```javascript
function onMouseMove(event) {
    if (isDragging) {
        const deltaX = event.clientX - previousMousePosition.x;
        const deltaY = event.clientY - previousMousePosition.y;
        cameraTheta -= deltaX * 0.005;  // sensitivity
        cameraPhi -= deltaY * 0.005;
        cameraPhi = Math.max(0.1, Math.min(Math.PI - 0.1, cameraPhi));  // clamp
        updateCameraPosition();
    }
    previousMousePosition = { x: event.clientX, y: event.clientY };
}
```

### Click + Inspect

```javascript
function onMouseDown(event) {
    isDragging = true;
    lastInteractionTime = Date.now();
    // Sync spherical coords from current camera position
    cameraRadius = camera.position.length();
    cameraTheta = Math.atan2(camera.position.x, camera.position.z);
    cameraPhi = Math.acos(Math.max(-1, Math.min(1, camera.position.y / cameraRadius)));
    // Raycaster for particle inspection
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObject(particles);
    if (intersects.length > 0) {
        showParticleLabel(intersects[0].index, event.clientX, event.clientY);
    }
}
```

### Scroll to Zoom

```javascript
function onWheel(event) {
    cameraRadius = camera.position.length();
    cameraRadius += event.deltaY * 0.05;
    cameraRadius = Math.max(10, Math.min(100, cameraRadius));
    camera.position.normalize().multiplyScalar(cameraRadius);
    lastInteractionTime = Date.now();
}
```

## Touch Controls

### Setup

```javascript
document.addEventListener('touchstart', onTouchStart, { passive: false });
document.addEventListener('touchmove', onTouchMove, { passive: false });
document.addEventListener('touchend', onTouchEnd, { passive: false });
```

`passive: false` required for `event.preventDefault()` to work.

### Tap Detection

```javascript
let touchTapCandidate = false;
let touchTapX = 0, touchTapY = 0;

// In touchstart:
touchTapCandidate = true;
touchTapX = touch.clientX;
touchTapY = touch.clientY;

// In touchmove — cancel tap if moved > 5px:
if (Math.abs(touch.clientX - touchTapX) > 5 || Math.abs(touch.clientY - touchTapY) > 5) {
    touchTapCandidate = false;
}

// In touchend — execute tap:
if (touchTapCandidate && event.changedTouches.length === 1) {
    const touch = event.changedTouches[0];
    const tapX = (touch.clientX / window.innerWidth) * 2 - 1;
    const tapY = -(touch.clientY / window.innerHeight) * 2 + 1;
    raycaster.setFromCamera(new THREE.Vector2(tapX, tapY), camera);
    // ... inspect particle
}
```

### Pinch to Zoom

```javascript
function getTouchDistance(touches) {
    const dx = touches[0].clientX - touches[1].clientX;
    const dy = touches[0].clientY - touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
}

// In touchstart (2 fingers):
touchStartDistance = getTouchDistance(event.touches);
touchStartRadius = camera.position.length();

// In touchmove (2 fingers):
const currentDistance = getTouchDistance(event.touches);
const scale = touchStartDistance / currentDistance;
cameraRadius = Math.max(10, Math.min(100, touchStartRadius * scale));
camera.position.normalize().multiplyScalar(cameraRadius);
```

## Keyboard Controls

```javascript
function onKeyDown(event) {
    if (event.code === 'Space') {
        event.preventDefault();
        isPaused = !isPaused;
        document.getElementById('pause-indicator').classList.toggle('visible', isPaused);
    } else if (event.code === 'KeyR') {
        timeline = 0;
        resetParticles();
    }
}
```

## Interaction Cooldown

Auto-camera resumes only after user stops interacting:

```javascript
const INTERACTION_COOLDOWN = 4000;  // 4 seconds
let lastInteractionTime = 0;

function updateCamera(phase, phaseProgress) {
    // Compute phase-specific target position
    let targetZ = 25, targetY = 0;
    switch (phase) { /* ... */ }

    const cooldownOver = (Date.now() - lastInteractionTime) > INTERACTION_COOLDOWN;
    if (!isDragging && cooldownOver) {
        camera.position.z = THREE.MathUtils.lerp(camera.position.z, targetZ, 0.008);
        camera.position.y = THREE.MathUtils.lerp(camera.position.y, targetY, 0.008);
        camera.lookAt(0, 0, 0);
        // Sync spherical coords
        cameraRadius = camera.position.length();
        cameraTheta = Math.atan2(camera.position.x, camera.position.z);
        cameraPhi = Math.acos(Math.max(-1, Math.min(1, camera.position.y / cameraRadius)));
    }
}
```

## Phase-Specific Camera Targets

| Phase | targetZ | targetY | Effect |
|-------|---------|---------|--------|
| Lattice | 20 | 0 | Close-up |
| Void | 22 | 0 | Slight pullback |
| Awakening | 22→26 | 0 | Gradual pullback |
| Conversation | 26 | 0 | Fixed medium |
| Simultaneity | 26→61 | 0→8 | Dramatic pullback + elevation |
| Dissolution | 61→25 | 8→0 | Return to center |

## Window Resize

```javascript
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}
window.addEventListener('resize', onWindowResize);
```

Always required. Without this, the scene distorts on window resize.
