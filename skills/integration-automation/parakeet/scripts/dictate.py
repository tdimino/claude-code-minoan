#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#     "parakeet-mlx>=0.5.2",
#     "mlx-audio>=0.5.5",
#     "numpy>=1.26",
# ]
# ///
"""Record from the default microphone until Enter, then transcribe with Parakeet (MLX).

Recording uses ffmpeg's AVFoundation input, so no audio Python packages are needed.
For push-to-talk into any text field, use the Handy app instead.

Usage:
    dictate.py [--device :0]
"""

import argparse
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("batch", Path(__file__).with_name("batch_transcribe.py"))
batch = importlib.util.module_from_spec(spec)
sys.modules["batch"] = batch  # @dataclass resolves annotations via sys.modules
spec.loader.exec_module(batch)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--device", default=":default",
                        help="AVFoundation audio device (list: ffmpeg -f avfoundation -list_devices true -i '')")
    args = parser.parse_args()

    print("Loading Parakeet model...", file=sys.stderr)
    engine = batch.ParakeetEngine(batch.DEFAULT_MODELS["parakeet"], beam=1)

    with tempfile.TemporaryDirectory() as tmp:
        recording = Path(tmp) / "dictation.wav"
        recorder = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-f", "avfoundation", "-i", args.device,
             "-ac", "1", "-ar", str(batch.SAMPLE_RATE), str(recording)],
            stdin=subprocess.PIPE,
        )
        print("\n>>> Recording... press ENTER to stop <<<\n", file=sys.stderr)
        try:
            input()
        except KeyboardInterrupt:
            recorder.terminate()
            sys.exit("\nCancelled.")
        recorder.communicate(b"q")  # ffmpeg finalizes the WAV header on 'q'

        if not recording.exists() or recording.stat().st_size <= 44:
            sys.exit(f"No audio captured (ffmpeg exit {recorder.returncode}). Check --device; list devices "
                     "with: ffmpeg -f avfoundation -list_devices true -i ''")
        try:
            clip = batch.load_clip(recording, pad_under=2.0, pad_s=0.75)
        except batch.ClipError as error:
            sys.exit(f"Recording unreadable: {error}")
        if clip.peak_dbfs is None or clip.peak_dbfs < -80:
            # macOS records digital silence, not an error, when microphone access is denied.
            sys.exit("Recording is silent. Grant your terminal microphone access in System Settings > "
                     "Privacy & Security > Microphone, or pick another --device.")
        print(f"Recorded: {clip.duration_s:.1f}s (peak {clip.peak_dbfs} dBFS)", file=sys.stderr)
        text = engine.transcribe(clip)["text"]

    if text:
        print(text)
    else:
        print("(No speech detected)", file=sys.stderr)


if __name__ == "__main__":
    main()
