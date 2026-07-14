#!/usr/bin/env node
/**
 * index-transcripts.js — Build/refresh the transcript full-text index
 *
 * Usage: node index-transcripts.js [--rebuild] [--limit N] [--quiet]
 *
 * Walks all top-level session JSONL files (subagent/tool-result payloads in
 * session subdirectories are never enumerated), extracts user+assistant text,
 * and writes it to transcript_messages / transcript_fts in tracker.db.
 *
 * Incremental by default: sessions whose file size and mtime match
 * transcript_index_state are skipped. --rebuild reindexes everything.
 */

const os = require('os');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const utils = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-utils.js'));
const db = require(path.join(os.homedir(), '.claude', 'lib', 'tracker-db.js'));

const args = process.argv.slice(2);
const rebuild = args.includes('--rebuild');
const quiet = args.includes('--quiet');
const limitIdx = args.indexOf('--limit');
const limit = limitIdx !== -1 && args[limitIdx + 1] ? parseInt(args[limitIdx + 1], 10) : Infinity;

// Bump when extraction rules change (noise filters, skip prefixes, caps) —
// forces reindex of sessions indexed under older rules
const EXTRACTOR_VERSION = 4; // v4: title/nickname history extraction

// Guard against pathological single messages (huge pasted dumps)
const MAX_MESSAGE_CHARS = 20000;
// Skip system-injected turns: command wrappers, tool results rendered as user turns
const SKIP_PREFIXES = ['<command-', '<local-command', '<task-notification', '<system-reminder'];

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

async function main() {
  const t0 = Date.now();
  db.initSchema();

  const states = rebuild ? new Map() : db.getTranscriptIndexStates();
  const allFiles = utils.getAllSessionFiles();

  let indexed = 0, skipped = 0, empty = 0, errored = 0, messagesTotal = 0, titleEventsTotal = 0;

  for (const file of allFiles) {
    if (indexed >= limit) break;
    const sessionId = path.basename(file.filePath, '.jsonl');
    let stat;
    try { stat = fs.statSync(file.filePath); } catch { continue; }

    const prior = states.get(sessionId);
    if (prior && prior.transcript_size === stat.size && prior.mtime_ms === stat.mtimeMs
        && (prior.extractor_version || 1) === EXTRACTOR_VERSION) {
      skipped++;
      continue;
    }

    const { messages, titleEvents, hadError } = await extractMessages(file.filePath, sessionId);
    if (hadError) {
      // No state write — the session stays eligible for the next run
      errored++;
      if (!quiet) console.log(`  ! read error, will retry next run: ${sessionId.slice(0, 8)}`);
      continue;
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
    indexed++;
    messagesTotal += messages.length;
    titleEventsTotal += titleEvents.length;
    if (messages.length === 0) empty++;

    if (!quiet && indexed % 100 === 0) {
      console.log(`  ${indexed} indexed (${skipped} skipped) …`);
    }
  }

  // Reconcile deletions — only on full runs, where allFiles is authoritative
  let pruned = 0;
  if (limit === Infinity) {
    pruned = db.pruneTranscriptIndex(allFiles.map(f => path.basename(f.filePath, '.jsonl')));
  }

  const stats = db.getTranscriptIndexStats();
  const dbSize = fs.statSync(db.TRANSCRIPTS_DB_PATH).size;
  const secs = ((Date.now() - t0) / 1000).toFixed(1);

  console.log(`Indexed ${indexed} session(s) in ${secs}s — ${skipped} unchanged, ${empty} with no indexable text` +
    (errored ? `, ${errored} read errors (will retry)` : '') +
    (pruned ? `, ${pruned} deleted sessions pruned` : '') +
    (titleEventsTotal ? `, ${titleEventsTotal} title events` : '') + '.');
  console.log(`Index now holds ${stats.sessions} sessions, ${stats.messages} messages, ` +
    `${(stats.textBytes / 1e6).toFixed(1)} MB text. tracker-transcripts.db: ${(dbSize / 1e6).toFixed(1)} MB.`);
  db.close();
}

main().catch(err => { console.error(err); process.exit(1); });
