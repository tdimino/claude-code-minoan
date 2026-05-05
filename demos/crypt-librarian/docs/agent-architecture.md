# Agent Architecture — Crypt Librarian

Autonomous curation agent built on the Claude Agent SDK. Discovers 5-6 films per week matching gothic/literary taste criteria, tracks provenance in SQLite, and generates candidates for user approval. Taste compounds over time — approved films become seeds for future discovery.

---

## Lead Agent

**File:** `agent/crypt_librarian.py`

Orchestrates a 5-phase discovery workflow using `claude_agent_sdk.query()`. Delegates each phase to a specialized subagent.

---

## Subagents

Defined in `agent/subagents.py`:

| Subagent | Model | Responsibility |
|----------|-------|----------------|
| `taste_learner` | Haiku | Reads rated films from `films.json`, extracts lane averages and 5-candle predictors, writes `taste_seeds.json` |
| `film_discoverer` | Sonnet | Exa search + Firecrawl scraping using seeds from `taste_seeds.json` |
| `content_validator` | Haiku | Perplexity-based exclusion checks (gore, post-2016, Asian cinema, already-tracked) |
| `database_manager` | Haiku | SQLite provenance — saves candidates, checks duplicates, records declines |
| `subtitle_hunter` | Haiku | YIFY/OpenSubtitles fallback for subtitle availability on obscure titles |

Haiku handles structured I/O tasks (read, write, validate, query). Sonnet handles open-ended search and discovery where reasoning quality matters.

---

## Taste Calibration Loop

```
generate_taste_seeds.py → taste_seeds.json → Exa searches → crypt_db.py → films.json
         ↑                                                                     ↓
         └──────────────── rated films feed back ─────────────────────────────┘
```

The taste loop is the core of the system: rated films produce taste patterns (5-candle predictors, 3-candle warnings, lane calibration), which drive discovery, which produces candidates, which become rated films.

---

## Data Flow

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────────┐
│ taste_learner    │───►│ taste_seeds  │───►│ film_discoverer  │
│ (reads films.json)    │ .json        │    │ (Exa + Firecrawl)│
└─────────────────┘    └──────────────┘    └────────┬─────────┘
                                                     │
                                                     ▼
                       ┌──────────────┐    ┌──────────────────┐
                       │ database_mgr │◄───│ content_validator│
                       │ (SQLite)     │    │ (Perplexity)     │
                       └──────┬───────┘    └──────────────────┘
                              │
                              ▼
                       ┌──────────────┐    ┌──────────────────┐
                       │ candidates   │───►│ approve.py       │
                       │ .json        │    │ (human review)   │
                       └──────────────┘    └────────┬─────────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │ films.json   │
                                              │ (archive)    │
                                              └──────────────┘
```

---

## Database

SQLite at `crypt-librarian.db`, schema created by `agent/init_db.py`:

| Table | Purpose |
|-------|---------|
| `declined_films` | Films rejected by user — title, year, reason. Prevents re-recommendation. |
| `searched_sources` | URLs and queries already used. Prevents redundant searches. |
| `candidates` | Pending candidates — title, year, director, themes, discovery_source, status. |

---

## CLI Tools

### `scripts/crypt_db.py`

Primary CLI for database operations:

```bash
crypt_db.py check "Title" 1999      # Returns: NEW_FILM | ALREADY_TRACKED | DECLINED
crypt_db.py save-candidate --title "T" --year Y --director "D" --themes "..." --why "..."
crypt_db.py pending                   # List pending candidates
crypt_db.py decline "Title" 1999      # Mark as declined with reason
```

### `scripts/generate_taste_seeds.py`

Reads rated films from `films.json`, computes lane averages and taste patterns. Outputs `taste_seeds.json` consumed by the `film_discoverer` subagent. Also available as `--json` for direct inspection.

### `scripts/fetch_trailers.py`

YouTube trailer URL lookup for films in the archive.

### `scripts/flexible_discovery.py`

Discovery mode that relaxes default filters for requests outside the normal taste profile:

```bash
flexible_discovery.py "Korean revenge thrillers" --region asian --mood thriller
flexible_discovery.py "cozy mysteries" --era 90s --region british
```

---

## Running the Agent

```bash
# Manual discovery run
python3 agent/crypt_librarian.py

# Review pending candidates (interactive approval)
python3 agent/approve.py
```

---

## Mandatory Exclusions

Enforced at every stage of the pipeline:

| Filter | Reason |
|--------|--------|
| Post-2016 release | Strict cutoff, no exceptions |
| Gore/torture porn | Against sensibility |
| Animal cruelty | Dealbreaker |
| Child abuse as spectacle | Dealbreaker |
| Asian cinema | User preference |
| Already tracked | In `films.json` or `declined_films` table |

---

## Source of Truth

`films.json` is the canonical archive. Both the web app (reads via API) and the agent (writes via `crypt_db.py`) share it. The agent never overwrites existing entries — it only appends candidates with `status: "to_watch"`. User approval promotes candidates to `status: "watched"` with ratings and commentary.
