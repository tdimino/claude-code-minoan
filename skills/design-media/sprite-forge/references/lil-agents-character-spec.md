# lil-agents Character Specification

Reference for adding custom characters to the lil-agents macOS dock companion (github.com/ryanstephen/lil-agents).

## Video Format

| Property | Value |
|----------|-------|
| Container | `.mov` (QuickTime) |
| Codec | HEVC (H.265) with alpha channel |
| Tag | `hvc1` (required for AVFoundation) |
| Resolution | 1080x1920 (portrait) |
| Pixel format | `bgra` (RGBA 32-bit) |
| Duration | ~10 seconds (looping) |
| Frame rate | 12-30 fps (12 for pixel art, 24-30 for smooth) |

## Walk Cycle Timing Structure

The video contains a single idle→walk→idle cycle. The app controls playback position to sync character movement with dock position.

```
0s          3s      3.75s                    8s    8.5s        10s
|-- idle --|-- accel --|------ walk loop ------|-- decel --|-- idle --|
```

| Phase | Start | End | Description |
|-------|-------|-----|-------------|
| Idle start | 0.0s | 3.0s | Character stands still (first frame repeated) |
| Accelerate | 3.0s | 3.75s | Walk cycle begins, slow → fast |
| Full speed | 3.75s | 8.0s | Walk cycle at full speed (loop walk frames) |
| Decelerate | 8.0s | 8.5s | Walk cycle slows down |
| Idle end | 8.5s | 10.0s | Character stands still again |

## Swift Configuration Parameters

Each character needs these params in `LilAgentsController.swift`:

```swift
let myChar = WalkerCharacter(videoName: "walk-mychar-01")  // filename without .mov
myChar.accelStart = 3.0         // when acceleration begins (seconds into video)
myChar.fullSpeedStart = 3.75    // when full speed is reached
myChar.decelStart = 8.0         // when deceleration begins
myChar.walkStop = 8.5           // when character is fully stopped
myChar.walkAmountRange = 0.35...0.6  // walk distance as fraction of dock width
myChar.yOffset = -5             // vertical pixel offset above dock
myChar.flipXOffset = 0          // horizontal compensation when character flips direction
myChar.characterColor = NSColor(red: 0.5, green: 0.5, blue: 0.8, alpha: 1.0)  // accent color
myChar.positionProgress = 0.5   // starting position on dock (0.0 = left, 1.0 = right)
myChar.setup()
characters.append(myChar)
myChar.controller = self
```

## How the Animation System Works

1. `CVDisplayLink` fires at 60fps
2. App checks if character should walk (random 5-12s pause between walks)
3. During walk: reads video playback time → calls `movementPosition(at:)` → maps to dock pixel position
4. `movementPosition()` uses 4-phase easing: ease-in, linear, ease-out, stop
5. When direction reverses: `CATransform3D` flip on the player layer
6. After video completes: enter random pause, then replay

## Encoding Commands

### Direct HEVC (recommended for automation)

```bash
ffmpeg -framerate 12 -i frame_%04d.png \
  -c:v hevc_videotoolbox \
  -alpha_quality 1.0 \
  -tag:v hvc1 \
  -pix_fmt bgra \
  walk-mychar-01.mov
```

### Two-step ProRes (higher quality, manual)

```bash
# Step 1: PNG → ProRes 4444 with alpha
ffmpeg -framerate 12 -i frame_%04d.png \
  -c:v prores_ks -pix_fmt yuva444p10le \
  -alpha_bits 16 -profile:v 4444 \
  intermediate.mov

# Step 2: Right-click in Finder → Services → Encode Selected Video Files
# Select "HEVC 1080p" + "Preserve Transparency" + Continue
```

## Adding to Xcode Project

1. Copy `walk-mychar-01.mov` into `LilAgents/` directory
2. In Xcode, add file to the LilAgents target (drag into project navigator)
3. Verify the file appears in Build Phases → Copy Bundle Resources
4. Add Swift config block to `LilAgentsController.start()`
5. Build and run
