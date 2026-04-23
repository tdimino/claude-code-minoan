# Travel Requirements Gathering Workflow

This systematic workflow ensures comprehensive travel itinerary planning through structured phases.

## Overview

The workflow progresses through 5 phases:
1. **Initial Setup** - Create folder structure, capture initial request
2. **Discovery** - Ask 5 foundational yes/no questions with smart defaults
3. **Context Research** - Use MCP servers to gather detailed information
4. **Expert Detail** - Ask 5 specific questions based on research findings
5. **Requirements Specification** - Generate comprehensive final itinerary

---

## Phase 1: Initial Setup & Request Capture

### 1.1 Create Requirements Folder

Use the `create_requirements_folder.py` script:

```bash
python scripts/create_requirements_folder.py "<user request>" [base_path]
```

This creates:
- Timestamped folder: `YYYY-MM-DD-HHMM-slug/`
- `00-initial-request.md` - User's request and key elements
- `metadata.json` - Progress tracking
- `.current-requirement` file - Points to active folder

### 1.2 Extract Key Elements

From the user's request, identify and document in `00-initial-request.md`:
- **Logistical constraints**: Dates, accommodations, budget, transportation
- **Previous experience**: Past travel, capabilities, comfort levels
- **Specific destinations**: Must-visit locations, activities requested
- **Intentions**: Cultural, spiritual, adventure, relaxation objectives
- **Dietary needs**: Restrictions, preferences, halal/kosher/vegan requirements
- **Physical capability**: Hiking ability, mobility considerations

---

## Phase 2: Discovery Questions

### 2.1 Create Discovery Questions File

Create `01-discovery-questions.md` with 5 foundational yes/no questions covering:

1. **Activity Intensity**: Daily schedule pacing (intense vs. relaxed)
2. **Social Preferences**: Crowd tolerance at attractions, solitude needs
3. **Daily Structure**: Single-focus days vs. multi-activity combinations
4. **Amenities Priority**: Modern comfort vs. rustic/authentic experiences
5. **Flexibility**: Weather-responsive planning vs. fixed schedules

### 2.2 Question Format

Each question MUST include:
- Clear yes/no format
- **Smart default** with reasoning
- Implications for itinerary planning

Example:
```markdown
## Q1: Should the itinerary prioritize intense daily physical activity?

**Default if unknown:** No - One major activity per day with integration time

**Reasoning:** Most travelers benefit from pacing to absorb experiences.
Intensive daily schedules often lead to exhaustion and reduced enjoyment.
Based on typical travel patterns, balanced intensity yields better outcomes.

**Implications:**
- Affects number of sites visited per day
- Determines rest period requirements
- Influences accommodation selection (location vs. amenities)
- Impacts dining timing and style
```

### 2.3 Ask Questions ONE at a Time

**CRITICAL PROCESS**:
1. Write ALL 5 questions to `01-discovery-questions.md` BEFORE asking any
2. Present ONE question per message to user
3. Include the smart default and reasoning
4. Wait for user confirmation or adjustment
5. Record answer internally, but DO NOT create `02-discovery-answers.md` yet
6. Move to next question
7. ONLY AFTER all 5 answered, create `02-discovery-answers.md` with full context
8. Update `metadata.json` progress tracker

---

## Phase 3: Targeted Context Research

### 3.1 Identify Research Gaps

Based on discovery answers, determine what information is needed:
- **Destination specifics**: Weather patterns, seasonal considerations, terrain
- **Cultural context**: Local customs, dining culture, social etiquette, language
- **Practical logistics**: Transportation options, site hours, booking requirements
- **Dietary research**: Restaurant availability, cuisine characteristics, special needs
- **Safety factors**: Weather risks, terrain difficulty, health precautions
- **Accommodation context**: Location advantages, amenities, accessibility

### 3.2 Use MCP Servers for Research

