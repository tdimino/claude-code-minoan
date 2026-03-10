## components.json Configuration

Created by `shadcn init`. Central configuration for the CLI.

### Full Schema

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "zinc",
    "cssVariables": true,
    "prefix": ""
  },
  "iconLibrary": "lucide",
  "aliases": {
    "components": "@/components",
    "ui": "@/components/ui",
    "utils": "@/lib/utils",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "menuColor": "default",
  "menuAccent": "subtle",
  "rtl": false,
  "registries": {
    "@mycompany": {
      "url": "https://ui.mycompany.com/r/{name}.json"
    }
  }
}
```

### Field Reference

| Field | Type | Notes |
|-------|------|-------|
| `style` | string | `"new-york"` (default). `"default"` is deprecated. Also: `radix-vega`, `radix-nova`, `radix-maia`, `radix-lyra`, `radix-mira`, `base-vega`, `base-nova`, `base-maia`, `base-lyra`, `base-mira`. **Cannot change after init.** |
| `rsc` | boolean | `true` adds `"use client"` directive to client components. Set `true` for Next.js App Router. |
| `tsx` | boolean | `false` generates `.jsx` instead of `.tsx`. |
| `tailwind.config` | string | Path to `tailwind.config.js`. **Leave blank for Tailwind v4.** |
| `tailwind.css` | string | Path to CSS file importing Tailwind (e.g. `app/globals.css`). |
| `tailwind.baseColor` | string | Base palette: Neutral, Stone, Zinc, Mauve, Olive, Mist, Taupe. **Cannot change after init.** |
| `tailwind.cssVariables` | boolean | `true` = CSS custom properties (recommended). **Cannot change after init.** |
| `tailwind.prefix` | string | Optional prefix for all Tailwind utilities. |
| `iconLibrary` | string | Icon library used by components (e.g. `"lucide"`). |
| `aliases.*` | string | Import path aliases matching `tsconfig.json` paths. |
| `menuColor` | string | `"default"` or `"inverted"`. |
| `menuAccent` | string | `"subtle"` or `"bold"`. |
| `rtl` | boolean | Enable right-to-left layout support. |
| `registries` | object | Namespaced registry URLs with `{name}` placeholder. Supports auth headers. |

### Registry Auth Patterns

```json
{
  "registries": {
    "@private": {
      "url": "https://registry.internal.com/r/{name}.json",
      "headers": {
        "Authorization": "Bearer ${PRIVATE_REGISTRY_TOKEN}"
      }
    },
    "@simple": "https://ui.example.com/r/{name}.json"
  }
}
```

Environment variable expansion via `${VAR_NAME}` in header values.

### Immutable Fields

These cannot be changed after `init` — choose carefully:
- `style`
- `tailwind.baseColor`
- `tailwind.cssVariables`
