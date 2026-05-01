#!/usr/bin/env node
/**
 * One-time migration: scattered JSON/JSONL/YAML → tracker.db
 * Idempotent — uses INSERT OR IGNORE. Re-run safely.
 *
 * Usage:
 *   node migrate-to-sqlite.js              # Full migration
 *   node migrate-to-sqlite.js --incremental # Only new/changed JSONL files
 *   node migrate-to-sqlite.js --dry-run     # Count sources, don't write
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

const LIB_DIR = path.join(os.homedir(), '.claude', 'lib');
const trackerDb = require(path.join(LIB_DIR, 'tracker-db'));
const {
  loadSessionsIndex, loadSummaryCache, parseSessionEnriched,
  readSessionSlug, readCustomTitle, decodeProjectPath,
  loadGitTracking
} = require(path.join(LIB_DIR, 'tracker-utils'));

const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const REGISTRY_PATH = path.join(os.homedir(), '.claude', 'session-registry.json');
const SUMMARIES_PATH = path.join(os.homedir(), '.claude', 'session-summaries.json');
const GIT_INDEX_PATH = path.join(os.homedir(), '.claude', 'git-tracking-index.json');
const GIT_LOG_PATH = path.join(os.homedir(), '.claude', 'git-tracking.jsonl');
const HANDOFFS_DIR = path.join(os.homedir(), '.claude', 'handoffs');
const SOUL_REGISTRY_PATH = path.join(os.homedir(), '.claude', 'soul-sessions', 'registry.json');

const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const INCREMENTAL = args.includes('--incremental');
const SKIP_ENRICH = args.includes('--skip-enrich');
const BATCH_SIZE = 500;

function log(msg) { process.stdout.write(msg + '\n'); }
function progress(current, total, label) {
  if (current % 200 === 0 || current === total) {
    process.stdout.write(`\r  ${label}: ${current}/${total}`);
  }
}

// ---------------------------------------------------------------------------
// 1. Sessions
// ---------------------------------------------------------------------------

function collectSessions() {
  log('\n--- Phase 1: Sessions ---');

  const registry = loadRegistry();
  const summaries = loadSummaries();
  const sessionsIndex = loadAllSessionsIndex();

  const projectDirs = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory());

  const sessions = [];
  let jsonlCount = 0;

  for (const dir of projectDirs) {
    const projDir = path.join(PROJECTS_DIR, dir.name);
    const projectPath = decodeProjectPath(dir.name);
    const projectName = path.basename(projectPath);

    let jsonls;
    try {
      jsonls = fs.readdirSync(projDir).filter(f => f.endsWith('.jsonl'));
    } catch { continue; }

    for (const jsonl of jsonls) {
      const sessionId = path.basename(jsonl, '.jsonl');
      const filePath = path.join(projDir, jsonl);
      let stat;
      try { stat = fs.statSync(filePath); } catch { continue; }

      if (INCREMENTAL) {
        const existing = trackerDb.getSessionById(sessionId);
        if (existing && existing.transcript_size === stat.size
            && existing.summary && existing.num_turns > 0
            && existing.total_cost_usd > 0) continue;
      }

      const regEntry = registry[sessionId] || {};
      const sumEntry = summaries[sessionId] || {};
      const idxEntry = sessionsIndex[sessionId] || {};

      // Extract first line for cwd, slug
      let cwd = null;
      let slug = null;
      let firstPrompt = null;
      let createdAt = null;
      let lastUserMsgAt = null;

      try {
        const fd = fs.openSync(filePath, 'r');
        const buf = Buffer.alloc(8192);
        const bytesRead = fs.readSync(fd, buf, 0, 8192, 0);
        fs.closeSync(fd);
        const partial = buf.toString('utf-8', 0, bytesRead);
        const lines = partial.split('\n');
        for (let i = 0; i < Math.min(20, lines.length); i++) {
          if (!lines[i]) continue;
          try {
            const obj = JSON.parse(lines[i]);
            if (obj.cwd && !cwd) cwd = obj.cwd;
            if (obj.slug && !slug) slug = obj.slug;
            if (obj.type === 'user' && !firstPrompt) {
              const content = obj.message?.content;
              if (typeof content === 'string') {
                firstPrompt = content.slice(0, 500);
              } else if (Array.isArray(content)) {
                const textBlock = content.find(b => b.type === 'text');
                if (textBlock) firstPrompt = textBlock.text.slice(0, 500);
              }
            }
            if (obj.timestamp && !createdAt) createdAt = obj.timestamp;
            if (obj.type === 'user' && obj.timestamp) lastUserMsgAt = obj.timestamp;
          } catch { /* skip */ }
        }
      } catch { /* file unreadable */ }

      slug = slug || readSessionSlug(filePath) || null;

      let enriched = {};
      if (!SKIP_ENRICH) {
        try { enriched = parseSessionEnriched(filePath); } catch { /* skip */ }
      }

      const customTitle = readCustomTitle(filePath) || regEntry.title || idxEntry.customTitle || null;
      const autoTitle = sumEntry.title || null;
      const summary = regEntry.summary || sumEntry.summary || enriched.summary || idxEntry.summary || null;
      firstPrompt = firstPrompt || enriched.firstPrompt || idxEntry.firstPrompt || sumEntry.first_msg || null;

      const model = enriched.model || sumEntry.model || null;
      const modelShort = enriched.modelShort || (model ? model.replace('claude-opus-4-6', 'opus-4.6').replace(/^claude-/, '') : null);

      sessions.push({
        session_id: sessionId,
        short_id: sessionId.slice(0, 8),
        project_dir: dir.name,
        project_path: projectPath,
        project_name: projectName,
        cwd: cwd || projectPath,
        transcript_path: filePath,
        transcript_size: stat.size,
        slug,
        custom_title: customTitle,
        auto_title: autoTitle,
        summary,
        first_prompt: firstPrompt,
        created_at: createdAt || idxEntry.created || stat.birthtime.toISOString(),
        modified_at: idxEntry.modified || stat.mtime.toISOString(),
        last_user_msg_at: lastUserMsgAt,
        duration_ms: enriched.totalDurationMs || 0,
        model,
        model_short: modelShort,
        version: enriched.version || null,
        num_turns: enriched.numTurns || sumEntry.num_turns || idxEntry.messageCount || 0,
        total_input_tokens: enriched.totalInputTokens || 0,
        total_output_tokens: enriched.totalOutputTokens || 0,
        cache_read_tokens: enriched.cacheReadTokens || 0,
        cache_creation_tokens: enriched.cacheCreationTokens || 0,
        total_cost_usd: enriched.totalCostUsd || sumEntry.total_cost_usd || 0,
        git_branch: idxEntry.gitBranch || null,
        git_remote: null,
        is_worktree: enriched.isWorktree ? 1 : 0,
        is_sidechain: idxEntry.isSidechain ? 1 : 0,
        is_running: 0,
        pid: null,
      });

      jsonlCount++;
    }
  }

  log(`\n  Found ${jsonlCount} JSONL files, ${Object.keys(registry).length} registry entries, ${Object.keys(summaries).length} cached summaries`);

  if (DRY_RUN) {
    log(`  [DRY RUN] Would insert ${sessions.length} sessions`);
    return sessions.length;
  }

  // Batch insert
  for (let i = 0; i < sessions.length; i += BATCH_SIZE) {
    const batch = sessions.slice(i, i + BATCH_SIZE);
    trackerDb.bulkInsertSessions(batch);
    progress(Math.min(i + BATCH_SIZE, sessions.length), sessions.length, 'Sessions');
  }
  log('');

  return sessions.length;
}

