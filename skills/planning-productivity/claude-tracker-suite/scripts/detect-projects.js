#!/usr/bin/env node

/**
 * Detect and analyze all projects across Claude Code sessions.
 *
 * Scans sessions-index.json files to find every unique project,
 * checks for CLAUDE.md files, compares against global config,
 * and suggests additions or scaffolding.
 *
 * Usage:
 *   detect-projects.js                   Show all detected projects
 *   detect-projects.js --suggest         Suggest global CLAUDE.md additions
 *   detect-projects.js --scaffold        Create CLAUDE.md stubs for projects missing them
 *   detect-projects.js --json            JSON output
 *   detect-projects.js --since 30d       Only projects active in last 30 days
 */

const os = require('os');
const fs = require('fs');
const path = require('path');

const UTILS_PATH = path.join(os.homedir(), '.claude', 'lib', 'tracker-utils.js');
let utils;
try {
  utils = require(UTILS_PATH);
} catch (e) {
  console.error('Error: Could not load tracker utilities from ' + UTILS_PATH);
  process.exit(1);
}

const GLOBAL_CLAUDE_MD = path.join(os.homedir(), '.claude', 'CLAUDE.md');
const ACTIVE_PROJECTS_MD = path.join(os.homedir(), '.claude', 'agent_docs', 'active-projects.md');
const HOME = os.homedir();

// --- Args ---

function parseArgs(argv) {
  const args = { suggest: false, scaffold: false, json: false, since: null, help: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') args.help = true;
    else if (a === '--suggest') args.suggest = true;
    else if (a === '--scaffold') args.scaffold = true;
    else if (a === '--json') args.json = true;
    else if (a === '--since') args.since = parseDuration(argv[++i]);
  }
  return args;
}

function parseDuration(str) {
  if (!str) return null;
  const m = str.match(/^(\d+)(m|h|d|w)$/);
  if (!m) return null;
  const ms = { m: 60000, h: 3600000, d: 86400000, w: 604800000 };
  return Date.now() - parseInt(m[1]) * ms[m[2]];
}

// --- Project detection ---

function detectProjects(sinceMs) {
  const sessions = utils.loadSessionsIndex();
  const projectMap = new Map();

  for (const s of sessions) {
    const pp = s.projectPath;
    if (!pp) continue;

    // Filter by time if requested
    if (sinceMs) {
      const modified = s.modified || s.created;
      if (modified && new Date(modified).getTime() < sinceMs) continue;
    }

    if (!projectMap.has(pp)) {
      projectMap.set(pp, {
        projectPath: pp,
        projectName: path.basename(pp),
        sessionCount: 0,
        lastActive: null,
        branches: new Set(),
        hasCLAUDEmd: false,
        isGitRepo: false,
        summaries: [],
      });
    }

    const p = projectMap.get(pp);
    p.sessionCount++;

    const mod = s.modified || s.created;
    if (mod && (!p.lastActive || new Date(mod) > new Date(p.lastActive))) {
      p.lastActive = mod;
    }

    if (s.gitBranch) p.branches.add(s.gitBranch);
    if (s.summary) p.summaries.push(s.summary);
  }

  // Enrich with filesystem checks
  for (const [pp, p] of projectMap) {
    try {
      p.hasCLAUDEmd = fs.existsSync(path.join(pp, 'CLAUDE.md'));
    } catch (e) {}
    try {
      p.isGitRepo = fs.existsSync(path.join(pp, '.git'));
    } catch (e) {}
    // Convert Set to Array for serialization
    p.branches = Array.from(p.branches);
  }

  return Array.from(projectMap.values())
    .sort((a, b) => {
      // Sort by last active descending
      const aT = a.lastActive ? new Date(a.lastActive).getTime() : 0;
      const bT = b.lastActive ? new Date(b.lastActive).getTime() : 0;
      return bT - aT;
    });
}

// --- Global CLAUDE.md analysis ---

function loadGlobalCLAUDEmd() {
  try {
    return fs.readFileSync(GLOBAL_CLAUDE_MD, 'utf-8');
  } catch (e) {
    return '';
  }
}

function loadActiveProjectsMd() {
  try {
    return fs.readFileSync(ACTIVE_PROJECTS_MD, 'utf-8');
  } catch (e) {
    return '';
  }
}

function isProjectReferenced(projectPath, globalContent, activeContent) {
  const name = path.basename(projectPath);
  const displayPath = projectPath.replace(HOME, '~');
  return globalContent.includes(name) ||
         globalContent.includes(displayPath) ||
         activeContent.includes(name) ||
         activeContent.includes(displayPath);
}

// --- CLAUDE.md scaffold ---

