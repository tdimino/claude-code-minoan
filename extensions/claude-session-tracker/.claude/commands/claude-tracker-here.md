# Claude Sessions for Current Directory

List Claude sessions for the current project only.

## Instructions

```bash
node -e "
const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const cwd = process.cwd();

// Encode path like Claude does
const encodedPath = cwd.replace(/\\//g, '-');
const projectDir = path.join(PROJECTS_DIR, encodedPath);

async function parseSession(filePath) {
  return new Promise((resolve) => {
    const sessionId = path.basename(filePath, '.jsonl');
    let timestamp = '';
    let gitBranch = '';
    const userMessages = [];

    const stream = fs.createReadStream(filePath);
    const rl = readline.createInterface({ input: stream, crlfDelay: Infinity });

    let lineCount = 0;

    rl.on('line', (line) => {
      lineCount++;
      if (lineCount > 200) { rl.close(); return; }

      try {
        const data = JSON.parse(line);
        if (!timestamp && data.timestamp) timestamp = data.timestamp;
        if (!gitBranch && data.gitBranch) gitBranch = data.gitBranch;

        if (data.type === 'user' && data.message?.content) {
          const content = data.message.content;
          if (!content.includes('<observed_from_primary_session>') &&
              !content.includes('MEMORY PROCESSING') &&
              content.length < 500) {
            userMessages.push(content.substring(0, 100).replace(/\\n/g, ' '));
          }
        }
      } catch {}
    });

    rl.on('close', () => {
      stream.destroy();
      resolve({ sessionId, timestamp, gitBranch, userMessages: userMessages.slice(-3) });
    });

    rl.on('error', () => { stream.destroy(); resolve(null); });
  });
}

function formatAge(isoDate) {
  if (!isoDate) return 'unknown';
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return mins + 'm ago';
  const hours = Math.floor(mins / 60);
  if (hours < 24) return hours + 'h ago';
  return Math.floor(hours / 24) + 'd ago';
}

async function main() {
  console.log('\\n\\x1b[1m\\x1b[36mSessions for:\\x1b[0m ' + cwd + '\\n');

  if (!fs.existsSync(projectDir)) {
    console.log('\\x1b[33mNo sessions found for this directory.\\x1b[0m');
    console.log('\\x1b[90mLooking in: ' + projectDir + '\\x1b[0m\\n');
    return;
  }

  const files = fs.readdirSync(projectDir)
    .filter(f => f.endsWith('.jsonl'))
    .map(f => {
      const filePath = path.join(projectDir, f);
      const stat = fs.statSync(filePath);
      return { filePath, mtime: stat.mtime.getTime() };
    })
    .filter(f => f.mtime)
    .sort((a, b) => b.mtime - a.mtime)
    .slice(0, 10);

  if (files.length === 0) {
    console.log('\\x1b[33mNo sessions found.\\x1b[0m\\n');
    return;
  }

  for (let i = 0; i < files.length; i++) {
    const session = await parseSession(files[i].filePath);
    if (!session) continue;

    const age = formatAge(session.timestamp);

    console.log('\\x1b[33m[' + (i + 1) + ']\\x1b[0m \\x1b[90m' + age + '\\x1b[0m' + (session.gitBranch ? ' \\x1b[35m(' + session.gitBranch + ')\\x1b[0m' : ''));
    console.log('    \\x1b[90mID:\\x1b[0m ' + session.sessionId);

    if (session.userMessages.length > 0) {
      session.userMessages.forEach((msg, j) => {
        console.log('    \\x1b[32m›\\x1b[0m ' + msg.substring(0, 60) + (msg.length > 60 ? '...' : ''));
      });
    }
    console.log('');
  }

  console.log('\\x1b[90mResume: claude --resume <session-id>\\x1b[0m');
  console.log('\\x1b[90mContinue last: claude --continue\\x1b[0m\\n');
}

main().catch(console.error);
"
```
