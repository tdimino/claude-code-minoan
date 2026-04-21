# Twilio API

Comprehensive Twilio API reference for building SMS/MMS messaging, voice calls, webhook handlers, and phone number management. Covers SDK usage (Node.js), raw HTTP, TwiML responses, signature validation, A2P 10DLC registration, and production patterns including provider-agnostic webhook architecture.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Twilio's API surface is broad---messaging, voice, webhooks, TwiML, signature validation, rate limiting, A2P compliance. This skill consolidates the patterns you need for production SMS/voice into one reference with code examples, error handling, and provider-agnostic webhook architecture (Twilio + Telnyx from a single endpoint).

---

## Structure

```
twilio-api/
  SKILL.md                          # Full reference with 10 code patterns
  README.md                         # This file
  references/
    index.md                        # Overview and quick start
    messaging.md                    # SMS/MMS API reference
    llms.md                         # LLM-optimized API reference
```

---

## Quick Reference

```javascript
// Send SMS (Node.js SDK)
const client = require('twilio')(accountSid, authToken);
await client.messages.create({ to: '+14155552671', from: '+14155559999', body: 'Hello!' });

// Handle incoming webhook with TwiML
app.post('/webhook', (req, res) => {
  res.set('Content-Type', 'text/xml');
  res.send('<Response><Message>Thanks!</Message></Response>');
});

// Validate webhook signature
const twilio = require('twilio');
if (!twilio.validateRequest(authToken, signature, url, req.body)) {
  return res.status(403).send('Forbidden');
}
```

---

## Key Patterns

| Pattern | Description |
|---------|-------------|
| SDK send | `client.messages.create()` with retry and backoff |
| Raw HTTP send | Direct REST API via `https.request` (no SDK) |
| TwiML responses | XML response format for webhooks |
| Signature validation | HMAC-SHA1 verification (manual or SDK) |
| Provider-agnostic webhook | Single endpoint handling both Twilio and Telnyx |
| Message scheduling | GA feature via `SendAt` + Messaging Service |
| Bulk sending | Rate-limited batch with 100ms delay |
| Idempotency | Database-backed duplicate prevention |
| Fast mode | Return TwiML immediately, process async |
| Error handling | Status-aware retry with exponential backoff |
| E.164 validation | Phone number format normalization |

---

## Key Concepts

| Concept | Summary |
|---------|---------|
| E.164 format | `+[country code][number]`, e.g. `+14155552671` |
| TwiML | XML response language (`<Message>`, `<Dial>`, `<Say>`) |
| Webhook events | `MessageSid`, `From`, `To`, `Body`, `MessageStatus` |
| Message lifecycle | queued > sending > sent > delivered / failed |
| A2P 10DLC | Brand + Campaign registration for US messaging |
| Segmentation | GSM-7: 160 chars, UCS-2: 70 chars per segment |
| TLS requirement | TLS 1.3 or compliant 1.2 cipher suite (deadline Jun 2026) |
| MMS rate limits | Dynamic per-number limits based on Brand Trust Score (10DLC) |

---

## Setup

### Prerequisites

- Twilio account (sign up at twilio.com)
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` environment variables
- Node.js + `npm install twilio` (for SDK examples)
- No scripts to install---this is a reference skill

---

## Related Skills

- **`sms`**: Operational SMS sending/reading scripts using Telnyx and Twilio.
- **`resend`**: Email sending via Resend API.

---

## Requirements

- Twilio account with API credentials
- Node.js (for SDK examples) or any HTTP client

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/twilio-api ~/.claude/skills/
```
