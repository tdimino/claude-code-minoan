#!/usr/bin/env node
/**
 * index-transcripts.js — Build/refresh the transcript full-text index
 *
 * Usage: node index-transcripts.js [--rebuild] [--limit N] [--budget MS] [--quiet]
 *        node index-transcripts.js --session <id> | --file <path> | --stdin [--debounce SEC] [--detach]
 *
 * Walks all top-level <uuid>.jsonl session files (subagent/tool-result
 * payloads in session subdirectories and the .orphaned and .superseded copies are
 * never enumerated). One pass per file extracts user+assistant text into
 * transcript_messages / transcript_fts in the sidecar DB, title events into
 * title_history, and the session metadata row (titles, summary, first
 * prompt, model, turns, cost) into sessions.
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
const utils = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-utils.js'));
const db = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-db.js'));

// Bump when extraction rules change (noise filters, skip prefixes, caps,
// metadata fields) — forces reindex of sessions indexed under older rules
const EXTRACTOR_VERSION = 8; // v8: compact-summary preamble stripped, +estimated cost source, worktree detection from subdirectories

// --debounce: a session that grew less than this since its last index pass
// is not worth re-extracting mid-conversation
const DEBOUNCE_GROWTH_BYTES = 256 * 1024;

const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const ERROR_LOG = path.join(os.homedir(), '.claude', 'logs', 'transcript-index-errors.log');

/**
 * Errors from the database itself (locked, full, corrupt, read-only) stop a
 * pass: every later file would fail the same way. Anything else belongs to
 * one transcript and must not block the sessions after it.
 */
function isDbLevelError(err) {
  return !!err && err.code === 'ERR_SQLITE_ERROR'
    && /locked|busy|full|disk|corrupt|malformed|readonly|not a database/i.test(String(err.message));
}

/** One line per failed session, kept even under --quiet (hooks run quiet). */
function logIndexError(sessionId, err) {
  const line = `${new Date().toISOString()} ${String(sessionId).slice(0, 8)} ${err && err.stack ? err.stack.split('\n')[0] : err}\n`;
  try {
    fs.mkdirSync(path.dirname(ERROR_LOG), { recursive: true });
    fs.appendFileSync(ERROR_LOG, line);
  } catch { /* the stderr line below still reports it */ }
  console.error(`transcript-index: ${line.trim()}`);
}

/**
 * Is the cwd inside a linked worktree? Walks up to the nearest .git: a
 * directory is a main checkout; a file is a worktree when its gitdir points
 * into .git/worktrees/, and a submodule when it points into .git/modules/.
 * null when the cwd is unknown, gone, or outside any repository.
 */
function isWorktree(cwd) {
  if (!cwd || !fs.existsSync(cwd)) return null;
  for (let dir = path.resolve(cwd); ; dir = path.dirname(dir)) {
    const dotGit = path.join(dir, '.git');
    let stat = null;
    try { stat = fs.statSync(dotGit); } catch (e) {
      // Only "no .git here" means keep walking; anything else is unknowable
      if (e.code !== 'ENOENT' && e.code !== 'ENOTDIR') return null;
    }
    if (stat && stat.isDirectory()) return false;
    if (stat && stat.isFile()) {
      try {
        const gitdir = /^gitdir:\s*(.+)$/m.exec(fs.readFileSync(dotGit, 'utf8'));
        if (!gitdir) return null;
        return /[\\/]worktrees[\\/][^\\/]+[\\/]?$/.test(gitdir[1].trim());
      } catch { return null; }
    }
    if (path.dirname(dir) === dir) return null;
  }
}

// Metadata that a correct extraction never produces for a real session; a
// Claude Code format change shows up here first
const SANITY_CHECKS = [
  ['zero-turn transcript over 100 KB', 'COALESCE(s.num_turns, 0) = 0 AND t.transcript_size > 102400'],
  ['output with no model', 's.total_output_tokens > 0 AND s.model IS NULL'],
  ['output with no cost source', 's.total_output_tokens > 0 AND s.cost_source IS NULL'],
  ['estimated cost', "s.cost_source LIKE '%+estimated'"],
];

/**
 * Indexed sessions active in the last `days` that fail a sanity check.
 * Returns [[label, [sessionId…]]] for the checks that found any.
 */
function sanityCheck(days = 7) {
  const d = db.ensureTranscripts();
  return SANITY_CHECKS.map(([label, where]) => [label, d.prepare(`
    SELECT s.session_id FROM sessions s
    JOIN transcripts.transcript_index_state t ON t.session_id = s.session_id
    WHERE s.modified_at >= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?) AND ${where}
    ORDER BY s.modified_at DESC`).all(`-${days} days`).map(r => r.session_id)])
    .filter(([, ids]) => ids.length);
}

function formatSanity(found) {
  const sessions = new Set(found.flatMap(([, ids]) => ids)).size;
  const parts = found.map(([label, ids]) =>
    `${ids.length} ${label} (${ids.slice(0, 5).map(id => id.slice(0, 8)).join(' ')}${ids.length > 5 ? ' …' : ''})`);
  return `Sanity: ${sessions} recent session(s) look wrong: ${parts.join(', ')}.`;
}

