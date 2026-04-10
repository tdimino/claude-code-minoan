#!/usr/bin/env node
/**
 * tag-session.js — Attach manual keyword metatags to Claude Code sessions.
 *
 * Usage:
 *   node tag-session.js add <tag> [<tag>...] [--session ID]
 *   node tag-session.js remove <tag> [<tag>...] [--session ID]
 *   node tag-session.js list [--session ID]
 *   node tag-session.js clear [--session ID]
 *
 * Persistence model — two paths:
 *
 *   1. LIVE session (no --session flag, current cwd matches a session):
 *      Writes a `.pending-tags` / `.pending-tags-remove` breadcrumb at
 *      ~/.claude/session-tags/{session_id}.pending-tags
 *      The next Stop event triggers session-tags-infer.py, which reads the
 *      breadcrumb BEFORE its 3-min Qwen cooldown gate, applies the delta to
 *      the registry under fcntl lock, and deletes the breadcrumb.
 *      This mirrors the precedent set by plan-session-rename.py →
 *      `.pending-title` breadcrumbs at session-tags-infer.py:264-272.
 *
 *   2. CLOSED session (explicit --session ID, session not currently live):
 *      Writes directly to session-registry.json under fcntl lock. No hook
 *      trigger needed; the registry is the source of truth for searches.
 *
 * Session auto-detection (when --session is omitted):
 *   - No CLAUDE_SESSION_ID env var exists in slash-command bash context.
 *   - Heuristic: encode process.cwd() as `-Users-tomdimino-Desktop` and
 *     pick the most recently modified .jsonl in ~/.claude/projects/<encoded>/.
 *     Must be within the last 10 minutes to be considered "live".
 *
 * Searchability: Phase 1 of the plan merges display_tags + tags + user_tags
 * with case-insensitive dedupe in search-sessions.js --name mode, so manual
 * tags surface via `/claude-tracker-search <tag> --name` once applied.
 *
 * Plan reference: ~/.claude/plans/2026-04-10-claude-tracker-session-metatags.md
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const HOME = os.homedir();
const TAGS_DIR = path.join(HOME, '.claude', 'session-tags');
const REGISTRY_PATH = path.join(HOME, '.claude', 'session-registry.json');
const PROJECTS_DIR = path.join(HOME, '.claude', 'projects');
const LIVE_SESSION_MAX_AGE_MS = 10 * 60 * 1000;  // 10 minutes

// ---- session detection ----

/**
 * Encode a cwd path for Claude Code's projects/ directory naming.
 * /Users/tomdimino/Desktop → -Users-tomdimino-Desktop
 * NOTE: lossy if real dir names contain hyphens. Matches Claude Code's own
 * convention; see tracker-utils.js::decodeProjectPath for the reverse.
 */
function encodeCwdAsProjectDir(cwd) {
  return cwd.replace(/\//g, '-');
}

/**
 * Find the session_id for the current live Claude Code session.
 * Returns null if no live session detected.
 */
function detectCurrentSession() {
  const cwd = process.cwd();
  const encoded = encodeCwdAsProjectDir(cwd);
  const projDir = path.join(PROJECTS_DIR, encoded);

  if (!fs.existsSync(projDir)) return null;

  let entries;
  try {
    entries = fs.readdirSync(projDir)
      .filter(f => f.endsWith('.jsonl'))
      .map(f => {
        const full = path.join(projDir, f);
        try {
          return { name: f, mtime: fs.statSync(full).mtimeMs };
        } catch (e) {
          return null;
        }
      })
      .filter(Boolean)
      .sort((a, b) => b.mtime - a.mtime);
  } catch (e) {
    return null;
  }

  if (entries.length === 0) return null;

  const newest = entries[0];
  if (Date.now() - newest.mtime > LIVE_SESSION_MAX_AGE_MS) return null;

  // Verify the JSONL's actual cwd matches ours (handles lossy hyphen encoding)
  try {
    const full = path.join(projDir, newest.name);
    const fd = fs.openSync(full, 'r');
    const buf = Buffer.alloc(4096);
    const bytesRead = fs.readSync(fd, buf, 0, 4096, 0);
    fs.closeSync(fd);
    const firstLine = buf.toString('utf-8', 0, bytesRead).split('\n')[0];
    if (firstLine) {
      const parsed = JSON.parse(firstLine);
      if (parsed.cwd && parsed.cwd !== cwd) return null;
    }
  } catch (e) {
    // Can't verify — proceed with the match
  }

  return path.basename(newest.name, '.jsonl');
}

// ---- breadcrumb helpers (live sessions) ----

function ensureTagsDir() {
  try {
    fs.mkdirSync(TAGS_DIR, { recursive: true });
  } catch (e) {
    // dir exists or permission error — surface later
  }
}

/**
 * Append tags to a breadcrumb file atomically.
 * Reads existing contents, merges with new tags (dedupe case-insensitive),
 * writes to tmp, renames over target.
 */
function appendBreadcrumb(filePath, newTags) {
  let existing = [];
  if (fs.existsSync(filePath)) {
    try {
      existing = fs.readFileSync(filePath, 'utf-8')
        .split('\n')
        .map(l => l.trim())
        .filter(Boolean);
    } catch (e) { /* ignore */ }
  }

  const seen = new Set(existing.map(t => t.toLowerCase()));
  const merged = [...existing];
  for (const t of newTags) {
    const k = t.toLowerCase();
    if (!seen.has(k)) {
      merged.push(t);
      seen.add(k);
    }
  }

  const tmp = filePath + '.tmp';
  fs.writeFileSync(tmp, merged.join('\n') + '\n', 'utf-8');
  fs.renameSync(tmp, filePath);
}

// ---- registry helpers (closed sessions, direct write) ----

/**
 * Load the session registry. Returns {sessions: {...}} even if file is missing.
 */
function loadRegistry() {
  try {
    return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf-8'));
  } catch (e) {
    return { sessions: {} };
  }
}

/**
 * Atomically write the registry.
 * NOTE: Node has no portable fcntl. We rely on single-writer discipline:
 * direct registry writes only happen for closed sessions where the Stop
 * hook won't fire. Concurrent risk is low; atomic rename is our guard.
 */
function writeRegistry(registry) {
  const tmp = REGISTRY_PATH + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(registry, null, 2));
  fs.renameSync(tmp, REGISTRY_PATH);
}

