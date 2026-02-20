# Claude Sessions for Current Directory

List Claude Code sessions for the current working directory.

## Instructions

```bash
node -e "
const os = require('os');
const path = require('path');
const utils = require(os.homedir() + '/.claude/lib/tracker-utils.js');

async function main() {
  const cwd = process.cwd();
  const sessions = utils.getSessionsForPath(cwd);

  if (sessions.length === 0) {
    console.log('\\x1b[33mNo Claude sessions found for this directory.\\x1b[0m');
    console.log('\\x1b[90mPath: ' + cwd + '\\x1b[0m');
    return;
  }

  // Get status info
  const { sessions: sessionsWithStatus, runningCount, inactiveCount, vsCodeCount } = utils.buildSessionStatus(sessions, {
    maxSessions: utils.MAX_SESSIONS
  });

  const projectName = cwd.split('/').pop();

  // Header
  console.log('\\n\\x1b[1m\\x1b[36m═══════════════════════════════════════════════════════════════\\x1b[0m');
  console.log('\\x1b[1m\\x1b[36m              SESSIONS FOR: ' + projectName + '\\x1b[0m');
  console.log('\\x1b[1m\\x1b[36m═══════════════════════════════════════════════════════════════\\x1b[0m');
  console.log('\\x1b[90m  ' + runningCount + ' running, ' + inactiveCount + ' inactive  |  ' + vsCodeCount + ' in VS Code\\x1b[0m');
  console.log('\\x1b[90m  Path: ' + cwd + '\\x1b[0m\\n');

  for (let i = 0; i < sessionsWithStatus.length; i++) {
    const file = sessionsWithStatus[i];
    const session = await utils.parseSession(file.filePath, { projectPath: file.projectPath });
    if (!session) continue;

    const statusBadge = file.isRunning
      ? '\\x1b[42m\\x1b[30m RUNNING \\x1b[0m'
      : '\\x1b[100m INACTIVE \\x1b[0m';
    const vsCodeBadge = file.isInVSCode
      ? ' \\x1b[44m\\x1b[37m VS CODE \\x1b[0m'
      : '';

    console.log('\\x1b[33m[' + (i + 1) + ']\\x1b[0m ' + statusBadge + vsCodeBadge);

    // Show summary (descriptive) if available
    if (session.sessionSummary) {
      console.log('    \\x1b[90mSummary:\\x1b[0m \\x1b[1m' + session.sessionSummary + '\\x1b[0m');
    }
    if (session.sessionSlug) {
      console.log('    \\x1b[90mSession:\\x1b[0m ' + session.sessionSlug);
    }

    if (session.gitRemote) {
      console.log('    \\x1b[90mRepo:\\x1b[0m \\x1b[34m' + session.gitRemote + '\\x1b[0m');
    }
    if (session.gitBranch) {
      console.log('    \\x1b[90mBranch:\\x1b[0m \\x1b[35m' + session.gitBranch + '\\x1b[0m');
    }

    const lastMsgTime = session.lastUserTimestamp ? utils.formatAge(session.lastUserTimestamp) : utils.formatAge(session.timestamp);
    console.log('    \\x1b[90mLast user message:\\x1b[0m ' + lastMsgTime);
    console.log('    \\x1b[90mSession ID:\\x1b[0m ' + session.fullId);

    if (session.keywords.length > 0) {
      console.log('    \\x1b[90mKeywords:\\x1b[0m \\x1b[36m' + session.keywords.join('\\x1b[0m, \\x1b[36m') + '\\x1b[0m');
    }

    if (session.userMessages.length > 0) {
      console.log('    \\x1b[90mRecent messages:\\x1b[0m');
      session.userMessages.forEach((msg, j) => {
        console.log('      \\x1b[32m' + (j + 1) + '.\\x1b[0m ' + msg.substring(0, 70) + (msg.length > 70 ? '...' : ''));
      });
    }
    console.log('');
  }

  console.log('\\x1b[90m───────────────────────────────────────────────────────────────\\x1b[0m');
  console.log('\\x1b[90mTo resume a session:\\x1b[0m claude --resume <session-id>');
  console.log('\\x1b[90mTo continue most recent:\\x1b[0m claude --continue');
  console.log('');
}

main().catch(console.error);
"
```

Shows all Claude sessions for the current working directory with:
- **Status badge** (RUNNING or INACTIVE)
- **VS CODE badge** (if open in VS Code)
- **Session summary** (AI-generated description)
- **Session name** (slug)
- **Git remote** (primary repo URL)
- Git branch (if available)
- Last user message time
- Session ID (for `claude --resume`)
- Keywords extracted from conversation
- Last 3 user messages

Useful for seeing session history in a specific project.
