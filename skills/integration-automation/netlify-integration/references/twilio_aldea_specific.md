# Twilio-Aldea Specific Patterns

Netlify deployment patterns specific to the Twilio-Aldea SMS therapeutic AI project.

## Project Architecture

- **Framework:** Next.js 14 with TypeScript
- **Deployment:** Netlify (serverless functions)
- **Database:** Supabase (PostgreSQL)
- **SMS Providers:** Telnyx (primary) / Twilio (alternative)
- **AI Engine:** Daimonic Souls Engine
- **LLM:** OpenRouter API

## Critical Deployment Requirements

### 1. Webhook Timeout Configuration

**Problem:** 60% message loss due to webhook timeouts

**Root Cause:**
- Default 10s function timeout insufficient
- SMS processing with AI takes 15-20s
- Providers (Telnyx/Twilio) timeout webhooks at 10s

**Solution:**
```toml
# netlify.toml
[[functions."sms-webhook"]]
  timeout = 26  # Maximum for Pro tier

[[functions."unified-webhook"]]
  timeout = 26
```

**Code Pattern:**
```typescript
// .netlify/functions/sms-webhook.ts
export const handler: Handler = async (event, context) => {
  // Validate signature (< 1s)
  const isValid = await validateWebhook(event);
  if (!isValid) return { statusCode: 401, body: "Unauthorized" };

  // Return 200 IMMEDIATELY
  const response = {
    statusCode: 200,
    body: JSON.stringify({ received: true }),
  };

  // Process async (don't await)
  processSMSAsync(event.body)
    .catch(error => {
      console.error("SMS processing error:", error);
      // Log to error tracking service
    });

  return response;
};
```

### 2. Environment Variables

**Required for Production:**

```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# SMS Provider (Telnyx)
SMS_PROVIDER=telnyx
TELNYX_API_KEY=KEY019A080F468AAFD4AF4F6888D7795244_xxx
TELNYX_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"

# Application
NEXT_PUBLIC_APP_URL=https://your-site.netlify.app
NEXTAUTH_SECRET=random-secret-string-minimum-32-characters

# LLM/AI
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Feature Flags
SMS_FAST_MODE=false
DEBUG_MODE=false
```

**Set in Netlify Dashboard:**
```bash
netlify env:set SUPABASE_URL "https://xxx.supabase.co"
netlify env:set SUPABASE_SERVICE_KEY "eyJhbGc..."
netlify env:set TELNYX_API_KEY "KEY019A..."
# ... etc
```

### 3. Netlify Configuration

**Complete netlify.toml:**

```toml
[build]
  command = "npm run build"
  publish = ".next"
  functions = ".netlify/functions"

[build.environment]
  NODE_VERSION = "18"
  NEXT_TELEMETRY_DISABLED = "1"
  NPM_FLAGS = "--legacy-peer-deps"

[functions]
  directory = ".netlify/functions"
  node_bundler = "esbuild"
  included_files = [
    ".netlify/functions/**",
    "src/lib/**",
    "src/souls/**"
  ]
  timeout = 10

# SMS webhook with extended timeout
[[functions."sms-webhook"]]
  timeout = 26

# Unified webhook handler
[[functions."unified-webhook"]]
  timeout = 26

# API rewrites
[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200
  force = true

# Security headers
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    X-XSS-Protection = "1; mode=block"
    Referrer-Policy = "strict-origin-when-cross-origin"

# CORS for webhooks
[[headers]]
  for = "/api/sms/*"
  [headers.values]
    Access-Control-Allow-Origin = "*"
    Access-Control-Allow-Methods = "POST, OPTIONS"
    Access-Control-Allow-Headers = "Content-Type, Telnyx-Signature-Ed25519, Telnyx-Timestamp"

# Production context
[context.production]
  [context.production.environment]
    NODE_ENV = "production"

# Preview context
[context.deploy-preview]
  [context.deploy-preview.environment]
    NODE_ENV = "staging"
```

## Webhook Function Implementation

### Unified Webhook Handler

```typescript
// .netlify/functions/sms-webhook.ts
import { Handler } from "@netlify/functions";
import { validateWebhook } from "../../src/lib/sms/validation";
import { detectProvider } from "../../src/lib/sms/detection";
import { processInboundSMS } from "../../src/lib/sms/processor";

export const handler: Handler = async (event, context) => {
  console.log("SMS webhook received", {
    requestId: context.requestId,
    method: event.httpMethod,
    headers: Object.keys(event.headers),
  });

  // Detect provider (Telnyx or Twilio)
  const provider = detectProvider(event);
  console.log("Provider detected:", provider);

  // Validate webhook signature
  const isValid = await validateWebhook(event, provider);
  if (!isValid) {
    console.error("Webhook signature validation failed");
    return {
      statusCode: 401,
      body: JSON.stringify({ error: "Unauthorized" }),
    };
  }

  // Return 200 immediately
  const response = {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ received: true }),
  };

  // Process SMS async (don't await)
  processInboundSMS(event.body, provider)
    .catch(error => {
      console.error("SMS processing error:", {
        error: error.message,
        stack: error.stack,
        provider,
      });
    });

  return response;
};
```

### Provider Detection

