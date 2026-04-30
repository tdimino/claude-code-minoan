#!/usr/bin/env node
/**
 * quote-session.js — Capture and search notable phrases from sessions.
 *
 * Usage:
 *   node quote-session.js capture "phrase text" [--tags tag1,tag2] [--source user|assistant] [--session ID]
 *   node quote-session.js search "query text"
 *   node quote-session.js tag "tag-name" [--limit N]
 *   node quote-session.js list [--session ID] [--limit N]
 *
 * Stores tagged excerpts in tracker.db (tagged_phrases + tagged_phrase_tags),
 * searchable via FTS5.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const PROJECTS_DIR = path.join(HOME, '.claude', 'projects');
const LIB_DIR = path.join(HOME, '.claude', 'lib');

function detectCurrentSession() {
  const cwd = process.cwd();
  const encoded = '-' + cwd.split('/').filter(Boolean).join('-');
  const projDir = path.join(PROJECTS_DIR, encoded);

  if (!fs.existsSync(projDir)) return null;

  const files = fs.readdirSync(projDir)
    .filter(f => f.endsWith('.jsonl'))
    .map(f => {
      const stat = fs.statSync(path.join(projDir, f));
      return { name: f, mtime: stat.mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime);

  if (files.length === 0) return null;

  const maxAge = 10 * 60 * 1000;
  if (Date.now() - files[0].mtime > maxAge) return null;

  return path.basename(files[0].name, '.jsonl');
}

function formatAge(dateStr) {
  if (!dateStr) return 'unknown';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return mins + 'm ago';
  const hours = Math.floor(mins / 60);
  if (hours < 24) return hours + 'h ago';
  const days = Math.floor(hours / 24);
  return days + 'd ago';
}

function getCurrentPhase(db, sessionId) {
  try {
    const phase = db.getCurrentPhase(sessionId);
    return phase ? phase.phase : null;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

function captureQuote(db, sessionId, phrase, options = {}) {
  const source = ['user', 'assistant'].includes(options.source) ? options.source : 'user';
  const tags = options.tags || [];
  const phase = getCurrentPhase(db, sessionId);
  const timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, '');

  const id = db.capturePhrase(sessionId, {
    phrase,
    source,
    turnNumber: null,
    phase,
    timestamp,
    tags,
  });

  console.log(`\x1b[32m✓\x1b[0m Phrase captured (id: ${id})`);
  console.log(`  \x1b[90m"${phrase.length > 80 ? phrase.substring(0, 80) + '…' : phrase}"\x1b[0m`);
  if (tags.length > 0) console.log(`  \x1b[90mTags:\x1b[0m ${tags.join(', ')}`);
  if (phase) console.log(`  \x1b[90mPhase:\x1b[0m ${phase}`);
  console.log(`  \x1b[90mSource:\x1b[0m ${source}`);
  console.log(`  \x1b[90mSession:\x1b[0m ${sessionId.substring(0, 8)}`);
}

function searchQuotes(db, query) {
  const results = db.searchPhrases(query);

  if (results.length === 0) {
    console.log(`\x1b[33mNo phrases matching "${query}".\x1b[0m`);
    return;
  }

  console.log(`\n\x1b[1mPhrases matching "${query}"\x1b[0m (${results.length}):\n`);

  for (const r of results) {
    const age = formatAge(r.timestamp);
    const phaseTag = r.phase ? ` \x1b[36m[${r.phase}]\x1b[0m` : '';
    const tagStr = r.tags ? ` \x1b[35m#${r.tags.split(',').join(' #')}\x1b[0m` : '';
    const sourceIcon = r.source === 'assistant' ? '\x1b[34m⚙\x1b[0m' : '\x1b[32m●\x1b[0m';

    console.log(`  ${sourceIcon} \x1b[90m(${age})\x1b[0m${phaseTag}${tagStr}`);
    console.log(`    "${r.phrase}"`);
    console.log(`    \x1b[90mSession:\x1b[0m ${(r.session_id || '').substring(0, 8)}`);
    console.log('');
  }
}

function listByTag(db, tag, limit) {
  const results = db.getPhrasesWithTag(tag);
  const shown = results.slice(0, limit);

  if (shown.length === 0) {
    console.log(`\x1b[33mNo phrases tagged "${tag}".\x1b[0m`);
    return;
  }

  console.log(`\n\x1b[1mPhrases tagged #${tag}\x1b[0m (${results.length}${results.length > limit ? `, showing ${limit}` : ''}):\n`);

  for (const r of shown) {
    const age = formatAge(r.timestamp);
    const phaseTag = r.phase ? ` \x1b[36m[${r.phase}]\x1b[0m` : '';
    const allTags = r.tags ? ` \x1b[35m#${r.tags.split(',').join(' #')}\x1b[0m` : '';
    const sourceIcon = r.source === 'assistant' ? '\x1b[34m⚙\x1b[0m' : '\x1b[32m●\x1b[0m';

    console.log(`  ${sourceIcon} \x1b[90m(${age})\x1b[0m${phaseTag}${allTags}`);
    console.log(`    "${r.phrase}"`);
    console.log(`    \x1b[90mSession:\x1b[0m ${(r.session_id || '').substring(0, 8)}`);
    console.log('');
  }
}

function listPhrases(db, sessionId, limit) {
  let results;
  if (sessionId) {
    results = db.getDb().prepare(`
      SELECT tp.*, GROUP_CONCAT(tpt.tag) as tags
      FROM tagged_phrases tp
      LEFT JOIN tagged_phrase_tags tpt ON tpt.phrase_id = tp.id
      WHERE tp.session_id = ?
      GROUP BY tp.id
      ORDER BY tp.timestamp DESC
      LIMIT ?
    `).all(sessionId, limit);
  } else {
    results = db.getDb().prepare(`
      SELECT tp.*, GROUP_CONCAT(tpt.tag) as tags
      FROM tagged_phrases tp
      LEFT JOIN tagged_phrase_tags tpt ON tpt.phrase_id = tp.id
      GROUP BY tp.id
      ORDER BY tp.timestamp DESC
      LIMIT ?
    `).all(limit);
  }

  if (results.length === 0) {
    console.log('\x1b[33mNo phrases captured yet.\x1b[0m');
    return;
  }

  const scope = sessionId ? `session ${sessionId.substring(0, 8)}` : 'all sessions';
  console.log(`\n\x1b[1mCaptured Phrases\x1b[0m — ${scope} (${results.length}):\n`);

  for (const r of results) {
    const age = formatAge(r.timestamp);
    const phaseTag = r.phase ? ` \x1b[36m[${r.phase}]\x1b[0m` : '';
    const tagStr = r.tags ? ` \x1b[35m#${r.tags.split(',').join(' #')}\x1b[0m` : '';
    const sourceIcon = r.source === 'assistant' ? '\x1b[34m⚙\x1b[0m' : '\x1b[32m●\x1b[0m';

    console.log(`  ${sourceIcon} \x1b[90m(${age})\x1b[0m${phaseTag}${tagStr}`);
    console.log(`    "${r.phrase}"`);
    if (!sessionId) console.log(`    \x1b[90mSession:\x1b[0m ${(r.session_id || '').substring(0, 8)}`);
    console.log('');
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (!command || command === '--help' || command === '-h') {
    console.log('\n\x1b[33mUsage:\x1b[0m');
    console.log('  quote-session.js capture "phrase" [--tags tag1,tag2] [--source user|assistant] [--session ID]');
    console.log('  quote-session.js search "query"');
    console.log('  quote-session.js tag "tag-name" [--limit N]');
    console.log('  quote-session.js list [--session ID] [--limit N]');
    console.log('\n\x1b[90mExamples:');
    console.log('  quote-session.js capture "assumptions are the enemy" --tags design,principle');
    console.log('  quote-session.js search "assumptions"');
    console.log('  quote-session.js tag design\x1b[0m\n');
    process.exit(0);
  }

  let trackerDb;
  try {
    trackerDb = require(path.join(LIB_DIR, 'tracker-db'));
    if (!trackerDb.isAvailable()) {
      console.error('\x1b[31mtracker.db not available. Run migrate-to-sqlite.js first.\x1b[0m');
      process.exit(1);
    }
  } catch (e) {
    console.error('\x1b[31mFailed to load tracker-db: ' + e.message + '\x1b[0m');
    process.exit(1);
  }

  let sessionId = null;
  let tags = [];
  let source = 'user';
  let limit = 20;

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--session' && args[i + 1]) {
      sessionId = args[++i];
    } else if (args[i] === '--tags' && args[i + 1]) {
      tags = args[++i].split(',').map(t => t.trim()).filter(Boolean);
    } else if (args[i] === '--source' && args[i + 1]) {
      source = args[++i];
    } else if (args[i] === '--limit' && args[i + 1]) {
      limit = parseInt(args[++i], 10);
    }
  }

  if (command === 'capture') {
    const phrase = args[1];
    if (!phrase || phrase.startsWith('--')) {
      console.error('\x1b[31mUsage: quote-session.js capture "phrase text" [--tags tag1,tag2]\x1b[0m');
      process.exit(1);
    }

    if (!sessionId) {
      sessionId = detectCurrentSession();
      if (!sessionId) {
        console.error('\x1b[31mNo active session detected. Use --session ID.\x1b[0m');
        process.exit(1);
      }
    }

    captureQuote(trackerDb, sessionId, phrase, { tags, source });
  } else if (command === 'search') {
    const query = args[1];
    if (!query || query.startsWith('--')) {
      console.error('\x1b[31mUsage: quote-session.js search "query"\x1b[0m');
      process.exit(1);
    }
    searchQuotes(trackerDb, query);
  } else if (command === 'tag') {
    const tag = args[1];
    if (!tag || tag.startsWith('--')) {
      console.error('\x1b[31mUsage: quote-session.js tag "tag-name"\x1b[0m');
      process.exit(1);
    }
    listByTag(trackerDb, tag, limit);
  } else if (command === 'list') {
    if (!sessionId) sessionId = detectCurrentSession();
    listPhrases(trackerDb, sessionId, limit);
  } else {
    console.error(`\x1b[31mUnknown command: ${command}\x1b[0m`);
    process.exit(1);
  }

  trackerDb.close();
}

main();
