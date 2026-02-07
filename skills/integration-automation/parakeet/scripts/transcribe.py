#!/usr/bin/env python3
"""Transcribe audio file using Parakeet TDT 0.6B.

Usage:
    transcribe.py <audio-file>

Supports: .wav, .mp3, .m4a, .flac, .ogg, .aac
Output: Transcribed text to stdout
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
    if len(sys.argv) < 2:
        print("Usage: transcribe.py <audio-file>", file=sys.stderr)
        print("Supported formats: .wav, .mp3, .m4a, .flac, .ogg, .aac", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]

    # Expand user paths
    if filepath.startswith("~"):
        filepath = os.path.expanduser(filepath)

    # Resolve relative paths
    if not os.path.isabs(filepath):
        filepath = os.path.abspath(filepath)

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    # Import after path setup
    from src.audio import load_audio_file
    from src.transcriber import get_transcriber
    from src.config import get_config

    try:
        config = get_config()

        # Load audio file
        print(f"Loading: {os.path.basename(filepath)}...", file=sys.stderr)
        audio = load_audio_file(filepath)

        # Get duration (use config sample rate)
        duration = len(audio) / config.sample_rate
        print(f"Duration: {duration:.1f}s", file=sys.stderr)

        # Transcribe
        print("Transcribing...", file=sys.stderr)
        transcriber = get_transcriber()
        text = transcriber.transcribe(audio)

        # Output result
        print(text)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
