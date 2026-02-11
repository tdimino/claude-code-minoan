import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { SessionStorage } from './sessionStorage';
import { TerminalWatcher } from './terminalWatcher';
import { CrossWindowStateManager } from './crossWindowState';
import type { EnrichedSession, SessionIndexEntry, SessionSummaryCache } from './types';
import {
  getCurrentWorkspacePath,
  getAllWorkspacePaths,
  createResumedTerminal,
  sendSafeCommand,
  encodeWorkspacePath,
  truncate,
  formatRelativeTime,
  formatCost,
  shortenModelName,
  shouldShowEnrichedData,
  shouldHideSidechainSessions,
  MAX_RECENT_SESSIONS,
  CLAUDE_PROJECTS_DIR,
  SESSION_SUMMARIES_PATH,
} from './utils';
import { logger } from './logger';

/**
 * Register all extension commands
 */
export function registerCommands(
  context: vscode.ExtensionContext,
  storage: SessionStorage,
  watcher: TerminalWatcher,
  crossWindowState: CrossWindowStateManager
): void {
  // Focus active Claude terminal
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.focusTerminal', async () => {
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
    })
  );

  // Show unified session picker: active terminals + recent resumable sessions
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.showAllTerminals', async () => {
      const claudeTerminals = watcher.getActiveTerminals();
      const recentSessions = await loadRecentEnrichedSessions(12);

      interface SessionPickerItem extends vscode.QuickPickItem {
        type: 'active' | 'resumable';
        terminal?: vscode.Terminal;
        sessionId?: string;
        workspacePath?: string;
      }

      const items: SessionPickerItem[] = [];

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
      const showEnriched = shouldShowEnrichedData();
      for (const session of recentSessions) {
        const age = formatRelativeTime(session.modified);
        const descParts: string[] = [];
        if (showEnriched && session.model) descParts.push(session.model);
        if (showEnriched && session.numTurns) descParts.push(`${session.numTurns} turns`);
        if (!descParts.length && session.gitBranch) descParts.push(`$(git-branch) ${session.gitBranch}`);
        if (!descParts.length) descParts.push(`$(folder) ${session.projectName}`);

        const detailParts = [session.projectPath, age];
        if (session.gitBranch && descParts[0] !== `$(git-branch) ${session.gitBranch}`) {
          detailParts.splice(1, 0, session.gitBranch);
        }
        if (showEnriched && session.totalCostUsd) detailParts.push(formatCost(session.totalCostUsd));

        items.push({
          type: 'resumable',
          label: `$(debug-restart) ${truncate(session.displayTitle, 50)}`,
          description: descParts.join(' \u00b7 '),
          detail: detailParts.join(' \u00b7 '),
          sessionId: session.id,
          workspacePath: session.projectPath,
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

      if (!selected) return;

      if (selected.type === 'active' && selected.terminal) {
        selected.terminal.show();
      } else if (selected.type === 'resumable' && selected.workspacePath && selected.sessionId) {
        try {
          const terminal = createResumedTerminal(selected.workspacePath);
          sendSafeCommand(terminal, 'claude --resume', selected.sessionId);
        } catch (err) {
          logger.error('Failed to resume session:', err);
          vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
        }
      }
    })
  );

  // Show sessions across all projects
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.showAllSessions', async () => {
      const sessions = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Loading Claude sessions across all projects...',
          cancellable: false,
        },
        () => loadAllEnrichedSessions()
      );

      if (sessions.length === 0) {
        vscode.window.showInformationMessage('No Claude sessions found');
        return;
      }

      const showEnriched = shouldShowEnrichedData();
      const items = sessions.map(s => {
        const descParts = [`$(folder) ${s.projectName}`];
        if (showEnriched && s.model) descParts.push(s.model);

        const detailParts: string[] = [];
        if (s.gitBranch) detailParts.push(`$(git-branch) ${s.gitBranch}`);
        if (showEnriched && s.numTurns) detailParts.push(`${s.numTurns} turns`);
        if (showEnriched && s.totalCostUsd) detailParts.push(formatCost(s.totalCostUsd));
        detailParts.push(formatRelativeTime(s.modified));

        return {
          label: truncate(s.displayTitle, 60),
          description: descParts.join(' \u00b7 '),
          detail: detailParts.join(' \u00b7 '),
          sessionId: s.id,
          projectPath: s.projectPath,
        };
      });

      const selected = await vscode.window.showQuickPick(items, {
        placeHolder: `${sessions.length} recent sessions across all projects`,
        matchOnDescription: true,
        matchOnDetail: true,
      });

      if (selected) {
        try {
          const terminal = createResumedTerminal(selected.projectPath);
          sendSafeCommand(terminal, 'claude --resume', selected.sessionId);
        } catch (err) {
          logger.error('Failed to resume session:', err);
          vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
        }
      }
    })
  );

  // Recover sessions from crash
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.recoverSessions', async () => {
      const recoverable = crossWindowState.getRecoverableSessions();

      if (recoverable.length === 0) {
        vscode.window.showInformationMessage('No sessions to recover');
        return;
      }

      const uniquePaths = new Map<string, { name: string; workspacePath: string; lastUpdate: number }>();
      for (const session of recoverable) {
        if (!uniquePaths.has(session.workspacePath) ||
            uniquePaths.get(session.workspacePath)!.lastUpdate < session.lastUpdate) {
          uniquePaths.set(session.workspacePath, session);
        }
      }

      const sessions = Array.from(uniquePaths.values());

      const items = sessions.map(s => ({
        label: `$(folder) ${path.basename(s.workspacePath)}`,
        description: s.name,
        detail: `Last active: ${formatRelativeTime(new Date(s.lastUpdate).toISOString())}`,
        workspacePath: s.workspacePath,
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
          const terminal = createResumedTerminal(item.workspacePath);
          await new Promise(resolve => setTimeout(resolve, 500));
          sendSafeCommand(terminal, 'claude --continue');
        } catch (err) {
          logger.error(`Failed to recover session for ${item.workspacePath}:`, err);
        }
      }

      crossWindowState.clearStaleSessions();
      vscode.window.showInformationMessage(`Recovered ${selected.length} Claude session(s)`);
    })
  );

  // Resume ALL recoverable sessions at once
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.resumeAll', async () => {
      logger.info('resumeAll command invoked');
      const recoverable = crossWindowState.getRecoverableSessions();
      logger.info(`Found ${recoverable.length} recoverable sessions`);

      if (recoverable.length === 0) {
        logger.info('No sessions to resume');
        vscode.window.showInformationMessage('No sessions to resume');
        return;
      }

      const uniquePaths = new Map<string, { workspacePath: string }>();
      for (const session of recoverable) {
        uniquePaths.set(session.workspacePath, session);
        logger.debug(`Session to recover: ${session.workspacePath}`);
      }

      const sessions = Array.from(uniquePaths.values());
      logger.info(`Unique sessions to recover: ${sessions.length}`);

      const action = await vscode.window.showInformationMessage(
        `Resume ${sessions.length} Claude session(s) from before crash?`,
        'Resume All',
        'Pick Sessions',
        'Dismiss'
      );

      logger.info(`User selected: ${action ?? 'Dismiss'}`);

      if (action === 'Resume All') {
        let successCount = 0;
        let failCount = 0;

        for (const session of sessions) {
          try {
            logger.info(`Attempting to resume session in: ${session.workspacePath}`);
            const terminal = createResumedTerminal(session.workspacePath);
            logger.debug(`Created terminal for ${session.workspacePath}`);
            await new Promise(resolve => setTimeout(resolve, 500));
            sendSafeCommand(terminal, 'claude --continue');
            logger.info(`Sent 'claude --continue' to terminal for ${session.workspacePath}`);
            successCount++;
          } catch (err) {
            failCount++;
            logger.error(`Failed to resume session for ${session.workspacePath}:`, err);
          }
        }

        logger.info(`Resume complete: ${successCount} succeeded, ${failCount} failed`);
        crossWindowState.clearStaleSessions();
        vscode.window.showInformationMessage(`Resumed ${successCount} Claude session(s)${failCount > 0 ? ` (${failCount} failed)` : ''}`);
      } else if (action === 'Pick Sessions') {
        vscode.commands.executeCommand('claude-tracker.recoverSessions');
      } else {
        logger.info('User dismissed, clearing stale sessions');
        crossWindowState.clearStaleSessions();
      }
    })
  );

  // Resume last session - supports multi-root workspaces
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.resumeLast', async () => {
      const resumableWorkspaces = getAllWorkspacePaths()
        .filter(path => storage.getResumableForProject(path));

      let targetWorkspace: string | undefined;

      if (resumableWorkspaces.length === 0) {
        targetWorkspace = getCurrentWorkspacePath();
        if (!targetWorkspace) {
          vscode.window.showWarningMessage('No workspace folder open');
          return;
        }
      } else if (resumableWorkspaces.length === 1) {
        targetWorkspace = resumableWorkspaces[0];
      } else {
        const items = resumableWorkspaces.map(workspacePath => ({
          label: path.basename(workspacePath),
          description: workspacePath,
          workspacePath,
        }));

        const selected = await vscode.window.showQuickPick(items, {
          placeHolder: 'Select workspace to resume Claude session',
        });

        if (!selected) return;
        targetWorkspace = selected.workspacePath;
      }

      try {
        const terminal = createResumedTerminal(targetWorkspace);
        sendSafeCommand(terminal, 'claude --continue');
        await storage.clearResumable(targetWorkspace);
      } catch (err) {
        logger.error('Failed to resume Claude session:', err);
        vscode.window.showErrorMessage(`Failed to resume Claude session: ${err}`);
      }
    })
  );

  // Pick from recent sessions
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.pickSession', async () => {
      const cwd = getCurrentWorkspacePath();
      if (!cwd) {
        vscode.window.showWarningMessage('No workspace folder open');
        return;
      }

      const sessions = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Loading Claude sessions...',
          cancellable: false,
        },
        () => loadEnrichedSessionsForProject(cwd)
      );

      if (sessions.length === 0) {
        vscode.window.showInformationMessage('No Claude sessions found for this workspace');
        return;
      }

      const showEnriched = shouldShowEnrichedData();
      const items = sessions.map(s => {
        const descParts: string[] = [];
        if (showEnriched && s.model) descParts.push(s.model);
        if (showEnriched && s.numTurns) descParts.push(`${s.numTurns} turns`);
        if (!descParts.length) {
          descParts.push(s.gitBranch ? `$(git-branch) ${s.gitBranch}` : '$(circle-slash) No branch');
        }

        const detailParts = [formatRelativeTime(s.modified)];
        if (s.gitBranch && showEnriched) detailParts.push(s.gitBranch);
        if (showEnriched && s.totalCostUsd) detailParts.push(formatCost(s.totalCostUsd));

        return {
          label: truncate(s.displayTitle, 60),
          description: descParts.join(' \u00b7 '),
          detail: detailParts.join(' \u00b7 '),
          sessionId: s.id,
        };
      });

      const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Select a session to resume',
        matchOnDescription: true,
        matchOnDetail: true,
      });

      if (selected) {
        try {
          const terminal = createResumedTerminal(cwd);
          sendSafeCommand(terminal, 'claude --resume', selected.sessionId);
        } catch (err) {
          logger.error('Failed to resume session:', err);
          vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
        }
      }
    })
  );

  // Show recent sessions - alias for pickSession
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.showSessions', () => {
      vscode.commands.executeCommand('claude-tracker.pickSession');
    })
  );

  // Resume specific session (used by Session Browser TreeView)
  context.subscriptions.push(
    vscode.commands.registerCommand(
      'claude-tracker.resumeSession',
      async (sessionId: string, projectPath: string) => {
        try {
          const terminal = createResumedTerminal(projectPath);
          sendSafeCommand(terminal, 'claude --resume', sessionId);
        } catch (err) {
          logger.error('Failed to resume session:', err);
          vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
          throw err;
        }
      }
    )
  );
}

