/**
 * X API v2 wrapper — search, threads, profiles, single tweets.
 * Bearer token from: X_BEARER_TOKEN env var or ~/.config/env/global.env
 *
 * Pricing (Feb 2026 pay-per-use):
 *   Post read:   $0.005
 *   User lookup:  $0.010
 *   Post create:  $0.010
 */

import { readFileSync } from "fs";
import { createHmac, randomBytes } from "crypto";

const BASE = "https://api.x.com/2";
const RATE_DELAY_MS = 350;

function getToken(): string {
  if (process.env.X_BEARER_TOKEN) return process.env.X_BEARER_TOKEN;

  // Try global.env
  try {
    const envFile = readFileSync(
      `${process.env.HOME}/.config/env/global.env`,
      "utf-8"
    );
    const match = envFile.match(/X_BEARER_TOKEN=["']?([^"'\n]+)/);
    if (match) return match[1];
  } catch {}

  // Try skill-local .env
  try {
    const envFile = readFileSync(
      `${process.env.HOME}/.claude/skills/twitter/.env`,
      "utf-8"
    );
    const match = envFile.match(/X_BEARER_TOKEN=["']?([^"'\n]+)/);
    if (match) return match[1];
  } catch {}

  throw new Error(
    "X_BEARER_TOKEN not found. Set it via:\n" +
    "  1. export X_BEARER_TOKEN=... in shell\n" +
    "  2. ~/.config/env/global.env\n" +
    "  3. ~/.claude/skills/twitter/.env\n" +
    "Get a token at https://console.x.com"
  );
}

async function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export interface Tweet {
  id: string;
  text: string;
  author_id: string;
  username: string;
  name: string;
  created_at: string;
  conversation_id: string;
  metrics: {
    likes: number;
    retweets: number;
    replies: number;
    quotes: number;
    impressions: number;
    bookmarks: number;
  };
  urls: string[];
  mentions: string[];
  hashtags: string[];
  tweet_url: string;
}

interface RawResponse {
  data?: any[];
  includes?: { users?: any[] };
  meta?: { next_token?: string; result_count?: number };
  errors?: any[];
  title?: string;
  detail?: string;
  status?: number;
}

function parseTweets(raw: RawResponse): Tweet[] {
  if (!raw.data) return [];
  const users: Record<string, any> = {};
  for (const u of raw.includes?.users || []) {
    users[u.id] = u;
  }

  return raw.data.map((t: any) => {
    const u = users[t.author_id] || {};
    const m = t.public_metrics || {};
    return {
      id: t.id,
      text: t.text,
      author_id: t.author_id,
      username: u.username || "?",
      name: u.name || "?",
      created_at: t.created_at,
      conversation_id: t.conversation_id,
      metrics: {
        likes: m.like_count || 0,
        retweets: m.retweet_count || 0,
        replies: m.reply_count || 0,
        quotes: m.quote_count || 0,
        impressions: m.impression_count || 0,
        bookmarks: m.bookmark_count || 0,
      },
      urls: (t.entities?.urls || [])
        .map((u: any) => u.expanded_url)
        .filter(Boolean),
      mentions: (t.entities?.mentions || [])
        .map((m: any) => m.username)
        .filter(Boolean),
      hashtags: (t.entities?.hashtags || [])
        .map((h: any) => h.tag)
        .filter(Boolean),
      tweet_url: `https://x.com/${u.username || "?"}/status/${t.id}`,
    };
  });
}

const FIELDS =
  "tweet.fields=created_at,public_metrics,author_id,conversation_id,entities&expansions=author_id&user.fields=username,name,public_metrics";

function parseSince(since: string): string | null {
  const match = since.match(/^(\d+)(m|h|d)$/);
  if (match) {
    const num = parseInt(match[1]);
    const unit = match[2];
    const ms =
      unit === "m" ? num * 60_000 :
      unit === "h" ? num * 3_600_000 :
      num * 86_400_000;
    return new Date(Date.now() - ms).toISOString();
  }

  if (since.includes("T") || since.includes("-")) {
    try {
      return new Date(since).toISOString();
    } catch {
      return null;
    }
  }

  return null;
}

async function apiGet(url: string): Promise<RawResponse> {
  const token = getToken();
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (res.status === 429) {
    const reset = res.headers.get("x-rate-limit-reset");
    const waitSec = reset
      ? Math.max(parseInt(reset) - Math.floor(Date.now() / 1000), 1)
      : 60;
    throw new Error(`Rate limited. Resets in ${waitSec}s`);
  }

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`X API ${res.status}: ${body.slice(0, 200)}`);
  }

  return res.json();
}

// --- OAuth 1.0a for posting ---

interface OAuthCredentials {
  apiKey: string;
  apiSecret: string;
  accessToken: string;
  accessTokenSecret: string;
}

function getOAuthCredentials(): OAuthCredentials {
  const keys = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"];
  const vals: Record<string, string> = {};

  // Check env vars first
  for (const k of keys) {
    if (process.env[k]) vals[k] = process.env[k]!;
  }

  // Fall back to .env files if any missing
  if (Object.keys(vals).length < 4) {
    const envPaths = [
      `${process.env.HOME}/.config/env/global.env`,
      `${process.env.HOME}/.claude/skills/twitter/.env`,
    ];
    for (const path of envPaths) {
      try {
        const content = readFileSync(path, "utf-8");
        for (const k of keys) {
          if (!vals[k]) {
            const match = content.match(new RegExp(`${k}=["']?([^"'\\n]+)`));
            if (match && match[1].trim()) vals[k] = match[1].trim();
          }
        }
      } catch {}
    }
  }

  const missing = keys.filter((k) => !vals[k]);
  if (missing.length > 0) {
    throw new Error(
      `OAuth 1.0a credentials missing: ${missing.join(", ")}\n` +
      "Set them in ~/.claude/skills/twitter/.env or as env vars.\n" +
      "Generate at https://console.x.com → Project → Keys and tokens\n" +
      "(ensure Read and Write permissions are enabled)"
    );
  }

  return {
    apiKey: vals.X_API_KEY,
    apiSecret: vals.X_API_SECRET,
    accessToken: vals.X_ACCESS_TOKEN,
    accessTokenSecret: vals.X_ACCESS_TOKEN_SECRET,
  };
}

function percentEncode(str: string): string {
  return encodeURIComponent(str).replace(/[!'()*]/g, (c) =>
    "%" + c.charCodeAt(0).toString(16).toUpperCase()
  );
}

function oauthSign(
  method: string,
  url: string,
  params: Record<string, string>,
  creds: OAuthCredentials
): string {
  const oauthParams: Record<string, string> = {
    oauth_consumer_key: creds.apiKey,
    oauth_nonce: randomBytes(16).toString("hex"),
    oauth_signature_method: "HMAC-SHA1",
    oauth_timestamp: Math.floor(Date.now() / 1000).toString(),
    oauth_token: creds.accessToken,
    oauth_version: "1.0",
  };

  // Combine all params for signature base
  const allParams = { ...params, ...oauthParams };
  const paramStr = Object.keys(allParams)
    .sort()
    .map((k) => `${percentEncode(k)}=${percentEncode(allParams[k])}`)
    .join("&");

  const baseStr = `${method.toUpperCase()}&${percentEncode(url)}&${percentEncode(paramStr)}`;
  const signingKey = `${percentEncode(creds.apiSecret)}&${percentEncode(creds.accessTokenSecret)}`;
  const signature = createHmac("sha1", signingKey).update(baseStr).digest("base64");

  oauthParams.oauth_signature = signature;

  const header = Object.keys(oauthParams)
    .sort()
    .map((k) => `${percentEncode(k)}="${percentEncode(oauthParams[k])}"`)
    .join(", ");

  return `OAuth ${header}`;
}

async function apiPost(endpoint: string, body: Record<string, unknown>): Promise<any> {
  const creds = getOAuthCredentials();
  const url = `${BASE}${endpoint}`;
  const authHeader = oauthSign("POST", url, {}, creds);

  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: authHeader,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (res.status === 401) {
    throw new Error("OAuth 1.0a authentication failed. Check your credentials at console.x.com");
  }
  if (res.status === 403) {
    throw new Error("Forbidden — ensure your app has Read and Write permissions at console.x.com");
  }
  if (res.status === 429) {
    const reset = res.headers.get("x-rate-limit-reset");
    const waitSec = reset
      ? Math.max(parseInt(reset) - Math.floor(Date.now() / 1000), 1)
      : 60;
    throw new Error(`Rate limited. Resets in ${waitSec}s`);
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`X API POST ${res.status}: ${text.slice(0, 300)}`);
  }

  return res.json();
}

export async function postTweet(text: string): Promise<{ id: string; text: string }> {
  const result = await apiPost("/tweets", { text });
  return { id: result.data.id, text: result.data.text };
}

export async function replyToTweet(
  text: string,
  replyToId: string
): Promise<{ id: string; text: string }> {
  const result = await apiPost("/tweets", {
    text,
    reply: { in_reply_to_tweet_id: replyToId },
  });
  return { id: result.data.id, text: result.data.text };
}

export async function deleteTweet(tweetId: string): Promise<boolean> {
  const creds = getOAuthCredentials();
  const url = `${BASE}/tweets/${tweetId}`;
  const authHeader = oauthSign("DELETE", url, {}, creds);

  const res = await fetch(url, {
    method: "DELETE",
    headers: { Authorization: authHeader },
  });

  if (res.status === 401) {
    throw new Error("OAuth 1.0a authentication failed. Check your credentials at console.x.com");
  }
  if (res.status === 403) {
    throw new Error("Forbidden — ensure your app has Read and Write permissions at console.x.com");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`X API DELETE ${res.status}: ${text.slice(0, 300)}`);
  }

  const result = await res.json();
  return result.data?.deleted === true;
}

export async function search(
  query: string,
  opts: {
    maxResults?: number;
    pages?: number;
    sortOrder?: "relevancy" | "recency";
    since?: string;
  } = {}
): Promise<Tweet[]> {
  const maxResults = Math.max(Math.min(opts.maxResults || 100, 100), 10);
  const pages = opts.pages || 1;
  const sort = opts.sortOrder || "relevancy";
  const encoded = encodeURIComponent(query);

  let timeFilter = "";
  if (opts.since) {
    const startTime = parseSince(opts.since);
    if (startTime) {
      timeFilter = `&start_time=${startTime}`;
    }
  }

  let allTweets: Tweet[] = [];
  let nextToken: string | undefined;

  for (let page = 0; page < pages; page++) {
    const pagination = nextToken ? `&pagination_token=${nextToken}` : "";
    const url = `${BASE}/tweets/search/recent?query=${encoded}&max_results=${maxResults}&${FIELDS}&sort_order=${sort}${timeFilter}${pagination}`;

    const raw = await apiGet(url);
    const tweets = parseTweets(raw);
    allTweets.push(...tweets);

    nextToken = raw.meta?.next_token;
    if (!nextToken) break;
    if (page < pages - 1) await sleep(RATE_DELAY_MS);
  }

  return allTweets;
}

export async function thread(
  conversationId: string,
  opts: { pages?: number } = {}
): Promise<Tweet[]> {
  const query = `conversation_id:${conversationId}`;
  const tweets = await search(query, {
    pages: opts.pages || 2,
    sortOrder: "recency",
  });

  try {
    const rootUrl = `${BASE}/tweets/${conversationId}?${FIELDS}`;
    const raw = await apiGet(rootUrl);
    if (raw.data && !Array.isArray(raw.data)) {
      const rootTweets = parseTweets({ ...raw, data: [raw.data] });
      if (rootTweets.length > 0) {
        tweets.unshift(...rootTweets);
      }
    }
  } catch {}

  return tweets;
}

export async function profile(
  username: string,
  opts: { count?: number; includeReplies?: boolean } = {}
): Promise<{ user: any; tweets: Tweet[] }> {
  const userUrl = `${BASE}/users/by/username/${username}?user.fields=public_metrics,description,created_at`;
  const userData = await apiGet(userUrl);

  if (!userData.data) {
    throw new Error(`User @${username} not found`);
  }

  const user = (userData as any).data;
  await sleep(RATE_DELAY_MS);

  const replyFilter = opts.includeReplies ? "" : " -is:reply";
  const query = `from:${username} -is:retweet${replyFilter}`;
  const tweets = await search(query, {
    maxResults: Math.min(opts.count || 20, 100),
    sortOrder: "recency",
  });

  return { user, tweets };
}

export async function getTweet(tweetId: string): Promise<Tweet | null> {
  const url = `${BASE}/tweets/${tweetId}?${FIELDS}`;
  const raw = await apiGet(url);

  if (raw.data && !Array.isArray(raw.data)) {
    const parsed = parseTweets({ ...raw, data: [raw.data] });
    return parsed[0] || null;
  }
  return null;
}

export function sortBy(
  tweets: Tweet[],
  metric: "likes" | "impressions" | "retweets" | "replies" = "likes"
): Tweet[] {
  return [...tweets].sort((a, b) => b.metrics[metric] - a.metrics[metric]);
}

export function filterEngagement(
  tweets: Tweet[],
  opts: { minLikes?: number; minImpressions?: number }
): Tweet[] {
  return tweets.filter((t) => {
    if (opts.minLikes && t.metrics.likes < opts.minLikes) return false;
    if (opts.minImpressions && t.metrics.impressions < opts.minImpressions)
      return false;
    return true;
  });
}

export function dedupe(tweets: Tweet[]): Tweet[] {
  const seen = new Set<string>();
  return tweets.filter((t) => {
    if (seen.has(t.id)) return false;
    seen.add(t.id);
    return true;
  });
}
