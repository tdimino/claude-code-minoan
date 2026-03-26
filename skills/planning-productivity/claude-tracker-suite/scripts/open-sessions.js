#!/usr/bin/env node
/**
 * open-sessions.js — List recent sessions and open them in cmux tabs/splits
 *
 * Usage:
 *   node open-sessions.js [OPTIONS]
 *
 * Options:
 *   --limit <n>         Number of sessions to show (default: 10)
 *   --split <direction>  Open as splits instead of tabs (left|right|up|down)
 *   --yes               Skip confirmation prompt
 *   --json              Output JSON (no interactive prompt)
 *   --list              List only, no prompt to open
 */

const os = require('os');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { execSync, spawnSync } = require('child_process');
const utils = require(os.homedir() + '/.claude/lib/tracker-utils.js');

// --- Parse arguments ---
const args = process.argv.slice(2);
let limit = 10;
let splitDirection = null; // null = tabs, otherwise left|right|up|down
let autoConfirm = false;
let jsonOutput = false;
let listOnly = false;
let forceTarget = null; // null = auto-detect, 'cmux' or 'ghostty'

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--limit' && args[i + 1]) {
    limit = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i] === '--split' && args[i + 1]) {
    splitDirection = args[i + 1];
    i++;
  } else if (args[i] === '--yes' || args[i] === '-y') {
    autoConfirm = true;
  } else if (args[i] === '--json') {
    jsonOutput = true;
  } else if (args[i] === '--list') {
    listOnly = true;
  } else if (args[i] === '--cmux') {
    forceTarget = 'cmux';
  } else if (args[i] === '--ghostty') {
    forceTarget = 'ghostty';
  } else if (args[i] === '--help' || args[i] === '-h') {
    console.log(`
Usage: node open-sessions.js [OPTIONS]

Lists the most recently active Claude Code sessions and opens selected
ones in new terminal tabs. Auto-detects cmux or Ghostty.

Options:
  --limit <n>           Number of sessions to show (default: 10)
  --split <direction>   Open as splits: left, right, up, down (cmux only)
  --cmux                Force cmux as terminal target
  --ghostty             Force Ghostty as terminal target (AppleScript)
  --yes, -y             Skip confirmation, open all listed sessions
  --json                Output JSON, no interactive prompt
  --list                List sessions only, don't offer to open
  --help, -h            Show this help
`);
    process.exit(0);
  }
}

// --- Check cmux availability ---
function hasCmux() {
  try {
    execSync('cmux ping', { stdio: 'pipe', timeout: 3000 });
    return true;
  } catch {
    return false;
  }
}

// --- Gather sessions ---
function getRecentSessions(n) {
  const allFiles = utils.getAllSessionFiles();
  const seen = new Set();
  const sessions = [];

  for (const file of allFiles) {
    if (sessions.length >= n) break;

    const sessionId = path.basename(file.filePath, '.jsonl');
    if (seen.has(sessionId)) continue;
    seen.add(sessionId);

    const projectPath = utils.decodeProjectPath(file.projectDir);
    const projectName = projectPath.split('/').pop();
    const slug = utils.readSessionSlug(file.filePath);
    const customTitle = utils.readCustomTitle(file.filePath);
    const age = utils.formatAge(new Date(file.mtime).toISOString());

    // Read first-line timestamp for display
    let timestamp = '';
    try {
      const fd = fs.openSync(file.filePath, 'r');
      const buf = Buffer.alloc(4096);
      const bytesRead = fs.readSync(fd, buf, 0, 4096, 0);
      fs.closeSync(fd);
      const firstLine = buf.toString('utf-8', 0, bytesRead).split('\n')[0];
      if (firstLine) {
        const obj = JSON.parse(firstLine);
        timestamp = obj.timestamp || '';
      }
    } catch {}

    sessions.push({
      sessionId,
      projectPath,
      projectName,
      slug: slug || '',
      name: customTitle || slug || projectName,
      age,
      timestamp,
      mtime: file.mtime,
    });
  }

  return sessions;
}

// --- Display sessions ---
function printSessions(sessions) {
  console.log('\n\x1b[1m\x1b[36m  Recent Claude Code Sessions\x1b[0m\n');

  sessions.forEach((s, i) => {
    const num = `\x1b[33m[${i + 1}]\x1b[0m`;
    const name = s.name ? `\x1b[1m${s.name}\x1b[0m` : `\x1b[1m${s.projectName}\x1b[0m`;
    const age = `\x1b[90m(${s.age})\x1b[0m`;
    console.log(`  ${num} ${name} ${age}`);
    console.log(`      \x1b[90mDir:\x1b[0m ${s.projectPath}`);
    console.log(`      \x1b[90mID:\x1b[0m  ${s.sessionId.substring(0, 8)}`);
    if (s.slug && s.slug !== s.name) {
      console.log(`      \x1b[90mSlug:\x1b[0m ${s.slug}`);
    }
    console.log('');
  });
}

