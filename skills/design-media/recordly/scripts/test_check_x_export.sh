#!/usr/bin/env bash
# Tests for check_x_export.py. Builds synthetic clips with ffmpeg in a temp directory, removed on exit.
# Usage: bash test_check_x_export.sh
#   CHECKER=/path/to/other_checker bash test_check_x_export.sh   # run the same cases against another checker
# Exit: 0 when every case passes, 1 otherwise.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CHECKER="${CHECKER:-$HERE/check_x_export.py}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0; fail=0; skip=0

# make NAME [ffmpeg args after the inputs...]; inputs: test pattern + stereo tone, overridable via SIZE/RATE/DUR/AUDIO
make() {
    local name="$1"; shift
    local size="${SIZE:-320x180}" rate="${RATE:-30}" dur="${DUR:-1}"
    local inputs=(-f lavfi -i "testsrc2=size=$size:rate=$rate")
    [ "${AUDIO:-1}" = "1" ] && inputs+=(-f lavfi -i "sine=frequency=440:sample_rate=48000,aformat=channel_layouts=stereo")
    ffmpeg -v error -y "${inputs[@]}" -t "$dur" "$@" "$WORK/$name.mp4" 2>"$WORK/$name.err"
}

GOOD_V=(-c:v libx264 -profile:v high -pix_fmt yuv420p)
GOOD_A=(-c:a aac -b:a 128k)

# expect LABEL WANT_EXIT PATTERN -- checker args
expect() {
    local label="$1" want="$2" pattern="$3"; shift 4
    local out got
    out="$(python3 "$CHECKER" "$@" 2>&1)"; got=$?
    if [ "$got" = "$want" ] && { [ -z "$pattern" ] || grep -qE "$pattern" <<<"$out"; }; then
        pass=$((pass + 1)); echo "ok    $label"
    else
        fail=$((fail + 1)); echo "FAIL  $label (exit $got, want $want; pattern '$pattern')"; sed 's/^/        /' <<<"$out"
    fi
}

made() {  # made NAME: true when the fixture exists, else record a SKIP with ffmpeg's reason
    if [ -s "$WORK/$1.mp4" ]; then return 0; fi
    skip=$((skip + 1)); echo "SKIP  $1: $(head -1 "$WORK/$1.err")"; return 1
}

# Fixtures
make good        "${GOOD_V[@]}" "${GOOD_A[@]}"
make main        -c:v libx264 -profile:v main -pix_fmt yuv420p "${GOOD_A[@]}"
make hevc        -c:v libx265 -tag:v hvc1 -pix_fmt yuv420p "${GOOD_A[@]}"
make yuv444      -c:v libx264 -pix_fmt yuv444p "${GOOD_A[@]}"
make heaac       "${GOOD_V[@]}" -c:a aac_at -profile:a 4 -b:a 64k   # 4 = HE-AAC
make mp3         "${GOOD_V[@]}" -c:a libmp3lame -b:a 128k
make alac        "${GOOD_V[@]}" -c:a alac
make surround    "${GOOD_V[@]}" -c:a aac -b:a 256k -af "aformat=channel_layouts=5.1"
RATE=120 make fps120 "${GOOD_V[@]}" "${GOOD_A[@]}"
SIZE=1600x400 make wide "${GOOD_V[@]}" "${GOOD_A[@]}"
SIZE=160x90 DUR=141 make long -c:v libx264 -profile:v high -pix_fmt yuv420p -preset veryfast "${GOOD_A[@]}"  # ultrafast drops to Baseline
make sar         "${GOOD_V[@]}" -vf setsar=4/3 "${GOOD_A[@]}"   # displays 427x180; 2:1 would breach X's 3:1 cap
make interlaced  "${GOOD_V[@]}" -flags +ildct+ilme -field_order tt "${GOOD_A[@]}"
AUDIO=0 make silent "${GOOD_V[@]}"
SIZE=1080x1080 make square1080 "${GOOD_V[@]}" "${GOOD_A[@]}"
# testsrc2 rounds sizes to even, so the odd clip uses the color source. 4:4:4 allows odd sizes; 4:2:0 does not.
ffmpeg -v error -y -f lavfi -i "color=c=blue:size=321x181:rate=30" -f lavfi -i "sine=frequency=440:sample_rate=48000" \
    -t 1 -c:v libx264 -pix_fmt yuv444p "${GOOD_A[@]}" "$WORK/odd.mp4" 2>"$WORK/odd.err"
SIZE=1920x1080 make landscape1080 "${GOOD_V[@]}" "${GOOD_A[@]}"
[ -s "$WORK/landscape1080.mp4" ] && ffmpeg -v error -y -display_rotation 90 -i "$WORK/landscape1080.mp4" -c copy \
    "$WORK/rotated.mp4" 2>"$WORK/rotated.err"   # stored 1920x1080, displayed portrait
# Cover art: a 64x64 PNG muxed into the Main-profile clip so --fix runs. The MP4 muxer always stores the cover after
# the video, so this guards that cover art does not break --fix; it cannot tell first-stream from index mapping apart.
ffmpeg -v error -y -f lavfi -i "color=c=red:size=64x64" -frames:v 1 "$WORK/cover.png" 2>/dev/null
[ -s "$WORK/main.mp4" ] && ffmpeg -v error -y -i "$WORK/main.mp4" -i "$WORK/cover.png" -map 0 -map 1 -c copy \
    -c:v:1 png -disposition:v:1 attached_pic "$WORK/coverart.mp4" 2>"$WORK/coverart.err"
