#!/usr/bin/env python3
"""Design a voice with Qwen3-TTS VoiceDesign model."""
import argparse
import time
import sys
import os

# Suppress flash-attn warning during import (CUDA-only, doesn't work on Apple Silicon)
_stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel

sys.stderr = _stderr

def main():
    parser = argparse.ArgumentParser(description="Design voice with Qwen3-TTS")
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument("instruct", help="Voice description")
    parser.add_argument("-o", "--output", default="designed.wav", help="Output file")
    parser.add_argument("-l", "--lang", default="Auto", help="Language")
    parser.add_argument("--fast", action="store_true", help="Use bfloat16 (saves memory, M4+ recommended)")
    args = parser.parse_args()

    # Device selection: CUDA > MPS (Apple Silicon) > CPU
    if torch.cuda.is_available():
        device, dtype = "cuda:0", torch.bfloat16
    elif torch.backends.mps.is_available():
        device = "mps"
        # bfloat16 works on M4+ (PyTorch 2.10+), saves ~50% memory
        dtype = torch.bfloat16 if args.fast else torch.float32
    else:
        device, dtype = "cpu", torch.float32

    # Load model with timing (suppress flash-attn warning during load)
    print(f"Loading VoiceDesign model on {device}...", file=sys.stderr)
    t_load_start = time.time()
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map=device, dtype=dtype)
    sys.stdout = _stdout
    t_load = time.time() - t_load_start
    print(f"Model loaded in {t_load:.1f}s", file=sys.stderr)

    # Generate with timing
    instruct_preview = args.instruct[:50] + "..." if len(args.instruct) > 50 else args.instruct
    print(f"Designing voice: '{instruct_preview}'", file=sys.stderr)
    t_gen_start = time.time()
    wavs, sr = model.generate_voice_design(text=args.text, language=args.lang, instruct=args.instruct)
    t_gen = time.time() - t_gen_start

    # Calculate stats
    audio_duration = len(wavs[0]) / sr
    rtf = t_gen / audio_duration

    sf.write(args.output, wavs[0], sr)
    print(f"Saved: {args.output}", file=sys.stderr)
    print(f"Stats: {t_gen:.1f}s to generate {audio_duration:.1f}s audio (RTF: {rtf:.2f}x)", file=sys.stderr)

if __name__ == "__main__":
    main()
