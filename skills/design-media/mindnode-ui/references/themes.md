# MindNode-Inspired Theme System

Reference for implementing a theme engine inspired by MindNode's 27+ theme gallery, with per-level hierarchical styling, dynamic light/dark adaptation, and personal theme extraction.

---

## Theme Architecture

### Two Theme Categories

**Static Themes** define fixed colors that do not adapt to system appearance. Apply the same palette in light and dark OS modes.

**Dynamic Themes** provide dual palettes (light variant + dark variant) and automatically switch based on `prefers-color-scheme` or a manual toggle. MindNode's "Dynamic" section on their themes page describes these as auto-adapting to the user's current mode.

### Per-Level Hierarchical Styling

Every theme defines colors at each hierarchy level of the mind map tree:

| Level | Description | Typical Visual Role |
|-------|-------------|-------------------|
| Root | Central node | Largest, most prominent color |
| Level 1 | Direct children of root | Primary branch colors (each branch gets a different color from the palette) |
| Level 2 | Grandchildren | Lighter/desaturated variant of parent branch |
| Level 3+ | Deep descendants | Progressively softer or inherits from Level 2 |

Branch colors are assigned cyclically from the theme's palette array. All children of a Level 1 node inherit that branch's color family.

### Canvas Background

Each theme optionally specifies a canvas background color. Light themes typically use white or near-white; dark themes use deep navy or charcoal. Some themes use tinted backgrounds (e.g., Cappuccino uses warm beige, Goth Pastel uses dark gray).

---

## TypeScript Type Definitions

```ts
/** A single color stop in the hierarchy */
interface ThemeLevelColor {
  /** Node fill / background */
  fill: string;
  /** Node text color */
  text: string;
  /** Branch/edge stroke color */
  stroke: string;
  /** Optional: node border color (defaults to stroke) */
  border?: string;
}

/** A complete branch palette — colors assigned to one Level 1 subtree */
interface BranchPalette {
  level1: ThemeLevelColor;
  level2: ThemeLevelColor;
  level3Plus: ThemeLevelColor;
}

/** Canvas and global settings for a theme variant */
interface ThemeVariant {
  /** Canvas background color */
  canvasBg: string;
  /** Root node colors */
  root: ThemeLevelColor;
  /** Ordered array of branch palettes. Assigned cyclically to Level 1 children. */
  branches: BranchPalette[];
  /** Cross-connection line color */
  connectionStroke: string;
  /** Cross-connection line dash pattern (e.g., '6 4') */
  connectionDash?: string;
  /** Selection ring / highlight color */
  selectionColor: string;
  /** Text color for the outline view */
  outlineText: string;
  /** Outline view background */
  outlineBg: string;
}

type ThemeType = 'static' | 'dynamic';

interface MindNodeTheme {
  id: string;
  name: string;
  type: ThemeType;
  /** For static: single variant. For dynamic: light variant. */
  light: ThemeVariant;
  /** Only for dynamic themes — dark variant */
  dark?: ThemeVariant;
  /** User-provided personal themes are marked */
  isPersonal?: boolean;
  /** Optional metadata */
  author?: string;
  tags?: string[];
}
```

### Zustand Store Slice

```ts
import { StateCreator } from 'zustand';

interface ThemeSlice {
  /** Currently active theme */
  activeTheme: MindNodeTheme;
  /** All available themes (built-in + personal) */
  themes: MindNodeTheme[];
  /** Current mode for dynamic themes */
  colorMode: 'light' | 'dark' | 'system';
  /** Resolved variant based on colorMode + theme type */
  resolvedVariant: ThemeVariant;

  setTheme: (themeId: string) => void;
  setColorMode: (mode: 'light' | 'dark' | 'system') => void;
  addPersonalTheme: (theme: MindNodeTheme) => void;
  removePersonalTheme: (themeId: string) => void;
}

const createThemeSlice: StateCreator<ThemeSlice> = (set, get) => ({
  activeTheme: DEFAULT_THEME,
  themes: BUILT_IN_THEMES,
  colorMode: 'system',
  resolvedVariant: DEFAULT_THEME.light,

  setTheme: (themeId) => {
    const theme = get().themes.find((t) => t.id === themeId);
    if (!theme) return;
    set({
      activeTheme: theme,
      resolvedVariant: resolveVariant(theme, get().colorMode),
    });
  },

  setColorMode: (mode) => {
    set({
      colorMode: mode,
      resolvedVariant: resolveVariant(get().activeTheme, mode),
    });
  },

  addPersonalTheme: (theme) => {
    set((state) => ({ themes: [...state.themes, { ...theme, isPersonal: true }] }));
  },

  removePersonalTheme: (themeId) => {
    set((state) => ({
      themes: state.themes.filter((t) => t.id !== themeId || !t.isPersonal),
    }));
  },
});

/** Resolve which variant to use based on theme type and color mode */
function resolveVariant(theme: MindNodeTheme, mode: 'light' | 'dark' | 'system'): ThemeVariant {
  if (theme.type === 'static') return theme.light;
  const effectiveMode =
    mode === 'system'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      : mode;
  return effectiveMode === 'dark' && theme.dark ? theme.dark : theme.light;
}
```

