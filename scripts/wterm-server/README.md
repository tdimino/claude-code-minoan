# wterm-server

Web terminal daemon — browser-based shell access via [wterm](https://github.com/vercel-labs/wterm) (Zig/WASM terminal emulator) + node-pty. Deploy on any macOS machine; access locally or remotely from any device on your tailnet.

## Daimones vs Daemons

In the [Claudicle](https://github.com/tdimino/claudicle) ecosystem, a *daimon* (plural *daimones*) is a persistent daemon with a web UI that lives at `~/daimones/<name>/`. Daimones are standalone Node.js or Python services — heavier than the lightweight Python scripts in `scripts/` (cpu-watchdog, syspeek, screenshot-rename), which are simple launchd-managed utilities. The distinction: daimones have their own `package.json`, build steps, and browser frontends; daemons are single-file scripts with a plist.

wterm-server is a daimon. Its source lives here in the repo; it deploys to `~/daimones/wterm-server/` on whichever machine you choose.

## Architecture

```
Browser (any device)
  ↓ HTTP / WebSocket
wterm-server (Node.js)
  ├── HTTP: React SPA + REST API (session CRUD)
  ├── WebSocket: /ws/:sessionId — bidirectional terminal I/O
  └── node-pty: spawns zsh / claude / arbitrary shells
```

- **Server**: TypeScript — `node-pty`, `ws`, raw `http` module
- **Frontend**: React 19 + `@wterm/react` (WASM terminal) + Vite
- **Auth**: Bearer token via `WTERM_AUTH_TOKEN` (fail-closed — rejects all if unconfigured)
- **Session persistence**: 10,000-line scrollback ring buffer; reconnecting replays missed output

## Deployment

Deploy on any macOS machine — your primary laptop, a headless Mac Mini, a build server. The install script auto-detects `$HOME` and `node` path.

### Local (same machine)

```bash
# 1. Copy daemon source
mkdir -p ~/daimones
cp -r scripts/wterm-server/ ~/daimones/wterm-server/

# 2. Install dependencies and build frontend
cd ~/daimones/wterm-server && npm install
cd web && npm install && npx vite build

# 3. Generate auth token
mkdir -p ~/.config/env
echo "WTERM_AUTH_TOKEN=$(openssl rand -hex 32)" >> ~/.config/env/secrets.env

# 4. Install LaunchAgent (auto-detects $HOME and node path)
bash ~/.claude/skills/wterm/launchd/install.sh install

# 5. Verify
bash ~/.claude/skills/wterm/scripts/status.sh
```

Access: `http://localhost:3036` or `https://wterm.localhost` (via portless).

### Remote (e.g. Mac Mini via SSH)

```bash
# 1. Copy to remote machine
scp -r scripts/wterm-server/ <host>:~/daimones/wterm-server/

# 2. Install on remote
ssh <host> 'cd ~/daimones/wterm-server && npm install && cd web && npm install && npx vite build'

# 3. Generate token on remote
ssh <host> 'mkdir -p ~/.config/env && echo "WTERM_AUTH_TOKEN=$(openssl rand -hex 32)" >> ~/.config/env/secrets.env'

# 4. Install LaunchAgent on remote
ssh <host> 'bash ~/.claude/skills/wterm/launchd/install.sh install'
```

Access from any tailnet device: `http://<hostname>:3036`

## File Layout

```
src/
  server.ts              # HTTP + WebSocket entry point
  session-manager.ts     # PTY lifecycle, scrollback, client broadcast
  auth.ts                # Bearer token verification (env + secrets.env)
  protocol.ts            # Wire format (NUL-prefix control messages)
web/
  src/
    App.tsx              # Sidebar + terminal layout
    components/
      SessionList.tsx    # Session list with polling, create/kill
      TerminalPane.tsx   # @wterm/react terminal with WS connection
    hooks/
      useSession.ts      # WebSocket lifecycle hook
    lib/
      api.ts             # HTTP client + shared types from server
```

## REST API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Liveness + session count |
| `/api/sessions` | GET | List active sessions |
| `/api/sessions` | POST | Create session (`{command, args, name, cwd, cols, rows}`) |
| `/api/sessions/:id` | DELETE | Kill session |
| `/api/sessions/:id/resize` | POST | Resize PTY (`{cols, rows}`) |

All endpoints require `Authorization: Bearer <token>` header.

## Security

- Auth is **fail-closed** — no token configured means all requests rejected
- Spawned shells get a **curated environment** (sensitive vars like `WTERM_AUTH_TOKEN` stripped)
- **Path traversal protection** on static file serving
- **64KB body size limit** on all POST endpoints
- **CORS restricted** to known origins (wterm.localhost, localhost)
- **20 concurrent session limit** with 128-bit session IDs
- Input validation on resize dimensions (1–500 cols, 1–200 rows)
- All `JSON.parse` calls wrapped in try/catch — malformed input returns 400, never crashes

## LaunchAgent

`com.minoan.wterm-server` — RunAtLoad, KeepAlive, port 3036.

The plist is a template with `__HOME__` and `__NODE__` placeholders. The install script substitutes these at install time using `sed`, so the same template works on any machine regardless of username or node location.

Logs: `~/.claude/logs/wterm-server.{out,err}.log`

## Companion Skill

The `wterm` skill (`skills/integration-automation/wterm/`) provides Claude-facing management:

```
/wterm status    — daemon health + session count
/wterm list      — active sessions table
/wterm create    — spawn a new shell or Claude session
/wterm kill <id> — terminate a session
/wterm restart   — restart the daemon
```
