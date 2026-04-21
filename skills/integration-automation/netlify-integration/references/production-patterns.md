# Production Patterns from Twilio-Aldea

Real-world patterns from a production SMS-based AI therapy platform deployed on Netlify.

## Overview

Twilio-Aldea is a serverless Next.js application deployed on Netlify handling SMS-based AI conversations. It demonstrates production-ready patterns for:
- Webhook timeout handling (solved 60% message loss issue)
- Background function processing
- Environment variable management
- Next.js + Netlify Functions integration
- Error logging and monitoring

## Pattern 1: Immediate Response + Background Processing

### Problem
Webhook timeouts were causing 60% message loss. SMS providers (Twilio/Telnyx) require webhooks to respond within 10 seconds, but AI processing takes 15-25 seconds.

### Solution
Split webhook handling into two phases:
1. **Immediate acknowledgment** (< 200ms) - Return 200 OK to provider
2. **Background processing** (up to 15 min) - Handle AI logic in background function

### Implementation

**API Route (pages/api/twilio/sms-webhook.ts)**:
```typescript
import type { NextApiRequest, NextApiResponse } from 'next';

export const config = {
  api: {
    bodyParser: false,  // Preserve raw body for signature validation
  },
};

async function readRawBody(req: NextApiRequest): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    let data = '';
    req.setEncoding('utf8');
    req.on('data', (chunk) => { data += chunk; });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Read raw body
  const rawBody = await readRawBody(req);

  // IMMEDIATE: Return 200 OK to provider (< 200ms)
  res.status(200).send('<?xml version="1.0" encoding="UTF-8"?><Response></Response>');

  // BACKGROUND: Invoke background function for processing
  const baseUrl = getBaseUrl(req);
  await fetch(`${baseUrl}/.netlify/functions/sms-webhook-background`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phoneNumber: req.body.From,
      message: req.body.Body,
      messageSid: req.body.MessageSid,
    }),
  });
}
```

**Background Function (netlify/functions/sms-webhook-background.ts)**:
```typescript
import { Handler } from '@netlify/functions';
import { processIncomingSMS } from '../../src/lib/conversational-ai';

export const handler: Handler = async (event) => {
  if (!event.body) {
    return { statusCode: 400, body: 'No body provided' };
  }

  try {
    const { phoneNumber, message, messageSid } = JSON.parse(event.body);

    // Full 25-second processing with AI (no timeout constraint)
    await processIncomingSMS({ phoneNumber, message, messageSid });

    return { statusCode: 200, body: 'Processed' };
  } catch (error: unknown) {
    const err = error instanceof Error ? error : new Error(String(error));
    console.error('[Background] Error:', err);

    // Log to database for visibility
    await supabase.from('processing_errors').insert({
      message_sid: messageSid,
      error_message: err.message,
      error_stack: err.stack,
    });

    return { statusCode: 500, body: `Error: ${err.message}` };
  }
};
```

### Key Benefits
- ✅ 0% webhook timeouts (from 60% failure rate)
- ✅ Fast provider acknowledgment (< 200ms)
- ✅ Full processing time (up to 15 minutes on Netlify)
- ✅ Error logging to database
- ✅ No message loss

## Pattern 2: netlify.toml Configuration for Next.js + Functions

### Complete Configuration

**File: netlify.toml** (project root)
```toml
[build]
  command = "npm run build"
  publish = ".next"

# Note: @netlify/plugin-nextjs is legacy — the OpenNext adapter (@opennextjs/netlify)
# now auto-detects Next.js and requires no plugin entry.
[[plugins]]
  package = "@netlify/plugin-nextjs"

[functions]
  directory = "netlify/functions"
  node_bundler = "esbuild"
  # Include non-JavaScript files in function deployment
  included_files = ["src/lib/souls/**/*.md", "src/lib/souls/**/*.json"]
```

### Key Configuration Points

**1. Build Command**: `npm run build`
- Runs Next.js build process
- Generates `.next` directory

**2. Publish Directory**: `.next`
- Points to Next.js output
- Required for Next.js deployment

