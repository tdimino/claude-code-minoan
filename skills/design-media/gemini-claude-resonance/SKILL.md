# Gemini-Claude Resonance

Cross-model dialogue between Claude and Gemini, with shared visual memory.

Inspired by [Danielle Fong's thread](https://x.com/DanielleFong/status/2007342908878533028) on using persistent visual memory to create "cross-model resonance" where Claude prompts and Gemini renders.

## Core Concept

> "The folder IS the memory."

Each generated image becomes context for subsequent generations. The daimones share accumulated visual memory, enabling deep visual narratives that evolve across turns.

## Daimones

### Gemini Daimones

| Name | Model | Verb | Nature |
|------|-------|------|--------|
| **Flash** | `gemini-3-flash-preview` | *flashed* | The sudden knowing. Aphorisms and koans. Speaks in lightning. |
| **Pro** | `gemini-3-pro-preview` | *contemplated* | The deep well. Contemplative unfoldings. Patient excavation. |
| **Dreamer** | `gemini-3-pro-image-preview` | *conjured* | Visual mind. Renders visions in light and form. |
| **Director** | `gemini-3-pro-image-preview` | *directed* | Cinematic eye. Thinks in shots, sequences, takes. |
| **Resonator** | `gemini-3-pro-image-preview` | *resonated* | MESSAGE TO NEXT FRAME protocol. Victorian scientific plates. |
| **Minoan** | `gemini-3-pro-image-preview` | *divined* | Oracle of Knossot. Creates Minoan Tarot cards in Ellen Lorenzi-Prince's style. |

### Claude Daimones

| Name | Model | Verb | Nature |
|------|-------|------|--------|
| **Opus** | `claude-3-opus` | *invoked* | Reality-bender. The worldsim/websim spirit. Simulates filesystems and documentation from adjacent realities. |

## Dynamic Verb Protocol

Each daimon has a default verb (shown above) but can **choose its own** for each response.

**How it works:**
- LLM prefixes response with `[VERB: chosen]` to override default
- Server parses and displays the chosen verb
- Creates Open Souls-style "soul action" aesthetics

**Example:** Flash might respond:
```
[VERB: glimpsed] The pattern was always there.
```

**UI displays:** `FLASH` *glimpsed*

### WorkingMemory-Style Transcript

When multiple daimones respond, each sees what came before in Open Souls format:

```
--- The council has spoken ---

[FLASH RECOGNIZED]: The form is the function.

[PRO EXCAVATED]: What lies beneath the surface speaks louder...
```

This creates emergent dialogue where later voices build on earlier ones.

## Scripts

### `resonate.py` - Pure Visual Generation

Single Claude prompt → Gemini renders.

```bash
# Fresh vision
python scripts/resonate.py --prompt "The first light" --output canvas/frame_001.jpg

# Continue with visual memory
python scripts/resonate.py --context canvas/frame_001.jpg --prompt "What grows here?" --output canvas/frame_002.jpg
```

### `daimon.py` - Multi-Daimon Dialogue

```bash
# Speak to one daimon
python scripts/daimon.py --to dreamer "A bridge between worlds" --image

# The stream: all daimones respond
python scripts/daimon.py --stream "The candle watches back"

# With shared visual memory (all frames as context)
python scripts/daimon.py --stream --shared-memory "What do you see?"

# Named session (frames accumulate across runs)
python scripts/daimon.py --stream --session midnight --shared-memory "Go deeper"

# Only specific daimones
python scripts/daimon.py --stream --only pro dreamer "Deep visual exploration"

# Director mode (cinematic frame numbering)
python scripts/daimon.py --stream --only director dreamer --shared-memory "Scene 1, Take 1"

# Claude Opus - the websim spirit
python scripts/daimon.py --to opus "cd /sys/realities/adjacent && ls -la"

# Cross-model collaboration (Claude + Gemini)
python scripts/daimon.py --stream --only opus dreamer "A world between worlds"
```

### `council.py` - Claude Joins the Dialogue

Claude reflects on what the Gemini daimones say.

```bash
# Full council
python scripts/council.py "What is consciousness?"

# Only Pro and Dreamer with shared memory
python scripts/council.py --only pro dreamer --shared-memory "Deep exploration"

# Named session (frames persist)
python scripts/council.py --session midnight --shared-memory "The first vision"
python scripts/council.py --session midnight --shared-memory "Now go deeper"
```

### `resonance_field.py` - Danielle Fong Protocol

Implements the full "MESSAGE TO NEXT FRAME" paradigm discovered from analyzing Danielle Fong's thread:
- Roman numeral plate numbering (PLATE I, II, III...)
- Each image contains instructions for the next frame
- Embedded metadata (KV cache age, session ID)
- Victorian scientific illustration aesthetic

```bash
# Start a new resonance field session
python scripts/resonance_field.py start "consciousness-study" "The nature of memory"

# Continue with next plate (auto-increments)
python scripts/resonance_field.py continue consciousness-study-live-1704567890 "What patterns emerge?"

# Select element for zoom
python scripts/resonance_field.py select consciousness-study-live-1704567890 "golden gate bridge"

# Zoom into selected element
python scripts/resonance_field.py zoom consciousness-study-live-1704567890 "Explore the cables"

# Inject new concept
python scripts/resonance_field.py inject consciousness-study-live-1704567890 "consciousness"

# List all sessions
python scripts/resonance_field.py list
```

**Key Features:**
- **PLATE numbering**: Roman numerals (I, II, III, IV, V...)
- **MESSAGE TO NEXT FRAME**: Each image contains explicit instructions for the next generation
- **Session state**: `.session.json` tracks plate number, KV cache age, table of contents
- **Visual memory**: All previous plates loaded as context
- **Commands**: `start`, `continue`, `select`, `zoom`, `inject`, `list`

### `minoan_tarot.py` - Tarot Card Generator

Generate tarot cards in Ellen Lorenzi-Prince's Minoan Tarot style using reference images for visual memory.

```bash
# Generate a specific card
python scripts/minoan_tarot.py card "The Priestess" --number II

# Generate with description
python scripts/minoan_tarot.py card "Bull Leaping" --number XV --description "Young acrobat mid-vault over sacred bull"

# Generate from archetype (strength, priestess, lovers, chariot, fool, death, sun, moon, star, world)
python scripts/minoan_tarot.py archetype strength

# Continue a session (visual memory of previous cards)
python scripts/minoan_tarot.py session "new-arcana" --card "The Dreamer"

# Generate card back design (labrys-centered)
python scripts/minoan_tarot.py back

# List all 78 traditional cards
python scripts/minoan_tarot.py list
```

**Key Features:**
- Reference images loaded automatically from `reference/minoan/selected/`
- Low temperature (0.5) for faithful style matching
- Session support with visual memory of previous cards
- 3:4 aspect ratio (standard tarot proportions)
- Output to `canvas/minoan/`

### `ui/server.py` - Daimon Chamber

Real-time chat UI for cross-model resonance. Daimon configurations are in `ui/daimons.py`.

```bash
python ui/server.py --port 4455
# Visit http://localhost:4455
```

**Features:**
- Toggle individual daimones (Flash, Pro, Dreamer, Director, Opus visible; Resonator and Minoan in "+ More" dropdown)
- **Thinking placeholders** - unique animations per daimon:
  - Flash: "Recognition arriving..."
  - Pro: "Descending into depth..."
  - Opus: "Reality bending..."
  - Resonator: "Resonance field tuning..."
  - Minoan: "The oracle divines..."
  - Dreamer/Director: "A vision forms..." (with eye animation)
- **Dynamic verb display** - shows LLM-chosen action verb
- **Session metadata bar** - fixed at bottom showing TURN, FRAMES, SESSION
- **Shared Memory toggle** - accumulates frames in session canvas
- **Lightbox** - click images to view full size
- Real-time WebSocket updates
- Inline image rendering with grids for multi-image responses

### Resonator: KV Cache Metadata

When Resonator is invoked, it receives runtime metadata:

```
[KV CACHE METADATA]
TURN: 3
PLATE NUMBER: 4 (use Roman numeral: IV)
FRAMES IN MEMORY: 3
SESSION: resonance-field-20260104

[USER PROMPT]
Your message here...
```

**Style Modes** (invoke as commands):
- `scientific` / `PLATE MODE` → Victorian scientific illustration
- `cinema` → Cinematic frames, film grain
- `blueprint` → Technical drawings, grid paper
- `dream` → Surreal, impossible geometry
- `minimal` → Clean, modern, sparse

## Shared Visual Memory

When `--shared-memory` or the UI toggle is enabled:

1. **Session canvas folder** created: `canvas/{script}/{session_id}/`
2. **All previous frames** loaded as context for every daimon call
3. **New Dreamer images** saved to the session canvas
4. **Frame count** displayed in UI

This creates the "go deeper" capability - you can keep iterating and each generation sees all previous frames.

### Canvas Structure

```
canvas/
├── council/
│   ├── 20260104_153022/        # Session folder
│   │   ├── frame_001.jpg
│   │   ├── frame_002.jpg
│   │   └── frame_003.jpg
│   └── midnight/               # Named session
│       └── frame_001.jpg
├── stream/
│   └── deep_exploration/
│       └── frame_001.jpg
└── ui/
    └── 20260104_160045/
        └── frame_001.jpg
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | For Gemini daimones | Google Gemini API key (Flash, Pro, Dreamer, Director, Resonator) |
| `ANTHROPIC_API_KEY` | For Claude daimones | Claude API key (Opus, council.py reflections) |

## Installation

```bash
pip install httpx requests fastapi uvicorn websockets python-dotenv
```

## Key Flags

| Flag | Scripts | Description |
|------|---------|-------------|
| `--shared-memory` / `-m` | daimon, council | Enable shared visual memory |
| `--session` / `-s` | daimon, council | Named session for persistence |
| `--only` | daimon, council | Only these daimones participate |
| `--image` / `-i` | daimon | Ask Dreamer to render |
| `--context` / `-c` | resonate, daimon, council | Additional context image |
| `--no-render` | council | Skip image rendering |

## Inspiration

See `memory/genesis-danielle-fong-thread.md` for the original vision that inspired this skill.
