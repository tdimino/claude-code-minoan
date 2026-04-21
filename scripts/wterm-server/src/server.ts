import { createServer, IncomingMessage, ServerResponse } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { join, extname, resolve } from "node:path";
import { WebSocketServer, WebSocket } from "ws";
import { verifyAuth, rejectUnauthorized, warnIfInsecure } from "./auth.js";
import {
  createSession,
  listSessions,
  killSession,
  resizeSession,
  attachClient,
  writeToSession,
} from "./session-manager.js";
import { decodeClientMessage, encodeControl } from "./protocol.js";
import type { CreateSessionRequest, ResizeRequest } from "./protocol.js";

const PORT = parseInt(process.env.WTERM_PORT ?? "3036", 10);
const HOST = process.env.WTERM_HOST ?? "0.0.0.0";
const WEB_DIR = resolve(join(import.meta.dirname, "..", "web", "dist"));
const MAX_BODY = 64 * 1024;

const ALLOWED_ORIGINS = new Set([
  "https://wterm.localhost",
  `http://localhost:${PORT}`,
  `http://127.0.0.1:${PORT}`,
]);

const MIME_TYPES: Record<string, string> = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".wasm": "application/wasm",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
};

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > MAX_BODY) {
        req.destroy();
        reject(new Error("body too large"));
      }
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function parseJson<T>(raw: string): { ok: true; value: T } | { ok: false } {
  try {
    return { ok: true, value: JSON.parse(raw) as T };
  } catch {
    return { ok: false };
  }
}

function json(res: ServerResponse, data: unknown, status = 200): void {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(data));
}

function corsOrigin(req: IncomingMessage): string {
  const origin = req.headers.origin ?? "";
  if (ALLOWED_ORIGINS.has(origin)) return origin;
  if (origin.match(/^https?:\/\/mac-mini-ts(:\d+)?$/)) return origin;
  return "";
}

function serveStatic(res: ServerResponse, urlPath: string): void {
  let filePath = join(WEB_DIR, urlPath === "/" ? "index.html" : urlPath);

  const resolved = resolve(filePath);
  if (!resolved.startsWith(WEB_DIR)) {
    res.writeHead(403);
    res.end("forbidden");
    return;
  }

  if (!existsSync(resolved)) {
    if (!extname(urlPath)) {
      filePath = join(WEB_DIR, "index.html");
    } else {
      res.writeHead(404);
      res.end("not found");
      return;
    }
  }
  if (!existsSync(filePath)) {
    res.writeHead(404);
    res.end("not found");
    return;
  }
  const mime = MIME_TYPES[extname(filePath)] ?? "application/octet-stream";
  res.writeHead(200, { "Content-Type": mime });
  try {
    res.end(readFileSync(filePath));
  } catch {
    res.writeHead(500);
    res.end("read error");
  }
}

async function handleApi(
  req: IncomingMessage,
  res: ServerResponse,
  path: string
): Promise<void> {
  if (path === "/api/health" && req.method === "GET") {
    json(res, { status: "ok", sessions: listSessions().length });
    return;
  }

  if (path === "/api/sessions" && req.method === "GET") {
    json(res, listSessions());
    return;
  }

  if (path === "/api/sessions" && req.method === "POST") {
    let body: CreateSessionRequest;
    try {
      const raw = await readBody(req);
      const parsed = parseJson<CreateSessionRequest>(raw);
      if (!parsed.ok) {
        json(res, { error: "invalid JSON" }, 400);
        return;
      }
      body = parsed.value;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "bad request";
      json(res, { error: message }, 400);
      return;
    }
    try {
      const session = createSession(body);
      json(res, session, 201);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "spawn failed";
      json(res, { error: message }, 500);
    }
    return;
  }

  const sessionMatch = path.match(/^\/api\/sessions\/([a-f0-9]+)$/);
  if (sessionMatch && req.method === "DELETE") {
    const ok = killSession(sessionMatch[1]);
    if (!ok) {
      json(res, { error: "session not found" }, 404);
      return;
    }
    json(res, { ok: true });
    return;
  }

  const resizeMatch = path.match(/^\/api\/sessions\/([a-f0-9]+)\/resize$/);
  if (resizeMatch && req.method === "POST") {
    let body: ResizeRequest;
    try {
      const raw = await readBody(req);
      const parsed = parseJson<ResizeRequest>(raw);
      if (!parsed.ok) {
        json(res, { error: "invalid JSON" }, 400);
        return;
      }
      body = parsed.value;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "bad request";
      json(res, { error: message }, 400);
      return;
    }
    if (
      !Number.isFinite(body.cols) ||
      !Number.isFinite(body.rows) ||
      body.cols < 1 ||
      body.rows < 1 ||
      body.cols > 500 ||
      body.rows > 200
    ) {
      json(res, { error: "invalid dimensions" }, 400);
      return;
    }
    const ok = resizeSession(resizeMatch[1], body.cols, body.rows);
    if (!ok) {
      json(res, { error: "session not found" }, 404);
      return;
    }
    json(res, { ok: true });
    return;
  }

  json(res, { error: "not found" }, 404);
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url ?? "/", `http://${req.headers.host}`);
    const path = url.pathname;

    const origin = corsOrigin(req);
    if (origin) {
      res.setHeader("Access-Control-Allow-Origin", origin);
      res.setHeader("Vary", "Origin");
    }
    res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS");

    if (req.method === "OPTIONS") {
      res.writeHead(204);
      res.end();
      return;
    }

    if (path.startsWith("/api/")) {
      if (!verifyAuth(req)) {
        rejectUnauthorized(res);
        return;
      }
      await handleApi(req, res, path);
      return;
    }

    serveStatic(res, path);
  } catch (err) {
    console.error("[wterm] Unhandled error in request handler:", err);
    if (!res.headersSent) {
      json(res, { error: "internal server error" }, 500);
    }
  }
});

const wss = new WebSocketServer({ noServer: true });

server.on("upgrade", (req, socket, head) => {
  if (!verifyAuth(req)) {
    socket.write("HTTP/1.1 401 Unauthorized\r\n\r\n");
    socket.destroy();
    return;
  }

  const url = new URL(req.url ?? "/", `http://${req.headers.host}`);
  const wsMatch = url.pathname.match(/^\/ws\/([a-f0-9]+)$/);
  if (!wsMatch) {
    socket.write("HTTP/1.1 404 Not Found\r\n\r\n");
    socket.destroy();
    return;
  }

  const sessionId = wsMatch[1];

  wss.handleUpgrade(req, socket, head, (ws) => {
    const attached = attachClient(sessionId, ws);
    if (!attached) {
      ws.send(encodeControl({ type: "error", message: "session not found" }));
      ws.close();
      return;
    }

    ws.on("message", (raw) => {
      try {
        const msg = raw.toString();
        const parsed = decodeClientMessage(msg);

        if (parsed.kind === "input") {
          writeToSession(sessionId, parsed.data);
        } else if (parsed.kind === "control" && parsed.msg.type === "resize") {
          resizeSession(sessionId, parsed.msg.cols, parsed.msg.rows);
        }
      } catch (err) {
        console.error("[wterm] Error handling WebSocket message:", err);
      }
    });
  });
});

warnIfInsecure(HOST);

server.listen(PORT, HOST, () => {
  console.log(`wterm-server listening on ${HOST}:${PORT}`);
});
