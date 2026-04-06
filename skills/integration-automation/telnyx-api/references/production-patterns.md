# Telnyx Production Patterns

**Source**: Real-world patterns from Twilio-Aldea SMS-based AI therapy platform deployed on Netlify.

These patterns represent battle-tested solutions that solved production issues in a live SMS application handling concurrent sessions with AI-powered conversations.

## Pattern 1: Ed25519 Signature Validation with tweetnacl

**Problem**: Telnyx uses Ed25519 public key cryptography for webhook signatures, which is different from Twilio's HMAC-SHA1. Standard crypto libraries don't support Ed25519 verification out of the box.

**Solution**: Use `tweetnacl` library for Ed25519 signature verification with proper timestamp handling.

```typescript
import nacl from 'tweetnacl';

/**
 * Validate Telnyx webhook signature using Ed25519
 *
 * CRITICAL: payload must be the raw body string, NOT parsed object.
 * Ed25519 signatures are calculated on exact byte sequences.
 *
 * Signed payload format: `${timestamp}|${rawBodyString}`
 */
function validateTelnyxWebhook(
  rawBody: string,  // Raw request body string
  signature: string,  // telnyx-signature-ed25519 header (base64)
  timestamp: string,  // telnyx-timestamp header
  publicKey: string   // Your webhook public key from Telnyx portal (base64)
): boolean {
  try {
    // Build the signed payload: timestamp|rawBody
    const signedPayload = `${timestamp}|${rawBody}`;

    // Convert base64 strings to Uint8Array for nacl
    const publicKeyBytes = Buffer.from(publicKey, 'base64');
    const signatureBytes = Buffer.from(signature, 'base64');
    const messageBytes = Buffer.from(signedPayload, 'utf-8');

    // Verify Ed25519 signature
    const isValid = nacl.sign.detached.verify(
      messageBytes,
      signatureBytes,
      publicKeyBytes
    );

    return isValid;
  } catch (error) {
    console.error('Webhook validation error:', error);
    return false;
  }
}
```

**Key Points**:
- Use `telnyx-signature-ed25519` and `telnyx-timestamp` headers
- Signed payload is `${timestamp}|${rawBody}` (pipe-separated)
- All values are base64-encoded for transmission
- Must use raw body string, not re-serialized JSON
- Install: `npm install tweetnacl @types/tweetnacl`

**Production Usage** (Twilio-Aldea):
```typescript
// src/lib/sms/providers/telnyx.ts:182-224
validateWebhook(payload: string | any, signature: string, url: string, timestamp?: string): boolean {
  if (!this.webhookPublicKey) {
    console.warn('[Telnyx] Skipping signature validation - no public key configured');
    return true;  // Not recommended for production
  }

  if (!timestamp) {
    console.error('[Telnyx] Missing telnyx-timestamp header');
    return false;
  }

  const bodyString = typeof payload === 'string' ? payload : JSON.stringify(payload);
  const signedPayload = `${timestamp}|${bodyString}`;

  const publicKeyBytes = Buffer.from(this.webhookPublicKey, 'base64');
  const signatureBytes = Buffer.from(signature, 'base64');
  const messageBytes = Buffer.from(signedPayload, 'utf-8');

  return nacl.sign.detached.verify(messageBytes, signatureBytes, publicKeyBytes);
}
```

## Pattern 2: Provider-Agnostic Webhook Handler

**Problem**: Supporting both Twilio (form-urlencoded, TwiML) and Telnyx (JSON, HTTP 200) from a single endpoint without code duplication.

**Solution**: Auto-detect provider from payload structure, then delegate to provider-specific implementations.

