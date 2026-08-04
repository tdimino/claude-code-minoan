#!/usr/bin/env node
/**
 * save-workspace.js — Snapshot alive Claude + Codex sessions for restore after restart.
 *
 * Claude sessions come from the PID files Claude Code writes to
 * ~/.claude/sessions/<pid>.json (authoritative sessionId/cwd/name), with the
 * old pgrep+lsof scan as fallback. Codex sessions are discovered via ps and
 * lsof on their open rollout files. Writes ~/.claude/workspace-state.json,
 * ordered by TTY so restore recreates the tab order.
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

function isAlive(pid) {
  try { process.kill(pid, 0); return true; }
  catch (e) { return e.code === 'EPERM'; }
}

// pid -> tty for every TTY-attached process, one ps pass
function getTtyMap() {
  const map = {};
  try {
    const out = execSync('ps -axo pid=,tty= 2>/dev/null || true', {
      encoding: 'utf8', timeout: 5000
    });
    for (const line of out.trim().split('\n')) {
      const [pid, tty] = line.trim().split(/\s+/);
      if (pid && tty && tty !== '??') map[parseInt(pid)] = tty;
    }
  } catch (e) {}
  return map;
}

// Primary claude source: PID files written by Claude Code itself
function getClaudeSessionsFromPidFiles() {
  const sessions = [];
  const dir = path.join(HOME, '.claude', 'sessions');
  let files = [];
  try { files = fs.readdirSync(dir).filter(f => /^\d+\.json$/.test(f)); }
  catch (e) { return sessions; }
  for (const f of files) {
    try {
      const info = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
      if (!info.pid || !info.sessionId || !isAlive(info.pid)) continue;
      if (info.kind && info.kind !== 'interactive') continue;
      // Stale PID file + recycled PID: confirm the process is actually claude
      const cmd = execSync(`ps -p ${info.pid} -o command= 2>/dev/null || true`, {
        encoding: 'utf8', timeout: 5000
      }).trim();
      if (!cmd || !utils.isClaudeSession(cmd)) continue;
      sessions.push({
        pid: info.pid,
        cwd: info.cwd || '',
        sessionId: info.sessionId,
        name: info.name || '',
      });
    } catch (e) {}
  }
  return sessions;
}

// Codex sessions: native binary PIDs -> open rollout files via lsof.
// The earliest-opened rollout is the main thread (subagent threads open later).
function getRunningCodexSessions() {
  const sessions = [];
  if (process.platform !== 'darwin') return sessions;
  let psOut = '';
  try {
    psOut = execSync('ps -axo pid=,tty=,args= 2>/dev/null || true', {
      encoding: 'utf8', timeout: 5000
    });
  } catch (e) { return sessions; }

  // uuid -> thread name from codex's own index
  const threadNames = {};
  try {
    const idx = fs.readFileSync(path.join(HOME, '.codex', 'session_index.jsonl'), 'utf8');
    for (const line of idx.trim().split('\n')) {
      try {
        const row = JSON.parse(line);
        if (row.id && row.thread_name) threadNames[row.id] = row.thread_name;
      } catch (e) {}
    }
  } catch (e) {}

  const ROLLOUT_RE = /rollout-(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})-([0-9a-f-]{36})\.jsonl$/;

  for (const line of psOut.trim().split('\n')) {
    const m = line.trim().match(/^(\d+)\s+(\S+)\s+(.*)$/);
    if (!m || m[2] === '??') continue;
    const [, pidStr, tty, cmdArgs] = m;
    const firstTok = cmdArgs.split(/\s+/)[0];
    if (!firstTok.endsWith('/bin/codex') || cmdArgs.startsWith('node')) continue;

    const pid = parseInt(pidStr);
    let rollouts = [];
    let cwd = '';
    try {
      const lsof = execSync(`lsof -a -p ${pid} -Fn 2>/dev/null || true`, {
        encoding: 'utf8', timeout: 5000
      });
      for (const ln of lsof.split('\n')) {
        if (!ln.startsWith('n')) continue;
        const name = ln.slice(1);
        if (name.includes('/.codex/sessions/') && ROLLOUT_RE.test(name)) {
          rollouts.push(name);
        }
      }
      const cwdOut = execSync(`lsof -a -p ${pid} -d cwd -Fn 2>/dev/null || true`, {
        encoding: 'utf8', timeout: 5000
      });
      const cm = cwdOut.match(/^n(.+)$/m);
      if (cm) cwd = cm[1];
    } catch (e) {}
    if (rollouts.length === 0) continue;

    // Earliest filename timestamp = main thread (holds for fresh starts and
    // resumes alike; assumes codex stays one-process-per-session)
    rollouts.sort((a, b) => a.match(ROLLOUT_RE)[1].localeCompare(b.match(ROLLOUT_RE)[1]));
    const sessionId = rollouts[0].match(ROLLOUT_RE)[2];
    sessions.push({
      pid, tty, cwd, sessionId,
      name: threadNames[sessionId] || '',
    });
  }
  return sessions;
}

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

const ttyMap = getTtyMap();
const entries = [];
const seenSessions = new Set();

function pushEntry(agent, proc, sessionId) {
  if (seenSessions.has(sessionId)) return;
  seenSessions.add(sessionId);
  const projectDir = proc.cwd || '';
  const projectName = projectDir ? path.basename(projectDir) : '';
  const title = proc.name || (agent === 'claude' && getSessionTitle(sessionId)) || projectName;
  const tabTitle = `${projectName}—${sessionId.substring(0, 8)}`;
  entries.push({
    agent,
    sessionId,
    projectDir,
    projectName,
    title,
    tabTitle,
    pid: proc.pid,
    tty: proc.tty || ttyMap[proc.pid] || '',
    savedAt: new Date().toISOString(),
  });
}

// Claude: PID files first (authoritative), old process scan as fallback
for (const proc of getClaudeSessionsFromPidFiles()) {
  pushEntry('claude', proc, proc.sessionId);
}
for (const proc of getRunningClaudeProcesses()) {
  const sessionId = findSessionForProcess(proc);
  if (sessionId) pushEntry('claude', proc, sessionId);
}

// Codex
for (const proc of getRunningCodexSessions()) {
  pushEntry('codex', proc, proc.sessionId);
}

// Tab order lives in the TTY sequence (s000, s001, ...)
entries.sort((a, b) => (a.tty || 'zzz').localeCompare(b.tty || 'zzz'));

const state = {
  schema: 2,
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
  // Never clobber a useful snapshot with an empty one — after a crash or
  // logout there are 0 live sessions, and the previous snapshot is exactly
  // what restore-workspace.sh needs
  if (entries.length === 0) {
    let prior = null;
    try { prior = JSON.parse(fs.readFileSync(STATE_PATH, 'utf8')); } catch {}
    if (prior && Array.isArray(prior.sessions) && prior.sessions.length > 0) {
      console.log(`No live sessions detected — keeping prior snapshot of ${prior.sessions.length} session(s) (saved ${prior.savedAt}).`);
      process.exit(0);
    }
  }
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + '\n');
  console.log(`Saved ${entries.length} session(s) to ${STATE_PATH}`);
  for (const e of entries) {
    console.log(`  ${e.tabTitle} — ${e.projectDir}`);
  }
}