```typescript
// src/lib/sms/detection.ts
import type { HandlerEvent } from "@netlify/functions";

export function detectProvider(event: HandlerEvent): "telnyx" | "twilio" {
  // Telnyx has Ed25519 signature
  if (event.headers["telnyx-signature-ed25519"]) {
    return "telnyx";
  }

  // Twilio has X-Twilio-Signature
  if (event.headers["x-twilio-signature"]) {
    return "twilio";
  }

  // Default to Telnyx
  return "telnyx";
}
```

### Signature Validation

```typescript
// src/lib/sms/validation.ts
import crypto from "crypto";
import type { HandlerEvent } from "@netlify/functions";

export async function validateWebhook(
  event: HandlerEvent,
  provider: "telnyx" | "twilio"
): Promise<boolean> {
  if (provider === "telnyx") {
    return validateTelnyxSignature(event);
  } else {
    return validateTwilioSignature(event);
  }
}

function validateTelnyxSignature(event: HandlerEvent): boolean {
  const signature = event.headers["telnyx-signature-ed25519"];
  const timestamp = event.headers["telnyx-timestamp"];
  const publicKey = process.env.TELNYX_PUBLIC_KEY;

  if (!signature || !timestamp || !publicKey) {
    return false;
  }

  try {
    const signedPayload = `${timestamp}|${event.body}`;
    const verifier = crypto.createVerify("sha256");
    verifier.update(signedPayload);
    return verifier.verify(publicKey, signature, "base64");
  } catch (error) {
    console.error("Signature validation error:", error);
    return false;
  }
}

function validateTwilioSignature(event: HandlerEvent): boolean {
  // Implement Twilio signature validation
  // Uses HMAC-SHA1
  return true; // Placeholder
}
```

## Database Operations

### Supabase Client Pattern

```typescript
// src/lib/supabase/client.ts
import { createClient } from "@supabase/supabase-js";

// Singleton pattern for connection reuse
let supabase: any = null;

export function getSupabaseClient() {
  if (!supabase) {
    supabase = createClient(
      process.env.SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!,
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false,
        },
      }
    );
  }
  return supabase;
}
```

### Idempotency Pattern

```typescript
// Prevent duplicate message processing
export async function logInboundSMS(messageData: any) {
  const db = getSupabaseClient();

  const { data, error } = await db
    .from("sms_logs")
    .insert({
      message_sid: messageData.messageId,
      from_number: messageData.from,
      to_number: messageData.to,
      body: messageData.body,
      direction: "inbound",
      provider: messageData.provider,
    })
    .select()
    .single();

  // Duplicate detection (Postgres unique constraint)
  if (error?.code === "23505") {
    console.log("Duplicate message detected, skipping processing");
    return null; // Already processed
  }

  return data;
}
```

## Deployment Checklist

Before deploying to production:

**Pre-Deployment:**
- [ ] All environment variables set in Netlify Dashboard
- [ ] `netlify.toml` includes webhook timeout configuration (26s)
- [ ] Database migrations applied to Supabase
- [ ] SMS provider credentials validated
- [ ] Test webhook locally with `netlify dev`

**Post-Deployment:**
- [ ] Update webhook URL in Telnyx/Twilio dashboard
- [ ] Send test SMS and verify end-to-end flow
- [ ] Monitor function logs: `netlify functions:log sms-webhook --stream`
- [ ] Check Supabase logs for database operations
- [ ] Verify no timeout errors in first 24 hours
- [ ] Monitor message success rate (should be > 95%)

## Monitoring

### Key Metrics

```bash
# Function execution time
netlify functions:log sms-webhook | grep "duration_ms"

# Error rate
netlify functions:log sms-webhook | grep "ERROR"

# Webhook success rate
# Check sms_logs table in Supabase
SELECT
  COUNT(*) as total,
  COUNT(CASE WHEN status = 'success' THEN 1 END) as successes,
  COUNT(CASE WHEN status = 'error' THEN 1 END) as errors
FROM sms_logs
WHERE created_at > NOW() - INTERVAL '24 hours';
```

### Structured Logging

```typescript
function log(level: string, message: string, context?: any) {
  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    message,
    ...context,
  }));
}

// Usage in webhook
log("info", "SMS webhook received", {
  provider,
  from: messageData.from,
  messageId: messageData.messageId,
});
```

## Troubleshooting

### High Message Loss Rate

**Symptoms:**
- 40-60% of messages not processed
- Timeout errors in logs
- Provider reporting webhook failures

**Solutions:**
1. Verify timeout is 26s in netlify.toml
2. Ensure immediate response pattern implemented
3. Check database query performance
4. Monitor function execution time

### Database Connection Issues

**Symptoms:**
- "Connection refused" errors
- Timeouts on database operations

**Solutions:**
1. Verify SUPABASE_URL is correct
2. Check Supabase service status
3. Implement connection pooling
4. Add retries with exponential backoff

### Signature Validation Failures

**Symptoms:**
- All webhooks return 401
- "Invalid signature" errors

**Solutions:**
1. Verify TELNYX_PUBLIC_KEY includes newlines: `\n`
2. Check timestamp freshness (< 5 minutes)
3. Ensure correct signature header name

## Resources

- Twilio-Aldea README: `~/Desktop/Aldea/Prompt development/Twilio-Aldea/README.md`
- Twilio-Aldea CLAUDE.md: `~/Desktop/Aldea/Prompt development/Twilio-Aldea/CLAUDE.md`
- Daimonic Souls Engine Docs: `~/Desktop/A.I. & LLMs/daimonic-souls-engine/`
