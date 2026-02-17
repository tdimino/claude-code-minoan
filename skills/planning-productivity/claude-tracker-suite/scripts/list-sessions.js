#!/usr/bin/env node
/**
 * list-sessions.js — List recent Claude Code sessions with status badges
 *
 * Usage: node list-sessions.js [vscode]
 *
 * Shows recent sessions with RUNNING/INACTIVE status, VS Code badges,
 * summaries, slugs, git info, keywords, and recent messages.
 */

const os = require('os');
const utils = require(os.homedir() + '/.claude/lib/tracker-utils.js');

const VSCODE_ONLY = process.argv.slice(2).some(a => a.toLowerCase() === 'vscode');

async function main() {
  const allFiles = utils.getAllSessionFiles();

  if (allFiles.length === 0) {
    console.log('No Claude sessions found.');
    return;
  }

  const { sessions, runningCount, inactiveCount, vsCodeCount } = utils.buildSessionStatus(allFiles, {
    vsCodeOnly: VSCODE_ONLY,
    maxSessions: utils.MAX_SESSIONS,
  });

  // Header
  console.log('\n\x1b[1m\x1b[36m═══════════════════════════════════════════════════════════════\x1b[0m');
  if (VSCODE_ONLY) {
    console.log('\x1b[1m\x1b[36m               VS CODE SESSIONS (Crash Recovery)               \x1b[0m');
  } else {
    console.log('\x1b[1m\x1b[36m                    CLAUDE CODE SESSIONS                        \x1b[0m');
  }
  console.log('\x1b[1m\x1b[36m═══════════════════════════════════════════════════════════════\x1b[0m');

  if (VSCODE_ONLY) {
    console.log('\x1b[90m  Showing ' + sessions.length + ' sessions from VS Code workspaces\x1b[0m');
    console.log('\x1b[33m  Resume commands listed below for each session\x1b[0m\n');
  } else {
    console.log('\x1b[90m  ' + runningCount + ' running, ' + inactiveCount + ' inactive  |  ' + vsCodeCount + ' in VS Code\x1b[0m\n');
  }

  for (let i = 0; i < sessions.length; i++) {
    const file = sessions[i];
    const session = await utils.parseSession(file.filePath, { projectPath: file.projectPath });
    if (!session) continue;

    const projectName = file.projectPath.split('/').pop();
    const statusBadge = file.isRunning
      ? '\x1b[42m\x1b[30m RUNNING \x1b[0m'
      : '\x1b[100m INACTIVE \x1b[0m';
    const vsCodeBadge = file.isInVSCode
      ? ' \x1b[44m\x1b[37m VS CODE \x1b[0m'
      : '';

    console.log('\x1b[33m[' + (i + 1) + ']\x1b[0m \x1b[1m' + projectName + '\x1b[0m  ' + statusBadge + vsCodeBadge);

    if (session.sessionSummary) {
      console.log('    \x1b[90mSummary:\x1b[0m \x1b[1m' + session.sessionSummary + '\x1b[0m');
    }
    if (session.sessionSlug) {
      console.log('    \x1b[90mSession:\x1b[0m ' + session.sessionSlug);
    }

    console.log('    \x1b[90mPath:\x1b[0m ' + file.projectPath);
    if (session.gitRemote) console.log('    \x1b[90mRepo:\x1b[0m \x1b[34m' + session.gitRemote + '\x1b[0m');
    if (session.gitBranch) console.log('    \x1b[90mBranch:\x1b[0m \x1b[35m' + session.gitBranch + '\x1b[0m');

    const lastMsgTime = session.lastUserTimestamp
      ? utils.formatAge(session.lastUserTimestamp)
      : utils.formatAge(session.timestamp);
    console.log('    \x1b[90mLast user message:\x1b[0m ' + lastMsgTime);

    if (VSCODE_ONLY) {
      console.log('    \x1b[32m→ claude --resume ' + session.fullId + '\x1b[0m');
    } else {
      console.log('    \x1b[90mSession ID:\x1b[0m ' + session.fullId);
    }

    if (!VSCODE_ONLY && session.keywords.length > 0) {
      console.log('    \x1b[90mKeywords:\x1b[0m \x1b[36m' + session.keywords.join('\x1b[0m, \x1b[36m') + '\x1b[0m');
    }

    if (!VSCODE_ONLY && session.userMessages.length > 0) {
      console.log('    \x1b[90mRecent messages:\x1b[0m');
      session.userMessages.forEach((msg, j) => {
        console.log('      \x1b[32m' + (j + 1) + '.\x1b[0m ' + msg.substring(0, 70) + (msg.length > 70 ? '...' : ''));
      });
    }
    console.log('');
  }

  console.log('\x1b[90m───────────────────────────────────────────────────────────────\x1b[0m');
  if (VSCODE_ONLY) {
    console.log('\x1b[90mCopy a resume command above and run it in the appropriate terminal.\x1b[0m');
  } else {
    console.log('\x1b[90mTo resume a session:\x1b[0m claude --resume <session-id>');
    console.log('\x1b[90mTo continue most recent:\x1b[0m claude --continue');
    console.log('\x1b[90mFor crash recovery:\x1b[0m /claude-tracker vscode');
  }
  console.log('');
}

main().catch(console.error);
