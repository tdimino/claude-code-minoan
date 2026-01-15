import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { randomUUID } from 'crypto';

/**
 * Shared state file format for cross-window terminal tracking
 */
interface WindowState {
  windowId: string;
  pid: number;
  lastUpdate: number;
  terminals: {
    name: string;
    workspacePath: string;
  }[];
}

interface CrossWindowState {
  windows: Record<string, WindowState>;
}

const STATE_FILE = path.join(os.homedir(), '.claude', 'vscode-tracker-state.json');
const STALE_WINDOW_MS = 30000; // 30 seconds - consider window dead if no update

/**
 * Manages cross-window terminal state via shared file
 * Uses atomic writes to prevent race conditions between windows
 */
export class CrossWindowStateManager {
  private windowId: string;
  private fileWatcher: fs.FSWatcher | null = null;
  private updateCallback: ((totalCount: number) => void) | null = null;
  private currentTerminals: { name: string; workspacePath: string }[] = [];
  private debounceTimer: ReturnType<typeof setTimeout> | undefined;
  private heartbeatInterval: ReturnType<typeof setInterval> | undefined;

  constructor() {
    // Generate unique window ID using process ID and timestamp
    this.windowId = `${process.pid}-${Date.now()}`;
  }

  /**
   * Start tracking and watching for changes
   */
  activate(onUpdate: (totalCount: number) => void): void {
    this.updateCallback = onUpdate;

    // Ensure .claude directory exists
    const claudeDir = path.dirname(STATE_FILE);
    if (!fs.existsSync(claudeDir)) {
      fs.mkdirSync(claudeDir, { recursive: true });
    }

    // Watch for file changes from other windows
    this.startWatching();

    // Clean up stale windows and broadcast initial state
    this.updateState();
  }

  /**
   * Stop watching and clean up our window's state
   */
  deactivate(): void {
    // Clean up heartbeat interval
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = undefined;
    }

    // Clean up file watcher
    this.disposeWatcher();

