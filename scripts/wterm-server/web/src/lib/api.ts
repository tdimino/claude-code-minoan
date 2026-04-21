import type { SessionInfo } from "@wterm/shared";
export type { SessionInfo };

function getToken(): string | null {
  const hash = window.location.hash;
  const match = hash.match(/token=([^&]+)/);
  if (match) {
    localStorage.setItem("wterm_token", match[1]);
    window.location.hash = "";
    return match[1];
  }
  return localStorage.getItem("wterm_token");
}

function headers(): HeadersInit {
  const token = getToken();
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

export function getWsUrl(sessionId: string): string {
  const token = getToken();
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const base = `${proto}//${window.location.host}/ws/${sessionId}`;
  return token ? `${base}?token=${token}` : base;
}

async function checkedFetch(url: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = (body as { error?: string }).error ?? `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return res;
}

export async function listSessions(): Promise<SessionInfo[]> {
  const res = await checkedFetch("/api/sessions", { headers: headers() });
  return res.json();
}

export async function createSession(opts: {
  command?: string;
  name?: string;
  cwd?: string;
}): Promise<SessionInfo> {
  const res = await checkedFetch("/api/sessions", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(opts),
  });
  return res.json();
}

export async function killSession(id: string): Promise<void> {
  await checkedFetch(`/api/sessions/${id}`, {
    method: "DELETE",
    headers: headers(),
  });
}
