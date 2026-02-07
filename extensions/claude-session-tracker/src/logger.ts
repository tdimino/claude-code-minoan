import * as vscode from 'vscode';

/**
 * Centralized logging for the Claude Session Tracker extension.
 * Logs to both VS Code OutputChannel (visible in Output panel) and console.
 */
class Logger {
  private outputChannel: vscode.OutputChannel | null = null;
  private isInitialized = false;

  /**
   * Initialize the logger with VS Code context
   */
  init(context: vscode.ExtensionContext): void {
    if (this.isInitialized) return;

    this.outputChannel = vscode.window.createOutputChannel('Claude Session Tracker');
    context.subscriptions.push(this.outputChannel);
    this.isInitialized = true;
    this.info('Logger initialized');
  }

  /**
   * Log info message
   */
  info(message: string, ...args: unknown[]): void {
    const formatted = this.format('INFO', message, args);
    console.log(formatted);
    this.outputChannel?.appendLine(formatted);
  }

  /**
   * Log warning message
   */
  warn(message: string, ...args: unknown[]): void {
    const formatted = this.format('WARN', message, args);
    console.warn(formatted);
    this.outputChannel?.appendLine(formatted);
  }

  /**
   * Log error message
   */
  error(message: string, ...args: unknown[]): void {
    const formatted = this.format('ERROR', message, args);
    console.error(formatted);
    this.outputChannel?.appendLine(formatted);
  }

  /**
   * Log debug message (more verbose)
   */
  debug(message: string, ...args: unknown[]): void {
    const formatted = this.format('DEBUG', message, args);
    console.log(formatted);
    this.outputChannel?.appendLine(formatted);
  }

  /**
   * Show the output channel in VS Code
   */
  show(): void {
    this.outputChannel?.show();
  }

  private format(level: string, message: string, args: unknown[]): string {
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
          } catch {
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
export const logger = new Logger();