/**
 * Apply add/remove to user_tags of a specific session in the registry.
 * Returns the updated user_tags array, or null if session not found AND
 * allowCreate is false.
 */
function applyToRegistry(sessionId, adds, removes, { allowCreate = false } = {}) {
  const registry = loadRegistry();
  registry.sessions = registry.sessions || {};

  let entry = registry.sessions[sessionId];
  if (!entry) {
    if (!allowCreate) return null;
    entry = { user_tags: [] };
    registry.sessions[sessionId] = entry;
  }

  const current = Array.isArray(entry.user_tags) ? [...entry.user_tags] : [];
  const seen = new Set(current.map(t => t.toLowerCase()));

  for (const a of adds) {
    if (!seen.has(a.toLowerCase())) {
      current.push(a);
      seen.add(a.toLowerCase());
    }
  }

  const removeSet = new Set(removes.map(t => t.toLowerCase()));
  const final = current.filter(t => !removeSet.has(t.toLowerCase()));

  entry.user_tags = final;
  entry.updated = new Date().toISOString().replace(/\.\d+Z$/, '');

  writeRegistry(registry);
  return final;
}

// ---- arg parsing ----

function parseArgs(argv) {
  const args = argv.slice(2);
  const result = { command: null, tags: [], session: null };

  if (args.length === 0) return result;

  result.command = args[0];

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--session' && args[i + 1]) {
      result.session = args[i + 1];
      i++;
    } else if (args[i].startsWith('--')) {
      process.stderr.write('tag-session: unknown flag: ' + args[i] + '\n');
      process.exit(2);
    } else {
      result.tags.push(args[i]);
    }
  }

  return result;
}

function usage() {
  process.stdout.write([
    'Usage:',
    '  tag-session.js add <tag> [<tag>...] [--session ID]',
    '  tag-session.js remove <tag> [<tag>...] [--session ID]',
    '  tag-session.js list [--session ID]',
    '  tag-session.js clear [--session ID]',
    '',
    'Without --session, auto-detects the current live session by finding',
    'the most recently modified JSONL in ~/.claude/projects/<cwd-encoded>/.',
    '',
  ].join('\n'));
}

// ---- commands ----

function resolveSession(explicitSession) {
  if (explicitSession) return { sessionId: explicitSession, isLive: false };

  const detected = detectCurrentSession();
  if (!detected) {
    process.stderr.write(
      'tag-session: could not detect current session.\n' +
      `  cwd: ${process.cwd()}\n` +
      '  Pass --session <id> explicitly for closed sessions.\n'
    );
    process.exit(2);
  }
  return { sessionId: detected, isLive: true };
}

function cmdAdd(tags, explicitSession) {
  if (tags.length === 0) {
    process.stderr.write('tag-session add: no tags provided\n');
    process.exit(2);
  }

  const { sessionId, isLive } = resolveSession(explicitSession);

  if (isLive) {
    // Write breadcrumb; hook applies on next Stop event.
    ensureTagsDir();
    const breadcrumb = path.join(TAGS_DIR, `${sessionId}.pending-tags`);
    appendBreadcrumb(breadcrumb, tags);
    process.stdout.write(
      `tagged ${sessionId.slice(0, 8)}: +${tags.join(' +')}` +
      ` (applies on next session stop)\n`
    );
  } else {
    // Direct registry write for closed sessions.
    const final = applyToRegistry(sessionId, tags, [], { allowCreate: true });
    process.stdout.write(
      `tagged ${sessionId.slice(0, 8)}: +${tags.join(' +')}\n` +
      `  user_tags: ${JSON.stringify(final)}\n`
    );
  }
}

