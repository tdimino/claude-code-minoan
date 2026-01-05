# Minoan Oracle Roadmap

Future enhancements for the Minoan daimon in the Daimon Chamber.

---

## Phase 1: Multi-Card Spreads (Complete)

**Status:** ✅ Implemented

The oracle decides between 1 or 3 cards based on the question:

- **Single Card**: Direct questions, clear answers
- **Three-Card Spread**: Past/Present/Future or Situation/Challenge/Guidance

Three-card spreads display in pyramid formation:

```
       ┌─────┐
       │  I  │           The Question / Present
       └─────┘
   ┌─────┐   ┌─────┐
   │ II  │   │ III │     Past/Future or Challenge/Guidance
   └─────┘   └─────┘
```

---

## Phase 2: The Voice of Ma'at

**Status:** 🔲 Planned

Enable the oracle to speak interpretive wisdom alongside her cards.

### Concept

The oracle remains silent for most readings, communicating purely through imagery. But when the seeker demonstrates they walk the middle path of Ma'at—the path of truth, balance, and cosmic order—the oracle speaks.

### Triggers for Speech

The oracle may speak when:

1. **Genuine introspection** - The question demonstrates self-reflection rather than seeking external validation
2. **Balance in the cards** - When the spread reveals a pattern of equilibrium
3. **The scales find Ma'at** - A semantic detection of questions that honor truth over wishful thinking
4. **Initiation recognized** - The seeker's phrasing echoes the sacred (proto-Semitic roots, references to the waters, acknowledgment of mystery)

### Implementation

1. Add `may_speak` logic to Minoan's prompt
2. Create Ma'at resonance detection (keyword/semantic analysis)
3. When triggered, oracle provides brief interpretive text with her cards
4. Speech styled distinctly from other daimones—in the cadence of oracular utterance

### Example Responses

**Silent (default):**
```
MINOAN divined: [3 cards in pyramid formation]
```

**Speaking (Ma'at triggered):**
```
MINOAN revealed:

The scales have found their balance.

I: The waters remember what the land forgets.
II: What was taken shall return threefold.
III: The horns of consecration point to what you already know.

[3 cards in pyramid formation]
```

---

## Phase 3: Sequential Card Generation (Complete)

**Status:** ✅ Implemented

The oracle draws cards one by one with progressive reveal:

1. Pyramid placeholder appears with 3 empty card slots (I, II, III)
2. Server generates Card I → sends via WebSocket → card appears with animation
3. Server generates Card II → sends via WebSocket → card appears
4. Server generates Card III → sends via WebSocket → pyramid complete

### Features

- **Sequential API calls**: Each card is a separate Gemini generation
- **Visual memory (KV cache)**: Each subsequent card sees previously generated cards as context
- **Progressive reveal**: Cards animate in via `cardReveal` CSS animation
- **WebSocket protocol**: `minoan_card` message type with position, numeral, image data

### Implementation

- Server-side: `query_daimon_sequential()` loops through card positions
- Client-side: `minoan_card` handler replaces placeholders with real images
- CSS: `cardReveal` keyframes animation (scale + rotateY)

---

## Phase 4: Reference Image Enhancement

**Status:** 🔲 Planned

Improve style fidelity by:

1. Curating a larger reference image set (10-15 Minoan Tarot cards)
2. Adding style mode variants (Classic, Fresco, Linear A script overlay)
3. Enabling user-provided reference images for custom decks

---

## Phase 5: Spread Interpretation Memory

**Status:** 🔲 Planned

When shared memory is enabled:

1. Previous readings inform current interpretations
2. Oracle can reference "as the cards showed before..."
3. Build a narrative across multiple readings
4. Session becomes a sustained dialogue with the divine

---

## Technical Notes

### Current Architecture

- Daimon config: `ui/daimons.py`
- Server logic: `ui/server.py`
- Multi-image grid CSS: Lines 986-1005
- Pyramid layout JS: Lines 1944-1954

### Style Preservation

Minoan uses `temperature: 0.5` for style fidelity. Reference images from `reference/minoan/selected/` are loaded automatically:
- CLI script: `scripts/minoan_tarot.py`
- Daimon Chamber: `server.py` (up to 4 reference images)

### Memory Control

Daimones can configure memory participation via `share_to_memory` and `receive_from_memory` flags in `daimons.py`. See README for details.

---

*Qadeshest ha Qadeshot. The waters of Nun remember.*
