import * as vscode from 'vscode';
import { SessionStorage } from './sessionStorage';
import { StatusBarManager } from './statusBar';
import { CrossWindowStateManager } from './crossWindowState';
import {
  getCurrentWorkspacePath,
  getWorkspaceForPath,
  getProcessCwd,
  getProcessCommand,
  getChildProcesses,
  isClaudeProcess,
  getGitBranchRobust,
  sleep,
  TERMINAL_DETECTION_DELAY_MS,
  TERMINAL_DETECTION_MAX_ATTEMPTS,
} from './utils';

/** Git branch cache TTL in milliseconds */
const GIT_CACHE_TTL_MS = 60000;  // 1 minute

/**
 * Watches terminals for Claude Code sessions
 * Supports multi-root workspaces, process-based detection, and cross-window tracking
 */
export class TerminalWatcher {
  // Map: workspacePath → Set of terminals (Phase 3: multi-root support)
  private activeClaudeTerminals = new Map<string, Set<vscode.Terminal>>();

  // Git branch cache: path → { branch, timestamp }
  private gitBranchCache = new Map<string, { branch: string | undefined; timestamp: number }>();

  // Cross-window state manager
  private crossWindowState = new CrossWindowStateManager();

  constructor(
    private context: vscode.ExtensionContext,
    private storage: SessionStorage,
    private statusBar: StatusBarManager
  ) {}

  /**
   * Start watching terminals
   */
  activate(): void {
    // Initialize cross-window state tracking
    this.crossWindowState.activate((globalCount) => {
      // Called when another window updates its terminals
      this.updateStatusBar(globalCount);
    });

    // Start heartbeat to keep our window marked as alive
    this.context.subscriptions.push(
      this.crossWindowState.startHeartbeat()
    );

    // Clean up cross-window state on deactivation
    this.context.subscriptions.push({
      dispose: () => this.crossWindowState.deactivate(),
    });

    // Watch for new terminals
    this.context.subscriptions.push(
      vscode.window.onDidOpenTerminal(terminal => {
        this.onTerminalOpened(terminal);
      })
    );

    // Watch for closed terminals
    this.context.subscriptions.push(
      vscode.window.onDidCloseTerminal(terminal => {
        this.onTerminalClosed(terminal);
      })
    );

    // Check existing terminals on activation
    // Use Promise.all to properly handle async operations (not forEach)
    Promise.all(
      vscode.window.terminals.map(async terminal => {
        try {
          if (await this.isClaudeTerminal(terminal)) {
            await this.trackTerminal(terminal);
          }
        } catch (err) {
          console.error('Error checking existing terminal:', err);
        }
      })
    ).catch(err => {
      console.error('Error during terminal initialization:', err);
    });

    // Initialize status bar
    this.updateStatusBar();
  }

  /**
   * Check if a terminal is running Claude Code
   * Uses hybrid detection: fast name check + slow process inspection
   */
  private async isClaudeTerminal(terminal: vscode.Terminal): Promise<boolean> {
    // Fast path: name check
    const name = terminal.name.toLowerCase();
    if (
      name.includes('claude') ||
      name.includes('claude code') ||
      name === 'claude code (resumed)'
    ) {
      return true;
    }

    // Slow path: process inspection
    const pid = await terminal.processId;
    if (!pid) return false;

    // Check shell process command
    const command = getProcessCommand(pid);
    if (isClaudeProcess(command)) return true;

    // Check child processes (Claude may be child of shell)
    const children = getChildProcesses(pid);
    for (const childPid of children) {
      const childCommand = getProcessCommand(childPid);
      if (isClaudeProcess(childCommand)) return true;
    }

    return false;
  }

  /**
   * Handle terminal opened - poll for Claude terminal detection
   */
  private async onTerminalOpened(terminal: vscode.Terminal): Promise<void> {
    // Poll for terminal detection with timeout
    // Terminal processes may not be available immediately
    for (let i = 0; i < TERMINAL_DETECTION_MAX_ATTEMPTS; i++) {
      // Check if terminal was closed during detection polling
      if (terminal.exitStatus !== undefined) {
        return; // Terminal already closed, don't track
      }

      if (await this.isClaudeTerminal(terminal)) {
        // Double-check terminal is still open before tracking
        if (terminal.exitStatus !== undefined) {
          return;
        }

        // TOCTOU: Terminal may close between the check and tracking
        // Wrap in try-catch to handle gracefully
        try {
          await this.trackTerminal(terminal);
        } catch (err) {
          // Terminal may have closed during tracking - this is fine
          console.log('Terminal closed during tracking:', err);
        }
        return;
      }
      await sleep(TERMINAL_DETECTION_DELAY_MS);
    }
  }

  /**
   * Handle terminal closed
   */
  private async onTerminalClosed(terminal: vscode.Terminal): Promise<void> {
    // Find which workspace this terminal belonged to
    let closedWorkspacePath: string | undefined;

    for (const [workspacePath, terminals] of this.activeClaudeTerminals) {
      if (terminals.has(terminal)) {
        terminals.delete(terminal);
        closedWorkspacePath = workspacePath;

        // Clean up empty sets
        if (terminals.size === 0) {
          this.activeClaudeTerminals.delete(workspacePath);
        }
        break;
      }
    }

    if (!closedWorkspacePath) {
      return;  // Not a tracked terminal
    }

    await this.storage.markClosed(closedWorkspacePath);

    // Sync to cross-window state
    this.syncCrossWindowState();

    // Update status bar first, before showing notification
    this.updateStatusBar();

    // Show notification that session can be resumed
    this.showCloseNotification();
  }

