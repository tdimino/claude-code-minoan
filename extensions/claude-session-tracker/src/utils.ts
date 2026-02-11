import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { exec, execSync } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// === Constants ===

/** Delay between terminal name detection attempts */
export const TERMINAL_DETECTION_DELAY_MS = 100;

/** Maximum attempts to detect terminal name */
export const TERMINAL_DETECTION_MAX_ATTEMPTS = 10;

/** Maximum recent sessions to parse */
export const MAX_RECENT_SESSIONS = 20;

/** Git command timeout in milliseconds */
export const GIT_TIMEOUT_MS = 5000;

// === Workspace Utilities ===

/**
 * Get the current workspace folder path
 * Prioritizes active editor's workspace, falls back to first workspace
 */
export function getCurrentWorkspacePath(): string | undefined {
  // Try to get workspace of active editor first (multi-root safe)
  if (vscode.window.activeTextEditor) {
    const workspace = vscode.workspace.getWorkspaceFolder(
      vscode.window.activeTextEditor.document.uri
    );
    if (workspace) return workspace.uri.fsPath;
  }

  // Fallback: return first workspace (single-root or no editor open)
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

/**
 * Encode a workspace path the way Claude does
 * Claude replaces path separators with hyphens
 * Example: /Users/tom/project -> -Users-tom-project
 * Example: C:\Users\tom\project -> C--Users-tom-project
 */
export function encodeWorkspacePath(workspacePath: string): string {
  // Use path.sep for cross-platform compatibility
  // Replace both forward and back slashes for consistency
  return workspacePath.replace(/[/\\]/g, '-');
}

// === Terminal Utilities ===

/**
 * Create a terminal for resuming Claude sessions
 */
export function createResumedTerminal(cwd: string): vscode.Terminal {
  const terminal = vscode.window.createTerminal({
    name: 'Claude Code (Resumed)',
    cwd,
  });
  terminal.show();
  return terminal;
}

/**
 * Safely execute a command in terminal
 * Escapes quotes to prevent command injection
 */
export function sendSafeCommand(terminal: vscode.Terminal, command: string, ...args: string[]): void {
  const safeArgs = args.map(arg => {
    // Escape double quotes and wrap in quotes
    const escaped = arg.replace(/"/g, '\\"');
    return `"${escaped}"`;
  });

  const fullCommand = safeArgs.length > 0
    ? `${command} ${safeArgs.join(' ')}`
    : command;

  terminal.sendText(fullCommand);
}

// === Configuration Utilities ===

/**
 * Get Claude Tracker configuration
 */
export function getConfig(): vscode.WorkspaceConfiguration {
  return vscode.workspace.getConfiguration('claudeTracker');
}

/**
 * Check if status bar should be shown
 */
export function shouldShowStatusBar(): boolean {
  return getConfig().get('showStatusBar', true);
}

/**
 * Check if auto-resume is enabled
 */
export function isAutoResumeEnabled(): boolean {
  return getConfig().get('autoResume', false);
}

// === String Utilities ===

/**
 * Truncate string with ellipsis
 */
export function truncate(str: string, maxLength: number): string {
  const cleaned = str.replace(/\n/g, ' ').trim();
  if (cleaned.length <= maxLength) return cleaned;
  return cleaned.substring(0, maxLength - 1) + '…';
}

/**
 * Format ISO date to human-readable relative time
 */
export function formatRelativeTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    const diffMs = Date.now() - date.getTime();

    if (diffMs < 60000) return 'Just now';
    if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`;
    if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)}h ago`;
    if (diffMs < 604800000) return `${Math.floor(diffMs / 86400000)}d ago`;

    return date.toLocaleDateString();
  } catch {
    return isoString;
  }
}

// === Async Utilities ===

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// === Git Branch Utilities (Phase 1) ===

/**
 * Result of git branch detection with status information
 */
export interface GitBranchResult {
  branch: string | undefined;
  status: 'success' | 'not-git-repo' | 'timeout' | 'error' | 'detached';
  error?: string;
}

/**
 * Get git branch with robust error handling
 * Handles detached HEAD, timeouts, and non-git directories
 */
export async function getGitBranchRobust(cwd: string): Promise<GitBranchResult> {
  try {
    // Fast check: is this a git repo?
    try {
      await execAsync('git rev-parse --git-dir', { cwd, timeout: 1000 });
    } catch {
      return { branch: undefined, status: 'not-git-repo' };
    }

    // Get current branch
    const { stdout } = await execAsync('git branch --show-current', {
      cwd,
      timeout: GIT_TIMEOUT_MS,
    });

    const branch = stdout.trim();

    // Empty means detached HEAD
    if (!branch) {
      try {
        const { stdout: sha } = await execAsync('git rev-parse --short HEAD', {
          cwd,
          timeout: GIT_TIMEOUT_MS,
        });
        return { branch: `HEAD:${sha.trim()}`, status: 'detached' };
      } catch {
        return { branch: undefined, status: 'detached' };
      }
    }

    return { branch, status: 'success' };

  } catch (err: unknown) {
    const error = err as { killed?: boolean; message?: string };
    if (error.killed) {
      return { branch: undefined, status: 'timeout', error: 'Git command timed out' };
    }
    return { branch: undefined, status: 'error', error: error.message };
  }
}

