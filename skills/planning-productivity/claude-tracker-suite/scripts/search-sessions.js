#!/usr/bin/env node
/**
 * search-sessions.js — Search all Claude Code sessions by keyword
 *
 * Usage: node search-sessions.js <search-term> [--limit N] [--name]
 *
 * Searches user and assistant messages across all session JSONL files.
 * --name: search only session names/slugs/summaries (fast, no body scan).
 * Filters out system context injections (CLAUDE.md, MEMORY.md, active-projects).
 * Outputs: project name, session age, summary, slug, git remote, session ID,
 *          and highlighted matching excerpts.
 */

const os = require('os');
const utils = require(os.homedir() + '/.claude/lib/tracker-utils.js');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Parse arguments
const args = process.argv.slice(2);
let searchTerm = '';
let maxResults = 15;
let maxLinesPerFile = 8000;
let nameOnly = false;
let idPrefix = '';

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--limit' && args[i + 1]) {
    maxResults = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i] === '--lines' && args[i + 1]) {
    maxLinesPerFile = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i] === '--name') {
    nameOnly = true;
  } else if (args[i] === '--id' && args[i + 1]) {
    idPrefix = args[i + 1].toLowerCase();
    i++;
  } else if (!searchTerm) {
    searchTerm = args[i].toLowerCase();
  }
}

if (!searchTerm && !idPrefix) {
  console.log('\n\x1b[33mUsage:\x1b[0m node search-sessions.js <search-term> [--limit N] [--name]');
  console.log('\x1b[90mExample: node search-sessions.js "kothar mac mini"');
  console.log('Example: node search-sessions.js "websocket" --limit 5');
  console.log('Example: node search-sessions.js "thera" --name    (name/slug only, fast)');
  console.log('Example: node search-sessions.js --id d7b8f4dd     (lookup by session ID prefix)\x1b[0m\n');
  process.exit(0);
}

// Patterns that indicate system context injection (not real conversation)
const NOISE_PATTERNS = [
  'CLAUDE.md',
  'MEMORY.md',
  'active-projects.md',
  '<observed_from_primary_session>',
  'system-reminder',
  'agent_docs/',
  'user-invocable skills',
  'userModels/',
];

function extractText(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .filter(block => block && block.type === 'text' && block.text)
      .map(block => block.text)
      .join(' ');
  }
  return '';
}

function isNoise(content) {
  for (const pattern of NOISE_PATTERNS) {
    if (content.includes(pattern)) return true;
  }
  return false;
}

async function searchSession(filePath, projectPath) {
  return new Promise((resolve) => {
    const sessionId = path.basename(filePath, '.jsonl');
    const matches = [];
    let timestamp = '';
    let sessionSlug = '';
    let sessionSummary = '';
    let customTitle = '';
    let lineCount = 0;
    let resolved = false;
    let stream, rl;

    const cleanup = () => {
      if (resolved) return;
      resolved = true;
      if (rl) rl.close();
      if (stream) stream.destroy();
    };

    const done = () => {
      cleanup();
      // Match if body matches OR custom title matches the search term
      const titleMatch = customTitle && customTitle.toLowerCase().includes(searchTerm);
      if (matches.length > 0 || titleMatch) {
        resolve({
          sessionId,
          projectPath,
          timestamp,
          sessionSlug,
          sessionSummary,
          customTitle,
          matches: matches.slice(0, 5),
        });
      } else {
        resolve(null);
      }
    };

    try {
      stream = fs.createReadStream(filePath);
      rl = readline.createInterface({ input: stream, crlfDelay: Infinity });

      rl.on('line', (line) => {
        lineCount++;
        if (lineCount > maxLinesPerFile) {
          done();
          return;
        }

        try {
          const data = JSON.parse(line);
          if (timestamp === '' && data.timestamp) timestamp = data.timestamp;
          if (sessionSlug === '' && data.slug) sessionSlug = data.slug;
          if (data.type === 'summary' && data.summary) sessionSummary = data.summary;

          // Track user-assigned custom title (/rename) — last one wins
          if (data.type === 'custom-title' && data.customTitle) {
            customTitle = data.customTitle;
          }

          // Search user messages
          if (data.type === 'user' && data.message && data.message.content) {
            const text = extractText(data.message.content);
            if (text && text.toLowerCase().includes(searchTerm) && !isNoise(text)) {
              matches.push(text.substring(0, 200).replace(/\n/g, ' '));
            }
          }

          // Search assistant messages
          if (data.type === 'assistant' && data.message && data.message.content) {
            const text = extractText(data.message.content);
            if (text && text.toLowerCase().includes(searchTerm) && !isNoise(text)) {
              matches.push('[Assistant] ' + text.substring(0, 200).replace(/\n/g, ' '));
            }
          }
        } catch (e) {
          // Invalid JSON line — skip
        }
      });

      rl.on('close', done);
      rl.on('error', done);
      stream.on('error', done);
    } catch (e) {
      resolve(null);
    }
  });
}

