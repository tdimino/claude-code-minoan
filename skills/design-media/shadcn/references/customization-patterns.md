## Component Customization Patterns

shadcn components are source files you own. These patterns keep customizations maintainable while preserving the ability to pull upstream updates.

### Pattern 1: Wrapper Composition (Preferred)

Create project-specific wrappers that compose shadcn primitives:

```tsx
// components/app/submit-button.tsx
import { Button, type ButtonProps } from "@/components/ui/button"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface SubmitButtonProps extends ButtonProps {
  loading?: boolean
}

export function SubmitButton({ loading, children, className, disabled, ...props }: SubmitButtonProps) {
  return (
    <Button
      className={cn("min-w-[120px]", className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="mr-2 size-4 animate-spin" />}
      {children}
    </Button>
  )
}
```

Benefits:
- Base `button.tsx` stays untouched — can re-add from registry freely
- Project-specific logic isolated in wrapper
- Multiple wrapper variants possible from same base

### Pattern 2: data-slot Styling

Target component internals via `data-slot` attributes without modifying source:

```css
/* In globals.css or component CSS */
[data-slot="card"] {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

[data-slot="card-header"] {
  padding-block: 1.5rem;
}
```

### Pattern 3: cn() Class Merging

Always use `cn()` for class composition — it handles Tailwind class conflicts:

```tsx
import { cn } from "@/lib/utils"

// Later classes override earlier ones
cn("px-4 py-2", "px-6")  // → "py-2 px-6"

// Conditional classes
cn("base-class", isActive && "active-class", className)
```

### Pattern 4: Structural Edits (Base Component)

Edit the base component directly only for structural changes — when the wrapper pattern adds too much indirection:

```tsx
// components/ui/button.tsx — direct edit
// Add a new variant to buttonVariants
const buttonVariants = cva("...", {
  variants: {
    variant: {
      default: "...",
      destructive: "...",
      // YOUR ADDITION:
      ghost_accent: "hover:bg-accent/50 text-accent-foreground",
    },
  },
})
```

After structural edits, `npx shadcn@latest diff button` shows your changes vs upstream. Use this before re-adding to manually merge.

### Pattern 5: Theme-Level Customization

Many visual changes belong in CSS variables, not component code:

```css
:root {
  --radius: 0.625rem;  /* Global border radius */
}

/* Component-scoped overrides */
[data-slot="input"] {
  --ring: var(--primary);
}
```

### Tracking Upstream Changes

```bash
# See what changed upstream for a specific component
npx shadcn@latest diff button

# See all components with upstream changes
npx shadcn@latest diff
```

Always commit your customizations before running `add --overwrite` on an existing component.

### The cn() Utility

Installed at your `utils` alias path (default `@/lib/utils`):

```ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

`clsx` handles conditional joining. `twMerge` resolves Tailwind class conflicts (later wins).
