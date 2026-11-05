# Driving Recordly with agent-desktop and agent-browser

Verified against Recordly 1.4.0, agent-desktop 1.0.2 and agent-browser on macOS 15.6.1 (2026-11-05). Control names
are in `ui-map-v1.4.0.json`. After a Recordly upgrade, check them again.

## Which tool drives what

Recordly's control bar (the HUD) and its editor are web content inside Electron windows. macOS accessibility does not
expose the HUD: it is a transparent `hud-overlay` window that `agent-desktop list-windows --app Recordly` cannot list.
So the work splits like this:

| Surface | Tool | Why |
|---|---|---|
| Launch and quit Recordly | `agent-desktop launch Recordly --cdp`, `agent-desktop close-app Recordly` | Opens a DevTools port, quits gracefully |
| HUD and editor controls | `agent-browser --session recordly --cdp $PORT …` | DOM is reachable only through CDP |
| Save dialog | `agent-desktop set-value` + `click` | Native panel, which works headless |
| Open dialog (video or project) | **The user** | Native panel that headless and headed input both fail on |
| Privacy settings | `agent-desktop` on System Settings | Native app |

## Launch

```bash
agent-desktop close-app Recordly          # only if it is already running without a port
PORT=$(agent-desktop launch Recordly --cdp | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['cdp']['port'])")
AB="agent-browser --session recordly --cdp $PORT"
$AB tab list                               # t1 = HUD (?windowType=hud-overlay); the editor appears as another tab
```

- Pass `--cdp` on every call. `agent-browser connect <port>` opened a blank browser instead of attaching.
- Refs (`@e4`) do not carry between calls, so target by role and name: `$AB find role button click --name "Record"`.
- Never run `agent-browser close` on this session. Quit Recordly with `agent-desktop close-app`.
- `open -a Recordly <file>` and `launch_recordly.sh <file>` start the app but do not load the file.

## Permissions (once per machine)

Recordly does not add itself to the Screen Recording list. In System Settings → Privacy & Security → Screen & System
Audio Recording, the user clicks **+**, approves with Touch ID, presses ⌘⇧G, enters `/Applications/Recordly.app`, clicks
Open, and accepts Quit & Reopen. The reopen leaves Recordly quit, so relaunch it with `--cdp`.

The microphone and camera prompts appear when a device is chosen in the HUD menus (below). To verify all three, open
each pane and read the switch named `Recordly`:

```bash
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"   # also Privacy_Microphone, Privacy_Camera
agent-desktop snapshot --app "System Settings" -i --compact -w "switch:Recordly"
```

## Pre-flight (the agent does this; the user presses Record)

HUD buttons carry `title`s: **Screen**, **Enable microphone**, **Enable webcam overlay**, **Countdown delay**,
**Record**, **More**, **Hide HUD**, **Close App**.

The HUD's device menus closed after a reconnect, so open the menu and pick the device in one `eval`:

```bash
$AB eval '(async()=>{const b=()=>[...document.querySelectorAll("button")];
  b().find(e=>e.title==="Enable microphone").click(); await new Promise(r=>setTimeout(r,600));
  const mic=b().find(e=>e.innerText.trim().startsWith("Default - ")); if(!mic) return "no default microphone listed";
  mic.click();
  await new Promise(r=>setTimeout(r,600));
  return b().map(e=>e.title||e.innerText.trim()).join(" / ")})()'
```

- After a mic is picked the button reads **Disable microphone**. The menu also holds **Enable system audio** and
  **Turn Off Microphone**.
- The webcam works the same way: **Enable webcam overlay** → `MacBook Pro Camera (…)`. It then reads **Disable webcam
  overlay**, and the floating preview shows the camera live. **Hide Floating Preview** and **Turn Off Webcam** sit in
  the same menu.
- **More** holds **Hide HUD from recording** (turn it on for every take), **Recordings Path**, **Open video file**,
  **Open project**, theme and language.
- Report the setup and stop. The user clicks **Record** and stops the take.

## Opening media

HUD → **More** → **Open video file** (or **Open project**) raises the native panel "Import Media or Recordly Project".
Hand the pick to the user: on this panel a headless click only previews a file and Open stays disabled, the list's
`select` finds no item, `press` has no focused element, and `--headed` input could not verify its window while the
terminal held focus. Use `--headed` only with the user's permission. After one unverified headed key, stop, because
the key may land in the terminal. The editor opens as a new tab; check it with `$AB tab list`.

## Editor

| Area | Controls (names as clicked) |
|---|---|
| Header | Open projects, Undo, Redo, Rename project, Open presets, **Export** |
| Tabs | Scene, Cursor, **Webcam**, **Captions**, Settings, Extensions |
| Scene | Background (Image, Video, Color, Gradient, Upload Custom, named wallpapers), Blur, Shadow, Radius, Top/Bottom/Left/Right padding |
| Frame | aspect button (shows the current ratio), Crop Video, Add Layer |
| Timeline | Add Zoom (Z), Suggest Zooms from Cursor, Split Clip (C), Skip Back, Play, Skip Forward, Mute/Unmute, Preview volume |
| Webcam | position grid ↖ ↑ ↗ ← • → ↙ ↓ ↘, Webcam Width/Height, crop handles, Margin, Webcam Roundness, Webcam Shadow, Upload footage |
| Captions | Select Model, Auto Detect, Download Model, Generate Captions, Clear Captions, Text Color, Font Size, Rows, Bottom Offset, Max Width, Box Radius, Background Opacity |

Editor menus (aspect, Export) open on a real pointer event. A DOM `.click()` leaves them shut, so use
`$AB find … click`. They stay open across calls.

```bash
$AB find role button click --name "16:9"            # the button shows the current ratio
$AB find role menuitem click --name "1:1"           # Native, 16:9, 9:16, 1:1, 4:3, 4:5, 16:10, 10:16
$AB find role button click --name "Export"
for N in "MP4" "Original 1080 x 1080" "Balanced" "30"; do $AB find role button click --name "$N" --exact; done
$AB find role button click --name "Export Video" --exact
```

Size labels follow the aspect, with an ASCII `x`: at 1:1 they read `Low 648 x 648`, `Medium 810 x 810`,
`High 972 x 972`, `Original 1080 x 1080`.
Quality is Fast, Balanced or Quality. Frame rate is 24, 30 or 60. The panel exposes no selected state, so verify the
result with ffprobe.

## Save dialog

**Export Video** raises "Save Exported Video", prefilled `export-<epoch-ms>.mp4` in Downloads. It works headless:

```bash
agent-desktop snapshot --app Recordly --skeleton -i --compact      # find textfield "Save As:" and button "Save"
agent-desktop set-value @<ref Save As> "clip-01.mp4"
agent-desktop click @<ref Save>                                     # delivered_unverified, so confirm the file exists
```

Projects save under `~/Library/Application Support/Recordly/recordings/Projects/`, which stays empty until a project
is saved.

## Gotchas

- **Touch nothing during a take.** Any UI change on the recorded display ends up in the video.
- **Keep `agent-desktop cursor-overlay` off.** It draws a window on screen.
- **Headless clicks never move the real cursor,** so Suggest Zooms from Cursor ignores agent actions. Add zooms by hand.
- **System Settings snapshots time out** while a dialog loads thumbnails. Retry, or use `--skeleton`.
- **Whisper captions download a model first.** Its size and path have not been checked yet.
- **Watch codec fallback on other machines.** The pilot export was H.264 High, yuv420p and AAC-LC, but Recordly can
  fall back to Main profile. Check every export before posting.