/**
 * Does a saved offset still sit just past a newline? Claude Code only
 * appends; a file rewritten in place keeps its inode but not its line breaks.
 */
function endsLineAt(filePath, offset) {
  if (!offset) return true;
  let fd;
  try {
    fd = fs.openSync(filePath, 'r');
    const b = Buffer.alloc(1);
    return fs.readSync(fd, b, 0, 1, offset - 1) === 1 && b[0] === 0x0a;
  } catch { return false; } finally { if (fd !== undefined) fs.closeSync(fd); }
}

function isCurrent(prior, stat) {
  return prior && prior.transcript_size === stat.size && prior.mtime_ms === stat.mtimeMs
    && (prior.extractor_version || 1) === EXTRACTOR_VERSION;
}

/**
 * Can the last pass be continued from its byte offset? Only when it is the
 * same file (path and inode), under the same extraction rules, and has only
 * grown since. Anything else (shrank, replaced, moved, rules changed, or a
 * pass from before resume state existed) gets a full rebuild.
 */
function canResume(prior, file, stat) {
  return !!prior && prior.byte_offset != null && prior.line_no != null
    && (prior.extractor_version || 1) === EXTRACTOR_VERSION
    && prior.file_path === file.filePath
    && prior.inode === stat.ino
    && stat.size >= prior.transcript_size
    && stat.size >= prior.byte_offset;
}

/**
 * Index one transcript if its size/mtime/extractor version changed: an
 * increment from the last byte offset when possible (canResume), else a
 * full pass. Cost is proportional to the bytes appended since last time.
 * Returns {status: 'indexed'|'appended'|'skipped'|'errored'|'missing', messages, titleEvents}.
 */
