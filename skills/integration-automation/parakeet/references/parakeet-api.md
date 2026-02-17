# Parakeet API Reference

Technical reference for the Parakeet Dictate transcription engine.

## Location

```
~/Programming/parakeet-dictate/
├── src/
│   ├── audio.py        # Audio capture and file loading
│   ├── transcriber.py  # Parakeet model wrapper
│   └── config.py       # Configuration management
├── .venv/              # Python virtual environment
└── requirements.txt    # Dependencies
```

## Audio Module (`src/audio.py`)

### `load_audio_file(filepath, target_sample_rate=16000)`

Load an audio file and convert to format expected by Parakeet.

**Arguments:**
- `filepath` (str | Path): Path to audio file
- `target_sample_rate` (int): Target sample rate (default 16000Hz)

**Returns:**
- `np.ndarray`: Float32 audio array at target sample rate

**Supported Formats:**
- `.wav` - Waveform Audio
- `.mp3` - MPEG Audio Layer III
- `.m4a` - MPEG-4 Audio (AAC)
- `.flac` - Free Lossless Audio Codec
- `.ogg` - Ogg Vorbis
- `.aac` - Advanced Audio Coding

**Example:**
```python
from src.audio import load_audio_file

audio = load_audio_file("interview.mp3")
print(f"Duration: {len(audio) / 16000:.1f}s")
```

### `AudioRecorder`

Record audio from the microphone.

**Methods:**
- `start_recording()` - Begin capturing audio
- `stop_recording() -> np.ndarray` - Stop and return audio
- `cleanup()` - Release resources

**Example:**
```python
from src.audio import AudioRecorder

recorder = AudioRecorder()
recorder.start_recording()
# ... wait for user input ...
audio = recorder.stop_recording()
recorder.cleanup()
```

### `save_audio_to_file(audio, filepath, sample_rate=16000, channels=1)`

Save audio array to WAV file.

**Arguments:**
- `audio` (np.ndarray): Float32 audio array
- `filepath` (str): Output file path
- `sample_rate` (int): Sample rate in Hz
- `channels` (int): Number of channels

## Transcriber Module (`src/transcriber.py`)

### `get_transcriber() -> Transcriber`

Get the global transcriber singleton.

### `Transcriber`

Wrapper around NVIDIA Parakeet TDT model.

**Methods:**
- `preload()` - Pre-load model into memory
- `transcribe(audio) -> str` - Transcribe audio array to text

**Example:**
```python
from src.transcriber import get_transcriber
from src.audio import load_audio_file

transcriber = get_transcriber()
transcriber.preload()  # Optional, speeds up first transcription

audio = load_audio_file("recording.wav")
text = transcriber.transcribe(audio)
print(text)
```

## Configuration (`src/config.py`)

### `get_config() -> Config`

Get the global configuration.

### `Config`

**Fields:**
- `model_name` (str): Model identifier (default: `nvidia/parakeet-tdt-0.6b-v2`)
- `sample_rate` (int): Audio sample rate (default: 16000)
- `channels` (int): Audio channels (default: 1)

**Config File Location:**
`~/.config/parakeet-dictate/config.json`

## Model Details

### NVIDIA Parakeet TDT 0.6B v2

- **Parameters**: ~600M
- **Architecture**: Token-and-Duration Transducer (TDT)
- **Speed**: 3,386x realtime factor
- **Accuracy**: 6.05% WER (Word Error Rate)
- **Sample Rate**: 16kHz mono
- **Languages**: English (optimized)

### Hardware Acceleration

Automatically uses the best available:
1. **MPS** (Apple Silicon) - Fastest on Mac
2. **CUDA** (NVIDIA GPU) - Fastest on Linux/Windows
3. **CPU** - Fallback, slower but always works

## Error Handling

### Common Exceptions

```python
FileNotFoundError  # Audio file not found
ValueError         # Unsupported audio format
RuntimeError       # Model loading or transcription failure
```

### Example Error Handling

```python
from src.audio import load_audio_file
from src.transcriber import get_transcriber

try:
    audio = load_audio_file("audio.wav")
    transcriber = get_transcriber()
    text = transcriber.transcribe(audio)
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Invalid format: {e}")
except RuntimeError as e:
    print(f"Transcription failed: {e}")
```

## Performance Tips

1. **Pre-load the model** - Call `transcriber.preload()` before first use
2. **Batch processing** - Model stays in memory after first load
3. **Audio quality** - 16kHz mono is optimal; higher rates are downsampled
4. **Short clips** - Split long recordings into <30 second chunks for faster processing

## Dependencies

Required packages (in `.venv`):
- `nemo_toolkit[asr]>=2.0.0` - NVIDIA NeMo ASR framework
- `torch>=2.0.0` - PyTorch with MPS support
- `sounddevice>=0.4.6` - Audio capture
- `soundfile>=0.12.0` - Audio file loading
- `numpy>=1.24.0` - Array operations
