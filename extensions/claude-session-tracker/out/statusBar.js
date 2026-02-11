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
exports.StatusBarManager = void 0;
const vscode = __importStar(require("vscode"));
const utils_1 = require("./utils");
/**
 * Manages the status bar indicator for Claude sessions
 */
class StatusBarManager {
    constructor(context) {
        this.currentState = 'hidden';
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
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
    showActive(globalCount, localCount, totalCost) {
        if (!(0, utils_1.shouldShowStatusBar)()) {
            this.hide();
            return;
        }
        this.currentState = 'active';
        // Build status text with optional cost
        let text;
        if (globalCount === 1) {
            text = '$(terminal) Claude Active';
        }
        else {
            text = `$(terminal) Claude Active (${globalCount})`;
        }
        // Append cost if available and enabled
        if (totalCost && totalCost > 0 && (0, utils_1.shouldShowCostInStatusBar)()) {
            text += ` \u00b7 ${(0, utils_1.formatCost)(totalCost)}`;
        }
        this.statusBarItem.text = text;
        // Build informative tooltip
        if (localCount !== undefined && localCount !== globalCount) {
            const otherCount = globalCount - localCount;
            this.statusBarItem.tooltip = `${localCount} in this window, ${otherCount} in other window(s)\nClick to view all sessions`;
        }
        else {
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
    showResumable() {
        if (!(0, utils_1.shouldShowStatusBar)()) {
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
    showRecoverable(count) {
        if (!(0, utils_1.shouldShowStatusBar)()) {
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
    hide() {
        this.currentState = 'hidden';
        this.statusBarItem.hide();
    }
    /**
     * Get current state
     */
    getState() {
        return this.currentState;
    }
    /**
     * Dispose the status bar item
     */
    dispose() {
        this.statusBarItem.dispose();
    }
}
exports.StatusBarManager = StatusBarManager;
//# sourceMappingURL=statusBar.js.map