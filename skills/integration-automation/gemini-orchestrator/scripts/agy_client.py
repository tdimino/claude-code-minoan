"""The Antigravity CLI route for gemini-orchestrator. Standard library only; knows `agy` and nothing about OpenRouter.

Here the delegate is an agent with tools: it opens the files it chooses, so what leaves the machine is no longer a
pack. This module therefore builds the limits each run is given (a sandbox, per-run settings, one deny rule for every
file that may not be read), runs `agy --print` and reads its event stream, says how the run ended, and lists
afterwards what the delegate read and ran.

Verified against agy 1.5.14 on 2026-11-22 (the probe is recorded in the plan and in references/):
  - a deny rule under --sandbox must be an absolute path; a relative one breaks every shell command;
  - a tool that needs approval ends the run with an empty answer, status SUCCESS and exit 0;
  - the saved defaults may allow writes and network, so every run passes its own settings.
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import context_pack as cp

# `agy models`, 2026-11-22. Carbon is not offered on this route.
EFFORTS = {
    "neon": ("gemini-4-neon", ("low", "medium", "high", "xhigh")),
    "hydrogen": ("gemini-4-hydrogen", ("low", "medium", "high", "xhigh")),
    "argon": ("gemini-4-argon", ("low", "medium", "high")),
    "flash": ("gemini-3.8-flash", ("low", "medium", "high")),
}
MAX_SCAN_FILES = 20_000
MAX_SCAN_BYTES = 50 * 1024 * 1024
MAX_SETTINGS_BYTES = 200_000  # the settings travel on the command line
READ_TOOLS = {"read_file", "view_file"}


class AgyError(Exception):
    def __init__(self, message: str, *, usage: bool = False):
        super().__init__(message)
        self.usage = usage


def binary() -> str:
    found = os.environ.get("GEMINI_ORCH_AGY") or shutil.which("agy")
    if not found or not Path(found).exists():
        raise AgyError("the Antigravity CLI (agy) is not installed or not on PATH. Install it and run `agy` once to "
                       "sign in; --direct still works without it.")
    return found


def saved_settings() -> dict:
    path = Path(os.environ.get("GEMINI_ORCH_AGY_SETTINGS", Path.home() / ".gemini/antigravity-cli/settings.json"))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def model_slug(name: str, effort: str | None) -> str:
    """An alias and an effort -> the slug `agy --model` takes. Anything that is not an alias is passed as a slug."""
    if name == "carbon":
        raise AgyError(f"Carbon is not offered through agy; aliases here: {', '.join(EFFORTS)}. Use --direct for "
                       f"Carbon.", usage=True)
    if name not in EFFORTS:
        return name
    base, efforts = EFFORTS[name]
    effort = effort or "medium"
    if effort not in efforts:
        raise AgyError(f"{name} has no '{effort}' effort through agy; it has {', '.join(efforts)}", usage=True)
    return f"{base}-{effort}"


# --- personas -----------------------------------------------------------------------------------------------------

ALLOWED_TOOLS = {"view_file", "run_command"}  # the only two names that granted anything in the probe
# For a write profile only. Probed live: these names gave the model `write_file` and `edit_file`, which wrote inside
# the folder, were refused in .git by rule, and were refused outside the folder (that refusal ends the run empty).
WRITE_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content"}


def agents_home() -> Path:
    return Path(os.environ.get("GEMINI_ORCH_AGY_AGENTS", Path.home() / ".gemini/config/agents"))


def agent_name(profile: str) -> str:
    return f"orch-{profile}"  # the prefix keeps these apart from agents the user defines


FRONTMATTER_KEYS = {"name", "description", "tools", "subagent", "commandExecutionPolicy"}


def _frontmatter(front: str, source: Path) -> tuple[dict, list[str]]:
    """The few frontmatter forms a persona may use, read strictly: anything else is refused, not guessed at.

    Allowed: `key: value` at the margin, each key once and from the known set, and under `tools:` items written as
    two spaces, a dash and a name. A list in any other form, a repeated key or an unknown key could widen what the
    delegate may do while passing a looser check.
    """
    fields: dict[str, str] = {}
    tools: list[str] = []
    last = None
    for line in front.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and last == "tools":
            tools.append(line[4:].strip())
            continue
        key, colon, value = line.partition(":")
        if not colon or key not in FRONTMATTER_KEYS or key in fields or (key == "tools" and value.strip()):
            raise AgyError(f"{source}: frontmatter line not understood or not allowed: {line.strip()!r}")
        fields[key] = value.strip()
        last = key
    return fields, tools


def compose_persona(profile: str, harness: Path, *, write: bool = False) -> str:
    """The agent file agy reads: the persona's frontmatter, then the shared rules, then the role.

    agy takes a persona only as a file on disk, by name. The frontmatter is checked here, since it is what limits
    the delegate: the name must be the one passed to --agent, no tool beyond the two read-only ones (and, for a
    profile with write access, the write tools), and `subagent: false` so that agy's own planner never calls the
    persona uninvited. A write profile takes its shared rules from `_shared-write.md`.
    """
    allowed = ALLOWED_TOOLS | WRITE_TOOLS if write else ALLOWED_TOOLS
    source = harness / f"{profile}.md"
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as e:
        raise AgyError(f"profile '{profile}' has no harness persona ({source}); use --direct", usage=True) from e
    parts = text.split("---\n", 2)
    if len(parts) != 3 or parts[0].strip():
        raise AgyError(f"{source} must begin with a frontmatter block between two --- lines")
    front, body = parts[1], parts[2]
    fields, tools = _frontmatter(front, source)
    if fields.get("name") != agent_name(profile) or fields.get("subagent") != "false":
        raise AgyError(f"{source}: the frontmatter needs 'name: {agent_name(profile)}' and 'subagent: false'")
    if not tools or set(tools) - allowed:
        raise AgyError(f"{source}: tools must be drawn from {sorted(allowed)}; found {sorted(tools)}")
    if "run_command" in tools and fields.get("commandExecutionPolicy") != "sandbox":
        raise AgyError(f"{source}: a persona with run_command needs 'commandExecutionPolicy: sandbox'")
    shared = harness / ("_shared-write.md" if write else "_shared.md")
    rules = shared.read_text(encoding="utf-8").strip() + "\n\n" if shared.exists() else ""
    return f"---\n{front}---\n{rules}{body.lstrip()}"


def install_persona(profile: str, harness: Path, *, write: bool = False) -> str:
    """Write the persona where agy looks for it, if the installed copy differs. -> the name for --agent.

    The file is static, compared before writing and replaced in one step, so parallel launches cannot collide.
    """
    wanted = compose_persona(profile, harness, write=write)
    target = agents_home() / agent_name(profile) / "agent.md"
    try:
        if target.read_text(encoding="utf-8") == wanted:
            return agent_name(profile)
    except OSError:
        pass
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".agent.md.{os.getpid()}.tmp")
    temp.write_text(wanted, encoding="utf-8")
    os.replace(temp, target)
    return agent_name(profile)


# --- what the delegate may not read -------------------------------------------------------------------------------

# Folders denied whole, at any depth: git's records carry the author's address, and the other two hold earlier
# runs' streams and the issue tracker. The rest of cp.SKIP_DIRS (dependencies, caches) stays readable and unscanned.
DENIED_DIRS = {".git", ".subdaimon-output", ".beans"}


def _walk(workspace: Path) -> Iterator[tuple[str, Path]]:
    """-> ("file", path) for every file to scan, git-ignored ones included (.env usually is); ("deny", path) for
    what is denied without being opened: the DENIED_DIRS, any linked folder, whose target could be anywhere, and a
    `.git` that is a file (a worktree's or a submodule's pointer to its repository); and ("name", path) for a
    credentials file by name inside a dependency folder, whose other files are neither scanned nor denied."""
    for root, dirs, names in os.walk(workspace):
        unscanned = bool(cp.SKIP_DIRS.intersection(Path(root).relative_to(workspace).parts))
        keep = []
        for d in sorted(dirs):
            p = Path(root) / d
            if d in DENIED_DIRS or p.is_symlink():
                yield "deny", p
            else:
                keep.append(d)
        dirs[:] = keep
        for name in sorted(names):
            if name == ".git":
                yield "deny", Path(root) / name
            elif not unscanned:
                yield "file", Path(root) / name
            elif cp.FORBIDDEN_NAME.search(name):
                yield "name", Path(root) / name


def _git_places(workspace: Path) -> set[Path]:
    """Where git keeps the author's address outside the walk: the global configs and this repository's own folder."""
    home = Path.home()
    places = [home / ".gitconfig", Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config") / "git/config",
              *_git_dirs(workspace), *_git_includes(home)]
    if os.environ.get("GIT_CONFIG_GLOBAL"):
        places.append(Path(os.environ["GIT_CONFIG_GLOBAL"]))
    found: set[Path] = set()
    for p in places:
        p = p if p.is_absolute() else Path.cwd() / p  # git reads a relative GIT_CONFIG_GLOBAL from where it runs
        try:
            there = p.exists() or p.is_symlink()  # a rule for a path that is not there is left out
            # GIT_CONFIG_GLOBAL=/dev/null is a common way to say "no config"; a rule on it would break `> /dev/null`
            there = there and not (p.is_char_device() or p.is_block_device() or p.is_fifo() or p.is_socket())
        except OSError:
            there = True  # it cannot be examined from here; deny it all the same
        if there:
            found.add(p)
            try:
                found.add(p.resolve())
            except OSError:
                pass
    return found


def _git_dirs(workspace: Path) -> list[Path]:
    """The repository's own folders, also when the workspace sits below the repository's top or in a worktree."""
    found = []
    for flag in ("--absolute-git-dir", "--git-common-dir"):
        try:
            out = subprocess.run(["git", "-C", str(workspace), "rev-parse", flag], capture_output=True, text=True,
                                 timeout=10)
        except (OSError, subprocess.SubprocessError):
            continue
        if out.returncode == 0 and out.stdout.strip():
            p = Path(out.stdout.strip())
            found.append((p if p.is_absolute() else workspace / p).resolve())
    for folder in (workspace, *workspace.parents):  # and without git's help, should it fail or be missing
        if (folder / ".git").exists():
            found.append(folder / ".git")
            break
    return found


def _git_includes(home: Path) -> list[Path]:
    """Files the global git config pulls in with include.path or includeIf.*.path; they can carry an address too."""
    try:
        out = subprocess.run(["git", "config", "--global", "--includes", "-z", "--get-regexp",
                              r"^include(if\..*)?\.path$"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    found = []
    for record in out.stdout.split("\0"):  # each record is the key, a newline, the value
        value = record.partition("\n")[2].strip()
        if value:
            p = Path(value).expanduser()
            found.append(p if p.is_absolute() else home / p)  # git reads a relative one from the config's folder
    return found


# Files and folders that steer an agent or a shell in this folder: Claude Code's, agy's and Codex's settings and
# rules, and direnv's. A write profile may not touch them, since the session that reads them runs outside the sandbox.
CONTROL_NAMES = (".claude", ".agents", ".gemini", "AGENTS.md", "GEMINI.md", "CLAUDE.md", ".envrc")
RULE_UNSAFE = re.compile(r"[()*?\[\]\x00-\x1f]")


def control_file(path: str) -> bool:
    """Is this path, or a folder above it, one of the CONTROL_NAMES? Compared without case, as macOS does."""
    names = {n.lower() for n in CONTROL_NAMES}
    return any(part.lower() in names for part in Path(path).parts)


def _gitlinks(workspace: Path) -> set[Path]:
    """Repositories recorded inside this one (submodules): git keeps their commit only, so cannot restore a file."""
    found = set()
    for record in _git(workspace, "ls-files", "-s", "-z").split("\0"):
        meta, tab, name = record.partition("\t")
        if tab and meta.startswith("160000 "):
            found.add(workspace / name)
    return found


def _text_for_scan(data: bytes) -> str:
    """A file's bytes as text for the scan. UTF-16 text and binary files are also read with the NUL bytes taken out."""
    text = data.decode("utf-8", "replace")
    if b"\0" in data:
        text += "\n" + data.replace(b"\0", b"").decode("utf-8", "replace")
    return text


