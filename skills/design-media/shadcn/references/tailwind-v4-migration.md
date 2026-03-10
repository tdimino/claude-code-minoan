## Tailwind CSS v4 Migration

### Breaking Changes (February 2025+)

| Change | Before | After |
|--------|--------|-------|
| Color space | HSL (`hsl(var(--primary))`) | OKLCH (`oklch(0.205 0.03 264.05)`) |
| Theme config | `tailwind.config.ts` | `@theme` / `@theme inline` in CSS |
| Animation | `tailwindcss-animate` | `tw-animate-css` |
| Ref forwarding | `React.forwardRef<>` | `React.ComponentProps<>` |
| Slot attributes | className composition | `data-slot` attributes |
| Default style | `"default"` | `"new-york"` (only option) |
| Toast | `toast` component | `sonner` |
| Size utility | `w-* h-*` | `size-*` (from Tailwind 3.4) |

### Upgrade Steps

1. **Run Tailwind's codemod**:
```bash
npx @tailwindcss/upgrade@next
```

2. **Update CSS structure**:
```css
/* Move :root and .dark OUT of @layer base */
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
}

/* Wrap color values in @theme inline */
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
}
```

3. **Replace animation library**:
```bash
npm uninstall tailwindcss-animate
npm install -D tw-animate-css
```
```css
/* In globals.css */
@import "tw-animate-css";
```

4. **Remove forwardRef** (optional codemod):
```bash
npx react-codemod remove-forward-ref
```
Or manually convert:
```tsx
// Before
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, ...props }, ref) => (
    <button ref={ref} className={cn("...", className)} {...props} />
  )
)

// After
function Button({ className, ...props }: React.ComponentProps<"button">) {
  return <button className={cn("...", className)} {...props} />
}
```

5. **Re-add components to get updated versions**:
```bash
npx shadcn@latest add --all --overwrite
```

6. **Update chart configs**: Remove `hsl()` wrappers from chart color references.

7. **Use `size-*`**: Replace `w-4 h-4` with `size-4` throughout.

### `components.json` for v4

```json
{
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "zinc",
    "cssVariables": true
  }
}
```

Leave `config` blank — no `tailwind.config.ts` needed.

### `data-slot` Attributes

Every shadcn primitive now has `data-slot` for targeted styling without class props:

```tsx
<Button data-slot="trigger">Click me</Button>
```

Style with attribute selectors:
```css
[data-slot="trigger"] { /* styles */ }
```

### tw-animate-css Classes

Common animation utilities (replaces tailwindcss-animate):
- `animate-in`, `animate-out`
- `fade-in`, `fade-out`
- `slide-in-from-top`, `slide-in-from-bottom`, `slide-in-from-left`, `slide-in-from-right`
- `zoom-in`, `zoom-out`
- Duration/delay: `duration-*`, `delay-*`
