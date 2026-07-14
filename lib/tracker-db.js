/**
 * SQLite API for claude-tracker-suite
 * Singleton lazy-open pattern over better-sqlite3 (synchronous)
 */

const path = require('path');
const fs = require('fs');
const os = require('os');

const DB_PATH = path.join(os.homedir(), '.claude', 'tracker.db');
const TRANSCRIPTS_DB_PATH = path.join(os.homedir(), '.claude', 'tracker-transcripts.db');
const LIB_DIR = path.join(os.homedir(), '.claude', 'lib');

let _db = null;

function getDb() {
  if (_db) return _db;

  const Database = require(path.join(LIB_DIR, 'node_modules', 'better-sqlite3'));
  _db = new Database(DB_PATH);

  _db.pragma('journal_mode = WAL');
  _db.pragma('foreign_keys = ON');
  _db.pragma('busy_timeout = 5000');
  _db.pragma('synchronous = NORMAL');
  _db.pragma('cache_size = -8000');

  return _db;
}

function isAvailable() {
  try {
    return fs.existsSync(DB_PATH) && fs.statSync(DB_PATH).size > 0;
  } catch { return false; }
}

function close() {
  if (_db) { _db.close(); _db = null; _transcriptsAttached = false; }
}

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const SCHEMA_VERSION = 4;

const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS sessions (
    session_id        TEXT PRIMARY KEY,
    short_id          TEXT NOT NULL,
    project_dir       TEXT NOT NULL,
    project_path      TEXT NOT NULL,
    project_name      TEXT NOT NULL,
    cwd               TEXT,
    transcript_path   TEXT,
    transcript_size   INTEGER DEFAULT 0,
    slug              TEXT,
    custom_title      TEXT,
    auto_title        TEXT,
    summary           TEXT,
    first_prompt      TEXT,
    created_at        TEXT NOT NULL,
    modified_at       TEXT NOT NULL,
    last_user_msg_at  TEXT,
    duration_ms       INTEGER DEFAULT 0,
    model             TEXT,
    model_short       TEXT,
    version           TEXT,
    num_turns         INTEGER DEFAULT 0,
    total_input_tokens    INTEGER DEFAULT 0,
    total_output_tokens   INTEGER DEFAULT 0,
    cache_read_tokens     INTEGER DEFAULT 0,
    cache_creation_tokens INTEGER DEFAULT 0,
    total_cost_usd    REAL DEFAULT 0.0,
    git_branch        TEXT,
    git_remote        TEXT,
    is_worktree       INTEGER DEFAULT 0,
    is_sidechain      INTEGER DEFAULT 0,
    is_running        INTEGER DEFAULT 0,
    pid               INTEGER,
    indexed_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

CREATE TABLE IF NOT EXISTS session_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    tag_type    TEXT NOT NULL CHECK(tag_type IN ('user','auto','display')),
    source      TEXT,
    phase       TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    removed_at  TEXT,
    UNIQUE(session_id, tag, tag_type)
);

CREATE TABLE IF NOT EXISTS git_tracking (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    repo_path   TEXT NOT NULL,
    remote_url  TEXT,
    branch      TEXT,
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL,
    UNIQUE(session_id, repo_path)
);

CREATE TABLE IF NOT EXISTS git_operations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL,
    short_id      TEXT,
    repo_path     TEXT NOT NULL,
    remote_url    TEXT,
    branch        TEXT,
    operation     TEXT NOT NULL,
    command       TEXT,
    cwd           TEXT,
    commit_hash   TEXT,
    commit_msg    TEXT,
    timestamp     TEXT NOT NULL,
    UNIQUE(session_id, repo_path, operation, timestamp)
);

CREATE TABLE IF NOT EXISTS git_commits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    repo_path   TEXT NOT NULL,
    remote_url  TEXT,
    branch      TEXT,
    commit_hash TEXT NOT NULL,
    commit_msg  TEXT,
    timestamp   TEXT NOT NULL,
    UNIQUE(session_id, commit_hash)
);

CREATE TABLE IF NOT EXISTS handoffs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    timestamp      TEXT NOT NULL,
    trigger        TEXT,
    cwd            TEXT,
    project        TEXT,
    objective      TEXT,
    completed      TEXT,
    decisions      TEXT,
    blockers       TEXT,
    next_steps     TEXT,
    raw_yaml       TEXT,
    UNIQUE(session_id, timestamp)
);

CREATE TABLE IF NOT EXISTS soul_sessions (
    session_id    TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    short_id      TEXT,
    cwd           TEXT,
    project       TEXT,
    started_at    TEXT,
    last_active   TEXT,
    pid           INTEGER,
    slack_channel TEXT,
    topic         TEXT,
    summary       TEXT,
    model         TEXT
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    label           TEXT NOT NULL,
    turn_number     INTEGER,
    summary         TEXT,
    phase           TEXT,
    git_branch      TEXT,
    git_commit_hash TEXT,
    files_modified  TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    metadata        TEXT
);

CREATE TABLE IF NOT EXISTS phases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    phase       TEXT NOT NULL CHECK(phase IN (
        'exploring','planning','deepening','implementing',
        'testing','reviewing','debugging','committing',
        'deploying','discussing'
    )),
    turn_start  INTEGER NOT NULL,
    turn_end    INTEGER,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    duration_ms INTEGER,
    trigger     TEXT CHECK(trigger IN ('auto','manual','checkpoint')),
    confidence  REAL,
    tool_counts TEXT,
    metadata    TEXT
);

CREATE TABLE IF NOT EXISTS tagged_phrases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    phrase      TEXT NOT NULL,
    source      TEXT NOT NULL CHECK(source IN ('user','assistant')),
    turn_number INTEGER,
    phase       TEXT,
    timestamp   TEXT NOT NULL,
    metadata    TEXT
);

CREATE TABLE IF NOT EXISTS tagged_phrase_tags (
    phrase_id   INTEGER NOT NULL REFERENCES tagged_phrases(id) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    PRIMARY KEY (phrase_id, tag)
);

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    description TEXT
);

