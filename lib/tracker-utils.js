/**
 * Shared utilities for claude-tracker family of commands
 * Used by: claude-tracker, claude-tracker-here, claude-tracker-search, claude-tracker-resume
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');
const { execSync } = require('child_process');

// Constants
const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const IDE_DIR = path.join(os.homedir(), '.claude', 'ide');
const MAX_SESSIONS = 20;
const MAX_MESSAGES = 3;
const MAX_LINES_PER_FILE = 500;
const EXEC_TIMEOUT_MS = 5000;

// Common words to filter out from keywords
const STOP_WORDS = new Set(['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom', 'its', 'it', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'they', 'them', 'their', 'image', 'file', 'please', 'like', 'want', 'need', 'make', 'use', 'using', 'used', 'also', 'get', 'let', 'see', 'look', 'know', 'think', 'new', 'now', 'one', 'two', 'first', 'last', 'well', 'way', 'even', 'back', 'any', 'give', 'day', 'come', 'take', 'made', 'find', 'work', 'part', 'over', 'such', 'good', 'year', 'out', 'about', 'right', 'still', 'try', 'tell', 'call', 'keep', 'put', 'end', 'does', 'set', 'say', 'help']);

/**
 * Get git remote URL for a project path
 */
function getGitRemote(projectPath) {
  if (!projectPath || !fs.existsSync(projectPath)) return null;

  try {
    const result = execSync('git -C "' + projectPath + '" remote get-url origin 2>/dev/null || true', {
      encoding: 'utf8',
      timeout: EXEC_TIMEOUT_MS
    }).trim();

    if (result && result.length > 0) {
      return result;
    }
  } catch (e) {
    // Git command failed or timed out
  }
  return null;
}

/**
 * Check if a process command is an actual Claude CLI session
 */
function isClaudeSession(cmd) {
  if (!cmd) return false;
  const lower = cmd.toLowerCase();
  return (
    lower.match(/\/claude(\s|$)/) ||
    lower.includes('anthropic.claude-code') ||
    (lower.includes('tmux') && lower.includes('claude'))
  );
}

/**
 * Get running Claude terminal sessions with timeout protection
 */
function getRunningClaudeSessions() {
  const cwds = new Set();
  const homeDir = os.homedir();

  // Platform check - lsof/pgrep are Unix-only
  if (process.platform === 'win32') {
    return cwds;
  }

  try {
    const pidsResult = execSync('pgrep -f claude 2>/dev/null || true', {
      encoding: 'utf8',
      timeout: EXEC_TIMEOUT_MS
    });
    const pids = pidsResult.trim().split('\n').filter(p => p && /^\d+$/.test(p));

    for (const pid of pids) {
      try {
        const cmdResult = execSync('ps -p ' + pid + ' -o command= 2>/dev/null || true', {
          encoding: 'utf8',
          timeout: EXEC_TIMEOUT_MS
        }).trim();
        if (!isClaudeSession(cmdResult)) continue;

        const lsofResult = execSync('lsof -p ' + pid + ' 2>/dev/null | grep cwd || true', {
          encoding: 'utf8',
          timeout: EXEC_TIMEOUT_MS
        });
        const match = lsofResult.match(/(\/[^\n]+)$/m);
        if (match && match[1]) {
          const cwd = match[1].trim();
          if (cwd !== homeDir && !cwd.startsWith(homeDir + '/.claude/')) {
            cwds.add(cwd);
          }
        }
      } catch (e) {
        // Timeout or other error - skip this PID
      }
    }
  } catch (e) {
    // pgrep failed or timed out
  }
  return cwds;
}

/**
 * Get VS Code workspace folders from IDE lock files
 */
function getVSCodeWorkspaces() {
  const workspaces = new Set();
  if (!fs.existsSync(IDE_DIR)) return workspaces;

  try {
    const files = fs.readdirSync(IDE_DIR).filter(f => f.endsWith('.lock'));
    for (const file of files) {
      try {
        const content = fs.readFileSync(path.join(IDE_DIR, file), 'utf-8');
        const data = JSON.parse(content);
        if (data.workspaceFolders && Array.isArray(data.workspaceFolders)) {
          data.workspaceFolders.forEach(folder => workspaces.add(folder));
        }
      } catch (e) {
        // Invalid lock file - skip
      }
    }
  } catch (e) {
    // Can't read IDE dir
  }

  return workspaces;
}

/**
 * Check if a project path is within any VS Code workspace
 */
function isInVSCodeWorkspace(projectPath, vsCodeWorkspaces) {
  for (const ws of vsCodeWorkspaces) {
    if (projectPath.startsWith(ws) || ws.startsWith(projectPath)) {
      return true;
    }
  }
  return false;
}

