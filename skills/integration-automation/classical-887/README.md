# Classical 887

Check what's playing on WRHV 88.7 FM (Classical WMHT), fetch recent tracks with listen links across 7 platforms, build playlist reports, search by composer, and create/manage Spotify playlists from radio tracks.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

WRHV 88.7 FM is the classical music station in the Hudson Valley. This skill queries the NPR Composer API for real-time playlist data and provides clickable links to YouTube, Spotify, Apple Music, IMSLP, IDAGIO, Internet Archive, and Musopen---plus optional Spotify playlist creation from what was played.

---

## Structure

```
classical-887/
  SKILL.md                          # Full usage guide with all flags
  README.md                         # This file
  references/
    api-reference.md                # NPR Composer API: endpoints, schema, fields
    spotify-setup.md                # Spotify Developer App setup and OAuth
  scripts/
    classical_887.py                # Main CLI script
```

---

## Usage

```bash
# What's playing right now
python3 classical_887.py

# Last 10 tracks
python3 classical_887.py --recent 10

# Today's full playlist
python3 classical_887.py --period today

# Last week as Markdown report
python3 classical_887.py --period week --markdown ~/Desktop/classical-week.md

# Search for Bach across the past month
python3 classical_887.py --period month --search bach

# Create Spotify playlist from today's tracks
python3 classical_887.py --period today --spotify-playlist
```

---

## Key Features

| Feature | Flag |
|---------|------|
| Now playing | `--now` (default) |
| Recent tracks | `--recent N` |
| Date range | `--period today/yesterday/week/month` or `--date YYYY-MM-DD` |
| Search | `--search QUERY` (composer, piece, performer) |
| Markdown report | `--markdown [FILE]` |
| Spotify playlist | `--spotify-playlist [NAME]` |
| Spotify audit/cleanup | `--spotify-audit`, `--spotify-cleanup PATTERN` |
| JSON output | `--json` |

---

## Setup

### Prerequisites

- Python 3.9+
- `pip install requests`
- No API key required---uses NPR's public Composer API

### Spotify Integration (Optional)

- `pip install spotipy`
- Spotify Developer App credentials (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`)
- See `references/spotify-setup.md` for setup walkthrough

---

## Requirements

- Python 3.9+
- `requests`
- `spotipy` (optional, for Spotify features)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/classical-887 ~/.claude/skills/
```
