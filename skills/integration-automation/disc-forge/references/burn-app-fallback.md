# Burn.app fallback — when cdrdao won't cooperate

cdrdao is the primary burn engine for disc-forge because it's scriptable and bypasses macOS's DiscRecording framework gating. But if cdrdao fails to detect the drive, refuses to write, or hangs mid-burn, Burn.app 3.1.9 is a proven fallback that uses a different code path entirely.

## When to use this fallback

- `cdrdao drive-info` hangs or errors
- `cdrdao write` fails with SCSI errors despite `preflight.py` passing
- Need to visually preview the track layout before committing
- Want to burn a mix of MP3s without the WAV-conversion detour (Burn.app handles MP3 natively via bundled ffmpeg)

## Install location

Already installed at `/Applications/Burn.app` (version 3.1.9, universal arm64, signed by `TeamIdentifier 5M4D5N9TXW` / `com.kiwifruitware.Burn`). If missing, download from `https://burn-osx.sourceforge.io/`.

## Launching

```bash
open /Applications/Burn.app
```

**Not** `open -a Burn` — LaunchServices may not have indexed the app, especially right after install. Use the full path, or force a rescan first:

```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/Burn.app
open -a Burn
```

## Click sequence for a Red Book audio CD

1. **Top dropdown → Audio** (the skill's scope; other tabs are Data / Video / Copy).
2. **Segmented control → Audio-CD** (not MP3-CD — MP3-CD produces a data disc with MP3 files on it, which plays only in modern car stereos).
3. **Drag MP3s from Finder** into Burn's track list area. Burn auto-converts MP3/FLAC/ALAC/AAC to 16-bit/44.1kHz PCM internally via its bundled ffmpeg — no manual WAV conversion needed for this path.
4. **⌘I** to open the Inspector. Toggle **CD-Text** ON; album and artist auto-populate from ID3 tags on the first track.
5. **Pregap**: Leave at 2 seconds for normal albums; set to 0 for gapless (live albums, OSTs).
6. **Red Burn button** (bottom right). A burn sheet appears:
   - Drive: ASUS SDRW-08U9M-U (auto-selected if only one burner)
   - Speed: **16x** (or 10x for maximum reliability on cheap media)
   - Click **Burn**.

## Burn.app uses DiscRecording

Burn.app is linked against `/System/Library/Frameworks/DiscRecording.framework`, which means it inherits Apple's "Unsupported" gating. In practice, on the ASUS SDRW-08U9M-U this works anyway — DiscRecording enumerates the drive and will write to it even though drutil labels it Unsupported. But if the drive ever stops working in Burn.app on a future macOS update, cdrdao will still work because it's independent of DiscRecording.

## Why cdrdao is still the primary path

- **Scriptable**: the whole burn runs from a single `burn_audio_cd.py` invocation
- **No DiscRecording dependency**: future-proofed against Apple further restricting third-party drives
- **Deterministic CD-Text**: build_toc.py controls exactly what metadata is written, reproducibly
- **No GUI handoff**: no drag-and-drop, no manual clicking, no room for human error mid-burn

Burn.app is the fallback when cdrdao fails.
