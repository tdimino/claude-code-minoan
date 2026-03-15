# Wrangler CLI Command Reference

## Global Flags

| Flag | Purpose |
|------|---------|
| `-c, --config <path>` | Path to wrangler.toml / wrangler.jsonc (default: `./wrangler.toml`) |
| `--env <name>` | Environment to use (matches `[env.<name>]` in config) |
| `--cwd <path>` | Run as if started in specified directory |
| `--env-file <path>` | Path to .env file to load (repeatable) |

Note: `wrangler.jsonc` / `wrangler.json` is natively supported in Wrangler v4 — no flag needed.

## Authentication

| Command | Purpose |
|---------|---------|
| `wrangler login` | OAuth browser login |
| `wrangler logout` | Revoke local credentials |
| `wrangler whoami` | Show authenticated account |

Environment variables override login:
- `CLOUDFLARE_API_TOKEN` — API token (recommended)
- `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL` — legacy global key
- `CLOUDFLARE_ACCOUNT_ID` — target account

## Pages Commands

### `wrangler pages project`

```bash
wrangler pages project create <name> [--production-branch <branch>]
wrangler pages project list
wrangler pages project delete <name> [--yes]
```

### `wrangler pages deploy`

```bash
wrangler pages deploy <directory> [flags]
```

| Flag | Purpose | Default |
|------|---------|---------|
| `--project-name <name>` | Target project (required) | — |
| `--branch <branch>` | Git branch for this deploy | Current branch |
| `--commit-hash <hash>` | Commit SHA to associate | — |
| `--commit-message <msg>` | Commit message to display | — |
| `--commit-dirty` | Allow dirty git state | false |
| `--skip-caching` | Skip asset caching | false |
| `--no-bundle` | Skip bundling | false |
| `--upload-source-maps` | Upload source maps | false |

### `wrangler pages deployment`

```bash
wrangler pages deployment list --project-name <name>
wrangler pages deployment tail --project-name <name> [--deployment-id <id>]
```

## Workers Commands

### Creating Workers

```bash
# Recommended: use C3 scaffolding (wrangler init is deprecated)
npm create cloudflare@latest [name]
```

### `wrangler dev`

```bash
wrangler dev [script] [flags]
```

| Flag | Purpose | Default |
|------|---------|---------|
| `--port <port>` | Local dev server port | 8787 |
| `--ip <address>` | Bind address | localhost |
| `--local` | Run entirely locally (Miniflare) | true |
| `--remote` | Run on Cloudflare edge | false |
| `--persist-to <path>` | Persist local state | `.wrangler/state/v3` |
| `--test-scheduled` | Test cron triggers | false |
| `--inspector-port <port>` | DevTools inspector port | 9229 |

### `wrangler deploy`

```bash
wrangler deploy [script] [--name <worker-name>] [--dry-run] [--minify] [--no-bundle]
```

### `wrangler tail`

```bash
wrangler tail [worker-name] [flags]
```

| Flag | Purpose |
|------|---------|
| `--format json\|pretty` | Output format |
| `--status ok\|error\|canceled` | Filter by status |
| `--method GET\|POST\|...` | Filter by HTTP method |
| `--search <string>` | Filter by message content |
| `--ip <address>` | Filter by client IP |

### `wrangler delete`

```bash
wrangler delete [--name <worker-name>] [--dry-run]
```

Defaults to the worker name in `wrangler.toml`.

## KV Commands

### Namespace

```bash
wrangler kv namespace create <name>
wrangler kv namespace list
wrangler kv namespace delete --namespace-id <id>
```

Note: Preview namespaces are configured via `preview_id` in `wrangler.toml`, not via CLI flags.

### Key Operations

```bash
wrangler kv key put --namespace-id <id> <key> [value] [flags]
wrangler kv key get --namespace-id <id> <key> [--text]
wrangler kv key list --namespace-id <id> [--prefix <prefix>] [--limit <n>]
wrangler kv key delete --namespace-id <id> <key>
```

| Flag (put) | Purpose |
|------------|---------|
| `--path <file>` | Read value from file |
| `--expiration <unix>` | Expiration timestamp |
| `--expiration-ttl <seconds>` | TTL in seconds |
| `--metadata <json>` | JSON metadata |

### Bulk Operations

```bash
wrangler kv bulk put --namespace-id <id> <filename.json>
wrangler kv bulk delete --namespace-id <id> <filename.json>
```

## R2 Commands

### Bucket

```bash
wrangler r2 bucket create <name> [--jurisdiction <jur>]
wrangler r2 bucket list
wrangler r2 bucket delete <name>
```

### Object

```bash
wrangler r2 object put <bucket>/<key> --file <path> [--content-type <type>]
wrangler r2 object get <bucket>/<key> [--file <path>]
wrangler r2 object delete <bucket>/<key>
```

## D1 Commands

```bash
wrangler d1 create <name> [--location <hint>]
wrangler d1 list
wrangler d1 info <name>
wrangler d1 delete <name>
wrangler d1 execute <name> --command "<sql>" [--remote]
wrangler d1 execute <name> --file <path> [--remote]
wrangler d1 export <name> --output <path> [--remote]
wrangler d1 time-travel restore <name> --timestamp <ts>
wrangler d1 migrations list <name>
wrangler d1 migrations apply <name> [--remote]
```

**Important:** D1 commands default to local dev database. Add `--remote` to target production.

## Queues Commands

```bash
wrangler queues create <name>
wrangler queues list
wrangler queues delete <name>
wrangler queues consumer add <queue-name> <script-name>
wrangler queues consumer remove <queue-name> <script-name>
```

## Vectorize Commands

```bash
wrangler vectorize create <name> --dimensions <n> --metric <cosine|euclidean|dot-product>
wrangler vectorize list
wrangler vectorize delete <name>
wrangler vectorize insert <name> --file <ndjson-path>
wrangler vectorize get <name>
```

## Secrets

```bash
wrangler secret put <name> [--name <worker>]
wrangler secret list [--name <worker>]
wrangler secret delete <name> [--name <worker>]
wrangler secret bulk <filename.json> [--name <worker>]
```

## Other Commands

| Command | Purpose |
|---------|---------|
| `wrangler types` | Generate TypeScript types from wrangler.toml bindings |
| `wrangler docs [command]` | Open Cloudflare docs in browser |
| `wrangler deployments list` | List Worker deployments |
| `wrangler rollback [version-id]` | Rollback to previous Worker version |
| `wrangler ai` | Workers AI model catalog and inference |
| `wrangler hyperdrive create <name>` | Create Hyperdrive connection pool |
| `wrangler workflows list` | List Workflows (durable execution) |
