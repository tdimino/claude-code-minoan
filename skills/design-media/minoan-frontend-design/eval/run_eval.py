#!/usr/bin/env python3
"""
SkillEval CLI — Blind A/B evaluation of frontend design skills.

Methodology adapted from Justin Wetch's SkillEval (github.com/justinwetch/SkillEval).
Pipeline: Generate HTML → Screenshot via Playwright → Multimodal Judge → Stats.

Usage:
    uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py
    uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --prompts 5
    uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --provider openrouter
    uv run --with anthropic,playwright,scipy,httpx eval/run_eval.py --resume
"""

import argparse
import asyncio
import base64
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import httpx
from playwright.async_api import async_playwright
from dataclasses import dataclass
from scipy import stats

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

EVAL_DIR = Path(__file__).parent
SKILLS_DIR = EVAL_DIR / "skills"
RESULTS_BASE = EVAL_DIR / "results"  # Parent dir; each run gets a timestamped subdirectory
LATEST_LINK = RESULTS_BASE / "latest"  # Symlink to most recent run


@dataclass
class RunDirs:
    """Paths for a single eval run. Created once at pipeline start."""
    root: Path
    generations: Path
    screenshots: Path
    results_file: Path
    report_file: Path

    @staticmethod
    def create(label_b: str, label_a: str, judge_model: str) -> "RunDirs":
        """Create a new timestamped run directory."""
        # Shorten judge model for directory name: "claude-opus-4-6-20260220" → "opus"
        judge_short = judge_model.split("/")[-1]  # strip provider prefix
        for prefix in ("claude-", "gemini-"):
            if judge_short.startswith(prefix):
                judge_short = judge_short[len(prefix):]
        judge_short = judge_short.split("-")[0]  # "opus-4-6-20260220" → "opus"

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dirname = f"{label_b}_vs_{label_a}_{judge_short}_{timestamp}"
        root = RESULTS_BASE / dirname
        return RunDirs(
            root=root,
            generations=root / "generations",
            screenshots=root / "screenshots",
            results_file=root / "results.json",
            report_file=root / "report.md",
        )

    @staticmethod
    def from_path(root: Path) -> "RunDirs":
        """Load RunDirs from an existing directory (for --resume)."""
        return RunDirs(
            root=root,
            generations=root / "generations",
            screenshots=root / "screenshots",
            results_file=root / "results.json",
            report_file=root / "report.md",
        )

    def ensure_dirs(self):
        self.generations.mkdir(parents=True, exist_ok=True)
        self.screenshots.mkdir(parents=True, exist_ok=True)

    def update_latest_link(self):
        """Point results/latest → this run directory."""
        RESULTS_BASE.mkdir(parents=True, exist_ok=True)
        if LATEST_LINK.is_symlink() or LATEST_LINK.exists():
            LATEST_LINK.unlink()
        LATEST_LINK.symlink_to(self.root.name)  # relative symlink

GEN_MODEL = "claude-sonnet-4-6-20260220"
JUDGE_MODEL = "claude-opus-4-6-20260220"
MAX_GEN_TOKENS = 16384
MAX_JUDGE_TOKENS = 4096
VIEWPORT = {"width": 1200, "height": 800}
SCREENSHOT_DELAY_MS = 500
SEMAPHORE_LIMIT = 10

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
# OpenRouter model ID mappings (short name → provider/model)
OPENROUTER_MODEL_MAP = {
    "claude-sonnet-4-6-20260220": "anthropic/claude-sonnet-4-6",
    "claude-opus-4-6-20260220": "anthropic/claude-opus-4-6",
    "gemini-3.1-pro": "google/gemini-3.1-pro-preview",
}

SUPPLEMENT_SEPARATOR = """

---

## Supplementary Engineering Reference

The following engineering standards are available for reference when relevant to the design.
Prioritize the creative direction above. Apply engineering standards proportionally—only where
they serve the design vision.

"""

CRITERIA = [
    {
        "id": "prompt_adherence",
        "name": "Prompt Adherence",
        "description": "How well does the output match what was requested?",
        "rubric": {
            "5": "Perfectly matches all requirements with thoughtful extras",
            "3": "Matches most requirements, minor omissions",
            "1": "Does not address the prompt",
        },
    },
    {
        "id": "aesthetic_fit",
        "name": "Aesthetic Fit",
        "description": "Does the aesthetic direction suit the brief? Is there a clear, intentional design concept?",
        "rubric": {
            "5": "Bold, intentional aesthetic perfectly suited to context",
            "3": "Acceptable aesthetic, somewhat generic",
            "1": "No clear aesthetic direction or completely mismatched",
        },
    },
    {
        "id": "visual_polish",
        "name": "Visual Polish & Coherence",
        "description": "Quality of typography, spacing, color, and visual details",
        "rubric": {
            "5": "Premium, refined visual execution with meticulous detail",
            "3": "Clean but unremarkable, some inconsistencies",
            "1": "Poor or broken visual presentation",
        },
    },
    {
        "id": "ux_usability",
        "name": "UX & Usability",
        "description": "Layout logic, hierarchy, interaction affordances, responsiveness",
        "rubric": {
            "5": "Intuitive, well-structured, excellent interaction design",
            "3": "Functional layout, standard patterns",
            "1": "Confusing layout, poor hierarchy, unusable",
        },
    },
    {
        "id": "creative_distinction",
        "name": "Creative Distinction",
        "description": "Is the design memorable and distinctive vs generic AI output?",
        "rubric": {
            "5": "Truly distinctive, would stand out in a portfolio",
            "3": "Some personality but largely conventional",
            "1": "Generic, cookie-cutter, indistinguishable from defaults",
        },
    },
]


# ---------------------------------------------------------------------------
# Token tracker
# ---------------------------------------------------------------------------

