#!/usr/bin/env python3
"""
Classical 887 — what's playing on WRHV 88.7 FM (Classical WMHT).

Queries the NPR Composer API for now-playing and recent tracks from WMHT,
the classical music station in the Hudson Valley (simulcast of WMHT-FM 89.1,
Schenectady). Generates clickable links to YouTube, Spotify, Apple Music,
and IMSLP for each piece. Can create Spotify playlists from fetched tracks.

Usage:
    classical_887.py                              # What's playing now
    classical_887.py --recent 10                  # Last 10 tracks
    classical_887.py --recent 50 --markdown       # Markdown report
    classical_887.py --verbose                    # Full performer details
    classical_887.py --json                       # Raw JSON output
    classical_887.py --period yesterday --spotify-playlist "Yesterday on 88.7"

Requires: requests (uv pip install --system requests)
Optional: spotipy (uv pip install --system spotipy) — for Spotify playlist creation
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import quote_plus

try:
    import requests
except ImportError:
    print("Error: 'requests' package required.", file=sys.stderr)
    print("Install: uv pip install --system requests", file=sys.stderr)
    sys.exit(1)

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    HAS_SPOTIPY = True
except ImportError:
    HAS_SPOTIPY = False


# ── Constants ──────────────────────────────────────────────────────────────────

NPR_COMPOSER_BASE = "https://api.composer.nprstations.org/v1"
WMHT_UCS = "51892578e1c81d34d1474a5d"

WMHT_STREAM_URL = "https://wmht.org/classical/"
WMHT_PLAYLIST_URL = "https://classicalwmht.org/playlist"


# ── API Functions ─────────────────────────────────────────────────────────────

def get_now_playing() -> Dict[str, Any]:
    """Fetch the currently playing track from WMHT."""
    url = f"{NPR_COMPOSER_BASE}/widget/{WMHT_UCS}/now?format=json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()

    result = {"program": None, "track": None}

    on_now = data.get("onNow", {})
    program = on_now.get("program", {})
    if program:
        result["program"] = {
            "name": program.get("name", ""),
            "format": program.get("program_format", ""),
            "start_time": on_now.get("start_time", ""),
            "end_time": on_now.get("end_time", ""),
        }

    song = on_now.get("song", {})
    if song and song.get("trackName"):
        result["track"] = _parse_song(song)

    return result


def get_recent_tracks(limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch recently played tracks from WMHT."""
    limit = min(limit, 100)
    url = f"{NPR_COMPOSER_BASE}/widget/{WMHT_UCS}/tracks?format=json&limit={limit}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()

    tracks = []

    # Current track from onNow
    on_now = data.get("onNow", {})
    song = on_now.get("song", {})
    if song and song.get("trackName"):
        track = _parse_song(song)
        track["is_now_playing"] = True
        tracks.append(track)

    # Recent tracks from tracklist
    tracklist = data.get("tracklist", {})
    results = tracklist.get("results", [])
    for entry in results:
        song = entry.get("song", {})
        if song and song.get("trackName"):
            track = _parse_song(song)
            track["is_now_playing"] = False
            tracks.append(track)

    return tracks[:limit]


def get_tracks_since(since: datetime, until: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Fetch all tracks from `since` to `until` by paging backward with datestamp.

    The API returns tracks *before* a given datestamp, up to 100 per call.
    We page backward from `until` (default: now) until we pass `since`.
    """
    if until is None:
        until = datetime.now()

    all_tracks = []
    cursor = until
    max_pages = 50  # safety: ~5000 tracks max

    for _ in range(max_pages):
        datestamp = cursor.strftime("%Y-%m-%dT%H:%M:%S")
        url = (
            f"{NPR_COMPOSER_BASE}/widget/{WMHT_UCS}/tracks"
            f"?format=json&limit=100&datestamp={datestamp}"
        )
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        results = data.get("tracklist", {}).get("results", [])
        if not results:
            break

        batch = []
        oldest_in_batch = None
        for entry in results:
            song = entry.get("song", {})
            if not song or not song.get("trackName"):
                continue

            track = _parse_song(song)
            track["is_now_playing"] = False

            # Parse the track's datetime for filtering
            track_dt = _parse_start_datetime(track["start_time"])
            if track_dt and track_dt < since:
                # We've gone past our target date — stop
                oldest_in_batch = track_dt
                break

            batch.append(track)
            if track_dt:
                oldest_in_batch = track_dt

        all_tracks.extend(batch)

        # If we broke out early (hit the since boundary), done
        if oldest_in_batch and oldest_in_batch <= since:
            break

        # If fewer than 100 results, no more data
        if len(results) < 100:
            break

        # Move cursor backward: use the oldest track's timestamp
        if oldest_in_batch:
            cursor = oldest_in_batch - timedelta(seconds=1)
        else:
            break

        print(f"  Fetched {len(all_tracks)} tracks so far (back to {cursor.strftime('%m/%d %I:%M %p')})...",
              file=sys.stderr)

    return all_tracks


def _parse_start_datetime(start_time: str) -> Optional[datetime]:
    """Parse API timestamp string into a datetime object."""
    if not start_time:
        return None
    for fmt in ("%m-%d-%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(start_time, fmt)
        except ValueError:
            continue
    return None


def _parse_song(song: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a song object from the NPR Composer API into a clean dict."""
    composer = song.get("composerName", "").strip()
    track_name = song.get("trackName", "").strip()
    artist = song.get("artistName", "").strip()
    soloists = song.get("soloists", "").strip()
    ensembles = song.get("ensembles", "").strip()
    conductor = song.get("conductor", "").strip()
    album = song.get("collectionName", "").strip()
    label = song.get("copyright", "").strip()
    catalog_num = song.get("catalogNumber", "").strip()
    duration_ms = song.get("_duration", 0)
    start_time = song.get("_start_time", "")
    date = song.get("_date", "")

    # Build performers list
    performers = []
    if artist:
        performers.append(artist)
    if soloists and soloists != artist:
        performers.append(soloists)
    if ensembles:
        performers.append(ensembles)
    if conductor and conductor not in " ".join(performers):
        performers.append(conductor)

    # Format duration
    duration_str = ""
    if duration_ms and duration_ms > 0:
        total_sec = duration_ms // 1000
        minutes = total_sec // 60
        seconds = total_sec % 60
        duration_str = f"{minutes}:{seconds:02d}"

    # Build search URLs
    search_links = _build_search_urls(composer, track_name)

    return {
        "composer": composer,
        "track_name": track_name,
        "artist": artist,
        "soloists": soloists,
        "ensembles": ensembles,
        "conductor": conductor,
        "performers": ", ".join(p for p in performers if p),
        "album": album,
        "label": label,
        "catalog_number": catalog_num,
        "duration": duration_str,
        "duration_ms": duration_ms,
        "start_time": start_time,
        "date": date,
        "links": search_links,
    }


_LINK_LABELS = {
    "youtube": "YouTube",
    "spotify": "Spotify",
    "apple_music": "Apple Music",
    "imslp": "IMSLP",
    "idagio": "IDAGIO",
    "internet_archive": "Internet Archive",
    "musopen": "Musopen",
}


def _build_search_urls(composer: str, track_name: str) -> Dict[str, str]:
    """Build search URLs for YouTube, Spotify, Apple Music, IMSLP, IDAGIO, Internet Archive, and Musopen."""
    if not composer and not track_name:
        return {}

    query = f"{composer} {track_name}".strip()
    encoded = quote_plus(query)

    return {
        "youtube": f"https://www.youtube.com/results?search_query={encoded}",
        "spotify": f"https://open.spotify.com/search/{encoded}",
        "apple_music": f"https://music.apple.com/us/search?term={encoded}",
        "imslp": f"https://imslp.org/index.php?search={quote_plus(composer + ' ' + _extract_work_name(track_name))}",
        "idagio": f"https://app.idagio.com/search?q={encoded}",
        "internet_archive": f"https://archive.org/search?query={encoded}&and[]=mediatype:audio",
        "musopen": f"https://musopen.org/music/?q={encoded}",
    }


def _extract_work_name(track_name: str) -> str:
    """Extract the core work name for IMSLP search (strip movement info)."""
    # Common patterns: "Symphony No. 5, Mvt. 3" → "Symphony No. 5"
    # "Piano Trio 1 D Min, Op.49" → "Piano Trio 1 D Min, Op.49"
    # Keep op. numbers, strip movement indicators
    for sep in [", Mvt", ", mvt", "- Mvt", "- mvt", ": I.", ": II.", ": III.", ": IV."]:
        if sep in track_name:
            track_name = track_name[:track_name.index(sep)]
            break
    return track_name.strip()


# ── Spotify Integration ───────────────────────────────────────────────────────

SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
SPOTIFY_SCOPES = "playlist-read-private playlist-modify-public playlist-modify-private user-library-modify"
SPOTIFY_TOKEN_CACHE = os.path.expanduser("~/.claude/skills/classical-887/.spotify-cache")
PLAYLIST_LOG_PATH = os.path.expanduser("~/.claude/skills/classical-887/playlist-log.jsonl")
PLAYLIST_AUDIT_LOG_PATH = os.path.expanduser("~/.claude/skills/classical-887/playlist-audit.jsonl")


def _get_spotify_client(client_id: str, client_secret: str) -> "spotipy.Spotify":
    """Authenticate with Spotify and return a client."""
    if not HAS_SPOTIPY:
        print("Error: 'spotipy' package required for Spotify integration.", file=sys.stderr)
        print("Install: uv pip install --system spotipy", file=sys.stderr)
        sys.exit(1)

    auth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_path=SPOTIFY_TOKEN_CACHE,
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth)