// ---------------------------------------------------------------------------
// 2. Tags
// ---------------------------------------------------------------------------

function migrateTags() {
  log('\n--- Phase 2: Session Tags ---');

  const registry = loadRegistry();
  const tags = [];

  // Only insert tags for sessions that exist in the DB
  const existingIds = new Set(
    trackerDb.getDb().prepare('SELECT session_id FROM sessions').all().map(r => r.session_id)
  );

  let skipped = 0;
  for (const [sessionId, entry] of Object.entries(registry)) {
    if (!existingIds.has(sessionId)) { skipped++; continue; }
    const updated = entry.updated || new Date().toISOString();

    if (entry.tags && Array.isArray(entry.tags)) {
      for (const tag of entry.tags) {
        tags.push({ session_id: sessionId, tag, tag_type: 'auto', source: 'migration:session-registry', created_at: updated });
      }
    }
    if (entry.display_tags && Array.isArray(entry.display_tags)) {
      for (const tag of entry.display_tags) {
        tags.push({ session_id: sessionId, tag, tag_type: 'display', source: 'migration:session-registry', created_at: updated });
      }
    }
    if (entry.user_tags && Array.isArray(entry.user_tags)) {
      for (const tag of entry.user_tags) {
        tags.push({ session_id: sessionId, tag, tag_type: 'user', source: 'migration:session-registry', created_at: updated });
      }
    }
  }
  if (skipped) log(`  Skipped ${skipped} registry entries (no matching JSONL)`);

  log(`  Found ${tags.length} tags across ${Object.keys(registry).length} sessions`);

  if (DRY_RUN) {
    log(`  [DRY RUN] Would insert ${tags.length} tags`);
    return tags.length;
  }

  for (let i = 0; i < tags.length; i += BATCH_SIZE) {
    trackerDb.bulkInsertTags(tags.slice(i, i + BATCH_SIZE));
    progress(Math.min(i + BATCH_SIZE, tags.length), tags.length, 'Tags');
  }
  log('');

  return tags.length;
}

