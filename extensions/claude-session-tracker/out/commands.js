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
exports.registerCommands = registerCommands;
exports.loadAllEnrichedSessions = loadAllEnrichedSessions;
exports.loadEnrichedSessionsForProject = loadEnrichedSessionsForProject;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const utils_1 = require("./utils");
const logger_1 = require("./logger");
/**
 * Extract terminal display context from an EnrichedSession
 */
function toTerminalContext(session) {
    return {
        displayTitle: session.displayTitle,
        model: session.model,
        gitBranch: session.gitBranch,
        numTurns: session.numTurns,
        totalCostUsd: session.totalCostUsd,
        modified: session.modified,
    };
}
/**
 * Register all extension commands
 */
function registerCommands(context, storage, watcher, crossWindowState) {
    // Focus active Claude terminal
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.focusTerminal', async () => {
        const activeTerminals = watcher.getActiveTerminals();
        if (activeTerminals.length === 0) {
            vscode.window.showInformationMessage('No active Claude terminals');
            return;
        }
        if (activeTerminals.length === 1) {
            activeTerminals[0].show();
            return;
        }
        const items = activeTerminals.map((terminal, index) => ({
            label: terminal.name,
            description: `Terminal ${index + 1}`,
            terminal,
        }));
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select Claude terminal to focus',
        });
        if (selected) {
            selected.terminal.show();
        }
    }));
    // Show unified session picker: active terminals + recent resumable sessions
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.showAllTerminals', async () => {
        const claudeTerminals = watcher.getActiveTerminals();
        const recentSessions = await loadRecentEnrichedSessions(12);
        const items = [];
        // Active terminals first
        for (const terminal of claudeTerminals) {
            items.push({
                type: 'active',
                label: `$(terminal-tmux) ${terminal.name}`,
                description: '$(circle-filled) Active',
                detail: 'Click to focus this terminal',
                terminal,
            });
        }
        // Resumable sessions
        const showEnriched = (0, utils_1.shouldShowEnrichedData)();
        for (const session of recentSessions) {
            const age = (0, utils_1.formatRelativeTime)(session.modified);
            const descParts = [];
            if (showEnriched && session.model)
                descParts.push(session.model);
            if (showEnriched && session.numTurns)
                descParts.push(`${session.numTurns} turns`);
            if (!descParts.length && session.gitBranch)
                descParts.push(`$(git-branch) ${session.gitBranch}`);
            if (!descParts.length)
                descParts.push(`$(folder) ${session.projectName}`);
            const detailParts = [session.projectPath, age];
            if (session.gitBranch && descParts[0] !== `$(git-branch) ${session.gitBranch}`) {
                detailParts.splice(1, 0, session.gitBranch);
            }
            if (showEnriched && session.totalCostUsd)
                detailParts.push((0, utils_1.formatCost)(session.totalCostUsd));
            items.push({
                type: 'resumable',
                label: `$(debug-restart) ${(0, utils_1.truncate)(session.displayTitle, 50)}`,
                description: descParts.join(' \u00b7 '),
                detail: detailParts.join(' \u00b7 '),
                sessionId: session.id,
                workspacePath: session.projectPath,
                sessionCtx: toTerminalContext(session),
            });
        }
        if (items.length === 0) {
            vscode.window.showInformationMessage('No Claude sessions found in the last 12 hours');
            return;
        }
        const activeCount = claudeTerminals.length;
        const resumableCount = recentSessions.length;
        const placeHolder = activeCount > 0
            ? `${activeCount} active, ${resumableCount} resumable sessions (last 12h)`
            : `${resumableCount} resumable sessions (last 12h)`;
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder,
            matchOnDescription: true,
            matchOnDetail: true,
        });
        if (!selected)
            return;
        if (selected.type === 'active' && selected.terminal) {
            selected.terminal.show();
        }
        else if (selected.type === 'resumable' && selected.workspacePath && selected.sessionId) {
            try {
                const terminal = (0, utils_1.createEnrichedTerminal)(selected.workspacePath, selected.sessionCtx);
                (0, utils_1.sendSafeCommand)(terminal, 'claude --resume', selected.sessionId);
            }
            catch (err) {
                logger_1.logger.error('Failed to resume session:', err);
                vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
            }
        }
    }));
    // Show sessions across all projects
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.showAllSessions', async () => {
        const sessions = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Loading Claude sessions across all projects...',
            cancellable: false,
        }, () => loadAllEnrichedSessions());
        if (sessions.length === 0) {
            vscode.window.showInformationMessage('No Claude sessions found');
            return;
        }
        const showEnriched = (0, utils_1.shouldShowEnrichedData)();
        const items = sessions.map(s => {
            const descParts = [`$(folder) ${s.projectName}`];
            if (showEnriched && s.model)
                descParts.push(s.model);
            const detailParts = [];
            if (s.gitBranch)
                detailParts.push(`$(git-branch) ${s.gitBranch}`);
            if (showEnriched && s.numTurns)
                detailParts.push(`${s.numTurns} turns`);
            if (showEnriched && s.totalCostUsd)
                detailParts.push((0, utils_1.formatCost)(s.totalCostUsd));
            detailParts.push((0, utils_1.formatRelativeTime)(s.modified));
            return {
                label: (0, utils_1.truncate)(s.displayTitle, 60),
                description: descParts.join(' \u00b7 '),
                detail: detailParts.join(' \u00b7 '),
                sessionId: s.id,
                projectPath: s.projectPath,
                sessionCtx: toTerminalContext(s),
            };
        });
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: `${sessions.length} recent sessions across all projects`,
            matchOnDescription: true,
            matchOnDetail: true,
        });
        if (selected) {
            try {
                const terminal = (0, utils_1.createEnrichedTerminal)(selected.projectPath, selected.sessionCtx);
                (0, utils_1.sendSafeCommand)(terminal, 'claude --resume', selected.sessionId);
            }
            catch (err) {
                logger_1.logger.error('Failed to resume session:', err);
                vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
            }
        }
    }));
    // Recover sessions from crash
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.recoverSessions', async () => {
        const recoverable = crossWindowState.getRecoverableSessions();
        if (recoverable.length === 0) {
            vscode.window.showInformationMessage('No sessions to recover');
            return;
        }
        const uniquePaths = new Map();
        for (const session of recoverable) {
            if (!uniquePaths.has(session.workspacePath) ||
                uniquePaths.get(session.workspacePath).lastUpdate < session.lastUpdate) {
                uniquePaths.set(session.workspacePath, session);
            }
        }
        const sessions = Array.from(uniquePaths.values());
        const items = sessions.map(s => ({
            label: `$(folder) ${path.basename(s.workspacePath)}`,
            description: s.name,
            detail: `Last active: ${(0, utils_1.formatRelativeTime)(new Date(s.lastUpdate).toISOString())}`,
            workspacePath: s.workspacePath,
            lastUpdate: s.lastUpdate,
            picked: true,
        }));
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: `${sessions.length} session(s) to recover from crash`,
            canPickMany: true,
        });
        if (!selected || selected.length === 0) {
            crossWindowState.clearStaleSessions();
            return;
        }
        for (const item of selected) {
            try {
                const terminal = (0, utils_1.createEnrichedTerminal)(item.workspacePath, {
                    isRecovery: true,
                    modified: new Date(item.lastUpdate).toISOString(),
                });
                await new Promise(resolve => setTimeout(resolve, 500));
                (0, utils_1.sendSafeCommand)(terminal, 'claude --continue');
            }
            catch (err) {
                logger_1.logger.error(`Failed to recover session for ${item.workspacePath}:`, err);
            }
        }
        crossWindowState.clearStaleSessions();
        vscode.window.showInformationMessage(`Recovered ${selected.length} Claude session(s)`);
    }));
    // Resume ALL recoverable sessions at once
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.resumeAll', async () => {
        logger_1.logger.info('resumeAll command invoked');
        const recoverable = crossWindowState.getRecoverableSessions();
        logger_1.logger.info(`Found ${recoverable.length} recoverable sessions`);
        if (recoverable.length === 0) {
            logger_1.logger.info('No sessions to resume');
            vscode.window.showInformationMessage('No sessions to resume');
            return;
        }
        const uniquePaths = new Map();
        for (const session of recoverable) {
            uniquePaths.set(session.workspacePath, session);
            logger_1.logger.debug(`Session to recover: ${session.workspacePath}`);
        }
        const sessions = Array.from(uniquePaths.values());
        logger_1.logger.info(`Unique sessions to recover: ${sessions.length}`);
        const action = await vscode.window.showInformationMessage(`Resume ${sessions.length} Claude session(s) from before crash?`, 'Resume All', 'Pick Sessions', 'Dismiss');
        logger_1.logger.info(`User selected: ${action ?? 'Dismiss'}`);
        if (action === 'Resume All') {
            let successCount = 0;
            let failCount = 0;
            for (const session of sessions) {
                try {
                    logger_1.logger.info(`Attempting to resume session in: ${session.workspacePath}`);
                    const terminal = (0, utils_1.createEnrichedTerminal)(session.workspacePath, { isRecovery: true });
                    logger_1.logger.debug(`Created terminal for ${session.workspacePath}`);
                    await new Promise(resolve => setTimeout(resolve, 500));
                    (0, utils_1.sendSafeCommand)(terminal, 'claude --continue');
                    logger_1.logger.info(`Sent 'claude --continue' to terminal for ${session.workspacePath}`);
                    successCount++;
                }
                catch (err) {
                    failCount++;
                    logger_1.logger.error(`Failed to resume session for ${session.workspacePath}:`, err);
                }
            }
            logger_1.logger.info(`Resume complete: ${successCount} succeeded, ${failCount} failed`);
            crossWindowState.clearStaleSessions();
            vscode.window.showInformationMessage(`Resumed ${successCount} Claude session(s)${failCount > 0 ? ` (${failCount} failed)` : ''}`);
        }
        else if (action === 'Pick Sessions') {
            vscode.commands.executeCommand('claude-tracker.recoverSessions');
        }
        else {
            logger_1.logger.info('User dismissed, clearing stale sessions');
            crossWindowState.clearStaleSessions();
        }
    }));
    // Resume last session - supports multi-root workspaces
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.resumeLast', async () => {
        const resumableWorkspaces = (0, utils_1.getAllWorkspacePaths)()
            .filter(path => storage.getResumableForProject(path));
        let targetWorkspace;
        if (resumableWorkspaces.length === 0) {
            targetWorkspace = (0, utils_1.getCurrentWorkspacePath)();
            if (!targetWorkspace) {
                vscode.window.showWarningMessage('No workspace folder open');
                return;
            }
        }
        else if (resumableWorkspaces.length === 1) {
            targetWorkspace = resumableWorkspaces[0];
        }
        else {
            const items = resumableWorkspaces.map(workspacePath => ({
                label: path.basename(workspacePath),
                description: workspacePath,
                workspacePath,
            }));
            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select workspace to resume Claude session',
            });
            if (!selected)
                return;
            targetWorkspace = selected.workspacePath;
        }
        try {
            // Look up most recent session for enriched terminal display
            const recentSessions = await loadEnrichedSessionsForProject(targetWorkspace);
            const sessionCtx = recentSessions.length > 0
                ? toTerminalContext(recentSessions[0])
                : undefined;
            const terminal = (0, utils_1.createEnrichedTerminal)(targetWorkspace, sessionCtx);
            (0, utils_1.sendSafeCommand)(terminal, 'claude --continue');
            await storage.clearResumable(targetWorkspace);
        }
        catch (err) {
            logger_1.logger.error('Failed to resume Claude session:', err);
            vscode.window.showErrorMessage(`Failed to resume Claude session: ${err}`);
        }
    }));
    // Pick from recent sessions
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.pickSession', async () => {
        const cwd = (0, utils_1.getCurrentWorkspacePath)();
        if (!cwd) {
            vscode.window.showWarningMessage('No workspace folder open');
            return;
        }
        const sessions = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Loading Claude sessions...',
            cancellable: false,
        }, () => loadEnrichedSessionsForProject(cwd));
        if (sessions.length === 0) {
            vscode.window.showInformationMessage('No Claude sessions found for this workspace');
            return;
        }
        const showEnriched = (0, utils_1.shouldShowEnrichedData)();
        const items = sessions.map(s => {
            const descParts = [];
            if (showEnriched && s.model)
                descParts.push(s.model);
            if (showEnriched && s.numTurns)
                descParts.push(`${s.numTurns} turns`);
            if (!descParts.length) {
                descParts.push(s.gitBranch ? `$(git-branch) ${s.gitBranch}` : '$(circle-slash) No branch');
            }
            const detailParts = [(0, utils_1.formatRelativeTime)(s.modified)];
            if (s.gitBranch && showEnriched)
                detailParts.push(s.gitBranch);
            if (showEnriched && s.totalCostUsd)
                detailParts.push((0, utils_1.formatCost)(s.totalCostUsd));
            return {
                label: (0, utils_1.truncate)(s.displayTitle, 60),
                description: descParts.join(' \u00b7 '),
                detail: detailParts.join(' \u00b7 '),
                sessionId: s.id,
                sessionCtx: toTerminalContext(s),
            };
        });
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a session to resume',
            matchOnDescription: true,
            matchOnDetail: true,
        });
        if (selected) {
            try {
                const terminal = (0, utils_1.createEnrichedTerminal)(cwd, selected.sessionCtx);
                (0, utils_1.sendSafeCommand)(terminal, 'claude --resume', selected.sessionId);
            }
            catch (err) {
                logger_1.logger.error('Failed to resume session:', err);
                vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
            }
        }
    }));
    // Show recent sessions - alias for pickSession
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.showSessions', () => {
        vscode.commands.executeCommand('claude-tracker.pickSession');
    }));
    // Resume specific session (used by Session Browser TreeView)
    context.subscriptions.push(vscode.commands.registerCommand('claude-tracker.resumeSession', async (sessionId, projectPath, sessionCtx) => {
        try {
            const terminal = (0, utils_1.createEnrichedTerminal)(projectPath, sessionCtx);
            (0, utils_1.sendSafeCommand)(terminal, 'claude --resume', sessionId);
        }
        catch (err) {
            logger_1.logger.error('Failed to resume session:', err);
            vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
            throw err;
        }
    }));
}
// === Session Loading via Index + Cache ===
/**
 * Load the session summaries cache
 */
