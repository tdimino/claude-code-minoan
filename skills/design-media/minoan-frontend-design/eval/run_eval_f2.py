#!/usr/bin/env python3
"""
Feature 2 Eval — Agent-based behavioral evaluation of frontend design skills.

Tests progressive disclosure: does an agent that can *choose* to load reference
files produce better output than one with everything force-fed or nothing available?

4-Arm Design:
  A: wetch-agent       — wetch skill, no references
  B: syncretic-agent   — syncretic-v3 skill, no references
  C: syncretic-refs    — syncretic-v3 skill + references/ directory available
  D: syncretic-force   — syncretic-v3 + all references concatenated inline

Requires: claude-agent-sdk, anthropic, playwright, scipy, httpx
Usage:
    uv run --with claude-agent-sdk,anthropic,playwright,scipy,httpx eval/run_eval_f2.py
    uv run --with claude-agent-sdk,anthropic,playwright,scipy,httpx eval/run_eval_f2.py --arms A,C --prompts 5
    uv run --with claude-agent-sdk,anthropic,playwright,scipy,httpx eval/run_eval_f2.py --pilot
"""

import argparse
import asyncio
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

EVAL_DIR = Path(__file__).parent
SKILLS_DIR = EVAL_DIR / "skills"
REFERENCES_DIR = EVAL_DIR.parent / "references"
RESULTS_BASE = EVAL_DIR / "results"

# Skill files
WETCH_SKILL = SKILLS_DIR / "wetch.md"
SYNCRETIC_SKILL = SKILLS_DIR / "syncretic-v3.md"

# Reference files for arm C workspace
REFERENCE_FILES = [
    "design-dials.md",
    "creative-arsenal.md",
    "eval-insights.md",
    "vercel-web-interface-guidelines.md",
    "design-system-checklist.md",
]

# Supplement separator (same as run_eval.py)
SUPPLEMENT_SEPARATOR = """

---

## Supplementary Engineering Reference

The following reference material is available for context. Prioritize the creative
direction above. Apply these standards proportionally—only where they serve the design.

---

"""

# Agent config
AGENT_MODEL = "claude-sonnet-4-6-20260220"
AGENT_MAX_TURNS = 15