def deny_rules(workspace: Path, addresses: list[str], *, exempt: set[str] | None = None,
               write: bool = False) -> tuple[list[str], list[tuple[str, str]]]:
    """-> (permission rules, [(path, why it is withheld)]). Every rule names an absolute path.

    Withheld: a credentials file by name, a file holding a denied address or a secret pattern, and a file too large
    to scan. `exempt` paths skip the secret patterns only, as on the direct route.
    """
    workspace = workspace.resolve()
    withheld: list[tuple[str, str]] = []
    denied: set[Path] = _git_places(workspace)
    count = 0
    for kind, p in _walk(workspace):
        if kind == "deny":
            denied.update((p, p.resolve()))
            continue
        if kind == "name":
            withheld.append((str(p.relative_to(workspace)), "credentials file"))
            denied.update((p, p.resolve()))
            continue
        count += 1
        if count > MAX_SCAN_FILES:
            raise AgyError(f"{workspace} holds more than {MAX_SCAN_FILES:,} files, too many to scan before a run. "
                           f"Run from a narrower folder, or use --direct with --context.", usage=True)
        rel = str(p.relative_to(workspace))
        try:
            if not p.is_file():
                continue
            why = None
        except OSError:  # a link into a folder that cannot be entered: is_file() raises on EACCES
            why = "could not be scanned"
        # A link is judged by its own name and by its target's: notes.txt -> ../.env is a credentials file.
        if why:
            pass
        elif any(cp.FORBIDDEN_NAME.search(str(name).replace(os.sep, "/")) for name in {rel, p.resolve()}):
            why = "credentials file"
        else:
            try:
                if p.stat().st_size > MAX_SCAN_BYTES:
                    why = "too large to scan"
                else:
                    data = p.read_bytes()
            except OSError:
                why = "could not be scanned"
            if why is None:
                found = cp.scan([(rel, _text_for_scan(data))], addresses, exempt=exempt)
                why = found[0].kind if found else None
        if why:
            withheld.append((rel, why))
            denied.update((p, p.resolve()))  # a link and its target both, since the sandbox may see either
    write_denied: set[Path] = set()
    if write:
        # A write run may change only what git can show and restore: nothing denied to reading (git's own folders,
        # withheld files), nothing git does not track, ignored or merely never added, no repository recorded
        # inside this one, and no file that steers an agent. New files can still be made. Probed live: these rules
        # bind the shell in the sandbox as well as the write tools.
        write_denied = (denied | _untracked(workspace) | _gitlinks(workspace)
                        | {workspace / name for name in CONTROL_NAMES})
    # How agy reads a bracket, a glob character or a line break inside a rule is not known: a rule read wrongly
    # either leaves its file open or, like a relative rule, breaks every shell command. Such a path stops the run.
    for p in sorted({workspace, *denied, *write_denied}):
        if RULE_UNSAFE.search(str(p)):
            raise AgyError(f"{str(p)!r} needs a permission rule, and its name holds a character (one of ()[]*? or a "
                           f"line break) that agy may misread in a rule. Rename it, or use --direct.", usage=True)
    rules = [f"read_file({p})" for p in sorted(denied)]
    if write:
        rules += [f"write_file({p})" for p in sorted(write_denied)]
    else:
        rules.append(f"write_file({workspace})")
    return rules, withheld