async function loadSummaryCache() {
    try {
        const content = await fs.promises.readFile(utils_1.SESSION_SUMMARIES_PATH, 'utf-8');
        return JSON.parse(content);
    }
    catch {
        return {};
    }
}
/**
 * Decode a project directory name back to the original path.
 * Uses sessions-index.json projectPath as ground truth.
 */
function decodeProjectPath(projectDir) {
    const encoded = path.basename(projectDir);
    return encoded.replace(/^-/, '/').replace(/-/g, '/');
}
/**
 * Build an EnrichedSession from index entry + summary cache
 */
function buildEnrichedSession(entry, projectPath, cache) {
    const cached = cache[entry.sessionId];
    const projectName = path.basename(projectPath);
    // Resolve display title: customTitle > cached title > firstPrompt
    let displayTitle = entry.customTitle || cached?.title || entry.summary || '';
    if (!displayTitle && entry.firstPrompt) {
        displayTitle = (0, utils_1.truncate)(entry.firstPrompt, 60);
    }
    if (!displayTitle) {
        displayTitle = `Session ${entry.sessionId.substring(0, 8)}`;
    }
    // Model shortening
    const model = cached?.model ? (0, utils_1.shortenModelName)(cached.model) : undefined;
    return {
        id: entry.sessionId,
        projectPath,
        projectName,
        displayTitle,
        firstPrompt: entry.firstPrompt || cached?.first_msg || '',
        summary: cached?.summary || entry.summary,
        messageCount: entry.messageCount,
        gitBranch: entry.gitBranch,
        created: entry.created || '',
        modified: entry.modified || entry.created || '',
        isSidechain: entry.isSidechain || false,
        model,
        numTurns: cached?.num_turns,
        totalCostUsd: cached?.total_cost_usd,
    };
}
/**
 * Load all enriched sessions across all projects
 */