/**
 * Zoxide-style ordered-token substring match.
 * All space-delimited tokens must appear in the target in order, case-insensitive.
 */
function matchName(query, target) {
  if (!target) return false;
  const haystack = target.toLowerCase();
  const tokens = query.trim().split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return false;
  let pos = 0;
  for (const token of tokens) {
    const idx = haystack.indexOf(token, pos);
    if (idx === -1) return false;
    pos = idx + token.length;
  }
  return true;
}

/**
 * Name-only search: matches against customTitle, slug, summary, and tags.
 * Uses loadSessionsIndex() + lightweight slug read. No full JSONL body scan.
 */
function searchByName() {
  const sessions = utils.loadSessionsIndex();

  // Load registry once for tags (loadSessionsIndex only surfaces title+summary)
  const registryPath = path.join(os.homedir(), '.claude', 'session-registry.json');
  let registry = {};
  try {
    registry = JSON.parse(fs.readFileSync(registryPath, 'utf-8')).sessions || {};
  } catch (e) { /* no registry */ }

  const results = [];

  for (const session of sessions) {
    const slug = utils.readSessionSlug(session.fullPath);
    const regEntry = registry[session.sessionId] || {};
    // Merge all tag sources: display_tags, auto-tags, and user-tags (case-insensitive dedupe)
    const rawTags = [
      ...(regEntry.display_tags || []),
      ...(regEntry.tags || []),
      ...(regEntry.user_tags || []),
    ].map(t => (t || '').trim()).filter(Boolean);
    const seenTags = new Set();
    const tagsArr = rawTags.filter(t => {
      const k = t.toLowerCase();
      if (seenTags.has(k)) return false;
      seenTags.add(k);
      return true;
    });
    const tagsStr = tagsArr.join(' ');

    // Read user-assigned custom title from JSONL (/rename)
    const userTitle = utils.readCustomTitle(session.fullPath);

    const matchedFields = [];

    // Check user-assigned name first (from /rename)
    if (userTitle && matchName(searchTerm, userTitle)) {
      matchedFields.push({ field: 'name', value: userTitle });
    }
    // Also check auto-generated title from registry
    if (session.customTitle && matchName(searchTerm, session.customTitle)) {
      matchedFields.push({ field: 'title', value: session.customTitle });
    }
    if (slug && matchName(searchTerm, slug)) {
      matchedFields.push({ field: 'slug', value: slug });
    }
    if (session.summary && matchName(searchTerm, session.summary)) {
      matchedFields.push({ field: 'summary', value: session.summary });
    }
    if (tagsStr && matchName(searchTerm, tagsStr)) {
      matchedFields.push({ field: 'tags', value: tagsArr.join(', ') });
    }

    if (matchedFields.length > 0) {
      results.push({
        sessionId: session.sessionId,
        projectPath: session.projectPath,
        projectName: session.projectName,
        fileMtime: session.fileMtime,
        matchedFields,
        slug,
      });
    }
  }

  results.sort((a, b) => new Date(b.fileMtime) - new Date(a.fileMtime));
  return results;
}

/**
 * Print results from --name search.
 * Shows matched fields with per-token highlighting instead of body excerpts.
 */
