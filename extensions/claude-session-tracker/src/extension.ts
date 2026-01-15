import * as vscode from 'vscode';
import { SessionStorage } from './sessionStorage';
import { StatusBarManager } from './statusBar';
import { TerminalWatcher } from './terminalWatcher';
import { registerCommands } from './commands';
import { isAutoResumeEnabled } from './utils';

/**
 * Claude Session Tracker Extension
 *
 * Tracks VS Code terminals running Claude Code and enables easy session
 * resumption after crashes or disconnections.
 *
 * Features:
 * - Detects Claude Code terminals automatically
 * - Shows status bar indicator when sessions are active/resumable
 * - Cross-window tracking to see all Claude sessions
 * - Crash recovery to resume sessions after VS Code crashes
 * - Cmd+Shift+C to quickly resume last session
 * - Session picker to choose from recent sessions
 */
export function activate(context: vscode.ExtensionContext): void {
  console.log('Claude Session Tracker activating...');

  // Initialize components
  const storage = new SessionStorage(context);
  const statusBar = new StatusBarManager(context);
  const watcher = new TerminalWatcher(context, storage, statusBar);

  // Start watching terminals first (so watcher has terminals tracked)
  watcher.activate();

  // Get cross-window state manager for commands
  const crossWindowState = watcher.getCrossWindowState();

  // Register commands (pass watcher and crossWindowState for crash recovery)
  registerCommands(context, storage, watcher, crossWindowState);

  // Check for crash-recoverable sessions FIRST (higher priority than normal resume)
  const recoverableSessions = crossWindowState.getRecoverableSessions();
  if (recoverableSessions.length > 0) {
    // Deduplicate by workspace path
    const uniquePaths = new Set(recoverableSessions.map(s => s.workspacePath));
    const count = uniquePaths.size;

    vscode.window.showWarningMessage(
      `${count} Claude session(s) can be recovered from crash.`,
      'Resume All',
      'Pick Sessions',
      'Dismiss'
    ).then(
      action => {
        if (action === 'Resume All') {
          vscode.commands.executeCommand('claude-tracker.resumeAll')
            .then(undefined, err => {
              console.error('Failed to resume all sessions:', err);
              vscode.window.showErrorMessage('Failed to resume sessions');
            });
        } else if (action === 'Pick Sessions') {
          vscode.commands.executeCommand('claude-tracker.recoverSessions')
            .then(undefined, err => {
              console.error('Failed to show recovery picker:', err);
            });
        } else {
          // Dismissed - clear stale sessions
          crossWindowState.clearStaleSessions();
        }
      },
      err => {
        console.error('Recovery notification API error:', err);
      }
    );
  } else if (isAutoResumeEnabled() && storage.hasResumableSession()) {
    // Normal auto-resume check (no crash recovery needed)
    vscode.window.showInformationMessage(
      'A previous Claude session can be resumed.',
      'Resume',
      'Dismiss'
    ).then(
      action => {
        if (action === 'Resume') {
          vscode.commands.executeCommand('claude-tracker.resumeLast')
            .then(undefined, err => {
              console.error('Failed to auto-resume session:', err);
              vscode.window.showErrorMessage('Failed to resume Claude session');
            });
        }
        // action is undefined if user dismissed (Escape/click outside)
      },
      err => {
        // Actual API error (rare) - not user dismissal
        console.error('Auto-resume notification API error:', err);
      }
    );
  }

  // Update status bar on activation
  if (storage.hasResumableSession()) {
    statusBar.showResumable();
  }

  console.log('Claude Session Tracker activated');
}

export function deactivate(): void {
  console.log('Claude Session Tracker deactivated');
}
