#!/usr/bin/env node
/**
 * list-sessions.js — List recent Claude Code sessions with live status
 *
 * Usage: node list-sessions.js [--here] [--limit N] [--vscode]
 *
 *   --here       Only sessions whose project is the current directory
 *   --limit N    Sessions to show (default: tracker-utils MAX_SESSIONS)
 *   --vscode     Only sessions whose project is open in a VS Code workspace
 *
 * Live status comes from Claude Code's own PID files (~/.claude/sessions/)
 * via buildSessionStatus: LIVE badge with the tab's TTY, plus summary, slug,
 * git info, keywords and recent messages per session.
 */

const os = require('os');
const utils = require(os.homedir() + '/.claude/lib/tracker-utils.js');

const args = process.argv.slice(2);
let here = false, vsCodeOnly = false, limit = utils.MAX_SESSIONS;
for (let i = 0; i < args.length; i++) {
  const a = args[i].toLowerCase();
  if (a === '--here') here = true;
  else if (a === '--vscode' || a === 'vscode') vsCodeOnly = true;
  else if (a === '--limit' && args[i + 1]) limit = parseInt(args[++i], 10) || limit;
  else if (a === '--help' || a === '-h') {
    console.log('Usage: node list-sessions.js [--here] [--limit N] [--vscode]');
    process.exit(0);
  }
}

async function main() {
  const cwd = process.cwd();
  const allFiles = here ? utils.getSessionsForPath(cwd) : utils.getAllSessionFiles();

  if (allFiles.length === 0) {
    console.log(here
      ? '\x1b[33mNo Claude sessions found for this directory.\x1b[0m\n\x1b[90mPath: ' + cwd + '\x1b[0m'
      : 'No Claude sessions found.');
    return;
  }

  const { sessions, runningCount, inactiveCount, vsCodeCount } = utils.buildSessionStatus(allFiles, {
    vsCodeOnly,
    maxSessions: limit,
  });

  const title = here ? 'SESSIONS FOR: ' + cwd.split('/').pop()
    : vsCodeOnly ? 'SESSIONS IN VS CODE WORKSPACES' : 'CLAUDE CODE SESSIONS';
  const rule = '\x1b[1m\x1b[36m═══════════════════════════════════════════════════════════════\x1b[0m';
  console.log('\n' + rule);
  console.log('\x1b[1m\x1b[36m' + ' '.repeat(Math.max(0, Math.floor((63 - title.length) / 2))) + title + '\x1b[0m');
  console.log(rule);
  let headerLine = '\x1b[90m  ' + runningCount + ' live, ' + inactiveCount + ' inactive';
  if (vsCodeCount) headerLine += '  |  ' + vsCodeCount + ' in VS Code';
  if (here) headerLine += '\n  Path: ' + cwd;
  console.log(headerLine + '\x1b[0m\n');

  for (let i = 0; i < sessions.length; i++) {
    const file = sessions[i];
    const session = await utils.parseSession(file.filePath, { projectPath: file.projectPath });
    if (!session) continue;

    const projectName = file.projectPath.split('/').pop();
    const statusBadge = file.isRunning
      ? '\x1b[42m\x1b[30m LIVE' + (file.tty ? ' ' + file.tty.replace('ttys', 's') : '') + ' \x1b[0m'
      : '\x1b[100m INACTIVE \x1b[0m';
    const vsCodeBadge = file.isInVSCode ? ' \x1b[44m\x1b[37m VS CODE \x1b[0m' : '';

    console.log('\x1b[33m[' + (i + 1) + ']\x1b[0m \x1b[1m' + projectName + '\x1b[0m  ' + statusBadge + vsCodeBadge);

    if (file.liveName) console.log('    \x1b[90mName:\x1b[0m \x1b[1m\x1b[35m' + file.liveName + '\x1b[0m');
    if (session.sessionSummary) console.log('    \x1b[90mSummary:\x1b[0m \x1b[1m' + session.sessionSummary + '\x1b[0m');
    if (session.sessionSlug) console.log('    \x1b[90mSession:\x1b[0m ' + session.sessionSlug);

    if (!here) console.log('    \x1b[90mPath:\x1b[0m ' + file.projectPath);
    if (session.gitRemote) console.log('    \x1b[90mRepo:\x1b[0m \x1b[34m' + session.gitRemote + '\x1b[0m');
    if (session.gitBranch) console.log('    \x1b[90mBranch:\x1b[0m \x1b[35m' + session.gitBranch + '\x1b[0m');

    // Repos touched from git-tracking (cross-directory awareness)
    const repos = utils.getReposForSession(session.fullId);
    const repoEntries = Object.entries(repos);
    if (repoEntries.length > 0) {
      const repoStrs = repoEntries.map(([rpath, rdata]) => {
        const name = rpath.split('/').pop();
        const branch = (rdata.branches || [])[0] || '';
        const commits = (rdata.commits || []).length;
        let s = name;
        if (branch) s += '/' + branch;
        if (commits) s += ' (' + commits + ' commit' + (commits > 1 ? 's' : '') + ')';
        return s;
      });
      console.log('    \x1b[90mRepos touched:\x1b[0m \x1b[33m' + repoStrs.join('\x1b[0m, \x1b[33m') + '\x1b[0m');
    }

    const lastMsgTime = session.lastUserTimestamp
      ? utils.formatAge(session.lastUserTimestamp)
      : utils.formatAge(session.timestamp);
    console.log('    \x1b[90mLast user message:\x1b[0m ' + lastMsgTime);
    console.log('    \x1b[90mSession ID:\x1b[0m ' + session.fullId);

    if (session.keywords.length > 0) {
      console.log('    \x1b[90mKeywords:\x1b[0m \x1b[36m' + session.keywords.join('\x1b[0m, \x1b[36m') + '\x1b[0m');
    }
    if (session.userMessages.length > 0) {
      console.log('    \x1b[90mRecent messages:\x1b[0m');
      session.userMessages.forEach((msg, j) => {
        console.log('      \x1b[32m' + (j + 1) + '.\x1b[0m ' + msg.substring(0, 70) + (msg.length > 70 ? '...' : ''));
      });
    }
    console.log('');
  }

  console.log('\x1b[90m───────────────────────────────────────────────────────────────\x1b[0m');
  console.log('\x1b[90mResume in this terminal:\x1b[0m claude --resume <session-id|name>');
  console.log('\x1b[90mResume in a new Ghostty tab:\x1b[0m ~/.claude/scripts/ghostty-resume.sh <session-id>');
  console.log('\x1b[90mCrashed sessions:\x1b[0m claude-tracker-resume [--open]');
  console.log('');
}

main().catch(console.error);