**3. Netlify Next.js Plugin**: `@netlify/plugin-nextjs` (legacy — replaced by the OpenNext adapter `@opennextjs/netlify`)
- The OpenNext adapter auto-detects Next.js and requires no plugin entry
- Handles serverless function generation, ISR, SSR, and static pages

**4. Functions Directory**: `netlify/functions`
- Where custom Netlify Functions live
- Separate from Next.js API routes

**5. Node Bundler**: `esbuild`
- Fast compilation
- Production-ready bundling

**6. Included Files**:
- Non-code files needed at runtime
- Example: AI soul definitions (.md, .json)
- Critical for apps with non-JS assets

### Common Pitfalls

❌ **Wrong publish directory**
```toml
publish = "out"  # Wrong for Next.js
```
✅ **Correct**
```toml
publish = ".next"  # Correct for Next.js
```

❌ **Missing plugin**
```toml
# No plugin specified - Next.js won't work properly
```
✅ **Correct** (legacy — OpenNext adapter now auto-detects; no plugin entry needed for new projects)
```toml
[[plugins]]
  package = "@netlify/plugin-nextjs"
```

## Pattern 3: Environment Variable Management

### Production Setup

**Required Environment Variables** (set in Netlify Dashboard):
```bash
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...

# SMS Provider
SMS_PROVIDER=telnyx  # or 'twilio'
TELNYX_API_KEY=KEY019A...

# Application
NEXT_PUBLIC_APP_URL=https://your-site.netlify.app
NEXTAUTH_SECRET=random-secret-string

# LLM
OPENROUTER_API_KEY=sk-or-v1-xxx
```

### Best Practices

1. **Never commit .env files** - Add `.env*` to `.gitignore`
2. **Use Netlify Dashboard for production** - Site Settings → Environment Variables
3. **Use .env.local for development** - Git-ignored, local-only
4. **Prefix client-side variables** - `NEXT_PUBLIC_` for browser access
5. **Validate at startup** - Fail fast if required variables missing

### Accessing Variables

**Server-side (API routes, functions)**:
```typescript
// Always available in server context
const apiKey = process.env.TELNYX_API_KEY;
```

**Client-side (components)**:
```typescript
// Only works with NEXT_PUBLIC_ prefix
const appUrl = process.env.NEXT_PUBLIC_APP_URL;
```

### Validation Pattern

```typescript
// src/lib/config.ts
export function validateEnv() {
  const required = [
    'SUPABASE_URL',
    'SUPABASE_SERVICE_KEY',
    'SMS_PROVIDER',
    'NEXT_PUBLIC_APP_URL',
  ];

  const missing = required.filter(key => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(`Missing environment variables: ${missing.join(', ')}`);
  }
}

// Call at app startup
validateEnv();
```

## Pattern 4: Proxy Pattern for Legacy Endpoints

### Use Case
Maintaining backward compatibility while migrating to new endpoints.

### Implementation

**Legacy endpoint proxies to new unified endpoint**:
```typescript
// pages/api/twilio/sms-webhook.ts (legacy)
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  console.log('[Legacy] Proxying to unified webhook');

  const rawBody = await readRawBody(req);
  const baseUrl = getBaseUrl(req);

  // Forward to new unified endpoint
  const response = await fetch(`${baseUrl}/api/sms/webhook`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'x-twilio-signature': req.headers['x-twilio-signature'] as string || '',
    },
    body: rawBody,
  });

  // Return same response from unified endpoint
  return res.status(response.status).send(await response.text());
}
```

### Benefits
- ✅ Zero-downtime migration
- ✅ Both old and new URLs work
- ✅ Single source of truth (new endpoint)
- ✅ Easy to deprecate later

## Pattern 5: Error Logging to Database

### Pattern
Log all function errors to Supabase for visibility and debugging.

### Implementation

