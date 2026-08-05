#!/usr/bin/env bun
/**
 * x-search — CLI for X/Twitter research via official API v2.
 *
 * Commands:
 *   search <query> [options]    Search recent tweets (last 7 days)
 *   multi <q1> <q2>... [opts]   Fan out query variants, merge + dedupe (see references/query-expansion.md)
 *   counts <query> [options]    Tweet volume histogram ($0.005/request — probe before reading)
 *   thread <tweet_id>           Fetch full conversation thread
 *   profile <username>          Recent tweets from a user (--count N, default 20)
 *   tweet <tweet_id>            Fetch a single tweet
 *   feed <group|users> [opts]   Daily feed from account groups
 *   feedgroup [subcommand]      Manage feed groups (list/show/create/add/remove/delete/alias)
 *   watchlist                   Show watchlist
 *   watchlist add <user> [note] Add user to watchlist
 *   watchlist remove <user>     Remove user from watchlist
 *   watchlist check             Check recent tweets from all watchlist accounts
 *   cache clear                 Clear search cache
 *   usage                       Billed post consumption per day
 *   post <text>                 Post a tweet (OAuth 1.0a; --allow-url for URL posts)
 *   reply <tweet_id> <text>     Reply to a tweet (OAuth 1.0a; --allow-url for URL posts)
 *
 * Search options:
 *   --sort likes|impressions|retweets|recent   Sort order (default: likes)
 *   --min-likes N              Filter by minimum likes
 *   --min-impressions N        Filter by minimum impressions
 *   --pages N                  Number of pages to fetch (default: 1, max 5)
 *   --no-replies               Exclude replies
 *   --retweets                 Include retweets (excluded by default)
 *   --limit N                  Max results to display (default: 15)
 *   --quick                    Quick mode: 1 page, noise filter, 1hr cache
 *   --today                    Only since local midnight (sugar for --since today)
 *   --since <spec>             Nm|Nh|Nd (e.g. 15m, 3h, 7d), today, yesterday, or ISO date
 *   --until <spec>             Upper bound (end_time); same specs as --since
 *   --from <username>          Shorthand for from:username in query
 *   --quality                  Pre-filter low-engagement (min 10 likes)
 *   --bird                     Free session-based search via bird CLI (no API cost)
 *   --dry-run                  Print final query + window + est. cost, no API call
 *   --save                     Save results to ~/tools/smaug/knowledge/research/
 *   --json                     Output raw JSON
 *   --markdown                 Output as markdown research doc
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";
import * as api from "./lib/api";
import * as cache from "./lib/cache";
import * as fmt from "./lib/format";

const SKILL_DIR = import.meta.dir;
const WATCHLIST_PATH = join(SKILL_DIR, "data", "watchlist.json");
const FEEDGROUPS_PATH = join(SKILL_DIR, "data", "feedgroups.json");
const RESEARCH_DIR = join(process.env.HOME!, "tools", "smaug", "knowledge", "research");

// --- Arg parsing ---

const args = process.argv.slice(2);
const command = args[0];

function getFlag(name: string): boolean {
  const idx = args.indexOf(`--${name}`);
  if (idx >= 0) {
    args.splice(idx, 1);
    return true;
  }
  return false;
}

function getOpt(name: string): string | undefined {
  const idx = args.indexOf(`--${name}`);
  if (idx >= 0 && idx + 1 < args.length) {
    const val = args[idx + 1];
    args.splice(idx, 2);
    return val;
  }
  return undefined;
}

// Call after a command has consumed all its flags. Anything still --prefixed
// is a typo — without this, `--sicne 1d` silently leaks "1d" into the query.
function rejectUnknownFlags() {
  const unknown = args.filter((a) => a.startsWith("--"));
  if (unknown.length > 0) {
    console.error(`Unknown flag${unknown.length > 1 ? "s" : ""}: ${unknown.join(", ")}`);
    process.exit(1);
  }
}

// --- Shared search machinery (used by search + multi) ---

interface SearchOpts {
  quick: boolean;
  quality: boolean;
  fromUser?: string;
  sortOpt: string;
  minLikes: number;
  minImpressions: number;
  pages: number;
  limit: number;
  since?: string;
  until?: string;
  noReplies: boolean;
  includeRetweets: boolean;
  save: boolean;
  asJson: boolean;
  asMarkdown: boolean;
  useBird: boolean;
  dryRun: boolean;
}

function parseSearchOpts(): SearchOpts {
  const quick = getFlag("quick");
  const quality = getFlag("quality");
  const fromUser = getOpt("from");
  const sortOpt = getOpt("sort") || "likes";
  const minLikes = parseInt(getOpt("min-likes") || "0");
  const minImpressions = parseInt(getOpt("min-impressions") || "0");
  let pages = Math.min(parseInt(getOpt("pages") || "1"), 5);
  let limit = parseInt(getOpt("limit") || "15");
  let since = getOpt("since");
  if (getFlag("today")) since = "today";
  const until = getOpt("until");
  const noReplies = getFlag("no-replies");
  const includeRetweets = getFlag("retweets");
  if (getFlag("no-retweets")) {
    console.error("Note: retweets are already excluded by default; use --retweets to include them.");
  }
  const save = getFlag("save");
  const asJson = getFlag("json");
  const asMarkdown = getFlag("markdown");
  const useBird = getFlag("bird");
  const dryRun = getFlag("dry-run");

  if (quick) {
    pages = 1;
    limit = Math.min(limit, 10);
  }

  return {
    quick, quality, fromUser, sortOpt, minLikes, minImpressions, pages, limit,
    since, until, noReplies, includeRetweets, save, asJson, asMarkdown, useBird, dryRun,
  };
}

// API v2 and bird (web/GraphQL) use different operator dialects.
function buildSearchQuery(raw: string, o: SearchOpts, dialect: "api" | "bird" = "api"): string {
  let query = raw;
  const rtOp = dialect === "bird" ? "-filter:retweets" : "-is:retweet";
  const replyOp = dialect === "bird" ? "-filter:replies" : "-is:reply";

  if (o.fromUser && !query.toLowerCase().includes("from:")) {
    query += ` from:${o.fromUser.replace(/^@/, "")}`;
  }
  if (!o.includeRetweets && !query.includes(rtOp.slice(1))) {
    query += ` ${rtOp}`;
  }
  if ((o.quick || o.noReplies) && !query.includes(replyOp.slice(1))) {
    query += ` ${replyOp}`;
  }
  return query;
}

async function runRecentSearch(
  query: string,
  o: SearchOpts
): Promise<{ tweets: api.Tweet[]; cached: boolean }> {
  const cacheTtlMs = o.quick ? 3_600_000 : 900_000;
  const cacheParams = `sort=${o.sortOpt}&pages=${o.pages}&since=${o.since || "7d"}&until=${o.until || ""}`;
  const cached = cache.get(query, cacheParams, cacheTtlMs);
  if (cached) return { tweets: cached, cached: true };

  const tweets = await api.search(query, {
    pages: o.pages,
    sortOrder: o.sortOpt === "recent" ? "recency" : "relevancy",
    since: o.since || undefined,
    until: o.until || undefined,
  });
  cache.set(query, cacheParams, tweets);
  return { tweets, cached: false };
}

// bird's GraphQL search date-filters only via native operators (day granularity).
// until:D excludes day D itself, so name the day AFTER the bound and let
// searchBird's client-side trim enforce the precise timestamp.
function birdDateOperators(o: SearchOpts): string {
  const { startTime, endTime } = api.parseWindow(o.since, o.until);
  let ops = "";
  if (startTime) ops += ` since:${startTime.split("T")[0]}`;
  if (endTime) {
    const dayAfter = new Date(new Date(endTime).getTime() + 86_400_000);
    ops += ` until:${dayAfter.toISOString().split("T")[0]}`;
  }
  return ops;
}

async function searchBird(rawQuery: string, o: SearchOpts): Promise<api.Tweet[]> {
  const query = buildSearchQuery(rawQuery, o, "bird") + birdDateOperators(o);
  const proc = Bun.spawn(
    ["bird", "--cookie-source", "chrome", "search", query, "-n", String(Math.max(o.limit * 3, 20)), "--json", "--plain"],
    { stdout: "pipe", stderr: "pipe" }
  );
  const output = await new Response(proc.stdout).text();
  await proc.exited;

  const parsed = JSON.parse(output);
  const rawTweets = parsed.tweets || parsed || [];
  let tweets: api.Tweet[] = rawTweets.map((t: any) => mapBirdTweet(t));

  // since:/until: are day-granular; trim to the exact window client-side.
  if (o.since) {
    const cutoff = Date.now() - parseSinceToMs(o.since);
    tweets = tweets.filter((t) => new Date(t.created_at).getTime() > cutoff);
  }
  if (o.until) {
    const { endTime } = api.parseWindow(undefined, o.until);
    if (endTime) {
      const endCutoff = new Date(endTime).getTime();
      tweets = tweets.filter((t) => new Date(t.created_at).getTime() < endCutoff);
    }
  }
  return tweets;
}

// --- Watchlist ---

interface Watchlist {
  accounts: { username: string; note?: string; addedAt: string }[];
}

function loadWatchlist(): Watchlist {
  if (!existsSync(WATCHLIST_PATH)) return { accounts: [] };
  return JSON.parse(readFileSync(WATCHLIST_PATH, "utf-8"));
}

function saveWatchlist(wl: Watchlist) {
  writeFileSync(WATCHLIST_PATH, JSON.stringify(wl, null, 2));
}

// --- Feed Groups ---

interface FeedAccount {
  username: string;
  label?: string;
}

interface FeedGroup {
  accounts: FeedAccount[];
  description?: string;
}

interface FeedGroups {
  groups: Record<string, FeedGroup>;
  aliases: Record<string, string[]>;
}

function loadFeedGroups(): FeedGroups {
  if (!existsSync(FEEDGROUPS_PATH)) return { groups: {}, aliases: {} };
  return JSON.parse(readFileSync(FEEDGROUPS_PATH, "utf-8"));
}

function saveFeedGroups(fg: FeedGroups) {
  writeFileSync(FEEDGROUPS_PATH, JSON.stringify(fg, null, 2));
}

function resolveFeedAccounts(fg: FeedGroups, target: string): FeedAccount[] {
  // 1. Check aliases
  if (fg.aliases[target]) {
    const seen = new Set<string>();
    const accounts: FeedAccount[] = [];
    for (const name of fg.aliases[target]) {
      if (!fg.groups[name]) {
        console.error(`  Warning: alias "${target}" references nonexistent group "${name}"`);
        continue;
      }
      for (const acct of fg.groups[name].accounts) {
        const key = acct.username.toLowerCase();
        if (!seen.has(key)) {
          seen.add(key);
          accounts.push(acct);
        }
      }
    }
    return accounts;
  }

  // 2. Check group names
  if (fg.groups[target]) {
    return fg.groups[target].accounts;
  }

  // 3. Comma-separated usernames
  return target.split(",").map((u) => ({
    username: u.replace(/^@/, "").trim(),
  }));
}

function batchAccountsForQuery(accounts: FeedAccount[]): FeedAccount[][] {
  const batches: FeedAccount[][] = [];
  let current: FeedAccount[] = [];
  let currentLen = 0;
  const overhead = "() -is:retweet -is:reply".length;

  for (const acct of accounts) {
    const clause = `from:${acct.username}`;
    const addLen = current.length === 0 ? clause.length : " OR ".length + clause.length;

    if (currentLen + addLen + overhead > 480 && current.length > 0) {
      batches.push(current);
      current = [acct];
      currentLen = clause.length;
    } else {
      current.push(acct);
      currentLen += addLen;
    }
  }

  if (current.length > 0) batches.push(current);
  return batches;
}

function parseSinceToMs(since: string): number {
  const now = new Date();
  if (since === "today") {
    return now.getTime() - new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  }
  if (since === "yesterday") {
    return now.getTime() - new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1).getTime();
  }
  const match = since.match(/^(\d+)(m|h|d)$/);
  if (!match) return 86_400_000; // default 1 day
  const num = parseInt(match[1]);
  const unit = match[2];
  if (unit === "m") return num * 60_000;
  if (unit === "h") return num * 3_600_000;
  return num * 86_400_000;
}

// bird's user-tweets and search endpoints emit different shapes
// (username/likes/created_at vs author.username/likeCount/createdAt) — cover both.
function mapBirdTweet(t: any, fallbackUsername = ""): api.Tweet {
  const username = t.username || t.user?.username || t.author?.username || fallbackUsername;
  const id = t.id || t.tweetId || "";
  return {
    id,
    text: t.text || t.content || "",
    author_id: t.author_id || t.authorId || "",
    username,
    name: t.name || t.user?.name || t.author?.name || username,
    created_at: t.created_at || t.createdAt || t.date || "",
    conversation_id: t.conversation_id || t.conversationId || t.id || "",
    metrics: {
      likes: t.metrics?.likes || t.likes || t.likeCount || t.favorite_count || 0,
      retweets: t.metrics?.retweets || t.retweets || t.retweetCount || t.retweet_count || 0,
      replies: t.metrics?.replies || t.replies || t.replyCount || t.reply_count || 0,
      quotes: t.metrics?.quotes || t.quotes || t.quoteCount || 0,
      impressions: t.metrics?.impressions || t.impressions || t.viewCount || 0,
      bookmarks: t.metrics?.bookmarks || t.bookmarks || t.bookmarkCount || 0,
    },
    urls: t.urls || [],
    mentions: t.mentions || [],
    hashtags: t.hashtags || [],
    tweet_url: t.tweet_url || `https://x.com/${username}/status/${id}`,
  };
}

async function fetchFeedApi(
  accounts: FeedAccount[],
  since: string,
  limit: number,
  noCache: boolean
): Promise<Map<string, { label?: string; tweets: api.Tweet[] }>> {
  const result = new Map<string, { label?: string; tweets: api.Tweet[] }>();

  for (const acct of accounts) {
    result.set(acct.username.toLowerCase(), { label: acct.label, tweets: [] });
  }

  const batches = batchAccountsForQuery(accounts);
  const allTweets: api.Tweet[] = [];

  for (let i = 0; i < batches.length; i++) {
    const batch = batches[i];
    const fromClauses = batch.map((a) => `from:${a.username}`).join(" OR ");
    const query = `(${fromClauses}) -is:retweet -is:reply`;
    const cacheParams = `feed&since=${since}`;

    let tweets: api.Tweet[] | null = null;

    if (!noCache) {
      tweets = cache.get(query, cacheParams, 900_000);
    }

    if (tweets) {
      console.error(`  (cached: ${batch.length} accounts)`);
    } else {
      console.error(`  Fetching batch ${i + 1}/${batches.length} (${batch.length} accounts)...`);
      tweets = await api.search(query, {
        maxResults: 100,
        sortOrder: "recency",
        since,
      });
      cache.set(query, cacheParams, tweets);
    }

    allTweets.push(...tweets);

    if (i < batches.length - 1) {
      await new Promise((r) => setTimeout(r, 400));
    }
  }

  for (const tweet of allTweets) {
    const key = tweet.username.toLowerCase();
    const entry = result.get(key);
    if (entry) {
      entry.tweets.push(tweet);
    }
  }

  for (const [, data] of result) {
    data.tweets.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    data.tweets = data.tweets.slice(0, limit);
  }

  return result;
}

async function fetchFeedBird(
  accounts: FeedAccount[],
  since: string,
  limit: number
): Promise<Map<string, { label?: string; tweets: api.Tweet[] }>> {
  const result = new Map<string, { label?: string; tweets: api.Tweet[] }>();
  const cutoff = Date.now() - parseSinceToMs(since);

  for (const acct of accounts) {
    console.error(`  bird: @${acct.username}...`);
    try {
      const proc = Bun.spawn(
        ["bird", "--cookie-source", "chrome", "user-tweets", acct.username, "-n", String(limit * 3), "--json", "--plain"],
        { stdout: "pipe", stderr: "pipe" }
      );
      const output = await new Response(proc.stdout).text();
      await proc.exited;

      const parsed = JSON.parse(output);
      const rawTweets = parsed.tweets || parsed || [];
      const tweets: api.Tweet[] = rawTweets
        .filter((t: any) => {
          const ts = new Date(t.created_at || t.createdAt || t.date).getTime();
          return ts > cutoff;
        })
        .slice(0, limit)
        .map((t: any) => mapBirdTweet(t, acct.username));

      result.set(acct.username.toLowerCase(), { label: acct.label, tweets });
    } catch (e: any) {
      console.error(`  Error: @${acct.username}: ${e.message}`);
      result.set(acct.username.toLowerCase(), { label: acct.label, tweets: [] });
    }

    // Rate limit courtesy between bird requests
    if (accounts.indexOf(acct) < accounts.length - 1) {
      await new Promise((r) => setTimeout(r, 300));
    }
  }

  return result;
}

// --- Commands ---

async function cmdSearch() {
  const o = parseSearchOpts();
  rejectUnknownFlags();

  const raw = args.slice(1).join(" ");
  if (!raw) {
    console.error("Usage: x-search search <query> [options]");
    process.exit(1);
  }

  const dialect = o.useBird ? "bird" : "api";
  const query = buildSearchQuery(raw, o, dialect);

  if (o.dryRun) {
    const { startTime, endTime } = api.parseWindow(o.since, o.until);
    console.log(`[dry-run] query: ${query}${o.useBird ? birdDateOperators(o) : ""}`);
    if (startTime) console.log(`[dry-run] start_time: ${startTime}`);
    if (endTime) console.log(`[dry-run] end_time: ${endTime}`);
    console.log(`[dry-run] pages: ${o.pages} · sort: ${o.sortOpt}`);
    console.log(
      `[dry-run] est. cost: ${o.useBird ? "$0.00 (bird)" : `up to ~$${(o.pages * 100 * 0.005).toFixed(2)}`}`
    );
    return;
  }

  let tweets: api.Tweet[];
  if (o.useBird) {
    tweets = await searchBird(raw, o);
  } else {
    const res = await runRecentSearch(query, o);
    tweets = res.tweets;
    if (res.cached) console.error(`(cached — ${tweets.length} tweets)`);
  }

  const rawTweetCount = tweets.length;

  if (o.minLikes > 0 || o.minImpressions > 0) {
    tweets = api.filterEngagement(tweets, {
      minLikes: o.minLikes || undefined,
      minImpressions: o.minImpressions || undefined,
    });
  }

  if (o.quality) {
    tweets = api.filterEngagement(tweets, { minLikes: 10 });
  }

  if (o.sortOpt !== "recent") {
    tweets = api.sortBy(tweets, o.sortOpt as "likes" | "impressions" | "retweets");
  }

  tweets = api.dedupe(tweets);

  if (o.asJson) {
    console.log(JSON.stringify(tweets.slice(0, o.limit), null, 2));
  } else if (o.asMarkdown) {
    console.log(fmt.formatResearchMarkdown(query, tweets, { queries: [query] }));
  } else {
    console.log(fmt.formatResultsTelegram(tweets, { query, limit: o.limit }));
  }

  if (o.save) {
    saveResearch(query, tweets, [query]);
  }

  const cost = o.useBird ? "0.00 (bird)" : (rawTweetCount * 0.005).toFixed(2);
  if (o.quick) {
    console.error(`\nquick mode · ${rawTweetCount} tweets read (~$${cost})`);
  } else {
    console.error(`\n${rawTweetCount} tweets read · est. cost ~$${cost}`);
  }

  const filtered = rawTweetCount !== tweets.length ? ` -> ${tweets.length} after filters` : "";
  const sinceLabel = o.since ? ` | since ${o.since}` : "";
  const untilLabel = o.until ? ` | until ${o.until}` : "";
  console.error(
    `${rawTweetCount} tweets${filtered} | sorted by ${o.sortOpt} | ${o.pages} page(s)${sinceLabel}${untilLabel}`
  );
}

function saveResearch(title: string, tweets: api.Tweet[], queries: string[]) {
  if (!existsSync(RESEARCH_DIR)) mkdirSync(RESEARCH_DIR, { recursive: true });
  const slug = title
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40)
    .toLowerCase();
  const date = new Date().toISOString().split("T")[0];
  const path = join(RESEARCH_DIR, `x-research-${slug}-${date}.md`);
  writeFileSync(path, fmt.formatResearchMarkdown(title, tweets, { queries }));
  console.error(`\nSaved to ${path}`);
}

async function cmdMulti() {
  const o = parseSearchOpts();
  rejectUnknownFlags();

  const rawQueries = args.slice(1);
  if (rawQueries.length < 2) {
    console.error('Usage: x-search multi "<query1>" "<query2>" [...] [search options]');
    console.error("Fan out expanded query variants, merge + dedupe (see references/query-expansion.md).");
    process.exit(1);
  }

  const dialect = o.useBird ? "bird" : "api";
  const finalQueries = rawQueries.map((q) => buildSearchQuery(q, o, dialect));

  if (o.dryRun) {
    const { startTime, endTime } = api.parseWindow(o.since, o.until);
    finalQueries.forEach((q, i) =>
      console.log(`[dry-run] q${i + 1}: ${q}${o.useBird ? birdDateOperators(o) : ""}`)
    );
    if (startTime) console.log(`[dry-run] start_time: ${startTime}`);
    if (endTime) console.log(`[dry-run] end_time: ${endTime}`);
    console.log(
      `[dry-run] est. cost: ${o.useBird ? "$0.00 (bird)" : `up to ~$${(finalQueries.length * o.pages * 100 * 0.005).toFixed(2)}`}`
    );
    return;
  }

  const seen = new Set<string>();
  const merged: api.Tweet[] = [];
  const perVariant: { count: number; fresh: number; cached: boolean; error?: string }[] = [];
  let billedReads = 0;

  for (let i = 0; i < finalQueries.length; i++) {
    try {
      let tweets: api.Tweet[];
      let cached = false;
      if (o.useBird) {
        tweets = await searchBird(rawQueries[i], o);
      } else {
        const res = await runRecentSearch(finalQueries[i], o);
        tweets = res.tweets;
        cached = res.cached;
        if (!cached) billedReads += tweets.length;
      }
      let fresh = 0;
      for (const t of tweets) {
        if (!seen.has(t.id)) {
          seen.add(t.id);
          merged.push(t);
          fresh++;
        }
      }
      perVariant.push({ count: tweets.length, fresh, cached });
    } catch (e: any) {
      // Fail-soft: a bad variant shouldn't sink the run.
      console.error(`  q${i + 1} failed: ${e.message}`);
      perVariant.push({ count: 0, fresh: 0, cached: false, error: e.message });
    }
    if (i < finalQueries.length - 1) {
      await new Promise((r) => setTimeout(r, 400));
    }
  }

  let tweets = merged;
  if (o.minLikes > 0 || o.minImpressions > 0) {
    tweets = api.filterEngagement(tweets, {
      minLikes: o.minLikes || undefined,
      minImpressions: o.minImpressions || undefined,
    });
  }
  if (o.quality) {
    tweets = api.filterEngagement(tweets, { minLikes: 10 });
  }
  if (o.sortOpt !== "recent") {
    tweets = api.sortBy(tweets, o.sortOpt as "likes" | "impressions" | "retweets");
  }

  if (o.asJson) {
    console.log(JSON.stringify(tweets.slice(0, o.limit), null, 2));
  } else if (o.asMarkdown) {
    console.log(fmt.formatResearchMarkdown(rawQueries[0], tweets, { queries: finalQueries }));
  } else {
    console.log(
      fmt.formatResultsTelegram(tweets, { query: `${rawQueries.length} variants`, limit: o.limit })
    );
  }

  if (o.save) {
    saveResearch(rawQueries[0], tweets, finalQueries);
  }

  console.error("");
  perVariant.forEach((v, i) => {
    const status = v.error
      ? `error — ${v.error}`
      : `${v.count} tweets (${v.fresh} new)${v.cached ? " · cached" : ""}`;
    console.error(`  q${i + 1}: ${status}`);
  });
  const cost = o.useBird ? "0.00 (bird)" : (billedReads * 0.005).toFixed(2);
  console.error(
    `${merged.length} unique tweets from ${rawQueries.length} variants · est. cost ~$${cost}`
  );
}

async function cmdCounts() {
  const granularity = (getOpt("granularity") || "hour") as "minute" | "hour" | "day";
  let since = getOpt("since");
  if (getFlag("today")) since = "today";
  const until = getOpt("until");
  const asJson = getFlag("json");
  const dryRun = getFlag("dry-run");
  rejectUnknownFlags();

  const query = args.slice(1).join(" ");
  if (!query) {
    console.error("Usage: x-search counts <query> [--granularity minute|hour|day] [--today|--since|--until] [--json]");
    process.exit(1);
  }

  if (dryRun) {
    const { startTime, endTime } = api.parseWindow(since, until);
    console.log(`[dry-run] counts query: ${query} · granularity: ${granularity}`);
    if (startTime) console.log(`[dry-run] start_time: ${startTime}`);
    if (endTime) console.log(`[dry-run] end_time: ${endTime}`);
    console.log(`[dry-run] est. cost: $0.005 (1 request)`);
    return;
  }

  const { buckets, total } = await api.counts(query, {
    granularity,
    since: since || undefined,
    until: until || undefined,
  });

  if (asJson) {
    console.log(JSON.stringify({ query, granularity, total, buckets }, null, 2));
  } else {
    console.log(fmt.formatCounts(query, buckets, total, { granularity }));
  }

  console.error(
    `1 counts request · $0.005 — reading all ${total.toLocaleString()} tweets would cost ~$${(total * 0.005).toFixed(2)}`
  );
}

async function cmdThread() {
  const tweetId = args[1];
  if (!tweetId) {
    console.error("Usage: x-search thread <tweet_id>");
    process.exit(1);
  }

  const pages = Math.min(parseInt(getOpt("pages") || "2"), 5);
  rejectUnknownFlags();
  const tweets = await api.thread(tweetId, { pages });

  if (tweets.length === 0) {
    console.log("No tweets found in thread.");
    return;
  }

  console.log(`Thread (${tweets.length} tweets)\n`);
  for (const t of tweets) {
    console.log(fmt.formatTweetTelegram(t, undefined, { full: true }));
    console.log();
  }

  console.error(`${tweets.length} tweets read · est. cost ~$${(tweets.length * 0.005).toFixed(2)}`);
}

async function cmdProfile() {
  const username = args[1]?.replace(/^@/, "");
  if (!username) {
    console.error("Usage: x-search profile <username>");
    process.exit(1);
  }

  const count = parseInt(getOpt("count") || "20");
  const includeReplies = getFlag("replies");
  const asJson = getFlag("json");
  let since = getOpt("since");
  if (getFlag("today")) since = "today";
  rejectUnknownFlags();

  const { user, tweets } = await api.profile(username, { count, includeReplies, since });

  if (asJson) {
    console.log(JSON.stringify({ user, tweets }, null, 2));
  } else {
    console.log(fmt.formatProfileTelegram(user, tweets));
  }

  console.error(
    `\n1 user lookup + ${tweets.length} tweets read · est. cost ~$${(0.01 + tweets.length * 0.005).toFixed(2)}`
  );
}

async function cmdTweet() {
  const tweetId = args[1];
  if (!tweetId) {
    console.error("Usage: x-search tweet <tweet_id>");
    process.exit(1);
  }

  const asJson = getFlag("json");
  rejectUnknownFlags();

  const tweet = await api.getTweet(tweetId);
  if (!tweet) {
    console.log("Tweet not found.");
    return;
  }
  if (asJson) {
    console.log(JSON.stringify(tweet, null, 2));
  } else {
    console.log(fmt.formatTweetTelegram(tweet, undefined, { full: true }));
  }
}

async function cmdWatchlist() {
  const sub = args[1];
  const wl = loadWatchlist();

  if (sub === "add") {
    const username = args[2]?.replace(/^@/, "");
    const note = args.slice(3).join(" ") || undefined;
    if (!username) {
      console.error("Usage: x-search watchlist add <username> [note]");
      process.exit(1);
    }
    if (wl.accounts.find((a) => a.username.toLowerCase() === username.toLowerCase())) {
      console.log(`@${username} already on watchlist.`);
      return;
    }
    wl.accounts.push({ username, note, addedAt: new Date().toISOString() });
    saveWatchlist(wl);
    console.log(`Added @${username} to watchlist.${note ? ` (${note})` : ""}`);
    return;
  }

  if (sub === "remove" || sub === "rm") {
    const username = args[2]?.replace(/^@/, "");
    if (!username) {
      console.error("Usage: x-search watchlist remove <username>");
      process.exit(1);
    }
    const before = wl.accounts.length;
    wl.accounts = wl.accounts.filter(
      (a) => a.username.toLowerCase() !== username.toLowerCase()
    );
    saveWatchlist(wl);
    console.log(
      wl.accounts.length < before
        ? `Removed @${username} from watchlist.`
        : `@${username} not found on watchlist.`
    );
    return;
  }

  if (sub === "check") {
    let since = getOpt("since");
    if (getFlag("today")) since = "today";
    rejectUnknownFlags();
    if (wl.accounts.length === 0) {
      console.log("Watchlist empty. Add accounts with: watchlist add <username>");
      return;
    }
    console.log(`Checking ${wl.accounts.length} watchlist accounts...\n`);
    let lookups = 0;
    let reads = 0;
    for (const acct of wl.accounts) {
      try {
        const { user, tweets } = await api.profile(acct.username, { count: 5, since });
        lookups++;
        reads += tweets.length;
        const label = acct.note ? ` (${acct.note})` : "";
        console.log(`\n--- @${acct.username}${label} ---`);
        if (tweets.length === 0) {
          console.log("  No recent tweets.");
        } else {
          for (const t of tweets.slice(0, 3)) {
            console.log(fmt.formatTweetTelegram(t));
            console.log();
          }
        }
      } catch (e: any) {
        console.error(`  Error checking @${acct.username}: ${e.message}`);
      }
    }
    console.error(
      `\n${lookups} user lookups + ${reads} tweets read · est. cost ~$${(lookups * 0.01 + reads * 0.005).toFixed(2)}`
    );
    return;
  }

  if (wl.accounts.length === 0) {
    console.log("Watchlist empty. Add accounts with: watchlist add <username>");
    return;
  }
  console.log(`Watchlist (${wl.accounts.length} accounts)\n`);
  for (const acct of wl.accounts) {
    const note = acct.note ? ` — ${acct.note}` : "";
    console.log(`  @${acct.username}${note} (added ${acct.addedAt.split("T")[0]})`);
  }
}

async function cmdCache() {
  const sub = args[1];
  if (sub === "clear") {
    console.log(`Cleared ${cache.clear()} cached entries.`);
  } else {
    console.log(`Pruned ${cache.prune()} expired entries.`);
  }
}

// Posts containing a URL bill at $0.20 instead of $0.015 (April 2026 repricing).
// Refuse by default — agents post autonomously, and a warning alone doesn't protect spend.
// X's t.co shortener also wraps bare domains (example.com/page), so protocol-only
// detection under-matches; the common-TLD alternation errs toward over-blocking,
// which is safe because --allow-url overrides.
const URL_PATTERN =
  /https?:\/\/|www\.|\b[a-z0-9][a-z0-9-]*\.(com|org|net|io|ai|dev|co|app|me|xyz|info|gg|tv|sh|so|to|us|uk|ca|de|fr|es|it|nl|jp|in|edu|gov|mil|biz|online|site|tech|store|blog|news|cloud|link)(\/|\b)/i;

function guardUrlSurcharge(text: string, allowUrl: boolean) {
  if (allowUrl) return;
  if (URL_PATTERN.test(text)) {
    console.error(
      "Refused: text contains a URL. X bills URL posts at $0.200 (vs $0.015 without).\n" +
        "Re-run with --allow-url to accept the surcharge."
    );
    process.exit(1);
  }
}

async function cmdPost() {
  const allowUrl = getFlag("allow-url");
  const dryRun = getFlag("dry-run");
  rejectUnknownFlags();
  const text = args.slice(1).join(" ");
  if (!text) {
    console.error("Usage: x-search post <text> [--allow-url] [--dry-run]");
    process.exit(1);
  }
  if (text.length > 280) {
    console.error(`Tweet too long: ${text.length}/280 chars`);
    process.exit(1);
  }
  guardUrlSurcharge(text, allowUrl);
  if (dryRun) {
    console.log(`[dry-run] Would post (${text.length}/280 chars): ${text}`);
    console.log(`[dry-run] Cost would be: ~$${allowUrl ? "0.20" : "0.015"}`);
    return;
  }
  const result = await api.postTweet(text);
  console.log(`Posted: https://x.com/i/status/${result.id}`);
  console.log(`Cost: ~$${allowUrl ? "0.20" : "0.015"}`);
}

async function cmdReply() {
  const allowUrl = getFlag("allow-url");
  const dryRun = getFlag("dry-run");
  rejectUnknownFlags();
  const tweetId = args[1];
  const text = args.slice(2).join(" ");
  if (!tweetId || !text) {
    console.error("Usage: x-search reply <tweet_id> <text> [--allow-url] [--dry-run]");
    process.exit(1);
  }
  if (text.length > 280) {
    console.error(`Reply too long: ${text.length}/280 chars`);
    process.exit(1);
  }
  guardUrlSurcharge(text, allowUrl);
  if (dryRun) {
    console.log(`[dry-run] Would reply to ${tweetId} (${text.length}/280 chars): ${text}`);
    console.log(`[dry-run] Cost would be: ~$${allowUrl ? "0.20" : "0.015"}`);
    return;
  }
  const result = await api.replyToTweet(text, tweetId);
  console.log(`Replied: https://x.com/i/status/${result.id}`);
  console.log(`Cost: ~$${allowUrl ? "0.20" : "0.015"}`);
}

async function cmdUsage() {
  const asJson = getFlag("json");
  rejectUnknownFlags();
  const raw = await api.getUsage();
  if (asJson) {
    console.log(JSON.stringify(raw, null, 2));
  } else {
    console.log(fmt.formatUsage(raw));
  }
}

async function cmdDelete() {
  rejectUnknownFlags();
  const tweetId = args[1];
  if (!tweetId) {
    console.error("Usage: x-search delete <tweet_id>");
    process.exit(1);
  }
  const deleted = await api.deleteTweet(tweetId);
  if (deleted) {
    console.log(`Deleted tweet ${tweetId}`);
  } else {
    console.error(`Failed to delete tweet ${tweetId}`);
  }
}

async function cmdFeed() {
  const target = args[1];
  if (!target) {
    console.error("Usage: x-search feed <group|alias|user1,user2,...> [options]");
    console.error("\nOptions:");
    console.error("  --since <spec>             Nm|Nh|Nd, today, yesterday (default: 1d)");
    console.error("  --today                    Sugar for --since today (local midnight)");
    console.error("  --limit N                  Tweets per account (default: 4)");
    console.error("  --markdown                 Markdown output");
    console.error("  --save                     Save to smaug/knowledge/research/");
    console.error("  --json                     Raw JSON");
    console.error("  --bird                     Free bird CLI fallback");
    console.error("  --dry-run                  Show batches + est. cost, no API call");
    console.error("  --no-cache                 Skip cache");
    process.exit(1);
  }

  let since = getOpt("since") || "1d";
  if (getFlag("today")) since = "today";
  const limit = parseInt(getOpt("limit") || "4");
  const asMarkdown = getFlag("markdown");
  const asJson = getFlag("json");
  const save = getFlag("save");
  const useBird = getFlag("bird");
  const noCache = getFlag("no-cache");
  const dryRun = getFlag("dry-run");
  rejectUnknownFlags();

  const feedgroups = loadFeedGroups();
  const accounts = resolveFeedAccounts(feedgroups, target);

  if (accounts.length === 0) {
    console.error(`No accounts found for "${target}". Use: x-search feedgroup`);
    process.exit(1);
  }

  if (dryRun) {
    const batches = batchAccountsForQuery(accounts);
    const { startTime, endTime } = api.parseWindow(since);
    console.log(`[dry-run] ${accounts.length} accounts in ${batches.length} batched quer${batches.length === 1 ? "y" : "ies"}`);
    batches.forEach((b, i) =>
      console.log(`[dry-run] batch ${i + 1}: (${b.map((a) => `from:${a.username}`).join(" OR ")}) -is:retweet -is:reply`)
    );
    if (startTime) console.log(`[dry-run] start_time: ${startTime}`);
    if (endTime) console.log(`[dry-run] end_time: ${endTime}`);
    console.log(
      `[dry-run] est. cost: ${useBird ? "$0.00 (bird)" : `up to ~$${(batches.length * 100 * 0.005).toFixed(2)}`}`
    );
    return;
  }

  console.error(`Fetching feed: ${accounts.length} accounts, since ${since}...\n`);

  let groupedTweets: Map<string, { label?: string; tweets: api.Tweet[] }>;

  if (useBird) {
    groupedTweets = await fetchFeedBird(accounts, since, limit);
  } else {
    groupedTweets = await fetchFeedApi(accounts, since, limit, noCache);
  }

  const windowLabel =
    since === "today" ? "today" :
    since === "yesterday" ? "yesterday" :
    since === "1d" ? "last 24h" :
    since === "7d" ? "last week" : `last ${since}`;
  const totalTweets = [...groupedTweets.values()].reduce((s, d) => s + d.tweets.length, 0);
  const costStr = useBird ? "0.00 (bird)" : (totalTweets * 0.005).toFixed(2);

  if (asJson) {
    const obj: Record<string, any> = {};
    for (const [u, data] of groupedTweets) {
      obj[u] = data;
    }
    console.log(JSON.stringify(obj, null, 2));
  } else if (asMarkdown) {
    console.log(
      fmt.formatFeedGroupMarkdown(groupedTweets, {
        groupName: target,
        window: windowLabel,
        cost: costStr,
      })
    );
  } else {
    console.log(fmt.formatFeedGroupTelegram(groupedTweets, { limit, window: windowLabel }));
  }

  if (useBird) {
    console.error(`\n${totalTweets} tweets from ${accounts.length} accounts (bird, free)`);
  } else {
    console.error(`\n${totalTweets} tweets from ${accounts.length} accounts \u00B7 est. cost ~$${costStr}`);
  }

  if (save) {
    if (!existsSync(RESEARCH_DIR)) mkdirSync(RESEARCH_DIR, { recursive: true });
    const date = new Date().toISOString().split("T")[0];
    const path = join(RESEARCH_DIR, `x-feed-${target}-${date}.md`);
    writeFileSync(
      path,
      fmt.formatFeedGroupMarkdown(groupedTweets, {
        groupName: target,
        window: windowLabel,
        cost: costStr,
      })
    );
    console.error(`Saved to ${path}`);
  }
}

async function cmdFeedGroup() {
  const sub = args[1];
  const fg = loadFeedGroups();

  if (sub === "show") {
    const name = args[2];
    if (!name) {
      console.error("Usage: x-search feedgroup show <name>");
      process.exit(1);
    }
    if (fg.aliases[name]) {
      console.log(`Alias "${name}" -> [${fg.aliases[name].join(", ")}]`);
      const accounts = resolveFeedAccounts(fg, name);
      console.log(`  ${accounts.length} accounts total`);
      for (const a of accounts) {
        const label = a.label ? ` \u2014 ${a.label}` : "";
        console.log(`    @${a.username}${label}`);
      }
      return;
    }
    const group = fg.groups[name];
    if (!group) {
      console.error(`Group "${name}" not found.`);
      process.exit(1);
    }
    console.log(`${name} (${group.accounts.length} accounts)`);
    if (group.description) console.log(`  ${group.description}`);
    for (const a of group.accounts) {
      const label = a.label ? ` \u2014 ${a.label}` : "";
      console.log(`  @${a.username}${label}`);
    }
    return;
  }

  if (sub === "create") {
    const name = args[2];
    if (!name) {
      console.error("Usage: x-search feedgroup create <name> [description]");
      process.exit(1);
    }
    if (fg.groups[name]) {
      console.log(`Group "${name}" already exists.`);
      return;
    }
    const desc = args.slice(3).join(" ") || undefined;
    fg.groups[name] = { accounts: [], description: desc };
    saveFeedGroups(fg);
    console.log(`Created group "${name}".${desc ? ` (${desc})` : ""}`);
    return;
  }

  if (sub === "add") {
    const groupName = args[2];
    const username = args[3]?.replace(/^@/, "");
    if (!groupName || !username) {
      console.error("Usage: x-search feedgroup add <group> <username> [label]");
      process.exit(1);
    }
    if (!fg.groups[groupName]) {
      console.error(`Group "${groupName}" not found. Create it first.`);
      process.exit(1);
    }
    if (fg.groups[groupName].accounts.find((a) => a.username.toLowerCase() === username.toLowerCase())) {
      console.log(`@${username} already in "${groupName}".`);
      return;
    }
    const label = args.slice(4).join(" ") || undefined;
    fg.groups[groupName].accounts.push({ username, label });
    saveFeedGroups(fg);
    console.log(`Added @${username} to "${groupName}".${label ? ` (${label})` : ""}`);
    return;
  }

  if (sub === "remove" || sub === "rm") {
    const groupName = args[2];
    const username = args[3]?.replace(/^@/, "");
    if (!groupName || !username) {
      console.error("Usage: x-search feedgroup remove <group> <username>");
      process.exit(1);
    }
    if (!fg.groups[groupName]) {
      console.error(`Group "${groupName}" not found.`);
      process.exit(1);
    }
    const before = fg.groups[groupName].accounts.length;
    fg.groups[groupName].accounts = fg.groups[groupName].accounts.filter(
      (a) => a.username.toLowerCase() !== username.toLowerCase()
    );
    saveFeedGroups(fg);
    console.log(
      fg.groups[groupName].accounts.length < before
        ? `Removed @${username} from "${groupName}".`
        : `@${username} not found in "${groupName}".`
    );
    return;
  }

  if (sub === "delete" || sub === "del") {
    const name = args[2];
    if (!name) {
      console.error("Usage: x-search feedgroup delete <name>");
      process.exit(1);
    }
    if (fg.groups[name]) {
      delete fg.groups[name];
      saveFeedGroups(fg);
      console.log(`Deleted group "${name}".`);
    } else if (fg.aliases[name]) {
      delete fg.aliases[name];
      saveFeedGroups(fg);
      console.log(`Deleted alias "${name}".`);
    } else {
      console.error(`"${name}" not found.`);
    }
    return;
  }

  if (sub === "alias") {
    const name = args[2];
    const groups = args[3];
    if (!name || !groups) {
      console.error("Usage: x-search feedgroup alias <name> <group1,group2,...>");
      process.exit(1);
    }
    const groupList = groups.split(",").map((g) => g.trim());
    const missing = groupList.filter((g) => !fg.groups[g]);
    if (missing.length > 0) {
      console.error(`Group(s) not found: ${missing.join(", ")}. Create them first.`);
      process.exit(1);
    }
    if (fg.aliases[name]) {
      console.error(`Updating alias "${name}" (was: [${fg.aliases[name].join(", ")}])`);
    }
    fg.aliases[name] = groupList;
    saveFeedGroups(fg);
    console.log(`Alias "${name}" -> [${fg.aliases[name].join(", ")}]`);
    return;
  }

  // Default: list all groups
  const groupNames = Object.keys(fg.groups);
  const aliasNames = Object.keys(fg.aliases);

  if (groupNames.length === 0 && aliasNames.length === 0) {
    console.log("No feed groups. Create one with: feedgroup create <name>");
    return;
  }

  console.log("Feed Groups\n");
  for (const name of groupNames) {
    const g = fg.groups[name];
    const desc = g.description ? ` \u2014 ${g.description}` : "";
    console.log(`  ${name} (${g.accounts.length} accounts)${desc}`);
    for (const a of g.accounts) {
      const label = a.label ? ` (${a.label})` : "";
      console.log(`    @${a.username}${label}`);
    }
    console.log();
  }

  if (aliasNames.length > 0) {
    console.log("Aliases\n");
    for (const name of aliasNames) {
      const resolved = resolveFeedAccounts(fg, name);
      console.log(`  ${name} -> [${fg.aliases[name].join(", ")}] (${resolved.length} accounts)`);
    }
  }
}

function usage() {
  console.log(`x-search — X/Twitter research CLI (official API v2)

Commands:
  search <query> [options]    Search recent tweets (last 7 days)
  multi <q1> <q2>... [opts]   Fan out query variants, merge + dedupe by tweet ID
  counts <query> [options]    Tweet volume histogram — probe before reading ($0.005)
  thread <tweet_id>           Fetch full conversation thread
  profile <username>          Recent tweets from a user (--count N, default 20)
  tweet <tweet_id>            Fetch a single tweet
  feed <group|users> [opts]   Daily feed from account groups
  feedgroup [subcommand]      Manage feed groups (list/show/create/add/remove/delete/alias)
  post <text>                 Post a tweet (requires OAuth 1.0a)
  reply <tweet_id> <text>     Reply to a tweet (requires OAuth 1.0a)
  watchlist                   Show watchlist
  watchlist add <user> [note] Add user to watchlist
  watchlist remove <user>     Remove user from watchlist
  watchlist check             Check recent from all watchlist accounts (--today/--since)
  usage                       Billed post consumption per day (--json for raw)
  delete <tweet_id>           Delete own tweet ($0.01)
  cache clear                 Clear search cache

Search options (also apply to multi):
  --sort likes|impressions|retweets|recent   (default: likes)
  --today                    Only since local midnight (sugar for --since today)
  --since <spec>             Nm|Nh|Nd (e.g. 15m, 3h, 7d), today, yesterday, or ISO date
  --until <spec>             Upper bound (end_time); same specs as --since
  --min-likes N              Filter minimum likes
  --min-impressions N        Filter minimum impressions
  --pages N                  Pages to fetch, 1-5 (default: 1)
  --limit N                  Results to display (default: 15)
  --quick                    Quick mode: 1 page, max 10, noise filter, 1hr cache
  --from <username>          Shorthand for from:username in query
  --quality                  Filter low-engagement tweets (min 10 likes)
  --no-replies               Exclude replies
  --retweets                 Include retweets (excluded by default)
  --bird                     Free session-based search via bird CLI ($0.00)
  --dry-run                  Show final query + window + est. cost, no API call
  --save                     Save to ~/tools/smaug/knowledge/research/
  --json                     Raw JSON output
  --markdown                 Markdown research doc

Counts options:
  --granularity minute|hour|day   Bucket size (default: hour)
  --today / --since / --until     Window (same specs as search)
  --json                          Raw JSON output

Feed options:
  --since <spec>             Nm|Nh|Nd, today, yesterday (default: 1d)
  --today                    Sugar for --since today
  --limit N                  Tweets per account (default: 4)
  --bird                     Free bird CLI fallback (no API cost)
  --markdown                 Markdown output
  --save                     Save to ~/tools/smaug/knowledge/research/
  --json                     Raw JSON output
  --no-cache                 Skip cache

Post options:
  --allow-url                Accept the $0.200 URL-post surcharge (refused otherwise)
  --dry-run                  Validate and show cost without posting

Cost: $0.005/post read, $0.01/user lookup, $0.015/post create,
      $0.20/post create with URL, $0.001/owned read (pay-per-use)`);
}

async function main() {
  // Drop cache entries past the longest TTL (1hr quick mode) so data/cache
  // doesn't accumulate dead files indefinitely.
  cache.prune(60 * 60 * 1000);

  switch (command) {
    case "search":
    case "s":
      await cmdSearch();
      break;
    case "multi":
    case "m":
      await cmdMulti();
      break;
    case "counts":
    case "c":
      await cmdCounts();
      break;
    case "thread":
    case "t":
      await cmdThread();
      break;
    case "profile":
    case "p":
      await cmdProfile();
      break;
    case "tweet":
      await cmdTweet();
      break;
    case "feed":
    case "f":
      await cmdFeed();
      break;
    case "feedgroup":
    case "fg":
      await cmdFeedGroup();
      break;
    case "watchlist":
    case "wl":
      await cmdWatchlist();
      break;
    case "cache":
      await cmdCache();
      break;
    case "post":
      await cmdPost();
      break;
    case "reply":
      await cmdReply();
      break;
    case "delete":
    case "rm":
      await cmdDelete();
      break;
    case "usage":
    case "u":
      await cmdUsage();
      break;
    default:
      usage();
  }
}

main().catch((e) => {
  console.error(`Error: ${e.message}`);
  process.exit(1);
});
