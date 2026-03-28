# ASCII Art Techniques

## Character Sets (Density Ramps)

Characters ordered from least to most dense (bright to dark):

| Name | Characters | Levels | Best For |
|------|-----------|--------|----------|
| standard | ` .:-=+*#%@` | 10 | General use, README badges |
| detailed | ` .'^\`",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$` | 70 | Photo conversions |
| blocks | ` ░▒▓█` | 5 | Unicode terminals, retro look |

## Aspect Ratio Correction

Terminal characters are approximately 2x taller than they are wide. Without correction, output is vertically stretched. Apply a 0.55 ratio to the height:

```
new_height = width * (image_height / image_width) * 0.55
```

## Rendering Modes

### Grayscale Density Ramp
Map each pixel's brightness (0-255) to a character from the density ramp.

```python
brightness = pixel_value  # 0-255
index = int(brightness / 256 * len(charset))
char = charset[min(index, len(charset) - 1)]
```

### Color Half-Block (Unicode)
Uses the upper half block character `▀` with ANSI 24-bit true color. Each output character represents TWO rows of pixels — the top pixel becomes the foreground color, the bottom pixel becomes the background color.

```
\033[38;2;R1;G1;B1m    # foreground = top pixel
\033[48;2;R2;G2;B2m    # background = bottom pixel
▀                       # upper half block
\033[0m                 # reset at end of line
```

This doubles vertical resolution compared to single-character approaches.

### jp2a (External Tool)
Best for quick grayscale photo-to-ASCII conversions.

```bash
brew install jp2a
jp2a --width=80 photo.jpg
jp2a --width=80 --invert photo.jpg  # light-on-dark
```

## External Tools

| Tool | Install | Strengths |
|------|---------|-----------|
| jp2a | `brew install jp2a` | Best grayscale photo converter |
| img2txt (libcaca) | `brew install libcaca` | 256-color support |
| chafa | `brew install chafa` | Sixel/kitty protocol for modern terminals |
| Mezzotone | Go binary | Interactive parameter adjustment, GIF support |

## When to Use Each Mode

| Need | Mode | Why |
|------|------|-----|
| README badges, simple diagrams | gray (standard) | Universally renderable |
| Terminal previews, mascot display | color (half-block) | Full color, double resolution |
| Quick photo conversion | jp2a | Fast, good defaults |
| Modern terminal with graphics protocol | chafa | Highest fidelity |

## Tips

- **Invert for dark terminals**: Light-on-dark terminals need inverted density ramps (dense chars = bright)
- **Width matters**: 80 chars for standard terminal, 120+ for wide terminals
- **Font choice**: Monospace fonts with uniform character widths are essential
- **File output**: Save color mode to file with ANSI codes for later `cat` display