function cmdRemove(tags, explicitSession) {
  if (tags.length === 0) {
    process.stderr.write('tag-session remove: no tags provided\n');
    process.exit(2);
  }

  const { sessionId, isLive } = resolveSession(explicitSession);

  if (isLive) {
    ensureTagsDir();
    const breadcrumb = path.join(TAGS_DIR, `${sessionId}.pending-tags-remove`);
    appendBreadcrumb(breadcrumb, tags);
    process.stdout.write(
      `tagged ${sessionId.slice(0, 8)}: -${tags.join(' -')}` +
      ` (applies on next session stop)\n`
    );
  } else {
    const final = applyToRegistry(sessionId, [], tags, { allowCreate: false });
    if (final === null) {
      process.stderr.write(`tag-session remove: session ${sessionId} not found in registry\n`);
      process.exit(3);
    }
    process.stdout.write(
      `tagged ${sessionId.slice(0, 8)}: -${tags.join(' -')}\n` +
      `  user_tags: ${JSON.stringify(final)}\n`
    );
  }
}

function cmdList(explicitSession) {
  const { sessionId } = resolveSession(explicitSession);

  const registry = loadRegistry();
  const entry = (registry.sessions && registry.sessions[sessionId]) || {};

  const pendingAdd = path.join(TAGS_DIR, `${sessionId}.pending-tags`);
  const pendingRemove = path.join(TAGS_DIR, `${sessionId}.pending-tags-remove`);

  let pendingAdds = [];
  let pendingRemoves = [];
  if (fs.existsSync(pendingAdd)) {
    pendingAdds = fs.readFileSync(pendingAdd, 'utf-8').split('\n').map(l => l.trim()).filter(Boolean);
  }
  if (fs.existsSync(pendingRemove)) {
    pendingRemoves = fs.readFileSync(pendingRemove, 'utf-8').split('\n').map(l => l.trim()).filter(Boolean);
  }

  process.stdout.write(`Session: ${sessionId}\n`);
  if (entry.title) process.stdout.write(`  Title: ${entry.title}\n`);

  process.stdout.write('\n  User tags:\n');
  const userTags = entry.user_tags || [];
  if (userTags.length === 0 && pendingAdds.length === 0) {
    process.stdout.write('    (none)\n');
  } else {
    for (const t of userTags) process.stdout.write(`    · ${t}\n`);
    for (const t of pendingAdds) process.stdout.write(`    · ${t} (pending add)\n`);
    for (const t of pendingRemoves) process.stdout.write(`    · ${t} (pending remove)\n`);
  }

  if (entry.display_tags && entry.display_tags.length) {
    process.stdout.write('\n  Display tags (Qwen):\n');
    for (const t of entry.display_tags) process.stdout.write(`    · ${t}\n`);
  }

  if (entry.tags && entry.tags.length) {
    process.stdout.write('\n  Auto tags (Qwen):\n');
    for (const t of entry.tags) process.stdout.write(`    · ${t}\n`);
  }
}

function cmdClear(explicitSession) {
  const { sessionId, isLive } = resolveSession(explicitSession);

  if (isLive) {
    // Collect any pending adds before deleting, so they get cleared too
    ensureTagsDir();
    const pendingAdd = path.join(TAGS_DIR, `${sessionId}.pending-tags`);
    let pendingAdds = [];
    if (fs.existsSync(pendingAdd)) {
      try {
        pendingAdds = fs.readFileSync(pendingAdd, 'utf-8').split('\n').map(l => l.trim()).filter(Boolean);
      } catch (e) { /* ignore */ }
      fs.unlinkSync(pendingAdd);
    }

    const registry = loadRegistry();
    const entry = (registry.sessions && registry.sessions[sessionId]) || {};
    const current = [...(entry.user_tags || []), ...pendingAdds];
    if (current.length === 0) {
      process.stdout.write(`tag-session clear: ${sessionId.slice(0, 8)} has no user_tags\n`);
      return;
    }

    const pendingRemove = path.join(TAGS_DIR, `${sessionId}.pending-tags-remove`);
    appendBreadcrumb(pendingRemove, current);
    process.stdout.write(
      `tagged ${sessionId.slice(0, 8)}: cleared ${current.length} tag(s) (applies on next session stop)\n`
    );
  } else {
    const registry = loadRegistry();
    const entry = registry.sessions && registry.sessions[sessionId];
    if (!entry) {
      process.stderr.write(`tag-session clear: session ${sessionId} not found in registry\n`);
      process.exit(3);
    }
    entry.user_tags = [];
    entry.updated = new Date().toISOString().replace(/\.\d+Z$/, '');
    writeRegistry(registry);
    process.stdout.write(`tagged ${sessionId.slice(0, 8)}: cleared all user_tags\n`);
  }
}

// ---- main ----

function main() {
  const { command, tags, session } = parseArgs(process.argv);

  switch (command) {
    case 'add':
      cmdAdd(tags, session);
      break;
    case 'remove':
    case 'rm':
      cmdRemove(tags, session);
      break;
    case 'list':
    case 'ls':
      cmdList(session);
      break;
    case 'clear':
      cmdClear(session);
      break;
    default:
      usage();
      process.exit(command ? 2 : 0);
  }
}

main();
