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
exports.SESSION_SUMMARIES_PATH = exports.CLAUDE_PROJECTS_DIR = exports.GIT_TIMEOUT_MS = exports.MAX_RECENT_SESSIONS = exports.TERMINAL_DETECTION_MAX_ATTEMPTS = exports.TERMINAL_DETECTION_DELAY_MS = void 0;
exports.getCurrentWorkspacePath = getCurrentWorkspacePath;
exports.encodeWorkspacePath = encodeWorkspacePath;
exports.getTerminalColor = getTerminalColor;
exports.getTerminalIcon = getTerminalIcon;
exports.formatTerminalName = formatTerminalName;
exports.createEnrichedTerminal = createEnrichedTerminal;
exports.createResumedTerminal = createResumedTerminal;
exports.sendSafeCommand = sendSafeCommand;
exports.getConfig = getConfig;
exports.shouldShowStatusBar = shouldShowStatusBar;
exports.isAutoResumeEnabled = isAutoResumeEnabled;
exports.truncate = truncate;
exports.formatRelativeTime = formatRelativeTime;
exports.sleep = sleep;
exports.getGitBranchRobust = getGitBranchRobust;
exports.getProcessCommand = getProcessCommand;
exports.isClaudeProcess = isClaudeProcess;
exports.getChildProcesses = getChildProcesses;
exports.getAllWorkspacePaths = getAllWorkspacePaths;
exports.getWorkspaceForPath = getWorkspaceForPath;
exports.getProcessCwd = getProcessCwd;
exports.shortenModelName = shortenModelName;
exports.formatCost = formatCost;
exports.shouldShowCostInStatusBar = shouldShowCostInStatusBar;
exports.shouldShowEnrichedData = shouldShowEnrichedData;
exports.shouldHideSidechainSessions = shouldHideSidechainSessions;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const os = __importStar(require("os"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
// === Constants ===
/** Delay between terminal name detection attempts */
exports.TERMINAL_DETECTION_DELAY_MS = 100;
/** Maximum attempts to detect terminal name */
exports.TERMINAL_DETECTION_MAX_ATTEMPTS = 10;
/** Maximum recent sessions to parse */
exports.MAX_RECENT_SESSIONS = 20;
/** Git command timeout in milliseconds */
exports.GIT_TIMEOUT_MS = 5000;
// === Workspace Utilities ===
/**
 * Get the current workspace folder path
 * Prioritizes active editor's workspace, falls back to first workspace
 */
function getCurrentWorkspacePath() {
    // Try to get workspace of active editor first (multi-root safe)
    if (vscode.window.activeTextEditor) {
        const workspace = vscode.workspace.getWorkspaceFolder(vscode.window.activeTextEditor.document.uri);
        if (workspace)
            return workspace.uri.fsPath;
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
function encodeWorkspacePath(workspacePath) {
    // Use path.sep for cross-platform compatibility
    // Replace both forward and back slashes for consistency
    return workspacePath.replace(/[/\\]/g, '-');
}
/**
 * Compute terminal tab color from session recency
 */
function getTerminalColor(ctx) {
    if (ctx?.isRecovery)
        return new vscode.ThemeColor('terminal.ansiRed');
    if (!ctx?.modified)
        return new vscode.ThemeColor('terminal.ansiCyan');
    const hours = (Date.now() - new Date(ctx.modified).getTime()) / 3600000;
    if (hours < 1)
        return new vscode.ThemeColor('terminal.ansiGreen');
    if (hours < 6)
        return new vscode.ThemeColor('terminal.ansiCyan');
    if (hours < 24)
        return new vscode.ThemeColor('terminal.ansiYellow');
    if (hours < 72)
        return new vscode.ThemeColor('terminal.ansiMagenta');
    return new vscode.ThemeColor('terminal.ansiBrightBlack');
}
/**
 * Compute terminal tab icon from model name
 */
function getTerminalIcon(ctx) {
    if (ctx?.isRecovery)
        return new vscode.ThemeIcon('warning');
    if (!ctx?.model)
        return new vscode.ThemeIcon('robot');
    const m = ctx.model.toLowerCase();
    if (m.includes('opus'))
        return new vscode.ThemeIcon('sparkle');
    if (m.includes('haiku'))
        return new vscode.ThemeIcon('zap');
    return new vscode.ThemeIcon('robot');
}
/**
 * Format enriched terminal name from session context
 * Terminal name doubles as hover tooltip in VS Code
 */
function formatTerminalName(ctx) {
    if (!ctx)
        return 'Claude Code (Resumed)';
    const parts = ['Claude'];
    if (ctx.isRecovery) {
        parts.push('Recovered');
    }
    else if (ctx.displayTitle) {
        parts.push(`"${truncate(ctx.displayTitle, 35)}"`);
    }
    if (ctx.model)
        parts.push(ctx.model);
    if (ctx.gitBranch)
        parts.push(ctx.gitBranch);
    if (ctx.totalCostUsd)
        parts.push(formatCost(ctx.totalCostUsd));
    if (ctx.modified)
        parts.push(formatRelativeTime(ctx.modified));
    return parts.join(' \u00b7 ');
}
/**
 * Create a terminal with enriched icon, color, and name
 */
function createEnrichedTerminal(cwd, ctx) {
    const terminal = vscode.window.createTerminal({
        name: formatTerminalName(ctx),
        cwd,
        iconPath: getTerminalIcon(ctx),
        color: getTerminalColor(ctx),
    });
    terminal.show();
    return terminal;
}
/**
 * Create a terminal for resuming Claude sessions
 * @deprecated Use createEnrichedTerminal() for enriched terminal tabs
 */
function createResumedTerminal(cwd) {
    return createEnrichedTerminal(cwd);
}
/**
 * Safely execute a command in terminal
 * Escapes quotes to prevent command injection
 */
function sendSafeCommand(terminal, command, ...args) {
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
function getConfig() {
    return vscode.workspace.getConfiguration('claudeTracker');
}
/**
 * Check if status bar should be shown
 */
function shouldShowStatusBar() {
    return getConfig().get('showStatusBar', true);
}
/**
 * Check if auto-resume is enabled
 */
function isAutoResumeEnabled() {
    return getConfig().get('autoResume', false);
}
// === String Utilities ===
/**
 * Truncate string with ellipsis
 */
function truncate(str, maxLength) {
    const cleaned = str.replace(/\n/g, ' ').trim();
    if (cleaned.length <= maxLength)
        return cleaned;
    return cleaned.substring(0, maxLength - 1) + '…';
}
/**
 * Format ISO date to human-readable relative time
 */
function formatRelativeTime(isoString) {
    try {
        const date = new Date(isoString);
        const diffMs = Date.now() - date.getTime();
        if (diffMs < 60000)
            return 'Just now';
        if (diffMs < 3600000)
            return `${Math.floor(diffMs / 60000)}m ago`;
        if (diffMs < 86400000)
            return `${Math.floor(diffMs / 3600000)}h ago`;
        if (diffMs < 604800000)
            return `${Math.floor(diffMs / 86400000)}d ago`;
        return date.toLocaleDateString();
    }
    catch {
        return isoString;
    }
}
// === Async Utilities ===
/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
/**
 * Get git branch with robust error handling
 * Handles detached HEAD, timeouts, and non-git directories
 */
async function getGitBranchRobust(cwd) {
    try {
        // Fast check: is this a git repo?
        try {
            await execAsync('git rev-parse --git-dir', { cwd, timeout: 1000 });
        }
        catch {
            return { branch: undefined, status: 'not-git-repo' };
        }
        // Get current branch
        const { stdout } = await execAsync('git branch --show-current', {
            cwd,
            timeout: exports.GIT_TIMEOUT_MS,
        });
        const branch = stdout.trim();
        // Empty means detached HEAD
        if (!branch) {
            try {
                const { stdout: sha } = await execAsync('git rev-parse --short HEAD', {
                    cwd,
                    timeout: exports.GIT_TIMEOUT_MS,
                });
                return { branch: `HEAD:${sha.trim()}`, status: 'detached' };
            }
            catch {
                return { branch: undefined, status: 'detached' };
            }
        }
        return { branch, status: 'success' };
    }
    catch (err) {
        const error = err;
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
function isValidPid(pid) {
    return Number.isInteger(pid) && pid > 0;
}
/**
 * Get process command line by PID (cross-platform)
 */
function getProcessCommand(pid) {
    if (!isValidPid(pid))
        return undefined;
    try {
        if (process.platform === 'darwin' || process.platform === 'linux') {
            const output = (0, child_process_1.execSync)(`ps -p ${pid} -o command=`, {
                timeout: 1000,
                encoding: 'utf8',
            });
            return output.trim();
        }
        else if (process.platform === 'win32') {
            const output = (0, child_process_1.execSync)(`wmic process where processid=${pid} get commandline`, { timeout: 1000, encoding: 'utf8' });
            return output.split('\n')[1]?.trim();
        }
    }
    catch {
        return undefined;
    }
    return undefined;
}
/**
 * Check if a command line indicates Claude Code process
 */
function isClaudeProcess(command) {
    if (!command)
        return false;
    const lower = command.toLowerCase();
    return lower.includes('claude') || lower.includes('@anthropic');
}
/**
 * Get child process PIDs of a parent process
 */
function getChildProcesses(parentPid) {
    if (!isValidPid(parentPid))
        return [];
    try {
        if (process.platform === 'darwin' || process.platform === 'linux') {
            const output = (0, child_process_1.execSync)(`pgrep -P ${parentPid}`, {
                encoding: 'utf8',
                timeout: 1000,
            });
            return output.trim().split('\n').map(Number).filter(Boolean);
        }
    }
    catch {
        // pgrep returns exit code 1 if no children found
        return [];
    }
    return [];
}
// === Multi-Root Workspace Utilities (Phase 3) ===
/**
 * Get all workspace folder paths
 */
function getAllWorkspacePaths() {
    return vscode.workspace.workspaceFolders?.map(f => f.uri.fsPath) ?? [];
}
/**
 * Get workspace folder containing a given path
 */
function getWorkspaceForPath(filePath) {
    const folder = vscode.workspace.getWorkspaceFolder(vscode.Uri.file(filePath));
    return folder?.uri.fsPath;
}
/**
 * Get process current working directory by PID (cross-platform)
 */
function getProcessCwd(pid) {
    if (!isValidPid(pid))
        return undefined;
    try {
        if (process.platform === 'darwin') {
            // macOS: use lsof to get cwd
            const output = (0, child_process_1.execSync)(`lsof -p ${pid} 2>/dev/null | grep cwd`, {
                encoding: 'utf8',
                timeout: 1000,
            });
            // Parse: "node    12345 user  cwd    DIR  1,4  ... /path/to/cwd"
            const match = output.match(/cwd\s+\S+\s+\S+\s+\S+\s+(.+)$/m);
            return match?.[1]?.trim();
        }
        else if (process.platform === 'linux') {
            // Linux: read /proc/{pid}/cwd symlink
            return fs.readlinkSync(`/proc/${pid}/cwd`);
        }
    }
    catch {
        return undefined;
    }
    return undefined;
}
// === Enrichment Utilities ===
/** Claude projects directory */
exports.CLAUDE_PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
/** Session summaries cache path */
exports.SESSION_SUMMARIES_PATH = path.join(os.homedir(), '.claude', 'session-summaries.json');
/**
 * Shorten Claude model ID for display
 */
function shortenModelName(model) {
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
function formatCost(cost) {
    if (cost < 0.01)
        return '<$0.01';
    return `$${cost.toFixed(2)}`;
}
/**
 * Check if cost should be shown in status bar
 */
function shouldShowCostInStatusBar() {
    return getConfig().get('showCostInStatusBar', true);
}
/**
 * Check if enriched data should be shown
 */
function shouldShowEnrichedData() {
    return getConfig().get('showEnrichedData', true);
}
/**
 * Check if sidechain sessions should be hidden
 */
function shouldHideSidechainSessions() {
    return getConfig().get('hideSidechainSessions', true);
}
//# sourceMappingURL=utils.js.map