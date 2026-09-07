#!/usr/bin/env bash
# ghostty-resume.sh — open a Claude Code or Codex session (or any command) in a new Ghostty tab
#
# The single terminal opener for claude-tracker-suite. Writes a tiny launcher
# script to ~/.claude/run/launch/ and has Ghostty run "bash <its short path>"
# in a new tab or split: through Ghostty's AppleScript dictionary (>= 1.3.0,
# no keystrokes, no clipboard), or on older builds via Cmd-T + one paste.
# No shell escaping crosses AppleScript. The launcher itself checks the
# project dir and transcript and falls back to a fresh session with a reason.
#
# Usage:
#   ghostty-resume.sh <session-id> [--agent claude|codex] [--project <path>] [--name <title>]
#   ghostty-resume.sh --exec "<command>" --project <path> [--name <title>]
#   ghostty-resume.sh <session-id> --split [right|left|down|up]   # split the current tab instead
#   ghostty-resume.sh <session-id> --print          # write the launcher, print its path, open nothing
#   ghostty-resume.sh --help
#
# Arguments:
#   <session-id>         Session to resume (claude UUID or codex UUID).
#   --agent <name>       claude (default) or codex.
#   --project <path>     Explicit project directory (skips auto-detection; required for codex
#                        and for --exec).
#   --exec <command>     Run this command instead of a resume (new sessions: "claude -n foo").
#   --split [dir]        Open in a split of the focused terminal (right — default — left,
#                        down, up) instead of a new tab. Needs Ghostty >= 1.3.0.
#   --name <title>       Label used in this script's output only. Claude Code sets the tab
#                        title itself (-n / derived name), so nothing is injected.
#   --print              Only write the launcher and print its path (for in-place exec).
#   --help / -h          Print this usage message and exit.
#
# Delivery: Ghostty >= 1.3.0 exposes an AppleScript dictionary (surface
# configuration + new tab / split), used directly — no keystrokes, no
# clipboard, no focus dependency. Older builds (incl. pre-March-2026 nightlies)
# fall back to activate + Cmd-T + one paste of the launcher path.
#
# Exit codes: 0 opened · 1 bad arguments / unresolvable session · 2 Ghostty or
# Accessibility unavailable (message explains the fix).

set -uo pipefail

usage() {
  sed -n '2,36p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

SESSION_ID=""
PROJECT_DIR=""
TAB_NAME=""
AGENT="claude"
EXEC_CMD=""
SPLIT_DIR=""
PRINT_ONLY=false
LAUNCH_DIR="$HOME/.claude/run/launch"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage ;;
    --agent)
      [[ $# -lt 2 ]] && { echo "ghostty-resume: --agent requires claude or codex" >&2; exit 1; }
      AGENT="$2"
      [[ "$AGENT" == "claude" || "$AGENT" == "codex" ]] || { echo "ghostty-resume: unknown agent: $AGENT" >&2; exit 1; }
      shift 2 ;;
    --project)
      [[ $# -lt 2 ]] && { echo "ghostty-resume: --project requires a path" >&2; exit 1; }
      PROJECT_DIR="$2"; shift 2 ;;
    --name)
      [[ $# -lt 2 ]] && { echo "ghostty-resume: --name requires a title" >&2; exit 1; }
      TAB_NAME="$2"; shift 2 ;;
    --exec)
      [[ $# -lt 2 ]] && { echo "ghostty-resume: --exec requires a command" >&2; exit 1; }
      EXEC_CMD="$2"; shift 2 ;;
    --print) PRINT_ONLY=true; shift ;;
    --split)
      SPLIT_DIR="right"
      if [[ $# -ge 2 ]]; then
        case "$2" in
          right|left|down|up) SPLIT_DIR="$2"; shift ;;
          -*|'') ;;
          *) echo "ghostty-resume: --split takes right|left|down|up (got: $2)" >&2; exit 1 ;;
        esac
      fi
      shift ;;
    --no-activate) shift ;;   # accepted for compatibility; the native path never activates
    -*) echo "ghostty-resume: unknown option: $1" >&2; exit 1 ;;
    *)
      if [[ -z "$SESSION_ID" ]]; then SESSION_ID="$1"
      else echo "ghostty-resume: unexpected argument: $1" >&2; exit 1; fi
      shift ;;
  esac