# Reference pointer line added to arm C's skill
REFERENCE_POINTER = (
    "\n\nAdditional engineering and design references are available in the "
    "`references/` directory if the task would benefit from implementation "
    "standards, technique inspiration, or design calibration dials."
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ArmConfig:
    """Configuration for one experimental arm."""
    label: str
    skill_content: str
    has_references: bool = False  # Whether workspace includes references/
    description: str = ""


@dataclass
class TrajectoryMetrics:
    """Metrics extracted from an agent session trajectory."""
    references_read: int = 0
    which_references: list = field(default_factory=list)
    write_count: int = 0
    read_count: int = 0
    total_turns: int = 0
    tool_calls: list = field(default_factory=list)  # List of tool name strings
    duration_seconds: float = 0.0
    success: bool = False  # Whether output/index.html was produced


@dataclass
class F2RunDirs:
    """Paths for a Feature 2 eval run."""
    root: Path
    trajectories: Path
    generations: Path
    screenshots: Path
    results_file: Path
    report_file: Path

    @staticmethod
    def create(label: str) -> "F2RunDirs":
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dirname = f"f2_{label}_{timestamp}"
        root = RESULTS_BASE / dirname
        return F2RunDirs(
            root=root,
            trajectories=root / "trajectories",
            generations=root / "generations",
            screenshots=root / "screenshots",
            results_file=root / "results.json",
            report_file=root / "report.md",
        )

    def ensure_dirs(self):
        for d in [self.trajectories, self.generations, self.screenshots]:
            d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Workspace setup
# ---------------------------------------------------------------------------

def setup_workspace(workspace_dir: Path, include_references: bool = False):
    """Create an isolated workspace directory for an agent session."""
    workspace_dir.mkdir(parents=True, exist_ok=True)
    output_dir = workspace_dir / "output"
    output_dir.mkdir(exist_ok=True)

    if include_references:
        refs_dir = workspace_dir / "references"
        refs_dir.mkdir(exist_ok=True)
        for fname in REFERENCE_FILES:
            src = REFERENCES_DIR / fname
            if src.exists():
                shutil.copy2(src, refs_dir / fname)


def build_user_prompt(prompt_text: str) -> str:
    """Build the user prompt for agent sessions."""
    return f"""Build the following frontend interface and save the result as a complete, self-contained HTML file to output/index.html.

{prompt_text}

Requirements:
- Single HTML file with embedded CSS and JavaScript
- No external dependencies except CDN-hosted fonts and libraries
- Must render correctly at 1200x800 viewport
- Save the final file to output/index.html"""


# ---------------------------------------------------------------------------
# Arm configurations
# ---------------------------------------------------------------------------

def build_arms(selected_arms: list[str] | None = None) -> dict[str, ArmConfig]:
    """Build arm configurations. Load skill files lazily."""
    wetch_content = WETCH_SKILL.read_text()
    syncretic_content = SYNCRETIC_SKILL.read_text()

    # Build force-fed version: syncretic + all references concatenated
    ref_texts = []
    for fname in REFERENCE_FILES:
        fpath = REFERENCES_DIR / fname
        if fpath.exists():
            ref_texts.append(f"# {fname}\n\n{fpath.read_text()}")
    all_refs = "\n\n---\n\n".join(ref_texts)
    syncretic_force = syncretic_content + SUPPLEMENT_SEPARATOR + all_refs

    # Syncretic with reference pointer (for arm C)
    syncretic_refs = syncretic_content + REFERENCE_POINTER

    arms = {
        "A": ArmConfig(
            label="wetch-agent",
            skill_content=wetch_content,
            has_references=False,
            description="Wetch skill, no references",
        ),
        "B": ArmConfig(
            label="syncretic-agent",
            skill_content=syncretic_content,
            has_references=False,
            description="Syncretic-v3 skill, no references",
        ),
        "C": ArmConfig(
            label="syncretic-refs",
            skill_content=syncretic_refs,
            has_references=True,
            description="Syncretic-v3 skill + references/ directory",
        ),
        "D": ArmConfig(
            label="syncretic-force",
            skill_content=syncretic_force,
            has_references=False,
            description="Syncretic-v3 + all references concatenated",
        ),
    }

    if selected_arms:
        return {k: v for k, v in arms.items() if k in selected_arms}
    return arms


# ---------------------------------------------------------------------------
# Agent session runner
# ---------------------------------------------------------------------------

async def run_agent_session(
    arm: ArmConfig,
    prompt_text: str,
    workspace_dir: Path,
    prompt_id: str,
) -> tuple[TrajectoryMetrics, str | None]:
    """Run a single agent session and return trajectory metrics + HTML output."""
    from claude_agent_sdk import query, ClaudeAgentOptions

    setup_workspace(workspace_dir, include_references=arm.has_references)
    user_prompt = build_user_prompt(prompt_text)

    metrics = TrajectoryMetrics()
    start_time = time.time()

    try:
        async for message in query(
            prompt=user_prompt,
            options=ClaudeAgentOptions(
                system_prompt=arm.skill_content,
                allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
                permission_mode="bypassPermissions",
                cwd=str(workspace_dir),
                max_turns=AGENT_MAX_TURNS,
                model=AGENT_MODEL,
            ),
        ):
            # Extract tool calls from assistant messages
            if hasattr(message, "content") and isinstance(message.content, list):
                for block in message.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        tool_name = block.name if hasattr(block, "name") else str(block)
                        metrics.tool_calls.append(tool_name)
                        metrics.total_turns += 1

                        if tool_name == "Write":
                            metrics.write_count += 1
                        elif tool_name == "Read":
                            metrics.read_count += 1
                            # Check if reading a reference file
                            if hasattr(block, "input") and isinstance(block.input, dict):
                                file_path = block.input.get("file_path", "")
                                if "references/" in file_path:
                                    ref_name = Path(file_path).name
                                    metrics.references_read += 1
                                    if ref_name not in metrics.which_references:
                                        metrics.which_references.append(ref_name)

    except Exception as e:
        print(f"  Agent error ({arm.label}, {prompt_id}): {e}", file=sys.stderr)

    metrics.duration_seconds = time.time() - start_time

    # Check for output
    output_file = workspace_dir / "output" / "index.html"
    html_content = None
    if output_file.exists():
        html_content = output_file.read_text()
        metrics.success = True

    return metrics, html_content


# ---------------------------------------------------------------------------
# Screenshot capture (reuse from run_eval.py)
# ---------------------------------------------------------------------------

async def capture_screenshot(page, html: str, path: Path) -> str | None:
    """Render HTML and capture a 1200x800 screenshot. Returns base64 PNG."""
    import base64
    try:
        await page.set_viewport_size({"width": 1200, "height": 800})
        await page.set_content(html, wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(3500)  # Let animations settle
        png_bytes = await page.screenshot(type="png", full_page=False)
        path.write_bytes(png_bytes)
        return base64.b64encode(png_bytes).decode()
    except Exception as e:
        print(f"  Screenshot error: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Judge (reuse core logic from run_eval.py)
# ---------------------------------------------------------------------------

JUDGE_CRITERIA = """Evaluate both designs on these 5 criteria (1-5 scale each):

1. **Prompt Adherence** — Does the design faithfully address every element of the prompt?
2. **Aesthetic Fit** — Does the visual style match the content's purpose and audience?
3. **Visual Polish & Coherence** — Is the design refined, consistent, and cohesive?
4. **UX & Usability** — Is the interface intuitive, navigable, and well-structured?
5. **Creative Distinction** — Does the design feel genuinely distinctive rather than generic?

For each criterion, give Design A and Design B a score from 1 to 5.
Then declare an overall winner: the design with the higher total score.

Respond in this exact JSON format:
{
  "criteria": {
    "prompt_adherence": {"a": <score>, "b": <score>},
    "aesthetic_fit": {"a": <score>, "b": <score>},
    "visual_polish": {"a": <score>, "b": <score>},
    "ux_usability": {"a": <score>, "b": <score>},
    "creative_distinction": {"a": <score>, "b": <score>}
  },
  "winner": "<A or B or TIE>",
  "reasoning": "<2-3 sentence explanation>"
}"""


async def judge_pair(
    provider,
    judge_model: str,
    prompt_text: str,
    screenshot_a_b64: str,
    screenshot_b_b64: str,
    html_a: str,
    html_b: str,
) -> dict | None:
    """Run blind A/B judgment on a pair of designs."""
    import httpx

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": f"**Design prompt:** {prompt_text}\n\n{JUDGE_CRITERIA}"},
            {"type": "text", "text": "## Design A"},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": screenshot_a_b64
            }},
            {"type": "text", "text": f"### HTML Source A\n```html\n{html_a[:8000]}\n```"},
            {"type": "text", "text": "## Design B"},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/png", "data": screenshot_b_b64
            }},
            {"type": "text", "text": f"### HTML Source B\n```html\n{html_b[:8000]}\n```"},
        ],
    }]

    try:
        content, usage = await provider.create_message(
            model=judge_model,
            system="You are an expert UI/UX judge evaluating frontend designs in a blind A/B test.",
            messages=messages,
            max_tokens=2048,
        )
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"  Judge error: {e}", file=sys.stderr)

    return None