def _search_spotify_track(sp: "spotipy.Spotify", composer: str, track_name: str) -> Optional[Dict[str, Any]]:
    """Search Spotify for a classical track. Returns the best match or None."""
    # Classical music search strategy:
    # 1. Try composer + full track name
    # 2. If no results, try composer + extracted work name (without movement)
    # 3. If still nothing, try just the work name

    queries = [
        f"{composer} {track_name}",
        f"{composer} {_extract_work_name(track_name)}",
    ]

    for query in queries:
        try:
            results = sp.search(q=query, type="track", limit=5)
            items = results.get("tracks", {}).get("items", [])
            if items:
                # Prefer results where artist name contains the composer name
                composer_lower = composer.lower()
                for item in items:
                    artists = " ".join(a["name"].lower() for a in item.get("artists", []))
                    album = (item.get("album", {}).get("name", "") or "").lower()
                    if composer_lower in artists or composer_lower in album:
                        return {
                            "uri": item["uri"],
                            "name": item["name"],
                            "artists": ", ".join(a["name"] for a in item.get("artists", [])),
                            "album": item.get("album", {}).get("name", ""),
                            "url": item.get("external_urls", {}).get("spotify", ""),
                        }
                # Fallback: just take the first result
                item = items[0]
                return {
                    "uri": item["uri"],
                    "name": item["name"],
                    "artists": ", ".join(a["name"] for a in item.get("artists", [])),
                    "album": item.get("album", {}).get("name", ""),
                    "url": item.get("external_urls", {}).get("spotify", ""),
                }
        except Exception as e:
            print(f"  Spotify search error for '{query}': {e}", file=sys.stderr)
            continue

    return None


def _spotify_api_headers(sp: "spotipy.Spotify") -> Dict[str, str]:
    """Get auth headers from spotipy client for direct API calls."""
    token = sp.auth_manager.get_access_token(as_dict=False)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _find_existing_playlist(sp: "spotipy.Spotify", user_id: str, name: str) -> Optional[Dict[str, Any]]:
    """Find an existing playlist by name using GET /me/playlists.

    Uses ``next`` URL pagination (Feb 2026 Dev Mode compat).
    """
    headers = _spotify_api_headers(sp)
    url: Optional[str] = "https://api.spotify.com/v1/me/playlists?limit=50&offset=0"
    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        if not items:
            break
        for pl in items:
            if pl["name"] == name and pl["owner"]["id"] == user_id:
                return pl
        url = data.get("next")
    return None


def _create_playlist_api(sp: "spotipy.Spotify", name: str, public: bool, description: str) -> Dict[str, Any]:
    """Create playlist via POST /me/playlists (Feb 2026 safe endpoint)."""
    headers = _spotify_api_headers(sp)
    r = requests.post(
        "https://api.spotify.com/v1/me/playlists",
        headers=headers,
        json={"name": name, "public": public, "description": description},
    )
    r.raise_for_status()
    return r.json()


def _add_items_to_playlist(sp: "spotipy.Spotify", playlist_id: str, uris: List[str]) -> None:
    """Add items via POST /playlists/{id}/items (Feb 2026 safe endpoint)."""
    headers = _spotify_api_headers(sp)
    for batch_start in range(0, len(uris), 100):
        batch = uris[batch_start:batch_start + 100]
        r = requests.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
            headers=headers,
            json={"uris": batch},
        )
        r.raise_for_status()


def _rename_playlist(
    sp: "spotipy.Spotify",
    playlist_id: str,
    new_name: str,
    new_description: Optional[str] = None,
) -> None:
    """Rename a playlist via PUT /playlists/{id} (Feb 2026 safe endpoint)."""
    headers = _spotify_api_headers(sp)
    body: Dict[str, str] = {"name": new_name}
    if new_description is not None:
        body["description"] = new_description
    r = requests.put(
        f"https://api.spotify.com/v1/playlists/{playlist_id}",
        headers=headers,
        json=body,
    )
    r.raise_for_status()


