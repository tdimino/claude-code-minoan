# Netlify Integration

The deployment skill. Production-grade Netlify deployment and serverless function management, with battle-tested webhook patterns from the Twilio-Aldea SMS platform that solved a 60% message loss problem.

**Last updated:** 2026-01-02

**Reflects:** Netlify official documentation, Netlify Functions runtime, Next.js on Netlify patterns, and production webhook architectures from Twilio-Aldea.

---

## Why This Skill Exists

Deploying to Netlify is straightforward until you need serverless functions that handle webhooks reliably. The default pattern---process the webhook in the request handler---fails under load because Netlify Functions have hard timeout limits (10s free, 26s Pro). For SMS/telephony webhooks, this causes 60% message loss.

This skill encodes the solution: immediate 200 OK response followed by background processing. It also covers the full Netlify surface---`netlify.toml` configuration, environment variable management, Next.js integration, debugging, and local development with `ntl dev`. Reference docs include both custom production patterns and official Netlify documentation for authoritative detail.

---

## Structure

```
netlify-integration/
  SKILL.md                                     # Complete deployment guide
  README.md                                    # This file
  assets/
    .env.example                               # Environment variable template
    netlify.toml.template                      # Starter netlify.toml
    webhook_function_template.ts               # Production webhook handler
    examples/
      api-route.ts                             # Next.js API route example
      background-function.ts                   # Background processing function
      webhook-function.ts                      # Minimal webhook handler
      netlify.toml                             # Example configuration
  references/
    debugging.md                               # Console logging, error handling, local testing
    environment_variables.md                   # Dashboard, CLI, .env management
    functions_best_practices.md                # Function design patterns and timeouts
    netlify_config.md                          # netlify.toml reference
    production-patterns.md                     # 8 production patterns from Twilio-Aldea
    twilio_aldea_specific.md                   # SMS processing, threading, error recovery
    official-docs/
      environment-variables.md                 # Official Netlify env var docs
      functions.md                             # Official Netlify Functions docs
      netlify-toml.md                          # Official netlify.toml reference
      nextjs.md                                # Official Next.js on Netlify guide
  scripts/
    check_deployment.sh                        # Verify deployment status
    setup_env_vars.sh                          # Configure environment variables
    test_function_locally.sh                   # Local testing with ntl dev
```

Note: the `references/github/` directory contains full upstream Netlify SDK docs (releases, changelog, file structure) for authoritative reference.

---

## What It Covers

### The Webhook Timeout Pattern

The centerpiece of this skill. Solves the 60% message loss problem in webhook-driven systems:

```
Webhook arrives (e.g., Twilio SMS)
       |
       v
  Handler returns 200 OK immediately (< 200ms)
       |
       v
  Background function processes the message asynchronously
       |
       v
  Response posted via API callback
```

Without this pattern, complex webhook handlers hit the 10s timeout and Twilio retries, causing duplicate processing and lost messages.

### Netlify Functions

| Aspect | Detail |
|--------|--------|
| Runtime | Node.js 18+ / TypeScript |
| Free tier timeout | 10 seconds |
| Pro tier timeout | 26 seconds |
| Background functions | Up to 15 minutes (Pro) |
| Location | `netlify/functions/` or Next.js API routes |

### Environment Management

Three approaches, each with tradeoffs:

| Method | Scope | Version Control |
|--------|-------|----------------|
| Netlify Dashboard | Per-deploy context (production, preview, branch) | No |
| Netlify CLI (`ntl env:set`) | Same as Dashboard, scriptable | No |
| `.env` files | Local development only | Gitignored |

### Next.js Integration

Netlify auto-detects Next.js and configures build settings. Key patterns:
- API routes become serverless functions automatically
- ISR and SSR work with Netlify Edge Functions
- `netlify.toml` can override auto-detection when needed

---

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `check_deployment.sh` | Verify deployment status and build logs | `bash check_deployment.sh` |
| `setup_env_vars.sh` | Configure environment variables via CLI | `bash setup_env_vars.sh` |
| `test_function_locally.sh` | Run functions locally with `ntl dev` | `bash test_function_locally.sh` |

---

## Templates

| Template | Purpose |
|----------|---------|
| `webhook_function_template.ts` | Production webhook handler with Twilio signature validation, immediate response, and background processing |
| `background-function.ts` | Background function pattern for long-running tasks |
| `api-route.ts` | Next.js API route with error handling |
| `netlify.toml.template` | Starter configuration with common settings |
| `.env.example` | Environment variable template |

---

## Production Patterns

`references/production-patterns.md` documents 8 battle-tested patterns from the Twilio-Aldea SMS platform:

1. Immediate response + background processing
2. Twilio signature validation
3. Idempotent webhook processing
4. Conversation threading
5. Error recovery and retry logic
6. Rate limiting
7. Structured logging for debugging
8. Environment-specific configuration

---

## Requirements

- Netlify account (free tier sufficient for basic use)
- Netlify CLI (`npm install -g netlify-cli`)
- Node.js 18+
- No additional dependencies for scripts

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/netlify-integration ~/.claude/skills/
```