def _git(workspace: Path, *argv: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(workspace), *argv], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise AgyError(f"git {argv[0]} could not be run in {workspace}: {e}") from e
    if out.returncode != 0 and "not a git repository" in out.stderr.lower():
        raise AgyError(f"a profile that writes needs a git repository, so its changes can be seen and undone; "
                       f"git said of {workspace}: {out.stderr.strip()}", usage=True)
    if out.returncode != 0:
        raise AgyError(f"git {argv[0]} failed in {workspace}: {out.stderr.strip()}")
    return out.stdout


def _untracked(workspace: Path) -> set[Path]:
    """Existing paths under the workspace that git does not track, a wholly untracked folder as one entry."""
    names = _git(workspace, "ls-files", "--others", "--directory", "-z").split("\0")
    return {(workspace / name.rstrip("/")) for name in names if name}


def git_changes(workspace: Path) -> list[tuple[str, str]]:
    """-> [(status, path)] as `git status` gives them for the workspace, ignored files and folders included (`!!`).

    Run by the launcher, outside the sandbox: git does not run inside it. Paths are relative to the repository's
    top. Nothing is left out: the launcher's own output files are written after the second reading.
    """
    tokens = _git(workspace, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=matching",
                  "--", ".").split("\0")
    found, i = [], 0
    while i < len(tokens):
        token = tokens[i]
        i += 1
        if len(token) < 4:
            continue
        status, path = token[:2], token[3:]
        if "R" in status or "C" in status:
            i += 1  # a rename or copy is followed by the path it came from
        found.append((status.strip(), path))
    return found


