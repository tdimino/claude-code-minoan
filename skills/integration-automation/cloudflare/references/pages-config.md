# Cloudflare Pages Configuration

## Build Settings

### Framework Presets

| Framework | Build Command | Output Dir |
|-----------|--------------|------------|
| Next.js (static export) | `npx next build` | `out` |
| Astro | `npx astro build` | `dist` |
| Vite / React | `npx vite build` | `dist` |
| Create React App | `npx react-scripts build` | `build` |
| SvelteKit (static) | `npx vite build` | `build` |
| Hugo | `hugo` | `public` |
| 11ty | `npx @11ty/eleventy` | `_site` |

### Environment Variables

Set in dashboard (Workers & Pages → project → Settings → Environment Variables) or via wrangler.toml for Workers.

| Variable | Purpose | Example |
|----------|---------|---------
| `NODE_VERSION` | Node.js version for build | `22` |
| `NPM_FLAGS` | Flags passed to npm install | `--prefer-offline` |
| `YARN_VERSION` | Use specific Yarn version | `1.22.19` |

Preview vs Production environments can have different env vars.

### System Environment Variables

These are automatically set during Pages builds:

| Variable | Value |
|----------|-------|
| `CI` | `true` |
| `CF_PAGES` | `1` |
| `CF_PAGES_COMMIT_SHA` | Git commit SHA |
| `CF_PAGES_BRANCH` | Git branch name |
| `CF_PAGES_URL` | Deployment URL |

## `_headers` File

Place in build output root (or `public/` for frameworks that copy static files).

### Format

```
# Path pattern
/path/*
  Header-Name: header-value
  Another-Header: value

# Multiple paths
/api/*
  Access-Control-Allow-Origin: *

/_next/static/*
  Cache-Control: public, max-age=31536000, immutable
```

### Rules

- Indentation: 2 spaces before header name (required)
- Path patterns: `*` matches any path segment(s)
- Max 100 header rules per project
- Max 2,000 characters per rule
- Headers from all matching rules are merged; for duplicate header names, the most specific path pattern takes precedence
- Use `! Header-Name` to detach (remove) an inherited header

### Common Patterns

```
# Cache static assets forever
/_next/static/*
  Cache-Control: public, max-age=31536000, immutable

# Short cache for data files
/data/*
  Cache-Control: public, max-age=300, stale-while-revalidate=600

# Security headers for all pages
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
```

## `_redirects` File

Place alongside `_headers` in build output root.

### Format

```
# Source  Destination  StatusCode
/old-path /new-path 301
/blog/* /posts/:splat 302
https://www.example.com/* https://example.com/:splat 301
```

### Rules

- One redirect per line
- Status codes: `301` (permanent), `302` (temporary), `200` (rewrite/proxy)
- `*` wildcard captures path segments; `:splat` references the capture in the destination
- Max 2,000 static redirect rules; dynamic redirects: 100 (Free), 500 (Pro), 1,000 (Business/Enterprise)
- Evaluated top-to-bottom; first match wins

### Common Patterns

```
# www to apex
https://www.example.com/* https://example.com/:splat 301

# Old URL structure (use * + :splat, not named params)
/blog/* /posts/:splat 301

# SPA fallback (serve index.html for all routes)
/* /index.html 200
```

Note: Cloudflare Pages `_redirects` only supports `*` wildcard with `:splat` replacement. Named placeholders (`:param`) are not supported.

## Custom Domains

Typically managed via dashboard (Workers & Pages → project → Custom Domains):

1. Add domain → CF auto-creates CNAME DNS record
2. TLS provisioned automatically (Let's Encrypt)
3. Both apex (`example.com`) and subdomains (`www.example.com`) supported

## Preview Deployments

- Every push to a non-production branch creates a preview deploy
- URL pattern: `<branch>.<project>.pages.dev`
- Each commit gets a unique URL: `<hash>.<project>.pages.dev`
- Preview deploys share the same project settings but can have separate env vars
- Deploy a preview via CLI: `wrangler pages deploy out --project-name mysite --branch staging`