// ---------------------------------------------------------------------------
// 3. Git Tracking
// ---------------------------------------------------------------------------

function migrateGitTracking() {
  log('\n--- Phase 3: Git Tracking ---');

  if (!fs.existsSync(GIT_INDEX_PATH)) {
    log('  No git-tracking-index.json found, skipping');
    return 0;
  }

  const index = loadGitTracking();
  const trackingRows = [];
  const commitRows = [];

  const existingIds = new Set(
    trackerDb.getDb().prepare('SELECT session_id FROM sessions').all().map(r => r.session_id)
  );

  // sessions map: sessionId -> { repos: { repoPath: { remote, branch, commits, first_seen, last_seen } } }
  const sessions = index.sessions || {};

  for (const [sessionId, sessionData] of Object.entries(sessions)) {
    if (!existingIds.has(sessionId)) continue;
    const repos = sessionData.repos || {};
    for (const [repoPath, repoData] of Object.entries(repos)) {
      trackingRows.push({
        session_id: sessionId,
        repo_path: repoPath,
        remote_url: repoData.remote || null,
        branch: repoData.branch || null,
        first_seen: repoData.first_seen || new Date().toISOString(),
        last_seen: repoData.last_seen || new Date().toISOString(),
      });

      const commits = repoData.commits || [];
      for (const commit of commits) {
        commitRows.push({
          session_id: sessionId,
          repo_path: repoPath,
          commit_hash: commit.hash || commit,
          commit_msg: commit.message || null,
          branch: repoData.branch || null,
          remote_url: repoData.remote || null,
          timestamp: commit.timestamp || repoData.last_seen || new Date().toISOString(),
        });
      }
    }
  }

  log(`  Found ${trackingRows.length} repo associations, ${commitRows.length} commits`);

  if (DRY_RUN) {
    log(`  [DRY RUN] Would insert ${trackingRows.length} tracking rows, ${commitRows.length} commits`);
    return trackingRows.length + commitRows.length;
  }

  for (let i = 0; i < trackingRows.length; i += BATCH_SIZE) {
    trackerDb.bulkInsertGitTracking(trackingRows.slice(i, i + BATCH_SIZE));
  }

  for (let i = 0; i < commitRows.length; i += BATCH_SIZE) {
    trackerDb.bulkInsertGitCommits(commitRows.slice(i, i + BATCH_SIZE));
  }

  log(`  Inserted ${trackingRows.length} tracking rows, ${commitRows.length} commits`);
  return trackingRows.length + commitRows.length;
}

// ---------------------------------------------------------------------------
// 4. Git Operations (streaming JSONL)
// ---------------------------------------------------------------------------

async function migrateGitOperations() {
  log('\n--- Phase 4: Git Operations ---');

  if (!fs.existsSync(GIT_LOG_PATH)) {
    log('  No git-tracking.jsonl found, skipping');
    return 0;
  }

  const stat = fs.statSync(GIT_LOG_PATH);
  log(`  Reading ${GIT_LOG_PATH} (${(stat.size / 1024 / 1024).toFixed(1)}MB)`);

  if (DRY_RUN) {
    const content = fs.readFileSync(GIT_LOG_PATH, 'utf-8');
    const lineCount = content.split('\n').filter(l => l.trim()).length;
    log(`  [DRY RUN] Would insert ~${lineCount} operations`);
    return lineCount;
  }

  const rl = readline.createInterface({
    input: fs.createReadStream(GIT_LOG_PATH),
    crlfDelay: Infinity,
  });

  let batch = [];
  let count = 0;

  for await (const line of rl) {
    if (!line.trim()) continue;
    try {
      const obj = JSON.parse(line);
      batch.push({
        session_id: obj.session_id || obj.sessionId || '',
        short_id: obj.short_id || obj.sessionShort || null,
        repo_path: obj.repo_path || obj.repoPath || obj.cwd || '',
        remote_url: obj.remote_url || obj.remote || null,
        branch: obj.branch || null,
        operation: obj.operation || obj.type || 'unknown',
        command: obj.command || obj.cmd || null,
        cwd: obj.cwd || null,
        commit_hash: obj.commit_hash || obj.commitHash || null,
        commit_msg: obj.commit_msg || obj.commitMsg || null,
        timestamp: obj.timestamp || new Date().toISOString(),
      });

      if (batch.length >= BATCH_SIZE) {
        trackerDb.bulkInsertGitOperations(batch);
        count += batch.length;
        batch = [];
        progress(count, 10000, 'Git ops');
      }
    } catch { /* skip malformed lines */ }
  }

  if (batch.length > 0) {
    trackerDb.bulkInsertGitOperations(batch);
    count += batch.length;
  }

  log(`\n  Inserted ${count} git operations`);
  return count;
}

