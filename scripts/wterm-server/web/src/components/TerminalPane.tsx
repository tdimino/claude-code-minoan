import { useRef, useEffect } from "react";
import { Terminal, type TerminalHandle } from "@wterm/react";
import "@wterm/react/css";
import { useSession } from "../hooks/useSession.js";

interface TerminalPaneProps {
  sessionId: string | null;
  onDisconnect?: () => void;
}

export function TerminalPane({ sessionId, onDisconnect }: TerminalPaneProps) {
  const termRef = useRef<TerminalHandle>(null);
  const hasConnectedRef = useRef(false);
  const { connect, disconnect, send, sendResize, onData, connected, sessionEnded } = useSession();

  useEffect(() => {
    if (!sessionId) return;
    hasConnectedRef.current = false;
    connect(sessionId);
    return () => {
      hasConnectedRef.current = false;
      disconnect();
    };
  }, [sessionId, connect, disconnect]);

  useEffect(() => {
    if (connected) {
      hasConnectedRef.current = true;
    } else if (hasConnectedRef.current && sessionId && onDisconnect) {
      onDisconnect();
    }
  }, [connected, sessionId, onDisconnect]);

  useEffect(() => {
    onData((data) => {
      termRef.current?.write(data);
    });
  }, [onData]);

  if (!sessionId) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#565f89" }}>
        Select or create a session
      </div>
    );
  }

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Terminal
        ref={termRef}
        onData={send}
        onResize={(cols, rows) => sendResize(cols, rows)}
        autoResize
        cursorBlink
        style={{ width: "100%", height: "100%" }}
      />
      {sessionEnded !== null && (
        <div style={{
          position: "absolute",
          bottom: "12px",
          left: "50%",
          transform: "translateX(-50%)",
          padding: "6px 16px",
          background: "#1a1b26ee",
          border: "1px solid #414868",
          borderRadius: "6px",
          color: sessionEnded === 0 ? "#9ece6a" : "#f7768e",
          fontSize: "12px",
          pointerEvents: "none",
        }}>
          Session ended (exit code {sessionEnded})
        </div>
      )}
    </div>
  );
}