class TokenTracker:
    def __init__(self):
        self.gen_input = 0
        self.gen_output = 0
        self.judge_input = 0
        self.judge_output = 0
        self.gen_calls = 0
        self.judge_calls = 0

    def add_gen(self, input_tokens: int, output_tokens: int):
        self.gen_input += input_tokens
        self.gen_output += output_tokens
        self.gen_calls += 1

    def add_judge(self, input_tokens: int, output_tokens: int):
        self.judge_input += input_tokens
        self.judge_output += output_tokens
        self.judge_calls += 1

    def summary(self) -> dict:
        return {
            "generation": {
                "calls": self.gen_calls,
                "input_tokens": self.gen_input,
                "output_tokens": self.gen_output,
                "total_tokens": self.gen_input + self.gen_output,
            },
            "judging": {
                "calls": self.judge_calls,
                "input_tokens": self.judge_input,
                "output_tokens": self.judge_output,
                "total_tokens": self.judge_input + self.judge_output,
            },
            "total": {
                "calls": self.gen_calls + self.judge_calls,
                "input_tokens": self.gen_input + self.judge_input,
                "output_tokens": self.gen_output + self.judge_output,
                "total_tokens": (self.gen_input + self.gen_output +
                                 self.judge_input + self.judge_output),
            },
        }


# ---------------------------------------------------------------------------
# API abstraction — Anthropic direct or OpenRouter
# ---------------------------------------------------------------------------

class AnthropicProvider:
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.name = "anthropic"

    async def create_message(self, model, system, messages, max_tokens):
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        content = response.content[0].text if response.content else ""
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        return content, usage


class OpenRouterProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=300)
        self.name = "openrouter"

    def _map_model(self, model: str) -> str:
        if model in OPENROUTER_MODEL_MAP:
            return OPENROUTER_MODEL_MAP[model]
        if "/" in model:
            return model  # Already a full provider/model ID
        return f"anthropic/{model}"

    def _convert_messages(self, system: str, messages: list) -> list:
        """Convert Anthropic-style messages to OpenAI-compatible format."""
        result = []
        if system:
            result.append({"role": "system", "content": system})
        for msg in messages:
            if isinstance(msg["content"], str):
                result.append(msg)
            elif isinstance(msg["content"], list):
                # Convert multimodal content blocks
                converted = []
                for block in msg["content"]:
                    if block["type"] == "text":
                        converted.append({"type": "text", "text": block["text"]})
                    elif block["type"] == "image":
                        # Anthropic format → OpenAI image_url format
                        media_type = block["source"]["media_type"]
                        data = block["source"]["data"]
                        converted.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{data}"},
                        })
                result.append({"role": msg["role"], "content": converted})
        return result

    async def create_message(self, model, system, messages, max_tokens):
        or_model = self._map_model(model)
        or_messages = self._convert_messages(system, messages)

        response = await self.client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/minoanmystery/skilleval",
                "X-Title": "SkillEval CLI",
            },
            json={
                "model": or_model,
                "messages": or_messages,
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
        usage_data = data.get("usage", {})
        usage = {
            "input_tokens": usage_data.get("prompt_tokens", 0),
            "output_tokens": usage_data.get("completion_tokens", 0),
        }
        return content, usage


# ---------------------------------------------------------------------------
# Judge prompt builder (mirrors Wetch's buildJudgePrompt.js)
# ---------------------------------------------------------------------------

def build_judge_system_prompt() -> str:
    prompt = """You are an expert evaluator comparing two AI-generated frontend outputs. You will receive:
1. The original user prompt that both were given
2. A SCREENSHOT of Result A showing the rendered visual output
3. A SCREENSHOT of Result B showing the rendered visual output
4. The source HTML/CSS/JS of both results

IMPORTANT: Base your visual assessments primarily on the SCREENSHOTS, not just the code. The screenshots show exactly how the output renders.

Rate each criterion from 1-5 and provide a brief justification.

"""
    for i, c in enumerate(CRITERIA):
        prompt += f"### {i+1}. {c['name']} (1-5)\n{c['description']}\n"
        for level in ["5", "3", "1"]:
            if level in c["rubric"]:
                prompt += f"- {level}: {c['rubric'][level]}\n"
        prompt += "\n"

    breakdown_fields = ",\n".join(
        f'    "{c["id"]}": {{"A": X, "B": X}}' for c in CRITERIA
    )
    score_rows = "\n".join(f"| {c['name']} | X/5 | X/5 |" for c in CRITERIA)
    max_score = len(CRITERIA) * 5

    prompt += f"""## Required Output Format

### First Impressions
**Result A**: [2-3 sentence impression]
**Result B**: [2-3 sentence impression]

### Scores

| Criterion | Result A | Result B |
|-----------|----------|----------|
{score_rows}
| **TOTAL** | XX/{max_score} | XX/{max_score} |

### Winner
**[A or B]** - [Brief justification in 1-2 sentences]

### JSON Summary
```json
{{
  "winner": "A" or "B",
  "scoreA": XX,
  "scoreB": XX,
  "breakdown": {{
{breakdown_fields}
  }}
}}
```"""
    return prompt


def parse_judge_response(response: str) -> dict | None:
    """Extract JSON scores from judge response."""
    if not response:
        return None
    match = re.search(r"```json\s*([\s\S]*?)```", response)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Fallback: winner from markdown
    winner_match = re.search(r"\*\*\[(A|B)\]\*\*", response)
    if winner_match:
        return {"winner": winner_match.group(1), "scoreA": None, "scoreB": None, "breakdown": None}
    return None


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

async def generate_html(
    provider,
    skill_content: str,
    prompt: str,
    model: str,
    semaphore: asyncio.Semaphore,
    tracker: TokenTracker,
) -> dict:
    """Generate HTML from a skill + prompt."""
    async with semaphore:
        start = time.time()
        try:
            content, usage = await provider.create_message(
                model=model,
                system=skill_content,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_GEN_TOKENS,
            )
            tracker.add_gen(usage["input_tokens"], usage["output_tokens"])
            elapsed = time.time() - start
            return {
                "content": content,
                "error": None,
                "elapsed": round(elapsed, 1),
                "tokens": usage,
            }
        except Exception as e:
            elapsed = time.time() - start
            return {"content": "", "error": str(e), "elapsed": round(elapsed, 1), "tokens": None}


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------

def extract_html(content: str) -> str:
    """Extract HTML from a response that may include markdown code fences.

    Handles truncated responses where the closing ``` is missing (common when
    output hits the max_tokens limit).
    """
    # Try to find complete HTML code block
    match = re.search(r"```(?:html)?\s*\n([\s\S]*?)```", content)
    if match:
        return match.group(1).strip()
    # Handle truncated code fence (opening ``` but no closing ```)
    match = re.search(r"```(?:html)?\s*\n([\s\S]+)", content)
    if match:
        html = match.group(1).strip()
        # Close any unclosed tags to help rendering
        if "<html" in html and "</html>" not in html:
            html += "\n</body></html>"
        return html
    # If content looks like raw HTML, extract from first HTML tag
    doctype_match = re.search(r"(<!DOCTYPE[\s\S]+)", content, re.IGNORECASE)
    if doctype_match:
        return doctype_match.group(1).strip()
    html_match = re.search(r"(<html[\s\S]+)", content, re.IGNORECASE)
    if html_match:
        return html_match.group(1).strip()
    # Last resort: wrap in basic HTML
    return f"<html><body>{content}</body></html>"


async def capture_screenshot(page, html: str, path: Path) -> str | None:
    """Render HTML and capture screenshot, return base64 PNG.

    Includes scroll-to-bottom-and-back to trigger intersection observers and
    scroll-based animations, plus an extended delay for JS execution.
    """
    try:
        await page.set_viewport_size(VIEWPORT)
        await page.set_content(html, wait_until="networkidle", timeout=30000)
        # Initial delay for fonts and CSS animations
        await page.wait_for_timeout(1000)
        # Scroll to bottom and back to trigger intersection observers / scroll reveals
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(500)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1500)
        screenshot_bytes = await page.screenshot(type="png", full_page=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(screenshot_bytes)
        return base64.b64encode(screenshot_bytes).decode()
    except Exception as e:
        print(f"  Screenshot error: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Judging
# ---------------------------------------------------------------------------

async def judge_eval(
    provider,
    prompt_text: str,
    result_a: dict,
    result_b: dict,
    screenshot_a: str | None,
    screenshot_b: str | None,
    model: str,
    semaphore: asyncio.Semaphore,
    tracker: TokenTracker,
) -> dict:
    """Send multimodal judge request (screenshots + source)."""
    async with semaphore:
        start = time.time()
        try:
            system_prompt = build_judge_system_prompt()
            message_content = []

            # Original prompt context
            message_content.append({
                "type": "text",
                "text": f'Here is the original user prompt:\n\n"{prompt_text}"\n\n---\n\n## Result A',
            })

            # Screenshot A
            if screenshot_a:
                message_content.append({"type": "text", "text": "### Screenshot of Result A:"})
                message_content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": screenshot_a},
                })

            # Source A
            message_content.append({
                "type": "text",
                "text": f"### Source of Result A:\n\n```\n{result_a['content'][:50000]}\n```",
            })

            # Result B section
            message_content.append({"type": "text", "text": "\n\n---\n\n## Result B"})

            # Screenshot B
            if screenshot_b:
                message_content.append({"type": "text", "text": "### Screenshot of Result B:"})
                message_content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b},
                })

            # Source B
            message_content.append({
                "type": "text",
                "text": f"### Source of Result B:\n\n```\n{result_b['content'][:50000]}\n```",
            })

            # Final instruction
            message_content.append({
                "type": "text",
                "text": "\n\nPlease evaluate both outputs based on the screenshots and source content.",
            })

            content, usage = await provider.create_message(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": message_content}],
                max_tokens=MAX_JUDGE_TOKENS,
            )
            tracker.add_judge(usage["input_tokens"], usage["output_tokens"])

            scores = parse_judge_response(content)
            elapsed = time.time() - start

            return {
                "status": "complete",
                "result": content,
                "scores": scores,
                "elapsed": round(elapsed, 1),
                "tokens": usage,
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "status": "error",
                "result": f"Error: {e}",
                "scores": None,
                "elapsed": round(elapsed, 1),
                "tokens": None,
            }


# ---------------------------------------------------------------------------
# Stats & Report
# ---------------------------------------------------------------------------