def guarded(workspace: Path, withheld: list[tuple[str, str]]) -> list[Path]:
    """The paths a write run must leave as they are: the withheld files and everything git does not track."""
    workspace = workspace.resolve()
    return sorted({workspace / rel for rel, _ in withheld} | _untracked(workspace))


def fingerprints(paths: list[Path]) -> dict[str, str]:
    """-> {path: what is there now}: a file's hash, or only that a folder or a file too large to hash exists."""
    found = {}
    for p in paths:
        try:
            if p.is_file() and p.stat().st_size <= MAX_SCAN_BYTES:
                found[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
            elif p.exists() or p.is_symlink():
                found[str(p)] = "present"
        except OSError:
            found[str(p)] = "unreadable"
    return found


def disturbed(before: dict[str, str], paths: list[Path]) -> list[tuple[str, str]]:
    """-> [(path, "missing" or "altered")] against an earlier fingerprints(). The permission rules name paths, so a
    renamed parent folder would carry a withheld file out from under its rule; this is how that is noticed."""
    after = fingerprints(paths)
    return [(path, "missing" if path not in after else "altered")
            for path, was in sorted(before.items()) if after.get(path) != was]


# --- files agy loads by itself ------------------------------------------------------------------------------------

def shadow_agents(workspace: Path) -> list[Path]:
    """Agent folders in or above the workspace that carry this skill's prefix. agy also reads agents from
    `.agents/agents/` in a repository; one named like a persona here could be loaded in its place, tools and all."""
    found = []
    for folder in (workspace, *workspace.parents):
        found += sorted((folder / ".agents" / "agents").glob(f"{agent_name('')}*"))
    return found


def rules_files(workspace: Path) -> list[Path]:
    """AGENTS.md and GEMINI.md in the workspace and every folder above it, and the user's own GEMINI.md: agy puts
    them before the model without a tool step, so no deny rule and no audit covers them."""
    own = Path(os.environ.get("GEMINI_ORCH_AGY_RULES", Path.home() / ".gemini/GEMINI.md"))
    places = [folder / name for folder in (workspace, *workspace.parents) for name in ("AGENTS.md", "GEMINI.md")]
    return [p for p in (*places, own) if p.is_file()]


def run_settings(rules: list[str]) -> dict:
    """Settings for one run, passed with --settings and never saved. They replace the saved defaults that matter."""
    settings = {
        "agentMode": "",                          # not `auto`, which approves tools unasked
        "toolPermission": "proceed-in-sandbox",
        "enableTerminalSandbox": True,            # shell commands confined, with no network
        "useG1Credits": False,                    # when the quota runs out the call fails; nothing is charged
        "permissions": {"deny": rules},
    }
    if len(json.dumps(settings)) > MAX_SETTINGS_BYTES:
        raise AgyError(f"{len(rules):,} deny rules are too many for one command line. Run from a narrower folder.",
                       usage=True)
    return settings


def build_prompt(brief: str, workspace: Path, hints: list[str], *, write: bool = False) -> str:
    parts = [f"<task>\n{brief}\n</task>"]
    if hints:
        parts.append("Start with these files: " + ", ".join(hints))
    may = ("You may create and edit files inside this folder; you cannot reach the network." if write
           else "You cannot write files or reach the network.")
    parts.append(f"Work only inside this folder ({workspace}); asking for anything outside it ends the run with no "
                 f"answer. {may} When you quote a file, cite it as "
                 f"[path/from/this/folder:L12-L14] \"the exact words\".")
    return "\n\n".join(parts)


def build_command(agy: str, prompt: str, slug: str, settings: dict, *, seconds: float,
                  agent: str | None = None, write: bool = False) -> list[str]:
    cmd = [agy, "--print", prompt, "--model", slug, "--sandbox", "--disable-slash-commands",
           "--output-format", "stream-json", "--print-timeout", f"{max(1, round(seconds))}s",  # agy reads 0s as no limit
           "--settings", json.dumps(settings)]
    if agent:
        cmd += ["--agent", agent]
    if write:
        cmd += ["--mode", "accept-edits"]  # edits inside the folder go through unasked; nothing else is widened
    return cmd


# --- one run ------------------------------------------------------------------------------------------------------

@dataclass
class AgyResult:
    status: str = ""                 # SUCCESS or ERROR from agy; empty when no result event arrived
    response: str = ""
    error: str | None = None
    conversation_id: str | None = None
    model: str | None = None
    usage: dict = field(default_factory=dict)
    steps: int = 0
    tools: list[dict] = field(default_factory=list)   # finished tool steps: index, name, parameters, output
    denied: list[str] = field(default_factory=list)   # actions agy auto-denied because nobody could approve them
    stderr: str = ""
    exit_code: int | None = None
    stopped: str | None = None       # why the launcher killed the run, if it did
    partial_text: str = ""           # the last answer text streamed, kept when no result arrived
    timing: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)    # the raw stream


