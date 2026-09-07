#!/usr/bin/env node
/**
 * index-transcripts.js — Build/refresh the transcript full-text index
 *
 * Usage: node index-transcripts.js [--rebuild] [--limit N] [--budget MS] [--quiet]
 *        node index-transcripts.js --session <id> | --file <path> | --stdin [--debounce SEC]
 *
 * Walks all top-level session JSONL files (subagent/tool-result payloads in
 * session subdirectories are never enumerated), extracts user+assistant text,
 * and writes it to transcript_messages / transcript_fts in the sidecar DB.
 *
 * Incremental by default: sessions whose file size and mtime match
 * transcript_index_state are skipped. --rebuild reindexes everything.
 * --budget stops after MS milliseconds (newest files first) and reports how
 * many remain — used by search-sessions.js for an on-demand catch-up.
 *
 * Single-session mode (--session/--file/--stdin) is what the Stop and
 * SessionEnd hooks call so every session is searchable within seconds of its
 * last turn. --stdin reads the hook JSON ({session_id, transcript_path}).
 * --debounce skips the reindex when the same session was indexed less than
 * SEC seconds ago and has grown by less than 256 KB since.
 *
 * Also usable as a module: refreshTranscriptIndex(), indexSession(),
 * indexOne(). Module callers own the DB handle (nothing here closes it).
 */

const os = require('os');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const utils = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-utils.js'));
const db = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-db.js'));

// Bump when extraction rules change (noise filters, skip prefixes, caps) —
// forces reindex of sessions indexed under older rules
const EXTRACTOR_VERSION = 4; // v4: title/nickname history extraction

// Guard against pathological single messages (huge pasted dumps)
const MAX_MESSAGE_CHARS = 20000;
// Skip system-injected turns: command wrappers, tool results rendered as user turns
const SKIP_PREFIXES = ['<command-', '<local-command', '<task-notification', '<system-reminder'];
// --debounce: a session that grew less than this since its last index pass
// is not worth re-extracting mid-conversation
const DEBOUNCE_GROWTH_BYTES = 256 * 1024;

const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');

function shouldSkip(text) {
  if (!text) return true;
  const head = text.trimStart().slice(0, 40);
  for (const p of SKIP_PREFIXES) {
    if (head.startsWith(p)) return true;
  }
  return utils.isTranscriptNoise(text.slice(0, 2000));
}

/**
 * Stream one JSONL transcript, returning {messages, titleEvents, hadError}.
 * hadError=true means the read did not reach a clean EOF — the caller must
 * NOT record index state, or the incremental skip would permanently mask a
 * partially-read session from search.
 *
 * Title events: custom-title lines route by their OWN sessionId — a /rename
 * after /resume writes into the active file but targets another session
 * (anthropics/claude-code#27202; Claude Code's scanner gets this wrong, we
 * don't). Lines carry no timestamp; the nearest preceding timestamped line
 * dates the event. Consecutive duplicates (Claude Code rewrites the line
 * constantly) collapse to one event per actual change.
 */
function extractMessages(filePath, fileSessionId) {
  return new Promise((resolve) => {
    const messages = [];
    const titleEvents = [];
    const lastTitleByTarget = new Map();
    let lastSlug = null;
    let lastTimestamp = null;
    let lineNo = 0;
    let hadError = false;
    let stream, rl;
    try {
      stream = fs.createReadStream(filePath);
      rl = readline.createInterface({ input: stream, crlfDelay: Infinity });
    } catch {
      return resolve({ messages, titleEvents, hadError: true });
    }
    rl.on('line', (line) => {
      lineNo++;
      let data;
      try { data = JSON.parse(line); } catch { return; }
      if (data.timestamp) lastTimestamp = data.timestamp;

      if (data.type === 'custom-title' && data.customTitle) {
        const target = data.sessionId || fileSessionId;
        if (lastTitleByTarget.get(target) !== data.customTitle) {
          lastTitleByTarget.set(target, data.customTitle);
          titleEvents.push({ sessionId: target, title: data.customTitle, source: 'user',
            observedAt: lastTimestamp, firstSeenSeq: lineNo });
        }
        return;
      }
      if (data.slug && data.slug !== lastSlug) {
        lastSlug = data.slug;
        titleEvents.push({ sessionId: fileSessionId, title: data.slug, source: 'slug',
          observedAt: lastTimestamp || data.timestamp || null, firstSeenSeq: lineNo });
      }

      if (data.type !== 'user' && data.type !== 'assistant') return;
      if (data.isSidechain) return;
      const text = utils.extractMessageText(data.message && data.message.content);
      if (!text || shouldSkip(text)) return;
      messages.push({ role: data.type, text: text.slice(0, MAX_MESSAGE_CHARS) });
    });
    rl.on('close', () => resolve({ messages, titleEvents, hadError }));
    rl.on('error', () => { hadError = true; resolve({ messages, titleEvents, hadError }); });
    stream.on('error', () => { hadError = true; resolve({ messages, titleEvents, hadError }); });
  });
}