function scaffoldCLAUDEmd(project) {
  const name = project.projectName;
  const isGit = project.isGitRepo;
  const recentWork = project.summaries.slice(0, 3).map(s => `- ${s}`).join('\n');

  let content = `# ${name}\n\n`;

  // Detect project type from path
  const pp = project.projectPath.toLowerCase();
  if (pp.includes('aldea')) {
    content += `Aldea project.\n\n`;
  } else if (pp.includes('research') || pp.includes('paper')) {
    content += `Research project.\n\n`;
  }

  content += `## Overview\n\n`;
  content += `<!-- TODO: Describe this project's purpose and Claude's role -->\n\n`;

  if (recentWork) {
    content += `## Recent Work\n\n${recentWork}\n\n`;
  }

  if (isGit && project.branches.length > 0) {
    content += `## Branches\n\n`;
    for (const b of project.branches.slice(0, 5)) {
      content += `- \`${b}\`\n`;
    }
    content += `\n`;
  }

  content += `## Conventions\n\n`;
  content += `<!-- TODO: Add project-specific conventions, tools, and constraints -->\n`;

  return content;
}

// --- Suggest additions to global CLAUDE.md ---

function suggestGlobalAdditions(projects, globalContent, activeContent) {
  const unreferenced = projects.filter(p =>
    !isProjectReferenced(p.projectPath, globalContent, activeContent) &&
    p.sessionCount >= 2
  );

  if (unreferenced.length === 0) return null;

  // Group by domain
  const groups = {
    'Aldea / Work': [],
    'Research': [],
    'Gaming': [],
    'Personal / Tools': [],
  };

  for (const p of unreferenced) {
    const pp = p.projectPath.toLowerCase();
    if (pp.includes('aldea') || pp.includes('kothar') || pp.includes('soul')) {
      groups['Aldea / Work'].push(p);
    } else if (pp.includes('research') || pp.includes('paper') || pp.includes('thera') || pp.includes('minoan')) {
      groups['Research'].push(p);
    } else if (pp.includes('bg3') || pp.includes('game') || pp.includes('crypt')) {
      groups['Gaming'].push(p);
    } else {
      groups['Personal / Tools'].push(p);
    }
  }

  let suggestion = '## Suggested Additions to Global CLAUDE.md\n\n';
  suggestion += 'The following projects have 2+ sessions but are not referenced in your global config:\n\n';

  for (const [group, items] of Object.entries(groups)) {
    if (items.length === 0) continue;
    suggestion += `### ${group}\n\n`;
    for (const p of items) {
      const displayPath = p.projectPath.replace(HOME, '~');
      const hasMd = p.hasCLAUDEmd ? ' (has CLAUDE.md)' : ' **needs CLAUDE.md**';
      const age = p.lastActive ? formatAge(p.lastActive) : 'unknown';
      suggestion += `- \`${displayPath}\` — ${p.sessionCount} sessions, last active ${age}${hasMd}\n`;
    }
    suggestion += '\n';
  }

  // Generate the active-projects.md snippet
  suggestion += '### Suggested active-projects.md entries\n\n';
  suggestion += '```markdown\n';
  for (const p of unreferenced.slice(0, 10)) {
    const displayPath = p.projectPath.replace(HOME, '~');
    const hasMd = p.hasCLAUDEmd ? ' (CLAUDE.md)' : '';
    suggestion += `### \`${displayPath}\`${hasMd}\n\n`;
    suggestion += '| Last Active | Session | Branch |\n';
    suggestion += '|---|---|---|\n';
    const branch = p.branches[0] || '—';
    const age = p.lastActive ? p.lastActive.substring(0, 16).replace('T', ' ') : '?';
    suggestion += `| ${age} | — | ${branch} |\n\n`;
  }
  suggestion += '```\n';

  return { suggestion, unreferenced };
}

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

// --- Display ---