def absorb(result: AgyResult, line: str, elapsed: float) -> None:
    """Fold one line of the stream into the result. A line that is not JSON is kept in `lines` and otherwise ignored."""
    result.lines.append(line.rstrip("\n"))
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return
    if not isinstance(event, dict):
        return
    kind = event.get("event")
    result.conversation_id = event.get("conversation_id") or result.conversation_id
    body = event.get(kind) if isinstance(kind, str) else None
    if not isinstance(body, dict):
        return
    if kind == "init":
        result.model = body.get("model")
    elif kind == "step_update":
        step = body
        try:
            index = int(step.get("step_index") or 0)
        except (TypeError, ValueError):
            return
        result.steps = max(result.steps, index + 1)
        if step.get("step_type") == "tool":
            # Kept from its first update, so a step still running when the run is cut is audited too; a later
            # update of the same step replaces the earlier one.
            info = step.get("tool_info") if isinstance(step.get("tool_info"), dict) else {}
            entry = {"index": index, "name": str(info.get("name") or step.get("tool_name") or ""),
                     "parameters": info.get("parameters") if isinstance(info.get("parameters"), dict) else {},
                     "output": str(info.get("output") or ""),
                     # agy ends a refused or failed call in state ERROR with an error and no output: nothing was
                     # shown to the model. Any output at all, or a step cut while running, counts as shown.
                     "failed": (step.get("state") == "ERROR" and bool(info.get("error"))
                                and not info.get("output"))}
            result.tools = sorted([t for t in result.tools if t["index"] != index] + [entry],
                                  key=lambda t: t["index"])
        elif step.get("step_type") == "agent_response" and step.get("text_delta"):
            if result.timing.get("text_step") != index:
                result.timing["text_step"] = index
                result.partial_text = ""
            result.partial_text += str(step["text_delta"])
            result.timing.setdefault("first_text_s", round(elapsed, 1))
    elif kind == "result":
        r = body
        result.status = str(r.get("status") or "")
        result.response = str(r.get("response") or "")
        result.error = r.get("error") or r.get("message")
        result.usage = r.get("usage") if isinstance(r.get("usage"), dict) else {}
        result.conversation_id = r.get("conversation_id") or result.conversation_id
        actions = r.get("denied_actions") if isinstance(r.get("denied_actions"), list) else []
        result.denied = [str(a.get("action") or a.get("display_name")) if isinstance(a, dict) else str(a)
                         for a in actions if a]
        result.timing["agy_seconds"] = r.get("duration_seconds")


