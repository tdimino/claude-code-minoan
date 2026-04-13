# disc-forge gotchas — the full failure-mode inventory

Every one of these cost turns the first time the author tried to burn an audio CD on an M4 Max running Sequoia. Each entry explains *why* so the rule generalizes to future drives, macOS versions, and source libraries.

## 1. SMB is not reachable over Tailscale

**Symptom:** `open smb://mac-mini-ts/...` silently fails. `osascript -e 'mount volume "smb://..."'` returns error `-5016`.

**Cause:** macOS's File Sharing (smbd) only binds to the LAN interface, not the Tailscale `utun` interface. `mac-mini-ts` resolves to a Tailscale IP (`100.x.y.z`), and port 445 is actively refused on that IP. Only port 22 (SSH) works over Tailscale. Verify with:

```bash
nc -zv $(ssh -G mac-mini-ts | awk '/^hostname/{print $2}') 22 445
```

**Rule:** Never attempt SMB for Hoodrat HDD. Use SSH as the transport. `stage_tracks.py` does this via tar-over-SSH.

## 2. Apple's bundled `rsync` splits remote paths on spaces

**Symptom:** `rsync` errors like `rsync: unrecognized option --info=progress2` or `rsync(NNN): error: /Volumes/Hoodrat: (l)stat: No such file or directory` followed by the path fragmented into separate tokens.