/**
 * Extract keywords from messages
 */
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

/**
 * Parse a session JSONL file and extract metadata
 */
function parseSession(filePath, options = {}) {
  const { maxMessages = MAX_MESSAGES, maxLines = MAX_LINES_PER_FILE, projectPath = null } = options;

  // Get git remote if projectPath provided
  const gitRemote = projectPath ? getGitRemote(projectPath) : null;

  return new Promise((resolve) => {
    const sessionId = path.basename(filePath, '.jsonl');
    let timestamp = '';
    let gitBranch = '';
    let sessionSlug = '';
    let sessionSummary = '';
    let lastUserTimestamp = '';
    const userMessages = [];
    const allText = [];

    let stream;
    let rl;
    let lineCount = 0;
    let resolved = false;

    const cleanup = () => {
      if (!resolved) {
        resolved = true;
        if (rl) rl.close();
        if (stream) stream.destroy();
      }
    };

    const resolveSession = () => {
      cleanup();
      resolve({
        id: sessionId.substring(0, 8),
        fullId: sessionId,
        timestamp,
        gitBranch,
        gitRemote,
        sessionSlug,
        sessionSummary,
        lastUserTimestamp,
        userMessages: userMessages.slice(-maxMessages),
        keywords: extractKeywords(allText),
        filePath
      });
    };

    try {
      stream = fs.createReadStream(filePath);
      rl = readline.createInterface({ input: stream, crlfDelay: Infinity });

      rl.on('line', (line) => {
        lineCount++;
        if (lineCount > maxLines) {
          resolveSession();
          return;
        }

        try {
          const data = JSON.parse(line);
          if (!timestamp && data.timestamp) timestamp = data.timestamp;
          if (!gitBranch && data.gitBranch) gitBranch = data.gitBranch;
          if (!sessionSlug && data.slug) sessionSlug = data.slug;

          // Extract AI-generated summary (last one wins - most recent)
          if (data.type === 'summary' && data.summary) {
            sessionSummary = data.summary;
          }

          if (data.type === 'user' && data.timestamp && !data.isMeta) {
            lastUserTimestamp = data.timestamp;
          }

          if (data.type === 'user' && data.message?.content) {
            const content = data.message.content;
            if (!content.includes('<observed_from_primary_session>') &&
                !content.includes('MEMORY PROCESSING') &&
                !content.startsWith('<') &&
                content.length < 500) {
              userMessages.push(content.substring(0, 100).replace(/\n/g, ' '));
              allText.push(content);
            }
          }
        } catch (e) {
          // Invalid JSON line - skip
        }
      });

      rl.on('close', resolveSession);
      rl.on('error', resolveSession);
      stream.on('error', resolveSession);
    } catch (e) {
      resolve(null);
    }
  });
}

/**
 * Decode project path from directory name.
 * Uses sessions-index.json as ground truth when available, since the
 * hyphen-encoded directory names are lossy (hyphens in real paths collide
 * with path separators). Falls back to filesystem heuristic.
 */
function decodeProjectPath(dirName) {
  // Try sessions-index.json first — has the real projectPath
  const indexPath = path.join(PROJECTS_DIR, dirName, 'sessions-index.json');
  try {
    const index = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
    if (index.entries && index.entries.length > 0 && index.entries[0].projectPath) {
      return index.entries[0].projectPath;
    }
  } catch (e) {
    // No index or unreadable — fall through
  }

  // Fallback: greedy filesystem walk
  return resolvePathHeuristic(dirName);
}

/**
 * Resolve an encoded directory name to a real path by walking the filesystem.
 * At each hyphen, prefer joining with hyphen if that directory exists,
 * otherwise split as a path separator.
 */
function resolvePathHeuristic(dirName) {
  const segments = dirName.replace(/^-/, '').split('-');
  let current = '/';

  for (let i = 0; i < segments.length; i++) {
    // Try joining this segment with hyphens to subsequent segments
    // and see which grouping matches a real directory
    let bestLen = 0;
    for (let j = i; j < segments.length; j++) {
      const candidate = segments.slice(i, j + 1).join('-');
      const testPath = path.join(current, candidate);
      try {
        if (fs.existsSync(testPath)) {
          bestLen = j - i + 1;
        }
      } catch (e) {
        // Permission error — stop extending
        break;
      }
    }

    if (bestLen > 0) {
      current = path.join(current, segments.slice(i, i + bestLen).join('-'));
      i += bestLen - 1; // -1 because loop increments
    } else {
      current = path.join(current, segments[i]);
    }
  }

  return current;
}

