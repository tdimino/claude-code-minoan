# X API Pay-Per-Use Rate Card (July 2026)

Source: https://docs.x.com/x-api/getting-started/pricing (fetched 2026-07-05).
X repriced twice in 2026 (February launch, April hike) — re-verify before large spends.

## Reads (charged per resource returned)

| Resource | Cost |
|----------|------|
| Post read | $0.005 |
| User read | $0.010 |
| DM event read | $0.010 |
| Following/Followers read | $0.010 |
| List / Space / Community / Note read | $0.005 |
| Like / Mute / Block read | $0.001 |
| Profile Update read | $0.005 |
| **Owned Reads** (see below) | **$0.001** |

## Writes (charged per request)

| Action | Cost |
|--------|------|
| Post create | $0.015 |
| **Post create (with URL)** | **$0.200** — 13x surcharge; x-search refuses without `--allow-url` |
| Post create (summoned) | $0.010 |
| DM / user interaction create | $0.015 |
| Interaction delete | $0.010 |
| Bookmark | $0.005 |
| List create / manage | $0.010 / $0.005 |
| Content manage | $0.005 |
| Media metadata | $0.005 |
| Privacy update | $0.010 |
| Mute delete | $0.005 |
| Trends | $0.010 |
| Counts (recent / all) | $0.005 / $0.010 |

Webhook events via the X Activity API bill per event delivered ($0.005–$0.010 for
post.create, follows, DMs/chat received; deletes and sent-events not billed), with
the same 24h dedup window.

## Owned Reads — $0.001/resource

Requests by your own developer app for the authenticated user's own data. Qualifying
endpoints (when `{id}` = authenticated user who owns the app):

`/2/users/{id}/tweets`, `/mentions`, `/liked_tweets`, `/bookmarks`, `/followers`,
`/following`, `/blocking`, `/muting`, `/owned_lists`, `/followed_lists`,
`/list_memberships`, `/pinned_lists`

This is the cheap path for mentions monitoring and bookmark archival (~$0.02 per
20-bookmark fetch) — the designated migration target for Smaug when bird dies.

## Billing mechanics

- **Deduplication:** same resource re-requested within a 24h UTC window is charged once. Window resets midnight UTC.
- **Read ceiling:** 2,000,000 posts/month on pay-per-use (`x-search usage` shows cap + consumption).
- **xAI credit rebate** per billing cycle, on cumulative spend: $200+ → 10%, $500+ → 15%, $1,000+ → 20% back as xAI API credits.
- **Spending limits + auto-recharge** configured in the Developer Console (console.x.com). Auto-recharge fires at most once per 5 minutes and pauses at zero balance.
- **Usage endpoint:** `GET /2/usage/tweets` (Bearer) — wired as `x-search usage`.

## Worked estimates

| Operation | Est. cost |
|-----------|-----------|
| Quick search (~100 tweets) | ~$0.50 |
| 3-page deep search (~300 tweets) | ~$1.50 |
| Profile check (user + 20 tweets, default `--count`) | ~$0.11 |
| Feed pull, 20 accounts × 4 tweets | ~$0.40 |
| Post (no URL) | $0.015 |
| Cached / deduped repeat | free |