function printNameResults(results, escapedTerm) {
  // Build alternation regex for multi-token highlighting
  const tokenPattern = escapedTerm.split(/\s+/).filter(Boolean).join('|');
  let count = 0;

  for (const result of results) {
    if (count >= maxResults) {
      console.log('\x1b[90m... (showing first ' + maxResults + ' results)\x1b[0m\n');
      return;
    }
    count++;

    const gitRemote = utils.getGitRemote(result.projectPath);

    console.log(
      '\x1b[33m[' + count + ']\x1b[0m \x1b[1m' + result.projectName +
      '\x1b[0m \x1b[90m(' + utils.formatAge(result.fileMtime) + ')\x1b[0m'
    );

    result.matchedFields.forEach(({ field, value }) => {
      const label = field.charAt(0).toUpperCase() + field.slice(1);
      const highlighted = value.replace(
        new RegExp('(' + tokenPattern + ')', 'gi'),
        '\x1b[43m\x1b[30m$1\x1b[0m'
      );
      console.log('    \x1b[32m›\x1b[0m \x1b[90m' + label + ':\x1b[0m ' + highlighted);
    });

    if (result.slug && !result.matchedFields.find(f => f.field === 'slug')) {
      console.log('    \x1b[90mSlug:\x1b[0m ' + result.slug);
    }
    if (gitRemote) {
      console.log('    \x1b[90mRepo:\x1b[0m \x1b[34m' + gitRemote + '\x1b[0m');
    }
    console.log('    \x1b[90mDir:\x1b[0m ' + result.projectPath);
    console.log('    \x1b[90mID:\x1b[0m ' + result.sessionId);
    console.log('    \x1b[90mResume:\x1b[0m \x1b[36mcd ' + result.projectPath + ' && claude --resume ' + result.sessionId + '\x1b[0m');
    console.log('');
  }
}

/** Read timestamp from first JSONL line (for title-only matches) */
async function getFirstLineTimestamp(filePath) {
  try {
    const fd = fs.openSync(filePath, 'r');
    const buf = Buffer.alloc(4096);
    const bytesRead = fs.readSync(fd, buf, 0, 4096, 0);
    fs.closeSync(fd);
    const firstLine = buf.toString('utf-8', 0, bytesRead).split('\n')[0];
    if (firstLine) {
      const obj = JSON.parse(firstLine);
      return obj.timestamp || '';
    }
  } catch (e) { /* skip */ }
  return '';
}

