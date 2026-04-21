import { useRef, useCallback, useEffect, useState } from "react";
import { getWsUrl } from "../lib/api.js";
import { CONTROL_PREFIX } from "@wterm/shared";

export interface UseSessionReturn {
  connect: (sessionId: string) => void;
  disconnect: () => void;
  send: (data: string) => void;
  sendResize: (cols: number, rows: number) => void;
  onData: (cb: (data: string) => void) => void;
  connected: boolean;
  replaying: boolean;
  sessionEnded: number | null;
}

export function useSession(): UseSessionReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const dataCallbackRef = useRef<((data: string) => void) | null>(null);
  const [connected, setConnected] = useState(false);
  const [replaying, setReplaying] = useState(false);
  const [sessionEnded, setSessionEnded] = useState<number | null>(null);

  const connect = useCallback((sessionId: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    setSessionEnded(null);
    const ws = new WebSocket(getWsUrl(sessionId));
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onerror = (event) => {
      console.error("[wterm] WebSocket error:", event);
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
    };

    ws.onmessage = (event) => {
      const data = event.data as string;
      if (data.startsWith(CONTROL_PREFIX)) {
        try {
          const msg = JSON.parse(data.slice(1));
          if (msg.type === "replay_start") setReplaying(true);
          else if (msg.type === "replay_end") setReplaying(false);
          else if (msg.type === "session_ended") {
            setSessionEnded(msg.code ?? -1);
            ws.close();
          }
        } catch (err) {
          console.error("[wterm] Malformed control message:", err);
        }
        return;
      }
      dataCallbackRef.current?.(data);
    };
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const send = useCallback((data: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(data);
  }, []);

  const sendResize = useCallback((cols: number, rows: number) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const msg = CONTROL_PREFIX + JSON.stringify({ type: "resize", cols, rows });
    wsRef.current.send(msg);
  }, []);

  const onData = useCallback((cb: (data: string) => void) => {
    dataCallbackRef.current = cb;
  }, []);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { connect, disconnect, send, sendResize, onData, connected, replaying, sessionEnded };
}
