# Poster Acquisition Pipeline

Fetches movie poster art for the VELVET CATALOGUE web interface.

## Script

`web/frontend/public/posters/fetch_posters.py`

## Source Priority

1. **TMDB** (The Movie Database) — w500 resolution JPG. Best quality, free API.
2. **OMDB** — IMDB poster URLs. Fallback when TMDB misses.
3. **SVG placeholder** — Styled placeholder with film title if no poster found.

## API Keys

```bash
# Required in environment or ~/.config/env/secrets.env
TMDB_API_KEY=...    # Free at https://www.themoviedb.org/settings/api
OMDB_API_KEY=...    # Optional, free at https://www.omdbapi.com/apikey.aspx
```

The script loads `~/.config/env/secrets.env` automatically if keys aren't in the environment.

## Usage

```bash
cd ~/Desktop/Programming/crypt-librarian/web/frontend/public/posters

# Fetch all missing posters
source ~/.config/env/secrets.env
uv run --with requests python3 fetch_posters.py

# Single film by ID
uv run --with requests python3 fetch_posters.py --id the-ninth-gate-1999

# Dry run (check TMDB matches without downloading)
uv run --with requests python3 fetch_posters.py --dry-run

# Force re-download existing posters
uv run --with requests python3 fetch_posters.py --force
```

## Output

| File | Description |
|------|-------------|
| `{film-id}.jpg` | Poster image (w500 from TMDB) |
| `{film-id}.svg` | Styled SVG fallback if no poster found |
| `manifest.json` | Provenance tracking — source, URL, resolution, timestamp per poster |

## manifest.json Entry

```json
{
  "the-ninth-gate-1999": {
    "source": "tmdb",
    "url": "https://image.tmdb.org/t/p/w500/...",
    "tmdb_id": 820,
    "resolution": "w500",
    "fetched": "2026-04-26T12:00:00"
  }
}
```

## TMDB Search Logic

1. Search `/search/movie?query={title}&year={year}`
2. If no results, retry without year filter
3. If still no results, try alternate title formats (strip "The", etc.)
4. Download poster from `https://image.tmdb.org/t/p/w500{poster_path}`

## Frontend Fallback Chain

In React components, the pattern is:
```tsx
const [imgError, setImgError] = useState(false);
const src = imgError ? `/posters/${film.id}.svg` : `/posters/${film.id}.jpg`;
<img src={src} onError={() => setImgError(true)} />
```

## When to Run

- After adding new films to `films.json`
- After running the autonomous agent's discovery cycle
- When the web app shows SVG placeholders where posters should be