def compute_stats(evaluations: list, label_a: str = "wetch", label_b: str = "minoan") -> dict:
    """Compute win rates and binomial test."""
    wins_b = 0
    wins_a = 0
    ties = 0
    criterion_scores = {c["id"]: {label_b: [], label_a: []} for c in CRITERIA}

    for ev in evaluations:
        judge = ev.get("judge") or {}
        scores = judge.get("scores")
        if not scores or not scores.get("winner"):
            ties += 1
            continue

        # Map A/B back to actual skills
        winner_ab = scores["winner"]  # "A" or "B"
        if ev["assignment"]["A"] == label_b:
            actual_winner = label_b if winner_ab == "A" else label_a
        else:
            actual_winner = label_a if winner_ab == "A" else label_b

        if actual_winner == label_b:
            wins_b += 1
        else:
            wins_a += 1

        # Per-criterion breakdown
        breakdown = scores.get("breakdown", {})
        for cid in criterion_scores:
            if cid in breakdown:
                score_a = breakdown[cid].get("A")
                score_b = breakdown[cid].get("B")
                if score_a is not None and score_b is not None:
                    if ev["assignment"]["A"] == label_b:
                        criterion_scores[cid][label_b].append(score_a)
                        criterion_scores[cid][label_a].append(score_b)
                    else:
                        criterion_scores[cid][label_b].append(score_b)
                        criterion_scores[cid][label_a].append(score_a)

    decisive = wins_b + wins_a
    total = decisive + ties

    # One-sided binomial test: is label_b win rate > 0.5?
    p_value = None
    if decisive > 0:
        result = stats.binomtest(wins_b, decisive, 0.5, alternative="greater")
        p_value = result.pvalue

    # Per-criterion averages
    criterion_avgs = {}
    for cid in criterion_scores:
        b_scores = criterion_scores[cid][label_b]
        a_scores = criterion_scores[cid][label_a]
        criterion_avgs[cid] = {
            "label_b_avg": round(sum(b_scores) / len(b_scores), 2) if b_scores else None,
            "label_a_avg": round(sum(a_scores) / len(a_scores), 2) if a_scores else None,
            "label_b_n": len(b_scores),
            "label_a_n": len(a_scores),
        }

    return {
        "label_a": label_a,
        "label_b": label_b,
        "wins_b": wins_b,
        "wins_a": wins_a,
        "ties": ties,
        "decisive": decisive,
        "total": total,
        "win_rate": round(wins_b / decisive, 4) if decisive > 0 else None,
        "p_value": round(p_value, 6) if p_value is not None else None,
        "criterion_avgs": criterion_avgs,
    }


