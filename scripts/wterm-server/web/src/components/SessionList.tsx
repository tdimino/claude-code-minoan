import { useState, useEffect, useCallback } from "react";
import { listSessions, createSession, killSession, type SessionInfo } from "../lib/api.js";

interface SessionListProps {
  activeId: string | null;
  onSelect: (id: string) => void;
}

export function SessionList({ activeId, onSelect }: SessionListProps) {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setSessions(await listSessions());
      setError(null);
    } catch (err) {
      console.error("[wterm] Failed to refresh sessions:", err);
      setError(err instanceof Error ? err.message : "Connection lost");
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleCreate = async (command?: string) => {
    try {
      const session = await createSession(command ? { command } : {});
      await refresh();
      onSelect(session.id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "unknown error";
      setError(`Failed to create session: ${msg}`);
    }
  };

  const handleKill = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await killSession(id);
      await refresh();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "unknown error";
      setError(`Failed to kill session: ${msg}`);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", padding: "12px" }}>
      <div style={{ marginBottom: "12px", display: "flex", gap: "8px" }}>
        <button onClick={() => handleCreate()} style={btnStyle}>
          + Shell
        </button>
        <button onClick={() => handleCreate("claude")} style={btnStyle}>
          + Claude
        </button>
      </div>

      {error && (
        <div style={{
          padding: "6px 10px",
          marginBottom: "8px",
          background: "#2d1b2e",
          border: "1px solid #f7768e",
          borderRadius: "6px",
          color: "#f7768e",
          fontSize: "11px",
        }}>
          {error}
        </div>
      )}

      <div style={{ flex: 1, overflow: "auto" }}>
        {sessions.map((s) => (
          <div
            key={s.id}
            onClick={() => onSelect(s.id)}
            style={{
              padding: "8px 10px",
              marginBottom: "4px",
              borderRadius: "6px",
              cursor: "pointer",
              background: s.id === activeId ? "#24283b" : "transparent",
              border: s.id === activeId ? "1px solid #414868" : "1px solid transparent",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "13px", fontWeight: 500 }}>{s.name}</span>
              <button
                onClick={(e) => handleKill(e, s.id)}
                style={{ background: "none", border: "none", color: "#f7768e", cursor: "pointer", fontSize: "12px" }}
              >
                kill
              </button>
            </div>
            <div style={{ fontSize: "11px", color: "#565f89", marginTop: "2px" }}>
              {s.command} &middot; pid {s.pid}
            </div>
          </div>
        ))}
        {sessions.length === 0 && !error && (
          <div style={{ color: "#565f89", fontSize: "13px", textAlign: "center", marginTop: "20px" }}>
            No active sessions
          </div>
        )}
      </div>
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  flex: 1,
  padding: "6px 10px",
  background: "#24283b",
  border: "1px solid #414868",
  borderRadius: "6px",
  color: "#c0caf5",
  cursor: "pointer",
  fontSize: "13px",
};