function display(projects, globalContent, activeContent) {
  const totalSessions = projects.reduce((sum, p) => sum + p.sessionCount, 0);
  const withCLAUDE = projects.filter(p => p.hasCLAUDEmd).length;
  const referenced = projects.filter(p => isProjectReferenced(p.projectPath, globalContent, activeContent)).length;

  console.log('\n\x1b[1m\x1b[36m══════════════════════════════════════════════════════════\x1b[0m');
  console.log('\x1b[1m\x1b[36m              CLAUDE CODE PROJECT DETECTION                \x1b[0m');
  console.log('\x1b[1m\x1b[36m══════════════════════════════════════════════════════════\x1b[0m');
  console.log(`\x1b[90m  ${projects.length} projects | ${totalSessions} sessions | ${withCLAUDE} with CLAUDE.md | ${referenced} in global config\x1b[0m\n`);

  for (let i = 0; i < projects.length; i++) {
    const p = projects[i];
    const displayPath = p.projectPath.replace(HOME, '~');
    const mdBadge = p.hasCLAUDEmd ? ' \x1b[42m\x1b[30m CLAUDE.md \x1b[0m' : ' \x1b[43m\x1b[30m NO CLAUDE.md \x1b[0m';
    const refBadge = isProjectReferenced(p.projectPath, globalContent, activeContent)
      ? ' \x1b[44m\x1b[37m IN CONFIG \x1b[0m'
      : ' \x1b[100m NOT IN CONFIG \x1b[0m';
    const gitBadge = p.isGitRepo ? ' \x1b[90mgit\x1b[0m' : '';
    const age = p.lastActive ? formatAge(p.lastActive) : 'unknown';

    console.log(
      `\x1b[33m[${i + 1}]\x1b[0m \x1b[1m${p.projectName}\x1b[0m${mdBadge}${refBadge}${gitBadge}`
    );
    console.log(`    \x1b[90mPath:\x1b[0m ${displayPath}`);
    console.log(`    \x1b[90mSessions:\x1b[0m ${p.sessionCount}  \x1b[90mLast active:\x1b[0m ${age}`);

    if (p.branches.length > 0) {
      console.log(`    \x1b[90mBranches:\x1b[0m \x1b[35m${p.branches.slice(0, 3).join(', ')}\x1b[0m`);
    }

    if (p.summaries.length > 0) {
      console.log(`    \x1b[90mRecent:\x1b[0m ${p.summaries[0]}`);
    }

    console.log('');
  }
}

// --- Main ---

function main() {
  const args = parseArgs(process.argv);

  if (args.help) {
    console.log(`
Usage: detect-projects.js [options]

Detect all projects across Claude Code sessions and analyze coverage.

Options:
  --suggest         Show suggestions for global CLAUDE.md additions
  --scaffold        Create CLAUDE.md stubs for projects missing them
  --json            JSON output
  --since <dur>     Only projects active within duration (e.g., 30d, 7d)
  -h, --help        Show this help

Examples:
  detect-projects.js                      List all detected projects
  detect-projects.js --suggest            Suggest global config additions
  detect-projects.js --scaffold           Scaffold missing CLAUDE.md files
  detect-projects.js --since 30d          Only recent projects
  detect-projects.js --json               Machine-readable output
`);
    return;
  }

  const projects = detectProjects(args.since);
  const globalContent = loadGlobalCLAUDEmd();
  const activeContent = loadActiveProjectsMd();

  if (args.json) {
    const output = projects.map(p => ({
      ...p,
      displayPath: p.projectPath.replace(HOME, '~'),
      isReferenced: isProjectReferenced(p.projectPath, globalContent, activeContent),
    }));
    console.log(JSON.stringify(output, null, 2));
    return;
  }

  display(projects, globalContent, activeContent);

  if (args.suggest) {
    const result = suggestGlobalAdditions(projects, globalContent, activeContent);
    if (result) {
      console.log('\x1b[1m\x1b[36m══════════════════════════════════════════════════════════\x1b[0m');
      console.log(result.suggestion);
    } else {
      console.log('\x1b[32mAll projects with 2+ sessions are already referenced in global config.\x1b[0m\n');
    }
  }

  if (args.scaffold) {
    const needsCLAUDE = projects.filter(p => !p.hasCLAUDEmd && p.sessionCount >= 2);
    if (needsCLAUDE.length === 0) {
      console.log('\x1b[32mAll active projects already have CLAUDE.md files.\x1b[0m\n');
      return;
    }

    console.log(`\n\x1b[1mScaffolding CLAUDE.md for ${needsCLAUDE.length} project(s):\x1b[0m\n`);
    for (const p of needsCLAUDE) {
      const mdPath = path.join(p.projectPath, 'CLAUDE.md');
      try {
        // Only create if directory exists and is writable
        if (!fs.existsSync(p.projectPath)) {
          console.log(`  \x1b[33m⊘\x1b[0m Skipped \x1b[1m${p.projectName}\x1b[0m — directory not found`);
          continue;
        }
        const content = scaffoldCLAUDEmd(p);
        fs.writeFileSync(mdPath, content);
        console.log(`  \x1b[32m✓\x1b[0m Created \x1b[1m${mdPath.replace(HOME, '~')}\x1b[0m`);
      } catch (e) {
        console.log(`  \x1b[31m✗\x1b[0m Failed \x1b[1m${p.projectName}\x1b[0m: ${e.message}`);
      }
    }
    console.log('');
  }
}

main();
