# Core Persona Model Template

Use this section skeleton when creating `{name}Model.md`. Adapt sections to the subject—omit what doesn't apply, add domain-specific sections as needed.

## Frontmatter

See `frontmatter-schema.md` for the full `type: user-model` spec.

## Required Sections

### Persona
One paragraph: who the person is, their primary roles, relationship to the user, location, household. Establish context for everything that follows.

> Example (Mary): "Partner of Tom di Mino. Poet, editor, and publishing professional."
> Example (Tom): "Independent scholar, founder of Minoan Mystery LLC, and builder of AI systems at Aldea Inc."

### Education
Reverse chronological. Include degree, institution, years, thesis if applicable. Note first-generation status or other contextual details.

### Career Timeline
Table format: `Period | Role | Organization`. Include job changes, career pivots, and gaps. Note self-reported tenure when it differs from inferred dates.

### Worldview
3-5 bullet points or paragraphs capturing the subject's core beliefs, philosophical positions, and value system. Draw from their writing and stated positions, not inference. Include key intellectual influences (scholars, books, traditions).

### Writing Voice
Brief characterization (2-3 sentences) of the subject's writing across modes. Point to supplementary dossiers for detailed analysis.

> Example: "Formally controlled poetry (ottava rima, modified tanka), colloquial diction. Medieval source texts fused with contemporary experience."

### Personal
Bullet list: nicknames, birth year/location, heritage, family, partner, pets, residence history, dietary/health notes, spiritual practice.

### Online Presence
Table: `Platform | Handle/URL`. Include all known public accounts with verification notes.

## Optional Sections

### Health
Include only if the subject has disclosed health information in their writing. Respect the boundary between what's published and what's private.

### Community
Clubs, organizations, events, alumni groups. Indicates social anchoring and connection patterns.

### Research Domains (for scholars/researchers)
Table: `Domain | Focus`. Maps the subject's expertise areas.

### Holistic/Niche Roles
For subjects with distinctive side projects or brand associations (e.g., Perennial Collective tea brand). Include role clarification (owner vs. contributor).

### Supplementary Dossiers
Final section before "Relationship with AI" (if applicable). Lists all dossier files and archive directories with one-line descriptions.

```markdown
## Writing Dossiers

Supplementary dossiers (on-demand):
- `{platform}-{name}.md` — Voice analysis, worldview markers, calibration quotes
- `archive/` — Full scraped content
```

### Relationship with AI
How the subject interacts with AI tools. Direct (uses Claude Code) or indirect (partner uses it on their behalf).

## Adaptation Notes

- **Non-writers**: Omit Writing Voice; expand Communication Style (verbal patterns, meeting behavior)
- **Public figures observed at a distance**: Use `type: social-dossier` instead of `type: user-model`. Dossiers describe people observed; user models describe collaborators.
- **Children/dependents**: Minimal model. Persona, Personal, Health if relevant. No Worldview or Career.
- **Pets**: Use `category: pet-model`. Sections: Persona, Health, Diet, Preferences, Vet Questions.
