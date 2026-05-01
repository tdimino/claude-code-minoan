# Xpoz API Reference (SDK v0.6.1)

## Overview

- **SDK**: `pip install xpoz` (requires Python 3.10+)
- **Auth**: API key passed to `XpozClient(api_key=...)`
- **Transport**: MCP-based (streamable HTTP to `mcp.xpoz.ai`)
- **Cost**: Free tier 100,000 results/month
- **Key**: `XPOZ_API_KEY` env var. Get at https://www.xpoz.ai
- **Important**: Call `client.close()` after use to clean up MCP connection

## SDK Client

```python
from xpoz import XpozClient
client = XpozClient(api_key=os.environ["XPOZ_API_KEY"])
# ... use client ...
client.close()
```

## Return Types

- **PaginatedResult[T]**: Has `.data` (list of T), `.has_next_page`, `.next_page()`, `.pagination`, `.export_csv()`, `.get_page()`
- Individual models (TwitterPost, RedditPost, etc.) have `.model_dump()` for dict serialization
- PaginatedResult does NOT have `.model_dump()` — access `.data` to get the list

## Twitter/X Methods

### client.twitter.search_posts(query, *, limit, ...)

Search tweets by keyword.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | str | required | Search query |
| `limit` | int | None | Max results |
| `start_date` | str | None | Start date `YYYY-MM-DD` |
| `end_date` | str | None | End date `YYYY-MM-DD` |
| `author_username` | str | None | Filter by author |
| `language` | str | None | Language code (e.g. `"en"`) |
| `filter_out_retweets` | bool | None | Exclude retweets |
| `force_latest` | bool | None | Force latest results |
| `fields` | list[str] | None | Specific fields to return |

Returns: `PaginatedResult[TwitterPost]`

### client.twitter.get_posts_by_author(identifier, *, limit, ...)

Get recent tweets from a specific user.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `identifier` | str | required | Username or user ID |
| `limit` | int | None | Max results |
| `start_date` | str | None | Start date |
| `end_date` | str | None | End date |

Returns: `PaginatedResult[TwitterPost]`

### client.twitter.get_comments(post_id, *, ...)

Get replies/comments on a tweet.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `post_id` | str | required | Tweet ID |
| `start_date` | str | None | Start date |

Returns: `PaginatedResult[TwitterPost]`

### client.twitter.get_user(identifier, identifier_type="username", *, fields)

Get user profile details (bio, followers, following, tweet count).

Returns: `TwitterUser` (has `.model_dump()`)

### client.twitter.count_posts(query, *, ...)

Count tweets matching a query.

### client.twitter.get_posts_by_ids(ids, *, fields)

Get tweets by their IDs.

### client.twitter.get_quotes(post_id, *, ...)

Get quote tweets of a specific tweet.

### client.twitter.get_retweets(post_id, *, ...)

Get retweets of a specific tweet.

### client.twitter.get_user_connections(identifier, *, ...)

Get a user's followers/following.

### client.twitter.get_users(identifiers, *, fields)

Get multiple user profiles.

### client.twitter.get_users_by_keywords(query, *, ...)

Search for users by keywords.

### client.twitter.search_users(query, *, ...)

Search for user profiles.

### client.twitter.get_post_interacting_users(post_id, *, ...)

Get users who interacted with a tweet.

## Reddit Methods

### client.reddit.search_posts(query, *, limit, subreddit, sort, time, ...)

Search Reddit posts.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | str | required | Search query |
| `limit` | int | None | Max results |
| `subreddit` | str | None | Scope to subreddit |
| `sort` | str | None | `"hot"`, `"new"`, `"top"`, `"rising"` |
| `time` | str | None | `"hour"`, `"day"`, `"week"`, `"month"`, `"year"`, `"all"` |
| `start_date` | str | None | Start date |
| `end_date` | str | None | End date |

Returns: `PaginatedResult[RedditPost]`

### client.reddit.get_subreddit_with_posts(subreddit_name, *, ...)

Get subreddit info and its posts.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `subreddit_name` | str | required | Subreddit name (without r/) |
| `subreddit_fields` | list[str] | None | Subreddit fields |
| `post_fields` | list[str] | None | Post fields |

Returns: `SubredditWithPosts` (has `.model_dump()` with `posts` key)

### client.reddit.get_post_with_comments(post_id, *, ...)

