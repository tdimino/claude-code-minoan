export interface SessionInfo {
  id: string;
  name: string;
  pid: number;
  command: string;
  cwd: string;
  created: string;
  lastActivity: string;
  cols: number;
  rows: number;
  clientCount: number;
}

export interface CreateSessionRequest {
  command?: string;
  args?: string[];
  name?: string;
  cwd?: string;
  cols?: number;
  rows?: number;
}

export interface ResizeRequest {
  cols: number;
  rows: number;
}

export const CONTROL_PREFIX = "\x00";

export type ServerControlMessage =
  | { type: "session_ended"; code: number }
  | { type: "replay_start"; lines: number }
  | { type: "replay_end" }
  | { type: "error"; message: string };

export type ClientControlMessage =
  | { type: "resize"; cols: number; rows: number }
  | { type: "detach" };

export function encodeControl(msg: ServerControlMessage): string {
  return CONTROL_PREFIX + JSON.stringify(msg);
}

export type DecodedMessage =
  | { kind: "input"; data: string }
  | { kind: "control"; msg: ClientControlMessage }
  | { kind: "error"; reason: string };

export function decodeClientMessage(data: string): DecodedMessage {
  if (data.startsWith(CONTROL_PREFIX)) {
    try {
      return { kind: "control", msg: JSON.parse(data.slice(1)) };
    } catch {
      return { kind: "error", reason: "malformed control message" };
    }
  }
  return { kind: "input", data };
}
