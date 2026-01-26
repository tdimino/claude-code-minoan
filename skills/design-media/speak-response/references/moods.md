# Qwen3-TTS Mood Presets

Natural language instructions for the CustomVoice model. The `-i/--instruct` parameter accepts any natural language description of voice qualities.

## Core Presets (Used by /speak)

| Preset | Instruction |
|--------|-------------|
| `calm` | "calm, soothing, gentle pace" |
| `warm` | "warm, empathetic, nurturing tone" |
| `excited` | "joyful, excited, enthusiastic" |
| `serious` | "serious, measured, authoritative" |
| `gentle` | "soft, gentle, whispered" |
| `encouraging` | "encouraging, uplifting, sincere" |
| `contemplative` | "thoughtful, slow pace, reflective" |

## Therapeutic/Supportive

For therapeutic conversations like Dr. Shefali:

| Preset | Instruction |
|--------|-------------|
| empathetic | "warm, empathetic, gentle pace, nurturing tone" |
| grounding | "calm, steady, grounding, reassuring" |
| encouraging | "encouraging, uplifting, sincere enthusiasm" |
| contemplative | "thoughtful, slow pace, contemplative, soft" |
| validating | "warm, understanding, gentle affirmation" |

## Conversational

| Preset | Instruction |
|--------|-------------|
| neutral | (no instruction - natural voice) |
| friendly | "friendly, casual, warm" |
| professional | "professional, clear, measured" |
| playful | "playful, light, with a smile" |
| curious | "curious, interested, questioning tone" |

## Dramatic

| Preset | Instruction |
|--------|-------------|
| serious | "serious, measured, authoritative" |
| dramatic | "dramatic, with emphasis and pauses" |
| whispered | "whispered, intimate, soft" |
| urgent | "urgent, rapid pace, intense" |
| mysterious | "mysterious, low, slow and deliberate" |

## Prosody Modifiers

Combine with any preset by appending:

| Modifier | Effect |
|----------|--------|
| "slow and deliberate" | Reduces pace |
| "with dramatic pauses" | Adds pauses between phrases |
| "rising intonation" | Questioning/uncertain feel |
| "emphatic on key words" | Stress important words |
| "flowing and musical" | Smooth, melodic delivery |

## Speaker + Mood Combinations

Different speakers pair well with different moods:

| Speaker | Best For |
|---------|----------|
| Ryan | Professional, serious, authoritative |
| Vivian | Warm, nurturing, therapeutic |
| Serena | Calm, gentle, contemplative |
| Dylan | Friendly, casual, playful |
| Eric | Serious, dramatic, commanding |
| Aiden | Encouraging, uplifting, energetic |

## Example Commands

```bash
# Therapeutic calm (Vivian is great for this)
scripts/speak.sh "Take a deep breath." Vivian "calm, soothing, slow pace"

# Excited announcement
scripts/speak.sh "We did it!" Ryan "joyful, excited, enthusiastic"

# Serious warning
scripts/speak.sh "This is important." Eric "serious, measured, emphatic"

# Encouraging affirmation
scripts/speak.sh "You're doing great." Vivian "warm, encouraging, sincere"

# Contemplative reflection
scripts/speak.sh "Let's think about this together." Serena "thoughtful, slow pace, gentle"

# Whispered secret
scripts/speak.sh "I have something to share with you." Serena "whispered, intimate, soft"
```

## Custom Instruction Tips

The model understands rich natural language. Be descriptive:

- **Emotion**: joyful, melancholic, anxious, calm, excited, contemplative
- **Pace**: slow and deliberate, rapid and energetic, measured, hesitant
- **Intensity**: soft and gentle, loud and commanding, whispered, emphatic
- **Style**: warm and nurturing, professional, playful, dramatic, matter-of-fact
- **Persona**: "like a wise grandmother", "like a friendly neighbor"

Example combining multiple aspects:
```bash
scripts/speak.sh "Welcome home." Vivian "warm, gentle, slow pace, with a smile in the voice"
```