// === Session Loading via Index + Cache ===

/**
 * Load the session summaries cache
 */
async function loadSummaryCache(): Promise<Record<string, SessionSummaryCache>> {
  try {
    const content = await fs.promises.readFile(SESSION_SUMMARIES_PATH, 'utf-8');
    return JSON.parse(content);
  } catch {
    return {};
  }
}

/**
 * Decode a project directory name back to the original path.
 * Uses sessions-index.json projectPath as ground truth.
 */
function decodeProjectPath(projectDir: string): string {
  const encoded = path.basename(projectDir);
  return encoded.replace(/^-/, '/').replace(/-/g, '/');
}

/**
 * Build an EnrichedSession from index entry + summary cache
 */
function buildEnrichedSession(
  entry: SessionIndexEntry,
  projectPath: string,
  cache: Record<string, SessionSummaryCache>
): EnrichedSession {
  const cached = cache[entry.sessionId];
  const projectName = path.basename(projectPath);

  // Resolve display title: customTitle > cached title > firstPrompt
  let displayTitle = entry.customTitle || cached?.title || entry.summary || '';
  if (!displayTitle && entry.firstPrompt) {
    displayTitle = truncate(entry.firstPrompt, 60);
  }
  if (!displayTitle) {
    displayTitle = `Session ${entry.sessionId.substring(0, 8)}`;
  }

  // Model shortening
  const model = cached?.model ? shortenModelName(cached.model) : undefined;

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
export async function loadAllEnrichedSessions(): Promise<EnrichedSession[]> {
  try {
    await fs.promises.access(CLAUDE_PROJECTS_DIR);
  } catch {
    return [];
  }

  const cache = await loadSummaryCache();
  const hideSidechain = shouldHideSidechainSessions();
  const sessions: EnrichedSession[] = [];

  let projectDirs: string[];
  try {
    const entries = await fs.promises.readdir(CLAUDE_PROJECTS_DIR, { withFileTypes: true });
    projectDirs = entries.filter(e => e.isDirectory()).map(e => e.name);
  } catch {
    return [];
  }

  for (const dirName of projectDirs) {
    const indexPath = path.join(CLAUDE_PROJECTS_DIR, dirName, 'sessions-index.json');
    try {
      const content = await fs.promises.readFile(indexPath, 'utf-8');
      const index = JSON.parse(content);
      if (!index.entries || !Array.isArray(index.entries)) continue;

      // Use projectPath from first entry as ground truth, fall back to decode
      const projectPath = index.entries[0]?.projectPath || decodeProjectPath(dirName);

      for (const entry of index.entries as SessionIndexEntry[]) {
        const session = buildEnrichedSession(
          entry,
          entry.projectPath || projectPath,
          cache
        );
        if (hideSidechain && session.isSidechain) continue;
        sessions.push(session);
      }
    } catch {
      // No index or parse error — skip
    }
  }

  // Sort by modified timestamp descending
  sessions.sort((a, b) => {
    const ta = a.modified ? new Date(a.modified).getTime() : 0;
    const tb = b.modified ? new Date(b.modified).getTime() : 0;
    return tb - ta;
  });

  return sessions.slice(0, MAX_RECENT_SESSIONS * 2);
}

/**
 * Load enriched sessions for a specific project workspace
 */
async function loadEnrichedSessionsForProject(workspacePath: string): Promise<EnrichedSession[]> {
  const encodedPath = encodeWorkspacePath(workspacePath);
  const indexPath = path.join(CLAUDE_PROJECTS_DIR, encodedPath, 'sessions-index.json');

  try {
    await fs.promises.access(indexPath);
  } catch {
    return [];
  }

  const cache = await loadSummaryCache();
  const hideSidechain = shouldHideSidechainSessions();

  try {
    const content = await fs.promises.readFile(indexPath, 'utf-8');
    const index = JSON.parse(content);
    if (!index.entries || !Array.isArray(index.entries)) return [];

    const sessions: EnrichedSession[] = [];
    for (const entry of index.entries as SessionIndexEntry[]) {
      const session = buildEnrichedSession(entry, workspacePath, cache);
      if (hideSidechain && session.isSidechain) continue;
      sessions.push(session);
    }

    // Sort by modified descending
    sessions.sort((a, b) => {
      const ta = a.modified ? new Date(a.modified).getTime() : 0;
      const tb = b.modified ? new Date(b.modified).getTime() : 0;
      return tb - ta;
    });

    return sessions.slice(0, MAX_RECENT_SESSIONS);
  } catch {
    return [];
  }
}

/**
 * Load recent enriched sessions from last N hours (across all projects)
 */
async function loadRecentEnrichedSessions(hours: number): Promise<EnrichedSession[]> {
  const cutoffTime = Date.now() - (hours * 60 * 60 * 1000);
  const all = await loadAllEnrichedSessions();
  return all.filter(s => {
    const t = s.modified ? new Date(s.modified).getTime() : 0;
    return t > cutoffTime;
  }).slice(0, MAX_RECENT_SESSIONS);
}
