import * as vscode from 'vscode';
import { shouldShowStatusBar, shouldShowCostInStatusBar, formatCost } from './utils';

/**
 * Manages the status bar indicator for Claude sessions
 */
export class StatusBarManager {
  private statusBarItem: vscode.StatusBarItem;
  private currentState: 'active' | 'resumable' | 'recoverable' | 'hidden' = 'hidden';

  constructor(context: vscode.ExtensionContext) {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      100
    );
    // Default command - will be updated based on state
    this.statusBarItem.command = 'claude-tracker.pickSession';
    context.subscriptions.push(this.statusBarItem);
  }

  /**
   * Show status for active Claude session(s)
   * @param globalCount Total terminals across all VS Code windows
   * @param localCount Terminals in this window only (optional)
   * @param totalCost Total session cost in USD (optional, from summary cache)
   */
  showActive(globalCount: number, localCount?: number, totalCost?: number): void {
    if (!shouldShowStatusBar()) {
      this.hide();
      return;
    }

    this.currentState = 'active';

    // Build status text with optional cost
    let text: string;
    if (globalCount === 1) {
      text = '$(terminal) Claude Active';
    } else {
      text = `$(terminal) Claude Active (${globalCount})`;
    }

    // Append cost if available and enabled
    if (totalCost && totalCost > 0 && shouldShowCostInStatusBar()) {
      text += ` \u00b7 ${formatCost(totalCost)}`;
    }

    this.statusBarItem.text = text;

    // Build informative tooltip
    if (localCount !== undefined && localCount !== globalCount) {
      const otherCount = globalCount - localCount;
      this.statusBarItem.tooltip = `${localCount} in this window, ${otherCount} in other window(s)\nClick to view all sessions`;
    } else {
      this.statusBarItem.tooltip = 'Click to view Claude sessions';
    }

    // Use session picker instead of direct focus to prevent accidental commands
    this.statusBarItem.command = 'claude-tracker.showAllTerminals';
    this.statusBarItem.backgroundColor = undefined;
    this.statusBarItem.show();
  }

  /**
   * Show status for resumable session
   */
  showResumable(): void {
    if (!shouldShowStatusBar()) {
      this.hide();
      return;
    }

    this.currentState = 'resumable';
    this.statusBarItem.text = '$(debug-restart) Resume Claude';
    this.statusBarItem.tooltip = 'Click to pick a session to resume (Cmd+Shift+C)';
    this.statusBarItem.command = 'claude-tracker.pickSession';
    this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    this.statusBarItem.show();
  }

  /**
   * Show status for crash-recoverable sessions
   */
  showRecoverable(count: number): void {
    if (!shouldShowStatusBar()) {
      this.hide();
      return;
    }

    this.currentState = 'recoverable';
    this.statusBarItem.text = `$(warning) Recover Claude (${count})`;
    this.statusBarItem.tooltip = `${count} Claude session(s) can be recovered from crash\nClick to recover`;
    this.statusBarItem.command = 'claude-tracker.resumeAll';
    this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    this.statusBarItem.show();
  }

  /**
   * Hide the status bar item
   */
  hide(): void {
    this.currentState = 'hidden';
    this.statusBarItem.hide();
  }

  /**
   * Get current state
   */
  getState(): 'active' | 'resumable' | 'recoverable' | 'hidden' {
    return this.currentState;
  }

  /**
   * Dispose the status bar item
   */
  dispose(): void {
    this.statusBarItem.dispose();
  }
}