# ---------------------------------------------------------------------------
# Provider (same as run_eval.py)
# ---------------------------------------------------------------------------

class OpenRouterProvider:
    def __init__(self, api_key: str):
        import httpx
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=300)

    async def create_message(self, model, system, messages, max_tokens):
        # Map model names
        model_map = {
            "claude-opus-4-6-20260220": "anthropic/claude-opus-4-6-20260220",
            "claude-sonnet-4-6-20260220": "anthropic/claude-sonnet-4-6-20260220",
        }
        or_model = model_map.get(model, f"anthropic/{model}")

        # Convert messages
        or_messages = [{"role": "system", "content": system}] if system else []
        for msg in messages:
            if isinstance(msg["content"], str):
                or_messages.append(msg)
            elif isinstance(msg["content"], list):
                converted = []
                for block in msg["content"]:
                    if block["type"] == "text":
                        converted.append({"type": "text", "text": block["text"]})
                    elif block["type"] == "image":
                        media_type = block["source"]["media_type"]
                        data = block["source"]["data"]
                        converted.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{data}"},
                        })
                or_messages.append({"role": msg["role"], "content": converted})

        response = await self.client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": or_model, "messages": or_messages, "max_tokens": max_tokens},
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
        usage = data.get("usage", {})
        return content, {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

async def run_f2_pipeline(args):
    """Main Feature 2 eval pipeline."""
    # Load env
    env_path = Path("~/.config/env/global.env").expanduser()
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

    # Parse arms
    selected_arms = [a.strip().upper() for a in args.arms.split(",")] if args.arms else None
    if args.pilot:
        selected_arms = selected_arms or ["A", "B", "C"]  # Skip D for pilot

    arms = build_arms(selected_arms)
    print(f"Arms: {', '.join(f'{k}={v.label}' for k, v in arms.items())}")

    # Load prompts
    if args.prompts_file:
        with open(args.prompts_file) as f:
            prompts = json.load(f)
    else:
        with open(EVAL_DIR / "prompts.json") as f:
            all_prompts = json.load(f)
        if args.pilot:
            prompts = all_prompts[:15]  # Pilot: first 15
        elif args.prompts:
            prompts = all_prompts[:args.prompts]
        else:
            prompts = all_prompts

    print(f"Prompts: {len(prompts)}")
    print(f"Total sessions: {len(prompts) * len(arms)}")

    # Create run directory
    arm_labels = "+".join(sorted(arms.keys()))
    run_dirs = F2RunDirs.create(f"{arm_labels}_{len(prompts)}p")
    run_dirs.ensure_dirs()
    print(f"Results: {run_dirs.root}")

    # Judge provider
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_MANAGEMENT_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    judge_provider = OpenRouterProvider(api_key)
    judge_model = args.judge_model

    # ---------------------------------------------------------------------------
    # Phase 1: Agent sessions
    # ---------------------------------------------------------------------------
    print("\n=== Phase 1: Agent Sessions ===")
    results = []
    from playwright.async_api import async_playwright

    for i, prompt_entry in enumerate(prompts):
        # Support both structured {id, category, prompt} and plain string formats
        if isinstance(prompt_entry, dict):
            prompt_text = prompt_entry["prompt"]
            prompt_id = prompt_entry.get("id", f"p{i+1:02d}")
            prompt_category = prompt_entry.get("category", "unknown")
        else:
            prompt_text = prompt_entry
            prompt_id = f"p{i+1:02d}"
            prompt_category = "unknown"
        print(f"\n--- Prompt {i+1}/{len(prompts)} [{prompt_category}]: {prompt_text[:60]}... ---")

        arm_outputs = {}  # arm_key -> {"metrics": ..., "html": ..., "b64": ...}

        for arm_key, arm in arms.items():
            workspace = run_dirs.root / "workspaces" / f"{prompt_id}_{arm.label}"
            print(f"  [{arm_key}] {arm.label}...", end=" ", flush=True)

            metrics, html = await run_agent_session(
                arm=arm,
                prompt_text=prompt_text,
                workspace_dir=workspace,
                prompt_id=prompt_id,
            )

            # Save trajectory
            traj_data = {
                "prompt_id": prompt_id,
                "arm": arm_key,
                "label": arm.label,
                "prompt": prompt_text,
                "category": prompt_category,
                "metrics": {
                    "references_read": metrics.references_read,
                    "which_references": metrics.which_references,
                    "write_count": metrics.write_count,
                    "read_count": metrics.read_count,
                    "total_turns": metrics.total_turns,
                    "tool_calls": metrics.tool_calls,
                    "duration_seconds": metrics.duration_seconds,
                    "success": metrics.success,
                },
            }
            traj_path = run_dirs.trajectories / f"{prompt_id}_{arm.label}.json"
            traj_path.write_text(json.dumps(traj_data, indent=2))

            # Save HTML
            if html:
                gen_path = run_dirs.generations / f"{prompt_id}_{arm.label}.html"
                gen_path.write_text(html)

            status = "OK" if metrics.success else "FAIL"
            refs = f" refs={metrics.references_read}" if arm.has_references else ""
            print(f"{status} ({metrics.total_turns} turns, {metrics.duration_seconds:.1f}s{refs})")

            arm_outputs[arm_key] = {"metrics": metrics, "html": html, "b64": None}

        # ---------------------------------------------------------------------------
        # Phase 2: Screenshots
        # ---------------------------------------------------------------------------
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            for arm_key, data in arm_outputs.items():
                if data["html"]:
                    ss_path = run_dirs.screenshots / f"{prompt_id}_{arms[arm_key].label}.png"
                    data["b64"] = await capture_screenshot(page, data["html"], ss_path)

            await browser.close()

        # ---------------------------------------------------------------------------
        # Phase 3: Pairwise judging (C vs A as primary comparison)
        # ---------------------------------------------------------------------------
        comparisons = []
        if "A" in arm_outputs and "C" in arm_outputs:
            comparisons.append(("C", "A", "syncretic-refs vs wetch"))
        if "B" in arm_outputs and "C" in arm_outputs:
            comparisons.append(("C", "B", "syncretic-refs vs syncretic-agent"))
        if "B" in arm_outputs and "A" in arm_outputs:
            comparisons.append(("B", "A", "syncretic-agent vs wetch"))
        if "C" in arm_outputs and "D" in arm_outputs:
            comparisons.append(("C", "D", "syncretic-refs vs syncretic-force"))

        prompt_result = {
            "prompt_id": prompt_id,
            "prompt": prompt_text,
            "category": prompt_category,
            "arms": {},
            "comparisons": [],
        }

        for arm_key, data in arm_outputs.items():
            m = data["metrics"]
            prompt_result["arms"][arm_key] = {
                "label": arms[arm_key].label,
                "success": m.success,
                "references_read": m.references_read,
                "which_references": m.which_references,
                "total_turns": m.total_turns,
                "duration_seconds": m.duration_seconds,
            }

        for challenger, baseline, desc in comparisons:
            c_data = arm_outputs.get(challenger, {})
            b_data = arm_outputs.get(baseline, {})
            c_b64 = c_data.get("b64") if c_data else None
            b_b64 = b_data.get("b64") if b_data else None
            c_html = c_data.get("html") if c_data else None
            b_html = b_data.get("html") if b_data else None

            if not (c_b64 and b_b64 and c_html and b_html):
                prompt_result["comparisons"].append({
                    "challenger": challenger,
                    "baseline": baseline,
                    "description": desc,
                    "winner": "error",
                    "error": "Missing screenshot or HTML",
                })
                continue

            # Randomize A/B assignment
            import random
            if random.random() < 0.5:
                judge_a_b64, judge_b_b64 = c_b64, b_b64
                judge_a_html, judge_b_html = c_html, b_html
                challenger_is_a = True
            else:
                judge_a_b64, judge_b_b64 = b_b64, c_b64
                judge_a_html, judge_b_html = b_html, c_html
                challenger_is_a = False

            print(f"  Judging: {desc}...", end=" ", flush=True)
            verdict = await judge_pair(
                provider=judge_provider,
                judge_model=judge_model,
                prompt_text=prompt_text,
                screenshot_a_b64=judge_a_b64,
                screenshot_b_b64=judge_b_b64,
                html_a=judge_a_html,
                html_b=judge_b_html,
            )

            if verdict:
                raw_winner = verdict.get("winner", "error")
                if raw_winner == "A":
                    actual_winner = challenger if challenger_is_a else baseline
                elif raw_winner == "B":
                    actual_winner = baseline if challenger_is_a else challenger
                else:
                    actual_winner = "TIE"

                prompt_result["comparisons"].append({
                    "challenger": challenger,
                    "baseline": baseline,
                    "description": desc,
                    "winner": actual_winner,
                    "verdict": verdict,
                    "challenger_is_a": challenger_is_a,
                })
                winner_label = arms[actual_winner].label if actual_winner in arms else actual_winner
                print(f"{winner_label}")
            else:
                prompt_result["comparisons"].append({
                    "challenger": challenger,
                    "baseline": baseline,
                    "description": desc,
                    "winner": "error",
                    "error": "Judge returned no verdict",
                })
                print("ERROR")

        results.append(prompt_result)

        # Save incremental results
        run_dirs.results_file.write_text(json.dumps(results, indent=2))

    # ---------------------------------------------------------------------------
    # Phase 4: Report
    # ---------------------------------------------------------------------------
    print("\n=== Generating Report ===")
    report = generate_f2_report(results, arms, len(prompts))
    run_dirs.report_file.write_text(report)
    print(f"Report: {run_dirs.report_file}")
    print("\nDone.")


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_f2_report(results: list, arms: dict, num_prompts: int) -> str:
    """Generate Feature 2 eval report with trajectory analysis."""
    from scipy.stats import binomtest

    lines = [
        "# Feature 2 Eval Report — Agent-Based Behavioral Evaluation",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Agent Model**: {AGENT_MODEL}",
        f"**Max Turns**: {AGENT_MAX_TURNS}",
        f"**Prompts**: {num_prompts}",
        f"**Arms**: {', '.join(f'{k}={v.label}' for k, v in arms.items())}",
        "",
    ]

    # Aggregate comparison stats
    comparison_stats = {}  # desc -> {challenger_wins, baseline_wins, ties, errors}
    for result in results:
        for comp in result.get("comparisons", []):
            desc = comp["description"]
            if desc not in comparison_stats:
                comparison_stats[desc] = {"challenger_wins": 0, "baseline_wins": 0, "ties": 0, "errors": 0, "challenger": comp["challenger"], "baseline": comp["baseline"]}
            winner = comp["winner"]
            if winner == comp["challenger"]:
                comparison_stats[desc]["challenger_wins"] += 1
            elif winner == comp["baseline"]:
                comparison_stats[desc]["baseline_wins"] += 1
            elif winner == "TIE":
                comparison_stats[desc]["ties"] += 1
            else:
                comparison_stats[desc]["errors"] += 1

    # Win rates table
    lines.extend([
        "## Pairwise Comparisons",
        "",
        "| Comparison | Challenger Wins | Baseline Wins | Ties | Errors | Challenger Win Rate | p-value |",
        "|------------|:-:|:-:|:-:|:-:|:-:|:-:|",
    ])
    for desc, stats in comparison_stats.items():
        decisive = stats["challenger_wins"] + stats["baseline_wins"]
        if decisive > 0:
            win_rate = stats["challenger_wins"] / decisive * 100
            p_val = binomtest(stats["challenger_wins"], decisive, 0.5, alternative="greater").pvalue
        else:
            win_rate = 0
            p_val = 1.0
        lines.append(
            f"| {desc} | {stats['challenger_wins']} | {stats['baseline_wins']} | {stats['ties']} | {stats['errors']} | {win_rate:.1f}% | {p_val:.4f} |"
        )
    lines.append("")

    # Trajectory analysis (arm C only)
    if "C" in arms:
        lines.extend([
            "## Trajectory Analysis (Arm C: syncretic-refs)",
            "",
        ])

        ref_reads = []
        ref_files_used = {}
        durations = []
        turns = []
        successes = 0
        total = 0

        for result in results:
            arm_data = result.get("arms", {}).get("C")
            if arm_data:
                total += 1
                if arm_data["success"]:
                    successes += 1
                ref_reads.append(arm_data["references_read"])
                durations.append(arm_data["duration_seconds"])
                turns.append(arm_data["total_turns"])
                for ref in arm_data.get("which_references", []):
                    ref_files_used[ref] = ref_files_used.get(ref, 0) + 1

        if total > 0:
            lines.extend([
                f"- **Success rate**: {successes}/{total} ({successes/total*100:.0f}%)",
                f"- **Avg references read**: {sum(ref_reads)/len(ref_reads):.1f}",
                f"- **Sessions reading ≥1 reference**: {sum(1 for r in ref_reads if r > 0)}/{total}",
                f"- **Avg turns**: {sum(turns)/len(turns):.1f}",
                f"- **Avg duration**: {sum(durations)/len(durations):.0f}s",
                "",
            ])

            if ref_files_used:
                lines.extend([
                    "### Reference File Usage",
                    "",
                    "| File | Times Read |",
                    "|------|:-:|",
                ])
                for fname, count in sorted(ref_files_used.items(), key=lambda x: -x[1]):
                    lines.append(f"| {fname} | {count} |")
                lines.append("")

    # Per-category breakdown
    categories = {}
    for result in results:
        cat = result.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {}
        for comp in result.get("comparisons", []):
            desc = comp["description"]
            if desc not in categories[cat]:
                categories[cat][desc] = {"challenger_wins": 0, "baseline_wins": 0}
            winner = comp["winner"]
            if winner == comp["challenger"]:
                categories[cat][desc]["challenger_wins"] += 1
            elif winner == comp["baseline"]:
                categories[cat][desc]["baseline_wins"] += 1

    if len(categories) > 1:  # Only show if multiple categories
        lines.extend([
            "## Per-Category Breakdown",
            "",
        ])
        for cat in sorted(categories.keys()):
            lines.append(f"### {cat.title()}")
            lines.append("")
            lines.append("| Comparison | Challenger Wins | Baseline Wins | Win Rate |")
            lines.append("|------------|:-:|:-:|:-:|")
            for desc, stats in categories[cat].items():
                decisive = stats["challenger_wins"] + stats["baseline_wins"]
                wr = stats["challenger_wins"] / decisive * 100 if decisive > 0 else 0
                lines.append(f"| {desc} | {stats['challenger_wins']} | {stats['baseline_wins']} | {wr:.0f}% |")
            lines.append("")

    # Per-prompt results
    lines.extend([
        "## Per-Prompt Results",
        "",
        "| # | Prompt | " + " | ".join(f"Arm {k}" for k in sorted(arms.keys())) + " | Comparisons |",
        "|---|--------|" + "|".join(":-:" for _ in arms) + "|-------------|",
    ])

    for result in results:
        pid = result["prompt_id"]
        prompt_short = result["prompt"][:50] + "..."
        arm_cells = []
        for arm_key in sorted(arms.keys()):
            arm_data = result.get("arms", {}).get(arm_key)
            if arm_data:
                status = "OK" if arm_data["success"] else "FAIL"
                refs = f" r={arm_data['references_read']}" if arm_data.get("references_read") else ""
                arm_cells.append(f"{status}{refs}")
            else:
                arm_cells.append("-")

        comp_parts = []
        for comp in result.get("comparisons", []):
            winner = comp["winner"]
            if winner in arms:
                comp_parts.append(f"{comp['description']}: **{arms[winner].label}**")
            else:
                comp_parts.append(f"{comp['description']}: {winner}")
        comp_str = "; ".join(comp_parts) if comp_parts else "-"

        lines.append(f"| {pid} | {prompt_short} | " + " | ".join(arm_cells) + f" | {comp_str} |")

    lines.extend([
        "",
        "## Methodology",
        "",
        "- **Agent sessions**: Each arm runs a Claude Agent SDK session with the skill as system prompt.",
        "- **Progressive disclosure**: Arm C includes reference files in the workspace; the agent chooses what to read.",
        "- **Blind judging**: Pairwise A/B comparison with randomized assignment, same 5 criteria as Feature 1.",
        "- **Trajectory capture**: Tool calls logged to measure reference utilization behavior.",
        "",
        "---",
        f"*Generated by run_eval_f2.py on {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Feature 2 Eval — Agent-based behavioral evaluation")
    parser.add_argument("--prompts", type=int, default=0, help="Number of prompts (0 = all)")
    parser.add_argument("--prompts-file", type=str, default=None, help="Custom prompts JSON")
    parser.add_argument("--arms", type=str, default=None, help="Comma-separated arms to run (e.g., A,C)")
    parser.add_argument("--pilot", action="store_true", help="Pilot mode: arms A,B,C × 15 prompts")
    parser.add_argument("--judge-model", default="claude-opus-4-6-20260220", help="Judge model")
    args = parser.parse_args()

    asyncio.run(run_f2_pipeline(args))


if __name__ == "__main__":
    main()