// ---------------------------------------------------------------------------
// 5. Handoffs
// ---------------------------------------------------------------------------

function migrateHandoffs() {
  log('\n--- Phase 5: Handoffs ---');

  if (!fs.existsSync(HANDOFFS_DIR)) {
    log('  No handoffs directory found, skipping');
    return 0;
  }

  let yamlFiles;
  try {
    yamlFiles = fs.readdirSync(HANDOFFS_DIR).filter(f => f.endsWith('.yaml') || f.endsWith('.yml'));
  } catch { return 0; }

  log(`  Found ${yamlFiles.length} handoff files`);

  if (DRY_RUN) {
    log(`  [DRY RUN] Would insert ${yamlFiles.length} handoffs`);
    return yamlFiles.length;
  }

  const existingIds = new Set(
    trackerDb.getDb().prepare('SELECT session_id FROM sessions').all().map(r => r.session_id)
  );

  const rows = [];
  let skipped = 0;
  for (const file of yamlFiles) {
    try {
      const content = fs.readFileSync(path.join(HANDOFFS_DIR, file), 'utf-8');
      const parsed = parseSimpleYaml(content);
      const sessionId = parsed.session_id || path.basename(file, path.extname(file));

      if (!existingIds.has(sessionId)) { skipped++; continue; }

      rows.push({
        session_id: sessionId,
        timestamp: parsed.timestamp || new Date().toISOString(),
        trigger: parsed.trigger || null,
        cwd: parsed.cwd || null,
        project: parsed.project || null,
        objective: parsed.objective || null,
        completed: parsed.completed ? JSON.stringify(parsed.completed) : null,
        decisions: parsed.decisions ? JSON.stringify(parsed.decisions) : null,
        blockers: parsed.blockers ? JSON.stringify(parsed.blockers) : null,
        next_steps: parsed.next_steps ? JSON.stringify(parsed.next_steps) : null,
        raw_yaml: content,
      });
    } catch { /* skip malformed files */ }
  }

  if (skipped) log(`  Skipped ${skipped} handoffs (no matching session)`);

  for (let i = 0; i < rows.length; i += BATCH_SIZE) {
    trackerDb.bulkInsertHandoffs(rows.slice(i, i + BATCH_SIZE));
  }

  log(`  Inserted ${rows.length} handoffs`);
  return rows.length;
}

// ---------------------------------------------------------------------------
// 6. Soul Sessions
// ---------------------------------------------------------------------------

