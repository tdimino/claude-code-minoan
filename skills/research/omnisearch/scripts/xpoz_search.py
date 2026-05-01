#!/usr/bin/env python3
"""
Xpoz Social Media Search — Twitter/X, Reddit, and Instagram via the Xpoz SDK.

Features:
- Twitter/X: search tweets, user timeline, threads, profiles, hashtags, quotes, likes, media
- Reddit: search posts, subreddit posts, post comments, user activity, trending, subreddit info
- Instagram: search posts, user posts/reels, profiles, hashtag posts, comments, followers
- SDK-first: uses XpozClient when available, fails cleanly with install instructions if not
- --json, --no-text, --markdown output modes
- Pydantic v2 model serialization via .model_dump()

Usage:
    xpoz_search.py twitter "Iran IRGC" -n 20
    xpoz_search.py twitter-user IdaeanDaktyl -n 10
    xpoz_search.py twitter-thread 1234567890
    xpoz_search.py twitter-profile elonmusk
    xpoz_search.py reddit "Gaza ceasefire" -n 15 --subreddit worldnews
    xpoz_search.py reddit-sub geopolitics -n 20
    xpoz_search.py reddit-trending -n 10
    xpoz_search.py instagram "conflict photography" -n 10
    xpoz_search.py instagram-user nytimes -n 10
    xpoz_search.py twitter "AI agents" --json
    xpoz_search.py reddit "Minoan civilization" --markdown

Requires: XPOZ_API_KEY environment variable
Install SDK: pip install xpoz (requires Python 3.10+)
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any, List

XPOZ_API_KEY = os.environ.get("XPOZ_API_KEY")
BASE_URL = "https://mcp.xpoz.ai"

try:
    from xpoz import XpozClient
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    XpozClient = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def _get_client() -> "XpozClient":
    """Return an authenticated XpozClient, raising on missing key or SDK."""
    if not XPOZ_API_KEY:
        raise ValueError(
            "XPOZ_API_KEY not set. Get your key at https://xpoz.ai/get-token"
        )
    if not HAS_SDK:
        raise ImportError(
            "Xpoz SDK not installed. Run: pip install xpoz  (requires Python 3.10+)"
        )
    return XpozClient(api_key=XPOZ_API_KEY)


def _to_dict(obj: Any) -> Any:
    """Recursively serialize Pydantic models, PaginatedResults, and plain objects."""
    if obj is None:
        return None
    if hasattr(obj, "data") and hasattr(obj, "has_next_page"):
        return [_to_dict(item) for item in obj.data]
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_dict(i) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Twitter / X
# ---------------------------------------------------------------------------

def twitter_search(query: str, count: int = 10) -> Dict[str, Any]:
    """Search tweets matching query."""
    client = _get_client()
    try:
        result = client.twitter.search_posts(query=query, limit=count)
        return {"platform": "twitter", "query": query, "results": _to_dict(result)}
    finally:
        client.close()


def twitter_user_tweets(username: str, count: int = 10) -> Dict[str, Any]:
    """Fetch recent tweets from a user's timeline."""
    client = _get_client()
    try:
        result = client.twitter.get_posts_by_author(identifier=username, limit=count)
        return {"platform": "twitter", "username": username, "results": _to_dict(result)}
    finally:
        client.close()


def twitter_thread(tweet_id: str) -> Dict[str, Any]:
    """Fetch replies/comments on a tweet ID."""
    client = _get_client()
    try:
        result = client.twitter.get_comments(post_id=tweet_id)
        return {"platform": "twitter", "tweet_id": tweet_id, "results": _to_dict(result)}
    finally:
        client.close()


def twitter_user_profile(username: str) -> Dict[str, Any]:
    """Fetch profile info for a Twitter username."""
    client = _get_client()
    try:
        result = client.twitter.get_user(identifier=username)
        return {"platform": "twitter", "username": username, "results": _to_dict(result)}
    finally:
        client.close()


def twitter_hashtag(hashtag: str, count: int = 10) -> Dict[str, Any]:
    """Search tweets for a hashtag (omit leading #)."""
    client = _get_client()
    try:
        result = client.twitter.search_posts(query=f"#{hashtag}", limit=count)
        return {"platform": "twitter", "hashtag": hashtag, "results": _to_dict(result)}
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Reddit
# ---------------------------------------------------------------------------

