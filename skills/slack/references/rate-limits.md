# Slack Rate Limits (Corrected Feb 2026)

Rate limits vary by app type. The May 2025 changes only reduced `conversations.history` and `conversations.replies` to Tier 1, and only for **commercially-distributed non-Marketplace apps** — NOT internal customer-built apps.

## Rate Limit Tiers

| Tier | Rate | Burst | Methods |
|------|------|-------|---------|
| **Tier 1** | **1/min** | None | `conversations.history`, `conversations.replies` (commercial non-Marketplace only) |
| **Tier 2** | 20/min | 3 burst | `conversations.list`, `users.list`, `search.messages`, `search.files` |
| **Tier 3** | 50/min | 5 burst | `reactions.*`, `conversations.info`, `conversations.join`, `users.info`, `users.lookupByEmail`, `chat.update`, `chat.delete`, `chat.scheduleMessage` |
| **Tier 4** | 100+/min | Varies | `files.getUploadURLExternal`, `files.completeUploadExternal` |
| **Special** | 1/sec/channel | 1 burst | `chat.postMessage` (per-channel, not global) |

## Key Corrections from Official Docs

- `conversations.list` and `users.list` were **never** reduced to Tier 1 — they remain Tier 2
- `files.getUploadURLExternal` and `files.completeUploadExternal` are Tier 4, not Tier 2
- `chat.postMessage` is "Special Tier" — 1 message per second **per channel**, not a global limit
- Tier 1 reduction only applies to commercially-distributed non-Marketplace apps; internal apps get Tier 3 for history/replies
- `search.messages` with a bot token (`xoxb-`) only searches channels the bot is a member of; use a user token (`xoxp-`) for workspace-wide search

## Handling 429 Responses

When rate limited, Slack returns:
- HTTP 429 status
- `Retry-After` header (seconds to wait)
- `X-RateLimit-*` headers on successful responses

Our `_slack_utils.py` handles this automatically:
1. Local cooldown timer per method prevents most 429s
2. On 429: reads `Retry-After`, waits, retries (up to 2 times)
3. Prints warning to stderr when waiting >5 seconds

## Practical Impact

### Reading history is the bottleneck (for commercial apps)
- Reading 1 channel = 1 API call = fine
- Reading 3 channels = 3 min minimum (1/min limit for commercial apps)
- Internal apps at Tier 3: 50/min = comfortable

**Mitigation**: Read once, parse locally. Don't re-fetch if you already have the data.

### Writing is comfortable
- `chat.postMessage` at 1/sec per channel = plenty for any reasonable use
- Reactions, updates at 50/min = comfortable

### Search is moderate
- 20 queries/min = fine for interactive use
- Bot tokens only search channels the bot is in
- For workspace-wide search, use a user token with `search:read` scope

## Marketplace vs Non-Marketplace

Marketplace apps get 10-100x higher limits. If rate limits become a real bottleneck, consider publishing the app to the Slack App Directory. For personal/team bots, the current limits are workable with the built-in throttling.

## References

- [Slack Rate Limits](https://api.slack.com/docs/rate-limits) — Official docs
- [May 2025 Rate Limit Changes](https://api.slack.com/changelog/2025-05-rate-limit-changes) — Changelog
