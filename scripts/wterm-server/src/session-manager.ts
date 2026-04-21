import * as pty from "node-pty";
import { randomBytes } from "node:crypto";
import { WebSocket } from "ws";
import type { CreateSessionRequest, SessionInfo } from "./protocol.js";
import { encodeControl } from "./protocol.js";

const SCROLLBACK_LIMIT = 10_000;
const MAX_SESSIONS = 20;

const SAFE_ENV_PREFIXES = [
  "HOME", "USER", "SHELL", "TERM", "LANG", "LC_", "PATH",
  "EDITOR", "VISUAL", "COLORTERM", "TMPDIR", "XDG_",
];
const BLOCKED_ENV_KEYS = new Set(["WTERM_AUTH_TOKEN"]);

interface Session {
  id: string;
  name: string;
  pid: number;
  pty: pty.IPty;
  command: string;
  cwd: string;
  created: Date;
  lastActivity: Date;
  cols: number;
  rows: number;
  scrollback: string[];
  clients: Set<WebSocket>;
}

const sessions = new Map<string, Session>();

function generateId(): string {
  return randomBytes(16).toString("hex");
}

function buildSafeEnv(): Record<string, string> {
  const env: Record<string, string> = {};
  for (const [k, v] of Object.entries(process.env)) {
    if (v === undefined) continue;
    if (BLOCKED_ENV_KEYS.has(k)) continue;
    if (SAFE_ENV_PREFIXES.some((p) => k === p || k.startsWith(p))) {
      env[k] = v;
    }
  }
  return env;
}

function safeSend(ws: WebSocket, data: string | Buffer): boolean {
  if (ws.readyState !== WebSocket.OPEN) return false;
  try {
    ws.send(data);
    return true;
  } catch {
    return false;
  }
}

export function createSession(req: CreateSessionRequest): SessionInfo {
  if (sessions.size >= MAX_SESSIONS) {
    throw new Error(`session limit reached (max ${MAX_SESSIONS})`);
  }

  const id = generateId();
  const command = req.command ?? "/bin/zsh";
  const args = req.args ?? [];
  const cwd = req.cwd ?? process.env.HOME ?? "/";
  const cols = req.cols ?? 120;
  const rows = req.rows ?? 40;
  const name = req.name ?? `${command.split("/").pop()}-${id.slice(0, 4)}`;

  const env = buildSafeEnv();

  const term = pty.spawn(command, args, {
    name: "xterm-256color",
    cols,
    rows,
    cwd,
    env,
  });

  const session: Session = {
    id,
    name,
    pid: term.pid,
    pty: term,
    command,
    cwd,
    created: new Date(),
    lastActivity: new Date(),
    cols,
    rows,
    scrollback: [],
    clients: new Set(),
  };

  term.onData((data) => {
    session.lastActivity = new Date();
    appendScrollback(session, data);
    for (const client of session.clients) {
      if (!safeSend(client, data)) {
        session.clients.delete(client);
      }
    }
  });

  term.onExit(({ exitCode }) => {
    const msg = encodeControl({ type: "session_ended", code: exitCode });
    for (const client of session.clients) {
      safeSend(client, msg);
      try { client.close(); } catch {}
    }
    session.clients.clear();
    sessions.delete(id);
  });

  sessions.set(id, session);
  return toSessionInfo(session);
}

export function listSessions(): SessionInfo[] {
  return Array.from(sessions.values()).map(toSessionInfo);
}

export function getSession(id: string): Session | undefined {
  return sessions.get(id);
}

export function killSession(id: string): boolean {
  const session = sessions.get(id);
  if (!session) return false;
  try {
    session.pty.kill();
  } catch (err) {
    console.warn(`[wterm] Error killing PTY for session ${id}:`, err);
  }
  return true;
}

export function resizeSession(id: string, cols: number, rows: number): boolean {
  const session = sessions.get(id);
  if (!session) return false;
  if (
    !Number.isFinite(cols) ||
    !Number.isFinite(rows) ||
    cols < 1 ||
    rows < 1 ||
    cols > 500 ||
    rows > 200
  ) {
    console.warn(`[wterm] Invalid resize dimensions: ${cols}x${rows}`);
    return false;
  }
  try {
    session.pty.resize(cols, rows);
  } catch (err) {
    console.error(`[wterm] Failed to resize session ${id}:`, err);
    return false;
  }
  session.cols = cols;
  session.rows = rows;
  return true;
}

export function attachClient(id: string, ws: WebSocket): boolean {
  const session = sessions.get(id);
  if (!session) return false;

  session.clients.add(ws);

  if (session.scrollback.length > 0) {
    safeSend(ws, encodeControl({ type: "replay_start", lines: session.scrollback.length }));
    for (const line of session.scrollback) {
      if (!safeSend(ws, line)) break;
    }
    safeSend(ws, encodeControl({ type: "replay_end" }));
  }

  ws.on("close", () => {
    session.clients.delete(ws);
  });

  return true;
}

export function writeToSession(id: string, data: string): boolean {
  const session = sessions.get(id);
  if (!session) return false;
  try {
    session.pty.write(data);
  } catch (err) {
    console.error(`[wterm] Failed to write to session ${id}:`, err);
    return false;
  }
  return true;
}

function appendScrollback(session: Session, data: string): void {
  session.scrollback.push(data);
  if (session.scrollback.length > SCROLLBACK_LIMIT) {
    session.scrollback.splice(0, session.scrollback.length - SCROLLBACK_LIMIT);
  }
}

function toSessionInfo(session: Session): SessionInfo {
  return {
    id: session.id,
    name: session.name,
    pid: session.pid,
    command: session.command,
    cwd: session.cwd,
    created: session.created.toISOString(),
    lastActivity: session.lastActivity.toISOString(),
    cols: session.cols,
    rows: session.rows,
    clientCount: session.clients.size,
  };
}