---

## Theme Gallery

### Static Themes

Derived from MindNode's themes page. Each entry lists the theme name, canvas background, and branch color palette.

| # | Theme | Canvas BG | Root Color | Branch Palette (Level 1 cycle) | Character |
|---|-------|-----------|------------|-------------------------------|-----------|
| 1 | **Elegant** | `#FFFFFF` | `#4A90D9` (blue) | Blue, coral/pink, green, amber, purple | Clean and professional with bright saturated tones |
| 2 | **Fresh** | `#FFFFFF` | `#7C8C9C` (blue-gray) | Teal, olive, sage, gray-blue | Muted natural tones, horizontal layout tendency |
| 3 | **Rainbow (Legacy)** | `#FFFFFF` | `#FF6B6B` (coral) | Red, orange, yellow, green, blue, purple | Full spectrum, high energy, colorful |
| 4 | **Teal (Legacy)** | `#FFFFFF` | `#4DB6AC` (teal) | Teal, seafoam, aqua, muted blue | Monochromatic cool greens |
| 5 | **Atlas Blue** | `#FFFFFF` | `#3F7FBF` (mid-blue) | Blue family: cobalt, cerulean, steel, navy, sky | All-blue monochromatic |
| 6 | **Atlas Yellow** | `#FFFFFF` | `#E6A817` (gold) | Amber, gold, honey, mustard, tan | Warm monochromatic golds |
| 7 | **Atlas Green** | `#FFFFFF` | `#4CAF50` (green) | Forest, sage, emerald, lime, olive | Green family monochromatic |
| 8 | **Atlas Pink** | `#FFFFFF` | `#E91E90` (hot pink) | Fuchsia, rose, salmon, blush, magenta | Pink family monochromatic |
| 9 | **Atlas Purple** | `#FFFFFF` | `#7B42D1` (purple) | Violet, lavender, plum, amethyst, grape | Purple family monochromatic |
| 10 | **Atlas Orange** | `#FFFFFF` | `#F57C00` (orange) | Tangerine, peach, burnt orange, apricot, rust | Orange family monochromatic |
| 11 | **Natural** | `#F5F0E8` (warm cream) | `#6B705C` (olive) | Olive, sienna, sage, warm gray, terracotta | Earthy, organic, warm neutral |
| 12 | **Pixel** | `#FFFFFF` | `#333333` (dark gray) | Bright primaries: red, blue, green, yellow, magenta | Retro 8-bit palette, high contrast |
| 13 | **Pleasant** | `#FFFFFF` | `#6C63FF` (purple) | Purple, coral, teal, amber, rose | MindNode's own brand palette |
| 14 | **Small Capacitor** | `#1A1A2E` (dark navy) | `#FF6B4A` (red-orange) | Neon green, electric blue, hot pink, amber on dark bg | Dark theme, circuit-board aesthetic |
| 15 | **Modern II** | `#FFFFFF` | `#2D3748` (charcoal) | Slate blue, muted rose, sage, steel | Professional, desaturated |
| 16 | **Neon Bamboo** | `#1A2E1A` (dark green) | `#00FF88` (neon green) | Neon green, lime, chartreuse, emerald | Dark theme, green neon glow |
| 17 | **Goth Pastel** | `#2D2D3D` (dark gray-purple) | `#C9A0DC` (light purple) | Pastel purple, pastel pink, pastel blue, pastel mint on dark bg | Soft pastels on dark background |
| 18 | **Twilight** | `#1A1A3E` (deep navy) | `#7B68EE` (medium slate blue) | Lavender, periwinkle, soft violet, muted cyan | Dusky evening palette on navy |
| 19 | **Cappuccino** | `#F5E6D3` (warm beige) | `#8B6914` (coffee brown) | Espresso, caramel, cream, mocha, latte | Warm coffee tones |
| 20 | **Dark Pastel** | `#2A2A3A` (dark gray) | `#FFB3BA` (pastel pink) | Pastel pink, pastel yellow, pastel green, pastel blue on dark | Candy pastels on dark |
| 21 | **Minimalist** | `#FFFFFF` | `#333333` (near-black) | Grayscale: dark gray, medium gray, light gray | Monochrome, typography-focused |
| 22 | **Roadmap** | `#FFFFFF` | `#4A90D9` (blue) | Blue, green, amber, red (status colors) | Project/timeline oriented |
| 23 | **Winter Day** | `#F0F8FF` (alice blue) | `#4A7FB5` (winter blue) | Ice blue, silver, frost, slate | Cool winter light palette |
| 24 | **Winter Night** | `#0D1B2A` (midnight blue) | `#A8C8E8` (pale blue) | Pale blue, silver, ice white, dark teal on midnight | Winter dark complement |

