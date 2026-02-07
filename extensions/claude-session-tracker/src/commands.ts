import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as readline from 'readline';
import { SessionStorage } from './sessionStorage';
import { TerminalWatcher } from './terminalWatcher';
import { CrossWindowStateManager } from './crossWindowState';
import type { SessionSummary, ClaudeSessionFile } from './types';
import {
  getCurrentWorkspacePath,
  getAllWorkspacePaths,
  createResumedTerminal,
  sendSafeCommand,
  encodeWorkspacePath,
  truncate,
  formatRelativeTime,
  MAX_RECENT_SESSIONS,
  MAX_LINES_FOR_SUMMARY,
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
        // Single terminal - focus it directly
        activeTerminals[0].show();
        return;
      }

      // Multiple terminals - show picker
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

      // Get recent sessions from last 12 hours
      const recentSessions = await getRecentResumableSessions(12);

      // Build unified quick pick items
      interface SessionPickerItem extends vscode.QuickPickItem {
        type: 'active' | 'resumable';
        terminal?: vscode.Terminal;
        sessionId?: string;
        workspacePath?: string;
      }

      const items: SessionPickerItem[] = [];

      // Active terminals first (grouped at top)
      if (claudeTerminals.length > 0) {
        // Add separator label for active terminals
        for (const terminal of claudeTerminals) {
          items.push({
            type: 'active',
            label: `$(terminal-tmux) ${terminal.name}`,
            description: '$(circle-filled) Active',
            detail: 'Click to focus this terminal',
            terminal,
          });
        }
      }

      // Resumable sessions from last 12 hours
      for (const session of recentSessions) {
        const projectName = path.basename(session.projectPath);
        const age = formatRelativeTime(session.timestamp);
        items.push({
          type: 'resumable',
          label: `$(debug-restart) ${truncate(session.firstMessage, 50)}`,
          description: session.gitBranch
            ? `$(git-branch) ${session.gitBranch}`
            : `$(folder) ${projectName}`,
          detail: `${session.projectPath} • ${age}`,
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
        // Focus the active terminal
        selected.terminal.show();
      } else if (selected.type === 'resumable' && selected.workspacePath && selected.sessionId) {
        // Resume the selected session in its workspace
        try {
          const terminal = createResumedTerminal(selected.workspacePath);
          sendSafeCommand(terminal, 'claude --resume', selected.sessionId);
        } catch (err) {
          console.error('Failed to resume session:', err);
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
        () => parseAllClaudeSessions()
      );

      if (sessions.length === 0) {
        vscode.window.showInformationMessage('No Claude sessions found');
        return;
      }

      // Group by project for better readability
      const items = sessions.map(s => ({
        label: truncate(s.firstMessage, 60),
        description: `$(folder) ${path.basename(s.projectPath)}`,
        detail: `${s.gitBranch ? `$(git-branch) ${s.gitBranch} · ` : ''}${formatRelativeTime(s.timestamp)}`,
        sessionId: s.id,
        projectPath: s.projectPath,
      }));

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
          console.error('Failed to resume session:', err);
          vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
        }
      }
    })
  );

  // Recover sessions from crash - shows sessions that were active before VS Code crashed
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.recoverSessions', async () => {
      const recoverable = crossWindowState.getRecoverableSessions();

      if (recoverable.length === 0) {
        vscode.window.showInformationMessage('No sessions to recover');
        return;
      }

      // Deduplicate by workspacePath (same project may have been in multiple windows)
      const uniquePaths = new Map<string, { name: string; workspacePath: string; lastUpdate: number }>();
      for (const session of recoverable) {
        if (!uniquePaths.has(session.workspacePath) ||
            uniquePaths.get(session.workspacePath)!.lastUpdate < session.lastUpdate) {
          uniquePaths.set(session.workspacePath, session);
        }
      }

      const sessions = Array.from(uniquePaths.values());

      // Show quick pick with multi-select
      const items = sessions.map(s => ({
        label: `$(folder) ${path.basename(s.workspacePath)}`,
        description: s.name,
        detail: `Last active: ${formatRelativeTime(new Date(s.lastUpdate).toISOString())}`,
        workspacePath: s.workspacePath,
        picked: true, // Pre-select all by default
      }));

      const selected = await vscode.window.showQuickPick(items, {
        placeHolder: `${sessions.length} session(s) to recover from crash`,
        canPickMany: true,
      });

      if (!selected || selected.length === 0) {
        // User cancelled or selected nothing - clear stale sessions
        crossWindowState.clearStaleSessions();
        return;
      }

      // Resume each selected session
      for (const item of selected) {
        try {
          const terminal = createResumedTerminal(item.workspacePath);
          // Use small delay between terminals to avoid overwhelming the system
          await new Promise(resolve => setTimeout(resolve, 500));
          sendSafeCommand(terminal, 'claude --continue');
        } catch (err) {
          console.error(`Failed to recover session for ${item.workspacePath}:`, err);
        }
      }

      // Clear stale sessions after recovery attempt
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

      // Deduplicate by workspacePath
      const uniquePaths = new Map<string, { workspacePath: string }>();
      for (const session of recoverable) {
        uniquePaths.set(session.workspacePath, session);
        logger.debug(`Session to recover: ${session.workspacePath}`);
      }

      const sessions = Array.from(uniquePaths.values());
      logger.info(`Unique sessions to recover: ${sessions.length}`);

      // Confirm with user
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
        // Dismiss - clear stale sessions
        logger.info('User dismissed, clearing stale sessions');
        crossWindowState.clearStaleSessions();
      }
    })
  );

  // Resume last session - supports multi-root workspaces
  context.subscriptions.push(
    vscode.commands.registerCommand('claude-tracker.resumeLast', async () => {
      // Find all workspaces with resumable sessions
      const resumableWorkspaces = getAllWorkspacePaths()
        .filter(path => storage.getResumableForProject(path));

      let targetWorkspace: string | undefined;

      if (resumableWorkspaces.length === 0) {
        // No resumable sessions in any workspace, use first workspace
        targetWorkspace = getCurrentWorkspacePath();
        if (!targetWorkspace) {
          vscode.window.showWarningMessage('No workspace folder open');
          return;
        }
      } else if (resumableWorkspaces.length === 1) {
        // Single resumable workspace - use it directly
        targetWorkspace = resumableWorkspaces[0];
      } else {
        // Multiple workspaces have resumable sessions - show picker
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

        // Only clear resumable status after successful terminal creation
        await storage.clearResumable(targetWorkspace);
      } catch (err) {
        console.error('Failed to resume Claude session:', err);
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

      // Show loading
      const sessions = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Loading Claude sessions...',
          cancellable: false,
        },
        () => parseClaudeSessions(cwd)
      );

      if (sessions.length === 0) {
        vscode.window.showInformationMessage('No Claude sessions found for this workspace');
        return;
      }

      // Create quick pick items
      const items = sessions.map(s => ({
        label: truncate(s.firstMessage, 60),
        description: s.gitBranch
          ? `$(git-branch) ${s.gitBranch}`
          : '$(circle-slash) No branch',
        detail: formatRelativeTime(s.timestamp),
        sessionId: s.id,
      }));

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
          console.error('Failed to resume session:', err);
          vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
        }
      }
    })
  );

  // Show recent sessions - alias for pickSession
  // Note: Could be extended to show a read-only list view in future
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
          console.error('Failed to resume session:', err);
          vscode.window.showErrorMessage(`Failed to resume session: ${err}`);
          throw err; // Propagate so VS Code knows command failed
        }
      }
    )
  );
}

