# Production Supabase Patterns

**Source**: Twilio-Aldea Production Codebase (SMS-based AI therapy platform)

This document contains real-world patterns extracted from a production Supabase application handling user sessions, messages, state management, and memory persistence.

## Table of Contents

1. [Client Initialization](#client-initialization)
2. [Session Management](#session-management)
3. [Memory Persistence](#memory-persistence)
4. [Message Storage](#message-storage)
5. [State Management](#state-management)
6. [Error Handling](#error-handling)
7. [Performance Patterns](#performance-patterns)

## Client Initialization

### Singleton Pattern with Environment Variables

```typescript
/**
 * Supabase Client Configuration
 * Pattern: Singleton with lazy initialization
 */
import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseClient: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (!supabaseClient) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY;

    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Missing Supabase environment variables');
    }

    supabaseClient = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,  // Server-side: no token refresh needed
        persistSession: false,     // Server-side: no session persistence
      },
    });
  }

  return supabaseClient;
}

export const supabase = getSupabaseClient();
```

**Why This Pattern?**
- ✅ Single client instance across application (better performance)
- ✅ Lazy initialization (client created only when needed)
- ✅ Environment validation at startup (fail fast)
- ✅ Server-side config (no session persistence overhead)

**When to Use**:
- Server-side applications (Next.js API routes, serverless functions)
- Applications using service role key

**When NOT to Use**:
- Client-side applications (use `createBrowserClient` instead)
- Multi-tenant applications (may need client per tenant)

## Session Management

### Load or Create Pattern with Timeout Logic

```typescript
/**
 * Session Management with Automatic Timeout
 * Pattern: Load-or-create with state reset on timeout
 */
import { SupabaseClient } from '@supabase/supabase-js';
import { getSupabaseClient } from './client';

export interface UserSession {
  id: string;
  phone_number: string;
  assigned_persona: string;
  first_contact_at: string;
  last_active_at: string;
  total_messages: number;
  metadata: Record<string, any>;
  __isNewSession?: boolean;  // Transient flag (not persisted)
}

const SESSION_TIMEOUT_MS = 60 * 60 * 1000; // 1 hour

export async function loadOrCreateSession(
  phoneNumber: string
): Promise<UserSession> {
  const supabase = getSupabaseClient();
  const now = new Date();
  const nowIso = now.toISOString();

  // Try to find existing session
  const { data: existing, error: fetchError } = await supabase
    .from('user_sessions')
    .select('*')
    .eq('phone_number', phoneNumber)
    .single();

  // Handle "no rows returned" as valid (not an error)
  if (fetchError && fetchError.code !== 'PGRST116') {
    throw new Error(`Failed to load session: ${fetchError.message}`);
  }

  if (existing) {
    // Get last user message timestamp
    const lastUserMessage = await getLastUserMessageTimestamp(
      supabase,
      existing.id
    );

    // Check if session has timed out
    const timeSinceUserMessage = lastUserMessage
      ? now.getTime() - lastUserMessage.getTime()
      : 0;

    const shouldIncrement = lastUserMessage
      ? timeSinceUserMessage >= SESSION_TIMEOUT_MS
      : false;

    // Increment session number if timeout occurred
    const currentNumber = coerceSessionNumber(existing.metadata);
    const nextSessionNumber = shouldIncrement
      ? currentNumber + 1
      : currentNumber;

    const metadata = buildSessionMetadata(
      existing.metadata,
      nextSessionNumber,
      nowIso,
      shouldIncrement
    );

    // Update session
    await supabase
      .from('user_sessions')
      .update({ last_active_at: nowIso, metadata })
      .eq('id', existing.id);

    // If timeout, clear ephemeral state
    if (shouldIncrement) {
      await Promise.all([
        supabase.from('process_memories').delete().eq('session_id', existing.id),
        supabase.from('mental_process_state').delete().eq('session_id', existing.id),
        supabase.from('working_memory_snapshots').delete().eq('session_id', existing.id),
      ]);
    }

    return {
      ...existing,
      metadata,
      last_active_at: nowIso,
      __isNewSession: false,
    };
  }

  // Create new session
  const assignedPersona = assignPersona();  // Your persona assignment logic

  const { data: newSession, error: insertError } = await supabase
    .from('user_sessions')
    .insert({
      phone_number: phoneNumber,
      assigned_persona: assignedPersona,
      total_messages: 0,
      metadata: { session_number: 1, last_session_started_at: nowIso },
    })
    .select()
    .single();

  if (insertError) {
    throw new Error(`Failed to create session: ${insertError.message}`);
  }

  return {
    ...newSession,
    __isNewSession: true,
  } as UserSession;
}

// Helper: Get last user message timestamp
async function getLastUserMessageTimestamp(
  supabase: SupabaseClient,
  sessionId: string
): Promise<Date | null> {
  const { data, error } = await supabase
    .from('messages')
    .select('created_at')
    .eq('session_id', sessionId)
    .eq('role', 'user')
    .order('created_at', { ascending: false })
    .limit(1);

  if (error) {
    console.warn('Failed to load last user message timestamp', error);
    return null;
  }

  const raw = data?.[0]?.created_at;
  if (!raw) return null;

  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}
```

**Key Patterns**:
1. **Graceful Error Handling**: Distinguish between "no rows" (PGRST116) and real errors
2. **Timeout Logic**: Automatically reset state after inactivity
3. **Transient Flags**: Use `__` prefix for non-persisted computed properties
4. **Atomic State Reset**: Clear multiple related tables on timeout

## Memory Persistence

### Dual Persistence Pattern (soulMemory + Regions)

```typescript
/**
 * Soul Memory Persistence
 * Pattern: Upsert with conflict resolution
 */
import { getSupabaseClient } from './client';

export interface SoulMemoryRow {
  id: string;
  session_id: string;
  key: string;
  value: any;  // JSONB column - stores any JSON-serializable value
  updated_at: string;
}

// Save (upsert) soul memory
export async function saveSoulMemory(
  sessionId: string,
  key: string,
  value: any
): Promise<SoulMemoryRow> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from('soul_memories')
    .upsert(
      {
        session_id: sessionId,
        key,
        value,
        updated_at: new Date().toISOString(),
      },
      { onConflict: 'session_id,key' }  // Composite unique constraint
    )
    .select()
    .single();

  if (error) {
    throw new Error(`Failed to save soul memory '${key}': ${error.message}`);
  }

  return data as SoulMemoryRow;
}

// Load all soul memories for a session
export async function loadSoulMemories(
  sessionId: string
): Promise<Record<string, any>> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from('soul_memories')
    .select('*')
    .eq('session_id', sessionId);

  if (error) {
    throw new Error(`Failed to load soul memories: ${error.message}`);
  }

  // Convert array to key-value map
  const map: Record<string, any> = {};
  for (const row of (data || []) as SoulMemoryRow[]) {
    map[row.key] = row.value;
  }

  return map;
}

// Load specific soul memory key
export async function loadSoulMemoryKey(
  sessionId: string,
  key: string
): Promise<any | undefined> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from('soul_memories')
    .select('value')
    .eq('session_id', sessionId)
    .eq('key', key)
    .single();

  // PGRST116 = no rows, not an error
  if (error && error.code !== 'PGRST116') {
    throw new Error(`Failed to load soul memory '${key}': ${error.message}`);
  }

  return (data as any)?.value;
}

/**
 * Process Memory Persistence
 * Pattern: Scoped by session + process name
 */
export interface ProcessMemoryRow {
  id: string;
  session_id: string;
  process_name: string;
  key: string;
  value: any;
  updated_at: string;
}

export async function saveProcessMemory(
  sessionId: string,
  processName: string,
  key: string,
  value: any
): Promise<ProcessMemoryRow> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from('process_memories')
    .upsert(
      {
        session_id: sessionId,
        process_name: processName,
        key,
        value,
        updated_at: new Date().toISOString(),
      },
      { onConflict: 'session_id,process_name,key' }  // Triple composite key
    )
    .select()
    .single();

  if (error) {
    throw new Error(
      `Failed to save process memory '${processName}:${key}': ${error.message}`
    );
  }

  return data as ProcessMemoryRow;
}
```

**Database Schema**:

```sql
-- Soul memories table (persistent across process transitions)
CREATE TABLE soul_memories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid REFERENCES user_sessions(id) ON DELETE CASCADE,
  key text NOT NULL,
  value jsonb NOT NULL,
  updated_at timestamptz DEFAULT now(),
  UNIQUE(session_id, key)  -- Composite unique constraint
);

CREATE INDEX idx_soul_memories_session ON soul_memories(session_id);

-- Process memories table (ephemeral, cleared on process transition)
CREATE TABLE process_memories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid REFERENCES user_sessions(id) ON DELETE CASCADE,
  process_name text NOT NULL,
  key text NOT NULL,
  value jsonb NOT NULL,
  updated_at timestamptz DEFAULT now(),
  UNIQUE(session_id, process_name, key)  -- Triple composite key
);

CREATE INDEX idx_process_memories_session ON process_memories(session_id);
CREATE INDEX idx_process_memories_process ON process_memories(session_id, process_name);
```

**Key Patterns**:
1. **Upsert Pattern**: Use `onConflict` to insert or update atomically
2. **Composite Keys**: Multi-column unique constraints for scoping
3. **JSONB Storage**: Flexible schema for any JSON value
4. **Cascading Deletes**: Automatic cleanup when session deleted
5. **Graceful Missing**: Treat "no rows" as valid (return undefined)

## Message Storage

### Message Storage with Regions

```typescript
/**
 * Message Storage with Memory Regions
 * Pattern: Region-based message organization
 */
import { getSupabaseClient } from './client';
import { Memory, ChatMessageRoleEnum } from '../core/types';

export interface MessageRecord {
  id: string;
  session_id: string;
  message_sid?: string;  // External message ID (SMS, etc.)
  role: string;
  content: string;
  region: string;        // Memory region: 'core', 'summary', 'default', etc.
  metadata: Record<string, any>;
  created_at: string;
}

export async function saveMessage(
  sessionId: string,
  role: ChatMessageRoleEnum,
  content: string,
  options: {
    messageSid?: string;
    region?: string;
    metadata?: Record<string, any>;
  } = {}
): Promise<MessageRecord> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from('messages')
    .insert({
      session_id: sessionId,
      role,
      content,
      region: options.region || 'default',
      message_sid: options.messageSid,
      metadata: options.metadata || {},
    })
    .select()
    .single();

  if (error) {
    throw new Error(`Failed to save message: ${error.message}`);
  }

  return data as MessageRecord;
}

// Load conversation history (most recent N messages)
export async function loadConversationHistory(
  sessionId: string,
  options: {
    limit?: number;
    region?: string;
  } = {}
): Promise<Memory[]> {
  const supabase = getSupabaseClient();
  const { limit = 20, region } = options;

  let query = supabase
    .from('messages')
    .select('*')
    .eq('session_id', sessionId)
    .order('created_at', { ascending: true });

  if (region) {
    query = query.eq('region', region);
  }

  if (limit > 0) {
    query = query.limit(limit);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(`Failed to load messages: ${error.message}`);
  }

  // Convert to Memory format
  return (data as MessageRecord[]).map((msg) => ({
    role: msg.role as ChatMessageRoleEnum,
    content: msg.content,
    timestamp: msg.created_at,
    metadata: { ...msg.metadata, region: msg.region },
  }));
}

// Load messages by specific region
export async function loadMessagesByRegion(
  sessionId: string,
  regionName: string
): Promise<Memory[]> {
  return loadConversationHistory(sessionId, { region: regionName, limit: 0 });
}

// Delete old messages (cleanup utility)
export async function deleteOldMessages(
  sessionId: string,
  olderThanDays: number
): Promise<number> {
  const supabase = getSupabaseClient();

  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - olderThanDays);

  const { data, error } = await supabase
    .from('messages')
    .delete()
    .eq('session_id', sessionId)
    .lt('created_at', cutoffDate.toISOString())
    .select();

  if (error) {
    throw new Error(`Failed to delete old messages: ${error.message}`);
  }

  return data?.length || 0;
}
```

**Key Patterns**:
1. **Region-Based Organization**: Separate messages by purpose (core, summary, default)
2. **Flexible Metadata**: JSONB field for extensible message metadata
3. **Efficient Loading**: Load only what's needed with limit + region filters
4. **Automatic Cleanup**: Utility to delete old messages

## State Management

### Mental Process State with Validation

```typescript
/**
 * Mental Process State Management
 * Pattern: State validation and auto-correction
 */
import { getSupabaseClient } from './client';
import { mentalProcessRegistry } from '../mentalProcesses';

export interface MentalProcessState {
  id: string;
  session_id: string;
  process_name: string;
  params: Record<string, any>;
  updated_at: string;
}

// Validate process name against registry
function validateProcessName(processName: string): string | null {
  if (!processName || typeof processName !== 'string') {
    return null;
  }

  if (mentalProcessRegistry.has(processName)) {
    return processName;
  }

  return null;
}

// Save mental process state with validation
export async function saveMentalProcessState(
  sessionId: string,
  processName: string,
  params: Record<string, any> = {}
): Promise<MentalProcessState> {
  const supabase = getSupabaseClient();

  // Validate before saving
  const validatedProcessName = validateProcessName(processName);

  if (!validatedProcessName) {
    console.warn(
      `[saveMentalProcessState] Invalid process name "${processName}". ` +
      `Falling back to "initial".`
    );
    processName = 'initial';  // Fallback to safe default
  }

  const { data, error } = await supabase
    .from('mental_process_state')
    .upsert(
      {
        session_id: sessionId,
        process_name: processName,
        params,
        updated_at: new Date().toISOString(),
      },
      { onConflict: 'session_id' }
    )
    .select()
    .single();

  if (error) {
    throw new Error(`Failed to save mental process state: ${error.message}`);
  }

  return data as MentalProcessState;
}

// Load mental process state with auto-correction
export async function loadMentalProcessState(
  sessionId: string
): Promise<MentalProcessState | null> {
  const supabase = getSupabaseClient();

  const { data, error } = await supabase
    .from('mental_process_state')
    .select('*')
    .eq('session_id', sessionId)
    .single();

  if (error && error.code !== 'PGRST116') {
    console.error('Error loading mental process state:', error);
    return null;
  }

  if (!data) return null;

  // Validate and sanitize corrupted state
  const validatedProcessName = validateProcessName(data.process_name);

  if (!validatedProcessName) {
    console.warn(
      `[loadMentalProcessState] Corrupted state for session ${sessionId}: ` +
      `invalid process_name "${data.process_name}". Auto-correcting to "initial".`
    );

    // Auto-correct corrupted state
    try {
      const corrected = await saveMentalProcessState(
        sessionId,
        'initial',
        data.params || {}
      );
      return corrected;
    } catch (correctError) {
      console.error('Failed to correct corrupted state:', correctError);
      return null;
    }
  }

  return data as MentalProcessState;
}
```

**Key Patterns**:
1. **Validation on Save/Load**: Prevent invalid state from corrupting database
2. **Auto-Correction**: Automatically fix corrupted state rather than failing
3. **Fallback Defaults**: Always have a safe fallback ("initial" process)
4. **Logging**: Warn when corruption detected for debugging

## Error Handling

### Graceful Error Handling Pattern

```typescript
/**
 * Error Handling Patterns
 */

// Pattern 1: Distinguish "no rows" from real errors
const { data, error } = await supabase
  .from('table')
  .select()
  .eq('id', id)
  .single();

if (error && error.code !== 'PGRST116') {  // PGRST116 = no rows
  throw new Error(`Database error: ${error.message}`);
}

// Pattern 2: Try-catch with fallback
try {
  await saveSoulMemory(sessionId, 'key', value);
} catch (error) {
  console.warn('Failed to persist memory, continuing...', error);
  // Continue execution - don't fail entire flow
}

// Pattern 3: Parallel operations with Promise.all + error isolation
const results = await Promise.allSettled([
  supabase.from('table1').delete().eq('session_id', sessionId),
  supabase.from('table2').delete().eq('session_id', sessionId),
  supabase.from('table3').delete().eq('session_id', sessionId),
]);

// Check individual results
results.forEach((result, index) => {
  if (result.status === 'rejected') {
    console.error(`Failed to clean table ${index + 1}:`, result.reason);
  }
});
```

## Performance Patterns

### Efficient Query Patterns

```typescript
// ✅ GOOD: Load only what you need
const { data } = await supabase
  .from('messages')
  .select('id, content, created_at')  // Explicit columns
  .eq('session_id', sessionId)
  .order('created_at', { ascending: false })
  .limit(20);  // Limit rows

// ✅ GOOD: Use indexes
// Ensure database has: CREATE INDEX idx_messages_session ON messages(session_id);

// ✅ GOOD: Batch operations
await supabase.from('messages').insert([
  { session_id, role: 'user', content: 'msg1' },
  { session_id, role: 'assistant', content: 'msg2' },
]);

// ✅ GOOD: Use RPC for complex operations
const { data } = await supabase.rpc('increment_session_messages', {
  session_id: sessionId
});

// ❌ AVOID: N+1 queries in loops
for (const session of sessions) {
  const messages = await supabase
    .from('messages')
    .select()
    .eq('session_id', session.id);  // N queries!
}

// ✅ GOOD: Single query with IN clause
const sessionIds = sessions.map(s => s.id);
const { data: allMessages } = await supabase
  .from('messages')
  .select()
  .in('session_id', sessionIds);  // 1 query!
```

## Resources

- **Twilio-Aldea Source**: `~/Desktop/Aldea/Prompt development/Twilio-Aldea/src/lib/supabase/`
- **Database Patterns**: `references/database-patterns.md`
- **Schema Design**: `references/schema-design.md`
- **RLS Policies**: `references/official-docs/row-level-security.md`