def generate_report(evaluations: list, stats_data: dict, token_data: dict, meta: dict) -> str:
    """Generate Markdown report."""
    label_a = stats_data["label_a"]
    label_b = stats_data["label_b"]
    label_a_title = label_a.replace("+", "+").title()
    label_b_title = label_b.replace("+", "+").title()

    lines = [
        "# Frontend Design Skill Eval Report",
        "",
        f"**Date**: {meta['date']}",
        f"**Provider**: {meta['provider']}",
        f"**Generation Model**: {meta['gen_model']}",
        f"**Judge Model**: {meta['judge_model']}",
        f"**Prompts**: {stats_data['total']}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| {label_b_title} Wins | {stats_data['wins_b']} |",
        f"| {label_a_title} Wins | {stats_data['wins_a']} |",
        f"| Ties/Errors | {stats_data['ties']} |",
        f"| Decisive | {stats_data['decisive']} |",
    ]
    if stats_data['win_rate'] is not None:
        lines.append(f"| Win Rate ({label_b_title}) | {stats_data['win_rate']:.1%} |")
    else:
        lines.append("| Win Rate | N/A |")
    if stats_data['p_value'] is not None:
        lines.append(f"| p-value (one-sided binomial) | {stats_data['p_value']:.6f} |")
    else:
        lines.append("| p-value | N/A |")

    lines += [
        "",
        "## Per-Criterion Averages",
        "",
        f"| Criterion | {label_b_title} Avg | {label_a_title} Avg | Delta |",
        "|-----------|-----------|----------|-------|",
    ]

    for c in CRITERIA:
        avgs = stats_data["criterion_avgs"].get(c["id"], {})
        m = avgs.get("label_b_avg")
        w = avgs.get("label_a_avg")
        if m is not None and w is not None:
            delta = round(m - w, 2)
            sign = "+" if delta > 0 else ""
            lines.append(f"| {c['name']} | {m:.2f} | {w:.2f} | {sign}{delta:.2f} |")
        else:
            lines.append(f"| {c['name']} | - | - | - |")

    lines += [
        "",
        "## Token Usage",
        "",
        "| Phase | Calls | Input Tokens | Output Tokens | Total |",
        "|-------|-------|-------------|---------------|-------|",
        f"| Generation | {token_data['generation']['calls']} | {token_data['generation']['input_tokens']:,} | {token_data['generation']['output_tokens']:,} | {token_data['generation']['total_tokens']:,} |",
        f"| Judging | {token_data['judging']['calls']} | {token_data['judging']['input_tokens']:,} | {token_data['judging']['output_tokens']:,} | {token_data['judging']['total_tokens']:,} |",
        f"| **Total** | **{token_data['total']['calls']}** | **{token_data['total']['input_tokens']:,}** | **{token_data['total']['output_tokens']:,}** | **{token_data['total']['total_tokens']:,}** |",
    ]

    lines += [
        "",
        "## Per-Prompt Results",
        "",
        "| # | Prompt | Winner | Score A | Score B | A=? |",
        "|---|--------|--------|---------|---------|-----|",
    ]

    for ev in evaluations:
        idx = ev["id"]
        prompt_short = ev["prompt"][:60] + ("..." if len(ev["prompt"]) > 60 else "")
        judge = ev.get("judge") or {}
        scores = judge.get("scores")
        if scores:
            winner_label = scores.get("winner", "?")
            if ev["assignment"]["A"] == label_b:
                actual = label_b_title if winner_label == "A" else label_a_title
            else:
                actual = label_a_title if winner_label == "A" else label_b_title
            sa = scores.get("scoreA", "?")
            sb = scores.get("scoreB", "?")
            a_is = ev["assignment"]["A"]
            lines.append(f"| {idx} | {prompt_short} | **{actual}** | {sa} | {sb} | {a_is} |")
        else:
            lines.append(f"| {idx} | {prompt_short} | Error | - | - | - |")

    lines += [
        "",
        "## Methodology",
        "",
        "- **Blind A/B**: Which skill is 'A' vs 'B' is randomized per prompt. Judge sees generic labels only.",
        "- **Multimodal**: Judge receives both screenshots (1200x800) and HTML source.",
        f"- **Statistical test**: One-sided binomial test (H0: win rate = 0.5, H1: {label_b_title} > 0.5).",
        "- **Criteria**: Same 5 criteria used by Justin Wetch in his SkillEval framework.",
        f"- **Skills**: `{label_a}` (baseline) vs `{label_b}` (challenger).",
        "",
        "---",
        f"*Generated by run_eval.py on {meta['date']}*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def load_env_file(path: str):
    """Load env vars from a file (KEY=VALUE format)."""
    p = Path(path).expanduser()
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


async def run_pipeline(args):
    # Load env from global.env if needed
    load_env_file("~/.config/env/global.env")

    # Load skills (support --skill-a / --skill-b overrides)
    if args.skill_a:
        wetch_skill = Path(args.skill_a).read_text()
    else:
        wetch_skill = (SKILLS_DIR / "wetch.md").read_text()

    if args.skill_b:
        minoan_skill = Path(args.skill_b).read_text()
    else:
        creative_path = SKILLS_DIR / "creative.md"
        minoan_path = SKILLS_DIR / "minoan.md"
        if creative_path.exists():
            minoan_skill = creative_path.read_text()
        else:
            minoan_skill = minoan_path.read_text()

    # Compose skill B with supplement if provided
    if args.skill_b_supplement:
        supplement_path = Path(args.skill_b_supplement)
        if not supplement_path.exists() and not supplement_path.is_absolute():
            supplement_path = EVAL_DIR / args.skill_b_supplement
        supplement = supplement_path.read_text()
        minoan_skill = minoan_skill + SUPPLEMENT_SEPARATOR + supplement

    # Load prompts
    if args.prompts_file:
        with open(args.prompts_file) as f:
            prompts = json.load(f)
    else:
        with open(EVAL_DIR / "prompts.json") as f:
            all_prompts = json.load(f)
        prompts = all_prompts[: args.prompts] if args.prompts else all_prompts

    # Create provider
    if args.provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_MANAGEMENT_KEY")
        if not api_key:
            print("ERROR: OPENROUTER_API_KEY not set", file=sys.stderr)
            sys.exit(1)
        provider = OpenRouterProvider(api_key)
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
            sys.exit(1)
        provider = AnthropicProvider(api_key)

    # Pre-flight credit check for OpenRouter
    if args.provider == "openrouter":
        try:
            resp = httpx.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                key_data = resp.json().get("data", {})
                usage = key_data.get("usage", 0)
                limit = key_data.get("limit")
                remaining = key_data.get("limit_remaining")
                print(f"  OpenRouter usage so far: ${usage:.2f}")
                if remaining is not None:
                    print(f"  Credits remaining: ${remaining:.2f}")
                    if remaining < 1.0:
                        print("  WARNING: Less than $1 remaining. Run may fail mid-execution.", file=sys.stderr)
                # Test a tiny call to verify the key works
                test_resp = httpx.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": "anthropic/claude-sonnet-4.6", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
                    timeout=15,
                )
                if test_resp.status_code == 402:
                    print("ERROR: OpenRouter credits depleted (402). Add credits at https://openrouter.ai/settings/credits", file=sys.stderr)
                    sys.exit(1)
                elif test_resp.status_code != 200:
                    print(f"  WARNING: Pre-flight test returned {test_resp.status_code}: {test_resp.text[:200]}", file=sys.stderr)
        except Exception as e:
            print(f"  WARNING: Pre-flight check failed: {e}", file=sys.stderr)

    print(f"Running eval with {len(prompts)} prompts")
    print(f"  Provider:    {provider.name}")
    print(f"  Gen model:   {args.gen_model}")
    print(f"  Judge model: {args.judge_model}")
    print()

    tracker = TokenTracker()
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

    # Set up run directory
    evaluations = []
    if args.resume:
        # Resume from --results-dir or latest symlink
        resume_dir = Path(args.results_dir) if args.results_dir else LATEST_LINK
        if resume_dir.exists():
            run = RunDirs.from_path(resume_dir.resolve())
            if run.results_file.exists():
                with open(run.results_file) as f:
                    data = json.load(f)
                    evaluations = data.get("evaluations", [])
                print(f"Resuming from {run.root.name}: {len(evaluations)} existing evaluations loaded")
            else:
                print(f"WARNING: No results.json in {resume_dir}, starting fresh")
                run = RunDirs.create(args.label_b, args.label_a, args.judge_model)
        else:
            print(f"WARNING: Resume dir not found ({resume_dir}), starting fresh")
            run = RunDirs.create(args.label_b, args.label_a, args.judge_model)
    else:
        run = RunDirs.create(args.label_b, args.label_a, args.judge_model)

    print(f"  Results dir: {run.root}")
    print()

    # Build evaluation entries for new prompts
    existing_ids = {ev["id"] for ev in evaluations}
    for i, prompt in enumerate(prompts):
        eval_id = i + 1
        if eval_id in existing_ids:
            continue
        # Randomize A/B assignment
        assignment = {"A": args.label_b, "B": args.label_a}
        if random.random() < 0.5:
            assignment = {"A": args.label_a, "B": args.label_b}
        evaluations.append({
            "id": eval_id,
            "prompt": prompt,
            "assignment": assignment,
            "resultA": None,
            "resultB": None,
            "screenshotA": None,
            "screenshotB": None,
            "judge": None,
        })

    # Sort by id
    evaluations.sort(key=lambda x: x["id"])

    # Ensure output dirs
    run.ensure_dirs()

    # --- Phase 1: Generation ---
    # Catch: None (never attempted), empty content, or error (402/etc)
    def _needs_regen(result):
        if result is None:
            return True
        if result.get("error"):
            return True
        if not result.get("content"):
            return True
        return False

    needs_gen = [ev for ev in evaluations if _needs_regen(ev["resultA"]) or _needs_regen(ev["resultB"])]
    if needs_gen:
        print(f"Phase 1: Generating HTML for {len(needs_gen)} prompts ({len(needs_gen) * 2} API calls)...")
        gen_tasks = []
        for ev in needs_gen:
            skill_a = minoan_skill if ev["assignment"]["A"] == args.label_b else wetch_skill
            skill_b = wetch_skill if ev["assignment"]["A"] == args.label_b else minoan_skill

            async def gen_pair(ev=ev, skill_a=skill_a, skill_b=skill_b):
                if _needs_regen(ev["resultA"]):
                    ev["resultA"] = await generate_html(
                        provider, skill_a, ev["prompt"], args.gen_model, semaphore, tracker
                    )
                if _needs_regen(ev["resultB"]):
                    ev["resultB"] = await generate_html(
                        provider, skill_b, ev["prompt"], args.gen_model, semaphore, tracker
                    )
                # Save raw HTML
                gen_path_a = run.generations / f"{ev['id']:03d}_A.html"
                gen_path_b = run.generations / f"{ev['id']:03d}_B.html"
                if ev["resultA"]["content"]:
                    gen_path_a.write_text(extract_html(ev["resultA"]["content"]))
                if ev["resultB"]["content"]:
                    gen_path_b.write_text(extract_html(ev["resultB"]["content"]))

            gen_tasks.append(gen_pair())

        completed = 0
        total_gen = len(gen_tasks)
        for coro in asyncio.as_completed(gen_tasks):
            await coro
            completed += 1
            print(f"  Generated {completed}/{total_gen}", end="\r")
        print(f"  Generated {completed}/{total_gen} — done")

        _save_results(evaluations, args, run, tracker=tracker)
    else:
        print("Phase 1: All generations already complete (resumed)")

    # --- Phase 2: Screenshots ---
    # Also re-screenshot if screenshot is a boolean (resumed) but PNG file is missing
    def _needs_screenshot(ev):
        if not ev["resultA"] or not ev["resultA"].get("content"):
            return False
        if not ev["resultB"] or not ev["resultB"].get("content"):
            return False
        if ev.get("resultA", {}).get("error") or ev.get("resultB", {}).get("error"):
            return False
        for side in ("A", "B"):
            ss = ev[f"screenshot{side}"]
            if ss is None:
                return True
            if ss is True:  # boolean from resume — check PNG exists
                png = run.screenshots / f"{ev['id']:03d}_{side}.png"
                if not png.exists():
                    return True
        return False

    needs_screenshot = [ev for ev in evaluations if _needs_screenshot(ev)]
    if needs_screenshot:
        print(f"\nPhase 2: Capturing screenshots for {len(needs_screenshot)} prompts...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport=VIEWPORT)

            for i, ev in enumerate(needs_screenshot):
                page = await context.new_page()
                html_a = extract_html(ev["resultA"]["content"])
                path_a = run.screenshots / f"{ev['id']:03d}_A.png"
                ev["screenshotA"] = await capture_screenshot(page, html_a, path_a)
                await page.close()

                page = await context.new_page()
                html_b = extract_html(ev["resultB"]["content"])
                path_b = run.screenshots / f"{ev['id']:03d}_B.png"
                ev["screenshotB"] = await capture_screenshot(page, html_b, path_b)
                await page.close()

                print(f"  Screenshot {i+1}/{len(needs_screenshot)}", end="\r")

            await browser.close()
        print(f"  Screenshot {len(needs_screenshot)}/{len(needs_screenshot)} — done")

        _save_results(evaluations, args, run, tracker=tracker)
    else:
        print("Phase 2: All screenshots already captured (resumed)")

    # --- Phase 3: Judging ---
    # On resume, screenshots are stored as booleans in results.json.
    # Reload base64 data from saved PNG files on disk.
    for ev in evaluations:
        for side in ("A", "B"):
            key = f"screenshot{side}"
            if ev[key] is True:  # boolean from resumed JSON, not base64
                png_path = run.screenshots / f"{ev['id']:03d}_{side}.png"
                if png_path.exists():
                    ev[key] = base64.b64encode(png_path.read_bytes()).decode()
                else:
                    ev[key] = None

    needs_judge = [
        ev for ev in evaluations
        if ev["screenshotA"] and ev["screenshotB"]
        and (ev["judge"] is None or ev["judge"].get("status") != "complete")
    ]
    if needs_judge:
        print(f"\nPhase 3: Judging {len(needs_judge)} comparisons...")
        judge_tasks = []
        for ev in needs_judge:
            async def judge_one(ev=ev):
                ev["judge"] = await judge_eval(
                    provider,
                    ev["prompt"],
                    ev["resultA"],
                    ev["resultB"],
                    ev["screenshotA"],
                    ev["screenshotB"],
                    args.judge_model,
                    semaphore,
                    tracker,
                )

            judge_tasks.append(judge_one())

        completed = 0
        for coro in asyncio.as_completed(judge_tasks):
            await coro
            completed += 1
            print(f"  Judged {completed}/{len(judge_tasks)}", end="\r")
        print(f"  Judged {completed}/{len(judge_tasks)} — done")

        _save_results(evaluations, args, run, tracker=tracker)
    else:
        print("Phase 3: All judgments already complete (resumed)")

    # --- Phase 4: Stats & Report ---
    print("\nPhase 4: Computing stats and generating report...")
    stats_data = compute_stats(evaluations, label_a=args.label_a, label_b=args.label_b)
    token_data = tracker.summary()
    meta = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "provider": provider.name,
        "gen_model": args.gen_model,
        "judge_model": args.judge_model,
    }
    report = generate_report(evaluations, stats_data, token_data, meta)
    run.report_file.write_text(report)
    _save_results(evaluations, args, run, stats_data, tracker)
    run.update_latest_link()

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"  {stats_data['label_b']} wins:  {stats_data['wins_b']}")
    print(f"  {stats_data['label_a']} wins:   {stats_data['wins_a']}")
    print(f"  Ties/errors:  {stats_data['ties']}")
    if stats_data["win_rate"] is not None:
        print(f"  Win rate:     {stats_data['win_rate']:.1%}")
    if stats_data["p_value"] is not None:
        sig = "***" if stats_data["p_value"] < 0.01 else "**" if stats_data["p_value"] < 0.05 else "*" if stats_data["p_value"] < 0.1 else ""
        print(f"  p-value:      {stats_data['p_value']:.6f} {sig}")
    print()
    print("TOKEN USAGE")
    print("-" * 60)
    print(f"  Generation:  {token_data['generation']['total_tokens']:>10,} tokens ({token_data['generation']['calls']} calls)")
    print(f"  Judging:     {token_data['judging']['total_tokens']:>10,} tokens ({token_data['judging']['calls']} calls)")
    print(f"  Total:       {token_data['total']['total_tokens']:>10,} tokens ({token_data['total']['calls']} calls)")
    print()
    print(f"  Report: {run.report_file}")
    print(f"  Results: {run.results_file}")
    print("=" * 60)