// --- Open session in cmux ---
function openInCmux(session, direction) {
  const cmd = `cd ${shellEscape(session.projectPath)} && claude --resume ${session.sessionId}`;
  const tabName = session.name.substring(0, 40);

  try {
    let surfaceOutput;
    if (direction) {
      surfaceOutput = execSync(`cmux new-split ${direction}`, { encoding: 'utf-8', timeout: 5000 }).trim();
    } else {
      surfaceOutput = execSync('cmux new-surface --type terminal', { encoding: 'utf-8', timeout: 5000 }).trim();
    }

    // Parse surface ID from output like "OK surface:6 pane:4 workspace:2"
    const surfaceMatch = surfaceOutput.match(/surface:\d+/);
    if (!surfaceMatch) {
      console.error(`  \x1b[31mFailed to parse surface ID from: ${surfaceOutput}\x1b[0m`);
      return false;
    }
    const surfaceId = surfaceMatch[0];

    // Small delay to let the terminal initialize
    execSync('sleep 0.3');

    spawnSync('cmux', ['send', '--surface', surfaceId, cmd], { timeout: 5000 });
    spawnSync('cmux', ['send-key', '--surface', surfaceId, 'enter'], { timeout: 5000 });
    spawnSync('cmux', ['rename-tab', '--surface', surfaceId, tabName], { timeout: 5000 });

    console.log(`  \x1b[32m✓\x1b[0m Opened \x1b[1m${tabName}\x1b[0m in ${surfaceId}`);
    return true;
  } catch (err) {
    console.error(`  \x1b[31m✗\x1b[0m Failed to open ${tabName}: ${err.message}`);
    return false;
  }
}

function shellEscape(str) {
  return "'" + str.replace(/'/g, "'\\''") + "'";
}

// --- Open session in Ghostty via resume-session.sh ---
function openInGhostty(session) {
  const scriptDir = path.dirname(process.argv[1]);
  const resumeScript = path.join(scriptDir, 'resume-session.sh');
  const args = [resumeScript, session.sessionId, '--ghostty'];
  if (session.projectPath) {
    args.push('--project', session.projectPath);
  }
  const result = spawnSync('bash', args, { timeout: 10000, stdio: 'inherit' });
  if (result.status !== 0 || result.error) {
    const msg = result.error ? result.error.message : `exit code ${result.status}`;
    console.error(`  \x1b[31m✗\x1b[0m Failed to open in Ghostty: ${msg}`);
    return false;
  }
  console.log(`  \x1b[32m✓\x1b[0m Opened \x1b[1m${session.name}\x1b[0m in Ghostty`);
  return true;
}

// --- Open session in best available terminal ---
function openSession(session, direction, target) {
  if (target === 'ghostty') return openInGhostty(session);
  if (target === 'cmux') return openInCmux(session, direction);
  // auto: try cmux first, fall back to ghostty
  if (hasCmux()) return openInCmux(session, direction);
  return openInGhostty(session);
}

// --- Interactive prompt ---
function promptUser(sessions) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  const mode = splitDirection ? `split ${splitDirection}` : 'new tab';
  let targetLabel;
  if (forceTarget === 'ghostty') targetLabel = 'Ghostty';
  else if (forceTarget === 'cmux' || hasCmux()) targetLabel = `cmux ${mode}`;
  else targetLabel = 'Ghostty';

  rl.question(
    `\x1b[36m  Open in ${targetLabel}?\x1b[0m Enter numbers (e.g. 1,3,5), "all", or "q" to quit: `,
    (answer) => {
      rl.close();
      answer = answer.trim().toLowerCase();

      if (answer === 'q' || answer === '') {
        console.log('  Cancelled.\n');
        return;
      }

      let selected;
      if (answer === 'all' || answer === 'a') {
        selected = sessions;
      } else {
        const indices = answer.split(/[,\s]+/).map(s => parseInt(s, 10) - 1).filter(i => i >= 0 && i < sessions.length);
        selected = indices.map(i => sessions[i]);
      }

      if (selected.length === 0) {
        console.log('  No valid selection.\n');
        return;
      }

      console.log('');
      let opened = 0;
      for (const s of selected) {
        if (openSession(s, splitDirection, forceTarget)) opened++;
        if (selected.length > 1) execSync('sleep 0.5');
      }
      console.log(`\n  \x1b[32mOpened ${opened}/${selected.length} session(s)\x1b[0m\n`);
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

  // JSON mode
  if (jsonOutput) {
    const out = sessions.map(s => ({
      sessionId: s.sessionId,
      name: s.name,
      projectPath: s.projectPath,
      age: s.age,
      resumeCommand: `cd ${shellEscape(s.projectPath)} && claude --resume ${s.sessionId}`,
    }));
    console.log(JSON.stringify(out, null, 2));
    return;
  }

  printSessions(sessions);

  if (listOnly) return;

  if (autoConfirm) {
    let opened = 0;
    for (const s of sessions) {
      if (openSession(s, splitDirection, forceTarget)) opened++;
      if (sessions.length > 1) execSync('sleep 0.5');
    }
    console.log(`\n  \x1b[32mOpened ${opened}/${sessions.length} session(s)\x1b[0m\n`);
    return;
  }

  promptUser(sessions);
}

main();
