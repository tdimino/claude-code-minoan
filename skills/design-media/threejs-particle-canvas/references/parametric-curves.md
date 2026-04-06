# Parametric Curve Catalog for Spinners

Mathematical curves for the `plotFunction(progress, detailScale, config)` pattern. All formulas use TSL nodes. `progress` is 0-1 along the curve, mapped to `t = PI2 * progress`.

## Lemniscate of Bernoulli (Infinity)

The classic infinity/figure-8 shape. Clean, minimal, universally recognizable as a loader.

```
t = PI2 * progress
scale = lemniscateA + detailScale * lemniscateBoost
sinT = sin(t), cosT = cos(t)
denom = d + sin(t)^2
x = scale * cos(t) / denom
y = scale * sin(t) * cos(t) / denom
```

| Param | Range | Effect |
|-------|-------|--------|
| `lemniscateA` | 0.1-0.5 | Overall size |
| `lemniscateBoost` | 0.1-0.3 | Detail breathing amplitude |
| `denom` | 0.5-2.0 | 1=classic infinity, >1 rounder lobes, <1 sharper crossing |

## Rose Curve (Rhodonea)

Flower and star shapes. `n/d` ratio controls petal count.

```
t = PI2 * progress
r = cos(n/d * t)
x = r * cos(t) * scale
y = r * sin(t) * scale
```

| Param | Range | Effect |
|-------|-------|--------|
| `n` | 1-8 | Numerator — higher = more petals |
| `d` | 1-5 | Denominator — n/d ratio determines petal count |
| `scale` | 0.1-0.5 | Overall size |

**Petal count rules**: If n/d is irreducible: n petals if n is odd, 2n petals if n is even. If d > 1, the curve may not close in one revolution — use `progress * d` to complete the full path.

## Spirograph (Epitrochoid)

Looping patterns of a circle rolling around another circle.

```
t = PI2 * progress
R = 1.0 (outer radius)
r = R / loops
d_offset = r * tinyLoopAmount
x = (R - r) * cos(t) + d_offset * cos((R - r) / r * t)
y = (R - r) * sin(t) + d_offset * sin((R - r) / r * t)
```

| Param | Range | Effect |
|-------|-------|--------|
| `loops` | 3-12 | Number of loops around the circle |
| `tinyLoopAmount` | 0.5-3.0 | Size of the small loops relative to rolling circle |

## Lissajous Figure

Oscilloscope-style figures from two perpendicular sinusoids.

```
t = PI2 * progress
x = sin(a * t + delta) * scale
y = sin(b * t) * scale
```

| Param | Range | Effect |
|-------|-------|--------|
| `a` | 1-5 | Horizontal frequency |
| `b` | 1-5 | Vertical frequency |
| `delta` | 0-PI | Phase offset (PI/2 for classic figure-8) |
| `scale` | 0.1-0.5 | Overall size |

**Common ratios**: 1:2 = figure-8, 2:3 = pretzel, 3:4 = complex knot

## Circle / Arc

Simple circular path. The baseline spinner.

```
t = PI2 * progress
x = radius * cos(t)
y = radius * sin(t)
```

| Param | Range | Effect |
|-------|-------|--------|
| `radius` | 0.1-0.5 | Circle size |

For a partial arc, multiply progress by a fraction < 1.

## Multi-Lobe (Triskelion)

N-fold rotational symmetry patterns.

```
t = PI2 * progress
lobe_t = t * lobes
r = cos(lobe_t) * outerRadius + innerRadius
twist_angle = t + sin(lobe_t * twist) * twistAmount
x = r * cos(twist_angle)
y = r * sin(twist_angle)
```

| Param | Range | Effect |
|-------|-------|--------|
| `lobes` | 2-6 | Number of symmetric lobes |
| `outerRadius` | 0.1-0.4 | Lobe reach |
| `innerRadius` | 0.05-0.2 | Center hub size |
| `twist` | 0.5-2.0 | Twist frequency per lobe |

## Heart (Cardioid Variant)

```
t = PI2 * progress
x = scale * (16 * sin(t)^3)
y = scale * (13 * cos(t) - 5 * cos(2t) - 2 * cos(3t) - cos(4t))
```

| Param | Range | Effect |
|-------|-------|--------|
| `scale` | 0.01-0.03 | Overall size (values are large, needs scaling) |

## Particle Sphere

3D distribution rather than a 2D curve. Points distributed on a sphere surface.

```
phi = acos(1 - 2 * progress)
theta = PI2 * progress * goldenRatio
x = radius * sin(phi) * cos(theta)
y = radius * sin(phi) * sin(theta)
z = radius * cos(phi)
```

| Param | Range | Effect |
|-------|-------|--------|
| `radius` | 0.2-0.5 | Sphere radius |
| `goldenRatio` | 1.618... | Fibonacci spiral distribution |

For a sphere spinner, animate by rotating the entire Points object rather than moving the trail along the curve.

## Spiral (Archimedean)

```
t = PI2 * progress * turns
r = a + b * t
x = r * cos(t)
y = r * sin(t)
```

| Param | Range | Effect |
|-------|-------|--------|
| `a` | 0 | Starting radius (0 = from center) |
| `b` | 0.01-0.05 | Expansion rate per radian |
| `turns` | 1-5 | Number of spiral turns |

## Combining Curves

More complex spinners combine curves:
- **Offset**: Add a slow-rotating offset to any curve for orbital motion
- **Modulation**: Multiply radius by `1 + sin(time * freq) * amp` for breathing
- **Superposition**: Add two curves at different scales for layered patterns
- **3D lift**: Set `z = sin(t * freq) * amplitude` for depth on any 2D curve
