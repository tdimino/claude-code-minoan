---
name: classical-887
description: "This skill should be used when checking what's playing on WRHV 88.7 FM (Classical WMHT) in the Hudson Valley, fetching recent tracks, building playlist reports, searching for pieces, or creating Spotify playlists from radio tracks."
---

# Classical 887

Check what's playing on WRHV 88.7 FM (Classical WMHT) — the classical music station in the Hudson Valley. Queries the NPR Composer API for real-time playlist data and provides clickable links to listen on YouTube, Spotify, Apple Music, and view scores on IMSLP.

## When to Use

- Checking what's playing right now on 88.7
- Getting recent tracks with links to listen again
- Building a Markdown playlist report
- Finding a specific piece heard on the radio
- Creating Spotify playlists from radio tracks

## Prerequisites

- `requests` Python package (`uv pip install --system requests`)
- No API key required — uses NPR's public Composer API
- **Spotify integration (optional):** `spotipy` package (`uv pip install --system spotipy`) + Spotify Developer App credentials

## Usage

```bash
# What's playing right now (default)
python3 ~/.claude/skills/classical-887/scripts/classical_887.py

# Last 10 tracks
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --recent 10

# Today's full playlist (pages through all tracks for today)
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period today

# Last week as Markdown report
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period week --markdown ~/Desktop/classical-week.md

# Last month as Markdown report
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period month --markdown ~/Desktop/classical-month.md

# Specific date (Valentine's Day)
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --date 2026-02-14

# Search for a composer across a date range
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period week --search bach

# Full performer details (album, label, catalog number)
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --recent 5 --verbose

# Raw JSON output
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --now --json

# Create Spotify playlist from today's tracks
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period today --spotify-playlist

# Add yesterday's tracks to the persistent playlist
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period yesterday --spotify-playlist

# Custom playlist name from a specific date
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --date 2026-02-14 --spotify-playlist "Valentine's Classical"

# Last week's Bach on Spotify
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period week --search bach --spotify-playlist "Bach on 88.7"
```

## Parameters

| Flag | Description | Default |
|------|-------------|---------|
| `--now` | Show what's playing now | On (if no other mode) |
| `--recent N` | Show last N tracks (1–100) | Off |
| `--date YYYY-MM-DD` | Fetch all tracks from a specific date | Off |
| `--period PERIOD` | Fetch tracks from: `today`, `yesterday`, `week`, `month` | Off |
| `--search QUERY` | Filter results by composer, piece, or performer | Off |
| `--verbose` | Full details (album, label, catalog, all performers) | Off |
| `--json` | Raw JSON output | Off |
| `--markdown [FILE]` | Write Markdown report with clickable links | `classical-playlist.md` |
| `--sort FIELD` | Sort by: `time` (newest first), `duration` (longest), `composer` (A–Z) | `time` |
| `--spotify-playlist [NAME]` | Create/append to a Spotify playlist | `Classical 88.7 FM` |
| `--spotify-client-id ID` | Spotify app client ID (or `SPOTIFY_CLIENT_ID` env var) | — |
| `--spotify-client-secret SECRET` | Spotify app client secret (or `SPOTIFY_CLIENT_SECRET` env var) | — |

## Output

Default shows: composer, piece, performers, duration, and listen links (YouTube, Spotify, Apple Music, IMSLP).

Markdown report includes: now-playing header, recent tracks table with links, and a composer index.

## Data Source

NPR Composer API (`api.composer.nprstations.org/v1/widget/`), which powers the WMHT playlist widget at `classicalwmht.org/playlist`.

Full API documentation: `references/api-reference.md`

## Station Info

WRHV 88.7 FM (Poughkeepsie, NY), simulcast of WMHT-FM 89.1 (Schenectady). Full station details in `references/api-reference.md`.

- Stream: [wmht.org/classical](https://wmht.org/classical/)
- Playlist: [classicalwmht.org/playlist](https://classicalwmht.org/playlist)

## Fallback

If the NPR Composer API is unavailable:

```bash
# Check the playlist page directly
firecrawl scrape "https://classicalwmht.org/playlist" --only-main-content
```

## Reference Documentation

| File | Contents |
|------|----------|
| `references/api-reference.md` | NPR Composer API: endpoints, request/response schema, field reference |
| `references/spotify-setup.md` | Spotify Developer App setup, OAuth, env vars, Dev Mode notes |
