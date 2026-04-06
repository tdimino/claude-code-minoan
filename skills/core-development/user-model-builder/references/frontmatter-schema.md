# UserModel Frontmatter Schema

## Core Persona (`{name}Model.md`)

```yaml
---
title: "{Full Name} — Core Persona"
type: user-model
subject: "{Full Name}"
category: persona
email: "user@example.com"        # Use ~ if unknown
phone: "+1XXXXXXXXXX"            # Use ~ if unknown
tags: [persona, {first-last}, {domain1}, {domain2}]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active                   # active | draft
---
```

**Required**: type, subject, category, email, phone, tags, created, updated, status

## Social Dossier

```yaml
---
title: "{Platform} — {Publication Name}"
type: social-dossier
subject: "{Full Name} (@handle)"
category: {platform}-analysis    # twitter-analysis, substack-analysis, blog-archive
tags: [{platform}, {publication}, {subject-name}]
created: YYYY-MM-DD
updated: YYYY-MM-DD
corpus: "{N} posts, {date range}, ~{N} words"
status: active                   # active | archived | verified
---
```

**Required**: type, subject, category, tags, created, updated, corpus, status

- `status: active` — platform is live and content may grow
- `status: archived` — platform is dead or dormant; content is frozen
- `status: verified` — content verified against primary sources

## Voice Model

```yaml
---
title: "{Platform} Voice — {Handle}"
type: voice-model
subject: "{Full Name}"
category: {platform}-voice
tags: [voice-model, {platform}, {subject-name}]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
---
```

Use for platform-specific voice calibration files (e.g., `tomTwitterModel.md`).

## Archive File (Individual Post)

```yaml
---
title: "{Post Title}"
date: YYYY-MM-DD
source_url: "https://..."
archived_from: "{platform}"      # substack, twitter, wayback, perennial-collective
archive_date: YYYY-MM-DD
---
```

## Pet Model

```yaml
---
title: "{Pet Name} — Pet Model"
type: user-model
subject: "{Pet Name}"
category: pet-model
email: ~
phone: ~
tags: [pet-model, {pet-name}, {species}]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
---
```

## INDEX Files

### Master Index (`~/.claude/userModels/INDEX.md`)

```yaml
---
title: "User Models Index"
type: index
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
---
```

### Archive Index (`archive/INDEX.md`)

```yaml
---
title: "{Subject} — Writing Archive"
type: archive-index
subject: "{Full Name}"
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
---
```