**Perplexity (`mcp__perplexity__search`)**:
Use for comprehensive, detailed research on:
- General destination information and context
- Weather patterns and seasonal climate data
- Cultural customs, etiquette, and local practices
- Dining options, restaurant profiles, cuisine information
- Transportation systems and logistics
- Historical/cultural background of sites

Example:
```
mcp__perplexity__search(
  query="November weather Kyoto Japan temperature rainfall patterns",
  detail_level="detailed"
)
```

**Exa Web Search (`mcp__plugin_exa-mcp-server_exa__web_search_exa`)**:
Use for real-time, current information:
- Recent travel reports and reviews
- Current pricing and availability
- Up-to-date venue information
- Recent news affecting travel plans

Example:
```
mcp__plugin_exa-mcp-server_exa__web_search_exa(
  query="best traditional kaiseki restaurants Kyoto 2025",
  numResults=5
)
```

### 3.3 Research Execution Strategy

**Run searches in PARALLEL when possible**:
```
Multiple independent searches should be executed simultaneously in one message
to maximize efficiency. Group related topics:

- All weather-related queries together
- All dining-related queries together
- All cultural/activity queries together
```

**Document findings in `03-context-findings.md`**:
Organize by topic:
1. Cafe culture / beverage options
2. Dining options (general and dietary-specific)
3. Weather patterns and safety protocols
4. Accommodation context
5. Transportation and logistics
6. Cultural customs and etiquette
7. Site-specific details (hours, booking, accessibility)

Include confidence levels:
- **High confidence**: Primary source verification, multiple corroborating sources
- **Medium confidence**: Secondary sources, limited verification
- **Speculative**: Interpretive, requires on-ground confirmation

---

## Phase 4: Expert Detail Questions

### 4.1 Create Detail Questions File

Now that you have deep research context, create `04-detail-questions.md` with 5 expert questions that address:

1. **Specific preferences** revealed by research gaps
2. **Trade-offs** between options discovered
3. **Prioritization** among multiple good choices
4. **Ritual/experience requirements** for special activities
5. **Timing preferences** for daily rhythm

### 4.2 Expert Question Characteristics

These questions should:
- Reference SPECIFIC findings from Phase 3 research
- Offer concrete options (not abstract choices)
- Include smart defaults based on research + discovery answers
- Address practical implementation details

Example:
```markdown
## Q1: Greek coffee culture vs. matcha - immersion preference?

Research shows matcha is not readily available in Sitia cafes. However,
exceptional Greek coffee culture exists at waterfront venues:
- Kafe-Cafe: 6:30 AM-1:30 AM, seaside, specialty coffee
- Plaza Lounge Cafe: Panoramic port/town views

Should the itinerary embrace authentic Greek coffee culture (frappé, freddo
espresso, elliniko) as the people-watching beverage, or is bringing your own
matcha powder essential?

**Default if unknown:** Embrace Greek coffee culture as refined local
immersion, aligning with luxury-through-authenticity philosophy.

**Implications:**
- Greek coffee = Feature Kafe-Cafe and Plaza Lounge as primary venues
- Matcha essential = Note to bring powder, request hot water at cafes
```

### 4.3 Ask Questions ONE at a Time

Same process as discovery phase:
1. Write all 5 questions first
2. Ask one at a time
3. Wait for answers
4. Only after all 5, create `05-detail-answers.md`
5. Update metadata progress

---

## Phase 5: Requirements Specification

### 5.1 Generate Comprehensive Spec

Create `06-requirements-spec.md` synthesizing ALL gathered information:

**Required Sections**:

1. **Problem Statement**
   - Traveler's objectives and constraints
   - Balance of priorities (spiritual/cultural/physical/safety)
   - Previous experience context

2. **Solution Overview**
   - High-level itinerary approach
   - Key sites and experiences
   - Integration philosophy

