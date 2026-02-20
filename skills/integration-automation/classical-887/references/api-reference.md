# NPR Composer API Reference

NPR Composer API powers playlist widgets for NPR member stations. WMHT uses it for their Classical WMHT playlist at `classicalwmht.org/playlist`. Fully public, no authentication required.

## Station

| Field | Value |
|-------|-------|
| Station | WRHV 88.7 FM (Classical WMHT) |
| Simulcast | WMHT-FM 89.1 (Schenectady, NY) |
| UCS ID | `51892578e1c81d34d1474a5d` |
| Stream | `https://wmht.org/classical/` |
| Playlist | `https://classicalwmht.org/playlist` |

## Base URL

```
https://api.composer.nprstations.org/v1
```

## Endpoints

| Endpoint | URL | Description |
|----------|-----|-------------|
| Now Playing | `/widget/{ucs}/now?format=json` | Current track + program info |
| Recent Tracks | `/widget/{ucs}/tracks?format=json&limit={n}` | Recently played (1–100) |
| Day Schedule | `/widget/{ucs}/day?format=json` | Today's program schedule |

### Query Parameters (tracks endpoint)

| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Number of tracks (1, 5, 10, 20, 50, 100) |
| `format` | string | `json` (required) |

## Now Playing Response

```json
{
  "onNow": {
    "program": {
      "name": "Classical WMHT",
      "program_format": "Classical",
      "program_id": "677ef89f9ea18c2245c61375"
    },
    "start_time": "00:00",
    "end_time": "06:00",
    "song": {
      "trackName": "Impromptus, D.899/3 G-Flat",
      "composerName": "Franz Schubert",
      "artistName": "John Novacek, piano",
      "soloists": "John Novacek, piano",
      "ensembles": "",
      "conductor": "",
      "collectionName": "",
      "catalogNumber": "3007",
      "copyright": "FOURWINDS",
      "_duration": 361000,
      "_start_time": "02-18-2026 00:00:00",
      "_date": "2/18/2026",
      "_start": "0:00:00"
    }
  }
}
```

## Tracks Response

```json
{
  "onNow": { "song": { ... } },
  "tracklist": {
    "results": [
      {
        "song": {
          "trackName": "Piano Trio 1 D Min, Op.49 (1839)",
          "composerName": "Felix Mendelssohn",
          "artistName": "Yo Yo Ma-Cello",
          "soloists": "Yo Yo Ma-Cello",
          "ensembles": "",
          "conductor": "Perlman, Itzhak-violin",
          "collectionName": "Mendelssohn Piano Trios",
          "catalogNumber": "52192",
          "copyright": "Sony",
          "_duration": 1878000,
          "_start_time": "02/17/2026 23:28:42",
          "_date": "2/17/2026"
        },
        "song_start_time": "02-17-2026 23:28:42",
        "program_name": ""
      }
    ]
  }
}
```

## Song Fields

| Field | Type | Description |
|-------|------|-------------|
| `trackName` | string | Piece name (may include opus/movement) |
| `composerName` | string | Composer full name |
| `artistName` | string | Primary performer |
| `soloists` | string | Soloist(s) with instrument |
| `ensembles` | string | Ensemble/orchestra name |
| `conductor` | string | Conductor (sometimes contains soloist info) |
| `collectionName` | string | Album name |
| `catalogNumber` | string | Label catalog number |
| `copyright` | string | Record label |
| `_duration` | int | Duration in milliseconds |
| `_start_time` | string | Airtime: `"MM-DD-YYYY HH:MM:SS"` or `"MM/DD/YYYY HH:MM:SS"` |
| `_date` | string | Date: `"M/D/YYYY"` |
| `_start` | string | Time of day: `"H:MM:SS"` |
| `imageURL` | string | Album art URL (usually empty) |

## Search URL Templates

For linking to performances and scores:

| Service | URL Template | Abbrev |
|---------|-------------|--------|
| YouTube | `https://www.youtube.com/results?search_query={composer}+{track}` | YT |
| Spotify | `https://open.spotify.com/search/{composer}+{track}` | Sp |
| Apple Music | `https://music.apple.com/us/search?term={composer}+{track}` | AM |
| IMSLP | `https://imslp.org/index.php?search={composer}+{work_name}` | IMSLP |
| IDAGIO | `https://app.idagio.com/search?q={composer}+{track}` | ID |
| Internet Archive | `https://archive.org/search?query={composer}+{track}&and[]=mediatype:audio` | IA |
| Musopen | `https://musopen.org/music/?q={composer}+{track}` | MO |

All values should be URL-encoded via `urllib.parse.quote_plus()`.

## Notes

- The API is unauthenticated and public but undocumented
- UCS ID could change if WMHT reconfigures their widget
- Timestamp formats are inconsistent (both `/` and `-` separators observed)
- `conductor` field sometimes contains soloist info instead of conductor name
- `_duration` of 0 means duration unknown
- Fallback: `classicalwmht.org/playlist` renders the same data in a browser
