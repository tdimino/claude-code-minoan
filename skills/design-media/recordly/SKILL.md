---
name: recordly
description: "Record and polish screen videos with Recordly (open-source Screen Studio alternative, v1.4.0): display or window capture with a live webcam bubble, microphone and system audio, auto-zoom, cursor effects, local Whisper captions, aspect-ratio presets, timeline trims and MP4/GIF export. Also includes Slant, a browser-based 3D perspective renderer with 12 animation presets. This skill should be used when recording oneself on camera over a screen (talking head over slides, PDFs, tablets or a website), making a video for X/Twitter, polishing a demo or walkthrough, or adding a 3D perspective effect. Triggers on record myself, talking head, screen and webcam, video for X, Twitter video, screen recording, demo video, product walkthrough, Recordly, Slant, 3D perspective."
argument-hint: "[install | launch | drive | x-check <file> | slant]"
---

# Recordly

Desktop recorder and editor (`webadderallorg/Recordly`, AGPL-3.0). It records a display or a single window with
microphone, system audio and a live webcam, then opens a timeline editor for trims, zooms, captions, framing and export.
On macOS it captures through native ScreenCaptureKit helpers and needs macOS 14 or later. Effects are 2D pan and zoom
with motion blur. For 3D perspective, use Slant (below).

The Homebrew cask installs v1.4.0 to `/Applications/Recordly.app` (bundle id `dev.recordly.app`), signed Developer ID
Application: Fido Tech (54QUWA9PZA), notarized and stapled.

Arguments: `install` runs `scripts/install_recordly.sh`, `launch` runs `scripts/launch_recordly.sh`, `drive` follows
"Drive with agent-desktop", `x-check <file>` runs `scripts/check_x_export.py`, `slant` opens `scripts/slant.html`.

## When to Use

- Recording the user on webcam over a window: a photo of an artifact, a PDF, a website, a slide.
- Placing a 3D object beside the user's face. See `references/3d-objects-beside-webcam.md`.
- Short clips for X, demos for PRs and docs, product walkthroughs.
- Polishing a raw capture from `compound-engineering:feature-video` (open it in Recordly, add zooms and a frame,
  export).

**Not for:** raw capture with no editing (QuickTime), batch or headless video work (ffmpeg), device bezels (Rotato,
Shots.so), audio mixing.

## Install and Launch

```bash
S=~/.claude/skills/recordly/scripts
bash $S/install_recordly.sh                 # Homebrew cask; upgrades when already installed
bash $S/install_recordly.sh --from-source   # clone and build in ~/tools/recordly
bash $S/launch_recordly.sh                  # files passed at launch are ignored; open them from HUD → More
```

Recordly needs **Screen Recording**, **Microphone** and **Camera**. It does not add itself to the Screen Recording list,
so the user adds `/Applications/Recordly.app` there with **+**. The microphone and camera prompts appear when a device is
chosen in the HUD. Steps and verification are in the reference below.

Update through `brew upgrade --cask recordly` and leave Recordly's experimental update channel off, so one updater owns
the installed version. The app is notarized, so it opens without clearing quarantine. If Gatekeeper ever rejects it,
inspect `spctl -a -vv /Applications/Recordly.app` before doing anything else.

## Record, Edit, Export

1. **HUD:** choose a display or a window, the microphone, system audio and the webcam. A countdown precedes the take.
2. **Take:** record, then stop. The editor opens on the take.
3. **Editor:** trims, manual zoom regions and automatic zoom suggestions, speed regions, text and image annotations,
   extra audio regions, Whisper captions (run locally), the webcam bubble (size, preset or custom position, mirror,
   roundness, shadow, zoom-reactive scaling), wallpaper, padding, corners, crop and aspect-ratio presets.
4. **Save and export:** save the `.recordly` project to keep the editor state, then export MP4 or GIF with quality and
   output-size settings.

## Drive with agent-desktop

The agent prepares and finishes. The user records. The agent's part:

1. `agent-desktop launch Recordly --cdp` to get a DevTools port.
2. Through `agent-browser --cdp <port>`, set the source, microphone and webcam, and turn on **Hide HUD from recording**.
3. Report the setup and stop. The user presses **Record** and stops the take.
4. In the editor, set the aspect, webcam position and captions, then export.
5. Fill the native save dialog with `agent-desktop`.

The HUD and editor are web content that macOS accessibility cannot see, so `agent-browser` drives them over CDP and
`agent-desktop` handles launch, System Settings and the save dialog. The native **open** dialog defeats both, so the
user picks files there. Commands, control names and failure modes are in `references/driving-with-agent-desktop.md`. The
control map for v1.4.0 is in `references/ui-map-v1.4.0.json`.

## Gotchas

- **Auto-zoom follows the cursor.** A talking-head take with a still mouse yields no zoom suggestions. Add manual zoom
  regions on the sign groups or lines being discussed, since small text is unreadable at 720p playback.
- **The export codec is not guaranteed.** Recordly asks for H.264 High (`avc1.640034`) and silently falls back to Main
  or Baseline when the encoder refuses. Its `copy-source` audio mode can mux MP3 or ALAC into the MP4. X rejects both,
  so run the check below on every export.
- **Notifications land in the take.** Turn on a Focus mode before recording a display.

## Export for X

The checker defaults to a free X account: 140 s and 512 MB per video, played back at 720p. On a free account, plan
takes under 2:20. Export from Recordly at **1:1** or **16:9**, MP4, **Original** size, Balanced, 30 fps. Then check it:

```bash
python3 ~/.claude/skills/recordly/scripts/check_x_export.py clip.mp4          # PASS, WARN or FAIL per rule; exit 1 on any FAIL
python3 ~/.claude/skills/recordly/scripts/check_x_export.py clip.mp4 --fix    # writes clip.x.mp4 beside it, never over it
```

- `--fix` re-encodes to H.264 High, yuv420p and AAC-LC 128k, scales to 720 on the short side (1080 with `--premium`),
  caps the frame rate at 60, and squares the pixels while keeping the displayed shape and rotation. It cannot fix length
  or aspect, so trim in Recordly, or change the preset.
  An Original-size export plus `--fix` gives a sharper 720p file than Recordly's Low preset (648).
- `--premium` switches to Premium caps (under 4 h, 16 GB, 1080p).
- The rules come from X's Help Center and the developer media best-practices page (read 2026-11-05). They are cited in
  the script header, along with where the two sources conflict.
- Posting stays with the user, because a post publishes.
- Tests: `bash ~/.claude/skills/recordly/scripts/test_check_x_export.sh` builds synthetic clips with ffmpeg and runs
  44 checks. The HE-AAC and HEVC fixtures need macOS's `aac_at` and `libx265`, and print SKIP where those are missing.

## Slant: 3D Perspective

`open ~/.claude/skills/recordly/scripts/slant.html` opens a self-contained Three.js page (r183 from CDN, no build).
Drop a recording, pick one of 12 presets, adjust the background and depth of field, export MP4, WebM or GIF. Presets,
codecs and controls are in `README.md`.

## Links

- Repo and releases: `github.com/webadderallorg/Recordly`
- Homebrew cask: `Casks/r/recordly.rb` in `Homebrew/homebrew-cask`
- Upstream: `github.com/siddharthvaddem/openscreen` (MIT)
- Extensions: `marketplace.recordly.dev/extensions`
