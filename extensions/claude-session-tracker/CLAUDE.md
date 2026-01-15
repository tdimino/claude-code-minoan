# Claude Session Tracker

VS Code extension for tracking and resuming Claude Code sessions across windows/crashes.

## Stack
- TypeScript, VS Code Extension API
- Node.js fs/readline for JSONL parsing
- Cross-window state via shared JSON file

## Structure
- `src/extension.ts` - Entry point, wires components
- `src/terminalWatcher.ts` - Terminal detection (name + process inspection)
- `src/crossWindowState.ts` - Multi-window state sync via `~/.claude/vscode-tracker-state.json`
- `src/statusBar.ts` - Status bar indicator (Active/Resumable/Recoverable states)
- `src/commands.ts` - All registered commands + JSONL session parsing
- `src/sessionStorage.ts` - VS Code globalState persistence
- `src/utils.ts` - Process detection, git branch, terminal helpers

## Commands
```bash
npm run compile      # Build TypeScript
npm run watch        # Watch mode
npx vsce package     # Create .vsix
```

## Testing
```bash
npx ts-node test/verify-fixes.ts  # Verify bug fixes
```
Manual testing: `test/manual-test-checklist.md`

## Key Patterns

**Cross-Window State (atomic writes):**
```typescript
// crossWindowState.ts uses temp file + rename for atomicity
writeStateAtomic(state) {
  const tempPath = `${STATE_FILE}.${randomUUID()}.tmp`;
  fs.writeFileSync(tempPath, JSON.stringify(state));
  fs.renameSync(tempPath, STATE_FILE); // Atomic on POSIX
}
```

**Terminal Detection (hybrid):**
1. Fast path: terminal name contains "claude"
2. Slow path: process inspection via `ps` (checks shell + children)

**Session Parsing:** Claude stores sessions in `~/.claude/projects/{encoded-path}/*.jsonl`

## Critical Invariants

**NEVER auto-run `claude --continue`** - Clicking status bar shows session picker, user must select.

**Stream cleanup required** - parseSessionFile must call `rl.close()` + `stream.destroy()`

**Heartbeat interval** - 10s updates, 30s stale threshold for crash detection

## State File Format
```json
{
  "windows": {
    "pid-timestamp": {
      "windowId": "pid-timestamp",
      "pid": 12345,
      "lastUpdate": 1705123456789,
      "terminals": [{ "name": "Claude Code", "workspacePath": "/path" }]
    }
  }
}
```

## Version
Bump `package.json` version: MAJOR=breaking, MINOR=features, PATCH=fixes
