## shadcn CLI v4 Reference

### Commands

| Command | Purpose | Key Flags |
|---------|---------|-----------|
| `shadcn init` | Initialize config and dependencies | `--preset`, `--template`, `--base`, `--monorepo` |
| `shadcn add <name>` | Add components/blocks/hooks | `--dry-run`, `--diff`, `--overwrite`, `--path` |
| `shadcn view <name>` | Inspect registry items before installing | Supports namespaced registries |
| `shadcn search [query]` | Search registries for items | Alias: `shadcn list` |
| `shadcn build` | Generate registry JSON from `registry.json` | `--output` |
| `shadcn docs <component>` | Fetch docs and API reference | Useful for agent context |
| `shadcn info` | Project state (framework, components, aliases) | `--json` for machine-readable |
| `shadcn migrate <type>` | Run migrations: `icons`, `radix`, `rtl` | |
| `shadcn diff <name>` | Show upstream changes vs local | |

### init

```bash
# Interactive setup
npx shadcn@latest init

# With project template
npx shadcn@latest init --template next
npx shadcn@latest init --template vite
npx shadcn@latest init --template astro
npx shadcn@latest init --template react-router
npx shadcn@latest init --template laravel
npx shadcn@latest init --template tanstack-start

# Monorepo (Turborepo structure)
npx shadcn@latest init --template next --monorepo

# With design preset (encodes colors, theme, icons, fonts, radius)
npx shadcn@latest init --preset adtk27v

# Choose primitive library
npx shadcn@latest init --base radix
npx shadcn@latest init --base base-ui
```

`create` is an alias for `init`.

### add

```bash
# Single or multiple components
npx shadcn@latest add button
npx shadcn@latest add button card dialog

# From custom registry URL
npx shadcn@latest add https://example.com/r/my-component.json

# From namespaced registry
npx shadcn@latest add @myregistry/component-name

# Add a block (pre-built page section)
npx shadcn@latest add login-01

# Preview before writing
npx shadcn@latest add --dry-run button

# Overwrite existing files
npx shadcn@latest add --overwrite button

# Re-add all with overwrite (bulk update)
npx shadcn@latest add --all --overwrite
```

### Presets (CLI v4)

Presets encode an entire design system into a short code: colors, theme, icon library, fonts, radius.

- Build at `https://ui.shadcn.com/create`
- Apply: `npx shadcn@latest init --preset <code>`
- Switch mid-project: reconfigures everything including installed components
- Share with teams or embed in AI agent prompts

### Monorepo Structure

```
my-monorepo/
  apps/
    web/
      components.json      # App-specific (blocks, pages)
      components/
  packages/
    ui/
      components.json      # Shared UI
      components/ui/
      lib/
      hooks/
```

Running `add button` from `apps/web/` installs to `packages/ui/`.
Running `add login-01` installs UI deps to `packages/ui/`, block to `apps/web/components/`.

Requirements:
- Every workspace needs its own `components.json`
- Same `style`, `iconLibrary`, and `baseColor` across all configs
- For Tailwind v4, leave `tailwind.config` empty

### Migrations

```bash
# Migrate to unified radix-ui package
npx shadcn@latest migrate radix

# Convert CSS to logical properties for RTL
npx shadcn@latest migrate rtl

# Update icon imports
npx shadcn@latest migrate icons
```
