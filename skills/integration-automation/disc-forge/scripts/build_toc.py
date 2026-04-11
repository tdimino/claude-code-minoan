#!/usr/bin/env python3
"""
build_toc.py — Generate a cdrdao TOC file with CD-Text from source ID3 tags.

Reads album/artist/title metadata from each *original* audio file (MP3 or
other tagged format) via ffprobe — not from the WAV, because PCM WAV does
not carry ID3. Emits a cdrdao TOC referencing the matching WAV in the
wav directory.

Gap semantics:
    Default: no explicit PREGAP lines. cdrdao inserts the mandatory 2-second
    pregap on track 1 per Red Book spec, and subsequent tracks default to
    zero-gap (gapless). This is right for OSTs, film scores, live albums.
    --gaps flag: inserts `PREGAP 00:02:00` on tracks 2-N for traditional
    pop-album-style 2-second spacers.

Track order is determined by sorted() on the filenames, which lines up with
the common `NN Title.mp3` convention used throughout most ripped-CD libraries.

Usage:
    build_toc.py --wav-dir ~/burn-staging/BSG-S1-wav \\
                 --source-dir ~/burn-staging/BSG-S1 \\
                 --output ~/burn-staging/bsg-s1.toc
    build_toc.py --wav-dir ... --source-dir ... --output ... --gaps
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

AUDIO_EXTS = {".mp3", ".flac", ".aiff", ".aif", ".m4a", ".ogg", ".opus", ".wma"}


def ffprobe_tags(path: Path, *keys: str) -> dict[str, str]:
    """Read multiple ID3 tags in a single ffprobe call. Returns lowercase-keyed dict."""
    r = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format_tags=" + ",".join(keys),
            "-of", "default=noprint_wrappers=1",
            str(path),
        ],
        capture_output=True, text=True,
    )
    tags: dict[str, str] = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            # ffprobe emits keys as "TAG:title", "TAG:artist", etc
            tags[k.split(":", 1)[-1].lower()] = v
    return tags


def escape_toc_string(s: str) -> str:
    """Escape backslashes and double-quotes for cdrdao TOC quoted strings.

    Used for both CD_TEXT fields and AUDIOFILE paths — any quoted string
    in the TOC format needs this treatment.
    """
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a cdrdao TOC with CD-Text")
    ap.add_argument("--wav-dir", type=Path, required=True, help="Directory of WAVs to burn")
    ap.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Directory of original tagged files (for CD-Text metadata)",
    )
    ap.add_argument("--output", type=Path, required=True, help="Output TOC file path")
    ap.add_argument(
        "--gaps",
        action="store_true",
        help="Insert 2-sec gaps between tracks (pop album style; default is gapless)",
    )
    args = ap.parse_args()

    if not args.wav_dir.is_dir():
        print(f"error: wav dir not found: {args.wav_dir}", file=sys.stderr)
        return 1
    if not args.source_dir.is_dir():
        print(f"error: source dir not found: {args.source_dir}", file=sys.stderr)
        return 1

    # Sort source files to establish track order (matches "NN Title.mp3" convention).
    sources = sorted(
        f for f in args.source_dir.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS
    )
    if not sources:
        print(f"error: no source audio files in {args.source_dir}", file=sys.stderr)
        return 1

    # Check for missing WAVs up front so no partial TOC is written.
    missing_wavs = [
        source.stem + ".wav"
        for source in sources
        if not (args.wav_dir / f"{source.stem}.wav").exists()
    ]
    if missing_wavs:
        print(f"error: missing WAVs in {args.wav_dir}:", file=sys.stderr)
        for name in missing_wavs:
            print(f"  {name}", file=sys.stderr)
        return 1

    album_tags = ffprobe_tags(sources[0], "album", "artist")
    album = album_tags.get("album") or "Unknown Album"
    album_artist = album_tags.get("artist") or "Unknown Artist"

    lines: list[str] = [
        "CD_DA",
        "",
        "CD_TEXT {",
        "  LANGUAGE_MAP { 0: EN }",
        "  LANGUAGE 0 {",
        f'    TITLE "{escape_toc_string(album)}"',
        f'    PERFORMER "{escape_toc_string(album_artist)}"',
        "  }",
        "}",
        "",
    ]

    for idx, source in enumerate(sources, start=1):
        wav = args.wav_dir / f"{source.stem}.wav"
        track_tags = ffprobe_tags(source, "title", "artist")
        title = track_tags.get("title") or source.stem
        artist = track_tags.get("artist") or album_artist
        lines.append("TRACK AUDIO")
        if args.gaps and idx > 1:
            lines.append("PREGAP 00:02:00")
        lines.extend([
            "CD_TEXT {",
            "  LANGUAGE 0 {",
            f'    TITLE "{escape_toc_string(title)}"',
            f'    PERFORMER "{escape_toc_string(artist)}"',
            "  }",
            "}",
            f'AUDIOFILE "{escape_toc_string(str(wav))}" 0',
            "",
        ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines))

    print(f"wrote {args.output}")
    print(f"album:  {album}")
    print(f"artist: {album_artist}")
    print(f"tracks: {len(sources)}")
    print(f"gaps:   {'2-sec between tracks' if args.gaps else 'gapless'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
