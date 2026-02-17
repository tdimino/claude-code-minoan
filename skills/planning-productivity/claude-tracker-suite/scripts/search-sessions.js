#!/usr/bin/env node
/**
 * search-sessions.js — Search all Claude Code sessions by keyword
 *
 * Usage: node search-sessions.js <search-term> [--limit N]
 *
 * Searches user and assistant messages across all session JSONL files.
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

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--limit' && args[i + 1]) {
    maxResults = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i] === '--lines' && args[i + 1]) {
    maxLinesPerFile = parseInt(args[i + 1], 10);
    i++;
  } else if (!searchTerm) {
    searchTerm = args[i].toLowerCase();
  }
}

if (!searchTerm) {
  console.log('\n\x1b[33mUsage:\x1b[0m node search-sessions.js <search-term> [--limit N]');
  console.log('\x1b[90mExample: node search-sessions.js "kothar mac mini"');
  console.log('Example: node search-sessions.js "websocket" --limit 5\x1b[0m\n');
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
      if (matches.length > 0) {
        resolve({
          sessionId,
          projectPath,
          timestamp,
          sessionSlug,
          sessionSummary,
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

          // Search user messages
          if (data.type === 'user' && data.message && data.message.content) {
            const content = data.message.content;
            if (typeof content === 'string' &&
                content.toLowerCase().includes(searchTerm) &&
                !isNoise(content)) {
              matches.push(content.substring(0, 200).replace(/\n/g, ' '));
            }
          }

          // Search assistant messages
          if (data.type === 'assistant' && data.message && data.message.content) {
            const content = data.message.content;
            if (typeof content === 'string' &&
                content.toLowerCase().includes(searchTerm) &&
                !isNoise(content)) {
              matches.push('[Assistant] ' + content.substring(0, 200).replace(/\n/g, ' '));
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

async function main() {
  console.log('\n\x1b[1m\x1b[36mSearching for:\x1b[0m "' + searchTerm + '"\n');

  const allFiles = utils.getAllSessionFiles();

  if (allFiles.length === 0) {
    console.log('\x1b[33mNo Claude sessions found.\x1b[0m\n');
    return;
  }

  let resultCount = 0;
  const escapedTerm = utils.escapeRegex(searchTerm);

  for (const file of allFiles) {
    const projectPath = utils.decodeProjectPath(file.projectDir);
    const projectName = projectPath.split('/').pop();

    const result = await searchSession(file.filePath, projectPath);
    if (result) {
      resultCount++;
      const gitRemote = utils.getGitRemote(projectPath);
      console.log(
        '\x1b[33m[' + resultCount + ']\x1b[0m \x1b[1m' + projectName +
        '\x1b[0m \x1b[90m(' + utils.formatAge(result.timestamp) + ')\x1b[0m'
      );

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

  if (resultCount === 0) {
    console.log('\x1b[33mNo matches found.\x1b[0m\n');
  } else {
    console.log('\x1b[90mFound ' + resultCount + ' session(s) with matches.\x1b[0m');
    console.log('\x1b[90mResume: claude --resume <session-id>\x1b[0m\n');
  }
}

main().catch(console.error);
