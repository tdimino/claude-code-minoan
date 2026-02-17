# Session Report

Generate a Markdown dashboard of recent Claude Code sessions with git activity, commits, and repo tracking.

**Usage:**
- `/session-report` - Show last 24 hours
- `/session-report 48h` - Show last 48 hours
- `/session-report 7d` - Show last 7 days
- `/session-report ~/Desktop/Programming/knossot` - Filter by repo path

## Arguments

$ARGUMENTS

## Instructions

```bash
node -e "
const os = require('os');
const path = require('path');
const fs = require('fs');
const utils = require(os.homedir() + '/.claude/lib/tracker-utils.js');

// Parse arguments
const args = '$ARGUMENTS'.trim();
let hours = 24;
let filterRepo = null;

if (args) {
  // Parse time window: 48h, 7d, etc.
  const timeMatch = args.match(/^(\d+)(h|d)$/);
  if (timeMatch) {
    hours = parseInt(timeMatch[1]) * (timeMatch[2] === 'd' ? 24 : 1);
  } else if (args.startsWith('/') || args.startsWith('~') || args.startsWith('.')) {
    // Repo path filter
    filterRepo = args.replace(/^~/, os.homedir());
    filterRepo = path.resolve(filterRepo);
  }
}

const cutoffDate = new Date(Date.now() - hours * 3600000);

// Load data sources
const tracking = utils.loadGitTracking();
const summaryCache = utils.loadSummaryCache();
const allFiles = utils.getAllSessionFiles();
const statusData = utils.buildSessionStatus(allFiles, { maxSessions: 30 });

// If filtering by repo, get relevant session IDs
let repoSessionFilter = null;
if (filterRepo) {
  const repoSessions = utils.getSessionsForRepo(filterRepo);
  if (repoSessions.length > 0) {
    repoSessionFilter = new Set(repoSessions);
  }
}

// Build session report data
const sessions = [];
for (const s of statusData.sessions) {
  // Time filter
  if (s.timestamp && new Date(s.timestamp) < cutoffDate) continue;

  // Repo filter
  if (repoSessionFilter && !repoSessionFilter.has(s.fullId) && !repoSessionFilter.has(s.id)) continue;

  const repos = utils.getReposForSession(s.fullId || s.id);
  const summary = summaryCache[s.fullId] || summaryCache[s.id] || {};

  sessions.push({
    ...s,
    repos,
    summaryData: summary,
  });
}

// Header
const now = new Date().toISOString().replace(/\.\d+Z$/, '');
const windowStr = hours >= 24 ? (hours / 24) + 'd' : hours + 'h';
console.log('# Session Report');
console.log('Generated: ' + now + ' | Window: ' + windowStr);
if (filterRepo) {
  console.log('Filter: ' + filterRepo.replace(os.homedir(), '~'));
}
console.log('');

// Count running vs inactive
const running = sessions.filter(s => s.isRunning).length;
const inactive = sessions.length - running;
const vsCode = sessions.filter(s => s.isInVSCode).length;

if (sessions.length === 0) {
  console.log('_No sessions found in the last ' + windowStr + '._');
  console.log('');
} else {
  console.log('## Sessions (' + running + ' running, ' + inactive + ' inactive' + (vsCode ? ', ' + vsCode + ' in VS Code' : '') + ')');
  console.log('');

  sessions.forEach((s, i) => {
    // Determine project name
    const projectName = s.projectName || path.basename(s.projectPath || s.cwd || '?');

    // Status badges
    const badges = [];
    if (s.isRunning) badges.push('RUNNING');
    if (s.isInVSCode) badges.push('VS Code');
    if (!s.isRunning && !s.isInVSCode) badges.push('INACTIVE');
    const badgeStr = badges.join(', ');

    console.log('### [' + (i + 1) + '] ' + projectName + ' — ' + badgeStr);

    // Session info
    const slug = s.sessionSlug || s.slug || '';
    const shortId = (s.fullId || s.id || '').substring(0, 8);
    if (slug) {
      console.log('- **Session**: ' + slug + ' (\`' + shortId + '\`)');
    } else {
      console.log('- **Session**: \`' + shortId + '\`');
    }

    // Time info
    const age = s.timestamp ? utils.formatAge(s.timestamp) : '?';
    const model = s.summaryData.model || s.model || '';
    const turns = s.summaryData.num_turns || '';
    const cost = s.summaryData.total_cost_usd ? '\$' + s.summaryData.total_cost_usd.toFixed(2) : '';
    const infoParts = ['Started: ' + age];
    if (model) infoParts.push('Model: ' + model);
    if (turns) infoParts.push('Turns: ' + turns);
    if (cost) infoParts.push('Cost: ' + cost);
    console.log('- ' + infoParts.join(' | '));

    // Summary
    const title = s.summaryData.title || s.sessionSummary || '';
    if (title) {
      console.log('- **Summary**: ' + title);
    }

    // Repos touched (from git tracking)
    const repoEntries = Object.entries(s.repos || {});
    if (repoEntries.length > 0) {
      const repoStrs = repoEntries.map(([rpath, rdata]) => {
        const shortPath = rpath.replace(os.homedir(), '~');
        const repoName = path.basename(rpath);
        const branch = (rdata.branches || [])[0] || '';
        const commitCount = (rdata.commits || []).length;
        const ops = rdata.operations || [];
        const isReadOnly = !ops.some(op => ['commit', 'push', 'add', 'merge', 'rebase'].includes(op));

        let desc = repoName;
        if (branch) desc += ' (' + branch + ')';
        if (commitCount > 0) desc += ', ' + commitCount + ' commit' + (commitCount > 1 ? 's' : '');
        else if (isReadOnly) desc += ', read-only';
        return desc;
      });
      console.log('- **Repos**: ' + repoStrs.join(' | '));

      // Show commits
      const allCommits = [];
      for (const [rpath, rdata] of repoEntries) {
        for (const commit of (rdata.commits || [])) {
          allCommits.push({
            ...commit,
            repoName: path.basename(rpath),
          });
        }
      }
      allCommits.sort((a, b) => (b.ts || '').localeCompare(a.ts || ''));

      if (allCommits.length > 0) {
        console.log('- **Commits**:');
        allCommits.slice(0, 5).forEach(c => {
          const commitAge = c.ts ? utils.formatAge(c.ts) : '';
          const msg = c.msg ? c.msg.substring(0, 80) : '';
          console.log('  - \`' + (c.hash || '?').substring(0, 7) + '\` ' + msg + (commitAge ? ' (' + c.repoName + ', ' + commitAge + ')' : ''));
        });
      }
    }

    // Git remote
    const gitRemote = s.gitRemote || '';
    if (gitRemote) {
      console.log('- **Remote**: ' + gitRemote);
    }

    // Resume command
    const fullId = s.fullId || s.id || '';
    if (fullId) {
      console.log('- **Resume**: \`claude --resume ' + fullId + '\`');
    }

    console.log('');
  });
}

// Git Activity Timeline
const events = utils.getRecentGitEvents({ hours, maxEvents: 30 });
if (events.length > 0) {
  console.log('## Git Activity Timeline');
  console.log('');
  console.log('| Time | Repo | Session | Op | Details |');
  console.log('|------|------|---------|----|---------|');

  events.forEach(e => {
    if (e.type === 'result') return; // Skip enrichment lines in timeline
    const time = (e.ts || '').substring(11, 16) || '?';
    const repoName = path.basename(e.repo || '?');
    const shortSid = (e.short || (e.sid || '').substring(0, 8));
    const ops = e.ops || '';
    let details = '';

    // Look for enrichment data
    if (ops.includes('commit') && e.msg) {
      details = e.msg.substring(0, 60);
    } else if (e.cmd) {
      details = e.cmd.substring(0, 60);
    }

    console.log('| ' + time + ' | ' + repoName + ' | \`' + shortSid + '\` | ' + ops + ' | ' + details + ' |');
  });
  console.log('');
}

// Repo Summary
const repoIndex = tracking.repo_index || {};
const repoEntries = Object.entries(repoIndex);
if (repoEntries.length > 0) {
  console.log('## Repo Summary');
  console.log('');
  console.log('| Repo | Branches | Sessions | Commits | Last Activity |');
  console.log('|------|----------|----------|---------|---------------|');

  // Collect repo stats
  const repoStats = [];
  for (const [rpath, sids] of repoEntries) {
    const repoName = path.basename(rpath);
    const branches = new Set();
    let totalCommits = 0;
    let lastActivity = '';

    for (const sid of sids) {
      const session = (tracking.sessions || {})[sid];
      if (!session) continue;
      const repoData = (session.repos || {})[rpath];
      if (!repoData) continue;

      (repoData.branches || []).forEach(b => branches.add(b));
      totalCommits += (repoData.commits || []).length;
      if (repoData.last_seen && repoData.last_seen > lastActivity) {
        lastActivity = repoData.last_seen;
      }
    }

    repoStats.push({ repoName, rpath, branches: [...branches], sessionCount: sids.length, totalCommits, lastActivity });
  }

  // Sort by last activity
  repoStats.sort((a, b) => b.lastActivity.localeCompare(a.lastActivity));

  repoStats.forEach(r => {
    const age = r.lastActivity ? utils.formatAge(r.lastActivity) : '?';
    console.log('| ' + r.repoName + ' | ' + r.branches.join(', ') + ' | ' + r.sessionCount + ' | ' + r.totalCommits + ' | ' + age + ' |');
  });
  console.log('');
}

console.log('---');
console.log('_Run \`/session-report\` to refresh. Resume with \`claude --resume <id>\`._');
"
```

Generates a comprehensive Markdown dashboard showing:
- **Session list** with status (running/inactive/VS Code), model, cost, turns
- **Repos touched** per session with branch and commit counts
- **Recent commits** with hashes and messages
- **Git activity timeline** (chronological event log)
- **Repo summary** table (all repos, sessions, commit counts)

Supports time window (`24h`, `48h`, `7d`) and repo path filtering.

Requires: `~/.claude/hooks/git-track.sh` (PreToolUse) to populate `git-tracking.jsonl`.
