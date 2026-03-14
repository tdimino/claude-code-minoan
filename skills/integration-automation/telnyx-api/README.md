# Telnyx API

The telephony skill. SMS/MMS messaging, webhook handling, 10DLC compliance, and phone number management---with production patterns extracted from the Twilio-Aldea SMS platform and Ed25519 signature validation for secure webhook processing.

**Last updated:** 2026-01-02

**Reflects:** Telnyx v2 API, Node.js SDK, 10DLC compliance requirements, and production webhook architectures from Twilio-Aldea.

---

## Why This Skill Exists

Building production SMS infrastructure involves more than sending messages. You need webhook signature validation (Ed25519, not HMAC), idempotent message processing, 10DLC campaign registration, E.164 phone number normalization, rate limiting for bulk sends, and a conversation threading model that survives server restarts. Getting any of these wrong causes silent failures---messages that never arrive, webhooks that process twice, campaigns that get suspended.

This skill encodes 8 battle-tested patterns from the Twilio-Aldea production SMS platform, complete with TypeScript examples, a provider-agnostic webhook handler design that supports both Telnyx and Twilio from a single endpoint, and comprehensive reference docs covering the full Telnyx API surface.

---

## Structure

```
telnyx-api/
  SKILL.md                                     # Quick reference and core workflows
  README.md                                    # This file
  assets/
    examples/
      webhook-handler.ts                       # Complete handler with Ed25519 validation
      send-sms.ts                              # SMS/MMS examples with error handling
      provider-implementation.ts               # Full production provider class
  references/
    authentication.md                          # API key management and security
    messaging-api.md                           # Full endpoint documentation
    webhooks.md                                # Event types, signature verification
    error-codes.md                             # Complete error reference and handling
    best-practices.md                          # Production deployment patterns
    10dlc.md                                   # 10DLC registration and compliance
    production-patterns.md                     # 8 battle-tested patterns from Twilio-Aldea
    index.md                                   # Reference navigation guide
    official-docs/
      authentication.md                        # Official Telnyx authentication docs
      messaging.md                             # Official Telnyx messaging API
      sdks.md                                  # Server-side SDK docs (7 languages)
      webhooks.md                              # Official Telnyx webhooks guide
```

Note: `references/github/` contains upstream SDK docs (README, issues, changelog, releases) for authoritative reference.

---

## What It Covers

### Core Capabilities

| Capability | What It Covers |
|-----------|---------------|
| **SMS/MMS** | Send, receive, status callbacks, media attachments |
| **Webhooks** | Ed25519 signature validation, event types, retry logic |
| **10DLC** | Campaign registration, brand verification, approval tracking |
| **Number management** | Purchase, configure, messaging profiles |
| **Error handling** | Retry strategies, error codes, fallback patterns |

### Ed25519 Signature Validation

Telnyx uses Ed25519 (not HMAC) for webhook signatures. This is the single most common integration mistake:

```typescript
// Requires tweetnacl for Ed25519 verification
// Raw body must be preserved (not parsed) for signature validation
// Timestamp tolerance prevents replay attacks
```

See `assets/examples/webhook-handler.ts` for the complete implementation.

### Provider-Agnostic Design

The `provider-implementation.ts` example demonstrates a webhook handler that supports both Telnyx and Twilio from a single endpoint---route by signature header, normalize to a common message format, process uniformly.

### 10DLC Compliance

10DLC (10-Digit Long Code) registration is required for US A2P messaging. `references/10dlc.md` covers:
- Brand registration and verification
- Campaign types and use cases
- Approval stages and timelines
- Common rejection reasons and remediation

### Production Patterns

`references/production-patterns.md` documents 8 patterns from Twilio-Aldea:

| Pattern | Problem It Solves |
|---------|------------------|
| Raw body preservation | Signature validation fails on parsed JSON |
| Idempotent processing | Duplicate webhooks from retries |
| Message state machine | Two-way conversation threading |
| Rate-limited bulk sends | Carrier throttling and 10DLC limits |
| E.164 normalization | Inconsistent phone number formats |
| Messaging profiles | Centralized sender configuration |
| Error recovery | Transient failures in message delivery |
| Structured logging | Debugging webhook processing in production |

---

## Examples

| Example | Purpose |
|---------|---------|
| `webhook-handler.ts` | Complete webhook handler: Ed25519 validation, event routing, error handling |
| `send-sms.ts` | Send SMS/MMS with retry logic and error handling |
| `provider-implementation.ts` | Full production provider class with Telnyx + Twilio support |

---

## Requirements

- Telnyx account with API key
- Node.js 18+ / TypeScript
- `telnyx` SDK (`npm install telnyx`)
- `tweetnacl` for Ed25519 signature validation (`npm install tweetnacl`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/telnyx-api ~/.claude/skills/
```
