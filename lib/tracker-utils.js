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
const _gitRemoteCache = new Map();   // projectPath → remote URL | null, per process
function getGitRemote(projectPath) {
  if (!projectPath) return null;
  if (_gitRemoteCache.has(projectPath)) return _gitRemoteCache.get(projectPath);

  let remote = null;
  if (fs.existsSync(projectPath)) {
    try {
      const result = execSync('git -C "' + projectPath + '" remote get-url origin 2>/dev/null || true', {
        encoding: 'utf8',
        timeout: EXEC_TIMEOUT_MS
      }).trim();
      if (result) remote = result;
    } catch (e) {
      // Git command failed or timed out
    }
  }
  _gitRemoteCache.set(projectPath, remote);
  return remote;
}

/**
 * Check if a process command is an actual Claude CLI session
 */
function isClaudeSession(cmd) {
  if (!cmd) return false;
  const lower = cmd.toLowerCase();
  // Claude Code's own helper processes share the binary name but are never
  // resumable sessions: background spares, the PTY host, the daemon
  if (/\bbg-spare\b|\bbg-pty-host\b|\bdaemon run\b/.test(lower)) return false;
  // Bare `claude --model …` (no path prefix) is the common modern invocation
  return (
    /(^|\/|\s)claude(\s|$)/.test(lower) ||
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

// ---------------------------------------------------------------------------
// Live sessions — the authoritative source is the PID file Claude Code writes
// to ~/.claude/sessions/<pid>.json ({pid, sessionId, cwd, kind, name, status,
// bridgeSessionId, ...}). One readdir + one `ps` pass, exact per session.
// getRunningClaudeSessions() above is only the fallback for machines whose
// Claude Code predates PID files.
// ---------------------------------------------------------------------------

const SESSIONS_DIR = path.join(os.homedir(), '.claude', 'sessions');

function isPidAlive(pid) {
  try { process.kill(pid, 0); return true; }
  catch (e) { return e.code === 'EPERM'; }
}

/** One `ps` pass: pid -> { tty, command } for every process (~20 ms). */
function getProcessTable() {
  const table = new Map();
  if (process.platform === 'win32') return table;
  try {
    const out = execSync('ps -axo pid=,tty=,command= 2>/dev/null || true', {
      encoding: 'utf8', timeout: EXEC_TIMEOUT_MS, maxBuffer: 16 * 1024 * 1024
    });
    for (const line of out.split('\n')) {
      const m = line.match(/^\s*(\d+)\s+(\S+)\s+(.*)$/);
      if (m) table.set(parseInt(m[1], 10), { tty: m[2] === '??' ? '' : m[2], command: m[3] });
    }
  } catch (e) { /* ps unavailable */ }
  return table;
}

/** Numeric sort key so ttys003 < ttys021 < ttys100; unknown TTYs sort last. */
function ttyOrder(tty) {
  const m = /(\d+)$/.exec(tty || '');
  return m ? parseInt(m[1], 10) : Number.POSITIVE_INFINITY;
}

const _liveCache = new Map();

/**
 * Live Claude Code sessions from PID files, TTY-ordered. Interactive only by
 * default; allKinds includes headless (-p) and background sessions. Cached
 * for the process lifetime unless refresh is set.
 * Returns [{ sessionId, pid, cwd, name, nameSource, status, kind, version,
 *            bridgeSessionId, tty, startedAt }]
 */
function getLiveSessions({ allKinds = false, refresh = false } = {}) {
  const key = allKinds ? 'all' : 'interactive';
  if (!refresh && _liveCache.has(key)) return _liveCache.get(key);

  const sessions = [];
  let files = [];
  try { files = fs.readdirSync(SESSIONS_DIR).filter(f => /^\d+\.json$/.test(f)); }
  catch (e) { /* no sessions dir */ }
  const procs = files.length ? getProcessTable() : new Map();

  for (const f of files) {
    let info;
    try { info = JSON.parse(fs.readFileSync(path.join(SESSIONS_DIR, f), 'utf8')); }
    catch (e) { continue; }
    if (!info.pid || !info.sessionId || !isPidAlive(info.pid)) continue;
    if (!allKinds && info.kind && info.kind !== 'interactive') continue;
    // Stale PID file + recycled PID: the process must still be claude
    const proc = procs.get(info.pid);
    if (!proc || !isClaudeSession(proc.command)) continue;
    sessions.push({
      sessionId: info.sessionId,
      pid: info.pid,
      cwd: info.cwd || '',
      name: info.name || '',
      nameSource: info.nameSource || '',
      status: info.status || '',
      kind: info.kind || 'interactive',
      version: info.version || '',
      bridgeSessionId: info.bridgeSessionId || '',
      tty: proc.tty,
      startedAt: info.startedAt || null,
    });
  }
  sessions.sort((a, b) => ttyOrder(a.tty) - ttyOrder(b.tty));
  _liveCache.set(key, sessions);
  return sessions;
}

function getLiveSessionIds(opts) {
  return new Set(getLiveSessions(opts).map(s => s.sessionId));
}

/**
 * Stale ("crashed") sessions: the newest transcript per project within
 * windowDays that has no live process, for projects with no live tab at all.
 * Returns [{ sessionId, filePath, projectDir, projectPath, projectName, mtime, ageDays }]
 * newest first. Shared by claude-tracker-alive and claude-tracker-resume.
 */
function getStaleSessions({ windowDays = 7, allKinds = false } = {}) {
  const live = getLiveSessions({ allKinds });
  const liveIds = new Set(live.map(s => s.sessionId));
  // Compare directories by their encoded key so a lossy decode (spaces,
  // hyphens) can never hide a live project from this check.
  const liveDirKeys = new Set(live.map(s => s.cwd).filter(Boolean).map(pathToKey));
  const cutoff = Date.now() - windowDays * 24 * 60 * 60 * 1000;

  const byProject = new Map();
  for (const file of getAllSessionFiles()) {   // newest first
    if (file.mtime <= cutoff) break;
    const sessionId = path.basename(file.filePath, '.jsonl');
    if (liveIds.has(sessionId)) continue;
    const projectPath = decodeProjectPath(file.projectDir);
    if (liveDirKeys.has(pathToKey(projectPath)) || byProject.has(projectPath)) continue;
    byProject.set(projectPath, {
      sessionId,
      filePath: file.filePath,
      projectDir: file.projectDir,
      projectPath,
      projectName: path.basename(projectPath),
      mtime: file.mtime,
      ageDays: (Date.now() - file.mtime) / (1000 * 60 * 60 * 24),
    });
  }
  return [...byProject.values()].sort((a, b) => b.mtime - a.mtime);
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
 * Uses JSONL transcript metadata as ground truth when available, since the
 * hyphen-encoded directory names are lossy (hyphens in real paths collide
 * with path separators). Falls back to filesystem heuristic.
 */
const _decodeCache = new Map();          // dirName → path, per process
let _projectDirMap = undefined;          // tracker.db project_dir → project_path (lazy)

function projectDirMap() {
  if (_projectDirMap !== undefined) return _projectDirMap;
  _projectDirMap = null;
  const db = tryDb();
  if (db) {
    try { _projectDirMap = db.getProjectDirMap(); } catch (e) { /* schema too old */ }
  }
  return _projectDirMap;
}

/**
 * Read the `cwd` recorded on the newest transcript in a project dir. Every
 * user/attachment line carries it, so the first 8 KB is enough.
 */
function readHeadCwd(projDir) {
  let newest = null;
  try {
    for (const f of fs.readdirSync(projDir)) {
      if (!f.endsWith('.jsonl')) continue;
      const full = path.join(projDir, f);
      const st = fs.statSync(full);
      if (!newest || st.mtimeMs > newest.mtimeMs) newest = { full, mtimeMs: st.mtimeMs };
    }
    if (!newest) return null;
    const fd = fs.openSync(newest.full, 'r');
    const buf = Buffer.alloc(8192);
    const n = fs.readSync(fd, buf, 0, 8192, 0);
    fs.closeSync(fd);
    const m = buf.toString('utf8', 0, n).match(/"cwd":"((?:[^"\\]|\\.)*)"/);
    if (m) return JSON.parse('"' + m[1] + '"');
  } catch (e) {
    // unreadable dir/file — fall through
  }
  return null;
}

/**
 * Precedence: memo → tracker.db sessions.project_path (exact, from the
 * transcript's cwd) → cwd on the newest transcript in the dir → filesystem
 * heuristic (lossy; wrong for moved/deleted dirs and hyphenated names).
 * sessions-index.json is not consulted: Claude Code documents it as internal,
 * and here it is a fossil (11 of 92 dirs, last written months ago).
 */
function decodeProjectPath(dirName) {
  if (_decodeCache.has(dirName)) return _decodeCache.get(dirName);

  let resolved = null;
  const map = projectDirMap();
  if (map) resolved = map.get(dirName) || null;
  if (!resolved) resolved = readHeadCwd(path.join(PROJECTS_DIR, dirName));
  if (!resolved) resolved = resolvePathHeuristic(dirName);

  _decodeCache.set(dirName, resolved);
  return resolved;
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
 * Load session metadata from session-registry.json and JSONL transcripts.
 * Returns a flat array of session entries enriched with projectDir and projectName.
 */
function loadSessionsIndex() {
  if (!fs.existsSync(PROJECTS_DIR)) return [];

  // Titles/summaries: tracker.db (kept current by the Stop hook). The
  // session-registry.json fallback is a frozen snapshot, used only without a DB.
  let registry = {};
  const db = tryDb();
  if (db) {
    try {
      for (const [id, meta] of db.getSessionMetaMap()) {
        registry[id] = { title: meta.customTitle, summary: meta.summary };
      }
    } catch (e) { /* schema too old — fall through to the file */ }
  }
  if (Object.keys(registry).length === 0) {
    const registryPath = path.join(os.homedir(), '.claude', 'session-registry.json');
    try {
      registry = JSON.parse(fs.readFileSync(registryPath, 'utf-8')).sessions || {};
    } catch (e) {
      // No registry either
    }
  }

  const allSessions = [];
  const projectDirs = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory());

  for (const dir of projectDirs) {
    const projDir = path.join(PROJECTS_DIR, dir.name);
    const projectPath = decodeProjectPath(dir.name);
    const projectName = path.basename(projectPath);

    // Enumerate JSONL transcripts as session entries
    try {
      const jsonls = fs.readdirSync(projDir).filter(f => f.endsWith('.jsonl'));
      for (const jsonl of jsonls) {
        const sessionId = path.basename(jsonl, '.jsonl');
        const stat = fs.statSync(path.join(projDir, jsonl));
        const regEntry = registry[sessionId] || {};

        allSessions.push({
          sessionId,
          customTitle: regEntry.title || '',
          summary: regEntry.summary || '',
          fullPath: path.join(projDir, jsonl),
          fileMtime: stat.mtime.toISOString(),
          projectDir: dir.name,
          projectPath,
          projectName
        });
      }
    } catch (e) {
      // Permission or read error — skip
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
 * Read only the slug from a JSONL session file by scanning the first N lines.
 * Synchronous — intended for metadata-only searches (--name mode).
 * Returns empty string if slug not found within headLines.
 */
function readSessionSlug(filePath, headLines = 15) {
  try {
    const fd = fs.openSync(filePath, 'r');
    const buf = Buffer.alloc(4096);
    const bytesRead = fs.readSync(fd, buf, 0, 4096, 0);
    fs.closeSync(fd);
    const partial = buf.toString('utf-8', 0, bytesRead);
    const lines = partial.split('\n');
    const limit = Math.min(headLines, lines.length);
    for (let i = 0; i < limit; i++) {
      if (!lines[i]) continue;
      try {
        const obj = JSON.parse(lines[i]);
        if (obj.slug) return obj.slug;
      } catch (e) { /* skip */ }
    }
  } catch (e) { /* file unreadable */ }
  return '';
}

/**
 * Read the user-assigned custom title from a JSONL session file.
 * /rename writes {"type": "custom-title", "customTitle": "..."} entries.
 * Returns the LAST custom title (most recent rename), or empty string.
 * Efficient tail-read: only reads the last tailBytes of the file.
 */
function readCustomTitle(filePath, tailBytes = 131072) {
  try {
    const stat = fs.statSync(filePath);
    const size = stat.size;
    const start = Math.max(0, size - tailBytes);
    const fd = fs.openSync(filePath, 'r');
    const buf = Buffer.alloc(Math.min(tailBytes, size));
    const bytesRead = fs.readSync(fd, buf, 0, buf.length, start);
    fs.closeSync(fd);
    const chunk = buf.toString('utf-8', 0, bytesRead);
    const lines = chunk.split('\n');
    // Skip first line if we seeked past the start (may be truncated)
    const startIdx = start > 0 ? 1 : 0;
    // Scan backwards — last rename wins
    for (let i = lines.length - 1; i >= startIdx; i--) {
      if (!lines[i]) continue;
      try {
        const obj = JSON.parse(lines[i]);
        if (obj.type === 'custom-title' && obj.customTitle) {
          return obj.customTitle;
        }
      } catch (e) { /* skip */ }
    }
  } catch (e) { /* file unreadable */ }
  return '';
}

/**
 * Extract plain text from a JSONL message content field.
 * Handles string content and content-block arrays; image/tool blocks are
 * dropped (only type:'text' blocks carry indexable conversation).
 */
function extractMessageText(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .filter(block => block && block.type === 'text' && block.text)
      .map(block => block.text)
      .join(' ');
  }
  return '';
}

/**
 * Substrings that mark system context injection rather than real conversation.
 * Shared by body search and the transcript indexer.
 */
const TRANSCRIPT_NOISE_PATTERNS = [
  'CLAUDE.md',
  'MEMORY.md',
  'active-projects.md',
  '<observed_from_primary_session>',
  'system-reminder',
  'agent_docs/',
  'user-invocable skills',
  'userModels/',
  'out of extra usage',       // harness usage banners rendered as messages
  'usage limit reached',
];

function isTranscriptNoise(text) {
  for (const pattern of TRANSCRIPT_NOISE_PATTERNS) {
    if (text.includes(pattern)) return true;
  }
  return false;
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
      const files = fs.readdirSync(dir.path).filter(f => SESSION_FILE_RE.test(f));
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

  // Exact per-session liveness from PID files. The directory-match scan is
  // only for machines without a sessions dir (pre-PID-file Claude Code).
  const liveById = new Map(getLiveSessions().map(s => [s.sessionId, s]));
  const runningDirs = fs.existsSync(SESSIONS_DIR) ? new Set() : getRunningClaudeSessions();
  const vsCodeWorkspaces = getVSCodeWorkspaces();

  let runningCount = 0;
  let inactiveCount = 0;
  let vsCodeCount = 0;

  const sessionsWithStatus = [];

  for (const file of files) {
    const projectPath = decodeProjectPath(file.projectDir);
    const sessionId = path.basename(file.filePath, '.jsonl');
    const live = liveById.get(sessionId) || null;

    let isRunning = !!live;
    if (!isRunning) {
      for (const runDir of runningDirs) {
        if (isPathMatch(file.projectDir, runDir)) { isRunning = true; break; }
      }
    }

    const isInVSCode = isInVSCodeWorkspace(projectPath, vsCodeWorkspaces);

    // Filter for VS Code only mode
    if (vsCodeOnly && !isInVSCode) continue;

    if (isRunning) runningCount++; else inactiveCount++;
    if (isInVSCode) vsCodeCount++;

    sessionsWithStatus.push({
      ...file, projectPath, isRunning, isInVSCode,
      pid: live ? live.pid : null,
      tty: live ? live.tty : '',
      liveName: live ? live.name : '',
      liveStatus: live ? live.status : '',
    });

    if (sessionsWithStatus.length >= maxSessions) break;
  }

  return {
    sessions: sessionsWithStatus,
    runningCount,
    inactiveCount,
    vsCodeCount
  };
}

// ---------------------------------------------------------------------------
// Pricing
// ---------------------------------------------------------------------------

/**
 * Anthropic API prices per million tokens, from the /claude-api skill's model
 * table (cached 2026-10-06). Cache writes cost 1.25x input for the 5-minute
 * TTL and 2x for the 1-hour TTL; cache reads are 0.1x input except where the
 * table lists a lower rate. Haiku stays priced: old transcripts and Claude
 * Code's own title calls use it. First matching pattern wins.
 */
const MODEL_PRICING = [
  // pattern                                   input  output  cacheRead
  [/fable-5-1|mythos-5-1/,                     10,    50,     0.25],
  [/fable|mythos/,                             10,    50,     1.00],
  [/opus-5-5/,                                  4,    20,     0.20],
  [/opus-4-[01]|opus-4-2025|opus-3|3-opus/,    15,    75,     1.50],
  [/opus/,                                      5,    25,     0.50],
  [/sonnet-5/,                                  2,    10,     0.20],
  [/sonnet/,                                    3,    15,     0.30],
  [/haiku-5/,                                0.10,  0.50,     0.01],
  [/3-5-haiku|haiku-3-5/,                    0.80,  4.00,     0.08],
  [/3-haiku|haiku-3/,                        0.25,  1.25,     0.03],
  [/haiku/,                                  1.00,  5.00,     0.10],
];
const DEFAULT_PRICING = [null, 2, 10, 0.20];  // unknown model: current Sonnet

/**
 * USD for one message's usage. cacheCreationTokens is the total written;
 * cacheCreation1hTokens is the part written with the 1-hour TTL (2x input),
 * the rest is 5-minute (1.25x).
 */
function calculateCostUsd(model, inputTokens = 0, outputTokens = 0, cacheReadTokens = 0, cacheCreationTokens = 0, cacheCreation1hTokens = 0) {
  const m = (model || '').toLowerCase();
  const [, input, output, cacheRead] = MODEL_PRICING.find(([re]) => re.test(m)) || DEFAULT_PRICING;
  const oneHour = Math.min(cacheCreation1hTokens, cacheCreationTokens);
  return (
    inputTokens * input +
    outputTokens * output +
    cacheReadTokens * cacheRead +
    (cacheCreationTokens - oneHour) * input * 1.25 +
    oneHour * input * 2
  ) / 1_000_000;
}

/** claude-opus-4-5-20251101 → opus-4.5, claude-sonnet-5-5 → sonnet-5.5 */
function shortModelName(model) {
  if (!model) return null;
  return model.replace(/^claude-/, '').replace(/-\d{8}$/, '').replace(/-(\d+)-(\d+)$/, '-$1.$2');
}

// ---------------------------------------------------------------------------
// Transcript extraction
//
// One streaming pass per transcript yields the FTS text rows, the title
// events, and the session metadata row. Field sources and their precedence
// are the plan's "Field sources" table; tests/extract*.test.js pin them.
// ---------------------------------------------------------------------------

// Real transcripts are <uuid>.jsonl. Claude Code's quarantined copies
// (<uuid>.orphaned-<ts>-<sfx>.jsonl, .superseded-*) also end in .jsonl.
const SESSION_FILE_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$/;

// FTS rows: cap pathological single messages (huge pasted dumps), and skip
// system-injected turns (command wrappers, tool results rendered as user turns)
const MAX_MESSAGE_CHARS = 20000;
const SKIP_PREFIXES = ['<command-', '<local-command', '<task-notification', '<system-reminder'];
const FIRST_PROMPT_CHARS = 500;
const COMPACT_SUMMARY_CHARS = 400;
// A single line this large is a tool payload, never metadata; parsing it
// would only risk the V8 string limit
const MAX_LINE_BYTES = 64 * 1024 * 1024;

// Not prompts: local-command output and caveats, notifications, reminders.
// A slash command (<command-message>/<command-name>) IS a prompt, as it is
// in origin-era transcripts; only the search index skips it.
const NON_PROMPT_PREFIXES = SKIP_PREFIXES.filter(p => p !== '<command-');

function startsWithAny(text, prefixes) {
  const head = text.trimStart().slice(0, 40);
  return prefixes.some(p => head.startsWith(p));
}

/** Claude Code's own wrappers (caveats, command output, notifications, reminders). */
function isWrapperText(text) {
  return startsWithAny(text, NON_PROMPT_PREFIXES);
}

/** Search-index filter: every wrapper, slash commands, and injected context. */
function isSkippedText(text) {
  if (!text) return true;
  return startsWithAny(text, SKIP_PREFIXES) || isTranscriptNoise(text.slice(0, 2000));
}

// Transcript fields are untrusted: a value of the wrong type is ignored,
// never stored (SQLite binding would throw) and never thrown on
const str = (v) => (typeof v === 'string' && v ? v : null);
const num = (v) => (typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : 0);

/**
 * Read complete lines of filePath synchronously, a chunk at a time, from byte
 * `start`. Splits on '\n' only: 0x0A never occurs inside a UTF-8 multibyte
 * sequence, and U+2028/2029 stay inside their line. A final line without a
 * newline is still being written and is left for the next read.
 * onLine(text, lineNo) is called for each non-empty line; lineNo is the
 * physical line number (blank and oversized lines count but are not
 * delivered), continuing from `startLine`. Exceptions from onLine propagate.
 * Returns {end, lines, error}: end is the byte offset just past the last
 * complete line, lines the physical line count reached, error the read error
 * that stopped it (null at clean EOF).
 */
function readLinesSync(filePath, onLine, { start = 0, startLine = 0, chunkBytes = 1 << 20, maxLineBytes = MAX_LINE_BYTES } = {}) {
  let fd;
  try { fd = fs.openSync(filePath, 'r'); } catch (error) { return { end: start, lines: startLine, error }; }
  const buf = Buffer.allocUnsafe(chunkBytes);
  let pos = start;
  let end = start;
  let lines = startLine;
  let pending = [];        // pieces of a line that spans chunks (copied: buf is reused)
  let pendingBytes = 0;
  try {
    for (;;) {
      let n;
      try { n = fs.readSync(fd, buf, 0, chunkBytes, pos); } catch (error) { return { end, lines, error }; }
      if (n === 0) break;
      const chunk = buf.subarray(0, n);
      let from = 0;
      let nl;
      while ((nl = chunk.indexOf(0x0a, from)) !== -1) {
        const piece = chunk.subarray(from, nl);
        const oversized = pendingBytes + piece.length > maxLineBytes;
        const text = oversized ? ''
          : (pending.length ? Buffer.concat([...pending, piece]) : piece).toString('utf8');
        pending = [];
        pendingBytes = 0;
        lines++;
        end = pos + nl + 1;
        from = nl + 1;
        if (text) onLine(text, lines);
      }
      if (from < n) {
        if (pendingBytes + (n - from) <= maxLineBytes) pending.push(Buffer.from(chunk.subarray(from)));
        else pending = [];
        pendingBytes += n - from;
      }
      pos += n;
    }
  } finally {
    fs.closeSync(fd);
  }
  return { end, lines, error: null };
}

function emptyUsage() {
  return {
    inputTokens: 0, outputTokens: 0, cacheReadTokens: 0, cacheCreationTokens: 0,
    computedCost: 0, costAfterState: 0, outputByModel: {}, lastModel: null, sawUsage: false,
  };
}

/**
 * Fresh accumulator for extractRecord. Plain data only, so a later
 * incremental indexer can serialize it and resume from a byte offset.
 */
function createExtractState(fileSessionId = null, { collectMessages = true } = {}) {
  return {
    fileSessionId,
    collectMessages,
    lineNo: 0,
    sessionId: null, cwd: null, gitBranch: null, entrypoint: null, version: null,
    firstTimestamp: null, lastTimestamp: null,
    // Prompts: older transcripts mark none (or only task-notification and
    // peer records), so plain non-meta user text counts as a prompt until
    // the first origin.kind === 'human' record; from then on only
    // human-origin records count. A legacy session resumed under a newer
    // Claude Code keeps its earlier prompts.
    sawHuman: false,
    plainTurns: 0, firstPlainPrompt: null, lastPlainAt: null,
    humanTurns: 0, firstHumanPrompt: null, lastHumanAt: null,
    durationMs: 0,
    aiTitle: null, agentName: null, slug: null,
    customTitles: {},                      // target sessionId → last custom title
    awaySummary: null, compactSummary: null, compactSummaries: 0, compactBoundaries: 0,
    prUrl: null, lastPrompt: null,
    // Cost: cost-state is written where a session resumes, so the total is
    // the last one's value plus the deduped usage of messages begun after it
    costState: null, costEpoch: 0,
    usage: emptyUsage(),
    // Streaming writes one record per content block, each repeating the
    // message id; repeats are always consecutive (0 exceptions in 1,779
    // files). Early records can carry partial or no usage, so the LAST
    // record with usage wins: it is held here until the id changes.
    pending: null,
    lastTitleByKey: {},
    messages: [],
    titleEvents: [],
  };
}

/** Add a finished message's usage to a usage accumulator (mutates `u`). */
function addUsage(u, p, st) {
  if (!p || !p.model) return u;
  u.inputTokens += p.input;
  u.outputTokens += p.output;
  u.cacheReadTokens += p.cacheRead;
  u.cacheCreationTokens += p.cacheWrite;
  u.outputByModel[p.model] = (u.outputByModel[p.model] || 0) + p.output;
  u.lastModel = p.model;
  u.sawUsage = true;
  const cost = calculateCostUsd(p.model, p.input, p.output, p.cacheRead, p.cacheWrite, p.cacheWrite1h);
  u.computedCost += cost;
  // Begun after the latest cost-state: not included in its total
  if (st.costState !== null && p.epoch === st.costEpoch) u.costAfterState += cost;
  return u;
}

function flushPending(st) {
  addUsage(st.usage, st.pending, st);
  st.pending = null;
}

/** `<command-message>…<command-name>/review</command-name><command-args>x</command-args>` → `/review x` */
function renderPrompt(text) {
  if (!text.trimStart().startsWith('<command-')) return text;
  const name = /<command-name>\s*\/?([^<]*?)\s*<\/command-name>/.exec(text);
  if (!name) return text;
  const args = /<command-args>([\s\S]*?)<\/command-args>/.exec(text);
  const a = args ? args[1].trim() : '';
  return '/' + name[1] + (a ? ' ' + a : '');
}

function pushTitleEvent(st, target, title, source) {
  const key = source + '\u0000' + target;
  if (st.lastTitleByKey[key] === title) return;
  st.lastTitleByKey[key] = title;
  st.titleEvents.push({ sessionId: target, title, source, observedAt: st.lastTimestamp, firstSeenSeq: st.lineNo });
}

function originKind(obj) {
  const o = obj.origin;
  if (o == null) return null;
  return typeof o === 'object' ? str(o.kind) : str(o);
}

/**
 * Fold one parsed transcript record into the accumulator. The caller sets
 * st.lineNo to the record's physical line number before calling.
 */
function extractRecord(obj, st) {
  if (!obj || typeof obj !== 'object') return;
  const sid = str(obj.sessionId) || str(obj.session_id);
  if (!st.sessionId && sid) st.sessionId = sid;
  if (!st.cwd && str(obj.cwd)) st.cwd = obj.cwd;
  if (!st.gitBranch && str(obj.gitBranch)) st.gitBranch = obj.gitBranch;
  if (!st.entrypoint && str(obj.entrypoint)) st.entrypoint = obj.entrypoint;
  if (str(obj.version)) st.version = obj.version;
  if (str(obj.timestamp)) {
    if (!st.firstTimestamp) st.firstTimestamp = obj.timestamp;
    st.lastTimestamp = obj.timestamp;
  }
  const ownId = st.fileSessionId || st.sessionId;
  // Title records route by their OWN sessionId: a /rename after /resume
  // lands in the active file but targets another session
  const target = sid || ownId;
  const mine = target === ownId;

  switch (obj.type) {
    case 'custom-title':
      if (str(obj.customTitle)) {
        st.customTitles[target] = obj.customTitle;
        pushTitleEvent(st, target, obj.customTitle, 'user');
      }
      return;
    case 'ai-title':
      if (str(obj.aiTitle)) {
        if (mine) st.aiTitle = obj.aiTitle;
        pushTitleEvent(st, target, obj.aiTitle, 'ai-title');
      }
      return;
    case 'agent-name':
      if (str(obj.agentName)) {
        if (mine) st.agentName = obj.agentName;
        pushTitleEvent(st, target, obj.agentName, 'agent-name');
      }
      return;
    case 'pr-link':
      if (str(obj.prUrl)) st.prUrl = obj.prUrl;
      return;
    case 'last-prompt':
      if (str(obj.lastPrompt) && obj.lastPrompt.trim()) st.lastPrompt = obj.lastPrompt;
      return;
    case 'cost-state':
      if (typeof obj.totalCostUSD === 'number' && Number.isFinite(obj.totalCostUSD)) {
        st.costState = obj.totalCostUSD;
        st.costEpoch++;
        st.usage.costAfterState = 0;
      }
      return;
    case 'system':
      if (obj.subtype === 'turn_duration') st.durationMs += num(obj.durationMs);
      else if (obj.subtype === 'away_summary' && str(obj.content) && obj.content.trim()) st.awaySummary = obj.content;
      else if (obj.subtype === 'compact_boundary') st.compactBoundaries++;
      return;
    default:
      break;
  }

  if (str(obj.slug) && obj.slug !== st.slug) {
    st.slug = obj.slug;
    pushTitleEvent(st, ownId, obj.slug, 'slug');
  }
  if (obj.type !== 'user' && obj.type !== 'assistant') return;
  const msg = obj.message && typeof obj.message === 'object' ? obj.message : {};
  const text = extractMessageText(msg.content);

  if (obj.type === 'user') {
    const kind = originKind(obj);
    if (obj.isCompactSummary) {
      st.compactSummaries++;
      if (text) st.compactSummary = text.slice(0, COMPACT_SUMMARY_CHARS);
    } else if (kind === 'human') {
      st.sawHuman = true;
      st.humanTurns++;
      if (str(obj.timestamp)) st.lastHumanAt = obj.timestamp;
      if (!st.firstHumanPrompt && text.trim()) st.firstHumanPrompt = renderPrompt(text).slice(0, FIRST_PROMPT_CHARS);
    } else if (!st.sawHuman && !kind && !obj.isMeta && !obj.isSidechain && text.trim() && !isWrapperText(text)) {
      // Prompt detection uses wrappers only: a real prompt may well mention
      // CLAUDE.md, which the search filter (isSkippedText) treats as noise
      st.plainTurns++;
      if (str(obj.timestamp)) st.lastPlainAt = obj.timestamp;
      if (!st.firstPlainPrompt) st.firstPlainPrompt = renderPrompt(text).slice(0, FIRST_PROMPT_CHARS);
    }
  } else {
    const id = str(msg.id);
    if (!id || !st.pending || st.pending.id !== id) flushPending(st);
    const u = msg.usage && typeof msg.usage === 'object' ? msg.usage : null;
    const model = str(msg.model);
    if (u && model && model !== '<synthetic>') {
      const cc = u.cache_creation && typeof u.cache_creation === 'object' ? u.cache_creation : {};
      const p = {
        id, model,
        input: num(u.input_tokens),
        output: num(u.output_tokens),
        cacheRead: num(u.cache_read_input_tokens),
        cacheWrite: num(u.cache_creation_input_tokens),
        cacheWrite1h: num(cc.ephemeral_1h_input_tokens),
        // A message keeps the epoch it began in, even if a cost-state lands
        // between its records
        epoch: st.pending && st.pending.id === id ? st.pending.epoch : st.costEpoch,
      };
      if (id) st.pending = p;
      else addUsage(st.usage, p, st);
    } else if (id && !st.pending) {
      // An id with no usage yet: hold its place so a later record with
      // usage still dates from here
      st.pending = { id, model: null, epoch: st.costEpoch };
    }
  }

  if (st.collectMessages && !obj.isSidechain && text && !isSkippedText(text)) {
    st.messages.push({ role: obj.type, text: text.slice(0, MAX_MESSAGE_CHARS) });
  }
}

/** Session metadata from an accumulator; never mutates it. */
function finalizeMeta(st) {
  const u = addUsage({ ...st.usage, outputByModel: { ...st.usage.outputByModel } }, st.pending, st);
  let model = null;
  let best = -1;
  for (const [m, out] of Object.entries(u.outputByModel)) {
    if (out > best) { best = out; model = m; }
  }
  let totalCostUsd = 0;
  let costSource = null;
  if (st.costState !== null) {
    totalCostUsd = st.costState + u.costAfterState;
    costSource = u.costAfterState > 0 ? 'cost-state+computed' : 'cost-state';
  } else if (u.sawUsage) {
    totalCostUsd = u.computedCost;
    costSource = 'computed';
  }
  const ownId = st.fileSessionId || st.sessionId;
  const summary = st.awaySummary || st.compactSummary || null;
  return {
    sessionId: st.sessionId || st.fileSessionId || null,
    cwd: st.cwd,
    gitBranch: st.gitBranch,
    entrypoint: st.entrypoint || 'cli',
    version: st.version,
    createdAt: st.firstTimestamp,
    modifiedAt: st.lastTimestamp,
    lastUserMsgAt: st.lastHumanAt || st.lastPlainAt,
    firstPrompt: st.firstPlainPrompt || st.firstHumanPrompt,
    numTurns: st.plainTurns + st.humanTurns,
    durationMs: st.durationMs,
    model,
    modelShort: shortModelName(model),
    lastModel: u.lastModel,
    inputTokens: u.inputTokens,
    outputTokens: u.outputTokens,
    cacheReadTokens: u.cacheReadTokens,
    cacheCreationTokens: u.cacheCreationTokens,
    totalCostUsd,
    costSource,
    autoTitle: st.aiTitle || st.agentName || null,
    titleSource: st.aiTitle ? 'claude-code' : (st.agentName ? 'agent-name' : null),
    customTitle: (ownId && st.customTitles[ownId]) || null,
    summary,
    summarySource: st.awaySummary ? 'claude-code' : (summary ? 'compact' : null),
    compactCount: Math.max(st.compactSummaries, st.compactBoundaries),
    prUrl: st.prUrl,
    lastPrompt: st.lastPrompt,
    slug: st.slug,
  };
}

function sessionIdFromPath(filePath) {
  const base = path.basename(filePath);
  return SESSION_FILE_RE.test(base) ? base.slice(0, -'.jsonl'.length) : null;
}

/**
 * One synchronous pass over a transcript. Returns {meta, messages,
 * titleEvents, end, lines, hadError}; hadError means the read stopped before
 * EOF, so callers must not record index state or metadata from it.
 */
function extractTranscript(filePath, { collectMessages = true, fileSessionId = sessionIdFromPath(filePath),
  chunkBytes, maxLineBytes } = {}) {
  const st = createExtractState(fileSessionId, { collectMessages });
  const opts = {};
  if (chunkBytes) opts.chunkBytes = chunkBytes;
  if (maxLineBytes) opts.maxLineBytes = maxLineBytes;
  const r = readLinesSync(filePath, (line, lineNo) => {
    st.lineNo = lineNo;
    let obj;
    try { obj = JSON.parse(line); } catch { return; }
    extractRecord(obj, st);
  }, opts);
  return { meta: finalizeMeta(st), messages: st.messages, titleEvents: st.titleEvents,
    end: r.end, lines: r.lines, hadError: !!r.error };
}

/** Session metadata only (no FTS rows held in memory); null if the read failed. */
function extractSessionMeta(filePath) {
  const r = extractTranscript(filePath, { collectMessages: false });
  return r.hadError ? null : r.meta;
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

/**
 * Load speculator snapshot for Ghostty tab → Claude session mapping.
 * Returns { byPid: { pid -> { tty, status, ... } }, bySessionId: { id -> entry }, windows: [] }
 */
const SPECULATOR_JSON = path.join(os.homedir(), '.claude', 'scripts', 'speculator', 'data', 'ghostty-sessions.json');

function loadSpeculatorData() {
  try {
    if (!fs.existsSync(SPECULATOR_JSON)) return null;
    const stat = fs.statSync(SPECULATOR_JSON);
    // Skip if data is older than 10 minutes
    if (Date.now() - stat.mtimeMs > 600000) return null;
    const data = JSON.parse(fs.readFileSync(SPECULATOR_JSON, 'utf-8'));
    if (!data || !data.sessions) return null;

    const byPid = {};
    const bySessionId = {};
    for (const entry of data.sessions) {
      const cs = entry.claude_session;
      if (!cs) continue;
      byPid[cs.pid] = { tty: entry.tty, ...cs };
      if (cs.sessionId) bySessionId[cs.sessionId] = { tty: entry.tty, ...cs };
    }
    return {
      byPid,
      bySessionId,
      windows: data.ghostty ? data.ghostty.windows : [],
      ghosttyRunning: data.ghostty ? data.ghostty.running : false,
      stats: data.stats || {},
    };
  } catch (e) {
    return null;
  }
}

/**
 * Get TTY info for a session from speculator data.
 * Returns { tty, status, pid } or null.
 */
function getSessionTTY(sessionId, speculatorData) {
  if (!speculatorData) return null;
  const entry = speculatorData.bySessionId[sessionId];
  if (entry) return { tty: entry.tty, status: entry.status, pid: entry.pid };
  return null;
}

// Export all utilities
// ---------------------------------------------------------------------------
// SQLite fast-path wrapper
// ---------------------------------------------------------------------------

let _trackerDb = undefined;
function tryDb() {
  if (_trackerDb !== undefined) return _trackerDb || null;
  let reason = 'unknown';
  try {
    const dbModule = require(path.join(__dirname, 'tracker-db'));
    if (dbModule.isAvailable()) {
      _trackerDb = dbModule;
      return _trackerDb;
    }
    const err = dbModule.getLastError && dbModule.getLastError();
    reason = err ? err.message : 'probe failed';
  } catch (e) {
    reason = e.message;
  }
  // Never degrade silently: a JSONL scan is 10-100x slower and misses
  // index-only features, so the caller must be able to see why it happened.
  process.stderr.write('\x1b[33mtracker-db unavailable: ' + reason + ' — falling back to JSONL scan\x1b[0m\n');
  _trackerDb = false;
  return null;
}

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
  SESSIONS_DIR,
  isPidAlive,
  getProcessTable,
  ttyOrder,
  getLiveSessions,
  getLiveSessionIds,
  getStaleSessions,
  getVSCodeWorkspaces,
  isInVSCodeWorkspace,
  extractKeywords,
  extractMessageText,
  isTranscriptNoise,
  TRANSCRIPT_NOISE_PATTERNS,
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
  readSessionSlug,
  readCustomTitle,
  calculateCostUsd,
  shortModelName,
  SESSION_FILE_RE,
  readLinesSync,
  createExtractState,
  extractRecord,
  finalizeMeta,
  extractTranscript,
  extractSessionMeta,

  // Git tracking
  GIT_TRACKING_INDEX,
  GIT_TRACKING_LOG,
  loadGitTracking,
  getSessionsForRepo,
  getReposForSession,
  getRecentCommits,
  getRecentGitEvents,

  // Speculator (Ghostty tab mapping)
  SPECULATOR_JSON,
  loadSpeculatorData,
  getSessionTTY,

  // SQLite fast-path
  tryDb,
};
