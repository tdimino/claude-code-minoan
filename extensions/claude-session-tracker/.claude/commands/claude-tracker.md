# Claude Session Tracker

List and browse your saved Claude Code sessions with status (running/inactive).

## Instructions

```bash
node -e "
const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');
const { execSync } = require('child_process');

const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const MAX_SESSIONS = 20;
const MAX_MESSAGES = 3;

// Common words to filter out from keywords
const STOP_WORDS = new Set(['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom', 'its', 'it', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'they', 'them', 'their', 'image', 'file', 'please', 'like', 'want', 'need', 'make', 'use', 'using', 'used', 'also', 'get', 'let', 'see', 'look', 'know', 'think', 'new', 'now', 'one', 'two', 'first', 'last', 'well', 'way', 'even', 'back', 'any', 'give', 'day', 'come', 'take', 'made', 'find', 'work', 'part', 'over', 'such', 'good', 'year', 'out', 'about', 'right', 'still', 'try', 'tell', 'call', 'keep', 'put', 'end', 'does', 'set', 'say', 'help']);

// Get running Claude processes and their working directories
function getRunningClaudeSessions() {
  const cwds = new Set();
  const homeDir = os.homedir();
  try {
    // Get all Claude process PIDs
    const pidsResult = execSync('pgrep -f claude 2>/dev/null || true', { encoding: 'utf8' });
    const pids = pidsResult.trim().split('\\n').filter(p => p && /^\\d+$/.test(p));

    // For each PID, get its cwd using lsof
    for (const pid of pids) {
      try {
        const lsofResult = execSync('lsof -p ' + pid + ' 2>/dev/null | grep cwd || true', { encoding: 'utf8' });
        // lsof format: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
        // Example: "node 7583 user cwd DIR 1,17 3296 275187 /Users/jane"
        const match = lsofResult.match(/(\\/[^\\n]+)$/m);
        if (match && match[1]) {
          const cwd = match[1].trim();
          // Filter out non-project dirs (home dir, .claude internal dirs)
          if (cwd !== homeDir &&
              !cwd.startsWith(homeDir + '/.claude/') &&
              !cwd.includes('/plugins/cache/')) {
            cwds.add(cwd);
          }
        }
      } catch {}
    }
  } catch {}
  return cwds;
}

function extractKeywords(messages) {
  const wordCounts = {};
  const text = messages.join(' ').toLowerCase();
  const words = text.match(/[a-z]{4,}/g) || [];

  words.forEach(word => {
    if (!STOP_WORDS.has(word)) {
      wordCounts[word] = (wordCounts[word] || 0) + 1;
    }
  });

  return Object.entries(wordCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([word]) => word);
}

async function parseSession(filePath) {
  return new Promise((resolve) => {
    const sessionId = path.basename(filePath, '.jsonl');
    let timestamp = '';
    let gitBranch = '';
    const userMessages = [];
    const allText = [];

    const stream = fs.createReadStream(filePath);
    const rl = readline.createInterface({ input: stream, crlfDelay: Infinity });

    let lineCount = 0;

    rl.on('line', (line) => {
      lineCount++;
      if (lineCount > 300) { rl.close(); return; }

      try {
        const data = JSON.parse(line);
        if (!timestamp && data.timestamp) timestamp = data.timestamp;
        if (!gitBranch && data.gitBranch) gitBranch = data.gitBranch;

        if (data.type === 'user' && data.message?.content) {
          const content = data.message.content;
          if (!content.includes('<observed_from_primary_session>') &&
              !content.includes('MEMORY PROCESSING') &&
              !content.startsWith('<') &&
              content.length < 500) {
            userMessages.push(content.substring(0, 100).replace(/\\n/g, ' '));
            allText.push(content);
          }
        }
      } catch {}
    });

    rl.on('close', () => {
      stream.destroy();
      resolve({
        id: sessionId.substring(0, 8),
        fullId: sessionId,
        timestamp,
        gitBranch,
        userMessages: userMessages.slice(-MAX_MESSAGES),
        keywords: extractKeywords(allText),
        filePath
      });
    });

    rl.on('error', () => { stream.destroy(); resolve(null); });
  });
}

function decodeProjectPath(dirName) {
  // Claude encodes: leading / -> -, all / -> -, space -> -
  // But we can't distinguish space from / from literal -, so we keep as-is for display
  // For matching, we'll normalize both paths
  return dirName.replace(/^-/, '/').replace(/-/g, '/');
}

function pathToKey(p) {
  // Convert path to comparison key: lowercase, replace spaces and slashes with dashes
  return p.toLowerCase().replace(/[\\/\\s]+/g, '-').replace(/^-/, '').replace(/-+/g, '-');
}

function isPathMatch(projectDirName, runningPath) {
  // projectDirName: -Users-jane-Desktop-Aldea-Prompt-development-Aldea-Soul-Engine
  // runningPath: /Users/jane/Desktop/Aldea/Prompt development/Aldea-Soul-Engine
  const projectKey = projectDirName.toLowerCase().replace(/^-/, '');
  const runningKey = pathToKey(runningPath);
  return projectKey === runningKey;
}

function formatAge(isoDate) {
  if (!isoDate) return 'unknown';
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return mins + 'm ago';
  const hours = Math.floor(mins / 60);
  if (hours < 24) return hours + 'h ago';
  const days = Math.floor(hours / 24);
  return days + 'd ago';
}

async function main() {
  if (!fs.existsSync(PROJECTS_DIR)) {
    console.log('No Claude sessions found.');
    return;
  }

  // Get running sessions first
  const runningDirs = getRunningClaudeSessions();

  const projectDirs = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => ({ name: d.name, path: path.join(PROJECTS_DIR, d.name) }));

  const allFiles = [];

  for (const dir of projectDirs) {
    try {
      const files = fs.readdirSync(dir.path).filter(f => f.endsWith('.jsonl'));
      for (const f of files) {
        const filePath = path.join(dir.path, f);
        const stat = fs.statSync(filePath);
        if (stat.size > 0) {
          allFiles.push({
            filePath,
            projectDir: dir.name,
            mtime: stat.mtime.getTime()
          });
        }
      }
    } catch {}
  }

  allFiles.sort((a, b) => b.mtime - a.mtime);
  const recent = allFiles.slice(0, MAX_SESSIONS);

  // Count running vs inactive
  let runningCount = 0;
  let inactiveCount = 0;

  const sessionsWithStatus = [];
  for (const file of recent) {
    const projectPath = decodeProjectPath(file.projectDir);
    // Check if any running dir matches this project
    let isRunning = false;
    for (const runDir of runningDirs) {
      if (isPathMatch(file.projectDir, runDir)) {
        isRunning = true;
        break;
      }
    }
    if (isRunning) runningCount++; else inactiveCount++;
    sessionsWithStatus.push({ ...file, projectPath, isRunning });
  }

  console.log('\\n\\x1b[1m\\x1b[36m═══════════════════════════════════════════════════════════════\\x1b[0m');
  console.log('\\x1b[1m\\x1b[36m                    CLAUDE CODE SESSIONS                        \\x1b[0m');
  console.log('\\x1b[1m\\x1b[36m═══════════════════════════════════════════════════════════════\\x1b[0m');
  console.log('\\x1b[90m  ' + runningCount + ' running, ' + inactiveCount + ' inactive\\x1b[0m\\n');

  for (let i = 0; i < sessionsWithStatus.length; i++) {
    const file = sessionsWithStatus[i];
    const session = await parseSession(file.filePath);
    if (!session) continue;

    const projectName = file.projectPath.split('/').pop();
    const age = formatAge(session.timestamp);
    const statusBadge = file.isRunning
      ? '\\x1b[42m\\x1b[30m RUNNING \\x1b[0m'
      : '\\x1b[100m INACTIVE \\x1b[0m';

    console.log('\\x1b[33m[' + (i + 1) + ']\\x1b[0m \\x1b[1m' + projectName + '\\x1b[0m  ' + statusBadge);
    console.log('    \\x1b[90mPath:\\x1b[0m ' + file.projectPath);
    if (session.gitBranch) console.log('    \\x1b[90mBranch:\\x1b[0m \\x1b[35m' + session.gitBranch + '\\x1b[0m');
    console.log('    \\x1b[90mLast active:\\x1b[0m ' + age);
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

Lists your 20 most recent Claude sessions with:
- **Status badge** (RUNNING or INACTIVE)
- Project name and path
- Git branch (if available)
- Last active time
- Session ID (for `claude --resume`)
- **Keywords** extracted from conversation
- Last 3 user messages

Running sessions detected via `lsof` checking for Claude processes.