**Cause:** macOS ships `openrsync 2.6.9` (Apple's fork) as `/usr/bin/rsync`. It is NOT GNU rsync 3.x. When given `mac-mini-ts:"/Volumes/Hoodrat HDD/..."`, the remote shell expansion leaks quoting and openrsync sees the path as multiple unrelated arguments.

**Rule:** For any Hoodrat HDD path (all of which have spaces), use **tar-over-SSH** instead:

```bash
ssh mac-mini-ts 'cd "/Volumes/Hoodrat HDD/Musica/ALBUM/" && tar cf - *.mp3' | tar xf - -C ./local-staging/
```

The quoting only has to survive one shell hop (the outer single-quoted ssh command), and tar archives with flat basenames.

`stage_tracks.py` encapsulates this. Alternative: install GNU rsync 3.x from Homebrew (`brew install rsync`) and use `--protect-args` / `-s`.

## 3. cdrdao 1.2.6 rejects MP3 and AIFF input

**Symptom:** cdrdao refuses to read a TOC file where `AUDIOFILE` references an MP3, or silently treats it as raw PCM.

**Cause:** The Homebrew cdrdao binary contains the literal string `"AIFF and MP3 not supported by cdrdao"`. Despite `libmad` being listed as a dependency (probably for a non-write codepath), the TOC format parser only accepts WAV/raw PCM files.

**Rule:** Always convert to WAV (44.1 kHz / 16-bit / stereo PCM) before building a cdrdao TOC. `convert_to_wav.py` does this with ffmpeg:

```bash
ffmpeg -i input.mp3 -ar 44100 -ac 2 -sample_fmt s16 -c:a pcm_s16le output.wav
```

**Alternative path that skips WAV:** Burn.app 3.1.9 handles MP3 natively (its bundled ffmpeg does the PCM conversion internally). See `burn-app-fallback.md`. cdrdao is preferred because it's scriptable.

## 4. "Unsupported" in `drutil` is not actually unsupported

**Symptom:** `drutil list` reports the USB burner as `SupportLevel: Unsupported`. Finder's "Burn to Disc" does nothing. Music.app can't see the drive.

**Cause:** Apple's DiscRecording framework maintains a whitelist of validated drive vendor/product IDs. Modern macOS increasingly drops third-party drives from that list. All the GUI burn paths (Finder, Music.app, Burn.app) route through DiscRecording and inherit this gating.

**cdrdao bypasses DiscRecording entirely.** It talks to the drive via IOKit's SCSI Architecture Model using the `IOCompactDiscServices` / `IODVDServices` nodes and sends MMC commands directly. It doesn't care about Apple's whitelist. Verify with:

```bash
cdrdao drive-info
# Should report "CD-TEXT writing is supported." and a driver line.
```

**Rule:** Treat the drutil "Unsupported" label as informational, not blocking. `preflight.py` surfaces it as a warning. The ASUS SDRW-08U9M-U is a known-working example despite the label.

## 5. Finder and Music.app burn-to-disc are broken on Sequoia

**Symptom:** Right-click → Burn to Disc does nothing in Finder. Music.app offers no Burn Playlist to Disc menu.

**Cause:** Apple removed the feature. Multiple Apple Support pages for macOS Sequoia 15.x confirm Music.app no longer supports burning audio CDs, and Apple Community threads confirm Finder's burn dispatcher is broken on Sequoia.

**Rule:** Don't fall back to GUI Apple tools. The realistic free paths on Sequoia are cdrdao (this skill) and Burn.app (the `burn-app-fallback.md` reference).

## 6. `open -a Burn` fails immediately after install

**Symptom:** After moving Burn.app into /Applications, `open -a Burn` returns `Unable to find application named 'Burn'`.

**Cause:** LaunchServices hasn't reindexed yet. macOS caches the app name → bundle-path mapping and doesn't pick up newly installed apps until a rescan.

**Rule:** Use the full path right after install:

```bash
open /Applications/Burn.app
# or force a LaunchServices rescan first:
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/Burn.app
```

## 7. Hoodrat HDD albums often have duplicate formats

**Symptom:** A 26-track album appears as 52 files in Finder. `check_duration.py` reports double the expected runtime.

**Cause:** Many Hoodrat HDD albums were copied from Windows-era media libraries that kept both MP3 and WMA versions, or from iTunes-era libraries that kept both MP3 and M4A. The duplicates share track numbers and filenames up to the extension.

**Rule:** Always filter to a single format at stage time. `stage_tracks.py --format mp3` is the default. `check_duration.py` also prints a format histogram so leftover duplicates surface loudly.

## 8. Preflight must verify a blank writable disc

**Symptom:** cdrdao writes to a disc that already has content, corrupts it, or refuses mid-burn.

**Cause:** `drutil status` can report multiple states: `blank`, `appendable`, `overwritable`, `Media Is Busy`, `Media Is Not Present`. Only `blank` + `writable` is safe for our Disc-at-Once audio CD workflow.

**Rule:** `preflight.py` requires `Writability: blank` before proceeding. Don't skip this check — silently burning over a non-blank disc is the fastest way to make a coaster.

## 9. CD-Text metadata comes from source files, not WAVs

**Symptom:** CD-Text writes blank or wrong values to the disc.

**Cause:** PCM WAV has no tagging container. The metadata lives in the ID3v2 chunk of the original MP3 (or equivalent for FLAC/M4A/etc). If `build_toc.py` reads tags from the WAV instead of the original, it gets nothing.

**Rule:** `build_toc.py` reads tags from `--source-dir` (the original MP3s), not `--wav-dir`. Keep the original staging dir around through the TOC build step even if you'll delete it later.

## 10. Burn speed: moderate beats maximum on cheap media

**Symptom:** Burn completes but disc won't play in older car stereos, or burn fails mid-write with BurnProof recoveries that eventually give up.

**Cause:** High write speeds (24x+) stress both the drive's buffer management and the media's dye layer. Cheap spindle CD-Rs are especially prone to burn artifacts at max speed.

**Rule:** Default to 16x. Drop to 10x if you're burning bulk-bin media or if you're getting weird playback issues on old stereos. The ~3 minutes saved at 24x isn't worth a coaster.

## 11. `drutil status` race after `cdrdao drive-info`

**Symptom:** Preflight reports `media is not blank` even though a brand-new CD-R is in the drive. Running `drutil status` manually from the shell a moment later shows `Writability: blank, writable` as expected.

**Cause:** `cdrdao drive-info` holds an IOKit SCSI passthrough session on the drive. For ~1–2 seconds after cdrdao exits, `drutil status` returns a truncated report with no `Writability:` line at all — so any downstream check for `"blank" in writability_line` fails closed.

**Rule:** `preflight.py`'s `check_blank_media()` retries `drutil status` up to 6 times at 0.5 s intervals, breaking as soon as the `Writability:` line appears. Don't remove the retry loop — the failure mode is invisible to anyone who runs `drutil` interactively because the drive has already released by then.
