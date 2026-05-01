# Soul Integration

Project Thorn is a single-file HTML template for narrative AI terminals. No build step, no dependencies. Fork it, change the CSS variables, replace the transcript blocks, and you have a new themed terminal. Expand it into React/Vue/Svelte when you need live AI souls behind the commands. The atmosphere layer (scanlines, vignette, CRT curvature) is framework-agnostic CSS. The audio engine is a standalone Web Audio module. The terminal dispatch is a state machine ready to wire into any LLM backend.

## Terminal as Soul Container

The command loop already implements perception → cognition → action:

1. User types a command (perception)
2. Terminal dispatches through `TERMINAL_CMDS` (cognition)
3. Response renders in the prompt area (action)

The dossier system is a knowledge base. The intercept stream is a narrative arc driven by timed events. The state machine (`idle → running → done`) maps directly to mental process transitions. The CRT aesthetic, Aurebesh decrypt, and holographic modals are the environment in which souls manifest—not decoration, but theophany interface.

## Entity-as-Soul Pattern

Each dossier entity (Ora, Cotla, Vorian, Fenri) becomes an independent soul with its own WorkingMemory. When the user `cat`s a file, they initiate a perception that triggers the entity's mental process. Ora responds dynamically. Cotla redacts information based on the user's clearance level. Vorian's encrypted file requires a multi-turn dialogue to unlock.

## Open Souls Mapping

| Terminal Concept | Open Souls Equivalent |
|---|---|
| `TERMINAL_CMDS` dispatch | `MemoryIntegrator` — perception routing |
| Command → response | `externalDialog` cognitive step |
| `state.phase` (idle→running→done) | Mental process transitions |
| `DOSSIERS` data object | `useSoulMemory` — persistent character knowledge |
| Decrypt passphrase mechanic | `decision` cognitive step (gate) |
| Intercept stream events | `scheduleEvent` — proactive timed perceptions |
| Multi-dossier filesystem | `useSharedContext` — cross-soul state |
| Audio cue engine | Subprocess — ambient soul behavior |

## The Bazaar Model

The Bazaar is a multi-soul social scene—multiple AI personalities interacting in a shared space. Project Thorn maps naturally to this pattern. Instead of static `TERMINAL_CMDS` responses, each entity becomes a soul with its own WorkingMemory. The terminal becomes a Cantina where AI personalities enter, converse, and exit on their own schedules.

## React Extraction Path

The single-file architecture isolates three clean layers:

1. **CSS atmosphere** (scanlines, vignette, flicker, CRT curvature) — portable as a CSS module
2. **HTML structure** (grid layout, content blocks, dialog modals) — maps directly to components
3. **JS engine** (state machine, audio, terminal) — extractable into hooks/stores

A framework migration splits `index.html` into:

| Component | Source |
|-----------|--------|
| `Terminal.tsx` | Grid shell + atmosphere |
| `TranscriptBlock.tsx` | Per-line decrypt animation |
| `DossierModal.tsx` | Holographic overlay |
| `TerminalPrompt.tsx` | Command input + dispatch |
| `useAudioEngine.ts` | Web Audio hook |
| `useDecryptAnimation.ts` | Character-by-character state machine |
| `atmosphere.css` | Scanlines + vignette + flicker |

The HTML version is the prototype. The React version is the production soul container.

## Extension Points for Soul Wiring

Where to connect LLM calls into the existing command dispatch:

1. **Replace `TERMINAL_CMDS` lookup** with an async function that calls `externalDialog` on the appropriate soul. The response renders the same way—just generated instead of static.

2. **Replace dossier static HTML** with a `useSoulMemory` read that populates the modal fields dynamically. The holographic frame, sweep animation, and open/close audio stay unchanged.

3. **Replace `INTERCEPT_LOG` schedule** with `scheduleEvent` calls from soul subprocesses. NPCs can trigger intercept events based on conversation context.

4. **Add `TERMINAL_FNS` function router** alongside `TERMINAL_CMDS` strings. Functions that return promises enable async soul responses with a typing indicator.

## Example: Live Ora

Replacing `TERMINAL_CMDS['ping ora']` static response ("Request timeout—host unreachable") with a live `externalDialog` call:

```js
TERMINAL_FNS['ping ora'] = async () => {
  const response = await soul.dispatch({
    perception: 'ping',
    from: 'operator-theta-7'
  });
  return response.action.content;
};
```

Ora's soul decides whether to respond based on its WorkingMemory—was the channel severed? Does the operator have clearance? Has too much time passed since last contact?
