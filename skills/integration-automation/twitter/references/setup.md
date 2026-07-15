# Credential Setup & Troubleshooting (x-search / official API)

Once configured, none of this needs revisiting — this file exists for
re-setup after a machine migration or credential rotation.

## Bearer token (reads: search, profiles, threads, feed, usage)

Get one at [console.x.com](https://console.x.com). Pay-per-use, no monthly commitment.
x-search resolves it in this order:

```bash
# 1. Shell env
export X_BEARER_TOKEN=your_token_here
# 2. Global env file
mkdir -p ~/.config/env && echo 'X_BEARER_TOKEN=your_token_here' >> ~/.config/env/global.env
# 3. Skill-local .env
echo 'X_BEARER_TOKEN=your_token_here' >> ~/.claude/skills/twitter/.env
```

## OAuth 1.0a (x-search posting/replying/deleting)

Required in addition to the Bearer token:

1. [console.x.com](https://console.x.com) → your project → **Keys and tokens**
2. Under "Consumer Keys": copy **API Key** and **API Key Secret**
3. Under "Authentication Tokens": generate **Access Token** and **Access Token Secret** with **Read and Write** permissions
4. Add all four to `~/.claude/skills/twitter/.env`:

```bash
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
```

## OAuth 2.0 (xurl + hosted MCP)

Separate credential pair (`CLIENT_ID`/`CLIENT_SECRET`) — see `xurl-mcp-setup.md`.

## bird CLI

```bash
npm install -g @steipete/bird     # frozen at 0.8.0; upstream deleted Feb 2026
bird --cookie-source chrome whoami
```

## Smaug

```bash
cd ~/tools/smaug && npx smaug setup
```

## Troubleshooting

- **"X_BEARER_TOKEN not found"** — set via one of the three methods above; the error message lists the search order.
- **"OAuth 1.0a credentials missing: ..."** — the named keys are absent from env and both .env files; regenerate at console.x.com with Read and Write permissions.
- **401 on posting but reads work** — Access Token was generated before Read/Write was enabled; regenerate the token pair.
- **429 rate limit** — x-search prints the reset time; wait it out (the cache absorbs repeats).
