# Speak Response Skill

Local text-to-speech using Qwen3-TTS. Default voice is the **Oracle** (deep, resonant Dune narrator). Supports voice cloning, voice design, and emotion-controlled preset speakers.

## Features

- **Oracle Voice (Default)**: Deep, prophetic narrator cloned from Dune audio
- **Preset Speakers**: 9 voices with per-message emotion/mood control
- **Voice Cloning**: Clone any voice from a 3+ second audio sample
- **Voice Design**: Create new voices from natural language descriptions
- **Local Inference**: Runs entirely on your machine (Apple Silicon M4 optimized)

## Installation

### Step 1: Install Qwen3-TTS CLI

```bash
# Create a Python environment
cd /path/to/your/projects
git clone https://github.com/QwenLM/Qwen3-TTS.git qwen3-tts
cd qwen3-tts

# Install with uv (recommended)
uv venv
uv pip install -e .
uv pip install soundfile

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install soundfile
```

### Step 2: Create the qwen-tts CLI Wrapper

The skill expects a `qwen-tts` command. Create wrapper scripts:

```bash
# Create bin directory
mkdir -p ~/bin

# Create the main wrapper
cat > ~/bin/qwen-tts << 'EOF'
#!/bin/bash
# Qwen3-TTS CLI wrapper
SCRIPT_DIR="/path/to/your/qwen3-tts"  # UPDATE THIS PATH
cd "$SCRIPT_DIR"
source .venv/bin/activate

case "$1" in
    generate)
        shift
        python generate.py "$@"
        ;;
    clone)
        shift
        python clone.py "$@"
        ;;
    design)
        shift
        python design.py "$@"
        ;;
    *)
        echo "Usage: qwen-tts {generate|clone|design} [args...]"
        exit 1
        ;;
esac
EOF

chmod +x ~/bin/qwen-tts

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Copy Python Scripts

Copy the optimized Python scripts from this skill to your qwen3-tts installation:

```bash
cp qwen3-tts/*.py /path/to/your/qwen3-tts/
```

These scripts include:
- **generate.py**: CustomVoice with preset speakers + instruction control
- **clone.py**: Voice cloning from audio samples
- **design.py**: Voice design from natural language descriptions

Features added:
- `--fast` flag for bfloat16 (50% memory savings on M4+)
- Timing logs (model load time, generation time, RTF)
- Suppressed flash-attn warnings (CUDA-only, harmless on Apple Silicon)

### Step 4: Download Models (First Run)

On first use, models will download from Hugging Face (~3-7GB each):

```bash
# Test generation (downloads CustomVoice model)
qwen-tts generate "Hello world" -o test.wav

# Test cloning (downloads Base model)
qwen-tts clone "Test" reference.mp3 -r "transcript" -o test.wav

# Test design (downloads VoiceDesign model)
qwen-tts design "Test text" "warm, friendly voice" -o test.wav
```

### Step 5: Install the Skill

```bash
# Copy to your Claude Code skills directory
cp -r speak-response ~/.claude/skills/

# Or symlink for easy updates
ln -s "$(pwd)/speak-response" ~/.claude/skills/speak-response
```

### Step 6: Set Up Oracle Voice (Optional)

The Oracle voice requires a reference audio file. The included preset uses this passage from Dune:

> "He was warrior and mystic, ogre and saint, the fox and the innocent, chivalrous, ruthless, less than a god, more than a man. There is no measuring Muad'Dib's motives by ordinary standards. In the moment of his triumph, he saw the death prepared for him, yet he accepted the treachery."

To use your own voice instead:

```bash
mkdir -p ~/.claude/skills/speak-response/voices/oracle

# Copy your reference audio (3+ seconds, clear speech)
cp your-voice.mp3 ~/.claude/skills/speak-response/voices/oracle/reference.mp3

# Create transcript file (exact words spoken in the audio)
echo "The exact words spoken in the reference audio" > ~/.claude/skills/speak-response/voices/oracle/transcript.txt
```

## Usage

### Default (Oracle Voice)

```bash
/speak                          # Last 2 sentences
/speak "The spice must flow."   # Specific text
```

**Showcase Example** - This passage generates exceptionally well with the Oracle voice:

```bash
/speak "He was warrior and mystic, ogre and saint, the fox and the innocent, chivalrous, ruthless, less than a god, more than a man. There is no measuring Muad'Dib's motives by ordinary standards. In the moment of his triumph, he saw the death prepared for him, yet he accepted the treachery."
```

The deep, prophetic quality of the Oracle voice brings this Dune-inspired narration to life with gravitas and ancient wisdom.

### Preset Speakers with Emotion Control

```bash
/speak --preset mood:warm                    # Warm preset
/speak --preset "Hello" Vivian "nurturing"   # Speaker + instruction
```

### Direct Script Usage

```bash
# Oracle voice
scripts/speak.sh "Your text here"

# Preset speaker with instruction
scripts/speak.sh --preset "Text" Ryan "calm, measured, professional"

# Clone a voice
scripts/clone.sh "New text" reference.mp3 "Transcript of reference"

# Design a new voice
scripts/design-voice.sh "Sample text" "deep, resonant, mysterious"
```

## Speakers

| Speaker | Style |
|---------|-------|
| Ryan | Professional, serious |
| Vivian | Warm, nurturing |
| Serena | Calm, gentle |
| Dylan | Friendly, casual |
| Eric | Dramatic, commanding |
| Aiden | Encouraging, energetic |
| Uncle_Fu | Wise, measured |
| Ono_Anna | Soft, gentle |
| Sohee | Clear, professional |

## Mood Presets

| Preset | Instruction |
|--------|-------------|
| `calm` | calm, soothing, gentle pace |
| `warm` | warm, empathetic, nurturing tone |
| `excited` | joyful, excited, enthusiastic |
| `serious` | serious, measured, authoritative |
| `gentle` | soft, gentle, whispered |
| `encouraging` | encouraging, uplifting, sincere |
| `contemplative` | thoughtful, slow pace, reflective |

## Performance

On Apple Silicon M4 Max:
- **Model load**: ~15-30s (cached after first load)
- **Generation**: ~1-3x realtime (RTF)
- **Memory**: ~8GB (float32) or ~4GB with `--fast` (bfloat16)

Use `--fast` flag for 50% memory savings:

```bash
qwen-tts generate "Text" --fast -o output.wav
```

## Troubleshooting

### "qwen-tts: command not found"

Ensure ~/bin is in your PATH:
```bash
echo $PATH | grep -q "$HOME/bin" || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### "flash-attn is not installed" warning

This warning is harmless on Apple Silicon. flash-attn is CUDA-only and cannot be installed on macOS. PyTorch falls back to standard attention automatically.

### Out of memory

Use `--fast` flag for bfloat16 precision (50% less memory):
```bash
qwen-tts generate "Text" --fast -o output.wav
```

Or use the smaller 0.6B model:
```bash
qwen-tts generate "Text" --small -o output.wav
```

### Audio doesn't play

The skill uses `afplay` (macOS). Ensure:
1. Volume is up
2. Audio file was created: `ls -la /tmp/claude-speak-*.wav`
3. Test manually: `afplay /tmp/claude-speak-*.wav`

## Files

```
speak-response/
├── SKILL.md              # Skill definition and documentation
├── README.md             # This file
├── scripts/
│   ├── speak.sh          # Main entry point (Oracle default)
│   ├── clone.sh          # Voice cloning
│   └── design-voice.sh   # Voice design
├── voices/
│   └── oracle/           # Oracle voice preset
│       ├── reference.mp3 # Reference audio
│       └── transcript.txt # Transcript
├── references/
│   └── moods.md          # Extended mood presets
└── qwen3-tts/            # Python scripts for CLI
    ├── generate.py       # CustomVoice generation
    ├── clone.py          # Voice cloning
    └── design.py         # Voice design
```

## Credits

- **Qwen3-TTS**: [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
- **Oracle Voice**: Inspired by the Dune narrator style
