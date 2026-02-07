#!/usr/bin/env python3
"""Record from microphone and transcribe using Parakeet TDT 0.6B.

Usage:
    dictate.py

Records audio from the default microphone until Enter is pressed,
then transcribes and outputs the text.
"""

import sys
import os
import warnings

# Suppress warnings before any imports
warnings.filterwarnings('ignore')
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

# Add Parakeet to path (configurable via PARAKEET_HOME)
PARAKEET_PATH = os.environ.get(
    "PARAKEET_HOME",
    os.path.expanduser("~/Programming/parakeet-dictate")
)
sys.path.insert(0, PARAKEET_PATH)

# Suppress NeMo's verbose logging (must be before nemo imports)
os.environ.setdefault("NEMO_CACHE_DIR", os.path.expanduser("~/.cache/nemo"))
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import logging
# Suppress all NeMo/PyTorch warnings for clean output
logging.disable(logging.WARNING)
logging.getLogger("nemo").setLevel(logging.ERROR)
logging.getLogger("nemo_logger").setLevel(logging.ERROR)
logging.getLogger("pytorch_lightning").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)


def main():
    # Import after path setup
    from src.audio import AudioRecorder
    from src.transcriber import get_transcriber
    from src.config import get_config

    recorder = None
    try:
        # Pre-load model while user reads prompt
        print("Loading Parakeet model...", file=sys.stderr)
        transcriber = get_transcriber()
        transcriber.preload()

        recorder = AudioRecorder()
        config = get_config()

        print("", file=sys.stderr)
        print(">>> Recording... Press ENTER to stop <<<", file=sys.stderr)
        print("", file=sys.stderr)

        recorder.start_recording()

        # Wait for Enter key
        input()

        # Stop recording and get audio
        audio = recorder.stop_recording()

        if audio.size == 0:
            print("No audio captured.", file=sys.stderr)
            sys.exit(1)

        # Show duration (use config sample rate)
        duration = len(audio) / config.sample_rate
        print(f"Recorded: {duration:.1f}s", file=sys.stderr)

        # Transcribe
        print("Transcribing...", file=sys.stderr)
        text = transcriber.transcribe(audio)

        if text.strip():
            print(text)
        else:
            print("(No speech detected)", file=sys.stderr)

    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if recorder:
            recorder.cleanup()


if __name__ == "__main__":
    main()