```typescript
export const handler: Handler = async (event) => {
  try {
    // Main logic
    await processIncomingSMS(data);
    return { statusCode: 200, body: 'Success' };
  } catch (error: unknown) {
    const err = error instanceof Error ? error : new Error(String(error));
    console.error('[Function] Error:', err);

    // Log to database
    try {
      await supabase.from('processing_errors').insert({
        session_id: sessionId || null,
        message_sid: messageSid,
        error_message: err.message,
        error_stack: err.stack,
        phone_number: phoneNumber,
        message_body: message,
        created_at: new Date().toISOString(),
      });
    } catch (logError) {
      console.error('[Function] Failed to log error:', logError);
    }

    return { statusCode: 500, body: `Error: ${err.message}` };
  }
};
```

### Database Schema

```sql
CREATE TABLE processing_errors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES user_sessions(id),
  message_sid TEXT,
  error_message TEXT NOT NULL,
  error_stack TEXT,
  phone_number TEXT,
  message_body TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_processing_errors_created_at ON processing_errors(created_at DESC);
CREATE INDEX idx_processing_errors_session_id ON processing_errors(session_id);
```

### Benefits
- ✅ Centralized error tracking
- ✅ Queryable error history
- ✅ Easy debugging
- ✅ Error rate monitoring

## Pattern 6: Function Timeout Configuration

### Problem
Default Netlify timeout (10s) too short for AI processing.

### Solution
Use background functions or increase timeout in netlify.toml.

### Configuration

```toml
[functions]
  directory = "netlify/functions"
  # Timeout not directly configurable in netlify.toml
  # Use background functions for > 10s processing
```

### Background Function Detection

Netlify automatically detects background functions by filename:
- `my-function.ts` → Regular function (10s timeout)
- `my-function-background.ts` → Background function (15 min timeout)

No additional configuration needed!

## Pattern 7: Raw Body Parsing for Signature Validation

### Pattern
Preserve raw request body for webhook signature validation (Twilio, Telnyx).

### Implementation

```typescript
import type { NextApiRequest, NextApiResponse } from 'next';

export const config = {
  api: {
    bodyParser: false,  // CRITICAL: Disable Next.js body parsing
  },
};

async function readRawBody(req: NextApiRequest): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    let data = '';
    req.setEncoding('utf8');
    req.on('data', (chunk) => { data += chunk; });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const rawBody = await readRawBody(req);

  // Validate signature with raw body
  const isValid = validateSignature(
    rawBody,
    req.headers['x-twilio-signature'] as string,
    webhookUrl
  );

  if (!isValid) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Now parse body for use
  const params = new URLSearchParams(rawBody);
  const phoneNumber = params.get('From');
  // ...
}
```

### Why This Matters
- ✅ Signature validation requires exact raw body
- ✅ Next.js body parser modifies body → breaks signature
- ✅ Must disable bodyParser and read manually
- ✅ Critical for security

## Pattern 8: Base URL Detection

### Pattern
Dynamically detect base URL for internal requests (preview, production).

### Implementation

```typescript
function getBaseUrl(req: NextApiRequest): string {
  const proto = (req.headers['x-forwarded-proto'] as string) || 'https';
  const host = (req.headers['x-forwarded-host'] as string) || (req.headers.host as string);
  return `${proto}://${host}`;
}

// Usage
const baseUrl = getBaseUrl(req);
const backgroundUrl = `${baseUrl}/.netlify/functions/sms-webhook-background`;
```

### Why This Matters
- ✅ Works in preview deploys (`preview-123.netlify.app`)
- ✅ Works in production (`yourdomain.com`)
- ✅ Works locally (`localhost:3000`)
- ✅ No hardcoded URLs

## Key Takeaways

1. **Webhook Timeouts**: Use background functions for long processing
2. **Configuration**: For new projects, the OpenNext adapter auto-detects Next.js (no plugin entry needed). Legacy projects may still use `@netlify/plugin-nextjs`
3. **Environment Variables**: Set in Netlify Dashboard, never commit
4. **Error Logging**: Log to database for visibility
5. **Signature Validation**: Disable bodyParser and read raw body
6. **Base URL**: Dynamically detect for internal requests
7. **Background Functions**: Name with `-background.ts` suffix

## References

- **Twilio-Aldea Production Code**: SMS-based AI therapy platform
- **Deployment**: Netlify serverless with Next.js 14
- **Traffic**: Real users, production SMS traffic
- **Architecture**: API routes + Netlify Functions + Supabase
