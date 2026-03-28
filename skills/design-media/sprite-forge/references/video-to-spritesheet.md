# Video-to-Spritesheet Pipeline

## Why Video-First

Image models (GPT Image, Nano Banana, Midjourney, Flux) cannot generate temporally coherent animation frames. Each frame is generated independently — characters teleport between poses, limbs change proportions, walk cycles don't look like walking.

Video models (Veo 3.1, Sora 2, Kling v3) understand motion and produce smooth frame-to-frame transitions. The pipeline: generate video → extract frames → stitch into sprite sheet.

## The Pipeline

```
Video → ffmpeg → Frames → [bg removal] → [resize] → Stitch → Sprite Sheet + Atlas
```

### Step 1: Extract Frames
```bash
ffmpeg -i walk.mp4 -vf "fps=12" frames/frame_%04d.png
# With time range:
ffmpeg -i walk.mp4 -ss 1.0 -to 3.5 -vf "fps=12" frames/frame_%04d.png
```

### Step 2: Remove Background (optional)
```bash
# ML-based (any background)
rembg i frame.png frame.png

# Chroma key (green screen video)
python3 scripts/chroma_key.py --input frame.png --output frame.png --despill
```

### Step 3: Resize to Uniform Cell Size
```bash
# Via Pillow in video_to_spritesheet.py
# Common sizes: 32x32, 48x48, 64x64, 128x128
```

### Step 4: Stitch + Generate Atlas
```bash
python3 scripts/stitch_spritesheet.py --input-dir frames/ --cols 8 --cell-size 64x64 --atlas json
```

### One-Shot Command
```bash
python3 scripts/video_to_spritesheet.py \
  --input walk.mp4 --fps 12 --cell-size 64x64 \
  --remove-bg rembg --cols 8 --atlas json
```

## Practitioner Approaches (March 2026)

**@backnotprop**: "Animate the original image. Slice animation. OpenCV magic for realignment and framing."

**@nmatares** (hybrid): Create multi-frame sprite sheet with Nano Banana Pro, use that sheet as a Veo 3.1 "ingredient" input.

**@techhalla** (most viral — 1,815 likes, 2,716 bookmarks): Create assets on Freepik AI tools, use custom app to select frames from generated videos, output downloadable sprite sheets.

**@martin_casado** (a16z GP): kie.ai → ezgif → local resize → stitch. Even a VC needs 4+ tools.

## Atlas Metadata Formats

### JSON (Phaser / Web)
```json
{
  "frames": {
    "frame_000": {"x": 0, "y": 0, "w": 64, "h": 64},
    "frame_001": {"x": 64, "y": 0, "w": 64, "h": 64}
  },
  "meta": {"image": "sheet.png", "size": {"w": 512, "h": 64}, "format": "RGBA8888"}
}
```

### XML (Unity TexturePacker)
```xml
<TextureAtlas imagePath="sheet.png">
  <SubTexture name="frame_000" x="0" y="0" width="64" height="64"/>
</TextureAtlas>
```

## Standard Frame Counts

| Animation | Frames | Timing |
|-----------|--------|--------|
| Walk | 6-8 | 60-120ms per frame |
| Run | 6-8 | 60-80ms |
| Idle | 4-6 | 100-200ms |
| Attack | 5-8 | 60-100ms |
| Jump | 4-6 | 80-120ms |

## Video Models for Animation

| Model | Best For | Notes |
|-------|---------|-------|
| Veo 3.1 Fast | Walk cycles | Used in chongdashu pipeline |
| Kling v3 | Character animation | Good consistency |
| Seedance 1.5 | Dance/motion | Newer, less tested |