def rename_spotify_playlist(
    current_name: str,
    new_name: str,
    client_id: str,
    client_secret: str,
    new_description: Optional[str] = None,
) -> Dict[str, Any]:
    """Find a playlist by current name and rename it.

    Returns a summary dict with old/new names and playlist URL.
    """
    sp = _get_spotify_client(client_id, client_secret)
    user = sp.current_user()
    user_id = user["id"]

    print(f"Authenticated as: {user['display_name']} ({user_id})", file=sys.stderr)
    print(f"Looking for playlist: {current_name}", file=sys.stderr)

    existing = _find_existing_playlist(sp, user_id, current_name)
    if not existing:
        print(f"Error: No playlist found with name '{current_name}'.", file=sys.stderr)
        return {"error": f"Playlist '{current_name}' not found", "renamed": False}

    playlist_id = existing["id"]
    playlist_url = existing["external_urls"]["spotify"]

    _rename_playlist(sp, playlist_id, new_name, new_description)

    print(f"Renamed: '{current_name}' → '{new_name}'", file=sys.stderr)
    if new_description:
        print(f"Description: {new_description}", file=sys.stderr)
    print(f"Playlist URL: {playlist_url}", file=sys.stderr)

    return {
        "renamed": True,
        "playlist_id": playlist_id,
        "playlist_url": playlist_url,
        "old_name": current_name,
        "new_name": new_name,
        "new_description": new_description,
    }


# ── Playlist Logging ─────────────────────────────────────────────────────────

