#!/usr/bin/env node
/**
 * save-workspace.js — Snapshot alive Claude + Codex sessions for restore after restart.
 *
 * Claude sessions come from the PID files Claude Code writes to
 * ~/.claude/sessions/<pid>.json (authoritative sessionId/cwd/name) via
 * tracker-utils.getLiveSessions(). Codex sessions are discovered via ps and
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

// Titles for sessions whose PID file carries no name (older Claude Code)
const db = utils.tryDb();

const args = process.argv.slice(2);
const jsonMode = args.includes('--json');
const dryRun = args.includes('--dry-run');

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

function getSessionTitle(sessionId) {
  if (!db) return null;
  try {
    const s = db.getSessionById(sessionId);
    if (!s) return null;
    return s.custom_title || s.auto_title || s.slug || (s.summary && s.summary.substring(0, 60)) || null;
  } catch (e) {}
  return null;
}

// --- Main ---

const entries = [];
const seenSessions = new Set();

function pushEntry(agent, proc) {
  if (seenSessions.has(proc.sessionId)) return;
  seenSessions.add(proc.sessionId);
  const projectDir = proc.cwd || '';
  const projectName = projectDir ? path.basename(projectDir) : '';
  const title = proc.name || (agent === 'claude' && getSessionTitle(proc.sessionId)) || projectName;
  const tabTitle = `${projectName}—${proc.sessionId.substring(0, 8)}`;
  entries.push({
    agent,
    sessionId: proc.sessionId,
    projectDir,
    projectName,
    title,
    tabTitle,
    pid: proc.pid,
    tty: proc.tty || '',
    status: proc.status || '',
    savedAt: new Date().toISOString(),
  });
}

for (const proc of utils.getLiveSessions()) pushEntry('claude', proc);
for (const proc of getRunningCodexSessions()) pushEntry('codex', proc);

// Tab order lives in the TTY sequence (ttys003 < ttys021 < ttys100)
entries.sort((a, b) => utils.ttyOrder(a.tty) - utils.ttyOrder(b.tty));

const state = {
  schema: 3,
  savedAt: new Date().toISOString(),
  sessions: entries,
};

if (jsonMode) {
  console.log(JSON.stringify(state, null, 2));
} else if (dryRun) {
  console.log(`Would save ${entries.length} session(s) to ${STATE_PATH}:`);
  for (const e of entries) {
    console.log(`  ${e.tty.padEnd(8)} ${e.tabTitle} — ${e.title} — ${e.projectDir} (PID ${e.pid})`);
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
