import * as vscode from 'vscode';
import * as path from 'path';
import { SessionStorage } from './sessionStorage';
import { StatusBarManager } from './statusBar';
import { TerminalWatcher } from './terminalWatcher';
import { registerCommands, loadAllEnrichedSessions } from './commands';
import { isAutoResumeEnabled, CLAUDE_PROJECTS_DIR, SESSION_SUMMARIES_PATH } from './utils';
import { logger } from './logger';
import { SessionBrowserProvider } from './sessionBrowser';

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
 * - Enriched display: model, turns, cost from tracker-suite data
 * - Auto-refresh via FileSystemWatcher on index/summary files
 */
export function activate(context: vscode.ExtensionContext): void {
  // Initialize logger first
  logger.init(context);
  logger.info('Claude Session Tracker activating...');

  // Initialize components
  const storage = new SessionStorage(context);
  const statusBar = new StatusBarManager(context);
  const watcher = new TerminalWatcher(context, storage, statusBar);

  // Get cross-window state manager for commands
  const crossWindowState = watcher.getCrossWindowState();

  // Register commands (pass watcher and crossWindowState for crash recovery)
  registerCommands(context, storage, watcher, crossWindowState);

  // Register Session Browser TreeView with enriched data loader
  const sessionBrowserProvider = new SessionBrowserProvider(loadAllEnrichedSessions);
  const sessionBrowserView = vscode.window.createTreeView('claudeSessionBrowser', {
    treeDataProvider: sessionBrowserProvider,
    showCollapseAll: false,
  });
  context.subscriptions.push(sessionBrowserView);

  // Register refresh command for Session Browser
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.refreshSessions', () => {
      sessionBrowserProvider.refresh();
    })
  );

  // === FileSystemWatchers for auto-refresh ===

  let refreshDebounceTimer: ReturnType<typeof setTimeout> | undefined;
  const debouncedRefresh = () => {
    if (refreshDebounceTimer) clearTimeout(refreshDebounceTimer);
    refreshDebounceTimer = setTimeout(() => {
      sessionBrowserProvider.refresh();
    }, 2000);
  };

  // Clean up debounce timer on deactivation to prevent firing on disposed objects
  context.subscriptions.push({
    dispose: () => {
      if (refreshDebounceTimer) {
        clearTimeout(refreshDebounceTimer);
        refreshDebounceTimer = undefined;
      }
    }
  });

  // Watch sessions-index.json files across all projects
  try {
    const indexPattern = new vscode.RelativePattern(
      vscode.Uri.file(CLAUDE_PROJECTS_DIR),
      '**/sessions-index.json'
    );
    const indexWatcher = vscode.workspace.createFileSystemWatcher(indexPattern);
    indexWatcher.onDidChange(debouncedRefresh);
    indexWatcher.onDidCreate(debouncedRefresh);
    context.subscriptions.push(indexWatcher);
    logger.info('FileSystemWatcher: watching sessions-index.json files');
  } catch (err) {
    logger.error('Failed to create sessions-index watcher:', err);
  }

  // Watch session-summaries.json for enrichment updates (VS Code API for proper lifecycle)
  try {
    const summaryPattern = new vscode.RelativePattern(
      vscode.Uri.file(path.dirname(SESSION_SUMMARIES_PATH)),
      'session-summaries.json'
    );
    const summaryWatcher = vscode.workspace.createFileSystemWatcher(summaryPattern);
    summaryWatcher.onDidChange(debouncedRefresh);
    summaryWatcher.onDidCreate(debouncedRefresh);
    context.subscriptions.push(summaryWatcher);
    logger.info('FileSystemWatcher: watching session-summaries.json');
  } catch (err) {
    logger.error('Failed to create session-summaries watcher:', err);
  }

  // Start watching terminals - wait for initial scan to complete before
  // checking crash recovery to avoid race conditions with status bar state
  watcher.activate().then(
    () => {
      // Check for crash-recoverable sessions (higher priority than normal resume)
      const recoverableSessions = crossWindowState.getRecoverableSessions();
      logger.info(`Found ${recoverableSessions.length} recoverable sessions from cross-window state`);

      if (recoverableSessions.length > 0) {
        for (const session of recoverableSessions) {
          logger.debug(`Recoverable session: ${session.workspacePath} (window: ${session.windowId}, lastUpdate: ${new Date(session.lastUpdate).toISOString()})`);
        }

        const uniquePaths = new Set(recoverableSessions.map(s => s.workspacePath));
        const count = uniquePaths.size;
        logger.info(`Unique workspace paths to recover: ${count}`);

        vscode.window.showWarningMessage(
          `${count} Claude session(s) can be recovered from crash.`,
          'Resume All',
          'Pick Sessions',
          'Dismiss'
        ).then(
          action => {
            logger.info(`User chose: ${action ?? 'Dismiss'}`);
            if (action === 'Resume All') {
              vscode.commands.executeCommand('claude-tracker.resumeAll')
                .then(undefined, err => {
                  logger.error('Failed to resume all sessions:', err);
                  vscode.window.showErrorMessage('Failed to resume sessions');
                });
            } else if (action === 'Pick Sessions') {
              vscode.commands.executeCommand('claude-tracker.recoverSessions')
                .then(undefined, err => {
                  logger.error('Failed to show recovery picker:', err);
                });
            } else {
              logger.info('Clearing stale sessions after dismissal');
              crossWindowState.clearStaleSessions();
            }
          },
          err => {
            logger.error('Recovery notification API error:', err);
          }
        );
      } else if (isAutoResumeEnabled() && storage.hasResumableSession()) {
        logger.info('Found resumable session from storage, showing auto-resume prompt');
        vscode.window.showInformationMessage(
          'A previous Claude session can be resumed.',
          'Resume',
          'Dismiss'
        ).then(
          action => {
            logger.info(`User chose: ${action ?? 'Dismiss'}`);
            if (action === 'Resume') {
              vscode.commands.executeCommand('claude-tracker.resumeLast')
                .then(undefined, err => {
                  logger.error('Failed to auto-resume session:', err);
                  vscode.window.showErrorMessage('Failed to resume Claude session');
                });
            }
          },
          err => {
            logger.error('Auto-resume notification API error:', err);
          }
        );
      } else {
        logger.info('No sessions to recover or resume');
      }

      logger.info('Claude Session Tracker activated successfully');
    },
    err => {
      logger.error('Failed to activate terminal watcher:', err);
    }
  );
}

export function deactivate(): void {
  logger.info('Claude Session Tracker deactivated');
}
