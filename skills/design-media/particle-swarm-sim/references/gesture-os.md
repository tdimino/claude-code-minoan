# Gesture OS

Hand gesture camera controls via MediaPipe Hands. Optional feature — the sandbox works with mouse/touch/keyboard when gesture OS is disabled or camera permission is denied.

## Dependencies

- [MediaPipe Hands](https://google.github.io/mediapipe/solutions/hands.html) v0.4
- [MediaPipe Camera Utils](https://google.github.io/mediapipe/solutions/camera_utils.html) v0.3
- Both loaded via CDN dynamic import (no build step)

## Configuration

```javascript
hands.setOptions({
  maxNumHands: 1,           // Single-hand tracking
  modelComplexity: 0,       // Fast mode (sufficient for gesture classification)
  minDetectionConfidence: 0.7,
  minTrackingConfidence: 0.5,
});
```

Camera: 320x240 resolution. Detection runs every 3rd frame to reduce CPU load.

## Gesture Classification

MediaPipe returns 21 hand landmarks per detected hand. Gesture classification uses fingertip vs. PIP joint vertical positions:

```
Fingertips: [8 (index), 12 (middle), 16 (ring), 20 (pinky)]
PIP joints: [6 (index), 10 (middle), 14 (ring), 18 (pinky)]

Extended = tip.y < pip.y (hand assumed roughly upright)
```

### Gesture Mapping

| Gesture | Fingers Extended | Action | Sensitivity |
|---------|-----------------|--------|-------------|
| **Finger** | Index only | Camera rotation (theta/phi) | 3.0 × dx/dy |
| **Palm** | All four | Zoom in/out | 50.0 × dx |
| **Peace** | Index + middle | Simulation speed | 2.0 × dx |
| **Fist** | None | Pause/resume toggle | Single event |

### Dead Zones

Movement deltas below `0.01` (normalized screen coordinates) are ignored to prevent jitter near gesture boundaries.

### Gesture State Machine

```
Frame N: detect landmarks → classify gesture
  │
  ├── if gesture !== currentGesture:
  │     Record new gesture
  │     Reset lastGestureX/Y to current hand center
  │     If fist → toggle pause
  │     Return (no action on gesture change frame)
  │
  └── if gesture === currentGesture:
        Compute dx, dy from lastGestureX/Y
        Apply gesture-specific action (rotation/zoom/speed)
        Update lastGestureX/Y
```

The "no action on gesture change" rule prevents sudden jumps when switching between gestures — the hand position resets to the new gesture's center point.

## Camera Action Mapping

### Finger (Rotation)
```javascript
cameraTheta += dx * 3;
cameraPhi = clamp(cameraPhi + dy * 2, 0.1, PI - 0.1);
```

### Palm (Zoom)
```javascript
cameraTargetRadius = clamp(cameraTargetRadius - dx * 50, 5, 100);
```

### Peace (Speed)
```javascript
simSpeed = clamp(simSpeed + dx * 2, 0.1, 5.0);
```

Note: `simSpeed` is reset to `1.0` on code injection to prevent confusion.

## Fallback

When gesture OS is unavailable (camera denied, MediaPipe load failure, mobile without camera):
- **Mouse**: Drag to rotate, scroll to zoom
- **Touch**: Single-finger drag to rotate, two-finger pinch to zoom
- **Keyboard**: Space = pause/resume, R = reset camera

The gesture status indicator shows "GESTURE OS UNAVAILABLE" briefly, then fades.

## Performance

- MediaPipe runs at ~30fps on modern hardware at complexity 0
- Detection every 3rd frame means ~10 hand detections per second
- CPU overhead: ~5ms per detection frame
- The video element is hidden (`display: none`) — no rendering overhead

## Implementation Notes

- MediaPipe Hands is loaded via dynamic `import()` from CDN — no bundle impact
- Camera resolution is kept low (320x240) since we only need landmark positions
- The `video` element is appended to the DOM but hidden
- Gesture classification uses only Y-axis comparison (vertical finger extension)
- Hand center is taken from landmark 9 (middle finger MCP) for smooth tracking
