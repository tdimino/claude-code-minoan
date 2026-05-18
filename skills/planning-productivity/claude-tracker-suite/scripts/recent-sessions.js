#!/usr/bin/env node

const os = require('os');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

const HOME = os.homedir();
const trackerDb = require(path.join(HOME, '.claude/lib/tracker-db'));
const utils = require(path.join(HOME, '.claude/lib/tracker-utils'));

const GHOSTTY_SCRIPT = path.join(HOME, '.claude/scripts/ghostty-resume.sh');

function resolveProjectPath(s) {
  if (s.project_path && !s.project_path.startsWith('-')) return s.project_path;
  const dirName = s.project_dir || s.project_path;
  if (!dirName) return s.project_path;
  return utils.decodeProjectPath(dirName);
}

function resolveProjectName(s, resolvedPath) {
  if (s.project_name && !s.project_name.startsWith('-')) return s.project_name;
  if (resolvedPath) return path.basename(resolvedPath);
  return s.project_name;
}

let limit = 10;
let jsonMode = false;
let projectFilter = null;
let modelFilter = null;
let sinceFilter = null;

const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--limit':
      limit = parseInt(args[++i], 10) || 10;
      break;
    case '--json':
      jsonMode = true;
      break;
    case '--project':
      projectFilter = args[++i];
      break;
    case '--model':
      modelFilter = args[++i];
      break;
    case '--since':
      sinceFilter = parseSince(args[++i]);
      break;
    case '--help':
    case '-h':
      console.log('Usage: recent-sessions.js [--limit N] [--json] [--project <name>] [--model <name>] [--since <duration>]');
      console.log('');
      console.log('  --limit N          Max sessions to show (default: 10)');
      console.log('  --json             Machine-readable JSON output');
      console.log('  --project <name>   Filter by project name (substring)');
      console.log('  --model <name>     Filter by model (e.g. opus, sonnet)');
      console.log('  --since <dur>      Recent only: 7d, 24h, 30m, 2w');
      process.exit(0);
  }
}

function parseSince(s) {
  if (!s) return null;
  const m = s.match(/^(\d+)([mhdw])$/);
  if (!m) { console.error('Invalid --since format. Use: 7d, 24h, 30m, 2w'); return null; }
  const n = parseInt(m[1], 10);
  const unit = { m: 60000, h: 3600000, d: 86400000, w: 604800000 }[m[2]];
  const d = new Date(Date.now() - n * unit);
  const offset = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - offset).toISOString().slice(0, 19);
}

function formatTags(tags) {
  const parts = [];
  if (tags.user && tags.user.length)
    parts.push(tags.user.map(t => '\x1b[36m[' + t + ']\x1b[0m').join(' '));
  if (tags.auto && tags.auto.length)
    parts.push(tags.auto.map(t => '\x1b[33mauto:[' + t + ']\x1b[0m').join(' '));
  if (tags.display && tags.display.length)
    parts.push(tags.display.map(t => '\x1b[32mdisplay:[' + t + ']\x1b[0m').join(' '));
  return parts.join('  ');
}

if (!trackerDb.isAvailable()) {
  console.error('tracker.db not found — run: node ~/.claude/scripts/migrate-to-sqlite.js');
  process.exit(1);
}

trackerDb.initSchema();

const sessions = trackerDb.getRecentSessions({
  limit,
  project: projectFilter,
  model: modelFilter,
  since: sinceFilter
});

if (sessions.length === 0) {
  console.log('No sessions found.');
  process.exit(0);
}

const hasGhosttyScript = fs.existsSync(GHOSTTY_SCRIPT);
let firstResumeCmd = null;

if (jsonMode) {
  const output = sessions.map(s => {
    const tags = trackerDb.getTags(s.session_id);
    const title = s.custom_title || s.auto_title || s.slug || null;
    const projectPath = resolveProjectPath(s);
    const projectName = resolveProjectName(s, projectPath);
    const resumeCmd = 'cd ' + projectPath + ' && claude --resume ' + s.session_id;
    return {
      sessionId: s.session_id,
      shortId: s.short_id,
      title,
      summary: s.summary || null,
      tags,
      projectName,
      projectPath,
      age: utils.formatAge(s.modified_at),
      model: s.model_short || s.model || null,
      cost: s.total_cost_usd || 0,
      numTurns: s.num_turns || 0,
      gitBranch: s.git_branch || null,
      isRunning: !!s.is_running,
      modifiedAt: s.modified_at,
      createdAt: s.created_at,
      resumeCommand: resumeCmd,
      ghosttyResumeCommand: hasGhosttyScript ? GHOSTTY_SCRIPT + ' ' + s.session_id : null
    };
  });
  console.log(JSON.stringify(output, null, 2));
  process.exit(0);
}

const filterParts = [];
if (projectFilter) filterParts.push('project: ' + projectFilter);
if (modelFilter) filterParts.push('model: ' + modelFilter);
if (sinceFilter) filterParts.push('since: ' + args[args.indexOf('--since') + 1]);
const filterStr = filterParts.length ? ', ' + filterParts.join(', ') : '';
console.log('\x1b[1mRecent sessions\x1b[0m (last ' + sessions.length + filterStr + '):\n');

sessions.forEach((s, i) => {
  const tags = trackerDb.getTags(s.session_id);
  const title = s.custom_title || s.auto_title || s.slug || null;
  const projectPath = resolveProjectPath(s);
  const projectName = resolveProjectName(s, projectPath);
  const age = utils.formatAge(s.modified_at);
  const model = s.model_short || s.model || '';
  const cost = s.total_cost_usd ? '$' + s.total_cost_usd.toFixed(2) : '';
  const turns = s.num_turns ? s.num_turns + ' turns' : '';
  const resumeCmd = 'cd ' + projectPath + ' && claude --resume ' + s.session_id;

  if (!firstResumeCmd) firstResumeCmd = resumeCmd;

  const headerParts = [
    '\x1b[33m[' + (i + 1) + ']\x1b[0m',
    '\x1b[1m' + projectName + '\x1b[0m',
    '\x1b[90m' + age + '\x1b[0m'
  ];
  if (model) headerParts.push('\x1b[35m' + model + '\x1b[0m');
  if (cost) headerParts.push('\x1b[32m' + cost + '\x1b[0m');
  if (turns) headerParts.push(turns);
  if (s.is_running) headerParts.push('\x1b[42m\x1b[30m RUNNING \x1b[0m');

  console.log(headerParts.join('  '));

  if (title) {
    console.log('    \x1b[1;35m' + title + '\x1b[0m');
  }

  if (s.summary) {
    const truncated = s.summary.length > 200 ? s.summary.substring(0, 200) + '...' : s.summary;
    console.log('    ' + truncated);
  }

  const tagStr = formatTags(tags);
  if (tagStr) {
    console.log('    ' + tagStr);
  }

  const metaParts = [];
  if (s.git_branch) metaParts.push('\x1b[35m' + s.git_branch + '\x1b[0m');
  metaParts.push(s.session_id.substring(0, 8));
  metaParts.push('\x1b[36m' + resumeCmd + '\x1b[0m');
  console.log('    ' + metaParts.join('  |  '));

  console.log('');
});

if (firstResumeCmd) {
  try {
    execSync('pbcopy', { input: firstResumeCmd });
    console.log('\x1b[32m✓ Copied to clipboard:\x1b[0m ' + firstResumeCmd + '\n');
  } catch (e) {}
}