function isCurrent(prior, stat) {
  return prior && prior.transcript_size === stat.size && prior.mtime_ms === stat.mtimeMs
    && (prior.extractor_version || 1) === EXTRACTOR_VERSION;
}

/**
 * Index one transcript if its size/mtime/extractor version changed.
 * Returns {status: 'indexed'|'skipped'|'errored'|'missing', messages, titleEvents}.
 */
async function indexOne(file, states, { quiet = true, force = false } = {}) {
  const sessionId = path.basename(file.filePath, '.jsonl');
  let stat;
  try { stat = fs.statSync(file.filePath); } catch { return { status: 'missing', messages: 0, titleEvents: 0 }; }

  if (!force && isCurrent(states.get(sessionId), stat)) {
    return { status: 'skipped', messages: 0, titleEvents: 0 };
  }

  const { messages, titleEvents, hadError } = await extractMessages(file.filePath, sessionId);
  if (hadError) {
    // No state write — the session stays eligible for the next run
    if (!quiet) console.log(`  ! read error, will retry next run: ${sessionId.slice(0, 8)}`);
    return { status: 'errored', messages: 0, titleEvents: 0 };
  }
  db.indexTranscript(sessionId, {
    filePath: file.filePath,
    projectDir: file.projectDir,
    transcriptSize: stat.size,
    mtimeMs: stat.mtimeMs,
    messages,
    titleEvents,
    extractorVersion: EXTRACTOR_VERSION,
  });
  return { status: 'indexed', messages: messages.length, titleEvents: titleEvents.length };
}

/**
 * Incremental refresh over every top-level transcript, newest first.
 * Stops before starting a file once budgetMs is spent or limit is reached.
 * Prunes index rows for deleted transcripts only on unbounded runs, where the
 * file list is authoritative. Never closes the DB.
 */
async function refreshTranscriptIndex({ budgetMs = Infinity, limit = Infinity, quiet = true,
  rebuild = false, prune = true } = {}) {
  const t0 = Date.now();
  db.initSchema();
  const states = rebuild ? new Map() : db.getTranscriptIndexStates();
  const allFiles = utils.getAllSessionFiles();

  const r = { indexed: 0, skipped: 0, empty: 0, errored: 0, remaining: 0,
    messages: 0, titleEvents: 0, pruned: 0, ms: 0 };

  let i = 0;
  for (; i < allFiles.length; i++) {
    if (r.indexed >= limit || Date.now() - t0 > budgetMs) break;
    const out = await indexOne(allFiles[i], states, { quiet });
    if (out.status === 'skipped') r.skipped++;
    else if (out.status === 'errored') r.errored++;
    else if (out.status === 'indexed') {
      r.indexed++;
      r.messages += out.messages;
      r.titleEvents += out.titleEvents;
      if (out.messages === 0) r.empty++;
      if (!quiet && r.indexed % 100 === 0) console.log(`  ${r.indexed} indexed (${r.skipped} skipped) …`);
    }
  }
  // Files not reached that would have needed work
  for (; i < allFiles.length; i++) {
    let stat;
    try { stat = fs.statSync(allFiles[i].filePath); } catch { continue; }
    if (!isCurrent(states.get(path.basename(allFiles[i].filePath, '.jsonl')), stat)) r.remaining++;
  }

  const unbounded = limit === Infinity && budgetMs === Infinity;
  if (prune && unbounded) {
    r.pruned = db.pruneTranscriptIndex(allFiles.map(f => path.basename(f.filePath, '.jsonl')));
  }
  r.ms = Date.now() - t0;
  return r;
}

/** Locate a session's top-level transcript by scanning project dirs (~2 ms). */
function findTranscript(sessionId) {
  let dirs;
  try { dirs = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true }); } catch { return null; }
  for (const d of dirs) {
    if (!d.isDirectory()) continue;
    const p = path.join(PROJECTS_DIR, d.name, sessionId + '.jsonl');
    if (fs.existsSync(p)) return { filePath: p, projectDir: d.name };
  }
  return null;
}

/**
 * Index exactly one session (hook path). Resolves the file from sessionId
 * when filePath is absent. Returns the indexOne result plus {sessionId}.
 * debounceSec: skip when indexed less than that long ago and the file grew
 * by less than DEBOUNCE_GROWTH_BYTES — bounds churn for chatty sessions.
 */