    // Remove our window from state
    try {
      const state = this.readState();
      delete state.windows[this.windowId];
      this.writeStateAtomic(state);
    } catch {
      // Ignore errors during cleanup
    }
  }

  /**
   * Clean up file watcher and debounce timer
   */
  private disposeWatcher(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = undefined;
    }
    if (this.fileWatcher) {
      this.fileWatcher.close();
      this.fileWatcher = null;
    }
  }

  /**
   * Update our window's terminal list
   */
  updateTerminals(terminals: { name: string; workspacePath: string }[]): void {
    this.currentTerminals = terminals;
    this.updateState();
  }

  /**
   * Get total terminal count across all windows
   */
  getTotalCount(): number {
    const state = this.readState();
    const now = Date.now();
    let total = 0;

    for (const [windowId, windowState] of Object.entries(state.windows)) {
      // Skip stale windows (hasn't updated in 30 seconds)
      if (now - windowState.lastUpdate > STALE_WINDOW_MS) {
        continue;
      }
      total += windowState.terminals.length;
    }

    return total;
  }

  /**
   * Get all terminals across all windows
   */
  getAllTerminals(): { name: string; workspacePath: string; windowId: string }[] {
    const state = this.readState();
    const now = Date.now();
    const terminals: { name: string; workspacePath: string; windowId: string }[] = [];

    for (const [windowId, windowState] of Object.entries(state.windows)) {
      if (now - windowState.lastUpdate > STALE_WINDOW_MS) {
        continue;
      }
      for (const terminal of windowState.terminals) {
        terminals.push({ ...terminal, windowId });
      }
    }

    return terminals;
  }

  /**
   * Get terminals from stale (crashed) windows that can be recovered
   * These are sessions that were active before VS Code crashed
   */
  getRecoverableSessions(): { name: string; workspacePath: string; windowId: string; lastUpdate: number }[] {
    const state = this.readState();
    const now = Date.now();
    const recoverable: { name: string; workspacePath: string; windowId: string; lastUpdate: number }[] = [];

    for (const [windowId, windowState] of Object.entries(state.windows)) {
      // Only include stale windows (crashed/closed without cleanup)
      if (now - windowState.lastUpdate > STALE_WINDOW_MS) {
        for (const terminal of windowState.terminals) {
          recoverable.push({
            ...terminal,
            windowId,
            lastUpdate: windowState.lastUpdate,
          });
        }
      }
    }

    return recoverable;
  }

  /**
   * Clear stale sessions after they've been recovered or dismissed
   */
  clearStaleSessions(): void {
    try {
      const state = this.readState();
      const now = Date.now();

      // Remove only stale windows
      for (const [windowId, windowState] of Object.entries(state.windows)) {
        if (now - windowState.lastUpdate > STALE_WINDOW_MS) {
          delete state.windows[windowId];
        }
      }

      this.writeStateAtomic(state);
    } catch (err) {
      console.warn('Failed to clear stale sessions:', err);
    }
  }

  /**
   * Check if there are recoverable sessions from a crash
   */
  hasRecoverableSessions(): boolean {
    return this.getRecoverableSessions().length > 0;
  }

  private startWatching(): void {
    // Clean up any existing watcher
    this.disposeWatcher();

    try {
      // Create file if it doesn't exist
      if (!fs.existsSync(STATE_FILE)) {
        this.writeStateAtomic({ windows: {} });
      }

      this.fileWatcher = fs.watch(STATE_FILE, (eventType) => {
        if (eventType === 'change') {
          // Debounce to prevent cascade updates
          if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
          }
          this.debounceTimer = setTimeout(() => {
            const total = this.getTotalCount();
            this.updateCallback?.(total);
          }, 100);
        }
      });

      // Handle watcher errors (file deleted, permissions changed, etc.)
      this.fileWatcher.on('error', (err) => {
        console.warn('File watcher error:', err);
        this.disposeWatcher();
      });
    } catch (err) {
      console.warn('Failed to watch cross-window state file:', err);
    }
  }

  /**
   * Update state with retry logic to handle race conditions
   */
  private updateState(retries = 3): void {
    for (let i = 0; i < retries; i++) {
      try {
        const state = this.readState();
        const now = Date.now();

        // NOTE: We intentionally do NOT delete stale windows here
        // Stale windows represent crash-recoverable sessions
        // They are only cleared via clearStaleSessions() after user dismisses/recovers them

        // Update our window's state
        state.windows[this.windowId] = {
          windowId: this.windowId,
          pid: process.pid,
          lastUpdate: now,
          terminals: this.currentTerminals,
        };

        this.writeStateAtomic(state);

        // Notify callback of new total
        const total = this.getTotalCount();
        this.updateCallback?.(total);
        return; // Success
      } catch (err) {
        if (i === retries - 1) {
          console.warn('Failed to update cross-window state after retries:', err);
          return;
        }
        // Small jitter before retry (1-50ms)
        const jitter = Math.floor(Math.random() * 50) + 1;
        // Use sync sleep via busy wait (acceptable for short duration)
        const start = Date.now();
        while (Date.now() - start < jitter) {
          // Busy wait
        }
      }
    }
  }

  private readState(): CrossWindowState {
    try {
      if (fs.existsSync(STATE_FILE)) {
        const content = fs.readFileSync(STATE_FILE, 'utf8');
        return JSON.parse(content) as CrossWindowState;
      }
    } catch {
      // Ignore parse errors
    }
    return { windows: {} };
  }

  /**
   * Atomically write state using temp file + rename pattern
   * This prevents race conditions when multiple windows update simultaneously
   */
  private writeStateAtomic(state: CrossWindowState): void {
    const tempPath = `${STATE_FILE}.${randomUUID()}.tmp`;
    try {
      fs.writeFileSync(tempPath, JSON.stringify(state, null, 2), 'utf8');
      fs.renameSync(tempPath, STATE_FILE); // Atomic on POSIX
    } catch (err) {
      // Clean up temp file on error
      try {
        fs.unlinkSync(tempPath);
      } catch {
        // Ignore cleanup errors
      }
      throw err;
    }
  }

  /**
   * Send periodic heartbeat to keep our window marked as alive
   */
  startHeartbeat(): vscode.Disposable {
    // Clear any existing heartbeat
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.heartbeatInterval = setInterval(() => {
      this.updateState();
    }, 10000); // Every 10 seconds

    return {
      dispose: () => {
        if (this.heartbeatInterval) {
          clearInterval(this.heartbeatInterval);
          this.heartbeatInterval = undefined;
        }
      },
    };
  }
}
