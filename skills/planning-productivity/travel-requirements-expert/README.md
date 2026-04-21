# Travel Requirements Expert

Transform travel requests into comprehensive, research-backed itineraries through a systematic 5-phase workflow: initial setup, discovery questions, research via Exa search and Firecrawl scraping, expert detail gathering, and a full requirements specification with day-by-day plans.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Ad-hoc trip planning misses details---weather safety, dietary constraints, cultural customs, backup options. This skill uses a structured requirements-gathering process (inspired by software spec methodology) to produce implementable itineraries with specific venues, times, and contingencies, backed by live research via Exa search and Firecrawl scraping.

---

## Structure

```
travel-requirements-expert/
  SKILL.md                          # Full 5-phase workflow
  README.md                         # This file
  references/
    requirements-workflow.md        # Detailed phase instructions and examples
  scripts/
    create_requirements_folder.py   # Create timestamped requirements folder
```

---

## 5-Phase Workflow

1. **Initialize** --- Create timestamped folder with `00-initial-request.md` and `metadata.json`
2. **Discovery** --- 5 foundational yes/no questions (activity intensity, social preferences, structure, amenities, flexibility)
3. **Research** --- Parallel searches (Exa for comprehensive research, Firecrawl for page extraction)
4. **Expert Detail** --- 5 specific questions based on research findings (real venues, concrete trade-offs)
5. **Requirements Spec** --- `06-requirements-spec.md` with day-by-day itinerary, safety protocols, packing list

---

## Usage

```bash
# Create requirements folder
python3 create_requirements_folder.py "10-day Crete hiking and cultural trip" requirements

# Output: YYYY-MM-DD-HHMM-crete-hiking/
#   00-initial-request.md
#   metadata.json
#   .current-requirement
```

The rest of the workflow is conversational---the skill guides Claude through the 5 phases, asking one question at a time with smart defaults.

---

## Output Files

| File | Phase | Contents |
|------|-------|----------|
| `00-initial-request.md` | 1 | User's original request |
| `01-discovery-questions.md` | 2 | 5 foundational questions |
| `02-discovery-answers.md` | 2 | User's answers |
| `03-context-findings.md` | 3 | Research results with confidence levels |
| `04-detail-questions.md` | 4 | 5 expert questions referencing specific findings |
| `05-detail-answers.md` | 4 | User's answers |
| `06-requirements-spec.md` | 5 | Complete itinerary with day-by-day breakdown |

---

## Setup

### Prerequisites

- Python 3.9+
- `EXA_API_KEY` env var (for Exa search and research)
- `FIRECRAWL_API_KEY` env var (for Firecrawl scraping and agent research)

---

## Related Skills

- **`exa-search`**: Neural web search used during the research phase.
- **`firecrawl`**: Web scraping for accommodation and venue details.

---

## Requirements

- Python 3.9+
- Exa API key
- Firecrawl API key

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/planning-productivity/travel-requirements-expert ~/.claude/skills/
```