function migrateSoulSessions() {
  log('\n--- Phase 6: Soul Sessions ---');

  if (!fs.existsSync(SOUL_REGISTRY_PATH)) {
    log('  No soul-sessions/registry.json found, skipping');
    return 0;
  }

  let data;
  try {
    data = JSON.parse(fs.readFileSync(SOUL_REGISTRY_PATH, 'utf-8'));
  } catch { return 0; }

  const sessions = data.sessions || {};
  log(`  Found ${Object.keys(sessions).length} soul sessions`);

  if (DRY_RUN) {
    log(`  [DRY RUN] Would insert ${Object.keys(sessions).length} soul sessions`);
    return Object.keys(sessions).length;
  }

  const existingIds = new Set(
    trackerDb.getDb().prepare('SELECT session_id FROM sessions').all().map(r => r.session_id)
  );
  let inserted = 0;
  for (const [sessionId, entry] of Object.entries(sessions)) {
    if (!existingIds.has(sessionId)) continue;
    try {
      trackerDb.upsertSoulSession({
        session_id: sessionId,
        short_id: entry.short_id || sessionId.slice(0, 8),
        cwd: entry.cwd || null,
        project: entry.project || null,
        started_at: entry.started_at || null,
        last_active: entry.last_active || null,
        pid: entry.pid || null,
        slack_channel: entry.slack_channel || null,
        topic: entry.topic || null,
        summary: entry.summary || null,
        model: entry.model || null,
      });
      inserted++;
    } catch { /* skip */ }
  }

  log(`  Inserted ${Object.keys(sessions).length} soul sessions`);
  return Object.keys(sessions).length;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

let _registry = null;
function loadRegistry() {
  if (_registry) return _registry;
  try {
    _registry = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf-8')).sessions || {};
  } catch { _registry = {}; }
  return _registry;
}

let _summaries = null;
function loadSummaries() {
  if (_summaries) return _summaries;
  _summaries = loadSummaryCache();
  return _summaries;
}

function loadAllSessionsIndex() {
  const result = {};
  try {
    const dirs = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true }).filter(d => d.isDirectory());
    for (const dir of dirs) {
      const idxPath = path.join(PROJECTS_DIR, dir.name, 'sessions-index.json');
      if (!fs.existsSync(idxPath)) continue;
      try {
        const data = JSON.parse(fs.readFileSync(idxPath, 'utf-8'));
        const entries = data.entries || [];
        for (const entry of entries) {
          result[entry.sessionId] = entry;
        }
      } catch { /* skip */ }
    }
  } catch { /* skip */ }
  return result;
}

function parseSimpleYaml(content) {
  const result = {};
  let currentKey = null;
  let currentList = null;

  for (const line of content.split('\n')) {
    // Top-level key: value
    const kvMatch = line.match(/^(\w[\w_]*)\s*:\s*(.*)$/);
    if (kvMatch) {
      if (currentKey && currentList) {
        result[currentKey] = currentList;
        currentList = null;
      }
      currentKey = kvMatch[1];
      let value = kvMatch[2].trim();

      if (value === '' || value === '[]') {
        // May start a list or be empty
        if (value === '[]') {
          result[currentKey] = [];
          currentKey = null;
        }
        continue;
      }

      // Strip quotes
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }

      result[currentKey] = value;
      currentList = null;
      continue;
    }

    // List item
    const listMatch = line.match(/^- (.+)$/);
    if (listMatch && currentKey) {
      if (!currentList) currentList = [];
      currentList.push(listMatch[1].trim());
      continue;
    }
  }

  if (currentKey && currentList) {
    result[currentKey] = currentList;
  }

  return result;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const startTime = Date.now();

  log('=== SQLite Tracker Migration ===');
  log(`Database: ${trackerDb.DB_PATH}`);
  log(`Mode: ${DRY_RUN ? 'DRY RUN' : INCREMENTAL ? 'INCREMENTAL' : 'FULL'}`);
  log(`Enrichment: ${SKIP_ENRICH ? 'SKIPPED (fast mode)' : 'ENABLED (reads JSONL head+tail)'}`);

  if (!DRY_RUN) {
    trackerDb.initSchema();
  }

  const sessionCount = collectSessions();
  const tagCount = migrateTags();
  const gitCount = migrateGitTracking();
  const gitOpsCount = await migrateGitOperations();
  const handoffCount = migrateHandoffs();
  const soulCount = migrateSoulSessions();

  if (!DRY_RUN) {
    log('\n--- Phase 7: Rebuild FTS Indexes ---');
    trackerDb.rebuildFTS();
    log('  FTS rebuilt');
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

  log('\n=== Migration Complete ===');
  log(`  Sessions:       ${sessionCount}`);
  log(`  Tags:           ${tagCount}`);
  log(`  Git tracking:   ${gitCount}`);
  log(`  Git operations: ${gitOpsCount}`);
  log(`  Handoffs:       ${handoffCount}`);
  log(`  Soul sessions:  ${soulCount}`);
  log(`  Time:           ${elapsed}s`);

  if (!DRY_RUN) {
    const dbSize = (fs.statSync(trackerDb.DB_PATH).size / 1024 / 1024).toFixed(1);
    log(`  DB size:        ${dbSize}MB`);
    log(`  DB path:        ${trackerDb.DB_PATH}`);

    const count = trackerDb.getSessionCount();
    log(`  Verified:       ${count} sessions in DB`);
  }

  trackerDb.close();
}

main().catch(err => {
  console.error('Migration failed:', err);
  trackerDb.close();
  process.exit(1);
});
