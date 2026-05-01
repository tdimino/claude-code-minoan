# Roadmap — From Terminal to Live Social Scene

## The Vision

An IRC-like channel system where players join encrypted or public channels, chat and emote in character, exchange credits, watch AI-driven NPCs enter and exit, and experience live narrative events—all rendered in the Imperial CRT aesthetic. The Mos Eisley Cantina as a persistent AI social scene.

## Channel Types

| Channel | Access | Aesthetic | Who's There |
|---|---|---|---|
| `#cantina` | Public | Ambient cantina noise, green phosphor | Players + AI patrons (Bothans, smugglers, droids) |
| `θ-7` (current) | Encrypted | Classified red, intercept stream | IMP-INT operators only. AI handler Cotla issues directives. |
| `#echo-cell` | Encrypted, invite-only | Rebel green, burst transmissions | ECHO cell members + Vorian (undercover) |
| `#bridge-chimaera` | Imperial Navy | Blue-cyan, tactical displays | Bridge officers, AI commander |
| `#black-sun` | Criminal, passcode-gated | Dark amber, Hutt aesthetic | Underworld contacts. Credit laundering, bounties. |

## Social Mechanics

**Chat modes:**
- `/say <message>` — in-character speech (green, speaker tag)
- `/emote <action>` — character actions (dim italic)
- `/whisper <target> <message>` — private, encrypted sidebar
- `/ooc <message>` — out-of-character (grey, bracketed)

**World actions:**
- `/tip <target> <amount> IC` — credit transfer (red, logged by the Empire)
- `/scan` — bio-signature sweep of current channel occupants
- `/dossier <target>` — pull up a character's file (holographic modal)
- `/enter` / `/exit` — arrive at or leave a channel (system message)
- `/encrypt <level>` — set message encryption (visible as Aurebesh to unauthorized readers)

**AI-driven events:**
- NPCs enter and exit channels on schedules
- AI characters respond to `/say` directed at them
- Narrative events fire across channels (Ora's transmission intercepted in θ-7 while the conversation happens in #cantina)
- Credit transactions between AI and player create economic state

## Architecture

```
┌──────────────────────────────────────┐
│  Client (HTML/React)                  │
│  CRT atmosphere + chat UI             │
│  Aurebesh decrypt on incoming msgs    │
│  Holographic dossier modals           │
│  Web Audio (ambient per channel)      │
├──────────────────────────────────────┤
│  WebSocket Layer                      │
│  Channel join/leave                   │
│  Message routing                      │
│  Presence (who's in #cantina)         │
├──────────────────────────────────────┤
│  Server (Cloudflare Workers/Durable)  │
│  Channel state (Durable Objects)      │
│  Credit ledger                        │
│  Message history per channel          │
│  AI soul orchestration                │
├──────────────────────────────────────┤
│  Soul Engine (Open Souls / Daimonic)  │
│  Per-NPC WorkingMemory                │
│  Mental processes (idle, converse,    │
│    suspicious, flee)                  │
│  useSharedContext across channels     │
│  scheduleEvent for narrative arcs     │
└──────────────────────────────────────┘
```

**Cloudflare stack:**
- Durable Objects for channel state (persistent WebSocket, per-channel memory)
- Workers for HTTP/API endpoints
- KV for user profiles + credit balances
- R2 for character portraits + audio assets
- Agents SDK with Code Mode for soul orchestration

## The SWG Connection

Not a game rebuild—a social interface rebuild. SWG's cantinas worked because characters had persistent identity, emotes created shared narrative, the economy gave interactions stakes, and NPCs were part of the scenery. The AI version replaces scripted NPCs with souls that remember, react, and improvise. Ora doesn't repeat the same lines—he evolves. Cotla responds to field reports. The Cantina becomes a persistent AI social scene where every visit is different.

## Phases

| Phase | Milestone | Stack |
|---|---|---|
| v1 (current) | Static HTML terminal, single-player intercept | HTML/CSS/JS, Cloudflare Pages |
| v2 (this plan) | Multi-dossier filesystem, responsive, documented | Same |
| v3 | React extraction, component library | React/Next.js, Cloudflare Pages |
| v4 | Soul wiring — live AI responses per entity | Open Souls Engine, OpenRouter |
| v5 | Single-channel multiplayer (#cantina) | Cloudflare Workers + Durable Objects |
| v6 | Multi-channel, encrypted channels, credit economy | Full Cloudflare stack |
| v7 | Public deployment — The Cantina as persistent AI social scene | Custom domain, auth, moderation |
