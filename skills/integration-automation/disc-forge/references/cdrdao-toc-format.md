# cdrdao TOC format — just enough to debug `build_toc.py` output

The cdrdao TOC format is a text file describing the layout of a CD for burning. `build_toc.py` generates these programmatically, but when something goes wrong you sometimes need to edit by hand or build a minimal test case.

## Minimal audio CD TOC

```
CD_DA

TRACK AUDIO
AUDIOFILE "/path/to/track1.wav" 0

TRACK AUDIO
AUDIOFILE "/path/to/track2.wav" 0
```

- `CD_DA` — tells cdrdao this is a Red Book audio CD (not a data disc)
- `TRACK AUDIO` — start of a new audio track
- `AUDIOFILE "path" 0` — source WAV (44.1 kHz / 16-bit / stereo PCM) and start offset in samples

## With CD-Text

Add album-level CD_TEXT after the `CD_DA` header, and per-track CD_TEXT inside each `TRACK AUDIO` block:

```
CD_DA

CD_TEXT {
  LANGUAGE_MAP { 0: EN }
  LANGUAGE 0 {
    TITLE "Album Title Here"
    PERFORMER "Album Artist Here"
  }
}

TRACK AUDIO
CD_TEXT {
  LANGUAGE 0 {
    TITLE "Track 1 Title"
    PERFORMER "Track 1 Artist"
  }
}
AUDIOFILE "/path/to/track1.wav" 0
```

- `LANGUAGE_MAP { 0: EN }` declares language slot 0 = English. Goes at the CD level only.
- Subsequent `LANGUAGE 0 { ... }` blocks use slot 0. Each track gets its own.
- Supported fields: `TITLE`, `PERFORMER`, `SONGWRITER`, `COMPOSER`, `ARRANGER`, `MESSAGE`, `ISRC`, `DISC_ID`, `UPC_EAN`.

## Pregap semantics

- **Track 1 always gets a 2-second pregap** per Red Book spec. cdrdao inserts this automatically — don't specify it.
- **Tracks 2–N default to no gap** (gapless). Right for film scores, live albums, DJ mixes.
- **To insert 2-second gaps** between tracks (traditional pop album style), add `PREGAP 00:02:00` inside each `TRACK AUDIO` block after the first:

```
TRACK AUDIO
PREGAP 00:02:00
CD_TEXT { ... }
AUDIOFILE "/path/to/track2.wav" 0
```

`build_toc.py --gaps` does this automatically.

## Character escaping

Inside CD_TEXT string values (double-quoted):

- `\\` for a literal backslash
- `\"` for a literal double-quote

`build_toc.py` does this via `escape_cdtext()`. If you see a parse error mentioning quote mismatch, check for an unescaped `"` in a track title.

## Validate without burning

```bash
cdrdao show-toc /path/to/file.toc
```

Parses the TOC, computes the exact disc layout, and prints per-track sector ranges. Run this before every burn to catch malformed TOCs, missing WAVs, or over-capacity situations. A clean validation ends with a final `TRACK NN` block listing its `END` sample count and exits 0.

## Common errors and fixes

| Error | Meaning | Fix |
|---|---|---|
| `ERROR: Cannot open audio file` | WAV path in AUDIOFILE doesn't exist or isn't readable | Verify the path; check that `convert_to_wav.py` ran successfully |
| `ERROR: Audio file ... is not a valid audio file` | File is not 44.1 kHz / 16-bit / stereo PCM | Re-run `convert_to_wav.py` with the exact ffmpeg flags |
| `ERROR: Expected "CD_DA" or "CD_ROM*"` | Missing / misspelled header | Top of the TOC must be `CD_DA` (no leading whitespace) |
| `ERROR: Syntax error at line N` | Unescaped quote or bad brace | Check that line; most common cause is a `"` in an album/track title |
| Burn starts but no CD-Text on the disc | Drive supports CD-Text but the burner driver doesn't use the TOC's CD_TEXT blocks | Verify with `cdrdao drive-info`; should say "CD-TEXT writing is supported." |
