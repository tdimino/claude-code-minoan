#!/usr/bin/env node
/**
 * save-workspace.js — Snapshot alive Claude sessions for restore after restart.
 *
 * Queries running Claude processes, matches them to sessions, and writes
 * a workspace manifest to ~/.claude/workspace-state.json.
 *
 * Usage:
 *   node save-workspace.js              # Save current workspace state
 *   node save-workspace.js --json       # Print state to stdout instead of saving
 *   node save-workspace.js --dry-run    # Show what would be saved without writing
 */

'use strict';

const os = require('os');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const HOME = os.homedir();
const UTILS_PATH = path.join(HOME, '.claude', 'lib', 'tracker-utils.js');
const STATE_PATH = path.join(HOME, '.claude', 'workspace-state.json');

let utils;
try {
  utils = require(UTILS_PATH);
} catch (e) {
  console.error('Error: Could not load tracker utilities from ' + UTILS_PATH);
  process.exit(1);
}

let db;
try {
  db = require(path.join(HOME, '.claude', 'lib', 'tracker-db.js'));
  if (db.isAvailable()) db.initSchema();
  else db = null;
} catch (e) {
  db = null;
}

const args = process.argv.slice(2);
const jsonMode = args.includes('--json');
const dryRun = args.includes('--dry-run');

function getRunningClaudeProcesses() {
  const processes = [];
  if (process.platform === 'win32') return processes;

  try {
    const pidsResult = execSync('pgrep -f claude 2>/dev/null || true', {
      encoding: 'utf8', timeout: 5000
    });
    const pids = pidsResult.trim().split('\n').filter(p => p && /^\d+$/.test(p));

    for (const pid of pids) {
      try {
        const cmd = execSync(`ps -p ${pid} -o command= 2>/dev/null || true`, {
          encoding: 'utf8', timeout: 5000
        }).trim();
        if (!utils.isClaudeSession(cmd)) continue;

        let cwd = '';
        try {
          const lsof = execSync(`lsof -p ${pid} 2>/dev/null | grep cwd || true`, {
            encoding: 'utf8', timeout: 5000
          });
          const match = lsof.match(/(\/[^\n]+)$/m);
          if (match) cwd = match[1].trim();
        } catch (e) {}

        // Extract --resume session ID if present
        const resumeMatch = cmd.match(/--resume\s+([a-f0-9-]+)/);
        const sessionId = resumeMatch ? resumeMatch[1] : null;

        processes.push({ pid: parseInt(pid), cmd, cwd, sessionId });
      } catch (e) {}
    }
  } catch (e) {}

  return processes;
}

function findSessionForProcess(proc) {
  if (proc.sessionId) return proc.sessionId;
  if (!proc.cwd) return null;

  // Find most recent session file matching this cwd
  const allFiles = utils.getAllSessionFiles();
  const cutoff = Date.now() - (24 * 60 * 60 * 1000); // last 24h
  const matching = allFiles
    .filter(f => f.mtime > cutoff && utils.isPathMatch(f.projectDir, proc.cwd))
    .sort((a, b) => b.mtime - a.mtime);

  if (matching.length > 0) {
    return path.basename(matching[0].filePath, '.jsonl');
  }
  return null;
}

function getSessionTitle(sessionId) {
  if (!db) return null;
  try {
    const s = db.getSessionById(sessionId);
    if (s && s.title) return s.title;
    if (s && s.summary) return s.summary.substring(0, 60);
  } catch (e) {}
  return null;
}

// --- Main ---

const processes = getRunningClaudeProcesses();
const entries = [];

for (const proc of processes) {
  const sessionId = findSessionForProcess(proc);
  if (!sessionId) continue;

  const projectDir = proc.cwd || '';
  const projectName = projectDir ? path.basename(projectDir) : '';
  const title = getSessionTitle(sessionId) || projectName;
  const tabTitle = `${projectName}—${sessionId.substring(0, 8)}`;

  entries.push({
    sessionId,
    projectDir,
    projectName,
    title,
    tabTitle,
    pid: proc.pid,
    savedAt: new Date().toISOString(),
  });
}

const state = {
  savedAt: new Date().toISOString(),
  sessions: entries,
};

if (jsonMode) {
  console.log(JSON.stringify(state, null, 2));
} else if (dryRun) {
  console.log(`Would save ${entries.length} session(s) to ${STATE_PATH}:`);
  for (const e of entries) {
    console.log(`  ${e.tabTitle} — ${e.projectDir} (PID ${e.pid})`);
  }
} else {
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + '\n');
  console.log(`Saved ${entries.length} session(s) to ${STATE_PATH}`);
  for (const e of entries) {
    console.log(`  ${e.tabTitle} — ${e.projectDir}`);
  }
}
