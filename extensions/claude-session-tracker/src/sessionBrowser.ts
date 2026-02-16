import * as vscode from 'vscode';
import type { EnrichedSession } from './types';
import { formatRelativeTime, formatCost, truncate, shouldShowEnrichedData } from './utils';
import { logger } from './logger';

/**
 * TreeItem for session browser
 * Displays enriched session info with click-to-resume functionality
 */
class SessionTreeItem extends vscode.TreeItem {
  constructor(public readonly session: EnrichedSession) {
    super(truncate(session.displayTitle, 55), vscode.TreeItemCollapsibleState.None);

    const showEnriched = shouldShowEnrichedData();

    // Description: model + turns (or fallback to branch/project)
    const descParts: string[] = [];
    if (showEnriched && session.model) descParts.push(session.model);
    if (showEnriched && session.numTurns) descParts.push(`${session.numTurns} turns`);
    if (!descParts.length && session.gitBranch) descParts.push(session.gitBranch);
    if (!descParts.length) descParts.push(session.projectName);
    this.description = descParts.join(' \u00b7 ');

    // Rich tooltip with all available data
    const tooltipLines = [`**${session.projectName}**\n`];

    if (session.summary) {
      const summaryText = session.summary.length > 200
        ? session.summary.substring(0, 197) + '...'
        : session.summary;
      tooltipLines.push(summaryText + '\n');
    } else if (session.firstPrompt) {
      const promptText = session.firstPrompt.length > 200
        ? session.firstPrompt.substring(0, 197) + '...'
        : session.firstPrompt;
      tooltipLines.push(promptText + '\n');
    }

    tooltipLines.push('---');
    tooltipLines.push(`$(folder) \`${session.projectPath}\``);
    tooltipLines.push(`$(clock) ${formatRelativeTime(session.modified)}`);
    if (session.gitBranch) {
      tooltipLines.push(`$(git-branch) ${session.gitBranch}`);
    }
    if (showEnriched) {
      const metaParts: string[] = [];
      if (session.numTurns) metaParts.push(`${session.numTurns} turns`);
      if (session.totalCostUsd) metaParts.push(formatCost(session.totalCostUsd));
      if (metaParts.length) {
        tooltipLines.push(`$(symbol-number) ${metaParts.join(' \u00b7 ')}`);
      }
      if (session.model) {
        tooltipLines.push(`$(server) ${session.model}`);
      }
    }
    if (session.isWorktree) {
      tooltipLines.push(`$(git-compare) worktree`);
    }

    this.tooltip = new vscode.MarkdownString(tooltipLines.join('\n\n'));
    this.tooltip.supportThemeIcons = true;

    // Icon: worktree gets git-compare, normal gets comment-discussion
    this.iconPath = session.isWorktree
      ? new vscode.ThemeIcon('git-compare')
      : new vscode.ThemeIcon('comment-discussion');

    // Click action - resume session
    this.command = {
      command: 'claude-tracker.resumeSession',
      title: 'Resume Session',
      arguments: [session.id, session.projectPath, {
        displayTitle: session.displayTitle,
        model: session.model,
        gitBranch: session.gitBranch,
        numTurns: session.numTurns,
        totalCostUsd: session.totalCostUsd,
        modified: session.modified,
      }],
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

  private sessions: EnrichedSession[] = [];
  private loadId = 0;

  constructor(private loadSessions: () => Promise<EnrichedSession[]>) {}

  refresh(): void {
    this.loadId++;
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: SessionTreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: SessionTreeItem): Promise<SessionTreeItem[]> {
    if (element) {
      return [];
    }

    const currentLoadId = this.loadId;

    try {
      const sessions = await this.loadSessions();

      // Don't update cache if a newer load was triggered while we waited
      if (currentLoadId !== this.loadId) {
        return [];
      }

      this.sessions = sessions;
      return this.sessions.map((session) => new SessionTreeItem(session));
    } catch (err) {
      logger.error('Failed to load Claude sessions:', err);
      return [];
    }
  }
}
