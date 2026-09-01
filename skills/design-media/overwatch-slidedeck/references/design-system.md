# Overwatch Mode — Design System

## Color Tokens

All colors are CSS custom properties defined in `globals.css`. Themes switch via `data-slide-mode` attribute on `SlideWrapper`.

### Base Palette

| Token | Value | Use |
|-------|-------|-----|
| `--color-black` | `#0c0c0e` | Dark mode background |
| `--color-white` | `#f5f5f3` | Light mode background (warm off-white) |
| `--color-orange` | `#ff6e41` | Primary accent |
| `--color-orange-muted` | `#e05829` | Muted accent, hover states |
| `--color-primary` | `var(--color-orange)` | Alias for primary accent |

### Theme Modes

#### Dark Mode (`mode="dark"`)
| Token | Value |
|-------|-------|
| `--color-bg-primary` | `#0c0c0e` |
| `--color-bg-secondary` | `#18181b` |
| `--color-text-primary` | `#f5f5f3` |
| `--color-text-secondary` | `#a1a1aa` |
| `--color-text-muted` | `#71717a` |
| `--color-border-light` | `#3f3f46` |

#### White Mode (`mode="white"`)
| Token | Value |
|-------|-------|
| `--color-bg-primary` | `#f5f5f3` |
| `--color-bg-secondary` | `#e5e7eb` |
| `--color-text-primary` | `#0c0c0e` |
| `--color-text-secondary` | `#52525b` |
| `--color-text-muted` | `#a1a1aa` |
| `--color-border-light` | `#d4d4d8` |

#### Orange Mode (`mode="orange"`)
| Token | Value |
|-------|-------|
| `--color-bg-primary` | `#ff6e41` |
| `--color-bg-secondary` | `#e05829` |
| `--color-text-primary` | `#0c0c0e` |
| `--color-text-secondary` | `#3f3f46` |
| `--color-text-muted` | `#52525b` |
| `--color-border-light` | `#333` |

## Typography

| Token | Stack | Use |
|-------|-------|-----|
| `--font-heading` | Playfair Display, Editorial New, Georgia, serif | Titles, headlines, quotes |
| `--font-body` | Inter, system-ui, -apple-system, sans-serif | Body text, labels, navigation |
| `--font-mono` | IBM Plex Mono, JetBrains Mono, Fira Code, monospace | Technical labels, counters, code |

### Type Scale

| Component | Size | Leading | Tracking |
|-----------|------|---------|----------|
| `Headline` | 140px | 0.85 | -0.02em |
| `SubHeadline` | 72px | 0.9 | -0.01em |
| `BodyText lg` | 28px | 1.6 | — |
| `BodyText md` | 24px | 1.6 | — |
| `BodyText sm` | 20px | 1.5 | — |
| `Eyebrow` | 18px | — | 0.15em |
| `MonoLabel lg` | 22px | — | 0.1em |
| `MonoLabel md` | 18px | — | 0.1em |
| `MonoLabel sm` | 14px | — | 0.1em |

## Dimensions

| Property | Value |
|----------|-------|
| Design canvas | 1920 x 1080px |
| Slide padding | 64px all sides |
| Content gap | 48px |
| Border radius | 1px (sm), 2px (md), 4px (lg) |

## Shadows

| Token | Value |
|-------|-------|
| `--shadow-sm` | `0 4px 12px rgba(0, 0, 0, 0.05)` |
| `--shadow-md` | `0 8px 24px rgba(0, 0, 0, 0.08)` |
| `--shadow-lg` | `0 16px 40px rgba(0, 0, 0, 0.12)` |
| `--shadow-xl` | `0 24px 64px rgba(0, 0, 0, 0.2)` |

## Fonts (Google Fonts)

Loaded via `index.html`:
```
Playfair Display: 400, 700, 900
IBM Plex Mono: 400, 500, 600
```

Inter is loaded from system fonts (no CDN needed).
