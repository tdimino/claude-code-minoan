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
exports.logger = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Centralized logging for the Claude Session Tracker extension.
 * Logs to both VS Code OutputChannel (visible in Output panel) and console.
 */
class Logger {
    constructor() {
        this.outputChannel = null;
        this.isInitialized = false;
    }
    /**
     * Initialize the logger with VS Code context
     */
    init(context) {
        if (this.isInitialized)
            return;
        this.outputChannel = vscode.window.createOutputChannel('Claude Session Tracker');
        context.subscriptions.push(this.outputChannel);
        this.isInitialized = true;
        this.info('Logger initialized');
    }
    /**
     * Log info message
     */
    info(message, ...args) {
        const formatted = this.format('INFO', message, args);
        console.log(formatted);
        this.outputChannel?.appendLine(formatted);
    }
    /**
     * Log warning message
     */
    warn(message, ...args) {
        const formatted = this.format('WARN', message, args);
        console.warn(formatted);
        this.outputChannel?.appendLine(formatted);
    }
    /**
     * Log error message
     */
    error(message, ...args) {
        const formatted = this.format('ERROR', message, args);
        console.error(formatted);
        this.outputChannel?.appendLine(formatted);
    }
    /**
     * Log debug message (more verbose)
     */
    debug(message, ...args) {
        const formatted = this.format('DEBUG', message, args);
        console.log(formatted);
        this.outputChannel?.appendLine(formatted);
    }
    /**
     * Show the output channel in VS Code
     */
    show() {
        this.outputChannel?.show();
    }
    format(level, message, args) {
        const timestamp = new Date().toISOString();
        let formatted = `[${timestamp}] [${level}] ${message}`;
        if (args.length > 0) {
            const argsStr = args.map(arg => {
                if (arg instanceof Error) {
                    return `${arg.message}\n${arg.stack}`;
                }
                if (typeof arg === 'object') {
                    try {
                        return JSON.stringify(arg, null, 2);
                    }
                    catch {
                        return String(arg);
                    }
                }
                return String(arg);
            }).join(' ');
            formatted += ` ${argsStr}`;
        }
        return formatted;
    }
}
// Export singleton instance
exports.logger = new Logger();
//# sourceMappingURL=logger.js.map