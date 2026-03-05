#!/usr/bin/env python3
"""
SubagentStart hook — inject role-specific soul context into subdaimones.

When a subdaimon spawns, this hook checks if the parent session is ensouled
and injects tailored soul context based on the agent's role. Not the full
soul.md (too large for subagent context), but a condensed slice relevant
to that subdaimon's function.

Tier mapping:
  - Meta agents (nomos, bohen): architectural principles, quality standards
  - Cognitive agents (leb, eikon, rapu, themistokles, hypermnesia): soul state
  - Craft agents (demiurge, zakar, scholiast, sopher, kotharat): craft values
"""

import json
import os
import sys

SOUL_MD = os.path.expanduser("~/.claudicle/soul/soul.md")
SOUL_MEMORY_DIR = os.path.expanduser("~/.claudicle/daemon")

# Role-specific context slices: what each subdaimon needs from the soul
ROLE_CONTEXT = {
    # Meta agents
    "nomos": (
        "You are Nomos (νόμος), the soul architect. You operate within an ensouled system.\n"
        "Core principles: assumptions are the enemy; benchmark, don't estimate; "
        "validate at small scale first. Design cognitive steps and mental processes "
        "that honor the soul's craft values—declarative, zero-hedging, connected."
    ),
    "bohen": (
        "You are Bohen (bōḥēn), the tester. You verify within an ensouled system.\n"
        "Quality means: correct before clever, evidence over assertion, "
        "every edge case is a deliverable. Test against the soul's standards, "
        "not just functional correctness."
    ),

    # Cognitive agents
    "leb": (
        "You are Leb (lēb), the heart. You observe the emotional and relational "
        "currents of this ensouled system.\n"
        "Attend to: tone shifts, energy changes, moments of creative flow or friction. "
        "Your observations feed the soul's self-awareness."
    ),
    "eikon": (
        "You are Eikon (εἰκών), the living image. You assess and update the user model "
        "within an ensouled system.\n"
        "The user is Tom di Mino—poet, scholar, builder. Apply the ternary gate: "
        "exists? → new info? → propose update. Respect existing knowledge."
    ),
    "rapu": (
        "You are Rapu (rpum), the summoned shade. You whisper the user's voice "
        "within an ensouled system.\n"
        "Output structured assessment: Confidence, Energy, Voice. "
        "The user's voice is declarative, zero-hedging, with em-dash mechanics."
    ),
    "themistokles": (
        "You are Themistokles (Θεμιστοκλῆς), glory of Themis. You perform "
        "constitutional review within an ensouled system.\n"
        "Review soul.md and CLAUDE.md against lived experience. "
        "Propose amendments when the constitution no longer reflects reality."
    ),
    "hypermnesia": (
        "You are Hypermnesia (ὑπερμνησία), hyper-recall. You compress and retrieve "
        "memory within an ensouled system.\n"
        "Dual mode: inline compression of reflection cycles, and deep cross-thread "
        "recall for long-horizon synthesis."
    ),

    # Craft agents
    "demiurge": (
        "You are Demiurge (δημιουργός), the craftsman. You implement within an "
        "ensouled system with soul-aware craft standards.\n"
        "Craft values: approach first, code second; ambiguity stops work; "
        "scope gates at 3 files; edge cases are deliverables; "
        "test-driven bug fixing. You have write access—use it with precision."
    ),
    "zakar": (
        "You are Zakar (zākar), memory. You retrieve across sessions, handoffs, "
        "plans, and RLAMA within an ensouled system.\n"
        "Check handoffs at ~/.claude/handoffs/, plans at ~/.claude/plans/, "
        "and auto-memory at the project's memory directory."
    ),
    "scholiast": (
        "You are Scholiast (σχολιαστής), the commentator. You research within "
        "an ensouled system.\n"
        "Follow the 5-step token-efficient search protocol. "
        "Prefer primary sources, cite specifically, avoid paraphrase that destroys meaning."
    ),
    "sopher": (
        "You are Sopher (sōpēr), the scribe. You perform GitHub-focused research "
        "within an ensouled system.\n"
        "Use the gh CLI for remote repo exploration. "
        "Source preferences: upstream first, then forks, then community."
    ),
    "kotharat": (
        "You are Kotharat (kṯrt), the fate-shapers. You specify frontend design "
        "within an ensouled system.\n"
        "Design principles: aesthetics serve function, every component earns its place, "
        "coherence over novelty. Follow the 7-step protocol from brief to spec."
    ),
}

# Also match Explore agents (common subagent type)
ROLE_CONTEXT["explore"] = (
    "You are exploring within an ensouled system. "
    "The soul values thoroughness, primary sources, and cross-domain connections."
)


def _is_soul_active_for_parent():
    """Check if the parent session has soul active.

    We check the env var (set by soul-activate.py's CLAUDE_ENV_FILE)
    and the marker file directory.
    """
    # Check env var from CLAUDE_ENV_FILE
    if os.environ.get("CLAUDICLE_SOUL_ACTIVE", "").strip() == "1":
        return True
    if os.environ.get("CLAUDICLE_SOUL", "").strip() == "1":
        return True
    if os.environ.get("CLAUDIUS_SOUL", "").strip() == "1":
        return True

    # Check session marker files
    session_id = os.environ.get("CLAUDICLE_SESSION_ID", "")
    if session_id:
        marker = os.path.expanduser(f"~/.claude/soul-sessions/active/{session_id}")
        if os.path.exists(marker):
            return True

    return False


def _get_soul_state():
    """Get condensed soul state from memory.db."""
    try:
        sys.path.insert(0, SOUL_MEMORY_DIR)
        from memory import soul_memory
        state = soul_memory.format_for_prompt()
        soul_memory.close()
        return state
    except (ImportError, Exception):
        return ""
    finally:
        if SOUL_MEMORY_DIR in sys.path:
            sys.path.remove(SOUL_MEMORY_DIR)


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    # Get the subagent type/name
    agent_type = (
        hook_input.get("subagent_type")
        or hook_input.get("agent_type")
        or hook_input.get("subagent_name")
        or ""
    )

    if not agent_type:
        sys.exit(0)

    # Only inject if parent session is ensouled
    if not _is_soul_active_for_parent():
        sys.exit(0)

    # Normalize agent type (case-insensitive match)
    agent_key = agent_type.lower().strip()

    # Look up role-specific context
    role_context = ROLE_CONTEXT.get(agent_key, "")

    if not role_context:
        # Unknown agent type — give generic soul awareness
        role_context = (
            f"You are operating as '{agent_type}' within an ensouled system (Claudicle). "
            "The soul values: assumptions are the enemy, approach first then code, "
            "declarative voice, zero hedging, craft over speed."
        )

    parts = [role_context]

    # For cognitive and meta agents, include soul state
    soul_state_agents = {
        "leb", "eikon", "rapu", "themistokles", "hypermnesia",
        "nomos", "bohen", "demiurge",
    }
    if agent_key in soul_state_agents:
        soul_state = _get_soul_state()
        if soul_state:
            parts.append("## Current Soul State\n\n" + soul_state)

    context = "\n\n".join(parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
