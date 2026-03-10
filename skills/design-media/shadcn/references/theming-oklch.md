## Theming with OKLCH Colors

shadcn v4 uses OKLCH color space for perceptually uniform color manipulation.

### Convention: background + foreground Pairs

Every semantic color role has two variables. The background suffix is omitted for the primary role:

```css
--primary: oklch(0.205 0.03 264.05);        /* background */
--primary-foreground: oklch(0.985 0 0);       /* text on that background */
```

Usage: `bg-primary text-primary-foreground`.

### Standard CSS Variables

| Variable | Purpose |
|----------|---------|
| `--background` / `--foreground` | Page background and body text |
| `--card` / `--card-foreground` | Card surfaces |
| `--popover` / `--popover-foreground` | Popover/dropdown surfaces |
| `--primary` / `--primary-foreground` | Primary actions and emphasis |
| `--secondary` / `--secondary-foreground` | Secondary actions |
| `--muted` / `--muted-foreground` | Muted/disabled states |
| `--accent` / `--accent-foreground` | Accent highlights |
| `--destructive` / `--destructive-foreground` | Destructive/danger actions |
| `--border` | Default border color |
| `--input` | Input border color |
| `--ring` | Focus ring color |
| `--chart-1` through `--chart-5` | Chart/data visualization colors |
| `--radius` | Global border radius |
| `--sidebar-*` | Sidebar-specific variants |

### Dark Mode

Define both `:root` (light) and `.dark` (dark) scopes:

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
}
```

### Tailwind v4 Integration

Map CSS variables to Tailwind utilities via `@theme inline`:

```css
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  /* ... all semantic tokens */
}
```

`@theme inline` makes variables available in both utility classes AND JavaScript (via `getComputedStyle`).

### Adding Custom Semantic Colors

Three steps — define variable, define dark variant, register with Tailwind:

```css
:root {
  --warning: oklch(0.84 0.16 84);
  --warning-foreground: oklch(0.14 0.04 84);
}

.dark {
  --warning: oklch(0.72 0.14 84);
  --warning-foreground: oklch(0.96 0.02 84);
}

@theme inline {
  --color-warning: var(--warning);
  --color-warning-foreground: var(--warning-foreground);
}
```

Then use as `bg-warning text-warning-foreground`.

### Base Colors

Available palettes (set at init, immutable):
Neutral, Stone, Zinc, Mauve, Olive, Mist, Taupe.

### OKLCH Primer

`oklch(lightness chroma hue)`
- **Lightness**: 0 (black) to 1 (white)
- **Chroma**: 0 (gray) to ~0.37 (max saturation)
- **Hue**: 0-360 degrees (0=pink, 90=yellow, 180=cyan, 270=blue)

Advantages over HSL: perceptually uniform — equal chroma steps produce equal visual saturation changes. Two colors with the same lightness value actually look equally bright.