def _append_playlist_log(result: Dict[str, Any]) -> str:
    """Append a JSONL entry to the playlist log after a --spotify-playlist operation.

    Each entry records the date, playlist metadata, matched/unmatched tracks,
    and total counts. Returns the log file path.
    """
    entry = {
        "date": datetime.now().isoformat(),
        "playlist_name": result.get("playlist_name", ""),
        "playlist_url": result.get("playlist_url", ""),
        "playlist_id": result.get("playlist_id", ""),
        "action": result.get("action", ""),
        "matched_count": result.get("matched", 0),
        "unmatched_count": result.get("unmatched", 0),
        "total_count": result.get("total", 0),
        "tracks_added": [],
        "tracks_not_found": [],
    }

    for m in result.get("matched_tracks", []):
        radio = m.get("radio_track", {})
        spotify = m.get("spotify", {})
        entry["tracks_added"].append({
            "composer": radio.get("composer", ""),
            "piece": radio.get("track_name", ""),
            "performers": radio.get("performers", ""),
            "duration": radio.get("duration", ""),
            "spotify_uri": spotify.get("uri", ""),
            "spotify_name": spotify.get("name", ""),
            "spotify_artists": spotify.get("artists", ""),
        })

    for t in result.get("unmatched_tracks", []):
        entry["tracks_not_found"].append({
            "composer": t.get("composer", ""),
            "piece": t.get("track_name", ""),
            "performers": t.get("performers", ""),
            "duration": t.get("duration", ""),
        })

    with open(PLAYLIST_LOG_PATH, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")

    return PLAYLIST_LOG_PATH


def _read_playlist_log() -> List[Dict[str, Any]]:
    """Read all entries from the playlist log JSONL file."""
    entries = []
    if not os.path.exists(PLAYLIST_LOG_PATH):
        return entries
    with open(PLAYLIST_LOG_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def format_playlist_log_report() -> str:
    """Render the playlist log as a Markdown report."""
    entries = _read_playlist_log()
    if not entries:
        return "No playlist log entries found.\n\nLog file: " + PLAYLIST_LOG_PATH

    lines = []
    lines.append("# Classical 88.7 FM — Spotify Playlist Log")
    lines.append(f"*{len(entries)} operations logged*\n")

    total_matched = 0
    total_unmatched = 0

    for i, entry in enumerate(entries, 1):
        date_str = entry.get("date", "")
        # Parse ISO date for display
        try:
            dt = datetime.fromisoformat(date_str)
            display_date = dt.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            display_date = date_str

        playlist_name = entry.get("playlist_name", "Unknown")
        playlist_url = entry.get("playlist_url", "")
        action = entry.get("action", "unknown")
        matched = entry.get("matched_count", 0)
        unmatched = entry.get("unmatched_count", 0)
        total = entry.get("total_count", 0)

        total_matched += matched
        total_unmatched += unmatched

        lines.append(f"## {i}. {display_date}")
        lines.append("")
        if playlist_url:
            lines.append(f"**Playlist:** [{playlist_name}]({playlist_url}) ({action})")
        else:
            lines.append(f"**Playlist:** {playlist_name} ({action})")
        lines.append(f"**Tracks:** {matched} matched, {unmatched} not found, {total} total")
        lines.append("")

        tracks_added = entry.get("tracks_added", [])
        if tracks_added:
            lines.append("### Tracks Added\n")
            lines.append("| Composer | Piece | Performers | Duration | Spotify |")
            lines.append("|----------|-------|------------|----------|---------|")
            for t in tracks_added:
                composer = t.get("composer", "").replace("|", "\\|")
                piece = t.get("piece", "").replace("|", "\\|")
                performers = t.get("performers", "").replace("|", "\\|")
                duration = t.get("duration", "")
                uri = t.get("spotify_uri", "")
                sp_name = t.get("spotify_name", "").replace("|", "\\|")
                if uri:
                    # Convert URI to URL
                    track_id = uri.replace("spotify:track:", "")
                    sp_link = f"[{sp_name}](https://open.spotify.com/track/{track_id})"
                else:
                    sp_link = sp_name
                lines.append(f"| {composer} | {piece} | {performers} | {duration} | {sp_link} |")
            lines.append("")

        not_found = entry.get("tracks_not_found", [])
        if not_found:
            lines.append("### Not Found on Spotify\n")
            for t in not_found:
                composer = t.get("composer", "?")
                piece = t.get("piece", "?")
                lines.append(f"- {composer} — {piece}")
            lines.append("")

        lines.append("---\n")

    # Summary
    lines.append("## Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total operations | {len(entries)} |")
    lines.append(f"| Total tracks matched | {total_matched} |")
    lines.append(f"| Total tracks not found | {total_unmatched} |")
    lines.append(f"| Match rate | {total_matched / max(total_matched + total_unmatched, 1) * 100:.1f}% |")
    lines.append(f"| Log file | `{PLAYLIST_LOG_PATH}` |")
    lines.append("")

    return "\n".join(lines)


def create_spotify_playlist(
    tracks: List[Dict[str, Any]],
    playlist_name: str,
    client_id: str,
    client_secret: str,
    public: bool = True,
) -> Dict[str, Any]:
    """Create or append to a Spotify playlist from classical tracks.

    Uses direct API calls to Feb 2026-safe endpoints (not spotipy methods
    that may still hit removed /users/{id}/playlists or /playlists/{id}/tracks).

    If a playlist with the given name already exists, appends new tracks.
    Returns a summary dict with playlist URL, matched/unmatched counts.
    """
    sp = _get_spotify_client(client_id, client_secret)
    user = sp.current_user()
    user_id = user["id"]

    print(f"Authenticated as: {user['display_name']} ({user_id})", file=sys.stderr)
    print(f"Searching Spotify for {len(tracks)} tracks...", file=sys.stderr)

    matched = []
    unmatched = []

    for i, t in enumerate(tracks):
        composer = t.get("composer", "")
        track_name = t.get("track_name", "")

        if not composer and not track_name:
            unmatched.append(t)
            continue

        result = _search_spotify_track(sp, composer, track_name)

        if result:
            matched.append({"radio_track": t, "spotify": result})
            print(f"  [{i+1}/{len(tracks)}] Found: {composer} — {track_name}", file=sys.stderr)
        else:
            unmatched.append(t)
            print(f"  [{i+1}/{len(tracks)}] NOT FOUND: {composer} — {track_name}", file=sys.stderr)

        # Rate limit: Spotify allows ~30 req/sec but be polite
        if (i + 1) % 10 == 0:
            time.sleep(0.5)

    if not matched:
        print("No tracks found on Spotify.", file=sys.stderr)
        return {"playlist_url": None, "matched": 0, "unmatched": len(unmatched), "tracks": []}

    today = datetime.now().strftime("%b %d, %Y")

    # Check for existing playlist with this name
    existing = None
    try:
        existing = _find_existing_playlist(sp, user_id, playlist_name)
    except Exception as e:
        print(f"  Could not list playlists ({e}), creating new.", file=sys.stderr)

    if existing:
        playlist_id = existing["id"]
        playlist_url = existing["external_urls"]["spotify"]
        print(f"Found existing playlist: {playlist_name}", file=sys.stderr)

        # Update description with today's date
        headers = _spotify_api_headers(sp)
        requests.put(
            f"https://api.spotify.com/v1/playlists/{playlist_id}",
            headers=headers,
            json={"description": f"Classical music from WRHV 88.7 FM (Classical WMHT) — updated {today}"},
        )
    else:
        # Create new playlist via POST /me/playlists
        description = f"Classical music from WRHV 88.7 FM (Classical WMHT) — created {today}"
        playlist = _create_playlist_api(sp, playlist_name, public, description)
        playlist_id = playlist["id"]
        playlist_url = playlist["external_urls"]["spotify"]
        print(f"Created new playlist: {playlist_name}", file=sys.stderr)

    # Add tracks via POST /playlists/{id}/items
    uris = [m["spotify"]["uri"] for m in matched]
    _add_items_to_playlist(sp, playlist_id, uris)

    action = "Appended to" if existing else "Created"
    print(f"\n{action} playlist: {playlist_url}", file=sys.stderr)
    print(f"  Added: {len(matched)} tracks ({today})", file=sys.stderr)
    if unmatched:
        print(f"  Not found on Spotify ({len(unmatched)}):", file=sys.stderr)
        for t in unmatched:
            print(f"    - {t.get('composer', '?')} — {t.get('track_name', '?')}", file=sys.stderr)

    result = {
        "playlist_url": playlist_url,
        "playlist_id": playlist_id,
        "playlist_name": playlist_name,
        "action": action.lower(),
        "matched": len(matched),
        "unmatched": len(unmatched),
        "total": len(tracks),
        "date_added": today,
        "matched_tracks": matched,
        "unmatched_tracks": unmatched,
    }

    # Auto-log to JSONL
    try:
        log_path = _append_playlist_log(result)
        print(f"  Logged to: {log_path}", file=sys.stderr)
    except Exception as e:
        print(f"  Warning: could not write playlist log ({e})", file=sys.stderr)

    return result


# ── Spotify Audit & Cleanup ──────────────────────────────────────────────────

def _list_all_playlists(
    sp: "spotipy.Spotify", user_id: str, search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Paginate GET /me/playlists, filter to owned, optional name match.

    Uses Spotify's ``next`` URL for pagination—Feb 2026 Dev Mode breaks
    manual offset construction but honours the cursor link returned in
    each response.
    """
    import fnmatch

    # Auto-wrap search in wildcards if it contains no glob characters,
    # so --search "Rediscover" matches "Rediscover - Aug 30th".
    pattern = search
    if pattern and not any(c in pattern for c in "*?["):
        pattern = f"*{pattern}*"

    headers = _spotify_api_headers(sp)
    playlists = []
    url: Optional[str] = "https://api.spotify.com/v1/me/playlists?limit=50&offset=0"
    retries = 0
    while url:
        r = requests.get(url, headers=headers)
        if r.status_code == 429:
            retries += 1
            if retries > 3:
                print("  Rate limit: max retries exceeded, returning partial results.", file=sys.stderr)
                break
            wait = min(int(r.headers.get("Retry-After", 5)), 30)
            print(f"  Rate limited, waiting {wait}s (attempt {retries}/3)...", file=sys.stderr)
            time.sleep(wait)
            continue
        r.raise_for_status()
        retries = 0
        data = r.json()
        items = data.get("items", [])
        if not items:
            break
        for pl in items:
            if pl["owner"]["id"] != user_id:
                continue
            track_info = pl.get("items", pl.get("tracks", {}))
            total = track_info.get("total", 0) if isinstance(track_info, dict) else 0
            entry = {
                "id": pl["id"],
                "name": pl["name"],
                "tracks": total,
                "public": pl.get("public", False),
                "url": pl.get("external_urls", {}).get("spotify", ""),
                "description": pl.get("description", ""),
            }
            if pattern and not fnmatch.fnmatch(entry["name"].lower(), pattern.lower()):
                continue
            playlists.append(entry)
        url = data.get("next")
    return playlists


def _get_playlist_age_proxy(sp: "spotipy.Spotify", playlist_id: str) -> Optional[str]:
    """Fetch first track's added_at as a proxy for playlist creation date."""
    headers = _spotify_api_headers(sp)
    try:
        r = requests.get(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            headers=headers,
            params={"limit": 1, "fields": "items(added_at)"},
        )
        r.raise_for_status()
        items = r.json().get("items", [])
        if items and items[0].get("added_at"):
            return items[0]["added_at"]
    except Exception:
        pass
    return None


def _unfollow_playlists_batch(sp: "spotipy.Spotify", playlist_ids: List[str]) -> int:
    """Unfollow (delete) playlists via DELETE /me/following in batches."""
    headers = _spotify_api_headers(sp)
    removed = 0
    # Spotify batch unfollow: DELETE /playlists/{id}/followers (one at a time)
    # The Feb 2026 DELETE /me/library endpoint is for albums/tracks.
    # For playlists, we must unfollow individually.
    for pid in playlist_ids:
        try:
            r = requests.delete(
                f"https://api.spotify.com/v1/playlists/{pid}/followers",
                headers=headers,
            )
            r.raise_for_status()
            removed += 1
        except Exception as e:
            print(f"  Warning: could not unfollow playlist {pid}: {e}", file=sys.stderr)
    return removed


def _append_audit_log(entry: Dict[str, Any]) -> str:
    """Append a JSONL entry to the playlist audit log."""
    entry["timestamp"] = datetime.now().isoformat()
    with open(PLAYLIST_AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    return PLAYLIST_AUDIT_LOG_PATH


def _fetch_playlist_tracks(sp: "spotipy.Spotify", playlist_id: str) -> List[Dict[str, Any]]:
    """Fetch all tracks from a playlist using ``next`` URL pagination.

    Uses ``/playlists/{id}/items`` (Feb 2026 safe endpoint) with limit=50
    to stay within Dev Mode caps.  The Feb 2026 API nests track data under
    the ``item`` key (not ``track``), so we check both for compatibility.
    """
    headers = _spotify_api_headers(sp)
    tracks = []
    url: Optional[str] = (
        f"https://api.spotify.com/v1/playlists/{playlist_id}/items"
        f"?limit=50&offset=0"
    )
    retries = 0
    while url:
        r = requests.get(url, headers=headers)
        if r.status_code == 429:
            retries += 1
            if retries > 3:
                print("  Rate limit: max retries exceeded, returning partial results.", file=sys.stderr)
                break
            wait = min(int(r.headers.get("Retry-After", 5)), 30)
            print(f"  Rate limited, waiting {wait}s (attempt {retries}/3)...", file=sys.stderr)
            time.sleep(wait)
            continue
        r.raise_for_status()
        retries = 0
        data = r.json()
        items = data.get("items", [])
        if not items:
            break
        for entry in items:
            # Feb 2026: track data under "item"; legacy: under "track"
            t = entry.get("item") or entry.get("track")
            if not t:
                continue
            tracks.append({
                "name": t.get("name", ""),
                "artists": ", ".join(a["name"] for a in t.get("artists", [])),
                "album": t.get("album", {}).get("name", ""),
                "uri": t.get("uri", ""),
                "url": t.get("external_urls", {}).get("spotify", ""),
                "duration_ms": t.get("duration_ms", 0),
                "added_at": entry.get("added_at", ""),
            })
        url = data.get("next")
    return tracks


def export_spotify_playlists(
    client_id: str,
    client_secret: str,
    search: Optional[str] = None,
    output_dir: str = ".",
) -> Dict[str, Any]:
    """Export matching playlists' track data to JSON files in output_dir."""
    sp = _get_spotify_client(client_id, client_secret)
    user_id = sp.current_user()["id"]

    print(f"Fetching playlists for {user_id}...", file=sys.stderr)
    playlists = _list_all_playlists(sp, user_id, search)

    if not playlists:
        print("No matching playlists found.", file=sys.stderr)
        return {"action": "export", "count": 0, "files": []}

    os.makedirs(output_dir, exist_ok=True)
    files = []
    for i, pl in enumerate(playlists, 1):
        print(f"  [{i}/{len(playlists)}] {pl['name']} ({pl['tracks']} tracks)...", file=sys.stderr)
        tracks = _fetch_playlist_tracks(sp, pl["id"])
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in pl["name"]).strip()
        filename = f"{safe_name}.json"
        filepath = os.path.join(output_dir, filename)
        export_data = {
            "playlist_id": pl["id"],
            "name": pl["name"],
            "url": pl["url"],
            "track_count": len(tracks),
            "exported_at": datetime.now().isoformat(),
            "tracks": tracks,
        }
        with open(filepath, "w") as f:
            f.write(json.dumps(export_data, indent=2, default=str, ensure_ascii=False))
        files.append(filepath)

    result = {"action": "export", "count": len(files), "output_dir": output_dir, "files": files}
    _append_audit_log({"action": "export", "user_id": user_id, "search": search, "count": len(files), "output_dir": output_dir})

    print(f"\nExported {len(files)} playlist(s) to {output_dir}/", file=sys.stderr)
    return result


def _format_audit_table(playlists: List[Dict[str, Any]], show_age: bool = False) -> str:
    """Render playlists as an ASCII table."""
    if not playlists:
        return "No playlists found."
    lines = []
    lines.append(f"Spotify Playlists ({len(playlists)} owned)")
    lines.append("=" * 90)
    if show_age:
        header = f"{'#':>3}  {'Name':<40} {'Tracks':>6}  {'Age Proxy':<12} {'Public':>6}"
    else:
        header = f"{'#':>3}  {'Name':<40} {'Tracks':>6}  {'Public':>6}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, pl in enumerate(playlists, 1):
        name = _truncate(pl["name"], 38)
        pub = "Yes" if pl.get("public") else "No"
        if show_age:
            age = pl.get("age_proxy", "")[:10] if pl.get("age_proxy") else "—"
            lines.append(f"{i:>3}  {name:<40} {pl['tracks']:>6}  {age:<12} {pub:>6}")
        else:
            lines.append(f"{i:>3}  {name:<40} {pl['tracks']:>6}  {pub:>6}")
    return "\n".join(lines)


def audit_spotify_playlists(
    client_id: str,
    client_secret: str,
    search: Optional[str] = None,
    sort_by: str = "name",
    as_json: bool = False,
) -> Dict[str, Any]:
    """List all user-owned playlists with optional filtering and sorting."""
    sp = _get_spotify_client(client_id, client_secret)
    user_id = sp.current_user()["id"]

    print(f"Fetching playlists for {user_id}...", file=sys.stderr)
    playlists = _list_all_playlists(sp, user_id, search)

    # Sort
    if sort_by == "tracks":
        playlists.sort(key=lambda p: p["tracks"], reverse=True)
    elif sort_by == "name":
        playlists.sort(key=lambda p: p["name"].lower())
    elif sort_by == "age":
        print("Fetching age proxies (this may take a moment)...", file=sys.stderr)
        for pl in playlists:
            pl["age_proxy"] = _get_playlist_age_proxy(sp, pl["id"])
        playlists.sort(key=lambda p: p.get("age_proxy") or "9999", reverse=True)

    result = {
        "action": "audit",
        "user_id": user_id,
        "search": search,
        "sort_by": sort_by,
        "count": len(playlists),
        "playlists": playlists,
    }

    _append_audit_log({"action": "audit", "user_id": user_id, "search": search, "count": len(playlists)})

    if as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(_format_audit_table(playlists, show_age=(sort_by == "age")))
        print(f"\n{len(playlists)} playlist(s) found.", file=sys.stderr)

    return result


def cleanup_spotify_playlists(
    pattern: str,
    client_id: str,
    client_secret: str,
    confirm: bool = False,
    max_remove: int = 0,
    as_json: bool = False,
) -> Dict[str, Any]:
    """Preview or execute removal of playlists matching a glob pattern."""
    sp = _get_spotify_client(client_id, client_secret)
    user_id = sp.current_user()["id"]

    print(f"Searching for playlists matching '{pattern}'...", file=sys.stderr)
    matched = _list_all_playlists(sp, user_id, pattern)

    if max_remove > 0:
        matched = matched[:max_remove]

    result = {
        "action": "cleanup_preview" if not confirm else "cleanup_execute",
        "user_id": user_id,
        "pattern": pattern,
        "matched": len(matched),
        "max_remove": max_remove,
        "playlists": matched,
        "removed": 0,
    }

    if not matched:
        print(f"No playlists matching '{pattern}'.", file=sys.stderr)
        _append_audit_log(result)
        return result

    # Always preview first
    print(f"\n{'WILL REMOVE' if confirm else 'DRY RUN — would remove'} {len(matched)} playlist(s):\n")
    for i, pl in enumerate(matched, 1):
        print(f"  {i}. {pl['name']} ({pl['tracks']} tracks)")

    if not confirm:
        print(f"\nTo execute, add --confirm (and optionally --max N for safety cap).", file=sys.stderr)
        _append_audit_log(result)
        return result

    # Execute removal
    print(f"\nRemoving {len(matched)} playlist(s)...", file=sys.stderr)
    ids = [pl["id"] for pl in matched]
    removed = _unfollow_playlists_batch(sp, ids)
    result["removed"] = removed
    print(f"  Removed {removed} of {len(matched)} playlist(s).", file=sys.stderr)

    _append_audit_log(result)

    if as_json:
        print(json.dumps(result, indent=2, default=str))

    return result


# ── Output Formatting ─────────────────────────────────────────────────────────

def format_now_playing(data: Dict[str, Any], verbose: bool = False) -> str:
    """Format now-playing data as a readable string."""
    lines = []
    lines.append("♫ NOW PLAYING on WRHV 88.7 FM (Classical WMHT)")
    lines.append("=" * 52)

    program = data.get("program")
    if program and program.get("name"):
        lines.append(f"Program:  {program['name']} ({program.get('start_time', '')}–{program.get('end_time', '')})")

    track = data.get("track")
    if not track:
        lines.append("\nNo track information available.")
        lines.append(f"\nCheck: {WMHT_PLAYLIST_URL}")
        return "\n".join(lines)

    lines.append("")
    lines.append(f"Composer: {track['composer']}")
    lines.append(f"Piece:    {track['track_name']}")
    if track["performers"]:
        lines.append(f"Performers: {track['performers']}")
    if track["duration"]:
        lines.append(f"Duration: {track['duration']}")

    if verbose:
        if track["album"]:
            lines.append(f"Album:    {track['album']}")
        if track["label"]:
            lines.append(f"Label:    {track['label']}")
        if track["catalog_number"]:
            lines.append(f"Catalog:  {track['catalog_number']}")

    # Links
    links = track.get("links", {})
    if links:
        lines.append("")
        lines.append("Listen:")
        if links.get("youtube"):
            lines.append(f"  YouTube:          {links['youtube']}")
        if links.get("spotify"):
            lines.append(f"  Spotify:          {links['spotify']}")
        if links.get("apple_music"):
            lines.append(f"  Apple Music:      {links['apple_music']}")
        if links.get("imslp"):
            lines.append(f"  IMSLP:            {links['imslp']}")
        if links.get("idagio"):
            lines.append(f"  IDAGIO:           {links['idagio']}")
        if links.get("internet_archive"):
            lines.append(f"  Internet Archive: {links['internet_archive']}")
        if links.get("musopen"):
            lines.append(f"  Musopen:          {links['musopen']}")

    lines.append("")
    lines.append(f"Stream live: {WMHT_STREAM_URL}")
    return "\n".join(lines)


def format_recent_tracks(tracks: List[Dict[str, Any]], verbose: bool = False) -> str:
    """Format recent tracks as an ASCII table."""
    if not tracks:
        return "No recent tracks found."

    lines = []
    lines.append(f"♫ WRHV 88.7 FM — Recent Tracks ({len(tracks)} shown)")
    lines.append("=" * 100)

    # Header
    if verbose:
        header = f"{'Time':<12} {'Composer':<22} {'Piece':<30} {'Performers':<25} {'Dur':>5}"
    else:
        header = f"{'Time':<12} {'Composer':<22} {'Piece':<40} {'Dur':>5}  Links"
    lines.append(header)
    lines.append("-" * len(header))

    for t in tracks:
        # Parse start time for display
        time_str = _format_time(t.get("start_time", ""))
        now_marker = " ♫" if t.get("is_now_playing") else ""

        composer = _truncate(t["composer"], 20)
        duration = t["duration"] or ""

        if verbose:
            piece = _truncate(t["track_name"], 28)
            performers = _truncate(t["performers"], 23)
            lines.append(f"{time_str:<12} {composer:<22} {piece:<30} {performers:<25} {duration:>5}{now_marker}")

            if t["album"]:
                lines.append(f"{'':>12} Album: {t['album']}")
            if t["label"]:
                lines.append(f"{'':>12} Label: {t['label']} | Cat: {t['catalog_number']}")

            links = t.get("links", {})
            if links:
                link_parts = []
                for name, url in links.items():
                    label = _LINK_LABELS.get(name, name)
                    link_parts.append(f"{label}: {url}")
                lines.append(f"{'':>12} {' | '.join(link_parts)}")
            lines.append("")
        else:
            piece = _truncate(t["track_name"], 38)
            yt = t.get("links", {}).get("youtube", "")
            yt_short = "YT" if yt else ""
            lines.append(f"{time_str:<12} {composer:<22} {piece:<40} {duration:>5}  {yt_short}{now_marker}")

    lines.append("")
    lines.append(f"Full playlist: {WMHT_PLAYLIST_URL}")
    lines.append(f"Stream live:   {WMHT_STREAM_URL}")
    return "\n".join(lines)


def format_markdown(tracks: List[Dict[str, Any]], now_playing: Optional[Dict] = None) -> str:
    """Format tracks as a Markdown report with clickable links."""
    lines = []
    now = datetime.now()
    lines.append(f"# WRHV 88.7 FM — Classical WMHT Playlist")
    lines.append(f"*Generated {now.strftime('%B %d, %Y at %I:%M %p')}*\n")

    # Now playing section
    if now_playing and now_playing.get("track"):
        t = now_playing["track"]
        prog = now_playing.get("program", {})
        lines.append("## ♫ Now Playing\n")
        lines.append(f"**{t['composer']}** — {t['track_name']}")
        if t["performers"]:
            lines.append(f"*{t['performers']}*")
        if prog and prog.get("name"):
            lines.append(f"Program: {prog['name']}")
        links = t.get("links", {})
        if links:
            link_parts = []
            if links.get("youtube"):
                link_parts.append(f"[YouTube]({links['youtube']})")
            if links.get("spotify"):
                link_parts.append(f"[Spotify]({links['spotify']})")
            if links.get("apple_music"):
                link_parts.append(f"[Apple Music]({links['apple_music']})")
            if links.get("imslp"):
                link_parts.append(f"[IMSLP]({links['imslp']})")
            if links.get("idagio"):
                link_parts.append(f"[IDAGIO]({links['idagio']})")
            if links.get("internet_archive"):
                link_parts.append(f"[Internet Archive]({links['internet_archive']})")
            if links.get("musopen"):
                link_parts.append(f"[Musopen]({links['musopen']})")
            lines.append(f"\n{' · '.join(link_parts)}")
        lines.append("")

    # Recent tracks table
    if tracks:
        lines.append("## Recent Tracks\n")
        lines.append("| Time | Composer | Piece | Performers | Duration | Listen |")
        lines.append("|------|----------|-------|------------|----------|--------|")

        for t in tracks:
            time_str = _format_time(t.get("start_time", ""))
            composer = t["composer"].replace("|", "\\|")
            piece = t["track_name"].replace("|", "\\|")
            performers = t["performers"].replace("|", "\\|") if t["performers"] else ""
            duration = t["duration"] or ""
            now_mark = " ♫" if t.get("is_now_playing") else ""

            # Build listen links
            links = t.get("links", {})
            link_parts = []
            if links.get("youtube"):
                link_parts.append(f"[YT]({links['youtube']})")
            if links.get("spotify"):
                link_parts.append(f"[Sp]({links['spotify']})")
            if links.get("apple_music"):
                link_parts.append(f"[AM]({links['apple_music']})")
            if links.get("imslp"):
                link_parts.append(f"[IMSLP]({links['imslp']})")
            if links.get("idagio"):
                link_parts.append(f"[ID]({links['idagio']})")
            if links.get("internet_archive"):
                link_parts.append(f"[IA]({links['internet_archive']})")
            if links.get("musopen"):
                link_parts.append(f"[MO]({links['musopen']})")

            listen = " ".join(link_parts)
            lines.append(f"| {time_str}{now_mark} | {composer} | {piece} | {performers} | {duration} | {listen} |")

        lines.append("")

    # Composer index
    if tracks:
        composers = {}
        for t in tracks:
            c = t["composer"]
            if c:
                if c not in composers:
                    composers[c] = []
                composers[c].append(t["track_name"])

        if composers:
            lines.append("## Composer Index\n")
            for composer in sorted(composers.keys()):
                pieces = composers[composer]
                lines.append(f"**{composer}** ({len(pieces)} piece{'s' if len(pieces) > 1 else ''})")
                for p in pieces:
                    lines.append(f"- {p}")
                lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"[Stream live]({WMHT_STREAM_URL}) · [Full playlist]({WMHT_PLAYLIST_URL})")
    lines.append(f"*Data: NPR Composer API · Station: WRHV 88.7 FM / WMHT-FM 89.1*")

    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_time(start_time: str) -> str:
    """Parse API timestamp into readable time string."""
    if not start_time:
        return ""
    # Formats seen: "02-18-2026 00:00:00" or "02/18/2026 00:00:00"
    for fmt in ("%m-%d-%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(start_time, fmt)
            return dt.strftime("%-I:%M %p")
        except ValueError:
            continue
    return start_time


def _truncate(s: str, maxlen: int) -> str:
    """Truncate string with ellipsis if needed."""
    if len(s) <= maxlen:
        return s
    return s[: maxlen - 1] + "…"


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="WRHV 88.7 FM (Classical WMHT) — now playing & recent tracks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s                                 What's playing now
  %(prog)s --recent 10                     Last 10 tracks
  %(prog)s --period today --markdown       Today's full playlist as Markdown
  %(prog)s --period week --markdown        Last 7 days as Markdown report
  %(prog)s --period month --search bach    All Bach from the last 30 days
  %(prog)s --date 2026-02-14               Valentine's Day playlist
  %(prog)s --verbose                       Full performer details
  %(prog)s --json                          Raw JSON output
  %(prog)s --spotify-rename "New Name"     Rename default playlist
  %(prog)s --spotify-playlist "Old" --spotify-rename "New"   Rename specific playlist
  %(prog)s --spotify-log-report            View playlist operation history
""",
    )
    parser.add_argument(
        "--now", action="store_true", default=False,
        help="Show what's playing now (default if no --recent)",
    )
    parser.add_argument(
        "--recent", type=int, metavar="N", default=0,
        help="Show last N tracks (1–100, default 20 if flag given without value)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show full details (album, label, catalog, all performers)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output raw JSON",
    )
    parser.add_argument(
        "--markdown", nargs="?", const="classical-playlist.md", metavar="FILE",
        help="Write Markdown report (default: classical-playlist.md)",
    )
    parser.add_argument(
        "--date", type=str, metavar="YYYY-MM-DD",
        help="Fetch tracks from a specific date (pages backward through full day)",
    )
    parser.add_argument(
        "--period", type=str, metavar="PERIOD",
        choices=["today", "yesterday", "week", "month"],
        help="Fetch tracks from a time period: today, yesterday, week, month",
    )
    parser.add_argument(
        "--search", type=str, metavar="QUERY",
        help="Search for a composer or piece in the fetched tracks",
    )
    parser.add_argument(
        "--sort", type=str, metavar="FIELD",
        choices=["time", "duration", "composer"],
        default="time",
        help="Sort by: time (default, newest first), duration (longest first), composer (A–Z)",
    )

    # Spotify integration
    parser.add_argument(
        "--spotify-playlist", type=str, metavar="NAME", nargs="?",
        const="Classical 88.7 FM",
        help="Create/append to a Spotify playlist (default name: 'Classical 88.7 FM')",
    )
    parser.add_argument(
        "--spotify-client-id", type=str,
        default=os.environ.get("SPOTIFY_CLIENT_ID", ""),
        help="Spotify app client ID (or set SPOTIFY_CLIENT_ID env var)",
    )
    parser.add_argument(
        "--spotify-client-secret", type=str,
        default=os.environ.get("SPOTIFY_CLIENT_SECRET", ""),
        help="Spotify app client secret (or set SPOTIFY_CLIENT_SECRET env var)",
    )
    parser.add_argument(
        "--spotify-rename", type=str, metavar="NEW_NAME", nargs="?", const=None,
        help="Rename a Spotify playlist. Renames the default 'Classical 88.7 FM' unless --spotify-playlist specifies the current name.",
    )
    parser.add_argument(
        "--spotify-description", type=str, metavar="DESC", default=None,
        help="New description when renaming a playlist (used with --spotify-rename)",
    )
    parser.add_argument(
        "--spotify-log-report", action="store_true",
        help="View the playlist operation log as a Markdown report",
    )

    # Spotify audit & cleanup
    parser.add_argument(
        "--spotify-audit", action="store_true",
        help="List all user-owned Spotify playlists (combine with --search, --sort, --json)",
    )
    parser.add_argument(
        "--spotify-export", type=str, metavar="DIR", nargs="?", const="spotify-export",
        help="Export matching playlists' tracks to JSON files in DIR (default: ./spotify-export/)",
    )
    parser.add_argument(
        "--spotify-cleanup", type=str, metavar="PATTERN", default=None,
        help="Preview removal of playlists matching glob pattern (dry run unless --confirm)",
    )
    parser.add_argument(
        "--confirm", action="store_true",
        help="Execute playlist removal (use with --spotify-cleanup)",
    )
    parser.add_argument(
        "--max", type=int, metavar="N", default=0,
        help="Safety cap: max playlists to remove per invocation (use with --spotify-cleanup)",
    )

    args = parser.parse_args()

    # ── Standalone Spotify modes (exit early) ────────────────────────────────

    # --spotify-log-report: render the JSONL log as Markdown and exit
    if args.spotify_log_report:
        report = format_playlist_log_report()
        print(report)
        return

    # --spotify-rename: rename an existing playlist and exit
    if args.spotify_rename is not None:
        if not args.spotify_client_id or not args.spotify_client_secret:
            print("Error: Spotify credentials required for --spotify-rename.", file=sys.stderr)
            print("  Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars.", file=sys.stderr)
            sys.exit(1)
        # The current name is either from --spotify-playlist or the default
        current_name = args.spotify_playlist if args.spotify_playlist else "Classical 88.7 FM"
        new_name = args.spotify_rename
        if not new_name:
            print("Error: --spotify-rename requires a new name.", file=sys.stderr)
            print("  Usage: --spotify-rename \"New Playlist Name\"", file=sys.stderr)
            sys.exit(1)
        result = rename_spotify_playlist(
            current_name=current_name,
            new_name=new_name,
            client_id=args.spotify_client_id,
            client_secret=args.spotify_client_secret,
            new_description=args.spotify_description,
        )
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        return

    # --spotify-export: export playlist tracks to JSON files and exit
    if args.spotify_export is not None:
        if not args.spotify_client_id or not args.spotify_client_secret:
            print("Error: Spotify credentials required for --spotify-export.", file=sys.stderr)
            print("  Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars.", file=sys.stderr)
            sys.exit(1)
        export_spotify_playlists(
            client_id=args.spotify_client_id,
            client_secret=args.spotify_client_secret,
            search=args.search,
            output_dir=args.spotify_export,
        )
        return

    # --spotify-audit: list all owned playlists and exit
    if args.spotify_audit:
        if not args.spotify_client_id or not args.spotify_client_secret:
            print("Error: Spotify credentials required for --spotify-audit.", file=sys.stderr)
            print("  Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars.", file=sys.stderr)
            sys.exit(1)
        sort_field = args.sort if args.sort in ("name", "tracks", "age") else "name"
        audit_spotify_playlists(
            client_id=args.spotify_client_id,
            client_secret=args.spotify_client_secret,
            search=args.search,
            sort_by=sort_field,
            as_json=args.json,
        )
        return

    # --spotify-cleanup: preview/execute playlist removal and exit
    if args.spotify_cleanup is not None:
        if not args.spotify_client_id or not args.spotify_client_secret:
            print("Error: Spotify credentials required for --spotify-cleanup.", file=sys.stderr)
            print("  Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars.", file=sys.stderr)
            sys.exit(1)
        cleanup_spotify_playlists(
            pattern=args.spotify_cleanup,
            client_id=args.spotify_client_id,
            client_secret=args.spotify_client_secret,
            confirm=args.confirm,
            max_remove=args.max,
            as_json=args.json,
        )
        return

    # ── Resolve date/period into a since/until range ─────────────────────────
    since = None
    until = None
    if args.date:
        try:
            day = datetime.strptime(args.date, "%Y-%m-%d")
            since = day
            until = day + timedelta(days=1)
        except ValueError:
            print(f"Error: invalid date format '{args.date}'. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
    elif args.period:
        now = datetime.now()
        if args.period == "today":
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif args.period == "yesterday":
            yesterday = now - timedelta(days=1)
            since = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            until = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif args.period == "week":
            since = now - timedelta(days=7)
        elif args.period == "month":
            since = now - timedelta(days=30)

    # Default: --now if no --recent, --date, or --period specified
    if args.recent == 0 and not args.now and since is None:
        args.now = True

    def _apply_sort(tracks):
        if args.sort == "duration":
            tracks.sort(key=lambda t: t.get("duration_ms") or 0, reverse=True)
        elif args.sort == "composer":
            tracks.sort(key=lambda t: t.get("composer", "").lower())
        # "time" is default order (newest first) — already returned that way
        return tracks

    # Helper: run Spotify playlist creation if requested
    def _maybe_spotify(tracks):
        if args.spotify_playlist is None:
            return
        if not args.spotify_client_id or not args.spotify_client_secret:
            print("Error: Spotify credentials required.", file=sys.stderr)
            print("  Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars,", file=sys.stderr)
            print("  or pass --spotify-client-id and --spotify-client-secret.", file=sys.stderr)
            sys.exit(1)
        if not tracks:
            print("No tracks to add to Spotify playlist.", file=sys.stderr)
            return
        result = create_spotify_playlist(
            tracks=tracks,
            playlist_name=args.spotify_playlist,
            client_id=args.spotify_client_id,
            client_secret=args.spotify_client_secret,
        )
        if args.json:
            print(json.dumps(result, indent=2, default=str))

    try:
        if since is not None:
            # Date/period mode — page through history
            label = args.date or args.period
            print(f"Fetching tracks for '{label}'...", file=sys.stderr)
            tracks = get_tracks_since(since, until)

            # Apply search filter if given
            if args.search:
                query = args.search.lower()
                tracks = [t for t in tracks if
                          query in t["composer"].lower() or
                          query in t["track_name"].lower() or
                          query in t["performers"].lower()]

            tracks = _apply_sort(tracks)
            _maybe_spotify(tracks)

            if args.json:
                print(json.dumps(tracks, indent=2))
                return

            if args.markdown is not None:
                md = format_markdown(tracks)
                outpath = args.markdown
                with open(outpath, "w") as f:
                    f.write(md)
                print(f"Wrote {len(tracks)} tracks to {outpath}")
                return

            print(format_recent_tracks(tracks, verbose=args.verbose))

        elif args.recent > 0:
            # Recent tracks mode
            tracks = get_recent_tracks(args.recent)

            # Apply search filter if given
            if args.search:
                query = args.search.lower()
                tracks = [t for t in tracks if
                          query in t["composer"].lower() or
                          query in t["track_name"].lower() or
                          query in t["performers"].lower()]

            tracks = _apply_sort(tracks)
            _maybe_spotify(tracks)
            now_data = None

            if args.json:
                print(json.dumps(tracks, indent=2))
                return

            if args.markdown is not None:
                try:
                    now_data = get_now_playing()
                except Exception:
                    pass
                md = format_markdown(tracks, now_data)
                outpath = args.markdown
                with open(outpath, "w") as f:
                    f.write(md)
                print(f"Wrote {len(tracks)} tracks to {outpath}")
                return

            print(format_recent_tracks(tracks, verbose=args.verbose))

        else:
            # Now-playing mode
            data = get_now_playing()

            if args.spotify_playlist is not None:
                # For now-playing mode with Spotify, grab recent tracks too
                tracks = get_recent_tracks(20)
                _maybe_spotify(tracks)

            if args.json:
                print(json.dumps(data, indent=2))
                return

            if args.markdown is not None:
                tracks = get_recent_tracks(20)
                md = format_markdown(tracks, data)
                outpath = args.markdown
                with open(outpath, "w") as f:
                    f.write(md)
                print(f"Wrote playlist to {outpath}")
                return

            print(format_now_playing(data, verbose=args.verbose))

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to NPR Composer API.", file=sys.stderr)
        print(f"Fallback: check {WMHT_PLAYLIST_URL}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"Error: API returned {e.response.status_code}", file=sys.stderr)
        print(f"Fallback: check {WMHT_PLAYLIST_URL}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