async function loadAllEnrichedSessions() {
    try {
        await fs.promises.access(utils_1.CLAUDE_PROJECTS_DIR);
    }
    catch {
        return [];
    }
    const cache = await loadSummaryCache();
    const hideSidechain = (0, utils_1.shouldHideSidechainSessions)();
    const sessions = [];
    let projectDirs;
    try {
        const entries = await fs.promises.readdir(utils_1.CLAUDE_PROJECTS_DIR, { withFileTypes: true });
        projectDirs = entries.filter(e => e.isDirectory()).map(e => e.name);
    }
    catch {
        return [];
    }
    for (const dirName of projectDirs) {
        const indexPath = path.join(utils_1.CLAUDE_PROJECTS_DIR, dirName, 'sessions-index.json');
        try {
            const content = await fs.promises.readFile(indexPath, 'utf-8');
            const index = JSON.parse(content);
            if (!index.entries || !Array.isArray(index.entries))
                continue;
            // Use projectPath from first entry as ground truth, fall back to decode
            const projectPath = index.entries[0]?.projectPath || decodeProjectPath(dirName);
            for (const entry of index.entries) {
                const session = buildEnrichedSession(entry, entry.projectPath || projectPath, cache);
                if (hideSidechain && session.isSidechain)
                    continue;
                sessions.push(session);
            }
        }
        catch {
            // No index or parse error — skip
        }
    }
    // Sort by modified timestamp descending
    sessions.sort((a, b) => {
        const ta = a.modified ? new Date(a.modified).getTime() : 0;
        const tb = b.modified ? new Date(b.modified).getTime() : 0;
        return tb - ta;
    });
    return sessions.slice(0, utils_1.MAX_RECENT_SESSIONS * 2);
}
/**
 * Load enriched sessions for a specific project workspace
 */
