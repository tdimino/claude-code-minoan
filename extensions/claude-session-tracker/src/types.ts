/**
 * Enriched Claude Code session — merges sessions-index.json + session-summaries.json
 */
export interface EnrichedSession {
  /** Full session UUID */
  id: string;
  /** Absolute path to the project directory */
  projectPath: string;
  /** Basename of projectPath */
  projectName: string;
  /** Best available title: customTitle > cached title > truncated firstPrompt */
  displayTitle: string;
  /** First user message text */
  firstPrompt: string;
  /** AI-generated or cached summary */
  summary?: string;
  /** Number of messages in session */
  messageCount?: number;
  /** Git branch at session time */
  gitBranch?: string;
  /** ISO timestamp — session creation */
  created: string;
  /** ISO timestamp — last modification */
  modified: string;
  /** Observer/background session (filtered from main list) */
  isSidechain: boolean;
  /** Short model name (e.g., "opus-4.6") */
  model?: string;
  /** Number of agent turns */
  numTurns?: number;
  /** Total session cost in USD */
  totalCostUsd?: number;
  /** Session is in a git worktree */
  isWorktree?: boolean;
}

/**
 * Tracked Claude Code session metadata (VS Code terminal tracking)
 */
export interface TrackedSession {
  /** Absolute path to the project directory */
  projectPath: string;
  /** Terminal name when session was active */
  terminalName: string;
  /** ISO timestamp when session started */
  startedAt: string;
  /** ISO timestamp when terminal was closed (if applicable) */
  closedAt?: string;
  /** Whether this session can be resumed */
  isResumable: boolean;
  /** Git branch at time of session (if available) */
  gitBranch?: string;
}

/**
 * Raw entry from sessions-index.json
 */
export interface SessionIndexEntry {
  sessionId: string;
  projectPath?: string;
  summary?: string;
  customTitle?: string;
  firstPrompt?: string;
  messageCount?: number;
  created?: string;
  modified?: string;
  gitBranch?: string;
  isSidechain?: boolean;
}

/**
 * Cached summary from session-summaries.json
 */
export interface SessionSummaryCache {
  title?: string;
  summary?: string;
  first_msg?: string;
  model?: string;
  num_turns?: number;
  total_cost_usd?: number;
  source?: string;
}
