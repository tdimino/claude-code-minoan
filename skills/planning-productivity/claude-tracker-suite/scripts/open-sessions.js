#!/usr/bin/env node
/**
 * open-sessions.js — List recent sessions and open selected ones in Ghostty tabs
 *
 * Usage:
 *   node open-sessions.js [OPTIONS]
 *
 * Options:
 *   --limit <n>   Number of sessions to show (default: 10)
 *   --yes, -y     Skip confirmation, open all listed sessions
 *   --json        Output JSON (no interactive prompt)
 *   --list        List only, no prompt to open
 *
 * Opening goes through ~/.claude/scripts/ghostty-resume.sh, the suite's single
 * terminal opener. Live sessions are marked and skipped (Claude Code refuses a
 * second attach to a running session).
 */

const os = require('os');
const path = require('path');
const readline = require('readline');
const { spawnSync } = require('child_process');
const utils = require(os.homedir() + '/.claude/lib/tracker-utils.js');

const OPENER = path.join(os.homedir(), '.claude', 'scripts', 'ghostty-resume.sh');

// --- Parse arguments ---
const args = process.argv.slice(2);
let limit = 10;
let autoConfirm = false;
let jsonOutput = false;
let listOnly = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--limit' && args[i + 1]) {
    limit = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i] === '--yes' || args[i] === '-y') {
    autoConfirm = true;
  } else if (args[i] === '--json') {
    jsonOutput = true;
  } else if (args[i] === '--list') {
    listOnly = true;
  } else if (args[i] === '--split' || args[i] === '--cmux' || args[i] === '--ghostty') {
    const flag = args[i];
    if (flag === '--split' && args[i + 1] && !args[i + 1].startsWith('-')) i++;   // swallow its value
    console.error(`Note: ${flag} is retired — Ghostty tabs are the only target`);
  } else if (args[i] === '--help' || args[i] === '-h') {
    console.log(`
Usage: node open-sessions.js [OPTIONS]

Lists the most recently active Claude Code sessions and opens selected
ones in new Ghostty tabs.

Options:
  --limit <n>     Number of sessions to show (default: 10)
  --yes, -y       Skip confirmation, open all listed sessions
  --json          Output JSON, no interactive prompt
  --list          List sessions only, don't offer to open
  --help, -h      Show this help
`);
    process.exit(0);
  }
}

function shellEscape(str) {
  return "'" + str.replace(/'/g, "'\\''") + "'";
}

// --- Gather sessions ---
function getRecentSessions(n) {
  const liveById = new Map(utils.getLiveSessions().map(s => [s.sessionId, s]));
  const sessions = [];

  for (const file of utils.getAllSessionFiles()) {
    if (sessions.length >= n) break;
    const sessionId = path.basename(file.filePath, '.jsonl');
    const projectPath = utils.decodeProjectPath(file.projectDir);
    const projectName = path.basename(projectPath);
    const live = liveById.get(sessionId) || null;
    const customTitle = utils.readCustomTitle(file.filePath);
    const slug = utils.readSessionSlug(file.filePath);

    sessions.push({
      sessionId,
      projectPath,
      projectName,
      slug: slug || '',
      name: (live && live.name) || customTitle || slug || projectName,
      age: utils.formatAge(new Date(file.mtime).toISOString()),
      mtime: file.mtime,
      live: !!live,
      tty: live ? live.tty : '',
    });
  }
  return sessions;
}

// --- Display sessions ---
function printSessions(sessions) {
  console.log('\n\x1b[1m\x1b[36m  Recent Claude Code Sessions\x1b[0m\n');
  sessions.forEach((s, i) => {
    const num = `\x1b[33m[${i + 1}]\x1b[0m`;
    const liveBadge = s.live ? ` \x1b[42m\x1b[30m LIVE ${s.tty} \x1b[0m` : '';
    console.log(`  ${num} \x1b[1m${s.name}\x1b[0m \x1b[90m(${s.age})\x1b[0m${liveBadge}`);
    console.log(`      \x1b[90mDir:\x1b[0m ${s.projectPath}`);
    console.log(`      \x1b[90mID:\x1b[0m  ${s.sessionId.substring(0, 8)}`);
    if (s.slug && s.slug !== s.name) console.log(`      \x1b[90mSlug:\x1b[0m ${s.slug}`);
    console.log('');
  });
}

// --- Open one session in a Ghostty tab ---
function openSession(session) {
  if (session.live) {
    console.log(`  \x1b[33m–\x1b[0m \x1b[1m${session.name}\x1b[0m is already running in ${session.tty}`);
    return false;
  }
  const result = spawnSync(OPENER, [session.sessionId, '--project', session.projectPath, '--name', session.name],
    { timeout: 20000, stdio: ['ignore', 'inherit', 'inherit'] });
  if (result.status !== 0 || result.error) {
    const msg = result.error ? result.error.message : `exit code ${result.status}`;
    console.error(`  \x1b[31m✗\x1b[0m Failed to open ${session.name}: ${msg}`);
    return false;
  }
  return true;
}

function openMany(selected) {
  let opened = 0;
  for (const s of selected) {
    if (openSession(s)) opened++;
    if (selected.length > 1) spawnSync('sleep', ['1']);
  }
  console.log(`\n  \x1b[32mOpened ${opened}/${selected.length} session(s)\x1b[0m\n`);
}

// --- Interactive prompt ---
function promptUser(sessions) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  rl.question(
    '\x1b[36m  Open in Ghostty tabs?\x1b[0m Enter numbers (e.g. 1,3,5), "all", or "q" to quit: ',
    (answer) => {
      rl.close();
      answer = answer.trim().toLowerCase();
      if (answer === 'q' || answer === '') { console.log('  Cancelled.\n'); return; }

      let selected;
      if (answer === 'all' || answer === 'a') {
        selected = sessions;
      } else {
        const indices = answer.split(/[,\s]+/).map(s => parseInt(s, 10) - 1).filter(i => i >= 0 && i < sessions.length);
        selected = indices.map(i => sessions[i]);
      }
      if (selected.length === 0) { console.log('  No valid selection.\n'); return; }
      console.log('');
      openMany(selected);
    }
  );
}

// --- Main ---
function main() {
  const sessions = getRecentSessions(limit);
  if (sessions.length === 0) {
    console.log('\n\x1b[33m  No Claude sessions found.\x1b[0m\n');
    process.exit(0);
  }

  if (jsonOutput) {
    console.log(JSON.stringify(sessions.map(s => ({
      sessionId: s.sessionId,
      name: s.name,
      projectPath: s.projectPath,
      age: s.age,
      live: s.live,
      tty: s.tty,
      resumeCommand: `cd ${shellEscape(s.projectPath)} && claude --resume ${s.sessionId}`,
      ghosttyCommand: `${OPENER} ${s.sessionId}`,
    })), null, 2));
    return;
  }

  printSessions(sessions);
  if (listOnly) return;
  if (autoConfirm) { openMany(sessions); return; }
  promptUser(sessions);
}

main();