CREATE TABLE IF NOT EXISTS title_history (
    id             INTEGER PRIMARY KEY,
    session_id     TEXT NOT NULL,
    title          TEXT NOT NULL,
    source         TEXT NOT NULL CHECK (source IN ('user','slug','cache','summarizer')),
    observed_at    TEXT,
    observed_in    TEXT,
    first_seen_seq INTEGER,
    recorded_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now')),
    UNIQUE(session_id, source, title, observed_in, first_seen_seq)
);
`;

const INDEXES_SQL = `
CREATE INDEX IF NOT EXISTS idx_sessions_short_id ON sessions(short_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_modified ON sessions(modified_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_project_path ON sessions(project_path);
CREATE INDEX IF NOT EXISTS idx_sessions_model ON sessions(model);
CREATE INDEX IF NOT EXISTS idx_session_tags_session ON session_tags(session_id);
CREATE INDEX IF NOT EXISTS idx_session_tags_tag ON session_tags(tag);
CREATE INDEX IF NOT EXISTS idx_git_tracking_session ON git_tracking(session_id);
CREATE INDEX IF NOT EXISTS idx_git_tracking_repo ON git_tracking(repo_path);
CREATE INDEX IF NOT EXISTS idx_git_operations_ts ON git_operations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_git_operations_session ON git_operations(session_id);
CREATE INDEX IF NOT EXISTS idx_git_commits_ts ON git_commits(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_git_commits_session ON git_commits(session_id);
CREATE INDEX IF NOT EXISTS idx_handoffs_session ON handoffs(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_session ON checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_phase ON checkpoints(phase);
CREATE INDEX IF NOT EXISTS idx_phases_session ON phases(session_id);
CREATE INDEX IF NOT EXISTS idx_phases_phase ON phases(phase);
CREATE INDEX IF NOT EXISTS idx_phases_started ON phases(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_tagged_phrases_session ON tagged_phrases(session_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_phases_one_open ON phases(session_id) WHERE ended_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_checkpoints_label ON checkpoints(session_id, label);
CREATE UNIQUE INDEX IF NOT EXISTS idx_git_ops_natural_key ON git_operations(session_id, repo_path, operation, timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS idx_handoffs_natural_key ON handoffs(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_title_history_session ON title_history(session_id, first_seen_seq);
CREATE INDEX IF NOT EXISTS idx_title_history_observed_in ON title_history(observed_in);
`;

const FTS_SQL = `
CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
    session_id UNINDEXED, custom_title, auto_title, slug, summary, first_prompt,
    content='sessions', content_rowid='rowid',
    tokenize='porter unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS phrases_fts USING fts5(
    id UNINDEXED, phrase,
    content='tagged_phrases', content_rowid='rowid',
    tokenize='porter unicode61'
);

`;

const FTS_TRIGGERS_SQL = `
CREATE TRIGGER IF NOT EXISTS sessions_ai AFTER INSERT ON sessions BEGIN
    INSERT INTO sessions_fts(rowid, session_id, custom_title, auto_title, slug, summary, first_prompt)
    VALUES (new.rowid, new.session_id, new.custom_title, new.auto_title, new.slug, new.summary, new.first_prompt);
END;

CREATE TRIGGER IF NOT EXISTS sessions_ad AFTER DELETE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, session_id, custom_title, auto_title, slug, summary, first_prompt)
    VALUES ('delete', old.rowid, old.session_id, old.custom_title, old.auto_title, old.slug, old.summary, old.first_prompt);
END;

CREATE TRIGGER IF NOT EXISTS sessions_au AFTER UPDATE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, session_id, custom_title, auto_title, slug, summary, first_prompt)
    VALUES ('delete', old.rowid, old.session_id, old.custom_title, old.auto_title, old.slug, old.summary, old.first_prompt);
    INSERT INTO sessions_fts(rowid, session_id, custom_title, auto_title, slug, summary, first_prompt)
    VALUES (new.rowid, new.session_id, new.custom_title, new.auto_title, new.slug, new.summary, new.first_prompt);
END;

CREATE TRIGGER IF NOT EXISTS phrases_ai AFTER INSERT ON tagged_phrases BEGIN
    INSERT INTO phrases_fts(rowid, id, phrase)
    VALUES (new.rowid, new.id, new.phrase);
END;

CREATE TRIGGER IF NOT EXISTS phrases_ad AFTER DELETE ON tagged_phrases BEGIN
    INSERT INTO phrases_fts(phrases_fts, rowid, id, phrase)
    VALUES ('delete', old.rowid, old.id, old.phrase);
END;

CREATE TRIGGER IF NOT EXISTS phrases_au AFTER UPDATE ON tagged_phrases BEGIN
    INSERT INTO phrases_fts(phrases_fts, rowid, id, phrase)
    VALUES ('delete', old.rowid, old.id, old.phrase);
    INSERT INTO phrases_fts(rowid, id, phrase)
    VALUES (new.rowid, new.id, new.phrase);
END;

`;

// ---------------------------------------------------------------------------
// Sidecar transcript database — tracker-transcripts.db
//
// The transcript index (~130K messages, ~100MB text + FTS) lives in its own
// file, ATTACHed on demand via ensureTranscripts(). Hooks that write one
// session row per event open a ~10MB tracker.db, not a ~300MB one. Unqualified
// table names resolve into the attached schema because main no longer defines
// them; all pre-split call sites work unchanged after calling
// ensureTranscripts().
// ---------------------------------------------------------------------------

const TRANSCRIPTS_SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS transcripts.transcript_messages (
    id          INTEGER PRIMARY KEY,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL CHECK(role IN ('user','assistant')),
    seq         INTEGER NOT NULL,
    text        TEXT NOT NULL,
    UNIQUE(session_id, seq)
);

CREATE TABLE IF NOT EXISTS transcripts.transcript_index_state (
    session_id      TEXT PRIMARY KEY,
    file_path       TEXT NOT NULL,
    project_dir     TEXT,
    transcript_size INTEGER NOT NULL,
    mtime_ms        INTEGER NOT NULL,
    message_count   INTEGER DEFAULT 0,
    extractor_version INTEGER DEFAULT 1,
    indexed_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

CREATE INDEX IF NOT EXISTS transcripts.idx_transcript_messages_session ON transcript_messages(session_id);
`;

const TRANSCRIPTS_FTS_SQL = `
CREATE VIRTUAL TABLE IF NOT EXISTS transcripts.transcript_fts USING fts5(
    session_id UNINDEXED, role UNINDEXED, text,
    content='transcript_messages', content_rowid='id',
    tokenize='porter unicode61'
);
`;

const TRANSCRIPTS_TRIGGERS_SQL = `
CREATE TRIGGER IF NOT EXISTS transcripts.transcripts_ai AFTER INSERT ON transcript_messages BEGIN
    INSERT INTO transcript_fts(rowid, session_id, role, text)
    VALUES (new.id, new.session_id, new.role, new.text);
END;

CREATE TRIGGER IF NOT EXISTS transcripts.transcripts_ad AFTER DELETE ON transcript_messages BEGIN
    INSERT INTO transcript_fts(transcript_fts, rowid, session_id, role, text)
    VALUES ('delete', old.id, old.session_id, old.role, old.text);
END;

CREATE TRIGGER IF NOT EXISTS transcripts.transcripts_au AFTER UPDATE ON transcript_messages BEGIN
    INSERT INTO transcript_fts(transcript_fts, rowid, session_id, role, text)
    VALUES ('delete', old.id, old.session_id, old.role, old.text);
    INSERT INTO transcript_fts(rowid, session_id, role, text)
    VALUES (new.id, new.session_id, new.role, new.text);
END;
`;

let _transcriptsAttached = false;

/**
 * Attach and initialize the sidecar transcript DB. Idempotent and cheap after
 * the first call. Also migrates legacy in-main transcript tables into the
 * sidecar on first contact (one-time, then drops them from main).
 */
function ensureTranscripts() {
  const db = getDb();
  if (_transcriptsAttached) return db;

  db.prepare('ATTACH DATABASE ? AS transcripts').run(TRANSCRIPTS_DB_PATH);
  db.pragma('transcripts.journal_mode = WAL');
  db.exec(TRANSCRIPTS_SCHEMA_SQL);

  // One-time migration: pre-split DBs carry the transcript tables in main
  const legacy = db.prepare(
    "SELECT name FROM main.sqlite_master WHERE type='table' AND name='transcript_messages'"
  ).get();
  if (legacy) {
    const sidecarEmpty = db.prepare('SELECT COUNT(*) c FROM transcripts.transcript_messages').get().c === 0;
    db.transaction(() => {
      if (sidecarEmpty) {
        // Explicit column lists — SELECT * matches by POSITION, and legacy DBs
        // that gained extractor_version via ALTER TABLE carry it after
        // indexed_at, swapping the two values into the sidecar (observed:
        // every version check failed and forced a full 1084-session reindex)
        const legacyCols = db.prepare('PRAGMA main.table_info(transcript_index_state)')
          .all().map(c => c.name);
        const verExpr = legacyCols.includes('extractor_version') ? 'extractor_version' : '1';
        db.exec(`
          INSERT INTO transcripts.transcript_messages (id, session_id, role, seq, text)
            SELECT id, session_id, role, seq, text FROM main.transcript_messages;
          INSERT INTO transcripts.transcript_index_state
            (session_id, file_path, project_dir, transcript_size, mtime_ms, message_count, extractor_version, indexed_at)
            SELECT session_id, file_path, project_dir, transcript_size, mtime_ms, message_count, ${verExpr}, indexed_at
            FROM main.transcript_index_state;
        `);
      }
      db.exec(`
        DROP TRIGGER IF EXISTS main.transcripts_ai;
        DROP TRIGGER IF EXISTS main.transcripts_ad;
        DROP TRIGGER IF EXISTS main.transcripts_au;
        DROP TABLE IF EXISTS main.transcript_fts;
        DROP TABLE IF EXISTS main.transcript_messages;
        DROP TABLE IF EXISTS main.transcript_index_state;
      `);
    })();
  }

  db.exec(TRANSCRIPTS_FTS_SQL);
  db.exec(TRANSCRIPTS_TRIGGERS_SQL);
  if (legacy) {
    db.exec("INSERT INTO transcripts.transcript_fts(transcript_fts) VALUES('rebuild')");
    try { db.exec('VACUUM main'); } catch { /* free pages persist until a manual VACUUM */ }
  }
  _transcriptsAttached = true;
  return db;
}

function initSchema() {
  const db = getDb();
  db.exec(SCHEMA_SQL);
  db.exec(INDEXES_SQL);
  db.exec(FTS_SQL);
  db.exec(FTS_TRIGGERS_SQL);

  const existing = db.prepare('SELECT MAX(version) as v FROM schema_version').get();
  if (!existing || !existing.v) {
    db.prepare('INSERT OR IGNORE INTO schema_version (version, description) VALUES (?, ?)')
      .run(SCHEMA_VERSION, 'Schema v3: transcript full-text index');
  } else if (existing.v < 2) {
    db.exec(`
      DELETE FROM git_operations WHERE id NOT IN (
        SELECT MIN(id) FROM git_operations GROUP BY session_id, repo_path, operation, timestamp
      );
      DELETE FROM handoffs WHERE id NOT IN (
        SELECT MIN(id) FROM handoffs GROUP BY session_id, timestamp
      );
    `);
    db.prepare('INSERT OR IGNORE INTO schema_version (version, description) VALUES (?, ?)')
      .run(2, 'Dedup git_operations/handoffs, add unique constraints and partial indexes');
  }
  if (existing && existing.v && existing.v < 3) {
    db.prepare('INSERT OR IGNORE INTO schema_version (version, description) VALUES (?, ?)')
      .run(3, 'Transcript full-text index: transcript_messages + transcript_fts + index state');
  }
  if (existing && existing.v && existing.v < 4) {
    db.prepare('INSERT OR IGNORE INTO schema_version (version, description) VALUES (?, ?)')
      .run(4, 'Title/nickname history: title_history table');
  }
  // transcript_index_state lives in the sidecar (extractor_version inline in
  // its schema); pre-versioning legacy mains are handled during migration
}

// ---------------------------------------------------------------------------
// Session queries
// ---------------------------------------------------------------------------

function getRecentSessions({ limit = 20, project, model, since, running } = {}) {
  const db = getDb();
  let sql = 'SELECT * FROM sessions WHERE 1=1';
  const params = {};

  if (project) { sql += ' AND project_path LIKE @project'; params.project = `%${project}%`; }
  if (model) { sql += ' AND (model = @model OR model_short = @model)'; params.model = model; }
  if (since) { sql += ' AND modified_at > @since'; params.since = since; }
  if (running !== undefined) { sql += ' AND is_running = @running'; params.running = running ? 1 : 0; }

  sql += ' ORDER BY modified_at DESC LIMIT @limit';
  params.limit = limit;

  return db.prepare(sql).all(params);
}

function getSessionById(sessionId) {
  const db = getDb();
  if (sessionId.length < 36) {
    return db.prepare('SELECT * FROM sessions WHERE short_id = ? OR session_id LIKE ?')
      .get(sessionId, `${sessionId}%`);
  }
  return db.prepare('SELECT * FROM sessions WHERE session_id = ?').get(sessionId);
}

function searchSessions(query, { limit = 20, nameOnly = false, project, since } = {}) {
  const db = getDb();

  const run = (ftsQuery) => {
    const params = {};
    // --name searches summaries too, matching the file-backed searchByName()
    params.query = nameOnly ? `{custom_title auto_title slug summary} : (${ftsQuery})` : ftsQuery;
    // bm25 weights per column: session_id(unindexed), custom_title, auto_title, slug, summary, first_prompt
    let sql = `SELECT s.*, bm25(sessions_fts, 0, 3.0, 2.0, 1.0, 2.0, 1.5) AS rank
               FROM sessions s
               JOIN sessions_fts ON sessions_fts.rowid = s.rowid
               WHERE sessions_fts MATCH @query`;
    if (project) { sql += ' AND s.project_path LIKE @project'; params.project = `%${project}%`; }
    if (since) { sql += ' AND s.modified_at > @since'; params.since = since; }
    sql += ' ORDER BY rank LIMIT @limit';
    params.limit = limit;
    return db.prepare(sql).all(params);
  };

  // AND across tokens (with synonym expansion) first; OR fallback for recall
  let rows = run(buildFtsQuery(query, { joiner: ' AND ' }));
  let mode = 'AND';
  if (rows.length === 0 && /\s/.test(query.trim())) {
    rows = run(buildFtsQuery(query, { joiner: ' OR ' }));
    mode = 'OR';
  }
  return rows.map(r => ({ ...r, mode }));
}

function getSessionCount() {
  return getDb().prepare('SELECT COUNT(*) as count FROM sessions').get().count;
}

function upsertSession(session) {
  const db = getDb();
  const sql = `INSERT INTO sessions (
    session_id, short_id, project_dir, project_path, project_name,
    cwd, transcript_path, transcript_size, slug,
    custom_title, auto_title, summary, first_prompt,
    created_at, modified_at, last_user_msg_at, duration_ms,
    model, model_short, version,
    num_turns, total_input_tokens, total_output_tokens,
    cache_read_tokens, cache_creation_tokens, total_cost_usd,
    git_branch, git_remote, is_worktree, is_sidechain, is_running, pid
  ) VALUES (
    @session_id, @short_id, @project_dir, @project_path, @project_name,
    @cwd, @transcript_path, @transcript_size, @slug,
    @custom_title, @auto_title, @summary, @first_prompt,
    @created_at, @modified_at, @last_user_msg_at, @duration_ms,
    @model, @model_short, @version,
    @num_turns, @total_input_tokens, @total_output_tokens,
    @cache_read_tokens, @cache_creation_tokens, @total_cost_usd,
    @git_branch, @git_remote, @is_worktree, @is_sidechain, @is_running, @pid
  ) ON CONFLICT(session_id) DO UPDATE SET
    custom_title = COALESCE(excluded.custom_title, sessions.custom_title),
    auto_title = COALESCE(excluded.auto_title, sessions.auto_title),
    summary = COALESCE(excluded.summary, sessions.summary),
    first_prompt = COALESCE(excluded.first_prompt, sessions.first_prompt),
    modified_at = excluded.modified_at,
    last_user_msg_at = COALESCE(excluded.last_user_msg_at, sessions.last_user_msg_at),
    duration_ms = COALESCE(excluded.duration_ms, sessions.duration_ms),
    model = COALESCE(excluded.model, sessions.model),
    model_short = COALESCE(excluded.model_short, sessions.model_short),
    num_turns = CASE WHEN excluded.num_turns > 0 THEN excluded.num_turns ELSE COALESCE(sessions.num_turns, 0) END,
    total_input_tokens = CASE WHEN excluded.total_input_tokens > 0 THEN excluded.total_input_tokens ELSE COALESCE(sessions.total_input_tokens, 0) END,
    total_output_tokens = CASE WHEN excluded.total_output_tokens > 0 THEN excluded.total_output_tokens ELSE COALESCE(sessions.total_output_tokens, 0) END,
    cache_read_tokens = CASE WHEN excluded.cache_read_tokens > 0 THEN excluded.cache_read_tokens ELSE COALESCE(sessions.cache_read_tokens, 0) END,
    cache_creation_tokens = CASE WHEN excluded.cache_creation_tokens > 0 THEN excluded.cache_creation_tokens ELSE COALESCE(sessions.cache_creation_tokens, 0) END,
    total_cost_usd = CASE WHEN excluded.total_cost_usd > 0 THEN excluded.total_cost_usd ELSE COALESCE(sessions.total_cost_usd, 0) END,
    transcript_size = COALESCE(excluded.transcript_size, sessions.transcript_size),
    is_running = excluded.is_running,
    pid = excluded.pid,
    indexed_at = strftime('%Y-%m-%dT%H:%M:%S','now')`;

  return db.prepare(sql).run(session);
}

// ---------------------------------------------------------------------------
// Tag operations
// ---------------------------------------------------------------------------

function addTags(sessionId, tags, tagType, source, phase) {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT INTO session_tags (session_id, tag, tag_type, source, phase)
    VALUES (@sessionId, @tag, @tagType, @source, @phase)
    ON CONFLICT(session_id, tag, tag_type) DO UPDATE SET
      removed_at = NULL,
      source = COALESCE(excluded.source, session_tags.source),
      phase = COALESCE(excluded.phase, session_tags.phase)
  `);

  const run = db.transaction((tags) => {
    for (const tag of tags) {
      stmt.run({ sessionId, tag, tagType: tagType, source: source || null, phase: phase || null });
    }
  });
  run(tags);
}

function removeTags(sessionId, tags) {
  const db = getDb();
  const stmt = db.prepare(`
    UPDATE session_tags SET removed_at = strftime('%Y-%m-%dT%H:%M:%S','now')
    WHERE session_id = ? AND tag = ? AND removed_at IS NULL
  `);
  const run = db.transaction((tags) => {
    for (const tag of tags) { stmt.run(sessionId, tag); }
  });
  run(tags);
}

function getTags(sessionId) {
  const db = getDb();
  const rows = db.prepare(
    'SELECT tag, tag_type FROM session_tags WHERE session_id = ? AND removed_at IS NULL'
  ).all(sessionId);

  const result = { user: [], auto: [], display: [] };
  for (const r of rows) {
    if (result[r.tag_type]) result[r.tag_type].push(r.tag);
  }
  return result;
}

function getTagHistory(sessionId) {
  return getDb().prepare(
    'SELECT * FROM session_tags WHERE session_id = ? ORDER BY created_at'
  ).all(sessionId);
}

function searchByTag(tag) {
  return getDb().prepare(`
    SELECT s.* FROM sessions s
    JOIN session_tags t ON t.session_id = s.session_id
    WHERE t.tag = ? AND t.removed_at IS NULL
    ORDER BY s.modified_at DESC
  `).all(tag);
}

function getTagFrequency({ since, project } = {}) {
  const db = getDb();
  let sql = `SELECT t.tag, t.tag_type, COUNT(*) as count
             FROM session_tags t
             JOIN sessions s ON s.session_id = t.session_id
             WHERE t.removed_at IS NULL`;
  const params = {};
  if (since) { sql += ' AND t.created_at > @since'; params.since = since; }
  if (project) { sql += ' AND s.project_path LIKE @project'; params.project = `%${project}%`; }
  sql += ' GROUP BY t.tag, t.tag_type ORDER BY count DESC';
  return db.prepare(sql).all(params);
}

// ---------------------------------------------------------------------------
// Checkpoints
// ---------------------------------------------------------------------------

function createCheckpoint(sessionId, { label, turnNumber, summary, phase, gitBranch, gitCommitHash, filesModified, metadata } = {}) {
  return getDb().prepare(`
    INSERT INTO checkpoints (session_id, label, turn_number, summary, phase, git_branch, git_commit_hash, files_modified, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(sessionId, label, turnNumber || null, summary || null, phase || null,
         gitBranch || null, gitCommitHash || null,
         filesModified ? (typeof filesModified === 'string' ? filesModified : JSON.stringify(filesModified)) : null,
         metadata ? (typeof metadata === 'string' ? metadata : JSON.stringify(metadata)) : null);
}

function getCheckpoints(sessionId) {
  return getDb().prepare(
    'SELECT * FROM checkpoints WHERE session_id = ? ORDER BY turn_number, created_at'
  ).all(sessionId);
}

function getCheckpointByLabel(sessionId, label) {
  return getDb().prepare(
    'SELECT * FROM checkpoints WHERE session_id = ? AND label = ?'
  ).get(sessionId, label);
}

function getRecentCheckpoints({ limit = 20, phase, since, project } = {}) {
  const db = getDb();
  let sql = `SELECT c.*, s.project_name FROM checkpoints c
             JOIN sessions s ON s.session_id = c.session_id WHERE 1=1`;
  const params = {};
  if (phase) { sql += ' AND c.phase = @phase'; params.phase = phase; }
  if (since) { sql += ' AND c.created_at > @since'; params.since = since; }
  if (project) { sql += ' AND s.project_path LIKE @project'; params.project = `%${project}%`; }
  sql += ' ORDER BY c.created_at DESC LIMIT @limit';
  params.limit = limit;
  return db.prepare(sql).all(params);
}

// ---------------------------------------------------------------------------
// Phase tracking
// ---------------------------------------------------------------------------

function recordPhaseTransition(sessionId, { phase, turnNumber, trigger, confidence, toolCounts } = {}) {
  const db = getDb();

  const transition = db.transaction(() => {
    const current = db.prepare(
      'SELECT id, started_at FROM phases WHERE session_id = ? AND ended_at IS NULL'
    ).get(sessionId);

    if (current) {
      const now = new Date().toISOString();
      const durationMs = new Date(now) - new Date(current.started_at);
      db.prepare(
        'UPDATE phases SET ended_at = ?, turn_end = ?, duration_ms = ? WHERE id = ?'
      ).run(now, turnNumber, durationMs, current.id);
    }

    return db.prepare(`
      INSERT INTO phases (session_id, phase, turn_start, started_at, trigger, confidence, tool_counts)
      VALUES (?, ?, ?, strftime('%Y-%m-%dT%H:%M:%S','now'), ?, ?, ?)
    `).run(sessionId, phase, turnNumber, trigger || 'auto', confidence || null,
           toolCounts ? JSON.stringify(toolCounts) : null);
  });

  return transition();
}

function getCurrentPhase(sessionId) {
  return getDb().prepare(
    'SELECT * FROM phases WHERE session_id = ? AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1'
  ).get(sessionId);
}

function getPhaseHistory(sessionId) {
  return getDb().prepare(
    'SELECT * FROM phases WHERE session_id = ? ORDER BY started_at'
  ).all(sessionId);
}

function getPhaseAnalytics({ phase, since, project } = {}) {
  const db = getDb();
  let sql = `SELECT p.phase, COUNT(*) as count,
                    AVG(p.duration_ms) as avg_duration_ms,
                    SUM(p.duration_ms) as total_duration_ms,
                    AVG(p.confidence) as avg_confidence
             FROM phases p
             JOIN sessions s ON s.session_id = p.session_id
             WHERE p.ended_at IS NOT NULL`;
  const params = {};
  if (phase) { sql += ' AND p.phase = @phase'; params.phase = phase; }
  if (since) { sql += ' AND p.started_at > @since'; params.since = since; }
  if (project) { sql += ' AND s.project_path LIKE @project'; params.project = `%${project}%`; }
  sql += ' GROUP BY p.phase ORDER BY count DESC';
  return db.prepare(sql).all(params);
}

// ---------------------------------------------------------------------------
// Tagged phrases
// ---------------------------------------------------------------------------

function capturePhrase(sessionId, { phrase, source, turnNumber, phase, timestamp, tags } = {}) {
  const db = getDb();

  const result = db.prepare(`
    INSERT INTO tagged_phrases (session_id, phrase, source, turn_number, phase, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(sessionId, phrase, source, turnNumber || null, phase || null, timestamp);

  if (tags && tags.length > 0) {
    const stmt = db.prepare('INSERT OR IGNORE INTO tagged_phrase_tags (phrase_id, tag) VALUES (?, ?)');
    const run = db.transaction((tags) => {
      for (const tag of tags) { stmt.run(result.lastInsertRowid, tag); }
    });
    run(tags);
  }

  return result.lastInsertRowid;
}

function searchPhrases(query) {
  const ftsQuery = query.split(/\s+/).map(w => `"${w.replace(/"/g, '')}"`).join(' ');
  return getDb().prepare(`
    SELECT tp.*, GROUP_CONCAT(tpt.tag) as tags
    FROM tagged_phrases tp
    LEFT JOIN tagged_phrase_tags tpt ON tpt.phrase_id = tp.id
    JOIN phrases_fts ON phrases_fts.rowid = tp.rowid
    WHERE phrases_fts MATCH ?
    GROUP BY tp.id
    ORDER BY rank
  `).all(ftsQuery);
}

function getPhrasesWithTag(tag) {
  return getDb().prepare(`
    SELECT tp.*, GROUP_CONCAT(tpt2.tag) as tags
    FROM tagged_phrases tp
    JOIN tagged_phrase_tags tpt ON tpt.phrase_id = tp.id AND tpt.tag = ?
    LEFT JOIN tagged_phrase_tags tpt2 ON tpt2.phrase_id = tp.id
    GROUP BY tp.id
    ORDER BY tp.timestamp DESC
  `).all(tag);
}

// ---------------------------------------------------------------------------
// Git tracking
// ---------------------------------------------------------------------------

function upsertGitTracking(sessionId, repoPath, remoteUrl, branch) {
  return getDb().prepare(`
    INSERT INTO git_tracking (session_id, repo_path, remote_url, branch, first_seen, last_seen)
    VALUES (?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%S','now'), strftime('%Y-%m-%dT%H:%M:%S','now'))
    ON CONFLICT(session_id, repo_path) DO UPDATE SET
      last_seen = strftime('%Y-%m-%dT%H:%M:%S','now'),
      remote_url = COALESCE(excluded.remote_url, git_tracking.remote_url),
      branch = COALESCE(excluded.branch, git_tracking.branch)
  `).run(sessionId, repoPath, remoteUrl || null, branch || null);
}

function insertGitOperation(op) {
  return getDb().prepare(`
    INSERT OR IGNORE INTO git_operations (session_id, short_id, repo_path, remote_url, branch, operation, command, cwd, commit_hash, commit_msg, timestamp)
    VALUES (@session_id, @short_id, @repo_path, @remote_url, @branch, @operation, @command, @cwd, @commit_hash, @commit_msg, @timestamp)
  `).run(op);
}

function insertGitCommit(sessionId, repoPath, commitHash, commitMsg, branch, remoteUrl, timestamp) {
  return getDb().prepare(`
    INSERT OR IGNORE INTO git_commits (session_id, repo_path, commit_hash, commit_msg, branch, remote_url, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(sessionId, repoPath, commitHash, commitMsg || null, branch || null, remoteUrl || null, timestamp);
}

function getSessionsForRepo(repoPath) {
  return getDb().prepare(`
    SELECT s.* FROM sessions s
    JOIN git_tracking gt ON gt.session_id = s.session_id
    WHERE gt.repo_path = ?
    ORDER BY s.modified_at DESC
  `).all(repoPath);
}

function getReposForSession(sessionId) {
  return getDb().prepare(
    'SELECT * FROM git_tracking WHERE session_id = ?'
  ).all(sessionId);
}

function getRecentCommits({ hours = 24, repoPath } = {}) {
  const db = getDb();
  const since = new Date(Date.now() - hours * 3600000).toISOString();
  let sql = 'SELECT * FROM git_commits WHERE timestamp > @since';
  const params = { since };
  if (repoPath) { sql += ' AND repo_path = @repoPath'; params.repoPath = repoPath; }
  sql += ' ORDER BY timestamp DESC';
  return db.prepare(sql).all(params);
}

// ---------------------------------------------------------------------------
// Handoffs
// ---------------------------------------------------------------------------

function insertHandoff(handoff) {
  return getDb().prepare(`
    INSERT OR IGNORE INTO handoffs (session_id, timestamp, trigger, cwd, project, objective, completed, decisions, blockers, next_steps, raw_yaml)
    VALUES (@session_id, @timestamp, @trigger, @cwd, @project, @objective, @completed, @decisions, @blockers, @next_steps, @raw_yaml)
  `).run(handoff);
}

function getHandoffsForSession(sessionId) {
  return getDb().prepare(
    'SELECT * FROM handoffs WHERE session_id = ? ORDER BY timestamp'
  ).all(sessionId);
}

// ---------------------------------------------------------------------------
// Soul sessions
// ---------------------------------------------------------------------------

function upsertSoulSession(soul) {
  return getDb().prepare(`
    INSERT INTO soul_sessions (session_id, short_id, cwd, project, started_at, last_active, pid, slack_channel, topic, summary, model)
    VALUES (@session_id, @short_id, @cwd, @project, @started_at, @last_active, @pid, @slack_channel, @topic, @summary, @model)
    ON CONFLICT(session_id) DO UPDATE SET
      last_active = excluded.last_active,
      pid = excluded.pid,
      topic = COALESCE(excluded.topic, soul_sessions.topic),
      summary = COALESCE(excluded.summary, soul_sessions.summary)
  `).run(soul);
}

// ---------------------------------------------------------------------------
// Transcript full-text index
// ---------------------------------------------------------------------------

const SYNONYMS_PATH = path.join(os.homedir(), '.claude', 'skills', 'claude-tracker-suite', 'references', 'synonyms.json');
let _synonymGroups = null;

/**
 * Load synonym groups from the skill's references/synonyms.json.
 * Format: {"groups": [["twitter","x","banner",...], ...]}
 * Each token expands to its whole group (bidirectional by construction).
 */
function loadSynonymGroups() {
  if (_synonymGroups) return _synonymGroups;
  try {
    const data = JSON.parse(fs.readFileSync(SYNONYMS_PATH, 'utf8'));
    _synonymGroups = new Map();
    for (const group of data.groups || []) {
      const words = group.map(w => String(w).toLowerCase()).filter(Boolean);
      for (const w of words) {
        const existing = _synonymGroups.get(w) || new Set();
        words.forEach(x => existing.add(x));
        _synonymGroups.set(w, existing);
      }
    }
  } catch {
    _synonymGroups = new Map();
  }
  return _synonymGroups;
}

function quoteFtsToken(w) {
  return `"${w.replace(/"/g, '')}"`;
}

/**
 * Build an FTS5 query string from a free-text query.
 * Each token expands to (token OR synonym...) when a synonym group matches;
 * tokens join with AND (default) or OR (joiner=' OR ' for the recall fallback).
 */
function buildFtsQuery(query, { joiner = ' AND ', synonyms = true } = {}) {
  const groups = synonyms ? loadSynonymGroups() : new Map();
  const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
  const parts = [...new Set(tokens.map(tok => {
    const syns = groups.get(tok);
    if (syns && syns.size > 1) {
      return '(' + [...syns].map(quoteFtsToken).join(' OR ') + ')';
    }
    return quoteFtsToken(tok);
  }))];
  return parts.join(joiner);
}

/**
 * Search transcript bodies via FTS5, aggregated to session level.
 *
 * Each query token (expanded by its synonym group) is searched independently,
 * then results intersect at the SESSION level — terms may appear in different
 * messages of the same session, which raw FTS5 'a AND b' (per-row) cannot do.
 * If no session contains every token group, falls back to OR (union), ranked
 * by groups-matched then combined bm25.
 *
 * Returns [{session_id, best_rank, match_count, matched_groups, total_groups,
 *           snippets, mode, ...session-metadata}]
 */
function searchTranscripts(query, { limit = 20, project, since } = {}) {
  const db = ensureTranscripts();
  const groups = loadSynonymGroups();
  const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return [];

  // Dedupe: two query tokens in the same synonym group (e.g. "twitter banner")
  // must count as ONE group, not a doubled penalty/boost
  const groupQueries = [...new Set(tokens.map(tok => {
    const syns = groups.get(tok);
    return (syns && syns.size > 1)
      ? [...syns].map(quoteFtsToken).join(' OR ')
      : quoteFtsToken(tok);
  }))];

  // Full-coverage aggregation per token group (no LIMIT — a truncated set
  // would break the session-level intersection for common terms).
  // Snippets are fetched later, only for the winning sessions.
  const perGroupStmt = db.prepare(`
    SELECT session_id, MIN(rank) AS best_rank, COUNT(*) AS match_count
    FROM transcript_fts
    WHERE transcript_fts MATCH ?
    GROUP BY session_id`);

  // A group whose FTS query THROWS is recorded and excluded from the
  // intersection — silently treating it as "no matches" would empty the AND
  // set and mislead via the OR fallback. Empty-but-valid groups keep their
  // correct AND semantics.
  const droppedTerms = [];
  const survivingQueries = [];
  let perGroup = groupQueries.map(q => {
    try {
      const m = new Map(perGroupStmt.all(q).map(r => [r.session_id, r]));
      survivingQueries.push(q);
      return m;
    } catch {
      droppedTerms.push(q);
      return null;
    }
  }).filter(Boolean);
  if (perGroup.length === 0) return [];

  let ids = [...perGroup[0].keys()].filter(id => perGroup.every(m => m.has(id)));
  let mode = 'AND';
  if (ids.length === 0 && perGroup.length > 1) {
    mode = 'OR';
    ids = [...new Set(perGroup.flatMap(m => [...m.keys()]))];
  }
  if (ids.length === 0) return [];

  // Scoring: IDF-weighted SATURATED DENSITY with a short-session damp.
  // Density (matches per message) is what actually separates "the session
  // about X" from "a long session that mentions X" in this corpus; the
  // saturation d/(d+K) caps its dynamic range so one dense group can't
  // dominate, and the credibility damp stops trivially short sessions from
  // scoring perfect density (raw log-density ranked 1-message sessions at
  // the theoretical maximum; message-count BM25 saturated to the IDF sum and
  // stopped discriminating at all). Positive IDF keeps rare terms dominant
  // and behaves correctly in OR mode.
  const DENSITY_K = 0.05;          // half-saturation density (5% of messages)
  const CRED_FULL_MSGS = 10;       // sessions this long get full credibility
  const idxStats = db.prepare('SELECT COUNT(*) c FROM transcript_index_state').get();
  const totalSessions = idxStats.c || 1;
  const groupWeights = perGroup.map(m => Math.log(1 + totalSessions / Math.max(1, m.size)));
  const msgCounts = new Map(
    db.prepare('SELECT session_id, message_count FROM transcript_index_state').all()
      .map(r => [r.session_id, r.message_count || 1])
  );

  const scored = ids.map(id => {
    const msgs = Math.max(1, msgCounts.get(id) || 1);
    const credibility = Math.min(1, Math.log(1 + msgs) / Math.log(1 + CRED_FULL_MSGS));
    let score = 0, matchCount = 0, matchedGroups = 0;
    perGroup.forEach((m, gi) => {
      const r = m.get(id);
      if (!r) return;
      const density = r.match_count / msgs;
      score += groupWeights[gi] * (density / (density + DENSITY_K)) * credibility;
      matchCount += r.match_count;
      matchedGroups++;
    });
    return {
      session_id: id, score, match_count: matchCount,
      matched_groups: matchedGroups, total_groups: perGroup.length, mode,
    };
  });
  scored.sort((a, b) => b.matched_groups - a.matched_groups || b.score - a.score);

  // Walk the FULL ranked list — truncating before applying project/since
  // filters would silently drop qualifying sessions ranked below the cutoff
  const candidates = scored;
  const metaStmt = db.prepare(`
    SELECT st.file_path, st.project_dir,
           s.project_path, s.project_name, s.custom_title, s.auto_title,
           s.slug, s.summary, s.modified_at, s.model_short
    FROM transcript_index_state st
    LEFT JOIN sessions s ON s.session_id = st.session_id
    WHERE st.session_id = ?`);

  // Snippets only for sessions we will actually return (session_id is
  // UNINDEXED in FTS5, so equality works as a post-filter on the match set)
  const orQuery = survivingQueries.length > 1 ? survivingQueries.map(q => `(${q})`).join(' OR ') : survivingQueries[0];
  const snippetStmt = db.prepare(`
    SELECT snippet(transcript_fts, 2, '>>', '<<', ' … ', 24) AS snip
    FROM transcript_fts
    WHERE transcript_fts MATCH ? AND session_id = ?
    ORDER BY rank LIMIT 3`);

  const out = [];
  for (const c of candidates) {
    if (out.length >= limit) break;
    const meta = metaStmt.get(c.session_id) || {};
    if (project && !(meta.project_path || '').includes(project)) continue;
    if (since && !((meta.modified_at || '') > since)) continue;
    let snippets = [];
    try { snippets = snippetStmt.all(orQuery, c.session_id).map(r => r.snip); } catch {}
    out.push({ ...c, ...meta, snippets, dropped_terms: droppedTerms });
  }
  return out;
}

/** Read incremental-skip state for the transcript indexer, keyed by session_id. */
function getTranscriptIndexStates() {
  const db = ensureTranscripts();
  const map = new Map();
  for (const row of db.prepare('SELECT * FROM transcript_index_state').all()) {
    map.set(row.session_id, row);
  }
  return map;
}

/**
 * (Re)index one session's messages. Replaces any prior rows for the session
 * in a single transaction; FTS stays in sync via triggers.
 * messages: [{role: 'user'|'assistant', text}]
 */
function indexTranscript(sessionId, { filePath, projectDir, transcriptSize, mtimeMs, messages, titleEvents = [], extractorVersion = 1 }) {
  const db = ensureTranscripts();
  const del = db.prepare('DELETE FROM transcript_messages WHERE session_id = ?');
  const ins = db.prepare('INSERT INTO transcript_messages (session_id, role, seq, text) VALUES (?, ?, ?, ?)');
  const state = db.prepare(`
    INSERT INTO transcript_index_state (session_id, file_path, project_dir, transcript_size, mtime_ms, message_count, extractor_version, indexed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%S','now'))
    ON CONFLICT(session_id) DO UPDATE SET
      file_path = excluded.file_path,
      project_dir = excluded.project_dir,
      transcript_size = excluded.transcript_size,
      mtime_ms = excluded.mtime_ms,
      message_count = excluded.message_count,
      extractor_version = excluded.extractor_version,
      indexed_at = excluded.indexed_at
  `);
  // Title events route by the event's own session_id (a /rename after /resume
  // lands in the active file but targets another session — trust the line, not
  // the file). All events observed in THIS file are replaced wholesale, so a
  // rescan under new extraction rules self-heals, including live-capture rows
  // the sync hook wrote with observed_in = this session.
  const delTitles = db.prepare('DELETE FROM title_history WHERE observed_in = ?');
  const insTitle = db.prepare(`
    INSERT OR IGNORE INTO title_history (session_id, title, source, observed_at, observed_in, first_seen_seq)
    VALUES (?, ?, ?, ?, ?, ?)
  `);

  const run = db.transaction(() => {
    del.run(sessionId);
    messages.forEach((m, i) => ins.run(sessionId, m.role, i, m.text));
    delTitles.run(sessionId);
    for (const t of titleEvents) {
      insTitle.run(t.sessionId, t.title, t.source, t.observedAt || null, sessionId, t.firstSeenSeq ?? null);
    }
    state.run(sessionId, filePath, projectDir || null, transcriptSize, mtimeMs, messages.length, extractorVersion);
  });
  run();
}

/**
 * Record a single title event outside an indexer pass (sync hook live capture,
 * summarizer provenance, cache import). observedIn must be non-NULL for the
 * UNIQUE key to dedupe repeats — use the session id for live capture, or a
 * source label ('session-summaries.json', 'backfill') for imports.
 */
function insertTitleEvent({ sessionId, title, source, observedAt = null, observedIn, firstSeenSeq = null }) {
  // NULLs are pairwise-distinct in SQLite UNIQUE constraints — a NULL
  // observed_in would make INSERT OR IGNORE duplicate on every repeat call
  if (!observedIn) throw new Error('insertTitleEvent: observedIn is required for dedup');
  const db = getDb();
  return db.prepare(`
    INSERT OR IGNORE INTO title_history (session_id, title, source, observed_at, observed_in, first_seen_seq)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(sessionId, title, source, observedAt, observedIn, firstSeenSeq).changes > 0;
}

/** Chronological title timeline for a session (timestamped first, then by observation order). */
function getTitleHistory(sessionId) {
  const db = getDb();
  return db.prepare(`
    SELECT title, source, observed_at, observed_in, first_seen_seq, recorded_at
    FROM title_history WHERE session_id = ?
    ORDER BY observed_at IS NULL, observed_at, first_seen_seq
  `).all(sessionId);
}

/** Sessions whose PAST titles match a term but whose current titles may not. */
function searchTitleHistory(term, limit = 20) {
  const db = getDb();
  return db.prepare(`
    SELECT th.session_id, th.title, th.source, th.observed_at,
           s.custom_title, s.auto_title, s.project_name, s.modified_at
    FROM title_history th
    JOIN sessions s ON s.session_id = th.session_id
    WHERE th.title LIKE ? COLLATE NOCASE
    ORDER BY s.modified_at DESC LIMIT ?
  `).all(`%${term}%`, limit);
}

/** Remove index rows for sessions whose transcript files no longer exist on disk. */
function pruneTranscriptIndex(liveSessionIds) {
  const db = ensureTranscripts();
  const live = new Set(liveSessionIds);
  const stale = db.prepare('SELECT session_id FROM transcript_index_state').all()
    .map(r => r.session_id)
    .filter(id => !live.has(id));
  if (stale.length === 0) return 0;
  const delMsgs = db.prepare('DELETE FROM transcript_messages WHERE session_id = ?');
  const delState = db.prepare('DELETE FROM transcript_index_state WHERE session_id = ?');
  const run = db.transaction(() => {
    for (const id of stale) { delMsgs.run(id); delState.run(id); }
  });
  run();
  return stale.length;
}

function getTranscriptIndexStats() {
  const db = ensureTranscripts();
  return {
    sessions: db.prepare('SELECT COUNT(DISTINCT session_id) c FROM transcript_messages').get().c,
    messages: db.prepare('SELECT COUNT(*) c FROM transcript_messages').get().c,
    textBytes: db.prepare('SELECT COALESCE(SUM(LENGTH(text)),0) b FROM transcript_messages').get().b,
  };
}

// ---------------------------------------------------------------------------
// FTS rebuild
// ---------------------------------------------------------------------------

function rebuildFTS() {
  const db = ensureTranscripts();
  db.exec("INSERT INTO sessions_fts(sessions_fts) VALUES('rebuild')");
  db.exec("INSERT INTO phrases_fts(phrases_fts) VALUES('rebuild')");
  db.exec("INSERT INTO transcript_fts(transcript_fts) VALUES('rebuild')");
}

// ---------------------------------------------------------------------------
// Bulk operations (for migration)
// ---------------------------------------------------------------------------

function bulkInsertSessions(sessions) {
  const db = getDb();
  const stmt = db.prepare(`INSERT INTO sessions (
    session_id, short_id, project_dir, project_path, project_name,
    cwd, transcript_path, transcript_size, slug,
    custom_title, auto_title, summary, first_prompt,
    created_at, modified_at, last_user_msg_at, duration_ms,
    model, model_short, version,
    num_turns, total_input_tokens, total_output_tokens,
    cache_read_tokens, cache_creation_tokens, total_cost_usd,
    git_branch, git_remote, is_worktree, is_sidechain, is_running, pid
  ) VALUES (
    @session_id, @short_id, @project_dir, @project_path, @project_name,
    @cwd, @transcript_path, @transcript_size, @slug,
    @custom_title, @auto_title, @summary, @first_prompt,
    @created_at, @modified_at, @last_user_msg_at, @duration_ms,
    @model, @model_short, @version,
    @num_turns, @total_input_tokens, @total_output_tokens,
    @cache_read_tokens, @cache_creation_tokens, @total_cost_usd,
    @git_branch, @git_remote, @is_worktree, @is_sidechain, @is_running, @pid
  ) ON CONFLICT(session_id) DO UPDATE SET
    custom_title = COALESCE(excluded.custom_title, sessions.custom_title),
    auto_title = COALESCE(excluded.auto_title, sessions.auto_title),
    summary = COALESCE(excluded.summary, sessions.summary),
    first_prompt = COALESCE(excluded.first_prompt, sessions.first_prompt),
    modified_at = excluded.modified_at,
    transcript_size = COALESCE(excluded.transcript_size, sessions.transcript_size),
    model = COALESCE(excluded.model, sessions.model),
    model_short = COALESCE(excluded.model_short, sessions.model_short),
    num_turns = CASE WHEN excluded.num_turns > 0 THEN excluded.num_turns ELSE COALESCE(sessions.num_turns, 0) END,
    total_input_tokens = CASE WHEN excluded.total_input_tokens > 0 THEN excluded.total_input_tokens ELSE COALESCE(sessions.total_input_tokens, 0) END,
    total_output_tokens = CASE WHEN excluded.total_output_tokens > 0 THEN excluded.total_output_tokens ELSE COALESCE(sessions.total_output_tokens, 0) END,
    cache_read_tokens = CASE WHEN excluded.cache_read_tokens > 0 THEN excluded.cache_read_tokens ELSE COALESCE(sessions.cache_read_tokens, 0) END,
    cache_creation_tokens = CASE WHEN excluded.cache_creation_tokens > 0 THEN excluded.cache_creation_tokens ELSE COALESCE(sessions.cache_creation_tokens, 0) END,
    total_cost_usd = CASE WHEN excluded.total_cost_usd > 0 THEN excluded.total_cost_usd ELSE COALESCE(sessions.total_cost_usd, 0) END,
    duration_ms = CASE WHEN excluded.duration_ms > 0 THEN excluded.duration_ms ELSE COALESCE(sessions.duration_ms, 0) END,
    indexed_at = strftime('%Y-%m-%dT%H:%M:%S','now')`);

  const run = db.transaction((rows) => {
    for (const row of rows) { stmt.run(row); }
  });
  run(sessions);
}

function bulkInsertTags(tags) {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT OR IGNORE INTO session_tags (session_id, tag, tag_type, source, created_at)
    VALUES (@session_id, @tag, @tag_type, @source, @created_at)
  `);
  const run = db.transaction((rows) => {
    for (const row of rows) { stmt.run(row); }
  });
  run(tags);
}

function bulkInsertGitTracking(rows) {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT OR IGNORE INTO git_tracking (session_id, repo_path, remote_url, branch, first_seen, last_seen)
    VALUES (@session_id, @repo_path, @remote_url, @branch, @first_seen, @last_seen)
  `);
  const run = db.transaction((rows) => {
    for (const row of rows) { stmt.run(row); }
  });
  run(rows);
}

function bulkInsertGitCommits(rows) {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT OR IGNORE INTO git_commits (session_id, repo_path, commit_hash, commit_msg, branch, remote_url, timestamp)
    VALUES (@session_id, @repo_path, @commit_hash, @commit_msg, @branch, @remote_url, @timestamp)
  `);
  const run = db.transaction((rows) => {
    for (const row of rows) { stmt.run(row); }
  });
  run(rows);
}

function bulkInsertGitOperations(rows) {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT OR IGNORE INTO git_operations (session_id, short_id, repo_path, remote_url, branch, operation, command, cwd, commit_hash, commit_msg, timestamp)
    VALUES (@session_id, @short_id, @repo_path, @remote_url, @branch, @operation, @command, @cwd, @commit_hash, @commit_msg, @timestamp)
  `);
  const run = db.transaction((rows) => {
    for (const row of rows) { stmt.run(row); }
  });
  run(rows);
}

function bulkInsertHandoffs(rows) {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT OR IGNORE INTO handoffs (session_id, timestamp, trigger, cwd, project, objective, completed, decisions, blockers, next_steps, raw_yaml)
    VALUES (@session_id, @timestamp, @trigger, @cwd, @project, @objective, @completed, @decisions, @blockers, @next_steps, @raw_yaml)
  `);
  const run = db.transaction((rows) => {
    for (const row of rows) { stmt.run(row); }
  });
  run(rows);
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  getDb, isAvailable, close, initSchema,

  // Sessions
  getRecentSessions, getSessionById, searchSessions, getSessionCount, upsertSession, bulkInsertSessions,

  // Tags
  addTags, removeTags, getTags, getTagHistory, searchByTag, getTagFrequency, bulkInsertTags,

  // Checkpoints
  createCheckpoint, getCheckpoints, getCheckpointByLabel, getRecentCheckpoints,
  insertTitleEvent, getTitleHistory, searchTitleHistory,

  // Phases
  recordPhaseTransition, getCurrentPhase, getPhaseHistory, getPhaseAnalytics,

  // Phrases
  capturePhrase, searchPhrases, getPhrasesWithTag,

  // Git
  upsertGitTracking, insertGitOperation, insertGitCommit,
  getSessionsForRepo, getReposForSession, getRecentCommits,
  bulkInsertGitTracking, bulkInsertGitCommits, bulkInsertGitOperations,

  // Handoffs
  insertHandoff, getHandoffsForSession, bulkInsertHandoffs,

  // Soul
  upsertSoulSession,

  // Transcript full-text index
  searchTranscripts, indexTranscript, getTranscriptIndexStates, getTranscriptIndexStats,
  pruneTranscriptIndex, buildFtsQuery, loadSynonymGroups,

  // Maintenance
  rebuildFTS,

  // Constants
  DB_PATH, TRANSCRIPTS_DB_PATH, SCHEMA_VERSION, ensureTranscripts,
};