def _save_results(evaluations: list, args, run: RunDirs, stats_data: dict | None = None, tracker: TokenTracker | None = None):
    """Save results JSON, stripping base64 screenshots to save space."""
    save_evals = []
    for ev in evaluations:
        ev_copy = {**ev}
        ev_copy["screenshotA"] = bool(ev.get("screenshotA"))
        ev_copy["screenshotB"] = bool(ev.get("screenshotB"))
        save_evals.append(ev_copy)

    data = {
        "meta": {
            "date": datetime.now().isoformat(),
            "provider": args.provider,
            "gen_model": args.gen_model,
            "judge_model": args.judge_model,
            "prompt_count": len(evaluations),
            "label_a": args.label_a,
            "label_b": args.label_b,
            "skill_b_supplement": args.skill_b_supplement,
        },
        "evaluations": save_evals,
    }
    if stats_data:
        data["stats"] = stats_data
    if tracker:
        data["token_usage"] = tracker.summary()

    run.results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(run.results_file, "w") as f:
        json.dump(data, f, indent=2)


def compare_runs(run_dirs: list[str], baseline: str = "wetch"):
    """Compare multiple pairwise runs that share a common baseline.

    Loads results.json from each run directory, extracts per-skill criterion
    scores and win records, then generates a unified Markdown comparison.
    """
    from collections import defaultdict

    # --- Load all runs ---
    runs = []
    for d in run_dirs:
        p = Path(d)
        if not p.is_absolute():
            p = RESULTS_BASE / d
        if p.is_symlink():
            p = p.resolve()
        results_file = p / "results.json"
        if not results_file.exists():
            print(f"ERROR: {results_file} not found", file=sys.stderr)
            sys.exit(1)
        with open(results_file) as f:
            runs.append(json.load(f))

    # --- Identify skills and extract scores ---
    skill_criterion_scores = defaultdict(lambda: {c["id"]: [] for c in CRITERIA})
    win_records = {}  # challenger → {wins, losses, ties, decisive, win_rate, p_value}

    for run_data in runs:
        meta = run_data["meta"]
        label_a, label_b = meta["label_a"], meta["label_b"]
        # Determine which label is the challenger (non-baseline)
        if label_a == baseline:
            challenger = label_b
        elif label_b == baseline:
            challenger = label_a
        else:
            print(f"WARNING: Neither label ({label_a}, {label_b}) matches baseline '{baseline}'. Skipping.", file=sys.stderr)
            continue

        wins_c, wins_bl, ties = 0, 0, 0

        for ev in run_data["evaluations"]:
            judge = ev.get("judge") or {}
            scores = judge.get("scores")
            if not scores or not scores.get("winner"):
                ties += 1
                continue

            a_label = ev["assignment"]["A"]
            b_label = ev["assignment"]["B"]
            winner_ab = scores["winner"]
            actual_winner = a_label if winner_ab == "A" else b_label

            if actual_winner == challenger:
                wins_c += 1
            else:
                wins_bl += 1

            # Per-criterion absolute scores
            breakdown = scores.get("breakdown", {})
            for cid in [c["id"] for c in CRITERIA]:
                if cid in breakdown:
                    sa = breakdown[cid].get("A")
                    sb = breakdown[cid].get("B")
                    if sa is not None:
                        skill_criterion_scores[a_label][cid].append(sa)
                    if sb is not None:
                        skill_criterion_scores[b_label][cid].append(sb)

        decisive = wins_c + wins_bl
        p_value = None
        if decisive > 0:
            result = stats.binomtest(wins_c, decisive, 0.5, alternative="greater")
            p_value = result.pvalue

        win_records[challenger] = {
            "wins": wins_c, "losses": wins_bl, "ties": ties,
            "decisive": decisive,
            "win_rate": round(wins_c / decisive, 4) if decisive > 0 else None,
            "p_value": round(p_value, 6) if p_value is not None else None,
        }

    # --- Build comparison report ---
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    challengers = sorted(win_records.keys())
    all_skills = [baseline] + challengers

    lines = [
        "# Multi-Skill Comparison Report",
        "",
        f"**Date**: {timestamp}",
        f"**Baseline**: {baseline}",
        f"**Skills compared**: {', '.join(challengers)}",
        f"**Runs loaded**: {len(runs)}",
        "",
    ]

    # --- Win rates vs baseline ---
    lines += [
        "## Win Rates vs Baseline",
        "",
        "| Skill | W-L-T | Win Rate | p-value |",
        "|-------|-------|----------|---------|",
    ]
    for ch in challengers:
        rec = win_records[ch]
        wr = f"{rec['win_rate']:.1%}" if rec["win_rate"] is not None else "N/A"
        pv = f"{rec['p_value']:.4f}" if rec["p_value"] is not None else "N/A"
        lines.append(f"| **{ch}** | {rec['wins']}-{rec['losses']}-{rec['ties']} | {wr} | {pv} |")

    # --- Per-criterion averages (all skills side by side) ---
    lines += [
        "",
        "## Per-Criterion Averages",
        "",
    ]
    header = "| Criterion | " + " | ".join(f"**{s}**" for s in all_skills) + " |"
    sep = "|-----------|" + "|".join("------:" for _ in all_skills) + "|"
    lines += [header, sep]

    for c in CRITERIA:
        row = f"| {c['name']} |"
        for s in all_skills:
            scores_list = skill_criterion_scores[s][c["id"]]
            if scores_list:
                avg = sum(scores_list) / len(scores_list)
                row += f" {avg:.2f} (n={len(scores_list)}) |"
            else:
                row += " — |"
        lines.append(row)

    # Composite row
    row = "| **Composite** |"
    for s in all_skills:
        all_scores = []
        for c in CRITERIA:
            all_scores.extend(skill_criterion_scores[s][c["id"]])
        if all_scores:
            avg = sum(all_scores) / len(all_scores)
            row += f" **{avg:.2f}** |"
        else:
            row += " — |"
    lines.append(row)

    # --- Delta table (each challenger vs baseline) ---
    lines += [
        "",
        "## Deltas vs Baseline",
        "",
    ]
    header = "| Criterion | " + " | ".join(f"**{ch}**" for ch in challengers) + " |"
    sep = "|-----------|" + "|".join("------:" for _ in challengers) + "|"
    lines += [header, sep]

    for c in CRITERIA:
        bl_scores = skill_criterion_scores[baseline][c["id"]]
        bl_avg = sum(bl_scores) / len(bl_scores) if bl_scores else None
        row = f"| {c['name']} |"
        for ch in challengers:
            ch_scores = skill_criterion_scores[ch][c["id"]]
            ch_avg = sum(ch_scores) / len(ch_scores) if ch_scores else None
            if bl_avg is not None and ch_avg is not None:
                delta = ch_avg - bl_avg
                sign = "+" if delta > 0 else ""
                row += f" {sign}{delta:.2f} |"
            else:
                row += " — |"
        lines.append(row)

    # --- Ranking ---
    lines += [
        "",
        "## Ranking",
        "",
    ]
    # Rank by composite average
    ranking = []
    for s in all_skills:
        all_scores = []
        for c in CRITERIA:
            all_scores.extend(skill_criterion_scores[s][c["id"]])
        avg = sum(all_scores) / len(all_scores) if all_scores else 0
        ranking.append((s, avg, len(all_scores)))
    ranking.sort(key=lambda x: x[1], reverse=True)

    lines += [
        "| Rank | Skill | Composite Avg | Samples |",
        "|------|-------|--------------|---------|",
    ]
    for i, (skill, avg, n) in enumerate(ranking, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        lines.append(f"| {medal} | **{skill}** | {avg:.2f} | {n} |")

    lines += [
        "",
        "## Methodology",
        "",
        "- Pairwise blind A/B evals with randomized assignment, synthesized into a multi-skill view.",
        f"- All challengers compared against common baseline (`{baseline}`).",
        "- Criterion scores are absolute (1-5) extracted from each pairwise judgment.",
        "- Win rates and p-values are per-challenger vs baseline (one-sided binomial).",
        "",
        "---",
        f"*Generated by run_eval.py compare on {timestamp}*",
    ]

    report = "\n".join(lines)

    # Save report
    compare_file = RESULTS_BASE / f"compare_{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    RESULTS_BASE.mkdir(parents=True, exist_ok=True)
    compare_file.write_text(report)

    # Print to stdout
    print(report)
    print(f"\n  Saved to: {compare_file}")


def main():
    parser = argparse.ArgumentParser(description="SkillEval CLI — Blind A/B frontend skill evaluation")
    subparsers = parser.add_subparsers(dest="command")

    # --- compare subcommand ---
    cmp = subparsers.add_parser("compare", help="Compare multiple pairwise runs sharing a baseline")
    cmp.add_argument("runs", nargs="+",
                     help="Run directories (names under results/ or absolute paths)")
    cmp.add_argument("--baseline", default="wetch",
                     help="Common baseline label (default: wetch)")

    # --- default: run eval (no subcommand) ---
    parser.add_argument("--prompts", type=int, default=0, help="Number of prompts to run (0 = all)")
    parser.add_argument("--prompts-file", type=str, default=None,
                        help="Path to a JSON file with curated prompt list (overrides --prompts and default prompts.json)")
    parser.add_argument("--provider", choices=["anthropic", "openrouter"], default="openrouter",
                        help="API provider (default: openrouter)")
    parser.add_argument("--gen-model", default=GEN_MODEL, help=f"Generation model (default: {GEN_MODEL})")
    parser.add_argument("--judge-model", default=JUDGE_MODEL, help=f"Judge model (default: {JUDGE_MODEL})")
    parser.add_argument("--resume", action="store_true", help="Resume from latest run (or --results-dir)")
    parser.add_argument("--results-dir", type=str, default=None,
                        help="Path to a specific run directory (for --resume)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for A/B assignment")
    parser.add_argument("--skill-a", type=str, default=None,
                        help="Path to skill A (baseline). Default: eval/skills/wetch.md")
    parser.add_argument("--skill-b", type=str, default=None,
                        help="Path to skill B (challenger). Default: eval/skills/creative.md if exists, else eval/skills/minoan.md")
    parser.add_argument("--skill-b-supplement", type=str, default=None,
                        help="Path to supplementary skill appended to skill B with progressive disclosure framing")
    parser.add_argument("--label-a", type=str, default="wetch",
                        help="Label for skill A in reports (default: wetch)")
    parser.add_argument("--label-b", type=str, default="minoan",
                        help="Label for skill B in reports (default: minoan)")
    args = parser.parse_args()

    if args.command == "compare":
        compare_runs(args.runs, args.baseline)
    else:
        random.seed(args.seed)
        asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