```typescript
// Auto-detect provider from webhook payload structure
function detectProvider(payload: any): 'twilio' | 'telnyx' {
  // Telnyx webhooks have { data: { event_type, payload } } structure
  if (payload.data?.event_type && payload.data?.payload) {
    return 'telnyx';
  }

  // Twilio webhooks have MessageSid, From, To at root level
  if (payload.MessageSid || payload.From || payload.To) {
    return 'twilio';
  }

  throw new Error('Unknown SMS provider - cannot detect from payload structure');
}

// Unified webhook handler
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const rawBody = await readRawBody(req);

  // Parse payload (JSON or form-urlencoded)
  let payload: any;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    payload = parseFormUrlEncoded(rawBody);
  }

  // Auto-detect provider
  const providerType = detectProvider(payload);
  const provider = getProviderByType(providerType);

  // Validate signature (provider-specific)
  const signature = req.headers[
    providerType === 'twilio' ? 'x-twilio-signature' : 'telnyx-signature-ed25519'
  ] as string;

  const timestamp = providerType === 'telnyx'
    ? req.headers['telnyx-timestamp'] as string
    : undefined;

  const validationPayload = providerType === 'telnyx' ? rawBody : payload;
  const isValid = provider.validateWebhook(validationPayload, signature, url, timestamp);

  if (!isValid && isProduction()) {
    return res.status(403).json({ error: 'Invalid signature' });
  }

  // Parse to standardized format
  const message = provider.parseIncomingMessage(payload);

  // Process message...
}
```

**Production Usage** (Twilio-Aldea):
- `src/pages/api/sms/webhook.ts:113-156` - Provider detection and validation
- `src/lib/sms/client.ts` - Provider registry pattern

## Pattern 3: Raw Body Parsing for Signature Validation

**Problem**: Next.js bodyParser converts request body to object, but signature validation requires the exact raw bytes received from Telnyx.

**Solution**: Disable Next.js bodyParser and manually read raw body stream.

```typescript
// Disable Next.js body parser
export const config = {
  api: {
    bodyParser: false,  // CRITICAL: Preserve raw body for signature validation
  },
};

// Read raw body as string
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
  // Read raw body FIRST, before any parsing
  const rawBody = await readRawBody(req);

  // Now parse for processing
  const payload = JSON.parse(rawBody);

  // Use raw body for signature validation
  const isValid = validateSignature(rawBody, signature, timestamp, publicKey);
}
```

**Why This Matters**:
- Ed25519 signatures are calculated on exact byte sequences
- Any re-serialization (like `JSON.stringify`) will change key order
- Parsing then re-stringifying will break signature validation
- Must validate against the exact bytes Telnyx sent

**Production Usage** (Twilio-Aldea):
- `src/pages/api/sms/webhook.ts:26-30` - Disable bodyParser config
- `src/pages/api/sms/webhook.ts:60-68` - Raw body reader
- `src/pages/api/sms/webhook.ts:110-119` - Parse after reading raw

## Pattern 4: Idempotency with Database Unique Constraint

**Problem**: Telnyx may send duplicate webhooks for the same message (network retries, failover). Processing duplicates causes double-replies and wasted LLM calls.

**Solution**: Use database unique constraint on `message_sid` with PostgreSQL error code detection.

```typescript
// Database schema (Supabase/PostgreSQL)
CREATE TABLE sms_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_sid TEXT NOT NULL UNIQUE,  -- Unique constraint prevents duplicates
  from_number TEXT NOT NULL,
  to_number TEXT NOT NULL,
  body TEXT,
  direction TEXT CHECK (direction IN ('inbound', 'outbound')),
  provider TEXT CHECK (provider IN ('twilio', 'telnyx')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

// Webhook handler with idempotency check
const { data, error } = await supabase
  .from('sms_logs')
  .insert({
    message_sid: message.messageId,
    from_number: message.from,
    to_number: message.to,
    body: message.body,
    direction: 'inbound',
    provider: 'telnyx',
  })
  .select()
  .single();

// Error code 23505 = duplicate key violation (PostgreSQL)
if (error && error.code === '23505') {
  console.log(`Duplicate message detected: ${message.messageId} - acknowledging without re-processing`);
  return res.status(200).send('');  // Telnyx expects 200 OK
}

// First time seeing this message - process it
await processMessage(message);
```

**Key Points**:
- Database enforces idempotency (not application logic)
- PostgreSQL error code `23505` = unique constraint violation
- Return 200 OK for duplicates (Telnyx considers it successful)
- Prevents double-processing without external cache/Redis