### Dynamic Themes

Dynamic themes auto-switch between light and dark variants. Listed at the bottom of MindNode's theme gallery. These adapt based on `prefers-color-scheme`.

| Theme | Light Variant | Dark Variant |
|-------|--------------|-------------|
| **MindNode Default** | White canvas, purple root, pastel branches | Navy canvas, bright purple root, vivid branches |
| **Professional** | Clean white, slate root, muted branches | Charcoal canvas, light text, soft branch colors |

---

## Theme Implementation

### CSS Custom Property Generation

Generate CSS custom properties from a resolved `ThemeVariant` for consumption by React components and Tailwind:

```ts
function generateThemeCSS(variant: ThemeVariant): Record<string, string> {
  const vars: Record<string, string> = {
    '--mn-canvas-bg': variant.canvasBg,
    '--mn-root-fill': variant.root.fill,
    '--mn-root-text': variant.root.text,
    '--mn-root-stroke': variant.root.stroke,
    '--mn-connection-stroke': variant.connectionStroke,
    '--mn-selection-color': variant.selectionColor,
    '--mn-outline-text': variant.outlineText,
    '--mn-outline-bg': variant.outlineBg,
  };

  if (variant.connectionDash) {
    vars['--mn-connection-dash'] = variant.connectionDash;
  }

  variant.branches.forEach((branch, i) => {
    const prefix = `--mn-branch-${i}`;
    vars[`${prefix}-l1-fill`] = branch.level1.fill;
    vars[`${prefix}-l1-text`] = branch.level1.text;
    vars[`${prefix}-l1-stroke`] = branch.level1.stroke;
    vars[`${prefix}-l2-fill`] = branch.level2.fill;
    vars[`${prefix}-l2-text`] = branch.level2.text;
    vars[`${prefix}-l2-stroke`] = branch.level2.stroke;
    vars[`${prefix}-l3-fill`] = branch.level3Plus.fill;
    vars[`${prefix}-l3-text`] = branch.level3Plus.text;
    vars[`${prefix}-l3-stroke`] = branch.level3Plus.stroke;
  });

  return vars;
}
```

### Applying Theme to DOM

```tsx
import { useEffect } from 'react';

function useApplyTheme(variant: ThemeVariant) {
  useEffect(() => {
    const vars = generateThemeCSS(variant);
    const root = document.documentElement;
    Object.entries(vars).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });
    return () => {
      Object.keys(vars).forEach((key) => {
        root.style.removeProperty(key);
      });
    };
  }, [variant]);
}
```

### Resolving Branch Colors for a Node

Given a node's depth and its Level 1 ancestor's branch index, resolve the correct colors:

```ts
function getNodeColors(
  variant: ThemeVariant,
  depth: number,
  branchIndex: number,
): ThemeLevelColor {
  if (depth === 0) return variant.root;

  const palette = variant.branches[branchIndex % variant.branches.length];

  if (depth === 1) return palette.level1;
  if (depth === 2) return palette.level2;
  return palette.level3Plus;
}
```

---

## Theme Switching

### Light/Dark Toggle + Custom Themes