// === Process Detection Utilities (Phase 2) ===

/**
 * Validate PID is a positive integer to prevent command injection
 */
function isValidPid(pid: number): boolean {
  return Number.isInteger(pid) && pid > 0;
}

/**
 * Get process command line by PID (cross-platform)
 */
export function getProcessCommand(pid: number): string | undefined {
  if (!isValidPid(pid)) return undefined;

  try {
    if (process.platform === 'darwin' || process.platform === 'linux') {
      const output = execSync(`ps -p ${pid} -o command=`, {
        timeout: 1000,
        encoding: 'utf8',
      });
      return output.trim();
    } else if (process.platform === 'win32') {
      const output = execSync(
        `wmic process where processid=${pid} get commandline`,
        { timeout: 1000, encoding: 'utf8' }
      );
      return output.split('\n')[1]?.trim();
    }
  } catch {
    return undefined;
  }
  return undefined;
}

/**
 * Check if a command line indicates Claude Code process
 */
export function isClaudeProcess(command: string | undefined): boolean {
  if (!command) return false;
  const lower = command.toLowerCase();
  return lower.includes('claude') || lower.includes('@anthropic');
}

/**
 * Get child process PIDs of a parent process
 */
export function getChildProcesses(parentPid: number): number[] {
  if (!isValidPid(parentPid)) return [];

  try {
    if (process.platform === 'darwin' || process.platform === 'linux') {
      const output = execSync(`pgrep -P ${parentPid}`, {
        encoding: 'utf8',
        timeout: 1000,
      });
      return output.trim().split('\n').map(Number).filter(Boolean);
    }
  } catch {
    // pgrep returns exit code 1 if no children found
    return [];
  }
  return [];
}

// === Multi-Root Workspace Utilities (Phase 3) ===

/**
 * Get all workspace folder paths
 */
export function getAllWorkspacePaths(): string[] {
  return vscode.workspace.workspaceFolders?.map(f => f.uri.fsPath) ?? [];
}

/**
 * Get workspace folder containing a given path
 */
export function getWorkspaceForPath(filePath: string): string | undefined {
  const folder = vscode.workspace.getWorkspaceFolder(vscode.Uri.file(filePath));
  return folder?.uri.fsPath;
}

/**
 * Get process current working directory by PID (cross-platform)
 */
export function getProcessCwd(pid: number): string | undefined {
  if (!isValidPid(pid)) return undefined;

  try {
    if (process.platform === 'darwin') {
      // macOS: use lsof to get cwd
      const output = execSync(`lsof -p ${pid} 2>/dev/null | grep cwd`, {
        encoding: 'utf8',
        timeout: 1000,
      });
      // Parse: "node    12345 user  cwd    DIR  1,4  ... /path/to/cwd"
      const match = output.match(/cwd\s+\S+\s+\S+\s+\S+\s+(.+)$/m);
      return match?.[1]?.trim();
    } else if (process.platform === 'linux') {
      // Linux: read /proc/{pid}/cwd symlink
      return fs.readlinkSync(`/proc/${pid}/cwd`);
    }
  } catch {
    return undefined;
  }
  return undefined;
}

// === Enrichment Utilities ===

/** Claude projects directory */
export const CLAUDE_PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');

/** Session summaries cache path */
export const SESSION_SUMMARIES_PATH = path.join(os.homedir(), '.claude', 'session-summaries.json');

/**
 * Shorten Claude model ID for display
 */
export function shortenModelName(model: string): string {
  return model
    .replace('claude-opus-4-6', 'opus-4.6')
    .replace('claude-opus-4-5-20251101', 'opus-4.5')
    .replace('claude-sonnet-4-5-20250929', 'sonnet-4.5')
    .replace('claude-haiku-4-5-20251001', 'haiku-4.5')
    .replace(/^claude-/, '');
}

/**
 * Format USD cost for display
 */
export function formatCost(cost: number): string {
  if (cost < 0.01) return '<$0.01';
  return `$${cost.toFixed(2)}`;
}

/**
 * Check if cost should be shown in status bar
 */
export function shouldShowCostInStatusBar(): boolean {
  return getConfig().get('showCostInStatusBar', true);
}

/**
 * Check if enriched data should be shown
 */
export function shouldShowEnrichedData(): boolean {
  return getConfig().get('showEnrichedData', true);
}

/**
 * Check if sidechain sessions should be hidden
 */
export function shouldHideSidechainSessions(): boolean {
  return getConfig().get('hideSidechainSessions', true);
}