async function indexSession({ sessionId, filePath, debounceSec = 0, quiet = true } = {}) {
  if (!sessionId && filePath) sessionId = path.basename(filePath, '.jsonl');
  let file = null;
  if (filePath && fs.existsSync(filePath)) {
    file = { filePath, projectDir: path.basename(path.dirname(filePath)) };
  } else if (sessionId) {
    file = findTranscript(sessionId);
  }
  if (!file) return { sessionId, status: 'missing', messages: 0, titleEvents: 0 };

  db.initSchema();
  const states = db.getTranscriptIndexStates();
  if (debounceSec > 0) {
    const prior = states.get(sessionId);
    if (prior && prior.indexed_at) {
      const ageSec = (Date.now() - Date.parse(prior.indexed_at + 'Z')) / 1000;
      let size = 0;
      try { size = fs.statSync(file.filePath).size; } catch { /* fallthrough */ }
      if (ageSec < debounceSec && size - prior.transcript_size < DEBOUNCE_GROWTH_BYTES) {
        return { sessionId, status: 'debounced', messages: 0, titleEvents: 0 };
      }
    }
  }
  const out = await indexOne(file, states, { quiet });
  return { sessionId, ...out };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function readStdinJson(quiet) {
  try {
    const raw = fs.readFileSync(0, 'utf8').trim();
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    if (!quiet) console.error('index-transcripts: could not parse hook JSON on stdin: ' + e.message);
    return {};
  }
}

async function main() {
  const args = process.argv.slice(2);
  const flag = (name) => args.includes(name);
  const opt = (name) => { const i = args.indexOf(name); return i !== -1 && args[i + 1] ? args[i + 1] : null; };

  const quiet = flag('--quiet');
  const rebuild = flag('--rebuild');
  const limit = opt('--limit') ? parseInt(opt('--limit'), 10) : Infinity;
  const budgetMs = opt('--budget') ? parseInt(opt('--budget'), 10) : Infinity;
  const debounceSec = opt('--debounce') ? parseInt(opt('--debounce'), 10) : 0;

  let single = null;
  if (flag('--stdin')) {
    const hook = readStdinJson(quiet);
    single = { sessionId: hook.session_id, filePath: hook.transcript_path };
    if (!single.sessionId && !single.filePath) {
      if (!quiet) console.log('No session_id/transcript_path on stdin — nothing to index.');
      return;
    }
  } else if (opt('--session')) {
    single = { sessionId: opt('--session') };
  } else if (opt('--file')) {
    single = { filePath: path.resolve(opt('--file')) };
  }

  const t0 = Date.now();
  if (single) {
    const out = await indexSession({ ...single, debounceSec, quiet });
    if (!quiet) {
      const id = (out.sessionId || '?').slice(0, 8);
      console.log(`${id}: ${out.status}` + (out.status === 'indexed'
        ? ` — ${out.messages} messages, ${out.titleEvents} title events, ${Date.now() - t0}ms` : ''));
    }
    db.close();
    return;
  }

  const r = await refreshTranscriptIndex({ budgetMs, limit, quiet, rebuild });
  // --quiet still reports work done (one line) so hook/launchd logs stay useful
  // without the per-file chatter; a no-op run prints nothing.
  if (!quiet || r.indexed || r.errored || r.pruned) {
    const secs = (r.ms / 1000).toFixed(1);
    console.log(`Indexed ${r.indexed} session(s) in ${secs}s — ${r.skipped} unchanged, ${r.empty} with no indexable text` +
      (r.errored ? `, ${r.errored} read errors (will retry)` : '') +
      (r.remaining ? `, ${r.remaining} still pending (budget/limit reached)` : '') +
      (r.pruned ? `, ${r.pruned} deleted sessions pruned` : '') +
      (r.titleEvents ? `, ${r.titleEvents} title events` : '') + '.');
  }
  if (!quiet) {
    const stats = db.getTranscriptIndexStats();
    const dbSize = fs.statSync(db.TRANSCRIPTS_DB_PATH).size;
    console.log(`Index now holds ${stats.sessions} sessions, ${stats.messages} messages, ` +
      `${(stats.textBytes / 1e6).toFixed(1)} MB text. tracker-transcripts.db: ${(dbSize / 1e6).toFixed(1)} MB.`);
  }
  db.close();
}

module.exports = { indexOne, refreshTranscriptIndex, indexSession, findTranscript, EXTRACTOR_VERSION };

if (require.main === module) {
  main().catch(err => { console.error(err); process.exit(1); });
}
