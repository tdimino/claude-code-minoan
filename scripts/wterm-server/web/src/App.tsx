import { useState } from "react";
import { SessionList } from "./components/SessionList.js";
import { TerminalPane } from "./components/TerminalPane.js";

export function App() {
  const [activeSession, setActiveSession] = useState<string | null>(null);

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{
        width: "220px",
        borderRight: "1px solid #24283b",
        flexShrink: 0,
        overflow: "hidden",
      }}>
        <SessionList activeId={activeSession} onSelect={setActiveSession} />
      </div>
      <div style={{ flex: 1, overflow: "hidden" }}>
        <TerminalPane
          sessionId={activeSession}
          onDisconnect={() => setActiveSession(null)}
        />
      </div>
    </div>
  );
}