```tsx
function ThemeSwitcher() {
  const { activeTheme, colorMode, setColorMode, themes, setTheme } = useThemeStore();

  return (
    <div className="flex items-center gap-4">
      {/* Color mode toggle (only meaningful for dynamic themes) */}
      {activeTheme.type === 'dynamic' && (
        <div className="flex rounded-full border border-[var(--mn-border)] p-0.5">
          {(['light', 'system', 'dark'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setColorMode(mode)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors
                ${colorMode === mode
                  ? 'bg-mn-purple text-white'
                  : 'text-[var(--mn-text-secondary)] hover:text-[var(--mn-text-primary)]'
                }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      )}

      {/* Theme gallery grid */}
      <div className="grid grid-cols-4 gap-3">
        {themes.map((theme) => (
          <button
            key={theme.id}
            onClick={() => setTheme(theme.id)}
            className={`group relative rounded-[var(--mn-radius-lg)] border-2 p-2
              transition-all duration-150
              ${activeTheme.id === theme.id
                ? 'border-mn-purple shadow-mn-node-hover'
                : 'border-transparent hover:border-[var(--mn-border)]'
              }`}
          >
            <ThemePreview theme={theme} />
            <span className="mt-1 block text-center text-xs font-medium
                           text-[var(--mn-text-secondary)]">
              {theme.name}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

### Theme Preview Thumbnail

Render a miniature mind map preview showing the theme's color palette:

```tsx
function ThemePreview({ theme }: { theme: MindNodeTheme }) {
  const variant = theme.light;

  return (
    <div
      className="aspect-[4/3] overflow-hidden rounded-[var(--mn-radius-md)]"
      style={{ backgroundColor: variant.canvasBg }}
    >
      <svg viewBox="0 0 120 90" className="h-full w-full">
        {/* Root node */}
        <rect
          x="45" y="35" width="30" height="18" rx="6"
          fill={variant.root.fill}
        />
        {/* Branch previews */}
        {variant.branches.slice(0, 4).map((branch, i) => {
          const angle = ((i - 1.5) * Math.PI) / 4;
          const x = 60 + Math.cos(angle) * 40;
          const y = 44 + Math.sin(angle) * 30;
          return (
            <g key={i}>
              <line
                x1="60" y1="44" x2={x} y2={y}
                stroke={branch.level1.stroke} strokeWidth="2"
              />
              <rect
                x={x - 10} y={y - 6} width="20" height="12" rx="4"
                fill={branch.level1.fill}
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
}
```

---

## Personal Theme Extraction

Allow users to create a personal theme from the current document's node colors:

```ts
interface ExtractedThemeInput {
  rootColor: string;
  branchColors: string[]; // Level 1 node fills from the document
  canvasBg: string;
}

function extractPersonalTheme(
  input: ExtractedThemeInput,
  name: string,
): MindNodeTheme {
  const branches: BranchPalette[] = input.branchColors.map((color) => ({
    level1: {
      fill: color,
      text: getContrastText(color),
      stroke: color,
    },
    level2: {
      fill: lighten(color, 0.3),
      text: getContrastText(lighten(color, 0.3)),
      stroke: lighten(color, 0.15),
    },
    level3Plus: {
      fill: lighten(color, 0.5),
      text: getContrastText(lighten(color, 0.5)),
      stroke: lighten(color, 0.3),
    },
  }));

  return {
    id: `personal-${Date.now()}`,
    name,
    type: 'static',
    isPersonal: true,
    light: {
      canvasBg: input.canvasBg,
      root: {
        fill: input.rootColor,
        text: getContrastText(input.rootColor),
        stroke: input.rootColor,
      },
      branches,
      connectionStroke: '#9898AD',
      selectionColor: '#6C63FF',
      outlineText: '#1A1A2E',
      outlineBg: '#FFFFFF',
    },
  };
}

/** Return white or dark text based on luminance */
function getContrastText(hex: string): string {
  const rgb = hexToRgb(hex);
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
  return luminance > 0.5 ? '#1A1A2E' : '#FFFFFF';
}

/** Lighten a hex color by a factor (0-1) */
function lighten(hex: string, factor: number): string {
  const rgb = hexToRgb(hex);
  return rgbToHex({
    r: Math.round(rgb.r + (255 - rgb.r) * factor),
    g: Math.round(rgb.g + (255 - rgb.g) * factor),
    b: Math.round(rgb.b + (255 - rgb.b) * factor),
  });
}
```

---

## Theme Persistence

Store the active theme ID and color mode preference in localStorage. Restore on app load:

```ts
const THEME_STORAGE_KEY = 'mn-active-theme';
const COLOR_MODE_KEY = 'mn-color-mode';

function persistThemeChoice(themeId: string, colorMode: string): void {
  localStorage.setItem(THEME_STORAGE_KEY, themeId);
  localStorage.setItem(COLOR_MODE_KEY, colorMode);
}

function loadThemeChoice(): { themeId: string; colorMode: 'light' | 'dark' | 'system' } {
  return {
    themeId: localStorage.getItem(THEME_STORAGE_KEY) ?? 'mindnode-default',
    colorMode: (localStorage.getItem(COLOR_MODE_KEY) as 'light' | 'dark' | 'system') ?? 'system',
  };
}
```

### System Appearance Listener

```ts
function useSystemAppearance(callback: (isDark: boolean) => void) {
  useEffect(() => {
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => callback(e.matches);
    mql.addEventListener('change', handler);
    callback(mql.matches);
    return () => mql.removeEventListener('change', handler);
  }, [callback]);
}
```
