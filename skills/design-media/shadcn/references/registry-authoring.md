## Custom Registry Authoring

shadcn registries distribute source code — components, hooks, pages, configs — via JSON manifests served over HTTP.

### Creating a Registry

1. **Define `registry.json`** at project root:

```json
{
  "$schema": "https://ui.shadcn.com/schema/registry.json",
  "name": "my-registry",
  "homepage": "https://my-registry.com",
  "items": [
    {
      "name": "data-grid",
      "type": "registry:ui",
      "title": "Data Grid",
      "description": "A sortable, filterable data grid",
      "dependencies": ["@tanstack/react-table"],
      "registryDependencies": ["table", "button", "input"],
      "files": [
        {
          "path": "registry/new-york/data-grid/data-grid.tsx",
          "type": "registry:component"
        }
      ]
    }
  ]
}
```

2. **Build the registry**:

```bash
npx shadcn@latest build
npx shadcn@latest build --output custom-dir  # default: public/r/
```

Generates per-item JSON files (e.g. `public/r/data-grid.json`).

3. **Serve and install**:

```bash
# Direct URL
npx shadcn@latest add https://my-registry.com/r/data-grid.json

# Or configure as namespaced registry in components.json
npx shadcn@latest add @myregistry/data-grid
```

### Registry Item Types

| Type | Purpose |
|------|---------|
| `registry:ui` | UI components (installed to `components/ui/`) |
| `registry:component` | General components |
| `registry:lib` | Library utilities |
| `registry:hook` | React hooks |
| `registry:page` | Full pages |
| `registry:block` | Page sections/blocks |
| `registry:base` | Entire design system (components, CSS vars, fonts, config) |
| `registry:font` | Font installation and configuration |
| `registry:theme` | Theme configuration |
| `registry:ai` | AI prompts/configurations |

### Namespaced Registries

Configure in `components.json`:

```json
{
  "registries": {
    "@acme": "https://ui.acme.com/r/{name}.json",
    "@clerk": {
      "url": "https://clerk.com/registry/{name}.json"
    },
    "@private": {
      "url": "https://internal.com/r/{name}.json",
      "headers": {
        "Authorization": "Bearer ${REGISTRY_TOKEN}"
      }
    }
  }
}
```

Then install with namespace prefix:

```bash
npx shadcn@latest add @acme/data-grid
npx shadcn@latest view @clerk/sign-in
npx shadcn@latest search @acme
```

Features:
- `{name}` and `{style}` URL placeholders
- Environment variable expansion in headers (`${VAR_NAME}`)
- Cross-registry dependency resolution
- Local version overrides (your copy takes precedence)

### Registry Template

GitHub: `shadcn-ui/registry-template` — pre-configured Next.js project ready to deploy as a shadcn registry. Clone and customize.

### Dependencies

Items can declare:
- `dependencies`: npm packages to install (e.g. `@tanstack/react-table`)
- `registryDependencies`: Other shadcn items required (e.g. `["table", "button"]`)
- `devDependencies`: Dev-only npm packages
