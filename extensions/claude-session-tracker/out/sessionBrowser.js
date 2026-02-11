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
const utils_1 = require("./utils");
const logger_1 = require("./logger");
/**
 * TreeItem for session browser
 * Displays enriched session info with click-to-resume functionality
 */
class SessionTreeItem extends vscode.TreeItem {
    constructor(session) {
        super((0, utils_1.truncate)(session.displayTitle, 55), vscode.TreeItemCollapsibleState.None);
        this.session = session;
        const showEnriched = (0, utils_1.shouldShowEnrichedData)();
        // Description: model + turns (or fallback to branch/project)
        const descParts = [];
        if (showEnriched && session.model)
            descParts.push(session.model);
        if (showEnriched && session.numTurns)
            descParts.push(`${session.numTurns} turns`);
        if (!descParts.length && session.gitBranch)
            descParts.push(session.gitBranch);
        if (!descParts.length)
            descParts.push(session.projectName);
        this.description = descParts.join(' \u00b7 ');
        // Rich tooltip with all available data
        const tooltipLines = [`**${session.projectName}**\n`];
        if (session.summary) {
            const summaryText = session.summary.length > 200
                ? session.summary.substring(0, 197) + '...'
                : session.summary;
            tooltipLines.push(summaryText + '\n');
        }
        else if (session.firstPrompt) {
            const promptText = session.firstPrompt.length > 200
                ? session.firstPrompt.substring(0, 197) + '...'
                : session.firstPrompt;
            tooltipLines.push(promptText + '\n');
        }
        tooltipLines.push('---');
        tooltipLines.push(`$(folder) \`${session.projectPath}\``);
        tooltipLines.push(`$(clock) ${(0, utils_1.formatRelativeTime)(session.modified)}`);
        if (session.gitBranch) {
            tooltipLines.push(`$(git-branch) ${session.gitBranch}`);
        }
        if (showEnriched) {
            const metaParts = [];
            if (session.numTurns)
                metaParts.push(`${session.numTurns} turns`);
            if (session.totalCostUsd)
                metaParts.push((0, utils_1.formatCost)(session.totalCostUsd));
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
    constructor(loadSessions) {
        this.loadSessions = loadSessions;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.sessions = [];
        this.loadId = 0;
    }
    refresh() {
        this.loadId++;
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    async getChildren(element) {
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
        }
        catch (err) {
            logger_1.logger.error('Failed to load Claude sessions:', err);
            return [];
        }
    }
}
exports.SessionBrowserProvider = SessionBrowserProvider;
//# sourceMappingURL=sessionBrowser.js.map