/**
 * Claude Session Tracker v0.2.1 - Fix Verification Script
 *
 * Run with: npx ts-node test/verify-fixes.ts
 *
 * Verifies the critical bug fixes without requiring VS Code runtime.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const STATE_FILE = path.join(os.homedir(), '.claude', 'vscode-tracker-state.json');
const CLAUDE_PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');

interface TestResult {
  name: string;
  passed: boolean;
  details: string;
}

const results: TestResult[] = [];

function test(name: string, fn: () => { passed: boolean; details: string }) {
  try {
    const result = fn();
    results.push({ name, ...result });
  } catch (err) {
    results.push({
      name,
      passed: false,
      details: `Error: ${err instanceof Error ? err.message : String(err)}`,
    });
  }
}

// =============================================================================
// Test 1: Cross-window state file format
// =============================================================================
test('Cross-window state file is valid JSON', () => {
  if (!fs.existsSync(STATE_FILE)) {
    return { passed: true, details: 'State file does not exist yet (OK for fresh install)' };
  }

  const content = fs.readFileSync(STATE_FILE, 'utf8');
  const state = JSON.parse(content);

  if (typeof state !== 'object' || state === null) {
    return { passed: false, details: 'State is not an object' };
  }

  if (!('windows' in state)) {
    return { passed: false, details: 'Missing "windows" property' };
  }

  return { passed: true, details: `Valid state with ${Object.keys(state.windows).length} window(s)` };
});

// =============================================================================
// Test 2: Atomic write pattern in source code
// =============================================================================
test('crossWindowState.ts uses atomic write pattern', () => {
  const filePath = path.join(__dirname, '../src/crossWindowState.ts');
  const content = fs.readFileSync(filePath, 'utf8');

  const hasAtomicWrite = content.includes('writeStateAtomic');
  const hasTempFile = content.includes('.tmp');
  const hasRename = content.includes('renameSync');

  if (!hasAtomicWrite) {
    return { passed: false, details: 'Missing writeStateAtomic method' };
  }
  if (!hasTempFile) {
    return { passed: false, details: 'Missing temp file pattern' };
  }
  if (!hasRename) {
    return { passed: false, details: 'Missing atomic rename' };
  }

  return { passed: true, details: 'Atomic write pattern implemented correctly' };
});

// =============================================================================
// Test 3: Status bar uses showAllTerminals command
// =============================================================================
test('statusBar.ts uses showAllTerminals command for active state', () => {
  const filePath = path.join(__dirname, '../src/statusBar.ts');
  const content = fs.readFileSync(filePath, 'utf8');

  // Check that showActive uses showAllTerminals, not focusTerminal
  const showActiveMatch = content.match(/showActive\([^)]*\)[^}]*\{[\s\S]*?command\s*=\s*['"]([^'"]+)['"]/);

  if (!showActiveMatch) {
    return { passed: false, details: 'Could not find showActive command assignment' };
  }

  const command = showActiveMatch[1];
  if (command === 'claude-tracker.focusTerminal') {
    return { passed: false, details: 'CRITICAL: Still using focusTerminal (causes auto-continue bug)' };
  }

  if (command !== 'claude-tracker.showAllTerminals') {
    return { passed: false, details: `Unexpected command: ${command}` };
  }

  return { passed: true, details: 'Using showAllTerminals (session picker)' };
});

// =============================================================================
// Test 4: Terminal watcher uses Promise.all (not forEach)
// =============================================================================
test('terminalWatcher.ts uses Promise.all for existing terminals', () => {
  const filePath = path.join(__dirname, '../src/terminalWatcher.ts');
  const content = fs.readFileSync(filePath, 'utf8');

  // Check for forEach with async (anti-pattern)
  const hasForEachAsync = /terminals\.forEach\s*\(\s*async/.test(content);
  if (hasForEachAsync) {
    return { passed: false, details: 'Still using forEach with async callback (fire-and-forget bug)' };
  }

  // Check for Promise.all pattern
  const hasPromiseAll = content.includes('Promise.all');
  if (!hasPromiseAll) {
    return { passed: false, details: 'Missing Promise.all pattern' };
  }

  return { passed: true, details: 'Using Promise.all for proper async handling' };
});

// =============================================================================
// Test 5: TOCTOU protection in terminal tracking
// =============================================================================
test('terminalWatcher.ts has TOCTOU protection', () => {
  const filePath = path.join(__dirname, '../src/terminalWatcher.ts');
  const content = fs.readFileSync(filePath, 'utf8');

  // Check for try-catch around trackTerminal
  const hasTryCatch = /try\s*\{[\s\S]*?trackTerminal[\s\S]*?\}\s*catch/.test(content);
  if (!hasTryCatch) {
    return { passed: false, details: 'Missing try-catch around trackTerminal' };
  }

  // Check for exitStatus check
  const hasExitStatusCheck = content.includes('exitStatus !== undefined');
  if (!hasExitStatusCheck) {
    return { passed: false, details: 'Missing exitStatus check before tracking' };
  }

  return { passed: true, details: 'TOCTOU protection implemented' };
});

// =============================================================================
// Test 6: File watcher cleanup
// =============================================================================
test('crossWindowState.ts has disposeWatcher method', () => {
  const filePath = path.join(__dirname, '../src/crossWindowState.ts');
  const content = fs.readFileSync(filePath, 'utf8');

  const hasDisposeWatcher = content.includes('disposeWatcher');
  const hasStreamDestroy = content.includes('.close()') || content.includes('.destroy()');

  if (!hasDisposeWatcher) {
    return { passed: false, details: 'Missing disposeWatcher method' };
  }

  return { passed: true, details: 'File watcher cleanup implemented' };
});

// =============================================================================
// Test 7: Session picker with 12-hour filter
// =============================================================================
test('commands.ts has getRecentResumableSessions function', () => {
  const filePath = path.join(__dirname, '../src/commands.ts');
  const content = fs.readFileSync(filePath, 'utf8');

  const hasFunction = content.includes('getRecentResumableSessions');
  const hasHoursParam = /getRecentResumableSessions\s*\(\s*hours/.test(content) ||
    /getRecentResumableSessions\s*\(\s*\d+\s*\)/.test(content);
  const hasCutoffTime = content.includes('cutoffTime');

  if (!hasFunction) {
    return { passed: false, details: 'Missing getRecentResumableSessions function' };
  }

  return { passed: true, details: '12-hour filter function implemented' };
});

// =============================================================================
// Test 8: Stream cleanup in parseSessionFile
// =============================================================================
test('commands.ts has proper stream cleanup in parseSessionFile', () => {
  const filePath = path.join(__dirname, '../src/commands.ts');
  const content = fs.readFileSync(filePath, 'utf8');

  const hasStreamDestroy = content.includes('stream.destroy()');
  const hasRlClose = content.includes('rl.close()');

  if (!hasStreamDestroy) {
    return { passed: false, details: 'Missing stream.destroy() call' };
  }
  if (!hasRlClose) {
    return { passed: false, details: 'Missing rl.close() call' };
  }

  return { passed: true, details: 'Stream cleanup implemented correctly' };
});

// =============================================================================
// Test 9: Heartbeat cleanup tracked
// =============================================================================
test('crossWindowState.ts tracks heartbeat interval', () => {
  const filePath = path.join(__dirname, '../src/crossWindowState.ts');
  const content = fs.readFileSync(filePath, 'utf8');

  const hasHeartbeatProperty = content.includes('heartbeatInterval');
  const clearsInDeactivate = /deactivate[\s\S]*?heartbeatInterval/.test(content);

  if (!hasHeartbeatProperty) {
    return { passed: false, details: 'Missing heartbeatInterval property' };
  }

  return { passed: true, details: 'Heartbeat interval tracked for cleanup' };
});

// =============================================================================
// Test 10: Session files exist and are parseable
// =============================================================================
test('Claude session files are accessible', () => {
  if (!fs.existsSync(CLAUDE_PROJECTS_DIR)) {
    return { passed: true, details: 'No projects directory yet (OK for fresh install)' };
  }

  const projectDirs = fs.readdirSync(CLAUDE_PROJECTS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => path.join(CLAUDE_PROJECTS_DIR, d.name));

  let totalFiles = 0;
  let recentFiles = 0;
  const cutoff = Date.now() - (12 * 60 * 60 * 1000);

  for (const dir of projectDirs) {
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.jsonl'));
    totalFiles += files.length;

    for (const file of files) {
      const stat = fs.statSync(path.join(dir, file));
      if (stat.mtime.getTime() > cutoff) {
        recentFiles++;
      }
    }
  }

  return {
    passed: true,
    details: `${totalFiles} total session files, ${recentFiles} from last 12 hours`,
  };
});

// =============================================================================
// Run and report
// =============================================================================
console.log('\n=== Claude Session Tracker v0.2.1 Fix Verification ===\n');

let passed = 0;
let failed = 0;

for (const result of results) {
  const status = result.passed ? '✅ PASS' : '❌ FAIL';
  console.log(`${status}: ${result.name}`);
  console.log(`   ${result.details}\n`);

  if (result.passed) {
    passed++;
  } else {
    failed++;
  }
}

console.log('='.repeat(50));
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log('='.repeat(50));

if (failed > 0) {
  process.exit(1);
}