class _Signalled(Exception):
    """SIGTERM or SIGHUP reached the launcher while agy was running."""


def _on_signal(signum, frame) -> None:
    raise _Signalled(signal.Signals(signum).name)


def run(cmd: list[str], cwd: Path, *, idle_seconds: float, total_seconds: float) -> AgyResult:
    """Run agy and read its stream. The run is killed after `idle_seconds` without a line or `total_seconds` in all.

    Ctrl-C, SIGTERM and SIGHUP end agy and are returned as a stopped run, not raised, so that the caller still
    records the run and, for a write profile, lists what was changed before it was cut.
    """
    result = AgyResult()
    started = time.monotonic()
    try:
        proc = subprocess.Popen(cmd, cwd=str(cwd), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                                start_new_session=True)
    except OSError as e:
        raise AgyError(f"could not start {cmd[0]}: {e}") from e
    lines: queue.Queue = queue.Queue()
    errors: list[str] = []

    def pump() -> None:
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    def pump_errors() -> None:
        for line in proc.stderr:  # line by line, so what was written is kept even if the pipe never closes
            errors.append(line)

    readers = [threading.Thread(target=pump, daemon=True), threading.Thread(target=pump_errors, daemon=True)]
    for t in readers:
        t.start()
    last, longest = started, 0.0
    handlers: dict[int, object] = {}
    try:
        # agy runs in its own session, where a signal sent to this process does not reach it. A background launch
        # is ended with SIGTERM, which by default would end this process and leave agy running for its full limit.
        if threading.current_thread() is threading.main_thread():
            for signum in (signal.SIGTERM, signal.SIGHUP):
                handlers[signum] = signal.signal(signum, _on_signal)
        while not result.status:  # the result event is the end of the run, whatever still holds the pipes open
            now = time.monotonic()
            idle_left, total_left = idle_seconds - (now - last), total_seconds - (now - started)
            try:
                if min(idle_left, total_left) <= 0:
                    raise queue.Empty
                line = lines.get(timeout=min(idle_left, total_left))
            except queue.Empty:
                result.stopped = (f"time limit of {int(total_seconds)} s" if total_left <= idle_left
                                  else f"no step for {int(idle_seconds)} s")
                break
            if line is None:
                break
            now = time.monotonic()
            longest, last = max(longest, now - last), now
            result.timing.setdefault("first_line_s", round(now - started, 1))
            absorb(result, line, now - started)
        longest = max(longest, time.monotonic() - last)  # the silence that ended the run counts as a gap
        if not result.stopped:
            try:
                result.exit_code = proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if result.status:
                    result.timing["killed_after_result"] = True  # it had answered; only the process lingered
                else:
                    result.stopped = "agy did not exit after its stream ended"
    except KeyboardInterrupt:
        result.stopped = "interrupted"
    except _Signalled as e:
        result.stopped = f"signal {e}"
    finally:
        # Always, also on an error above: the whole group, since agy starts helpers of its own.
        for signum, previous in handlers.items():
            signal.signal(signum, previous)
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        for t, pipe in zip(readers, (proc.stdout, proc.stderr)):
            t.join(timeout=2)
            if not t.is_alive():  # closing a pipe its reader still holds would block
                pipe.close()
    result.stderr = "".join(errors)
    result.timing.pop("text_step", None)
    result.timing.update({"total_s": round(time.monotonic() - started, 1), "longest_gap_s": round(longest, 1)})
    return result