/**
 * Parse Claude session files for current workspace
 * Uses async file operations to avoid blocking the extension host
 */
async function parseClaudeSessions(workspacePath: string): Promise<SessionSummary[]> {
  const claudeDir = path.join(os.homedir(), '.claude', 'projects');

  // Encode the workspace path the way Claude does
  // Claude replaces path separators with hyphens
  const encodedPath = encodeWorkspacePath(workspacePath);
  const projectDir = path.join(claudeDir, encodedPath);

  // Check if directory exists (async)
  try {
    await fs.promises.access(projectDir);
  } catch {
    return [];
  }

  let files: { name: string; path: string; stat: fs.Stats }[];

  try {
    // Read directory async
    const dirEntries = await fs.promises.readdir(projectDir);
    const jsonlFiles = dirEntries.filter(f => f.endsWith('.jsonl'));

    // Stat all files in parallel
    const fileStats = await Promise.all(
      jsonlFiles.map(async (f) => {
        const filePath = path.join(projectDir, f);
        try {
          const stat = await fs.promises.stat(filePath);
          return { name: f, path: filePath, stat };
        } catch {
          return null; // File may have been deleted
        }
      })
    );

    files = fileStats
      .filter((f): f is { name: string; path: string; stat: fs.Stats } => f !== null && f.stat.size > 0)
      .sort((a, b) => b.stat.mtime.getTime() - a.stat.mtime.getTime())
      .slice(0, MAX_RECENT_SESSIONS);
  } catch (err) {
    console.error('Failed to read sessions directory:', err);
    return [];
  }

  const sessions: SessionSummary[] = [];

  for (const file of files) {
    try {
      const summary = await parseSessionFile(file.path);
      if (summary) {
        sessions.push(summary);
      }
    } catch (err) {
      // Skip corrupt files but log for debugging
      console.warn(`Failed to parse session file ${file.path}:`, err);
    }
  }

  return sessions;
}

