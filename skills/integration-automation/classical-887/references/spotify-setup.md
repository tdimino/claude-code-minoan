# Spotify Developer App Setup

Complete setup guide for the Classical 887 Spotify playlist integration.

## Prerequisites

- Spotify Premium account (required for Dev Mode apps since Feb 2026)
- `spotipy` Python package: `uv pip install --system spotipy`

## Step 1: Create a Spotify Developer App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **Create App**
4. Fill in the form:
   - **App name:** `Classical 887` (or any name you prefer)
   - **App description:** `Playlist creation from WRHV 88.7 FM`
   - **Redirect URI:** `http://127.0.0.1:8888/callback`
   - **APIs:** check **Web API**
5. Click **Save**
6. Go to your app's **Settings** page
7. Copy the **Client ID** and **Client Secret**

> **Important:** The redirect URI must be exactly `http://127.0.0.1:8888/callback`. Spotify deprecated `localhost` as of Feb 2026—use `127.0.0.1` instead.

## Step 2: Add Users to the Allowlist

Since Feb 11, 2026, Spotify Dev Mode apps require explicit user allowlisting:

1. In the [Developer Dashboard](https://developer.spotify.com/dashboard), open your app
2. Go to **User Management**
3. Click **Add User**
4. Enter:
   - **Full name:** Your name (e.g., `Tom di Mino`)
   - **Email:** Your Spotify account email (e.g., `contact@tomdimino.com`)
5. Click **Save**

### Dev Mode Limits (Feb 2026+)

| Limit | Value |
|-------|-------|
| Max allowlisted users | 5 |
| Max client IDs per developer | 1 |
| Search results per query | 10 (was 50) |
| Account requirement | Spotify Premium |

## Step 3: Set Environment Variables

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export SPOTIFY_CLIENT_ID="your-client-id-here"
export SPOTIFY_CLIENT_SECRET="your-client-secret-here"
```

Apply changes:

```bash
source ~/.zshrc
```

Alternatively, pass credentials directly via CLI flags:

```bash
python3 ~/.claude/skills/classical-887/scripts/classical_887.py \
  --recent 10 \
  --spotify-playlist \
  --spotify-client-id YOUR_ID \
  --spotify-client-secret YOUR_SECRET
```

## Step 4: First Run (OAuth Authorization)

On first use of `--spotify-playlist`, a browser window opens for Spotify login:

```bash
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --recent 5 --spotify-playlist
```

1. Browser opens Spotify authorization page
2. Click **Agree** to grant playlist permissions
3. Browser redirects to `http://127.0.0.1:8888/callback`
4. Token is cached at `~/.claude/skills/classical-887/.spotify-cache`

Subsequent runs reuse the cached token automatically (auto-refreshes when expired).

## Usage Examples

```bash
# Add recent tracks to the default "Classical 88.7 FM" playlist
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --recent 10 --spotify-playlist

# Add today's full playlist
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period today --spotify-playlist

# Add yesterday's tracks
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period yesterday --spotify-playlist

# Custom playlist name
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period week --spotify-playlist "This Week on 88.7"

# Only Bach from the last week
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --period week --search bach --spotify-playlist "Bach on 88.7"

# Specific date
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --date 2026-02-14 --spotify-playlist "Valentine's Classical"
```

## How It Works

### Persistent Playlist

The `--spotify-playlist` flag creates a playlist with the given name (default: `Classical 88.7 FM`). On subsequent runs, it **finds the existing playlist by name and appends** new tracks rather than creating a duplicate. The playlist description is updated with the current date.

### Classical Music Search Strategy

Finding classical music on Spotify is tricky—the same piece appears under many artist/album combinations. The script uses a two-pass search:

1. **Full query:** `{composer} {full track name}` (e.g., `Beethoven Symphony No. 5, Mvt. 1`)
2. **Work name only:** `{composer} {work name without movement}` (e.g., `Beethoven Symphony No. 5`)

For each query, results where the Spotify artist name contains the composer name are preferred over generic matches.

### Direct API Calls (Feb 2026 Safe)

The script uses `spotipy` for OAuth token management and search, but makes **direct HTTP requests** for playlist operations. This bypasses `spotipy` methods that still call endpoints removed in Spotify's Feb 2026 Dev Mode migration:

| Operation | Removed Endpoint | Safe Endpoint Used |
|-----------|------------------|--------------------|
| List playlists | `GET /users/{id}/playlists` | `GET /me/playlists` |
| Create playlist | `POST /users/{id}/playlists` | `POST /me/playlists` |
| Add tracks | `POST /playlists/{id}/tracks` | `POST /playlists/{id}/items` |

### Required OAuth Scopes

| Scope | Purpose |
|-------|---------|
| `playlist-read-private` | Find existing playlists by name |
| `playlist-modify-public` | Create/modify public playlists |
| `playlist-modify-private` | Create/modify private playlists |

## Troubleshooting

### "Invalid redirect URL"

Ensure the redirect URI in your Spotify app settings is exactly `http://127.0.0.1:8888/callback` (not `localhost`).

### "Insufficient client scope" (403)

Delete the cached token and re-authorize:

```bash
rm ~/.claude/skills/classical-887/.spotify-cache
python3 ~/.claude/skills/classical-887/scripts/classical_887.py --recent 5 --spotify-playlist
```

### "User not registered in the Developer Dashboard"

Add your Spotify account email to the app's User Management page in the [Developer Dashboard](https://developer.spotify.com/dashboard).

### Token expired / auth errors

The cached token auto-refreshes, but if issues persist:

```bash
rm ~/.claude/skills/classical-887/.spotify-cache
```

Then re-run any `--spotify-playlist` command to re-authorize.