def outcome(result: AgyResult) -> tuple[str, str]:
    """-> (kind, status in words). Kinds: ok, permission, empty, error, stopped, no_result."""
    if result.stopped:
        return "stopped", f"stopped by the launcher ({result.stopped})"
    if not result.status:
        return "no_result", f"no result from agy (exit {result.exit_code})"
    if result.status != "SUCCESS":
        first = (result.stderr.strip().splitlines() or [""])[0]
        return "error", f"{result.status}: {result.error or first or 'no message'}"
    if result.exit_code not in (0, None):  # None: it answered and was then ended by the launcher
        return "error", f"agy exited {result.exit_code} after reporting SUCCESS"
    if not result.response.strip():
        if result.denied or "auto-denied" in result.stderr:
            return "permission", f"stopped at a permission request ({', '.join(result.denied) or 'tool not named'})"
        return "empty", "empty answer"
    return "ok", "ok"


# --- afterwards: what was read and run ----------------------------------------------------------------------------

def _read(p: Path) -> bytes | None:
    try:
        return p.read_bytes()
    except OSError:
        return None


def _entry(shown: str, p: Path, data: bytes) -> dict:
    text = data.decode("utf-8", "replace")
    return {"path": shown, "abs": str(p), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "lines": text.count("\n") + (0 if text.endswith("\n") or not text else 1)}


