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

/**
 * Extract enriched session metadata (model, tokens, turns, duration) from JSONL.
 * Reads head (first 100 lines) for model/version and tail (last 300 lines) for
 * usage stats. Efficient — does not read the full file.
 */
function parseSessionEnriched(filePath) {
  let model = '';
  let version = '';
  let totalInputTokens = 0;
  let totalOutputTokens = 0;
  let cacheReadTokens = 0;
  let cacheCreationTokens = 0;
  let numTurns = 0;
  let totalDurationMs = 0;
  let totalCostUsd = 0;
  let isWorktree = false;

  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');

    // Head: first 100 lines for model/version
    const headEnd = Math.min(100, lines.length);
    for (let i = 0; i < headEnd; i++) {
      if (!lines[i]) continue;
      try {
        const obj = JSON.parse(lines[i]);
        if (obj.type === 'assistant' && !model) {
          const msg = obj.message || {};
          model = msg.model || '';
          version = obj.version || '';
        }
        if (model) break;
      } catch (e) { /* skip */ }
    }

    // Tail: last 300 lines for usage/turns/duration/cost
    const tailStart = Math.max(0, lines.length - 300);
    const seenMsgIds = new Set();

    for (let i = tailStart; i < lines.length; i++) {
      if (!lines[i]) continue;
      try {
        const obj = JSON.parse(lines[i]);

        if (obj.type === 'assistant') {
          const msg = obj.message || {};
          if (!model && msg.model) model = msg.model;
          const usage = msg.usage || {};
          if (usage.output_tokens) {
            totalInputTokens += usage.input_tokens || 0;
            totalOutputTokens += usage.output_tokens || 0;
            cacheReadTokens += usage.cache_read_input_tokens || 0;
            cacheCreationTokens += usage.cache_creation_input_tokens || 0;
          }
          if (msg.id && !seenMsgIds.has(msg.id)) {
            seenMsgIds.add(msg.id);
          }
        }

        if (obj.type === 'system' && obj.subtype === 'turn_duration') {
          numTurns++;
          totalDurationMs += obj.durationMs || 0;
        }

        // Cost from result messages
        if (obj.type === 'result' && obj.total_cost_usd) {
          totalCostUsd = obj.total_cost_usd; // Last result has cumulative cost
        }
        // Also check costUsd field (alternative format)
        if (obj.costUsd) {
          totalCostUsd = Math.max(totalCostUsd, obj.costUsd);
        }
      } catch (e) { /* skip */ }
    }
  } catch (e) {
    // File read error
  }

  // Detect git worktree from project path
  // Extract project path from first line's cwd field
  try {
    const firstLine = fs.readFileSync(filePath, 'utf-8').split('\n')[0];
    if (firstLine) {
      const obj = JSON.parse(firstLine);
      const cwd = obj.cwd || '';
      if (cwd) {
        const gitDir = execSync('git -C "' + cwd.replace(/"/g, '\\"') + '" rev-parse --git-dir 2>/dev/null || true', {
          encoding: 'utf8',
          timeout: 3000
        }).trim();
        isWorktree = gitDir.includes('/worktrees/');
      }
    }
  } catch (e) { /* git check failed */ }

  // Shorten model name for display
  const modelShort = model
    .replace('claude-opus-4-6', 'opus-4.6')
    .replace('claude-opus-4-5-20251101', 'opus-4.5')
    .replace('claude-sonnet-4-5-20250929', 'sonnet-4.5')
    .replace('claude-haiku-4-5-20251001', 'haiku-4.5')
    .replace(/^claude-/, '');

  return {
    model,
    modelShort,
    version,
    totalInputTokens,
    totalOutputTokens,
    cacheReadTokens,
    cacheCreationTokens,
    numTurns,
    totalDurationMs,
    totalCostUsd,
    isWorktree,
  };
}

// ---------------------------------------------------------------------------
// Git Tracking Integration
// ---------------------------------------------------------------------------

const GIT_TRACKING_INDEX = path.join(os.homedir(), '.claude', 'git-tracking-index.json');
const GIT_TRACKING_LOG = path.join(os.homedir(), '.claude', 'git-tracking.jsonl');

/**
 * Load the git tracking index (bidirectional session <-> repo mapping).
 */
function loadGitTracking() {
  try {
    return JSON.parse(fs.readFileSync(GIT_TRACKING_INDEX, 'utf-8'));
  } catch (e) {
    return { version: 1, sessions: {}, repo_index: {} };
  }
}

/**
 * Get all session IDs that touched a given repo path.
 */
function getSessionsForRepo(repoPath) {
  const tracking = loadGitTracking();
  const normalized = path.resolve(repoPath);
  return tracking.repo_index[normalized] || [];
}

/**
 * Get all repos touched by a given session (keyed by repo path).
 */
function getReposForSession(sessionId) {
  if (!sessionId) return {};
  const tracking = loadGitTracking();
  // Try full ID first, then short ID prefix match
  let session = tracking.sessions[sessionId];
  if (!session) {
    const shortId = sessionId.substring(0, 8);
    for (const [sid, sdata] of Object.entries(tracking.sessions)) {
      if (sid.startsWith(shortId) || sdata.short_id === shortId) {
        session = sdata;
        break;
      }
    }
  }
  return session ? session.repos : {};
}

/**
 * Get recent git commits across all sessions, sorted by timestamp (newest first).
 * @param {Object} options - { hours: 24, repoPath: null }
 */
function getRecentCommits(options = {}) {
  const { hours = 24, repoPath = null } = options;
  const tracking = loadGitTracking();
  const cutoff = new Date(Date.now() - hours * 3600000).toISOString();
  const commits = [];

  for (const [sid, session] of Object.entries(tracking.sessions)) {
    for (const [repo, repoData] of Object.entries(session.repos || {})) {
      if (repoPath && path.resolve(repo) !== path.resolve(repoPath)) continue;
      for (const commit of (repoData.commits || [])) {
        if (commit.ts >= cutoff) {
          commits.push({
            ...commit,
            sessionId: sid,
            sessionShort: session.short_id,
            repo,
            remote: repoData.remote
          });
        }
      }
    }
  }

  commits.sort((a, b) => b.ts.localeCompare(a.ts));
  return commits;
}

/**
 * Read recent git events directly from the JSONL log (for timeline display).
 * @param {Object} options - { hours: 24, maxEvents: 50 }
 */
function getRecentGitEvents(options = {}) {
  const { hours = 24, maxEvents = 50 } = options;
  const cutoff = new Date(Date.now() - hours * 3600000).toISOString();

  if (!fs.existsSync(GIT_TRACKING_LOG)) return [];

  const events = [];
  try {
    const content = fs.readFileSync(GIT_TRACKING_LOG, 'utf-8');
    const lines = content.trim().split('\n').reverse(); // newest first
    for (const line of lines) {
      if (!line) continue;
      try {
        const event = JSON.parse(line);
        if (event.ts && event.ts >= cutoff) {
          events.push(event);
          if (events.length >= maxEvents) break;
        } else if (event.ts && event.ts < cutoff) {
          break; // JSONL is chronological, so we can stop
        }
      } catch (e) { continue; }
    }
  } catch (e) { /* file read error */ }

  return events;
}

>>>>>>> 7b90106 (feat: cross-repo git tracking hooks, session-report command, slack daemon, terminal title v2)
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
  loadSummaryCache,
  parseSessionEnriched,

  // Git tracking
  GIT_TRACKING_INDEX,
  GIT_TRACKING_LOG,
  loadGitTracking,
  getSessionsForRepo,
  getReposForSession,
  getRecentCommits,
  getRecentGitEvents
};