/**
 * Parse a single session file to extract summary
 * Properly handles stream cleanup to prevent file handle leaks
 */
async function parseSessionFile(filePath: string): Promise<SessionSummary | null> {
  return new Promise((resolve) => {
    const sessionId = path.basename(filePath, '.jsonl');
    let firstUserMessage = '';
    let timestamp = '';
    let gitBranch: string | undefined;

    // Store stream reference for proper cleanup
    const stream = fs.createReadStream(filePath);
    const rl = readline.createInterface({
      input: stream,
      crlfDelay: Infinity,
    });

    let lineCount = 0;

    const cleanup = () => {
      rl.close();
      stream.destroy(); // Explicitly destroy stream to prevent leaks
    };

    rl.on('line', (line) => {
      lineCount++;

      // Only parse first N lines to find metadata
      if (lineCount > MAX_LINES_FOR_SUMMARY) {
        cleanup();
        return;
      }

      try {
        const data = JSON.parse(line) as Partial<ClaudeSessionFile>;

        if (!timestamp && data.timestamp) {
          timestamp = data.timestamp;
        }

        if (!gitBranch && data.gitBranch) {
          gitBranch = data.gitBranch;
        }

        if (!firstUserMessage && data.type === 'user' && data.message?.content) {
          // Extract just the actual user message, not system prompts
          const content = data.message.content;
          // Filter out memory agent observations
          if (!content.includes('<observed_from_primary_session>') &&
              !content.includes('MEMORY PROCESSING') &&
              content.length < 500) { // Skip very long system messages
            firstUserMessage = content;
          }
        }
      } catch {
        // Skip malformed JSON lines
      }
    });

    rl.on('close', () => {
      stream.destroy(); // Ensure stream is destroyed
      if (timestamp && firstUserMessage) {
        resolve({
          id: sessionId,
          projectPath: filePath,
          firstMessage: firstUserMessage,
          timestamp,
          gitBranch,
        });
      } else {
        resolve(null);
      }
    });

    rl.on('error', (err) => {
      console.warn(`Error reading session file ${filePath}:`, err);
      cleanup();
      resolve(null);
    });

    stream.on('error', (err) => {
      console.warn(`Stream error for ${filePath}:`, err);
      cleanup();
      resolve(null);
    });
  });
}

/**
 * Parse Claude sessions from ALL projects
 * Returns the most recent sessions across all project directories
 */