3. **Functional Requirements**
   - FR1: Sacred/Special Sites (each with date, purpose, logistics)
   - FR2: Cultural Immersion Activities
   - FR3: Dining Experiences (specific restaurants matched to days)
   - FR4: Integration & Contemplation Windows
   - FR5: [Additional category as needed]

4. **Technical Requirements**
   - TR1: Weather Safety & Monitoring
   - TR2: Transportation & Logistics
   - TR3: Packing & Equipment
   - TR4: Accommodation Details
   - TR5: Cultural Etiquette & Rules

5. **Day-by-Day Itinerary**
   - Complete breakdown for each day
   - Morning/afternoon/evening structure
   - Specific venues, drive times, activities
   - Integration windows built in
   - Weather contingencies noted

6. **Acceptance Criteria**
   - How to measure trip success
   - Must-complete experiences
   - Safety protocols followed
   - Cultural immersion achieved

7. **Assumptions**
   - Physical capability levels
   - Flexibility in preferences
   - Weather cooperation expectations
   - Service availability

8. **Success Metrics**
   - Primary, secondary, tertiary success markers

### 5.2 Writing Style

- **Imperative form** for instructions
- **Specific details** with exact names, times, prices
- **Realistic timings** accounting for travel, rest, meals
- **Weather-responsive** alternatives throughout
- **Integration windows** explicitly scheduled
- **Safety protocols** clearly marked as non-negotiable

---

## Metadata Management

Throughout the workflow, keep `metadata.json` updated:

```json
{
  "id": "feature-slug",
  "started": "ISO-8601-timestamp",
  "lastUpdated": "ISO-8601-timestamp",
  "status": "active",
  "phase": "discovery|context|detail|complete",
  "progress": {
    "discovery": {"answered": 0, "total": 5},
    "detail": {"answered": 0, "total": 5}
  },
  "contextFiles": ["paths/to/referenced/files"],
  "relatedTopics": ["list", "of", "key", "topics"]
}
```

Update `phase` and `progress` as you move through workflow.

---

## Key Success Factors

1. **Always write questions before asking them** - ensures complete coverage
2. **One question at a time** - prevents user overwhelm, gets better answers
3. **Smart defaults are crucial** - makes decision-making easy
4. **Parallel MCP searches** - maximizes efficiency in Phase 3
5. **Specific > Abstract** - reference actual restaurants, times, prices in Phase 4-5
6. **Weather safety first** - especially for hiking/outdoor activities
7. **Integration windows explicit** - schedule rest, contemplation, flexibility
8. **Document everything** - capture all research, reasoning, decisions

---

## Common Pitfalls to Avoid

- ❌ Asking all questions at once (overwhelming)
- ❌ Creating answer files before all questions asked
- ❌ Generic questions without research context (Phase 4)
- ❌ Forgetting weather contingencies
- ❌ Unrealistic timing (no travel/rest buffers)
- ❌ Ignoring dietary restrictions until late
- ❌ Abstract recommendations without specific venues
- ❌ Missing integration/contemplation windows

---

## Workflow Completion Checklist

Phase 1:
- [ ] Requirements folder created
- [ ] Initial request documented
- [ ] Key elements extracted

Phase 2:
- [ ] 5 discovery questions written to file
- [ ] All questions asked one at a time
- [ ] Answers recorded in 02-discovery-answers.md

Phase 3:
- [ ] Research gaps identified
- [ ] MCP searches executed (parallel when possible)
- [ ] Findings documented in 03-context-findings.md

Phase 4:
- [ ] 5 expert detail questions written to file
- [ ] Questions reference specific research findings
- [ ] All questions asked and answered
- [ ] Answers recorded in 05-detail-answers.md

Phase 5:
- [ ] Comprehensive requirements spec created
- [ ] All required sections complete
- [ ] Day-by-day itinerary detailed
- [ ] Safety protocols clearly marked
- [ ] README.md summary created

**Trip is ready for implementation when all checkboxes complete!**