def _inside(p: Path, workspace: Path) -> str | None:
    try:
        return str(p.resolve().relative_to(workspace))
    except ValueError:
        return None


def audit(result: AgyResult, workspace: Path, addresses: list[str], *, cited: list[str] | None = None,
          exempt: set[str] | None = None) -> tuple[dict, list[cp.Finding]]:
    """-> (manifest, findings). The manifest lists the files read, the files cited and the commands run.

    The findings are denied addresses and secret patterns in what the machine showed the model: each tool's output
    and each file read. What the model wrote itself (its answer, its command lines) is not egress and is not
    scanned: the first live review quoted a made-up key in an example and was flagged for it. This cannot unsend
    anything; it makes a leak known at once. A file read by a shell command appears only as the command's output.
    """
    workspace = workspace.resolve()
    files: dict[str, dict] = {}
    commands: list[str] = []
    refused: list[str] = []
    texts: list[tuple[str, str]] = []
    cleared = set(exempt or ())  # labels that skip the secret patterns, never the addresses
    by_name: list[cp.Finding] = []
    for tool in result.tools:
        params = tool["parameters"]
        label = f"<step {tool['index']} {tool['name']}>"
        texts.append((label, tool["output"]))
        if tool["name"] in READ_TOOLS and params.get("Path"):
            p = Path(str(params["Path"]))
            p = (p if p.is_absolute() else workspace / p).resolve()  # agy runs in the workspace, wherever this does
            shown = _inside(p, workspace) or str(p)
            if shown in cleared:
                cleared.add(label)  # what the viewer showed of a file cleared with --allow is that same text
            if tool.get("failed"):  # refused by a deny rule, or missing: the model was shown nothing of it
                if shown not in refused:
                    refused.append(shown)
                continue
            if cp.FORBIDDEN_NAME.search(str(p).replace(os.sep, "/")):
                # No rule covered it (made during the run, or moved out from under its rule), and a key file need
                # not match any pattern.
                by_name.append(cp.Finding(shown, 0, "credentials file read"))
            data = _read(p)
            if data is not None and shown not in files:
                files[shown] = {**_entry(shown, p, data), "read": True}
                texts.append((shown, _text_for_scan(data)))  # as it stands now
        elif params.get("CommandLine"):
            commands.append(str(params["CommandLine"]))
    for raw in cited or []:  # files the answer cites, so its quotations can be checked even when read through `cat`
        p = Path(raw) if Path(raw).is_absolute() else workspace / raw
        if raw not in files and p.is_file() and _inside(p, workspace) is not None:
            data = _read(p.resolve())
            if data is not None:
                files[raw] = {**_entry(raw, p.resolve(), data), "read": False}
    findings = by_name + cp.scan(texts, addresses, exempt=cleared)
    manifest = {"cwd": str(workspace), "route": "agy", "conversation": result.conversation_id,
                "files": list(files.values()), "refused": refused, "commands": commands}
    return manifest, findings