def reddit_search(query: str, count: int = 10, subreddit: Optional[str] = None) -> Dict[str, Any]:
    """Search Reddit posts. Optionally scoped to a subreddit."""
    client = _get_client()
    try:
        if subreddit:
            result = client.reddit.search_posts(query=query, subreddit=subreddit, limit=count)
        else:
            result = client.reddit.search_posts(query=query, limit=count)
        return {
            "platform": "reddit",
            "query": query,
            "subreddit": subreddit,
            "results": _to_dict(result),
        }
    finally:
        client.close()


def reddit_subreddit_posts(subreddit: str, count: int = 10) -> Dict[str, Any]:
    """Fetch top posts from a subreddit."""
    client = _get_client()
    try:
        result = client.reddit.get_subreddit_with_posts(subreddit_name=subreddit)
        raw = _to_dict(result)
        posts = raw.get("posts", [])[:count] if isinstance(raw, dict) else raw
        return {"platform": "reddit", "subreddit": subreddit, "results": posts}
    finally:
        client.close()


def reddit_trending(count: int = 10) -> Dict[str, Any]:
    """Fetch trending subreddits."""
    client = _get_client()
    try:
        result = client.reddit.get_subreddits_by_keywords(query="trending")
        return {"platform": "reddit", "results": _to_dict(result)}
    finally:
        client.close()


def reddit_post_comments(post_id: str, count: int = 10) -> Dict[str, Any]:
    """Fetch a Reddit post with its comments."""
    client = _get_client()
    try:
        result = client.reddit.get_post_with_comments(post_id=post_id)
        return {"platform": "reddit", "post_id": post_id, "results": _to_dict(result)}
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

def instagram_search(query: str, count: int = 10) -> Dict[str, Any]:
    """Search Instagram posts by keyword."""
    client = _get_client()
    try:
        result = client.instagram.search_posts(query=query, limit=count)
        return {"platform": "instagram", "query": query, "results": _to_dict(result)}
    finally:
        client.close()


def instagram_user_posts(username: str, count: int = 10) -> Dict[str, Any]:
    """Fetch recent posts from an Instagram user."""
    client = _get_client()
    try:
        result = client.instagram.get_posts_by_user(identifier=username, limit=count)
        return {"platform": "instagram", "username": username, "results": _to_dict(result)}
    finally:
        client.close()


