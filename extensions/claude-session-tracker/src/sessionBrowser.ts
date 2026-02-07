import * as vscode from 'vscode';
import * as path from 'path';
import type { SessionSummary } from './types';
import { formatRelativeTime, truncate } from './utils';

/**
 * TreeItem for session browser
 * Displays session info with click-to-resume functionality
 */
class SessionTreeItem extends vscode.TreeItem {
  constructor(public readonly session: SessionSummary) {
    super(truncate(session.firstMessage, 50), vscode.TreeItemCollapsibleState.None);

    const projectName = path.basename(session.projectPath);

    this.description = session.gitBranch
      ? `${session.gitBranch}`
      : projectName;

    this.tooltip = new vscode.MarkdownString(
      `**${projectName}**\n\n` +
        `${session.firstMessage.slice(0, 200)}${session.firstMessage.length > 200 ? '...' : ''}\n\n` +
        `---\n` +
        `$(folder) \`${session.projectPath}\`\n\n` +
        `$(clock) ${formatRelativeTime(session.timestamp)}` +
        (session.gitBranch ? `\n\n$(git-branch) ${session.gitBranch}` : '')
    );
    this.tooltip.supportThemeIcons = true;

    this.iconPath = new vscode.ThemeIcon('comment-discussion');

    // Click action - resume session
    this.command = {
      command: 'claude-tracker.resumeSession',
      title: 'Resume Session',
      arguments: [session.id, session.projectPath],
    };

    this.contextValue = 'claudeSession';
  }
}

/**
 * Session Browser TreeView Provider
 * Displays flat list of recent Claude sessions sorted by most recent
 */
export class SessionBrowserProvider implements vscode.TreeDataProvider<SessionTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<SessionTreeItem | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private sessions: SessionSummary[] = [];
  private loadId = 0; // Incremented on each refresh to invalidate stale loads

  constructor(private parseAllClaudeSessions: () => Promise<SessionSummary[]>) {}

  /**
   * Refresh the session list
   */
  refresh(): void {
    this.loadId++; // Invalidate any ongoing loads
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: SessionTreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: SessionTreeItem): Promise<SessionTreeItem[]> {
    // Flat list - no parent/child hierarchy
    if (element) {
      return [];
    }

    const currentLoadId = this.loadId;

    try {
      // Load sessions
      this.sessions = await this.parseAllClaudeSessions();

      // Check if refresh was called during load (stale data)
      if (currentLoadId !== this.loadId) {
        return []; // Discard stale load, new getChildren() will be called
      }

      // Transform to TreeItems
      return this.sessions.map((session) => new SessionTreeItem(session));
    } catch (err) {
      console.error('Failed to load Claude sessions:', err);
      return [];
    }
  }
}
