#!/usr/bin/env node
/**
 * checkpoint-session.js — Create and query session checkpoints.
 *
 * Usage:
 *   node checkpoint-session.js create "label" [--summary "text"] [--session ID]
 *   node checkpoint-session.js list [--session ID] [--phase PHASE] [--limit N]
 *
 * Creates named bookmarks within a session capturing: label, git state
 * (branch + HEAD commit), current workflow phase, and optional summary.
 *
 * Session auto-detection: encodes process.cwd() as project dir name and
 * picks the most recently modified .jsonl in ~/.claude/projects/<encoded>/.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');

const HOME = os.homedir();
const PROJECTS_DIR = path.join(HOME, '.claude', 'projects');
const LIB_DIR = path.join(HOME, '.claude', 'lib');

function detectCurrentSession() {
  const cwd = process.cwd();
  const encoded = '-' + cwd.split('/').filter(Boolean).join('-');
  const projDir = path.join(PROJECTS_DIR, encoded);

  if (!fs.existsSync(projDir)) return null;

  const files = fs.readdirSync(projDir)
    .filter(f => f.endsWith('.jsonl'))
    .map(f => {
      const stat = fs.statSync(path.join(projDir, f));
      return { name: f, mtime: stat.mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime);

  if (files.length === 0) return null;

  const maxAge = 10 * 60 * 1000;
  if (Date.now() - files[0].mtime > maxAge) return null;

  return path.basename(files[0].name, '.jsonl');
}

function getGitState() {
  try {
    const branch = execSync('git rev-parse --abbrev-ref HEAD 2>/dev/null', { encoding: 'utf-8' }).trim();
    const commit = execSync('git rev-parse --short HEAD 2>/dev/null', { encoding: 'utf-8' }).trim();
    return { branch, commit };
  } catch {
    return { branch: null, commit: null };
  }
}

function getGitModifiedFiles() {
  try {
    const out = execSync('git diff --name-only HEAD 2>/dev/null', { encoding: 'utf-8' }).trim();
    const staged = execSync('git diff --cached --name-only 2>/dev/null', { encoding: 'utf-8' }).trim();
    const files = new Set([...out.split('\n'), ...staged.split('\n')].filter(Boolean));
    return [...files];
  } catch {
    return [];
  }
}

function getCurrentPhase(db, sessionId) {
  try {
    const phase = db.getCurrentPhase(sessionId);
    return phase ? phase.phase : null;
  } catch {
    return null;
  }
}

function formatAge(dateStr) {
  if (!dateStr) return 'unknown';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return mins + 'm ago';
  const hours = Math.floor(mins / 60);
  if (hours < 24) return hours + 'h ago';
  const days = Math.floor(hours / 24);
  return days + 'd ago';
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

function createCheckpoint(db, sessionId, label, summary) {
  const git = getGitState();
  const files = getGitModifiedFiles();
  const phase = getCurrentPhase(db, sessionId);

  try {
    db.createCheckpoint(sessionId, {
      label,
      summary: summary || null,
      phase,
      gitBranch: git.branch,
      gitCommitHash: git.commit,
      filesModified: files.length > 0 ? JSON.stringify(files) : null,
    });
  } catch (e) {
    if (e.message && e.message.includes('UNIQUE constraint failed')) {
      console.error(`\x1b[31mCheckpoint "${label}" already exists for this session.\x1b[0m`);
      console.error('Use a different label or list existing checkpoints.');
      process.exit(1);
    }
    throw e;
  }

  console.log(`\x1b[32m✓\x1b[0m Checkpoint created: \x1b[1m${label}\x1b[0m`);
  if (phase) console.log(`  \x1b[90mPhase:\x1b[0m ${phase}`);
  if (git.branch) console.log(`  \x1b[90mBranch:\x1b[0m ${git.branch} @ ${git.commit}`);
  if (files.length > 0) console.log(`  \x1b[90mModified:\x1b[0m ${files.length} file(s)`);
  if (summary) console.log(`  \x1b[90mSummary:\x1b[0m ${summary}`);
}

function listCheckpoints(db, sessionId, options = {}) {
  let checkpoints;
  if (sessionId) {
    checkpoints = db.getCheckpoints(sessionId);
  } else {
    checkpoints = db.getRecentCheckpoints({
      limit: options.limit || 20,
      phase: options.phase,
    });
  }

  if (checkpoints.length === 0) {
    console.log('\x1b[33mNo checkpoints found.\x1b[0m');
    return;
  }

  console.log(`\n\x1b[1mCheckpoints\x1b[0m (${checkpoints.length}):\n`);

  for (const cp of checkpoints) {
    const age = formatAge(cp.created_at);
    const phaseTag = cp.phase ? ` \x1b[36m[${cp.phase}]\x1b[0m` : '';
    const gitTag = cp.git_commit_hash ? ` \x1b[90m@ ${cp.git_branch || ''}:${cp.git_commit_hash}\x1b[0m` : '';

    console.log(`  \x1b[33m●\x1b[0m \x1b[1m${cp.label}\x1b[0m${phaseTag}${gitTag} \x1b[90m(${age})\x1b[0m`);
    if (cp.summary) console.log(`    ${cp.summary}`);
    if (cp.project_name) console.log(`    \x1b[90mProject:\x1b[0m ${cp.project_name}`);
    if (cp.files_modified) {
      try {
        const files = JSON.parse(cp.files_modified);
        if (files.length > 0) console.log(`    \x1b[90mFiles:\x1b[0m ${files.slice(0, 5).join(', ')}${files.length > 5 ? ` +${files.length - 5} more` : ''}`);
      } catch { /* skip */ }
    }
    console.log('    \x1b[90mSession:\x1b[0m ' + (cp.session_id || '').substring(0, 8));
    console.log('');
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command || command === '--help' || command === '-h') {
    console.log('\n\x1b[33mUsage:\x1b[0m');
    console.log('  node checkpoint-session.js create "label" [--summary "text"] [--session ID]');
    console.log('  node checkpoint-session.js list [--session ID] [--phase PHASE] [--limit N]');
    console.log('\n\x1b[90mExample: node checkpoint-session.js create "finished auth module"');
    console.log('Example: node checkpoint-session.js list --phase implementing\x1b[0m\n');
    process.exit(0);
  }

  let trackerDb;
  try {
    trackerDb = require(path.join(LIB_DIR, 'tracker-db'));
    if (!trackerDb.isAvailable()) {
      console.error('\x1b[31mtracker.db not available. Run migrate-to-sqlite.js first.\x1b[0m');
      process.exit(1);
    }
  } catch (e) {
    console.error('\x1b[31mFailed to load tracker-db: ' + e.message + '\x1b[0m');
    process.exit(1);
  }

  let sessionId = null;
  let summary = null;
  let phase = null;
  let limit = 20;

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--session' && args[i + 1]) {
      sessionId = args[++i];
    } else if (args[i] === '--summary' && args[i + 1]) {
      summary = args[++i];
    } else if (args[i] === '--phase' && args[i + 1]) {
      phase = args[++i];
    } else if (args[i] === '--limit' && args[i + 1]) {
      limit = parseInt(args[++i], 10);
    }
  }

  if (command === 'create') {
    const label = args[1];
    if (!label || label.startsWith('--')) {
      console.error('\x1b[31mUsage: checkpoint-session.js create "label" [--summary "text"]\x1b[0m');
      process.exit(1);
    }

    if (!sessionId) {
      sessionId = detectCurrentSession();
      if (!sessionId) {
        console.error('\x1b[31mNo active session detected. Use --session ID.\x1b[0m');
        process.exit(1);
      }
    }

    createCheckpoint(trackerDb, sessionId, label, summary);
  } else if (command === 'list') {
    if (!sessionId) sessionId = detectCurrentSession();
    listCheckpoints(trackerDb, sessionId, { phase, limit });
  } else {
    console.error(`\x1b[31mUnknown command: ${command}\x1b[0m`);
    process.exit(1);
  }

  trackerDb.close();
}

main();
