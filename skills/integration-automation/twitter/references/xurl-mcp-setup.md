# xurl + Hosted X MCP Setup

X's official agent surface, launched June 30, 2026: a hosted MCP server at
`https://api.x.com/mcp` (Streamable HTTP), bridged locally by the official
`xurl` CLI (xdevplatform/xurl). No new pricing — every tool call bills the
standard pay-per-use rates (see pricing.md).

## Why it matters

Two capabilities nothing else in this skill provides:

- **Full-archive search** — reaches across all of X's history, not the 7-day
  recent window x-search is limited to. Previously required the $5,000/mo Pro tier.
  Caveat (verified 2026-07-15): `search_posts_all` requires **App-Only auth**;
  the xurl bridge sends the OAuth2 user token and gets a 403. Workaround: POST
  JSON-RPC directly to `https://api.x.com/mcp` with `Authorization: Bearer
  $X_BEARER_TOKEN` (initialize → notifications/initialized → tools/call). All
  user-context tools (bookmarks, mentions, timelines) work fine through the bridge.
- **Trends by WOEID** + news search.

Plus: bookmarks CRUD, timelines/mentions, Articles (long-form draft + publish).
Six tool groups covering most of the X API surface.

## Install

```bash
npm install -g @xdevplatform/xurl        # installed 2026-07-05, v1.2.2
# or: brew install --cask xdevplatform/tap/xurl
```

## Auth setup (one-time)

Requires OAuth 2.0 enabled on the X developer app (console.x.com →
User authentication settings): type "Web App", redirect URI
`http://localhost:8080/callback`, scopes with `offline.access`.
Client ID + Secret live in `~/.claude/skills/twitter/.env` as `CLIENT_ID` / `CLIENT_SECRET`.

```bash
xurl auth apps add main --client-id "$CLIENT_ID" --client-secret "$CLIENT_SECRET"
xurl auth oauth2          # opens browser once; tokens cache to ~/.xurl, auto-refresh
# headless machines: xurl auth oauth2 --headless
```

Security: never read `~/.xurl` into LLM context — it holds live access tokens
(xurl maintainers' own warning). Same rule as the skill `.env`.

## MCP wiring (Claude Code, user scope)

```bash
claude mcp add xapi --scope user -- xurl --app main mcp https://api.x.com/mcp
```

No env vars needed — credentials and tokens live in `~/.xurl` under the named
app (`--app main`; the bare `default` app has none). `xurl mcp` bridges
stdio ↔ Streamable HTTP, injecting and refreshing the Bearer token. Done on
this machine 2026-07-15.

Gotcha from the live setup: the callback URI must be registered on the X app's
User authentication settings (console.x.com → app → Settings → Authentication)
or X shows "Something went wrong" at the approval screen. Only the app owner
can edit this. Read-only alternative (no OAuth, no writes): point any MCP client at the
URL directly with `Authorization: Bearer $X_BEARER_TOKEN`.

## xurl as a curl-like CLI

Quick examples live in SKILL.md. Additional flags:

```bash
xurl --auth oauth1 /2/users/me        # force OAuth 1.0a instead of 2.0
```

Use xurl for media posts, DMs, and Articles — surfaces x-search doesn't wrap.
Remember the $0.20 URL-post surcharge applies regardless of client.

## Self-hosted alternative

`xdevplatform/xMCP` — FastMCP server wrapping 175 endpoints, runs locally on
:8000. Only needed to customize the tool surface or keep traffic inside your
own network boundary; the hosted server is otherwise strictly less maintenance.