Get a post and its comments.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `post_id` | str | required | Reddit post ID |
| `post_fields` | list[str] | None | Post fields |
| `comment_fields` | list[str] | None | Comment fields |

Returns: `RedditPostWithComments` (has `.model_dump()`)

### client.reddit.get_subreddits_by_keywords(query, *, ...)

Find subreddits by keyword search.

Returns: `PaginatedResult[RedditSubreddit]`

### client.reddit.search_comments(query, *, ...)

Search Reddit comments.

### client.reddit.search_subreddits(query, *, ...)

Search subreddits.

### client.reddit.search_users(query, *, ...)

Search Reddit users.

### client.reddit.get_user(identifier, *, fields)

Get Reddit user profile.

### client.reddit.get_users_by_keywords(query, *, ...)

Find Reddit users by keywords.

## Instagram Methods

### client.instagram.search_posts(query, *, limit, ...)

Search Instagram posts.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | str | required | Search query |
| `limit` | int | None | Max results |
| `start_date` | str | None | Start date |
| `end_date` | str | None | End date |

Returns: `PaginatedResult[InstagramPost]`

### client.instagram.get_posts_by_user(identifier, identifier_type="username", *, limit, ...)

Get posts from a specific Instagram user.

Returns: `PaginatedResult[InstagramPost]`

### client.instagram.get_user(identifier, identifier_type="username", *, fields)

Get Instagram user profile.

Returns: `InstagramUser` (has `.model_dump()`)

### client.instagram.get_comments(post_id, *, ...)

Get comments on an Instagram post.

### client.instagram.get_post_interacting_users(post_id, *, ...)

Get users who interacted with a post.

### client.instagram.get_posts_by_ids(ids, *, fields)

Get Instagram posts by IDs.

### client.instagram.get_user_connections(identifier, *, ...)

Get a user's followers/following.

### client.instagram.get_users_by_keywords(query, *, ...)

Find Instagram users by keywords.

### client.instagram.search_users(query, *, ...)

Search for Instagram user profiles.

## Script Subcommand Mapping

| Subcommand | SDK Method | Platform |
|-----------|-----------|----------|
| `twitter` | `client.twitter.search_posts()` | Twitter/X |
| `twitter-user` | `client.twitter.get_posts_by_author()` | Twitter/X |
| `twitter-thread` | `client.twitter.get_comments()` | Twitter/X |
| `twitter-profile` | `client.twitter.get_user()` | Twitter/X |
| `twitter-hashtag` | `client.twitter.search_posts(query="#tag")` | Twitter/X |
| `reddit` | `client.reddit.search_posts()` | Reddit |
| `reddit-sub` | `client.reddit.get_subreddit_with_posts()` | Reddit |
| `reddit-post` | `client.reddit.get_post_with_comments()` | Reddit |
| `reddit-trending` | `client.reddit.get_subreddits_by_keywords()` | Reddit |
| `instagram` | `client.instagram.search_posts()` | Instagram |
| `instagram-user` | `client.instagram.get_posts_by_user()` | Instagram |
| `instagram-profile` | `client.instagram.get_user()` | Instagram |

## Key Differences from Pre-0.6 SDK

- All `count` parameters renamed to `limit`
- `search_tweets()` → `search_posts()`
- `get_user_tweets()` → `get_posts_by_author(identifier=)`
- `get_tweet_thread()` → `get_comments(post_id=)`
- `get_user_profile()` → `get_user(identifier=)`
- `get_hashtag_tweets()` removed — use `search_posts(query="#tag")`
- `get_subreddit_posts()` → `get_subreddit_with_posts(subreddit_name=)` (returns subreddit info + posts)
- `get_post_comments()` → `get_post_with_comments(post_id=)` (returns post + comments)
- `get_trending_posts()` removed — use `get_subreddits_by_keywords(query="trending")`
- `get_user_posts()` (Instagram) → `get_posts_by_user(identifier=)`
- Transport changed from REST to MCP (streamable HTTP)
- Must call `client.close()` to clean up

## Known Limitations

- SDK uses MCP transport — requires network connection for client init
- `get_subreddit_with_posts` does not accept a query parameter — subreddit browsing only
- No dedicated "trending" endpoint — `get_subreddits_by_keywords` is the closest
- Rate limits not documented per-method; 100K results/month aggregate