  /**
   * Show notification when Claude terminal closes
   */
  private showCloseNotification(): void {
    vscode.window.showInformationMessage(
      'Claude Code session closed. You can resume it anytime.',
      'Resume Now',
      'Dismiss'
    ).then(
      action => {
        if (action === 'Resume Now') {
          vscode.commands.executeCommand('claude-tracker.resumeLast')
            .then(undefined, err => {
              console.error('Failed to resume session:', err);
              vscode.window.showErrorMessage('Failed to resume Claude session');
            });
        }
        // action is undefined if user dismissed (Escape/click outside)
      },
      err => {
        // Actual API error (rare) - not user dismissal
        console.error('Notification API error:', err);
      }
    );
  }

  /**
   * Track a Claude terminal
   * Determines workspace from terminal's cwd when possible
   */
  private async trackTerminal(terminal: vscode.Terminal): Promise<void> {
    // Try to get terminal's actual cwd for multi-root support
    const pid = await terminal.processId;
    let workspacePath: string | undefined;

    if (pid) {
      const cwd = getProcessCwd(pid);
      if (cwd) {
        // Map cwd to a workspace folder, or use cwd directly
        workspacePath = getWorkspaceForPath(cwd) ?? cwd;
      }
    }

    // Fallback to first workspace
    workspacePath ??= getCurrentWorkspacePath();
    if (!workspacePath) return;

    // Track per-workspace
    if (!this.activeClaudeTerminals.has(workspacePath)) {
      this.activeClaudeTerminals.set(workspacePath, new Set());
    }
    this.activeClaudeTerminals.get(workspacePath)!.add(terminal);

    // Get git branch with caching
    const gitBranch = await this.getGitBranchCached(workspacePath);

    await this.storage.trackSession({
      projectPath: workspacePath,
      terminalName: terminal.name,
      gitBranch,
    });

    // Sync to cross-window state
    this.syncCrossWindowState();

    this.updateStatusBar();
  }

  /**
   * Sync local terminals to cross-window state file
   */
  private syncCrossWindowState(): void {
    const terminals: { name: string; workspacePath: string }[] = [];

    for (const [workspacePath, terminalSet] of this.activeClaudeTerminals) {
      for (const terminal of terminalSet) {
        terminals.push({
          name: terminal.name,
          workspacePath,
        });
      }
    }

    this.crossWindowState.updateTerminals(terminals);
  }

  /**
   * Get git branch with caching
   * Uses robust detection with timeout and error handling
   */
  private async getGitBranchCached(cwd: string): Promise<string | undefined> {
    const cached = this.gitBranchCache.get(cwd);
    const now = Date.now();

    if (cached && (now - cached.timestamp) < GIT_CACHE_TTL_MS) {
      return cached.branch;
    }

    const result = await getGitBranchRobust(cwd);
    this.gitBranchCache.set(cwd, { branch: result.branch, timestamp: now });

    // Log non-success cases for debugging
    if (result.status !== 'success' && result.status !== 'not-git-repo') {
      console.log(`Git branch ${result.status}: ${result.error ?? ''}`);
    }

    return result.branch;
  }

  /**
   * Update status bar based on current state
   * Uses global count from cross-window state when available
   */
  private updateStatusBar(globalCountOverride?: number): void {
    // Get global count from cross-window state (includes all VS Code windows)
    const globalCount = globalCountOverride ?? this.crossWindowState.getTotalCount();

    // Count local terminals (this window only)
    let localCount = 0;
    for (const terminals of this.activeClaudeTerminals.values()) {
      localCount += terminals.size;
    }

    // Show global count if there are active terminals anywhere
    if (globalCount > 0) {
      this.statusBar.showActive(globalCount, localCount);
      return;
    }

    // Check for crash-recoverable sessions (higher priority than normal resumable)
    const recoverableSessions = this.crossWindowState.getRecoverableSessions();
    if (recoverableSessions.length > 0) {
      // Deduplicate by workspace path
      const uniquePaths = new Set(recoverableSessions.map(s => s.workspacePath));
      this.statusBar.showRecoverable(uniquePaths.size);
      return;
    }

    if (this.storage.hasResumableSession()) {
      this.statusBar.showResumable();
      return;
    }

    this.statusBar.hide();
  }

  /**
   * Get all active Claude terminals
   */
  getActiveTerminals(): vscode.Terminal[] {
    const terminals: vscode.Terminal[] = [];
    for (const set of this.activeClaudeTerminals.values()) {
      terminals.push(...set);
    }
    return terminals;
  }

  /**
   * Get the cross-window state manager instance
   * Used by commands for crash recovery
   */
  getCrossWindowState(): CrossWindowStateManager {
    return this.crossWindowState;
  }
}