def instagram_user_profile(username: str) -> Dict[str, Any]:
    """Fetch Instagram profile info for a username."""
    client = _get_client()
    try:
        result = client.instagram.get_user(identifier=username)
        return {"platform": "instagram", "username": username, "results": _to_dict(result)}
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _truncate(text: Any, limit: int = 280) -> str:
    """Truncate a string to limit chars, appending ellipsis if needed."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return text[:limit] + "…" if len(text) > limit else text


def format_tweets(data: Dict[str, Any]) -> str:
    """Format twitter results for human-readable output."""
    lines: List[str] = []
    results = data.get("results")
    platform_label = data.get("platform", "twitter").upper()

    if data.get("query"):
        lines.append(f"[{platform_label}] query: {data['query']}")
    elif data.get("username"):
        lines.append(f"[{platform_label}] @{data['username']}")
    elif data.get("tweet_id"):
        lines.append(f"[{platform_label}] thread: {data['tweet_id']}")
    elif data.get("hashtag"):
        lines.append(f"[{platform_label}] #{data['hashtag']}")

    if results is None:
        lines.append("(no results)")
        return "\n".join(lines)

    # Handle profile response (dict, not list)
    if isinstance(results, dict) and not isinstance(results, list):
        for key, val in results.items():
            if val is not None:
                lines.append(f"  {key}: {_truncate(val, 120)}")
        return "\n".join(lines)

    # Handle list of tweets
    items = results if isinstance(results, list) else results.get("tweets", [results])
    lines.append(f"  {len(items)} result(s)")
    lines.append("")
    for i, tweet in enumerate(items, 1):
        if not isinstance(tweet, dict):
            tweet = {}
        author = tweet.get("author") or tweet.get("username") or tweet.get("user", {})
        if isinstance(author, dict):
            author = author.get("username") or author.get("name", "unknown")
        text = tweet.get("text") or tweet.get("full_text", "")
        date = tweet.get("created_at") or tweet.get("date", "")
        likes = tweet.get("likes") or tweet.get("favorite_count", "")
        retweets = tweet.get("retweets") or tweet.get("retweet_count", "")
        url = tweet.get("url") or tweet.get("tweet_url", "")

        lines.append(f"  [{i}] @{author}" + (f"  {date[:10]}" if date else ""))
        lines.append(f"      {_truncate(text)}")
        meta_parts = []
        if likes:
            meta_parts.append(f"likes: {likes}")
        if retweets:
            meta_parts.append(f"RT: {retweets}")
        if url:
            meta_parts.append(url)
        if meta_parts:
            lines.append("      " + "  |  ".join(meta_parts))
        lines.append("")

    return "\n".join(lines)


def format_reddit(data: Dict[str, Any]) -> str:
    """Format reddit results for human-readable output."""
    lines: List[str] = []
    results = data.get("results")

    if data.get("subreddit") and data.get("query"):
        lines.append(f"[REDDIT] r/{data['subreddit']} — search: {data['query']}")
    elif data.get("subreddit"):
        lines.append(f"[REDDIT] r/{data['subreddit']}")
    elif data.get("post_id"):
        lines.append(f"[REDDIT] comments on post: {data['post_id']}")
    else:
        label = f"search: {data['query']}" if data.get("query") else "trending"
        lines.append(f"[REDDIT] {label}")

    if results is None:
        lines.append("(no results)")
        return "\n".join(lines)

    items = results if isinstance(results, list) else results.get("posts", [results])
    lines.append(f"  {len(items)} result(s)")
    lines.append("")
    for i, post in enumerate(items, 1):
        if not isinstance(post, dict):
            post = {}
        title = post.get("title") or post.get("body", "")
        subreddit = post.get("subreddit") or post.get("subreddit_name", "")
        author = post.get("author") or post.get("username", "unknown")
        score = post.get("score") or post.get("ups", "")
        comments = post.get("num_comments") or post.get("comments", "")
        url = post.get("url") or post.get("permalink", "")
        date = post.get("created_utc") or post.get("date", "")

        lines.append(f"  [{i}] {_truncate(title, 120)}")
        sub_part = f"r/{subreddit}" if subreddit else ""
        auth_part = f"u/{author}" if author else ""
        date_part = str(date)[:10] if date else ""
        header = "  ".join(p for p in [sub_part, auth_part, date_part] if p)
        if header:
            lines.append(f"      {header}")
        meta_parts = []
        if score:
            meta_parts.append(f"score: {score}")
        if comments:
            meta_parts.append(f"comments: {comments}")
        if url:
            meta_parts.append(url[:80])
        if meta_parts:
            lines.append("      " + "  |  ".join(meta_parts))
        lines.append("")

    return "\n".join(lines)


def format_instagram(data: Dict[str, Any]) -> str:
    """Format instagram results for human-readable output."""
    lines: List[str] = []
    results = data.get("results")

    if data.get("query"):
        lines.append(f"[INSTAGRAM] search: {data['query']}")
    elif data.get("username"):
        lines.append(f"[INSTAGRAM] @{data['username']}")
    else:
        lines.append("[INSTAGRAM]")

    if results is None:
        lines.append("(no results)")
        return "\n".join(lines)

    # Profile response
    if isinstance(results, dict) and not isinstance(results, list):
        for key, val in results.items():
            if val is not None:
                lines.append(f"  {key}: {_truncate(val, 120)}")
        return "\n".join(lines)

    items = results if isinstance(results, list) else results.get("posts", [results])
    lines.append(f"  {len(items)} result(s)")
    lines.append("")
    for i, post in enumerate(items, 1):
        if not isinstance(post, dict):
            post = {}
        caption = post.get("caption") or post.get("text", "")
        author = post.get("owner") or post.get("username") or post.get("user", {})
        if isinstance(author, dict):
            author = author.get("username") or author.get("full_name", "unknown")
        likes = post.get("like_count") or post.get("likes", "")
        comments = post.get("comment_count") or post.get("comments", "")
        date = post.get("taken_at") or post.get("timestamp", "")
        url = post.get("url") or post.get("permalink", "")

        lines.append(f"  [{i}] @{author}" + (f"  {str(date)[:10]}" if date else ""))
        if caption:
            lines.append(f"      {_truncate(caption)}")
        meta_parts = []
        if likes:
            meta_parts.append(f"likes: {likes}")
        if comments:
            meta_parts.append(f"comments: {comments}")
        if url:
            meta_parts.append(url[:80])
        if meta_parts:
            lines.append("      " + "  |  ".join(meta_parts))
        lines.append("")

    return "\n".join(lines)


def _to_markdown(data: Dict[str, Any]) -> str:
    """Format results as semantic Markdown."""
    platform = data.get("platform", "").upper()
    results = data.get("results")
    lines: List[str] = [f"# {platform} Results\n"]

    if data.get("query"):
        lines.append(f"**Query:** {data['query']}\n")
    elif data.get("username"):
        lines.append(f"**User:** @{data['username']}\n")

    if results is None:
        lines.append("*No results*")
        return "\n".join(lines)

    if isinstance(results, dict):
        for key, val in results.items():
            if val is not None:
                lines.append(f"- **{key}:** {val}")
        return "\n".join(lines)

    items = results if isinstance(results, list) else []
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        title = item.get("text") or item.get("title") or item.get("caption") or ""
        url = item.get("url") or item.get("link") or item.get("permalink") or ""
        author = item.get("author") or item.get("username") or item.get("user", {})
        if isinstance(author, dict):
            author = author.get("username") or author.get("name", "")

        header = f"{i}. "
        if url:
            header += f"[{_truncate(title, 120)}]({url})"
        else:
            header += _truncate(title, 120)
        if author:
            header += f" — @{author}"
        lines.append(header)

        meta = []
        for k in ("likes", "favorite_count", "score", "retweets", "num_comments"):
            v = item.get(k)
            if v:
                meta.append(f"{k}: {v}")
        date = item.get("created_at") or item.get("date") or item.get("created_utc", "")
        if date:
            meta.append(str(date)[:10])
        if meta:
            lines.append(f"   *{', '.join(meta)}*")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_common_flags(p: argparse.ArgumentParser) -> None:
    """Attach shared output flags to a subparser."""
    p.add_argument("-n", "--num", type=int, default=10, help="Number of results (default: 10)")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output raw JSON")
    p.add_argument("--no-text", action="store_true", help="Suppress human-readable text output")
    p.add_argument("--markdown", action="store_true", help="Wrap output in Markdown code fence")


def _format_no_text(data: Dict[str, Any]) -> str:
    """Show titles/URLs only, no body text."""
    lines: List[str] = []
    platform = data.get("platform", "").upper()
    results = data.get("results")

    if results is None:
        return f"[{platform}] (no results)"

    if isinstance(results, dict):
        name = results.get("username") or results.get("name", "")
        url = results.get("url", "")
        return f"[{platform}] {name}  {url}"

    items = results if isinstance(results, list) else []
    lines.append(f"[{platform}] {len(items)} result(s)")
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        title = (item.get("text") or item.get("title") or item.get("caption") or "")[:120]
        url = item.get("url") or item.get("link") or item.get("permalink") or ""
        author = item.get("author") or item.get("username") or item.get("user", {})
        if isinstance(author, dict):
            author = author.get("username") or author.get("name", "")
        line = f"  [{i}]"
        if author:
            line += f" @{author}"
        if title:
            line += f"  {title}"
        if url:
            line += f"\n      {url}"
        lines.append(line)
    return "\n".join(lines)


def _emit(data: Dict[str, Any], args: argparse.Namespace) -> None:
    """Print results according to output flags."""
    if getattr(args, "as_json", False):
        print(json.dumps(data, indent=2, default=str))
        return
    if getattr(args, "no_text", False):
        print(_format_no_text(data))
        return
    platform = data.get("platform", "")
    if getattr(args, "markdown", False):
        print(_to_markdown(data))
    elif platform == "twitter":
        print(format_tweets(data))
    elif platform == "reddit":
        print(format_reddit(data))
    elif platform == "instagram":
        print(format_instagram(data))
    else:
        print(json.dumps(data, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Xpoz Social Media Search — Twitter/X, Reddit, Instagram",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  twitter QUERY          Search tweets
  twitter-user USERNAME  User's recent tweets
  twitter-thread ID      Full tweet thread
  twitter-profile USER   User profile
  twitter-hashtag TAG    Tweets for a hashtag (omit #)
  reddit QUERY           Search Reddit posts
  reddit-sub SUBREDDIT   Subreddit top posts
  reddit-post ID         Post comments
  reddit-trending        Trending posts
  instagram QUERY        Search Instagram posts
  instagram-user USER    User's recent posts
  instagram-profile USER User profile info

Output flags (all subcommands):
  -n / --num     Number of results
  --json         Raw JSON output
  --no-text      Suppress all output (useful when piping --json)
  --markdown     Wrap in Markdown code fence

Examples:
  xpoz_search.py twitter "IRGC drone" -n 20
  xpoz_search.py twitter-user IdaeanDaktyl
  xpoz_search.py twitter-thread 1234567890123456789
  xpoz_search.py reddit "Minoan script" --subreddit linguistics
  xpoz_search.py reddit-sub worldnews -n 15
  xpoz_search.py instagram "Gaza" --json
        """,
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # --- twitter ---
    p = subparsers.add_parser("twitter", help="Search tweets")
    p.add_argument("query", help="Search query")
    _add_common_flags(p)

    # --- twitter-user ---
    p = subparsers.add_parser("twitter-user", help="User's recent tweets")
    p.add_argument("username", help="Twitter/X username (without @)")
    _add_common_flags(p)

    # --- twitter-thread ---
    p = subparsers.add_parser("twitter-thread", help="Full tweet thread")
    p.add_argument("tweet_id", help="Tweet ID")
    p.add_argument("--json", dest="as_json", action="store_true")
    p.add_argument("--no-text", action="store_true")
    p.add_argument("--markdown", action="store_true")

    # --- twitter-profile ---
    p = subparsers.add_parser("twitter-profile", help="User profile info")
    p.add_argument("username", help="Twitter/X username (without @)")
    p.add_argument("--json", dest="as_json", action="store_true")
    p.add_argument("--no-text", action="store_true")
    p.add_argument("--markdown", action="store_true")

    # --- twitter-hashtag ---
    p = subparsers.add_parser("twitter-hashtag", help="Tweets for a hashtag")
    p.add_argument("hashtag", help="Hashtag without the leading #")
    _add_common_flags(p)

    # --- reddit ---
    p = subparsers.add_parser("reddit", help="Search Reddit posts")
    p.add_argument("query", help="Search query")
    p.add_argument("--subreddit", "-s", help="Scope search to this subreddit")
    _add_common_flags(p)

    # --- reddit-sub ---
    p = subparsers.add_parser("reddit-sub", help="Top posts from a subreddit")
    p.add_argument("subreddit", help="Subreddit name (without r/)")
    _add_common_flags(p)

    # --- reddit-post ---
    p = subparsers.add_parser("reddit-post", help="Comments on a Reddit post")
    p.add_argument("post_id", help="Reddit post ID")
    _add_common_flags(p)

    # --- reddit-trending ---
    p = subparsers.add_parser("reddit-trending", help="Trending posts across Reddit")
    _add_common_flags(p)

    # --- instagram ---
    p = subparsers.add_parser("instagram", help="Search Instagram posts")
    p.add_argument("query", help="Search query")
    _add_common_flags(p)

    # --- instagram-user ---
    p = subparsers.add_parser("instagram-user", help="User's recent posts")
    p.add_argument("username", help="Instagram username (without @)")
    _add_common_flags(p)

    # --- instagram-profile ---
    p = subparsers.add_parser("instagram-profile", help="Instagram user profile")
    p.add_argument("username", help="Instagram username (without @)")
    p.add_argument("--json", dest="as_json", action="store_true")
    p.add_argument("--no-text", action="store_true")
    p.add_argument("--markdown", action="store_true")

    args = parser.parse_args()
    num = getattr(args, "num", 10)

    try:
        if args.subcommand == "twitter":
            data = twitter_search(args.query, count=num)
        elif args.subcommand == "twitter-user":
            data = twitter_user_tweets(args.username, count=num)
        elif args.subcommand == "twitter-thread":
            data = twitter_thread(args.tweet_id)
        elif args.subcommand == "twitter-profile":
            data = twitter_user_profile(args.username)
        elif args.subcommand == "twitter-hashtag":
            data = twitter_hashtag(args.hashtag, count=num)
        elif args.subcommand == "reddit":
            data = reddit_search(args.query, count=num, subreddit=getattr(args, "subreddit", None))
        elif args.subcommand == "reddit-sub":
            data = reddit_subreddit_posts(args.subreddit, count=num)
        elif args.subcommand == "reddit-post":
            data = reddit_post_comments(args.post_id, count=num)
        elif args.subcommand == "reddit-trending":
            data = reddit_trending(count=num)
        elif args.subcommand == "instagram":
            data = instagram_search(args.query, count=num)
        elif args.subcommand == "instagram-user":
            data = instagram_user_posts(args.username, count=num)
        elif args.subcommand == "instagram-profile":
            data = instagram_user_profile(args.username)
        else:
            print(f"Unknown subcommand: {args.subcommand}", file=sys.stderr)
            sys.exit(1)

        _emit(data, args)

    except (ValueError, ImportError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
