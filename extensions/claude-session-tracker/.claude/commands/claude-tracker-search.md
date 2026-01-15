# Search Claude Sessions

Search across all your Claude sessions for specific keywords.

## Arguments

$ARGUMENTS - Search term(s) to find in your sessions

## Instructions

```bash
node -e "
const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const searchTerm = '$ARGUMENTS'.toLowerCase();

if (!searchTerm || searchTerm === '\$arguments') {
  console.log('\\n\\x1b[33mUsage:\\x1b[0m /claude-tracker-search <search-term>');
  console.log('\\x1b[90mExample: /claude-tracker-search \"websocket\"\\x1b[0m\\n');
  process.exit(0);
}

function decodeProjectPath(dirName) {
  return dirName.replace(/^-/, '/').replace(/-/g, '/');
}

async function searchSession(filePath, projectPath) {
  return new Promise((resolve) => {
    const sessionId = path.basename(filePath, '.jsonl');
    const matches = [];
    let timestamp = '';

    const stream = fs.createReadStream(filePath);
    const rl = readline.createInterface({ input: stream, crlfDelay: Infinity });

    rl.on('line', (line) => {
      try {
        const data = JSON.parse(line);
        if (!timestamp && data.timestamp) timestamp = data.timestamp;

        if (data.type === 'user' && data.message?.content) {
          const content = data.message.content;
          if (content.toLowerCase().includes(searchTerm) &&
              !content.includes('<observed_from_primary_session>')) {
            matches.push(content.substring(0, 150).replace(/\\n/g, ' '));
          }
        }
        if (data.type === 'assistant' && data.message?.content) {
          const content = data.message.content;
          if (content.toLowerCase().includes(searchTerm)) {
            matches.push('[Assistant] ' + content.substring(0, 150).replace(/\\n/g, ' '));
          }
        }
      } catch {}
    });

    rl.on('close', () => {
      stream.destroy();
      if (matches.length > 0) {
        resolve({ sessionId, projectPath, timestamp, matches: matches.slice(0, 5) });
      } else {
        resolve(null);
      }
    });

    rl.on('error', () => { stream.destroy(); resolve(null); });
  });
}

function formatAge(isoDate) {
  if (!isoDate) return '';
  const diff = Date.now() - new Date(isoDate).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 24) return hours + 'h ago';
  return Math.floor(hours / 24) + 'd ago';
}

async function main() {
  console.log('\\n\\x1b[1m\\x1b[36mSearching for:\\x1b[0m \"' + searchTerm + '\"\\n');

  if (!fs.existsSync(PROJECTS_DIR)) {
    console.log('\\x1b[33mNo Claude sessions found.\\x1b[0m\\n');
    return;
  }

  const projectDirs = fs.readdirSync(PROJECTS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => ({ name: d.name, path: path.join(PROJECTS_DIR, d.name) }));

  let resultCount = 0;

  for (const dir of projectDirs) {
    try {
      const files = fs.readdirSync(dir.path).filter(f => f.endsWith('.jsonl'));
      const projectPath = decodeProjectPath(dir.name);
      const projectName = projectPath.split('/').pop();

      for (const f of files) {
        const result = await searchSession(path.join(dir.path, f), projectPath);
        if (result) {
          resultCount++;
          console.log('\\x1b[33m[' + resultCount + ']\\x1b[0m \\x1b[1m' + projectName + '\\x1b[0m \\x1b[90m(' + formatAge(result.timestamp) + ')\\x1b[0m');
          console.log('    \\x1b[90mSession:\\x1b[0m ' + result.sessionId);

          result.matches.forEach(match => {
            // Highlight search term
            const highlighted = match.replace(new RegExp('(' + searchTerm + ')', 'gi'), '\\x1b[43m\\x1b[30m\$1\\x1b[0m');
            console.log('    \\x1b[32m›\\x1b[0m ' + highlighted.substring(0, 100) + (match.length > 100 ? '...' : ''));
          });
          console.log('');

          if (resultCount >= 15) {
            console.log('\\x1b[90m... (showing first 15 results)\\x1b[0m\\n');
            return;
          }
        }
      }
    } catch {}
  }

  if (resultCount === 0) {
    console.log('\\x1b[33mNo matches found.\\x1b[0m\\n');
  } else {
    console.log('\\x1b[90mFound ' + resultCount + ' session(s) with matches.\\x1b[0m');
    console.log('\\x1b[90mResume: claude --resume <session-id>\\x1b[0m\\n');
  }
}

main().catch(console.error);
"
```
