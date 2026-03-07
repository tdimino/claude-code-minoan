---
name: cloudflare
description: Cloudflare platform management via Wrangler CLI. Deploy Pages sites, manage Workers, KV namespaces, R2 buckets, D1 databases, Queues, Vectorize indexes, Workflows, and Hyperdrive connections. Use when deploying to Cloudflare, managing CF infrastructure, configuring wrangler.toml, working with CF storage services, or setting up Cloudflare Pages projects. Triggers on Cloudflare, wrangler, Pages deploy, KV namespace, R2 bucket, D1 database, CF Workers, Cloudflare DNS, Vectorize, Queues, Workflows, Hyperdrive.
---

# Cloudflare & Wrangler CLI

Manage Cloudflare infrastructure from the terminal: Pages, Workers, KV, R2, D1, Queues, Vectorize, and more.

## Prerequisites

```bash
# Install
npm install -g wrangler

# Authenticate (opens browser OAuth flow)
wrangler login

# Verify
wrangler whoami
```

**Environment variables** (alternative to `wrangler login`):
- `CLOUDFLARE_API_TOKEN` — scoped API token (recommended for CI/CD)
- `CLOUDFLARE_ACCOUNT_ID` — your account ID (found in dashboard URL)

## Quick Start

```bash
# Deploy a static site to Cloudflare Pages
npm run build && wrangler pages deploy out --project-name mysite
```

---

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------
| `wrangler pages deploy` | Deploy static site | `wrangler pages deploy out --project-name mysite` |
| `wrangler pages project list` | List Pages projects | `wrangler pages project list` |
| `wrangler deploy` | Deploy Worker | `wrangler deploy` |
| `wrangler dev` | Local dev server | `wrangler dev` |
| `wrangler tail` | Stream live logs | `wrangler tail my-worker` |
| `wrangler kv namespace list` | List KV namespaces | `wrangler kv namespace list` |
| `wrangler r2 bucket list` | List R2 buckets | `wrangler r2 bucket list` |
| `wrangler d1 list` | List D1 databases | `wrangler d1 list` |
| `wrangler secret put` | Set encrypted secret | `wrangler secret put API_KEY` |
| `wrangler whoami` | Check auth status | `wrangler whoami` |

**Full CLI reference:** `references/wrangler-commands.md`

---

## Pages

Primary use case for static site deployment (Next.js `output: 'export'`, Astro, etc.).

### Deploy

```bash
# Direct deploy (no git integration needed)
npm run build
wrangler pages deploy out --project-name worldwarwatcher

# With commit tracking
wrangler pages deploy out --project-name mysite --commit-hash $(git rev-parse HEAD) --commit-message "$(git log -1 --format=%s)"

# Preview deploy (non-production branch)
wrangler pages deploy out --project-name mysite --branch staging
```

### Project Management

```bash
wrangler pages project create mysite --production-branch main
wrangler pages project list
wrangler pages project delete mysite
```

### Deployment History & Rollback

```bash
wrangler pages deployment list --project-name mysite
wrangler pages deployment tail --project-name mysite    # Stream logs
```

To rollback: redeploy a previous build directory, or use the dashboard to promote an earlier deployment.

### Custom Domains

Custom domain management is **dashboard-only** — wrangler cannot add/remove custom domains for Pages projects. Use the Cloudflare dashboard:
1. Workers & Pages → project → Custom Domains → Add
2. CF auto-creates DNS records and provisions TLS

### Pages Config Files

Place `_headers` and `_redirects` in your static assets directory (e.g., `public/` for Next.js, Astro, Vite) — the build process copies them to the output root.

**Details:** `references/pages-config.md` — `_headers` format, `_redirects` format, framework presets, preview deploys.

---

## Workers

```bash
# Create new Worker project (C3 scaffolding)
npm create cloudflare@latest my-worker

# Local development (with hot reload)
wrangler dev

# Deploy to production
wrangler deploy

# Stream live logs
wrangler tail my-worker
```

Note: `wrangler init` is deprecated — use `npm create cloudflare@latest` instead.

---

## Storage & Data Services

| Service | Purpose | Key Commands |
|---------|---------|-------------|
| **KV** | Key-value store | `kv namespace create/list`, `kv key put/get/list/delete` |
| **R2** | Object storage (S3-compatible) | `r2 bucket create/list`, `r2 object put/get/delete` |
| **D1** | SQLite database | `d1 create/list`, `d1 execute --remote`, `d1 migrations apply --remote` |
| **Queues** | Message queues between Workers | `queues create/list/delete`, `queues consumer add/remove` |
| **Vectorize** | Vector DB for AI/embeddings | `vectorize create/list/delete`, `vectorize insert` |
| **Hyperdrive** | Connection pooling for external DBs | `hyperdrive create/list/delete` |

**Important:** D1 commands default to the local dev database. Add `--remote` to target production:
```bash
wrangler d1 execute my-database --command "SELECT * FROM users" --remote
```

**Full command reference with all flags:** `references/wrangler-commands.md`

---

## Secrets

```bash
wrangler secret put SECRET_NAME          # Prompts for value
echo "value" | wrangler secret put SECRET_NAME  # From stdin
wrangler secret list
wrangler secret bulk secrets.json        # Bulk upload
```

---

## Common Workflows

### CI/CD with GitHub Actions

```yaml
# .github/workflows/deploy.yml
- name: Deploy to Cloudflare Pages
  uses: cloudflare/wrangler-action@v3
  with:
    apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
    command: pages deploy out --project-name mysite
```

Note: In CI/CD (non-interactive), create the project first with `wrangler pages project create` — auto-creation only works interactively.

### Tail Production Logs

```bash
wrangler tail my-worker --format pretty
wrangler pages deployment tail --project-name mysite
```

---

## Troubleshooting

```bash
# Check auth
wrangler whoami

# Re-authenticate
wrangler logout && wrangler login

# Check wrangler version
wrangler --version

# Verbose output for debugging
WRANGLER_LOG=debug wrangler pages deploy out --project-name mysite
```

- **"Authentication error"** — Run `wrangler login` or set `CLOUDFLARE_API_TOKEN`
- **"Project not found"** — Check project name: `wrangler pages project list`
- **"Build output not found"** — Verify build output directory exists. See `references/pages-config.md` for framework-to-directory mapping.
- **Pages deploy hangs** — Check `_headers`/`_redirects` syntax (no YAML, plain text format)
- **Deploy includes too many files** — Ensure `--directory` points to the build output only (e.g., `out/`, `dist/`), not the project root

---

## Reference Documentation

| File | Contents |
|------|----------|
| `references/wrangler-commands.md` | Full Wrangler CLI command reference with all flags |
| `references/pages-config.md` | Pages config: `_headers`, `_redirects`, build presets, env vars |
