import { IncomingMessage, ServerResponse } from "node:http";
import { readFileSync } from "node:fs";
import { join } from "node:path";

let cachedToken: string | null | undefined = undefined;

function loadToken(): string | null {
  if (cachedToken !== undefined) return cachedToken;

  cachedToken = process.env.WTERM_AUTH_TOKEN ?? null;
  if (cachedToken) return cachedToken;

  try {
    const envPath = join(
      process.env.HOME ?? "",
      ".config",
      "env",
      "secrets.env"
    );
    const contents = readFileSync(envPath, "utf-8");
    for (const line of contents.split("\n")) {
      const match = line.match(/^WTERM_AUTH_TOKEN=(.+)$/);
      if (match) {
        cachedToken = match[1].trim().replace(/^["']|["']$/g, "");
        return cachedToken;
      }
    }
  } catch (err: unknown) {
    const code = (err as NodeJS.ErrnoException).code;
    if (code !== "ENOENT") {
      console.error(
        `[wterm-auth] Failed to load token from secrets.env: ${err}`
      );
      console.error(
        "[wterm-auth] Auth is DISABLED due to config error — fix secrets.env or set WTERM_AUTH_TOKEN"
      );
    }
  }

  cachedToken = null;
  return null;
}

function extractBearer(req: IncomingMessage): string | null {
  const auth = req.headers.authorization;
  if (auth?.startsWith("Bearer ")) return auth.slice(7);

  const url = new URL(req.url ?? "/", `http://${req.headers.host}`);
  const queryToken = url.searchParams.get("token");
  if (queryToken) return queryToken;

  return null;
}

export function verifyAuth(req: IncomingMessage): boolean {
  const token = loadToken();
  if (!token) return false;
  return extractBearer(req) === token;
}

export function rejectUnauthorized(res: ServerResponse): void {
  res.writeHead(401, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "unauthorized" }));
}

export function warnIfInsecure(host: string): void {
  const token = loadToken();
  if (!token && host !== "127.0.0.1" && host !== "localhost") {
    console.warn(
      "[wterm-auth] WARNING: No auth token configured. Server will reject all requests."
    );
    console.warn(
      "[wterm-auth] Set WTERM_AUTH_TOKEN in env or ~/.config/env/secrets.env"
    );
  }
}
