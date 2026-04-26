# films.json Schema

Source of truth for the entire archive. Read by the web API, the autonomous agent, taste seed generation, and poster fetching.

## Top-Level Structure

```json
{
  "meta": {
    "description": "Crypt Librarian film archive with multi-voice commentary",
    "last_updated": "2026-04-11",
    "voices": {
      "claude": "Curatorial analysis through the Crypt Librarian sensibility",
      "tom": "Tom (user) — personal response and notes",
      "mary": "Mary (Tom's partner) — personal response and notes"
    }
  },
  "films": [ ... ],
  "categories": { ... }
}
```

## Film Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Kebab-case: `{title}-{year}` (e.g., `the-ninth-gate-1999`) |
| `title` | string | yes | Display title |
| `year` | number | yes | Release year |
| `director` | string | yes | Primary director |
| `watched` | string\|bool | yes | `"pre-2026"`, `"2026-03-15"`, or `false` |
| `status` | enum | yes | `"watched"` or `"to_watch"` |
| `rating.tom` | number\|null | yes | 1–5 candles or null |
| `rating.mary` | number\|null | yes | 1–5 candles or null |
| `categories` | string[] | yes | Category keys from the registry |
| `themes` | string[] | yes | Free-text thematic tags |
| `discovery_source` | string | yes | How the film was found |
| `content_warnings` | string[] | yes | Violence, nudity, etc. |
| `commentary.claude` | string\|null | yes | Crypt Librarian curatorial voice |
| `commentary.tom` | string\|null | yes | Tom's personal notes |
| `commentary.mary` | string\|null | yes | Mary's personal notes |
| `connections` | string[] | yes | Free-text links to other films |
| `available_on` | string[] | yes | Streaming/physical sources |
| `trailer_url` | string | no | YouTube URL |

### ID Convention

`{title-in-kebab-case}-{year}`. Examples:
- `interview-with-the-vampire-1994`
- `the-long-goodbye-1973`
- `stir-of-echoes-1999`

Strip articles only when they'd sort oddly. "The Ninth Gate" → `the-ninth-gate-1999` (keep "the").

### Discovery Source Values

Common values: `"touchstone film"`, `"exa-research"`, `"perplexity"`, `"firecrawl"`, `"user-suggestion"`, `"connection from {film}"`, `"Criterion Collection"`, `"MUBI"`.

## Category Registry

28 categories with prose descriptions. Each key is used in the `categories[]` array on film objects.

| Key | Description |
|-----|-------------|
| `noir` | Shadow-drenched crime dramas, moral ambiguity |
| `neo-noir` | Modern noir sensibility, revisionist |
| `vampire` | Metaphors for desire, class, corruption |
| `feminine-gothic` | Female protagonists, patriarchal structures |
| `literary-adaptation` | Adapted from novels, plays, literary sources |
| `cerebral-occult` | Intellectual Satanism, theological debate, rare books |
| `folk-horror` | Pagan traditions, rural isolation |
| `period-piece` | Historical settings with atmospheric detail |
| `restrained-horror` | Atmosphere over spectacle |
| `occult-ritual` | Secret societies, ceremonial magic |
| `psychic-visions` | Unwanted visions, tied to justice |
| `ghost-seeking-justice` | The dead demanding acknowledgment |
| `southern-gothic` | Humid atmosphere, small-town secrets |
| `new-orleans-gothic` | Decay, heat, the supernatural |
| `los-angeles-noir` | Sun-bleached corruption |
| `american-gothic` | Uncanny dread in mundane settings |
| `irish-gothic` | Celtic melancholy, ancient curses |
| `coastal-decay` | Seaside settings in decline |
| `blue-collar-horror` | Working-class supernatural |
| `ensemble-cast` | Multiple strong performances |
| `homoerotic-subtext` | Desire coded through gaze |
| `femme-fatale-subversion` | Women who appear dangerous but are victims |
| `mother-daughter` | Maternal bonds tested |
| `murder-mystery` | Investigation-driven |
| `wrongly-accused` | Protagonist trapped by circumstance |
| `revisionist-genre` | Deconstructs genre conventions |
| `practical-effects` | Pre-CGI craftsmanship |
| `1970s-new-hollywood` | Auteur era cynicism |

## TypeScript Types

The frontend mirrors this schema exactly in `web/frontend/lib/types.ts`:
- `Film` — single film object
- `FilmsData` — `{ meta, films, categories }`
- `TasteData` — computed taste profile from `/api/taste`
- `ProfilesData` — Tom/Mary stats from `/api/profiles`

## Operations

```bash
# Read the archive
python3 -c "import json; d=json.load(open('films.json')); print(len(d['films']), 'films')"

# Check if a film exists
python3 scripts/crypt_db.py check "Film Title" 1975

# Add a candidate
python3 scripts/crypt_db.py save-candidate --title "T" --year Y --director "D" --themes "..." --why "..."

# List pending candidates
python3 scripts/crypt_db.py pending
```