**Production Usage** (Twilio-Aldea):
- `src/pages/api/sms/webhook.ts:177-207` - Idempotency check with error code detection
- Database schema in Supabase with `message_sid` unique constraint

## Pattern 5: Messaging Profile Configuration

**Problem**: Production deployments should use messaging profiles for centralized webhook management and number pooling.

**Solution**: Include `messaging_profile_id` in API calls when configured.

```typescript
class TelnyxProvider {
  private messagingProfileId?: string;

  constructor() {
    this.messagingProfileId = process.env.TELNYX_MESSAGING_PROFILE_ID;
  }

  async sendSMS(message: OutgoingMessage): Promise<string> {
    const payload: any = {
      from: message.from,
      to: message.to,
      text: message.body,
    };

    // Add messaging profile ID if configured
    // Recommended for production: centralized webhook management
    if (this.messagingProfileId) {
      payload.messaging_profile_id = this.messagingProfileId;
    }

    const response = await fetch('https://api.telnyx.com/v2/messages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    return (await response.json()).data.id;
  }
}
```

**Benefits**:
- Centralized webhook URL configuration (change once for all numbers)
- Number pooling for load distribution
- Alphanumeric sender IDs
- Easier number management

**Environment Variables**:
```bash
TELNYX_API_KEY=KEY019A080F468AAFD4AF4F6888D7795244_xxx
TELNYX_PHONE_NUMBER=+18334843851
TELNYX_MESSAGING_PROFILE_ID=abc85f64-5717-4562-b3fc-2c9600000000  # Optional but recommended
TELNYX_WEBHOOK_PUBLIC_KEY=dGVzdC1wdWJsaWMta2V5LWJhc2U2NC1lbmNvZGVk  # For signature validation
```

**Production Usage** (Twilio-Aldea):
- `src/lib/sms/providers/telnyx.ts:33-34` - Load from environment
- `src/lib/sms/providers/telnyx.ts:63-65` - Include in API payload

## Pattern 6: Debugger Mode with Phone Number Detection

**Problem**: Testing webhooks and AI responses without sending real SMS (costs money, clutters logs).

**Solution**: Detect debugger sessions by phone number pattern and skip actual SMS sending.

```typescript
class BaseSMSProvider {
  /**
   * Check if this is a debugger session (no real SMS sending)
   * Debugger uses phone format: debugger-{sessionId}
   */
  protected isDebuggerSession(phoneNumber: string): boolean {
    return phoneNumber.startsWith('debugger-');
  }
}

class TelnyxProvider extends BaseSMSProvider {
  async sendSMS(message: OutgoingMessage): Promise<string> {
    // Debugger mode - skip actual send
    if (this.isDebuggerSession(message.to)) {
      console.log('[Telnyx] Debugger mode - skipping SMS send:', message.body);
      return `debug-${Date.now()}`;  // Fake message ID
    }

    // Real SMS sending...
    const response = await fetch('https://api.telnyx.com/v2/messages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: message.from,
        to: message.to,
        text: message.body,
      }),
    });

    return (await response.json()).data.id;
  }
}
```

**Benefits**:
- Test AI conversations without SMS costs
- Faster development iteration
- No log pollution with test messages
- Same code path as production (just skips API call)

**Production Usage** (Twilio-Aldea):
- `src/lib/sms/providers/base.ts:8-14` - Base implementation
- `src/lib/sms/providers/telnyx.ts:50-53` - Check before sending
- Used in browser-based debugger UI for real-time testing

## Pattern 7: Error Logging to Database with Categorization

**Problem**: Serverless function errors are hard to debug (logs scattered, no persistence, hard to query).

**Solution**: Log all processing errors to database with categorized error types for easy filtering.

