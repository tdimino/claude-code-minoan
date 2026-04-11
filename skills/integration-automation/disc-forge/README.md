# disc-forge

Automated Red Book audio CD burning on macOS via [cdrdao](https://cdrdao.sourceforge.net/). Turns *"burn the BSG Season 1 soundtrack to a CD"* into a single command.

```bash
python3 ~/.claude/skills/disc-forge/scripts/burn_audio_cd.py \
  --source ~/Music/BSG-S1-OST \
  --name BSG-S1
```

One command runs the full pipeline — preflight → stage → duration check → parallel WAV conversion → TOC build with CD-Text pulled from ID3 tags → cdrdao write at 16x → cleanup → eject. ~5–7 minutes for an 80-minute disc.

## Why this exists

Burning an audio CD on a modern Mac should be easy. It isn't:

- **macOS Sequoia killed Music.app burning** and broke Finder's right-click "Burn to Disc."
- **Apple's DiscRecording framework** (which Finder, Music.app, and Burn.app all depend on) marks most third-party USB burners as "Unsupported," even when they work perfectly fine at the MMC/SCSI level.
- **cdrdao** bypasses DiscRecording entirely and talks to the drive via IOKit, so "Unsupported" drives burn just fine — but cdrdao is a CLI, wants a TOC file, rejects MP3 input, and requires CD-Text to be spelled out by hand.
- **Apple's bundled `rsync`** (`openrsync 2.6.9`) splits remote paths on spaces, so pulling albums from a remote music server over SSH with stock tooling is broken out of the box.

disc-forge is a six-script pipeline that handles every one of these and turns the whole thing into one command. The skill encodes the traps in `references/gotchas.md` so they don't have to be rediscovered.

## What it does

| Stage | Script | What it does |
|---|---|---|
| 1 | `preflight.py` | Verifies `cdrdao` + `ffmpeg`, drive reachable, **blank writable disc inserted**. Surfaces the drutil "Unsupported" label as an informational note (not a blocker). |
| 2 | `stage_tracks.py` | Pulls source files. Remote sources (`host:/path`) use **tar-over-SSH**, not rsync. Local sources use `cp`. Filters to one audio format (default `mp3`) to dedupe MP3+WMA / MP3+M4A siblings common in legacy libraries. |
| 3 | `check_duration.py` | Totals runtime via ffprobe. Aborts if the album overruns 80-min Red Book capacity. Prints a format histogram so leftover duplicates show up. |
| 4 | `convert_to_wav.py` | Parallel ffmpeg MP3→44.1 kHz/16-bit/stereo PCM (the exact Red Book format). Idempotent — skips WAVs already fresh. |
| 5 | `build_toc.py` | Generates a cdrdao TOC file with `CD_TEXT` blocks. Pulls title/artist/album from the **original source file's ID3 tags** (WAVs have no tagging container). Gapless by default; `--gaps` inserts 2-sec spacers for pop albums. |
| 6 | `cdrdao write` | The actual burn. `--speed 16 --eject` by default. Streams progress. Ctrl-C aborts safely via SIGTERM. |
| 7 | cleanup | Deletes `<name>-wav/` on success. Keeps `<name>/` MP3 staging for re-burns. |

## Install

### Dependencies

```bash
brew install cdrdao ffmpeg
```

- **cdrdao** — the actual burn engine. Bypasses Apple's DiscRecording framework, works with any MMC-compliant USB burner including drives that `drutil list` labels "Unsupported."
- **ffmpeg / ffprobe** — format conversion + tag reading.

You also need a USB CD burner. The skill has been tested on the **ASUS SDRW-08U9M-U** (external slim drive, works despite macOS labeling it "Unsupported") on macOS Sequoia 15.6, Apple Silicon (M4 Max). Any generic MMC-compliant USB drive should behave the same.

### Skill files

If you're cloning `claude-code-minoan`:

```bash
cp -r skills/integration-automation/disc-forge ~/.claude/skills/
```

Or symlink:

```bash
ln -s "$(pwd)/skills/integration-automation/disc-forge" ~/.claude/skills/disc-forge
```

## Usage

### Burn a full album from a local directory

```bash
python3 ~/.claude/skills/disc-forge/scripts/burn_audio_cd.py \
  --source ~/Music/BSG-S1-OST \
  --name BSG-S1
```

### Burn a full album from a remote music server over SSH

```bash
python3 ~/.claude/skills/disc-forge/scripts/burn_audio_cd.py \
  --source "music-server:/Volumes/Music/BSG Season 1 - OST/" \
  --name BSG-S1
```

`music-server` can be any `~/.ssh/config` alias. The script detects the `host:/path` form and switches to tar-over-SSH automatically, handling paths with spaces correctly.

### Dry-run the pipeline without burning

```bash
python3 ~/.claude/skills/disc-forge/scripts/burn_audio_cd.py \
  --source ~/Music/BSG-S1-OST \
  --name BSG-S1 \
  --dry-run
```

Runs every stage through TOC generation, prints the exact `cdrdao write` command you'd run next, and prints `cdrdao show-toc` so you can validate the TOC before committing to a disc.

### Pop album with 2-second gaps

Default behavior is gapless (right for OSTs, film scores, live albums, DJ mixes). For traditional pop albums, pass `--gaps`:

```bash
python3 ~/.claude/skills/disc-forge/scripts/burn_audio_cd.py \
  --source ~/Music/DarkSideOfTheMoon \
  --name DSOTM \
  --gaps
```

### Cherry-picked mixtape

Stage tracks manually into a single folder first, then point the orchestrator at it. Use numeric prefixes to force playback order:

```bash
mkdir -p ~/burn-staging/road-trip
cp ~/Music/BladeRunner/01\ Main\ Titles.mp3            ~/burn-staging/road-trip/01_main-titles.mp3
cp ~/Music/Inception/01\ Half\ Remembered\ Dream.mp3  ~/burn-staging/road-trip/02_half-remembered-dream.mp3
# ... more tracks ...
python3 ~/.claude/skills/disc-forge/scripts/burn_audio_cd.py \
  --source ~/burn-staging/road-trip \
  --name road-trip
```

Track order follows `sorted()` on filenames. CD-Text for each track comes from that track's own ID3 tags — so a mixtape ends up with correct per-track artist/title metadata on the disc.

## Flags

| Flag | Default | Description |
|---|---|---|
| `--source PATH` | required | Local directory or `host:/path` for SSH |
| `--name NAME` | required | Staging subdir name (and burn job name) |
| `--speed N` | 16 | cdrdao write speed multiplier |
| `--gaps` | off | Insert 2-second gaps between tracks (pop albums) |
| `--dry-run` | off | Run everything through TOC generation, skip cdrdao write |
| `--keep-wavs` | off | Preserve intermediate WAV staging dir after burn |
| `--ceiling N` | 80 | CD capacity in minutes (use 74 for older media) |
| `--format EXT` | mp3 | Source audio format filter (dedupes MP3+WMA siblings) |

## Scripts

All six scripts are independently usable and accept `--help`:

```
preflight.py        # Environment check: cdrdao, ffmpeg, drive, blank disc
stage_tracks.py     # Local cp or tar-over-SSH, with format filter
check_duration.py   # Runtime totals + 80-min fit check + format histogram
convert_to_wav.py   # Parallel ffmpeg → 44.1kHz/16/stereo PCM
build_toc.py        # cdrdao TOC generator with CD-Text from ID3 tags
burn_audio_cd.py    # Master orchestrator (chains the above)
```

## Supported input formats

`stage_tracks.py` can stage any of: `mp3`, `flac`, `wav`, `aiff`, `m4a`, `ogg` (pass `--format` to pick one). `convert_to_wav.py` can transcode any format ffmpeg reads, so the effective input list is essentially everything.

## Fallback: Burn.app

If cdrdao ever refuses a drive, **Burn 3.1.9** (`burn-osx.sourceforge.io`) is a free GUI fallback. Burn uses DiscRecording so it inherits the "Unsupported" gating, but it's been known to work on drives that drutil flags. See `references/burn-app-fallback.md` for the click sequence.

## What's not in scope

- **MP3 data CDs** — different tool chain (`drutil burn` + filesystem image). Might land in v2.
- **DVD burning** — audio or video.
- **CD ripping** — use [XLD](https://tmkk.undo.jp/xld/) for that.
- **Multi-session discs, DDP mastering** — overkill for this use case.

## Credits

- [cdrdao](https://cdrdao.sourceforge.net/) by Andreas Mueller — the actual burn engine, the only reason macOS audio CD burning still works in 2026.
- [Burn 3.1.9](https://burn-osx.sourceforge.io/) by kiwifruitware — documented as the GUI fallback.
- [ffmpeg](https://ffmpeg.org/) — format conversion and ID3 tag reading.

Battlestar Galactica Season One OST by Bear McCreary is used as the running example throughout this skill because it's 73 minutes of gapless orchestral science fiction that happens to fit perfectly on a single 80-minute disc with 6 minutes of headroom. Your car stereo deserves it.