export async function parseAllClaudeSessions(): Promise<SessionSummary[]> {
  const claudeDir = path.join(os.homedir(), '.claude', 'projects');

  // Check if projects directory exists
  try {
    await fs.promises.access(claudeDir);
  } catch {
    return [];
  }

  let projectDirs: string[];
  try {
    const entries = await fs.promises.readdir(claudeDir, { withFileTypes: true });
    projectDirs = entries
      .filter(e => e.isDirectory())
      .map(e => path.join(claudeDir, e.name));
  } catch {
    return [];
  }

  // Collect all session files from all projects
  const allFiles: { name: string; path: string; stat: fs.Stats; projectDir: string }[] = [];

  await Promise.all(
    projectDirs.map(async (projectDir) => {
      try {
        const dirEntries = await fs.promises.readdir(projectDir);
        const jsonlFiles = dirEntries.filter(f => f.endsWith('.jsonl'));

        await Promise.all(
          jsonlFiles.map(async (f) => {
            const filePath = path.join(projectDir, f);
            try {
              const stat = await fs.promises.stat(filePath);
              if (stat.size > 0) {
                allFiles.push({ name: f, path: filePath, stat, projectDir });
              }
            } catch {
              // File may have been deleted
            }
          })
        );
      } catch {
        // Skip inaccessible project directories
      }
    })
  );

  // Sort by modification time and take most recent
  const sortedFiles = allFiles
    .sort((a, b) => b.stat.mtime.getTime() - a.stat.mtime.getTime())
    .slice(0, MAX_RECENT_SESSIONS * 2); // Get more since we're across all projects

  const sessions: SessionSummary[] = [];

  for (const file of sortedFiles) {
    try {
      const summary = await parseSessionFile(file.path);
      if (summary) {
        sessions.push({
          ...summary,
          projectPath: decodeProjectPath(file.projectDir),
        });
      }
    } catch (err) {
      console.warn(`Failed to parse session file ${file.path}:`, err);
    }
  }

  return sessions;
}

/**
 * Decode a project directory name back to the original path
 */
function decodeProjectPath(projectDir: string): string {
  // Claude encodes paths by replacing separators with hyphens
  // e.g., "-Users-tomdimino-Desktop-Project" -> "/Users/tomdimino/Desktop/Project"
  const encoded = path.basename(projectDir);
  // Replace leading hyphen with / and all other hyphens with /
  return encoded.replace(/^-/, '/').replace(/-/g, '/');
}

/**
 * Get resumable sessions from the last N hours
 * Filters by JSONL file modification time for accuracy
 */
async function getRecentResumableSessions(hours: number): Promise<SessionSummary[]> {
  const claudeDir = path.join(os.homedir(), '.claude', 'projects');
  const cutoffTime = Date.now() - (hours * 60 * 60 * 1000);

  // Check if projects directory exists
  try {
    await fs.promises.access(claudeDir);
  } catch {
    return [];
  }

  let projectDirs: string[];
  try {
    const entries = await fs.promises.readdir(claudeDir, { withFileTypes: true });
    projectDirs = entries
      .filter(e => e.isDirectory())
      .map(e => path.join(claudeDir, e.name));
  } catch {
    return [];
  }

  // Collect all session files from all projects, filtering by modification time
  const recentFiles: { name: string; path: string; stat: fs.Stats; projectDir: string }[] = [];

  await Promise.all(
    projectDirs.map(async (projectDir) => {
      try {
        const dirEntries = await fs.promises.readdir(projectDir);
        const jsonlFiles = dirEntries.filter(f => f.endsWith('.jsonl'));

        await Promise.all(
          jsonlFiles.map(async (f) => {
            const filePath = path.join(projectDir, f);
            try {
              const stat = await fs.promises.stat(filePath);
              // Filter by modification time (last N hours)
              if (stat.size > 0 && stat.mtime.getTime() > cutoffTime) {
                recentFiles.push({ name: f, path: filePath, stat, projectDir });
              }
            } catch {
              // File may have been deleted
            }
          })
        );
      } catch {
        // Skip inaccessible project directories
      }
    })
  );

  // Sort by modification time (most recent first)
  const sortedFiles = recentFiles
    .sort((a, b) => b.stat.mtime.getTime() - a.stat.mtime.getTime())
    .slice(0, MAX_RECENT_SESSIONS);

  const sessions: SessionSummary[] = [];

  for (const file of sortedFiles) {
    try {
      const summary = await parseSessionFile(file.path);
      if (summary) {
        sessions.push({
          ...summary,
          projectPath: decodeProjectPath(file.projectDir),
        });
      }
    } catch (err) {
      console.warn(`Failed to parse session file ${file.path}:`, err);
    }
  }

  return sessions;
}
