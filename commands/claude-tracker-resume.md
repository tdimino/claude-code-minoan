# Claude Session Resume

Resume a Claude session by its number from `/claude-tracker` output.

## Arguments

- `$ARGUMENTS` - Session number (1-20) from the tracker list

## Instructions

```bash
node -e "
const os = require('os');
const utils = require(os.homedir() + '/.claude/lib/tracker-utils.js');

const sessionNum = parseInt('$ARGUMENTS'.trim(), 10);

if (!sessionNum || sessionNum < 1 || sessionNum > 20) {
  console.log('\\x1b[31mError: Please provide a session number (1-20)\\x1b[0m');
  console.log('Usage: /claude-tracker-resume <number>');
  console.log('Example: /claude-tracker-resume 3');
  process.exit(1);
}

async function main() {
  const allFiles = utils.getAllSessionFiles();

  if (allFiles.length === 0) {
    console.log('No Claude sessions found.');
    return;
  }

  const recent = allFiles.slice(0, utils.MAX_SESSIONS);

  if (sessionNum > recent.length) {
    console.log('\\x1b[31mError: Only ' + recent.length + ' sessions available\\x1b[0m');
    process.exit(1);
  }

  const selected = recent[sessionNum - 1];
  const projectPath = utils.decodeProjectPath(selected.projectDir);
  const session = await utils.parseSession(selected.filePath, { projectPath });
  const projectName = projectPath.split('/').pop();

  console.log('\\x1b[36mResuming session #' + sessionNum + ':\\x1b[0m');
  console.log('  Project: \\x1b[1m' + projectName + '\\x1b[0m');
  if (session.sessionSummary) {
    console.log('  Summary: ' + session.sessionSummary);
  }
  if (session.sessionSlug) {
    console.log('  Session: ' + session.sessionSlug);
  }
  if (session.gitRemote) {
    console.log('  Repo: \\x1b[34m' + session.gitRemote + '\\x1b[0m');
  }
  const lastMsgTime = session.lastUserTimestamp ? utils.formatAge(session.lastUserTimestamp) : utils.formatAge(session.timestamp);
  console.log('  Last activity: ' + lastMsgTime);
  console.log('  Session ID: ' + session.fullId);
  console.log('');
  console.log('\\x1b[33mRun this command in your terminal:\\x1b[0m');
  console.log('\\x1b[32mclaude --resume ' + session.fullId + '\\x1b[0m');
  console.log('');
}

main().catch(console.error);
"
```

Shows the resume command for a session by its number from `/claude-tracker`.

Usage: `/claude-tracker-resume 3` - Shows command to resume session #3

Note: This command outputs the resume command for you to copy. Claude Code sessions must be resumed in a proper terminal environment.
