# Claude Session Tracker v0.2.1 - Manual Test Checklist

## Test 1: Click Behavior (Critical)

**Purpose:** Verify clicking "Claude Active" never auto-runs `claude --continue`

### Steps:
1. Open VS Code with the extension
2. Start Claude in a terminal (`claude` command)
3. Wait for status bar to show "Claude Active"
4. Click "Claude Active" in status bar

### Expected:
- [ ] QuickPick dialog appears showing sessions
- [ ] No terminal receives any automatic input
- [ ] Active terminal shows with "Active" badge
- [ ] User must explicitly select before any action

### Fail Criteria:
- Any terminal automatically receives `claude --continue`
- Session resumes without user selection

---

## Test 2: Session Picker Contents

**Purpose:** Verify picker shows correct sessions

### Steps:
1. Start Claude in 2 different workspaces
2. Close one Claude session (Ctrl+C or close terminal)
3. Click "Claude Active" status bar

### Expected:
- [ ] Active terminals appear at top with $(terminal-tmux) icon
- [ ] Closed sessions appear with $(debug-restart) icon
- [ ] Sessions older than 12 hours do NOT appear
- [ ] Project paths and git branches shown correctly

---

## Test 3: Resume Flow

**Purpose:** Verify resume sends correct command

### Steps:
1. Have a resumable session in the picker
2. Click "Claude Active"
3. Select a resumable session

### Expected:
- [ ] New terminal opens in correct workspace directory
- [ ] Command `claude --resume <sessionId>` is sent
- [ ] NOT `claude --continue`

---

## Test 4: Multi-Window Cross-Window State

**Purpose:** Verify race conditions are fixed

### Steps:
1. Open 3 VS Code windows in different workspaces
2. Start Claude in each window simultaneously (within 2 seconds)
3. Check status bar in each window

### Expected:
- [ ] All windows show correct total count
- [ ] No sessions are lost
- [ ] Cross-window state file is not corrupted

### Verification:
```bash
cat ~/.claude/vscode-tracker-state.json | jq '.windows | keys | length'
# Should show 3
```

---

## Test 5: Crash Recovery

**Purpose:** Verify crash-recoverable sessions work

### Steps:
1. Start Claude sessions in 2 windows
2. Force-quit VS Code: `pkill -9 "Code"`
3. Reopen VS Code

### Expected:
- [ ] Status bar shows "Recover Claude (2)" with warning background
- [ ] Clicking shows recovery options
- [ ] Sessions can be recovered to correct workspaces

---

## Test 6: 12-Hour Filter

**Purpose:** Verify old sessions are filtered

### Steps:
1. Check for old session files:
```bash
find ~/.claude/projects -name "*.jsonl" -mtime +1 | head -5
```
2. Click "Claude Active" status bar

### Expected:
- [ ] Sessions modified >12 hours ago do NOT appear
- [ ] Only recent sessions shown
- [ ] Count in placeholder matches visible items

---

## Test 7: Terminal Detection (TOCTOU)

**Purpose:** Verify terminal detection handles race conditions

### Steps:
1. Rapidly open and close terminals:
```bash
for i in {1..5}; do
  osascript -e 'tell application "Visual Studio Code" to activate'
  sleep 0.5
done
```
2. Check VS Code Developer Console for errors

### Expected:
- [ ] No unhandled promise rejections
- [ ] No "Terminal closed during tracking" errors that crash extension
- [ ] Status bar remains responsive

---

## Test 8: Memory Leaks (File Watcher)

**Purpose:** Verify file watchers are cleaned up

### Steps:
1. Open/close VS Code 5 times
2. Monitor memory:
```bash
while true; do
  ps aux | grep "Code Helper" | grep -v grep | awk '{sum += $6} END {print sum/1024 " MB"}'
  sleep 5
done
```

### Expected:
- [ ] Memory doesn't grow unboundedly
- [ ] No "EMFILE: too many open files" errors

---

## Automated Verification Commands

```bash
# Check cross-window state file format
cat ~/.claude/vscode-tracker-state.json | jq '.'

# Count recent sessions (last 12h)
find ~/.claude/projects -name "*.jsonl" -mmin -720 | wc -l

# Check for corrupted state file
node -e "console.log(JSON.parse(require('fs').readFileSync('$HOME/.claude/vscode-tracker-state.json')))"

# List all session files by modification time
ls -lt ~/.claude/projects/*/*.jsonl | head -20
```

---

## Sign-Off

| Test | Pass | Fail | Notes |
|------|------|------|-------|
| 1. Click Behavior | [ ] | [ ] | |
| 2. Session Picker | [ ] | [ ] | |
| 3. Resume Flow | [ ] | [ ] | |
| 4. Multi-Window | [ ] | [ ] | |
| 5. Crash Recovery | [ ] | [ ] | |
| 6. 12-Hour Filter | [ ] | [ ] | |
| 7. TOCTOU | [ ] | [ ] | |
| 8. Memory Leaks | [ ] | [ ] | |

**Tested By:** _______________
**Date:** _______________
**Version:** 0.2.1