async function indexOne(file, states, { quiet = true, force = false } = {}) {
  const sessionId = path.basename(file.filePath, '.jsonl');
  let stat;
  try { stat = fs.statSync(file.filePath); } catch { return { status: 'missing', messages: 0, titleEvents: 0 }; }

  // The pass-wide snapshot is only a fast skip; another writer (a Stop hook
  // during the hourly pass) may have moved this session's state since, so
  // anything that resumes reads the state row fresh
  if (!force && isCurrent(states.get(sessionId), stat)) {
    return { status: 'skipped', messages: 0, titleEvents: 0 };
  }
  const prior = db.getTranscriptResumeState(sessionId);
  if (!force && isCurrent(prior, stat)) {
    return { status: 'skipped', messages: 0, titleEvents: 0 };
  }

  // One synchronous pass (tracker-utils extractTranscript) yields FTS rows,
  // title events and the session metadata row. Title events route by their
  // own sessionId; see extractRecord.
  for (let attempt = 0; ; attempt++) {
    let resume = null;
    if (attempt === 0 && !force && canResume(prior, file, stat) && prior.acc_json) {
      const why = utils.checkResumeState(prior.acc_json);
      if (why && why !== 'rules changed') logIndexError(sessionId, `resume state ${why}; re-reading the whole file`);
      if (!why && endsLineAt(file.filePath, prior.byte_offset)) {
        resume = { acc: prior.acc_json, start: prior.byte_offset, startLine: prior.line_no };
      }
    }
    const { messages, titleEvents, meta, end, lines, acc, hadError } =
      utils.extractTranscript(file.filePath, { fileSessionId: sessionId, resume });
    if (hadError) {
      // No state write — the session stays eligible for the next run
      logIndexError(sessionId, 'read error, will retry next run');
      return { status: 'errored', messages: 0, titleEvents: 0 };
    }
    try {
      db.indexTranscript(sessionId, {
        filePath: file.filePath,
        projectDir: file.projectDir,
        transcriptSize: stat.size,
        mtimeMs: stat.mtimeMs,
        messages,
        titleEvents,
        extractorVersion: EXTRACTOR_VERSION,
        meta,
        file: { projectPath: utils.decodeProjectPath(file.projectDir), mtime: stat.mtime.toISOString(),
          isWorktree: isWorktree(meta.cwd), authoritative: true },
        appendFrom: resume ? prior.message_count || 0 : null,
        expect: resume ? { byteOffset: prior.byte_offset, messageCount: prior.message_count } : null,
        resume: { byteOffset: end, lineNo: lines, inode: stat.ino, accJson: acc },
      });
    } catch (e) {
      // Lost the race to another writer: a whole-file pass is always consistent
      if (e && e.code === 'STALE_RESUME' && attempt === 0) continue;
      throw e;
    }
    return { status: resume ? 'appended' : 'indexed', messages: messages.length, titleEvents: titleEvents.length };
  }
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

  const r = { indexed: 0, appended: 0, skipped: 0, empty: 0, errored: 0, remaining: 0,
    messages: 0, titleEvents: 0, pruned: 0, ms: 0 };

  let i = 0;
  for (; i < allFiles.length; i++) {
    if (r.indexed + r.appended >= limit || Date.now() - t0 > budgetMs) break;
    let out;
    try {
      out = await indexOne(allFiles[i], states, { quiet, force: rebuild });
    } catch (err) {
      if (isDbLevelError(err)) throw err;
      // The transaction rolled back, so no state was recorded: the session
      // stays eligible and is retried next run
      logIndexError(path.basename(allFiles[i].filePath, '.jsonl'), err);
      out = { status: 'errored' };
    }
    if (out.status === 'skipped') r.skipped++;
    else if (out.status === 'errored') r.errored++;
    else if (out.status === 'appended') {
      r.appended++;
      r.messages += out.messages;
      r.titleEvents += out.titleEvents;
    } else if (out.status === 'indexed') {
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
  // Only real transcripts (<uuid>.jsonl): an .orphaned or .superseded copy
  // would otherwise become a bogus session row
  if (filePath && !utils.SESSION_FILE_RE.test(path.basename(filePath))) {
    return { sessionId: sessionId || path.basename(filePath), status: 'not-a-transcript', messages: 0, titleEvents: 0 };
  }
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
  try {
    const out = await indexOne(file, states, { quiet });
    return { sessionId, ...out };
  } catch (err) {
    if (isDbLevelError(err)) throw err;
    logIndexError(sessionId, err);
    return { sessionId, status: 'errored', messages: 0, titleEvents: 0 };
  }
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

const DETACH_LOG = path.join(os.homedir(), '.claude', 'logs', 'transcript-index-hook.log');

function detachIndex({ sessionId, filePath }, debounceSec) {
  const { spawn } = require('child_process');
  const target = filePath ? ['--file', filePath] : ['--session', sessionId];
  fs.mkdirSync(path.dirname(DETACH_LOG), { recursive: true });
  const log = fs.openSync(DETACH_LOG, 'a');
  const child = spawn(process.execPath, [__filename, ...target, '--debounce', String(debounceSec)], {
    detached: true,
    stdio: ['ignore', log, log],
  });
  child.unref();
  fs.closeSync(log);
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

  // --detach: re-run this single-session index in a detached child and return
  // at once. SessionEnd hooks share a 1.5 s budget, which a large transcript
  // overruns; the child's output goes to a log file, never the hook's pipes.
  if (single && flag('--detach')) {
    detachIndex(single, debounceSec);
    return;
  }

  const t0 = Date.now();
  if (single) {
    const out = await indexSession({ ...single, debounceSec, quiet });
    if (!quiet) {
      const id = (out.sessionId || '?').slice(0, 8);
      console.log(`${id}: ${out.status}` + (out.status === 'indexed' || out.status === 'appended'
        ? ` — ${out.messages} messages, ${out.titleEvents} title events, ${Date.now() - t0}ms` : ''));
    }
    db.close();
    return;
  }

  const r = await refreshTranscriptIndex({ budgetMs, limit, quiet, rebuild });
  // Full (hourly) runs also close phases left open by sessions that ended
  // without a SessionEnd hook; budgeted on-search refreshes skip it
  if (budgetMs === Infinity) {
    r.phasesClosed = db.closeStalePhases(utils.getLiveSessionIds({ allKinds: true }));
  }
  // --quiet still reports work done (one line) so hook/launchd logs stay useful
  // without the per-file chatter; a no-op run prints nothing.
  if (!quiet || r.indexed || r.appended || r.errored || r.pruned || r.phasesClosed) {
    const secs = (r.ms / 1000).toFixed(1);
    console.log(`Indexed ${r.indexed} session(s) in full and ${r.appended} by increment in ${secs}s — ${r.skipped} unchanged, ${r.empty} with no indexable text` +
      (r.errored ? `, ${r.errored} errors (will retry; see logs/transcript-index-errors.log)` : '') +
      (r.remaining ? `, ${r.remaining} still pending (budget/limit reached)` : '') +
      (r.pruned ? `, ${r.pruned} deleted sessions pruned` : '') +
      (r.titleEvents ? `, ${r.titleEvents} title events` : '') +
      (r.phasesClosed ? `, ${r.phasesClosed} stale phases closed` : '') + '.');
  }
  // Printed even under --quiet: the hourly log is where a regression shows
  if (budgetMs === Infinity) {
    try {
      const found = sanityCheck();
      if (found.length) console.log(formatSanity(found));
    } catch (e) { console.error(`transcript-index: sanity check failed: ${e.message}`); }
  }
  if (!quiet) {
    const stats = db.getTranscriptIndexStats();
    const dbSize = fs.statSync(db.TRANSCRIPTS_DB_PATH).size;
    console.log(`Index now holds ${stats.sessions} sessions, ${stats.messages} messages, ` +
      `${(stats.textBytes / 1e6).toFixed(1)} MB text. tracker-transcripts.db: ${(dbSize / 1e6).toFixed(1)} MB.`);
  }
  db.close();
}

module.exports = { indexOne, refreshTranscriptIndex, indexSession, findTranscript, isWorktree, sanityCheck, EXTRACTOR_VERSION };

if (require.main === module) {
  main().catch(err => { console.error(err); process.exit(1); });
}
