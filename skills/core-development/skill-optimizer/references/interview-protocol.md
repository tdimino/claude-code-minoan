# Skill Interview Protocol

Source: "Skill Builder: Claude Code Skill Development System" (March 2026), supplemented by Thariq (Anthropic) on gotchas methodology.

Use this protocol during Step 1 of the Skill Creation Process. Do not skip the interview. Do not start drafting until the exit criteria are met.

## 6 Required Questions

Ask these in order. Each question has probing follow-ups for when the initial answer is insufficient.

### Q1. What does this skill enable Claude to do?

Get specifics. "Help with data analysis" is not an answer. "Query our Snowflake warehouse using helper functions, build retention cohorts, and output formatted reports" is an answer.

**Probing**: "Is this something Claude can't do at all, or something it does inconsistently or incorrectly?"

### Q2. Give 2-3 concrete use cases

Real scenarios. What would the user actually say to trigger this? What does the input look like? What does the output look like?

**Probing**: "Walk me through what happens step by step for each case. What does the user type, and what should they see when it's done?"

### Q3. What tools, APIs, or dependencies does it need?

Built-in capabilities only? MCP servers? Specific packages? External APIs? CLI tools?

**Probing**: "Is there an existing tool, script, or workflow you use for this today that the skill should replicate or improve on?"

### Q4. What does Claude get wrong today without this skill?

This is the most important question. If Claude already handles it fine, the skill is not worth building. Identify the specific failure modes, bad defaults, or missing knowledge that justify the skill's existence.

**Probing**: "Can you show me an example of Claude failing at this? What did it produce, and what should it have produced?"

### Q5. What does success look like?

Describe the ideal output. Format, structure, quality bar. How would the user know the skill worked versus did not work?

**Probing**: "If I showed you two outputs -- one from a skill-assisted run and one without -- what would you look for to tell them apart?"

### Q6. What are the edge cases?

What inputs break things? What should the skill explicitly NOT do? What adjacent tasks should it avoid triggering on?

**Probing**: "What is the most common way this fails when you do it manually?"

## Pushback Rules

These rules prevent building weak or unfocused skills. Apply them during the interview.

**Vague scope**: If the user gives a one-sentence answer to Q1, push back:
> "That is too vague for a good skill. Can you walk me through exactly what Claude should do step by step? What is the input, what happens in the middle, what is the output?"

**No concrete use cases**: If the user cannot articulate 2 concrete use cases for Q2, push back:
> "If we cannot name 2 real scenarios, the skill might not be worth building yet. Let's figure out the specific situations where this saves you time."

**Overly broad scope**: If the user says "just make it work for everything," push back:
> "Skills that try to do everything trigger on nothing. Let's narrow to the 2-3 highest-value workflows and nail those."

**Missing failure analysis**: If the user skips Q4 or can't answer it, push back:
> "This is the most important input. The skill should contain the knowledge that Claude is missing. Without knowing what fails today, we are guessing."

## Gotchas as Gold

From Thariq: "The highest-signal content in any skill is the Gotchas section."

Every failure mode surfaced by Q4 becomes a gotcha entry in the skill. Gotchas are not afterthoughts -- they are the primary value a skill provides. They push Claude out of its normal way of thinking, which is the entire point.

**Building the gotchas list**:
1. Record every failure mode from Q4
2. For each failure, write the specific wrong behavior AND the correct behavior
3. Include the "why" -- Claude generalizes reasoning better than bare directives
4. Prioritize gotchas by frequency and severity of the failure

The gotchas section should grow over time as the skill is used on real tasks (Step 8: Iterate).

## Exit Criteria

Conclude the interview when you have all of the following:

- [ ] Concrete use cases with realistic user prompts (from Q2)
- [ ] A failure mode inventory -- specific things Claude gets wrong (from Q4)
- [ ] Verifiable success criteria -- how to tell the skill worked (from Q5)
- [ ] Clear boundaries -- what the skill does NOT do (from Q6)

If any of these are missing, continue the interview. Do not proceed to Step 2.