async function loadEnrichedSessionsForProject(workspacePath) {
    const encodedPath = (0, utils_1.encodeWorkspacePath)(workspacePath);
    const indexPath = path.join(utils_1.CLAUDE_PROJECTS_DIR, encodedPath, 'sessions-index.json');
    try {
        await fs.promises.access(indexPath);
    }
    catch {
        return [];
    }
    const cache = await loadSummaryCache();
    const hideSidechain = (0, utils_1.shouldHideSidechainSessions)();
    try {
        const content = await fs.promises.readFile(indexPath, 'utf-8');
        const index = JSON.parse(content);
        if (!index.entries || !Array.isArray(index.entries))
            return [];
        const sessions = [];
        for (const entry of index.entries) {
            const session = buildEnrichedSession(entry, workspacePath, cache);
            if (hideSidechain && session.isSidechain)
                continue;
            sessions.push(session);
        }
        // Sort by modified descending
        sessions.sort((a, b) => {
            const ta = a.modified ? new Date(a.modified).getTime() : 0;
            const tb = b.modified ? new Date(b.modified).getTime() : 0;
            return tb - ta;
        });
        return sessions.slice(0, utils_1.MAX_RECENT_SESSIONS);
    }
    catch {
        return [];
    }
}
/**
 * Load recent enriched sessions from last N hours (across all projects)
 */
async function loadRecentEnrichedSessions(hours) {
    const cutoffTime = Date.now() - (hours * 60 * 60 * 1000);
    const all = await loadAllEnrichedSessions();
    return all.filter(s => {
        const t = s.modified ? new Date(s.modified).getTime() : 0;
        return t > cutoffTime;
    }).slice(0, utils_1.MAX_RECENT_SESSIONS);
}
//# sourceMappingURL=commands.js.map