ffmpeg -v error -y -f lavfi -i "sine=frequency=440:sample_rate=48000" -t 1 "$WORK/audioonly.mp3" 2>/dev/null
[ -s "$WORK/audioonly.mp3" ] && cp "$WORK/audioonly.mp3" "$WORK/audioonly.mp4"   # made() looks for .mp4

# Checks
made good       && expect "compliant clip passes"          0 "ready for X"            -- "$WORK/good.mp4"
made main       && expect "Main profile fails"             1 "FAIL  H.264 profile"    -- "$WORK/main.mp4"
made hevc       && expect "HEVC fails"                     1 "FAIL  video codec"      -- "$WORK/hevc.mp4"
made yuv444     && expect "YUV 4:4:4 fails"                1 "FAIL  pixel format"     -- "$WORK/yuv444.mp4"
made heaac      && expect "HE-AAC fails"                   1 "FAIL  audio codec"      -- "$WORK/heaac.mp4"
made mp3        && expect "MP3 in MP4 fails"               1 "FAIL  audio codec"      -- "$WORK/mp3.mp4"
made alac       && expect "ALAC in MP4 fails"              1 "FAIL  audio codec"      -- "$WORK/alac.mp4"
made surround   && expect "5.1 audio fails"                1 "FAIL  audio channels"   -- "$WORK/surround.mp4"
made fps120     && expect "120 fps fails"                  1 "FAIL  frame rate"       -- "$WORK/fps120.mp4"
made wide       && expect "4:1 aspect fails"               1 "FAIL  aspect"           -- "$WORK/wide.mp4"
made long       && expect "141 s fails on a free account"  1 "FAIL  duration"         -- "$WORK/long.mp4"
made long       && expect "141 s passes with --premium"    0 "ready for X"            -- "$WORK/long.mp4" --premium
made sar        && expect "non-square pixels fail"         1 "FAIL  pixel aspect"     -- "$WORK/sar.mp4"
made interlaced && expect "interlaced scan fails"          1 "FAIL  scan"             -- "$WORK/interlaced.mp4"
made silent     && expect "no audio warns but passes"      0 "WARN  audio: no audio"  -- "$WORK/silent.mp4"
made square1080 && expect "1080 square warns on free"      0 "WARN  resolution"       -- "$WORK/square1080.mp4"
made square1080 && expect "1080 square clean on premium"   0 "PASS  resolution"       -- "$WORK/square1080.mp4" --premium

# --fix turns every fixable failure into a passing copy beside the input
for name in main hevc yuv444 heaac mp3 alac surround fps120 sar interlaced square1080; do
    made "$name" || continue
    expect "--fix repairs $name" 0 "wrote .*$name\.x\.mp4" -- "$WORK/$name.mp4" --fix
    [ -s "$WORK/$name.x.mp4" ] || { fail=$((fail + 1)); echo "FAIL  --fix $name wrote no file"; }
done
made square1080 && expect "--fix scales 1080 square to 720" 0 "PASS  resolution: short side 720" -- "$WORK/square1080.x.mp4"
made sar        && expect "--fix keeps the displayed shape of non-square pixels" 0 "PASS  aspect: 42[68]x180" -- "$WORK/sar.x.mp4"
made fps120     && expect "--fix caps 120 fps at 60"           0 "PASS  frame rate: 60.00" -- "$WORK/fps120.x.mp4"
made rotated    && expect "rotation is read as displayed portrait" 0 "aspect: 1080x1920" -- "$WORK/rotated.mp4" --premium
made rotated    && expect "--fix scales rotated video to 720x1280" 0 "wrote"           -- "$WORK/rotated.mp4" --fix
made rotated    && expect "rotated copy is 720x1280 portrait"  0 "PASS  aspect: 720x1280" -- "$WORK/rotated.x.mp4"
made odd        && expect "--fix rounds odd sizes to even"     0 "PASS  aspect: 320x180" -- "$WORK/odd.mp4" --fix
made coverart   && expect "--fix runs on a clip with cover art" 0 "wrote"               -- "$WORK/coverart.mp4" --fix
made coverart   && expect "cover-art copy keeps the 320x180 video" 0 "PASS  aspect: 320x180" -- "$WORK/coverart.x.mp4"
made audioonly  && expect "audio-only file fails cleanly"      1 "FAIL  video: no video stream" -- "$WORK/audioonly.mp4"
made audioonly  && expect "--fix on audio-only has nothing to fix" 1 "nothing to fix"   -- "$WORK/audioonly.mp4" --fix
made wide       && expect "--fix cannot fix the aspect"     1 "FAIL  aspect"           -- "$WORK/wide.mp4" --fix
made main       && expect "--fix refuses an existing copy"  2 "already exists"         -- "$WORK/main.mp4" --fix
made good       && expect "--fix leaves a good clip alone"  0 "nothing to fix"         -- "$WORK/good.mp4" --fix
[ ! -e "$WORK/good.x.mp4" ] && { pass=$((pass + 1)); echo "ok    no copy written for a good clip"; } \
    || { fail=$((fail + 1)); echo "FAIL  a copy was written for a good clip"; }
expect "missing file is a usage error" 2 "no such file" -- "$WORK/absent.mp4"

echo "passed $pass, failed $fail, skipped $skip"
[ "$fail" -eq 0 ]