```typescript
// Database schema for error tracking
CREATE TABLE processing_errors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES user_sessions(id),
  message_sid TEXT,
  phone_number TEXT,
  message_body TEXT,
  error_type TEXT,  -- Categorized: 'timeout', 'llm_error', 'database_error', etc.
  error_message TEXT NOT NULL,
  error_stack TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

// Log errors with categorization
try {
  await processIncomingSMS({ phoneNumber, message, messageSid });
} catch (error: unknown) {
  const err = error instanceof Error ? error : new Error(String(error));
  const isTimeout = err.message.includes('timed out');
  const errorType = isTimeout ? 'timeout' : 'processing_error';

  // Log to database for visibility
  await supabase.from('processing_errors').insert({
    session_id: sessionId,
    message_sid: messageSid,
    error_message: `${errorType.toUpperCase()}: ${err.message}`,
    error_stack: err.stack,
    phone_number: phoneNumber,
    message_body: message,
    error_type: errorType,  // Enables easy filtering in queries
  });

  // Return user-friendly error
  return res.status(200).send("I'm having trouble responding. Please try again.");
}
```

**Query Examples**:
```sql
-- Find all timeout errors in last hour
SELECT * FROM processing_errors
WHERE error_type = 'timeout'
AND created_at > NOW() - INTERVAL '1 hour';

-- Count errors by type
SELECT error_type, COUNT(*)
FROM processing_errors
GROUP BY error_type;

-- Find errors for specific phone number
SELECT * FROM processing_errors
WHERE phone_number = '+15551234567'
ORDER BY created_at DESC;
```

**Production Usage** (Twilio-Aldea):
- `src/pages/api/sms/webhook.ts:333-370` - Error logging with categorization
- Enables quick diagnosis of production issues via SQL queries

## Pattern 8: Phone Number Normalization to E.164

**Problem**: Phone numbers come in various formats (+1-555-123-4567, (555) 123-4567, 5551234567). Telnyx requires E.164 format.

**Solution**: Centralized normalization function that handles all common formats.

```typescript
class BaseSMSProvider {
  /**
   * Normalize phone number to E.164 format
   *
   * E.164: +[country code][number] (e.g., +14155551234)
   *
   * Handles:
   * - Already E.164: +14155551234 → +14155551234
   * - With country code: 14155551234 → +14155551234
   * - Without country code: 4155551234 → +14155551234
   * - Formatted: (415) 555-1234 → +14155551234
   */
  protected normalizePhoneNumber(phoneNumber: string): string {
    // Remove all non-digit characters
    let digits = phoneNumber.replace(/\D/g, '');

    // If already has + prefix and 11+ digits, return as-is
    if (phoneNumber.startsWith('+') && digits.length >= 11) {
      return phoneNumber;
    }

    // Add country code if missing (default: US +1)
    if (digits.length === 10) {
      digits = '1' + digits;
    }

    // Add + prefix
    return '+' + digits;
  }
}

// Usage
const normalized = this.normalizePhoneNumber('(415) 555-1234');  // +14155551234
const alreadyE164 = this.normalizePhoneNumber('+14155551234');   // +14155551234
```

**Edge Cases Handled**:
- `+14155551234` → `+14155551234` (already E.164)
- `14155551234` → `+14155551234` (missing +)
- `4155551234` → `+14155551234` (missing country code)
- `(415) 555-1234` → `+14155551234` (formatted)
- `555-123-4567` → `+15551234567` (dashes)

**Production Usage** (Twilio-Aldea):
- `src/lib/sms/providers/base.ts:16-36` - Base implementation
- Used for both `from` and `to` numbers in all SMS operations

## Summary

These 8 patterns represent production-tested solutions from a live SMS platform:

1. **Ed25519 Signature Validation** - Secure webhook authentication with tweetnacl
2. **Provider-Agnostic Handler** - Support Twilio + Telnyx from single endpoint
3. **Raw Body Parsing** - Preserve exact bytes for signature validation
4. **Database Idempotency** - Prevent duplicate processing with unique constraints
5. **Messaging Profiles** - Production-ready webhook and number management
6. **Debugger Mode** - Cost-free testing with phone number detection
7. **Error Logging** - Persistent, queryable error tracking with categorization
8. **E.164 Normalization** - Handle all phone number formats correctly

All patterns are from **Twilio-Aldea** (SMS-based AI therapy platform) deployed on Netlify with Telnyx integration.
