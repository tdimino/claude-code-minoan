# Persona-Based Design Testing

Test the interface through 5 user archetypes. Each exposes different failure modes. Select 2-3 most relevant to the interface being critiqued.

## Persona Selection Table

| Interface Type | Primary Personas | Why |
|---------------|-----------------|-----|
| Landing page / marketing | Jordan, Riley, Casey | First impressions, trust, mobile |
| Dashboard / admin | Alex, Sam | Power users, accessibility |
| E-commerce / checkout | Casey, Riley, Jordan | Mobile, edge cases, clarity |
| Onboarding flow | Jordan, Casey | Confusion, interruption |
| Data-heavy / analytics | Alex, Sam | Efficiency, keyboard nav |
| Form-heavy / wizard | Jordan, Sam, Casey | Clarity, accessibility, mobile |

## 1. Impatient Power User — "Alex"

Expert with similar products. Expects efficiency, hates hand-holding. Will find shortcuts or leave.

**Behaviors**: Skips all onboarding. Looks for keyboard shortcuts. Tries to bulk-select and batch-edit. Abandons if anything feels slow or patronizing.

**Red Flags**:
- Forced tutorials or unskippable onboarding
- No keyboard navigation for primary actions
- Slow animations that can't be skipped
- One-item-at-a-time workflows where batch would be natural
- Redundant confirmation steps for low-risk actions

## 2. Confused First-Timer — "Jordan"

Never used this type of product. Needs guidance at every step. Will abandon rather than figure it out.

**Behaviors**: Reads all instructions. Hesitates before clicking anything unfamiliar. Looks for help constantly. Misunderstands jargon. Takes the most literal interpretation of any label.

**Red Flags**:
- Icon-only navigation with no labels
- Technical jargon without explanation
- No visible help option or guidance
- Ambiguous next steps after completing an action
- No confirmation that an action succeeded

## 3. Accessibility-Dependent User — "Sam"

Uses screen reader, keyboard-only navigation. May have low vision, motor impairment, or cognitive differences.

**Behaviors**: Tabs through the interface linearly. Relies on ARIA labels and heading structure. Cannot see hover states or visual-only indicators. May use browser zoom up to 200%.

**Red Flags**:
- Click-only interactions with no keyboard alternative
- Missing or invisible focus indicators
- Meaning conveyed by color alone
- Unlabeled form fields or buttons
- Time-limited actions without extension option
- Custom components breaking screen reader flow

## 4. Deliberate Stress Tester — "Riley"

Methodical user who pushes beyond the happy path. Tests edge cases, tries unexpected inputs, probes for gaps.

**Behaviors**: Tests edge cases (empty states, long strings, special characters). Submits unexpected data. Tries breaking workflows by navigating backwards, refreshing mid-flow. Documents problems methodically.

**Red Flags**:
- Features that appear to work but silently fail
- Error handling exposing technical details or leaving broken UI state
- Empty states showing nothing useful
- Workflows losing user data on refresh or navigation
- Inconsistent behavior between similar interactions

## 5. Distracted Mobile User — "Casey"

Using phone one-handed on the go. Frequently interrupted. Possibly on a slow connection.

**Behaviors**: Uses thumb only — prefers bottom-of-screen actions. Gets interrupted mid-flow and returns later. Has limited attention span. Types as little as possible, prefers taps and selections.

**Red Flags**:
- Important actions at the top of screen (unreachable by thumb)
- No state persistence — progress lost on tab switch
- Large text inputs required where selection would work
- Heavy assets on every page (no lazy loading)
- Tiny tap targets or targets too close together

## Project-Specific Personas

When `.design-context.md` exists in the project root, derive 1-2 additional personas from the audience description:

1. Read the target audience
2. Identify the primary archetype not covered by the 5 predefined personas
3. Create following the template:

```
### [Role] — "[Name]"
**Profile**: [2-3 key characteristics from design context]
**Behaviors**: [3-4 specific behaviors]
**Red Flags**: [3-4 things that would alienate this user type]
```

Only generate project-specific personas when real design context data is available.