/**
 * Load all sessions-index.json files into a flat array of session entries.
 * Each entry is enriched with projectDir and projectName.
 */
function loadSessionsIndex() {
  if (!fs.existsSync(PROJECTS_DIR)) return [];

  const allSessions = [];
  const projectDirs = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory());

  for (const dir of projectDirs) {
    const indexPath = path.join(PROJECTS_DIR, dir.name, 'sessions-index.json');
    try {
      const index = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
      if (!index.entries || !Array.isArray(index.entries)) continue;

      const projectPath = (index.entries[0] && index.entries[0].projectPath)
        || decodeProjectPath(dir.name);
      const projectName = path.basename(projectPath);

      for (const entry of index.entries) {
        allSessions.push({
          ...entry,
          projectDir: dir.name,
          projectPath: entry.projectPath || projectPath,
          projectName
        });
      }
    } catch (e) {
      // No index or parse error — skip
    }
  }

  return allSessions;
}

/**
 * Load cached session summaries from llama-cli
 */
function loadSummaryCache() {
  const cachePath = path.join(os.homedir(), '.claude', 'session-summaries.json');
  try {
    return JSON.parse(fs.readFileSync(cachePath, 'utf-8'));
  } catch (e) {
    return {};
  }
}

/**
 * Convert path to comparison key
 */
function pathToKey(p) {
  return p.toLowerCase().replace(/[\/\s]+/g, '-').replace(/^-/, '').replace(/-+/g, '-');
}

/**
 * Check if project directory matches a running path
 */
function isPathMatch(projectDirName, runningPath) {
  const projectKey = projectDirName.toLowerCase().replace(/^-/, '');
  const runningKey = pathToKey(runningPath);
  return projectKey === runningKey;
}

/**
 * Format age from ISO date string
 */
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

/**
 * Escape regex special characters for safe regex construction
 */
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Get all session files sorted by modification time
 */
function getAllSessionFiles() {
  if (!fs.existsSync(PROJECTS_DIR)) {
    return [];
  }

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
    } catch (e) {
      // Can't read dir - skip
    }
  }

  allFiles.sort((a, b) => b.mtime - a.mtime);
  return allFiles;
}

/**
 * Get sessions for a specific directory path
 */
function getSessionsForPath(targetPath) {
  const allFiles = getAllSessionFiles();
  const normalizedTarget = pathToKey(targetPath);

  return allFiles.filter(file => {
    const projectKey = file.projectDir.toLowerCase().replace(/^-/, '');
    return projectKey === normalizedTarget;
  });
}

/**
 * Build session status (running, VS Code)
 */
function buildSessionStatus(files, options = {}) {
  const { vsCodeOnly = false, maxSessions = MAX_SESSIONS } = options;

  const runningDirs = getRunningClaudeSessions();
  const vsCodeWorkspaces = getVSCodeWorkspaces();

  let runningCount = 0;
  let inactiveCount = 0;
  let vsCodeCount = 0;

  const sessionsWithStatus = [];

  for (const file of files) {
    const projectPath = decodeProjectPath(file.projectDir);

    let isRunning = false;
    for (const runDir of runningDirs) {
      if (isPathMatch(file.projectDir, runDir)) {
        isRunning = true;
        break;
      }
    }

    const isInVSCode = isInVSCodeWorkspace(projectPath, vsCodeWorkspaces);

    // Filter for VS Code only mode
    if (vsCodeOnly && !isInVSCode) continue;

    if (isRunning) runningCount++; else inactiveCount++;
    if (isInVSCode) vsCodeCount++;

    sessionsWithStatus.push({ ...file, projectPath, isRunning, isInVSCode });

    if (sessionsWithStatus.length >= maxSessions) break;
  }

  return {
    sessions: sessionsWithStatus,
    runningCount,
    inactiveCount,
    vsCodeCount
  };
}

// Export all utilities
module.exports = {
  // Constants
  PROJECTS_DIR,
  IDE_DIR,
  MAX_SESSIONS,
  MAX_MESSAGES,
  MAX_LINES_PER_FILE,
  STOP_WORDS,

  // Functions
  getGitRemote,
  isClaudeSession,
  getRunningClaudeSessions,
  getVSCodeWorkspaces,
  isInVSCodeWorkspace,
  extractKeywords,
  parseSession,
  decodeProjectPath,
  resolvePathHeuristic,
  pathToKey,
  isPathMatch,
  formatAge,
  escapeRegex,
  getAllSessionFiles,
  getSessionsForPath,
  buildSessionStatus,
  loadSessionsIndex,
  loadSummaryCache
};