async function main() {
  // --id mode: lookup by session ID prefix
  if (idPrefix) {
    console.log('\n\x1b[1m\x1b[36mLooking up session:\x1b[0m "' + idPrefix + '"\n');
    const allFiles = utils.getAllSessionFiles();
    const matches = allFiles.filter(f => path.basename(f.filePath, '.jsonl').startsWith(idPrefix));

    if (matches.length === 0) {
      console.log('\x1b[33mNo session found matching ID prefix "' + idPrefix + '".\x1b[0m\n');
      return;
    }

    for (const file of matches.slice(0, 5)) {
      const sessionId = path.basename(file.filePath, '.jsonl');
      const projectPath = utils.decodeProjectPath(file.projectDir);
      const projectName = projectPath.split('/').pop();
      const slug = utils.readSessionSlug(file.filePath);
      const customTitle = utils.readCustomTitle(file.filePath);
      const age = utils.formatAge(new Date(file.mtime).toISOString());

      console.log('\x1b[1m' + projectName + '\x1b[0m \x1b[90m(' + age + ')\x1b[0m');
      if (customTitle) console.log('    \x1b[90mName:\x1b[0m \x1b[1m\x1b[35m' + customTitle + '\x1b[0m');
      if (slug) console.log('    \x1b[90mSlug:\x1b[0m ' + slug);
      console.log('    \x1b[90mDir:\x1b[0m ' + projectPath);
      console.log('    \x1b[90mID:\x1b[0m ' + sessionId);
      console.log('    \x1b[90mResume:\x1b[0m \x1b[36mcd ' + projectPath + ' && claude --resume ' + sessionId + '\x1b[0m');
      console.log('');
    }

    if (matches.length > 5) {
      console.log('\x1b[90m... and ' + (matches.length - 5) + ' more\x1b[0m\n');
    }
    return;
  }

  // --name mode: fast metadata-only search, no JSONL body scan
  if (nameOnly) {
    console.log('\n\x1b[1m\x1b[36mSearching names for:\x1b[0m "' + searchTerm + '" \x1b[90m(--name)\x1b[0m\n');
    const results = searchByName();
    if (results.length === 0) {
      console.log('\x1b[33mNo name matches found.\x1b[0m\n');
      return;
    }
    const escapedTerm = utils.escapeRegex(searchTerm);
    printNameResults(results, escapedTerm);
    console.log('\x1b[90mFound ' + results.length + ' session(s) by name.\x1b[0m');
    console.log('\x1b[90mResume: cd <dir> && claude --resume <session-id>\x1b[0m\n');
    return;
  }

  console.log('\n\x1b[1m\x1b[36mSearching for:\x1b[0m "' + searchTerm + '"\n');

  const allFiles = utils.getAllSessionFiles();

  if (allFiles.length === 0) {
    console.log('\x1b[33mNo Claude sessions found.\x1b[0m\n');
    return;
  }

  let resultCount = 0;
  const escapedTerm = utils.escapeRegex(searchTerm);
  // Build alternation regex for multi-token highlighting
  const tokenPattern = escapedTerm.split(/\s+/).filter(Boolean).join('|');

  // Phase 2: metadata pre-pass — collect tag/title/summary matches from registry
  // before body-scanning JSONLs. This surfaces sessions where the search term
  // appears in metadata but not in the transcript body (the motivating case).
  const metaResults = searchByName();
  const metaMap = new Map(metaResults.map(r => [r.sessionId, r]));

  for (const file of allFiles) {
    const projectPath = utils.decodeProjectPath(file.projectDir);
    const projectName = projectPath.split('/').pop();
    const sessionId = path.basename(file.filePath, '.jsonl');

    // Pre-read custom title (user rename) from JSONL tail — survives line limit
    const preReadTitle = utils.readCustomTitle(file.filePath);

    let result = await searchSession(file.filePath, projectPath);
    // Inject pre-read title if the stream didn't reach it (file > maxLinesPerFile)
    if (result && !result.customTitle && preReadTitle) {
      result.customTitle = preReadTitle;
    }
    // Synthesize a result for title-only matches (no body content matched)
    if (!result && preReadTitle && preReadTitle.toLowerCase().includes(searchTerm)) {
      result = {
        sessionId,
        projectPath,
        timestamp: await getFirstLineTimestamp(file.filePath),
        sessionSlug: utils.readSessionSlug(file.filePath),
        sessionSummary: '',
        customTitle: preReadTitle,
        matches: [],
      };
    }

    // Merge metadata hit if body scan missed this session
    const metaHit = metaMap.get(sessionId);
    if (!result && metaHit) {
      result = {
        sessionId,
        projectPath,
        timestamp: await getFirstLineTimestamp(file.filePath),
        sessionSlug: metaHit.slug || utils.readSessionSlug(file.filePath),
        sessionSummary: '',
        customTitle: '',
        matches: [],
        metadataHits: metaHit.matchedFields,
      };
    } else if (result && metaHit) {
      // Body matched too — attach metadata fields for richer display
      result.metadataHits = metaHit.matchedFields;
    }
    // Consume from map so we don't double-print
    if (metaHit) metaMap.delete(sessionId);

    if (result) {
      resultCount++;
      const gitRemote = utils.getGitRemote(projectPath);
      console.log(
        '\x1b[33m[' + resultCount + ']\x1b[0m \x1b[1m' + projectName +
        '\x1b[0m \x1b[90m(' + utils.formatAge(result.timestamp) + ')\x1b[0m'
      );

      if (result.customTitle) {
        const highlightedTitle = result.customTitle.replace(
          new RegExp('(' + escapedTerm + ')', 'gi'),
          '\x1b[43m\x1b[30m$1\x1b[0m\x1b[1m\x1b[35m'
        );
        console.log('    \x1b[90mName:\x1b[0m \x1b[1m\x1b[35m' + highlightedTitle + '\x1b[0m');
      }
      if (result.sessionSummary) {
        console.log('    \x1b[90mSummary:\x1b[0m \x1b[1m' + result.sessionSummary + '\x1b[0m');
      }
      if (result.sessionSlug) {
        console.log('    \x1b[90mSession:\x1b[0m ' + result.sessionSlug);
      }
      if (gitRemote) {
        console.log('    \x1b[90mRepo:\x1b[0m \x1b[34m' + gitRemote + '\x1b[0m');
      }
      console.log('    \x1b[90mDir:\x1b[0m ' + result.projectPath);
      console.log('    \x1b[90mID:\x1b[0m ' + result.sessionId);
      console.log('    \x1b[90mResume:\x1b[0m \x1b[36mcd ' + result.projectPath + ' && claude --resume ' + result.sessionId + '\x1b[0m');

      // Show metadata match indicators (tag/title/summary from registry)
      if (result.metadataHits && result.metadataHits.length > 0) {
        result.metadataHits.forEach(({ field, value }) => {
          const label = field.charAt(0).toUpperCase() + field.slice(1);
          const highlighted = value.replace(
            new RegExp('(' + tokenPattern + ')', 'gi'),
            '\x1b[43m\x1b[30m$1\x1b[0m'
          );
          console.log('    \x1b[32m›\x1b[0m \x1b[90m' + label + ':\x1b[0m ' + highlighted);
        });
      }

      result.matches.forEach((match) => {
        const highlighted = match.replace(
          new RegExp('(' + escapedTerm + ')', 'gi'),
          '\x1b[43m\x1b[30m$1\x1b[0m'
        );
        console.log(
          '    \x1b[32m›\x1b[0m ' +
          highlighted.substring(0, 120) +
          (match.length > 120 ? '...' : '')
        );
      });
      console.log('');

      if (resultCount >= maxResults) {
        console.log('\x1b[90m... (showing first ' + maxResults + ' results)\x1b[0m\n');
        return;
      }
    }
  }

  // Flush remaining metadata-only matches not covered by the JSONL file scan
  // (sessions whose project dir encoding didn't match, edge case)
  for (const meta of metaMap.values()) {
    if (resultCount >= maxResults) break;
    resultCount++;
    console.log(
      '\x1b[33m[' + resultCount + ']\x1b[0m \x1b[1m' + meta.projectName +
      '\x1b[0m \x1b[90m(' + utils.formatAge(meta.fileMtime) + ')\x1b[0m'
    );
    meta.matchedFields.forEach(({ field, value }) => {
      const label = field.charAt(0).toUpperCase() + field.slice(1);
      const highlighted = value.replace(
        new RegExp('(' + tokenPattern + ')', 'gi'),
        '\x1b[43m\x1b[30m$1\x1b[0m'
      );
      console.log('    \x1b[32m›\x1b[0m \x1b[90m' + label + ':\x1b[0m ' + highlighted);
    });
    if (meta.slug) console.log('    \x1b[90mSession:\x1b[0m ' + meta.slug);
    console.log('    \x1b[90mDir:\x1b[0m ' + meta.projectPath);
    console.log('    \x1b[90mID:\x1b[0m ' + meta.sessionId);
    console.log('    \x1b[90mResume:\x1b[0m \x1b[36mcd ' + meta.projectPath + ' && claude --resume ' + meta.sessionId + '\x1b[0m');
    console.log('');
  }

  if (resultCount === 0) {
    console.log('\x1b[33mNo matches found.\x1b[0m\n');
  } else {
    console.log('\x1b[90mFound ' + resultCount + ' session(s) with matches.\x1b[0m');
    console.log('\x1b[90mResume: cd <dir> && claude --resume <session-id>\x1b[0m\n');
  }
}

main().catch(console.error);
