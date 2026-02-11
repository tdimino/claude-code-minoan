"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const sessionStorage_1 = require("./sessionStorage");
const statusBar_1 = require("./statusBar");
const terminalWatcher_1 = require("./terminalWatcher");
const commands_1 = require("./commands");
const utils_1 = require("./utils");
const logger_1 = require("./logger");
const sessionBrowser_1 = require("./sessionBrowser");
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
function activate(context) {
    // Initialize logger first
    logger_1.logger.init(context);
    logger_1.logger.info('Claude Session Tracker activating...');
    // Initialize components
    const storage = new sessionStorage_1.SessionStorage(context);
    const statusBar = new statusBar_1.StatusBarManager(context);
    const watcher = new terminalWatcher_1.TerminalWatcher(context, storage, statusBar);
    // Get cross-window state manager for commands
    const crossWindowState = watcher.getCrossWindowState();
    // Register commands (pass watcher and crossWindowState for crash recovery)
    (0, commands_1.registerCommands)(context, storage, watcher, crossWindowState);
    // Register Session Browser TreeView with enriched data loader
    const sessionBrowserProvider = new sessionBrowser_1.SessionBrowserProvider(commands_1.loadAllEnrichedSessions);
    const sessionBrowserView = vscode.window.createTreeView('claudeSessionBrowser', {
        treeDataProvider: sessionBrowserProvider,
        showCollapseAll: false,
    });
    context.subscriptions.push(sessionBrowserView);
    // Register refresh command for Session Browser
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.refreshSessions', () => {
        sessionBrowserProvider.refresh();
    }));
    // === FileSystemWatchers for auto-refresh ===
    let refreshDebounceTimer;
    const debouncedRefresh = () => {
        if (refreshDebounceTimer)
            clearTimeout(refreshDebounceTimer);
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
        const indexPattern = new vscode.RelativePattern(vscode.Uri.file(utils_1.CLAUDE_PROJECTS_DIR), '**/sessions-index.json');
        const indexWatcher = vscode.workspace.createFileSystemWatcher(indexPattern);
        indexWatcher.onDidChange(debouncedRefresh);
        indexWatcher.onDidCreate(debouncedRefresh);
        context.subscriptions.push(indexWatcher);
        logger_1.logger.info('FileSystemWatcher: watching sessions-index.json files');
    }
    catch (err) {
        logger_1.logger.error('Failed to create sessions-index watcher:', err);
    }
    // Watch session-summaries.json for enrichment updates (VS Code API for proper lifecycle)
    try {
        const summaryPattern = new vscode.RelativePattern(vscode.Uri.file(path.dirname(utils_1.SESSION_SUMMARIES_PATH)), 'session-summaries.json');
        const summaryWatcher = vscode.workspace.createFileSystemWatcher(summaryPattern);
        summaryWatcher.onDidChange(debouncedRefresh);
        summaryWatcher.onDidCreate(debouncedRefresh);
        context.subscriptions.push(summaryWatcher);
        logger_1.logger.info('FileSystemWatcher: watching session-summaries.json');
    }
    catch (err) {
        logger_1.logger.error('Failed to create session-summaries watcher:', err);
    }
    // Start watching terminals - wait for initial scan to complete before
    // checking crash recovery to avoid race conditions with status bar state
    watcher.activate().then(() => {
        // Check for crash-recoverable sessions (higher priority than normal resume)
        const recoverableSessions = crossWindowState.getRecoverableSessions();
        logger_1.logger.info(`Found ${recoverableSessions.length} recoverable sessions from cross-window state`);
        if (recoverableSessions.length > 0) {
            for (const session of recoverableSessions) {
                logger_1.logger.debug(`Recoverable session: ${session.workspacePath} (window: ${session.windowId}, lastUpdate: ${new Date(session.lastUpdate).toISOString()})`);
            }
            const uniquePaths = new Set(recoverableSessions.map(s => s.workspacePath));
            const count = uniquePaths.size;
            logger_1.logger.info(`Unique workspace paths to recover: ${count}`);
            vscode.window.showWarningMessage(`${count} Claude session(s) can be recovered from crash.`, 'Resume All', 'Pick Sessions', 'Dismiss').then(action => {
                logger_1.logger.info(`User chose: ${action ?? 'Dismiss'}`);
                if (action === 'Resume All') {
                    vscode.commands.executeCommand('claude-tracker.resumeAll')
                        .then(undefined, err => {
                        logger_1.logger.error('Failed to resume all sessions:', err);
                        vscode.window.showErrorMessage('Failed to resume sessions');
                    });
                }
                else if (action === 'Pick Sessions') {
                    vscode.commands.executeCommand('claude-tracker.recoverSessions')
                        .then(undefined, err => {
                        logger_1.logger.error('Failed to show recovery picker:', err);
                    });
                }
                else {
                    logger_1.logger.info('Clearing stale sessions after dismissal');
                    crossWindowState.clearStaleSessions();
                }
            }, err => {
                logger_1.logger.error('Recovery notification API error:', err);
            });
        }
        else if ((0, utils_1.isAutoResumeEnabled)() && storage.hasResumableSession()) {
            logger_1.logger.info('Found resumable session from storage, showing auto-resume prompt');
            vscode.window.showInformationMessage('A previous Claude session can be resumed.', 'Resume', 'Dismiss').then(action => {
                logger_1.logger.info(`User chose: ${action ?? 'Dismiss'}`);
                if (action === 'Resume') {
                    vscode.commands.executeCommand('claude-tracker.resumeLast')
                        .then(undefined, err => {
                        logger_1.logger.error('Failed to auto-resume session:', err);
                        vscode.window.showErrorMessage('Failed to resume Claude session');
                    });
                }
            }, err => {
                logger_1.logger.error('Auto-resume notification API error:', err);
            });
        }
        else {
            logger_1.logger.info('No sessions to recover or resume');
        }
        logger_1.logger.info('Claude Session Tracker activated successfully');
    }, err => {
        logger_1.logger.error('Failed to activate terminal watcher:', err);
    });
}
function deactivate() {
    logger_1.logger.info('Claude Session Tracker deactivated');
}
//# sourceMappingURL=extension.js.map