done

if [[ -z "$EXEC_CMD" ]]; then
  [[ -z "$SESSION_ID" ]] && { echo "ghostty-resume: session ID (or --exec) is required" >&2; exit 1; }
  if [[ ! "$SESSION_ID" =~ ^[a-zA-Z0-9-]+$ ]]; then
    echo "ghostty-resume: invalid session ID: $SESSION_ID" >&2; exit 1
  fi
else
  [[ -z "$PROJECT_DIR" ]] && { echo "ghostty-resume: --exec requires --project" >&2; exit 1; }
fi

[[ "$(uname)" == "Darwin" ]] || { echo "ghostty-resume: macOS only" >&2; exit 1; }

if [[ "$AGENT" == "codex" && -z "$PROJECT_DIR" ]]; then
  echo "ghostty-resume: --project is required for codex sessions (not in tracker DB)" >&2
  exit 1
fi

# --- Resolve project directory and transcript for claude resumes ---------------

TRANSCRIPT=""
if [[ -z "$EXEC_CMD" && "$AGENT" == "claude" ]]; then
  RESOLVED=$(node -e '
    const sid = process.argv[1];
    const os = require("os"), path = require("path"), fs = require("fs");
    const utils = require(path.join(os.homedir(), ".claude/lib/tracker-utils"));
    let project = "", transcript = "";
    const projDir = path.join(os.homedir(), ".claude/projects");
    try {
      for (const d of fs.readdirSync(projDir, { withFileTypes: true })) {
        if (!d.isDirectory()) continue;
        const p = path.join(projDir, d.name, sid + ".jsonl");
        if (fs.existsSync(p)) { transcript = p; project = utils.decodeProjectPath(d.name); break; }
      }
    } catch (e) {}
    if (!project) {
      const db = utils.tryDb();
      if (db) {
        try {
          const s = db.getSessionById(sid);
          if (s) {
            transcript = transcript || s.transcript_path || "";
            project = s.project_path && !s.project_path.startsWith("-") ? s.project_path
              : utils.decodeProjectPath(s.project_dir || s.project_path);
          }
        } catch (e) {}
      }
    }
    process.stdout.write(project + "\t" + transcript);
  ' "$SESSION_ID" 2>/dev/null) || RESOLVED=""
  DETECTED_DIR="${RESOLVED%%$'\t'*}"
  TRANSCRIPT="${RESOLVED#*$'\t'}"
  [[ -z "$PROJECT_DIR" ]] && PROJECT_DIR="$DETECTED_DIR"
  if [[ -z "$PROJECT_DIR" ]]; then
    echo "ghostty-resume: could not resolve project directory for session $SESSION_ID" >&2
    echo "ghostty-resume: use --project <path> to specify it explicitly" >&2
    exit 1
  fi
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "ghostty-resume: project directory missing (moved or deleted): $PROJECT_DIR" >&2
  exit 1
fi

# --- Write the launcher ----------------------------------------------------------

mkdir -p "$LAUNCH_DIR" && chmod 700 "$LAUNCH_DIR"
find "$LAUNCH_DIR" -name '*.sh' -mtime +1 -delete 2>/dev/null || true

if [[ -n "$EXEC_CMD" ]]; then
  LAUNCHER="$LAUNCH_DIR/n-$(date +%s | tail -c 7)$RANDOM.sh"
else
  LAUNCHER="$LAUNCH_DIR/r-$(printf '%s' "${SESSION_ID:0:8}" | tr 'A-Z' 'a-z').sh"
fi

sq() { local q=\'; printf "'%s'" "${1//$q/$q\\$q$q}"; }   # 'it'\''s' — shell-safe single quoting

{
  echo '#!/usr/bin/env bash'
  echo "# generated by ghostty-resume.sh $(date '+%Y-%m-%d %H:%M:%S') — safe to delete"
  echo "cd $(sq "$PROJECT_DIR") 2>/dev/null || { echo 'project directory missing:' $(sq "$PROJECT_DIR") '— starting fresh in $HOME'; cd \"\$HOME\"; exec claude; }"
  if [[ -n "$EXEC_CMD" ]]; then
    echo "$EXEC_CMD"   # no exec: the command may be a compound (a; b) — bash stays as its parent
  elif [[ "$AGENT" == "codex" ]]; then
    echo "exec codex resume $SESSION_ID"
  else
    if [[ -n "$TRANSCRIPT" ]]; then
      echo "[ -f $(sq "$TRANSCRIPT") ] || { echo 'transcript missing for ${SESSION_ID:0:8} — starting a fresh session here'; exec claude; }"
    fi
    # No ||-fallback on the resume itself: a Ctrl-C must not spawn a second claude
    echo "exec claude --resume $SESSION_ID"
  fi
} > "$LAUNCHER"
chmod 700 "$LAUNCHER"

SHORT_PATH="~/.claude/run/launch/$(basename "$LAUNCHER")"

if [[ "$PRINT_ONLY" == "true" ]]; then
  echo "$LAUNCHER"
  exit 0
fi

# --- Open the tab ---------------------------------------------------------------

[[ -d "/Applications/Ghostty.app" ]] || { echo "ghostty-resume: Ghostty.app not found in /Applications" >&2; exit 2; }

# pgrep is unreliable here (the binary is "ghostty", and pgrep returns nothing
# under some sandboxes even for that), so detect the running app via ps.
ghostty_running() { ps -axo comm= | grep -q '/Ghostty.app/Contents/MacOS/ghostty$'; }

# Ghostty >= 1.3.0 (March 2026) ships an AppleScript dictionary: a "surface
# configuration" carries the working directory and the input to send, and
# "new tab"/"split" create the surface with it. No keystrokes, no clipboard,
# no dependency on which tab has keyboard focus. Detected by the presence of
# the scripting definition; older/nightly builds fall back to Cmd-T + paste.
GHOSTTY_SCRIPTABLE=false
sdef /Applications/Ghostty.app >/dev/null 2>&1 && GHOSTTY_SCRIPTABLE=true

NATIVE_DONE=false
if [[ "$GHOSTTY_SCRIPTABLE" == "true" ]]; then
  # --- Native path: Ghostty scripting dictionary -----------------------------
  # `initial input` is written to the new surface's pty right after its shell
  # starts (the same bytes typing would produce), so the launcher runs under
  # the normal login shell and the tab stays open with a prompt after claude
  # exits. `return` (CR) is what the Enter key sends.
  GHOSTTY_RESULT=$(osascript - "$SHORT_PATH" "$PROJECT_DIR" "$SPLIT_DIR" <<'APPLESCRIPT'
on run argv
    set launcherPath to item 1 of argv
    set projectDir to item 2 of argv
    set splitDir to item 3 of argv
    tell application "Ghostty"
        set cfg to new surface configuration
        set initial working directory of cfg to projectDir
        set initial input of cfg to "bash " & launcherPath & return
        if (count of windows) is 0 then
            set w to new window with configuration cfg
            set t to focused terminal of selected tab of w
            return "window:" & (id of t)
        else if splitDir is "" then
            set newTab to new tab in front window with configuration cfg
            set t to focused terminal of newTab
            return "tab:" & (id of t)
        else
            set target to focused terminal of selected tab of front window
            if splitDir is "right" then
                set t to split target direction right with configuration cfg
            else if splitDir is "left" then
                set t to split target direction left with configuration cfg
            else if splitDir is "down" then
                set t to split target direction down with configuration cfg
            else
                set t to split target direction up with configuration cfg
            end if
            return "split-" & splitDir & ":" & (id of t)
        end if
    end tell
end run
APPLESCRIPT
  )
  RC=$?
  if [[ $RC -eq 0 ]]; then
    NATIVE_DONE=true
    SURFACE_KIND="${GHOSTTY_RESULT%%:*}"
  else
    # A build can ship the sdef yet lack a command (early 1.3 nightlies): the
    # native call fails cleanly without sending anything, so fall back.
    echo "ghostty-resume: Ghostty scripting failed (exit $RC) — falling back to Cmd-T + paste" >&2
  fi
fi

if [[ "$NATIVE_DONE" != "true" ]]; then
  # --- Fallback path: Cmd-T + one paste event (pre-1.3 builds) ----------------
  if [[ -n "$SPLIT_DIR" ]]; then
    echo "ghostty-resume: --split needs Ghostty >= 1.3.0 (scripting dictionary); opening a tab instead" >&2
  fi
  if ! osascript -e 'tell application "System Events" to UI elements enabled' 2>/dev/null | grep -q true; then
    echo "ghostty-resume: Accessibility is not enabled for this terminal/osascript." >&2
    echo "  Fix: System Settings → Privacy & Security → Accessibility → enable the app running this script" >&2
    echo "  Then run: bash $SHORT_PATH  (in any Ghostty tab)" >&2
    exit 2
  fi

  JUST_LAUNCHED=false
  if ! ghostty_running; then
    open -a Ghostty
    JUST_LAUNCHED=true
    for _ in $(seq 1 20); do ghostty_running && break; sleep 0.25; done
    sleep 1.5   # first window + shell prompt
  fi

  # Activate, Cmd-T, a fixed 1 s settle so the new surface owns keyboard focus,
  # then ONE paste event (Cmd-V) of the short launcher path and Return. Typing
  # character-by-character races the new tab for focus and lands in whichever
  # tab is active; a single paste after the settle is what has proven reliable.
  # Clipboard is saved/restored (plain text only). A tab-count guard aborts
  # before pasting if Cmd-T produced no new tab, so nothing can be injected
  # into a live session. This whole path is inherently racy against a human
  # switching tabs during the ~2 s window — the dictionary path above is not.
  old_clipboard="$(pbpaste 2>/dev/null || true)"
  printf 'bash %s' "$SHORT_PATH" | pbcopy

  osascript - "$JUST_LAUNCHED" <<'APPLESCRIPT'
on tabCount()
    tell application "System Events"
        tell process "Ghostty"
            try
                return count of radio buttons of tab group 1 of front window
            on error
                return 1 -- a single tab shows no tab bar
            end try
        end tell
    end tell
end tabCount

on run argv
    set justLaunched to item 1 of argv
    tell application "Ghostty" to activate
    delay 0.5
    if justLaunched is not "true" then
        set nBefore to tabCount()
        tell application "System Events"
            tell process "Ghostty"
                keystroke "t" using command down
            end tell
        end tell
        delay 1.0
        if tabCount() ≤ nBefore then error "no new tab appeared (tab count stayed at " & nBefore & ")" number 3
    end if
    tell application "System Events"
        tell process "Ghostty"
            keystroke "v" using command down
            delay 0.2
            keystroke return
        end tell
    end tell
end run
APPLESCRIPT
  RC=$?
  sleep 0.3
  printf '%s' "$old_clipboard" | pbcopy 2>/dev/null || true
  if [[ $RC -ne 0 ]]; then
    echo "ghostty-resume: could not open a tab (exit $RC). Nothing was pasted. Run manually: bash $SHORT_PATH" >&2
    exit 2
  fi
  SURFACE_KIND="tab"
fi

LABEL="${TAB_NAME:-$(basename "$PROJECT_DIR")—${SESSION_ID:0:8}}"
case "$SURFACE_KIND" in
  split-right|split-down) WHERE="Ghostty split (${SURFACE_KIND#split-})" ;;
  window) WHERE="new Ghostty window" ;;
  *) WHERE="Ghostty tab" ;;
esac
if [[ -n "$EXEC_CMD" ]]; then
  echo "Opened ${WHERE} (${LABEL}): cd ${PROJECT_DIR} && ${EXEC_CMD}"
else
  echo "Opened ${WHERE} (${LABEL}): ${AGENT} resume ${SESSION_ID:0:8} in ${PROJECT_DIR}"
fi
