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
exports.SessionBrowserProvider = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const utils_1 = require("./utils");
/**
 * TreeItem for session browser
 * Displays session info with click-to-resume functionality
 */
class SessionTreeItem extends vscode.TreeItem {
    constructor(session) {
        super((0, utils_1.truncate)(session.firstMessage, 50), vscode.TreeItemCollapsibleState.None);
        this.session = session;
        const projectName = path.basename(session.projectPath);
        this.description = session.gitBranch
            ? `${session.gitBranch}`
            : projectName;
        this.tooltip = new vscode.MarkdownString(`**${projectName}**\n\n` +
            `${session.firstMessage.slice(0, 200)}${session.firstMessage.length > 200 ? '...' : ''}\n\n` +
            `---\n` +
            `$(folder) \`${session.projectPath}\`\n\n` +
            `$(clock) ${(0, utils_1.formatRelativeTime)(session.timestamp)}` +
            (session.gitBranch ? `\n\n$(git-branch) ${session.gitBranch}` : ''));
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
class SessionBrowserProvider {
    constructor(parseAllClaudeSessions) {
        this.parseAllClaudeSessions = parseAllClaudeSessions;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.sessions = [];
        this.loadId = 0; // Incremented on each refresh to invalidate stale loads
    }
    /**
     * Refresh the session list
     */
    refresh() {
        this.loadId++; // Invalidate any ongoing loads
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    async getChildren(element) {
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
        }
        catch (err) {
            console.error('Failed to load Claude sessions:', err);
            return [];
        }
    }
}
exports.SessionBrowserProvider = SessionBrowserProvider;
//# sourceMappingURL=sessionBrowser.js.map