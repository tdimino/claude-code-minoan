#!/usr/bin/env bun
/**
 * x-search — CLI for X/Twitter research via official API v2.
 *
 * Commands:
 *   search <query> [options]    Search recent tweets (last 7 days)
 *   thread <tweet_id>           Fetch full conversation thread
 *   profile <username>          Recent tweets from a user
 *   tweet <tweet_id>            Fetch a single tweet
 *   feed <group|users> [opts]   Daily feed from account groups
 *   feedgroup [subcommand]      Manage feed groups (list/show/create/add/remove/delete/alias)
 *   watchlist                   Show watchlist
 *   watchlist add <user> [note] Add user to watchlist
 *   watchlist remove <user>     Remove user from watchlist
 *   watchlist check             Check recent tweets from all watchlist accounts
 *   cache clear                 Clear search cache
 *   post <text>                 Post a tweet (OAuth 1.0a)
 *   reply <tweet_id> <text>     Reply to a tweet (OAuth 1.0a)
 *
 * Search options:
 *   --sort likes|impressions|retweets|recent   Sort order (default: likes)
 *   --min-likes N              Filter by minimum likes
 *   --min-impressions N        Filter by minimum impressions
 *   --pages N                  Number of pages to fetch (default: 1, max 5)
 *   --no-replies               Exclude replies
 *   --no-retweets              Exclude retweets (added by default)
 *   --limit N                  Max results to display (default: 15)
 *   --quick                    Quick mode: 1 page, noise filter, 1hr cache
 *   --from <username>          Shorthand for from:username in query
 *   --quality                  Pre-filter low-engagement (min 10 likes)
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
  const match = since.match(/^(\d+)(m|h|d)$/);
  if (!match) return 86_400_000; // default 1 day
  const num = parseInt(match[1]);
  const unit = match[2];
  if (unit === "m") return num * 60_000;
  if (unit === "h") return num * 3_600_000;
  return num * 86_400_000;
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
        ["bird", "user-tweets", acct.username, "-n", String(limit * 3), "--json", "--plain"],
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
        .map((t: any) => ({
          id: t.id || t.tweetId || "",
          text: t.text || t.content || "",
          author_id: t.author_id || "",
          username: t.username || t.user?.username || acct.username,
          name: t.name || t.user?.name || acct.username,
          created_at: t.created_at || t.createdAt || t.date || "",
          conversation_id: t.conversation_id || t.id || "",
          metrics: {
            likes: t.metrics?.likes || t.likes || t.favorite_count || 0,
            retweets: t.metrics?.retweets || t.retweets || t.retweet_count || 0,
            replies: t.metrics?.replies || t.replies || t.reply_count || 0,
            quotes: t.metrics?.quotes || t.quotes || 0,
            impressions: t.metrics?.impressions || t.impressions || 0,
            bookmarks: t.metrics?.bookmarks || t.bookmarks || 0,
          },
          urls: t.urls || [],
          mentions: t.mentions || [],
          hashtags: t.hashtags || [],
          tweet_url: t.tweet_url || `https://x.com/${acct.username}/status/${t.id || t.tweetId}`,
        }));

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
  const quick = getFlag("quick");
  const quality = getFlag("quality");
  const fromUser = getOpt("from");

  const sortOpt = getOpt("sort") || "likes";
  const minLikes = parseInt(getOpt("min-likes") || "0");
  const minImpressions = parseInt(getOpt("min-impressions") || "0");
  let pages = Math.min(parseInt(getOpt("pages") || "1"), 5);
  let limit = parseInt(getOpt("limit") || "15");
  const since = getOpt("since");
  const noReplies = getFlag("no-replies");
  const noRetweets = getFlag("no-retweets");
  const save = getFlag("save");
  const asJson = getFlag("json");
  const asMarkdown = getFlag("markdown");

  if (quick) {
    pages = 1;
    limit = Math.min(limit, 10);
  }

  const queryParts = args.slice(1).filter((a) => !a.startsWith("--"));
  let query = queryParts.join(" ");

  if (!query) {
    console.error("Usage: x-search search <query> [options]");
    process.exit(1);
  }

  if (fromUser && !query.toLowerCase().includes("from:")) {
    query += ` from:${fromUser.replace(/^@/, "")}`;
  }

  if (!query.includes("is:retweet") && !noRetweets) {
    query += " -is:retweet";
  }
  if (quick && !query.includes("is:reply")) {
    query += " -is:reply";
  } else if (noReplies && !query.includes("is:reply")) {
    query += " -is:reply";
  }

  const cacheTtlMs = quick ? 3_600_000 : 900_000;
  const cacheParams = `sort=${sortOpt}&pages=${pages}&since=${since || "7d"}`;
  const cached = cache.get(query, cacheParams, cacheTtlMs);
  let tweets: api.Tweet[];

  if (cached) {
    tweets = cached;
    console.error(`(cached — ${tweets.length} tweets)`);
  } else {
    tweets = await api.search(query, {
      pages,
      sortOrder: sortOpt === "recent" ? "recency" : "relevancy",
      since: since || undefined,
    });
    cache.set(query, cacheParams, tweets);
  }

  const rawTweetCount = tweets.length;

  if (minLikes > 0 || minImpressions > 0) {
    tweets = api.filterEngagement(tweets, {
      minLikes: minLikes || undefined,
      minImpressions: minImpressions || undefined,
    });
  }

  if (quality) {
    tweets = api.filterEngagement(tweets, { minLikes: 10 });
  }

  if (sortOpt !== "recent") {
    tweets = api.sortBy(tweets, sortOpt as "likes" | "impressions" | "retweets");
  }

  tweets = api.dedupe(tweets);

  if (asJson) {
    console.log(JSON.stringify(tweets.slice(0, limit), null, 2));
  } else if (asMarkdown) {
    console.log(fmt.formatResearchMarkdown(query, tweets, { queries: [query] }));
  } else {
    console.log(fmt.formatResultsTelegram(tweets, { query, limit }));
  }

  if (save) {
    if (!existsSync(RESEARCH_DIR)) mkdirSync(RESEARCH_DIR, { recursive: true });
    const slug = query
      .replace(/[^a-zA-Z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 40)
      .toLowerCase();
    const date = new Date().toISOString().split("T")[0];
    const path = join(RESEARCH_DIR, `x-research-${slug}-${date}.md`);
    writeFileSync(path, fmt.formatResearchMarkdown(query, tweets, { queries: [query] }));
    console.error(`\nSaved to ${path}`);
  }

  const cost = (rawTweetCount * 0.005).toFixed(2);
  if (quick) {
    console.error(`\nquick mode · ${rawTweetCount} tweets read (~$${cost})`);
  } else {
    console.error(`\n${rawTweetCount} tweets read · est. cost ~$${cost}`);
  }

  const filtered = rawTweetCount !== tweets.length ? ` -> ${tweets.length} after filters` : "";
  const sinceLabel = since ? ` | since ${since}` : "";
  console.error(
    `${rawTweetCount} tweets${filtered} | sorted by ${sortOpt} | ${pages} page(s)${sinceLabel}`
  );
}

async function cmdThread() {
  const tweetId = args[1];
  if (!tweetId) {
    console.error("Usage: x-search thread <tweet_id>");
    process.exit(1);
  }

  const pages = Math.min(parseInt(getOpt("pages") || "2"), 5);
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

  const { user, tweets } = await api.profile(username, { count, includeReplies });

  if (asJson) {
    console.log(JSON.stringify({ user, tweets }, null, 2));
  } else {
    console.log(fmt.formatProfileTelegram(user, tweets));
  }
}

async function cmdTweet() {
  const tweetId = args[1];
  if (!tweetId) {
    console.error("Usage: x-search tweet <tweet_id>");
    process.exit(1);
  }

  const tweet = await api.getTweet(tweetId);
  if (!tweet) {
    console.log("Tweet not found.");
    return;
  }

  const asJson = getFlag("json");
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
    if (wl.accounts.length === 0) {
      console.log("Watchlist empty. Add accounts with: watchlist add <username>");
      return;
    }
    console.log(`Checking ${wl.accounts.length} watchlist accounts...\n`);
    for (const acct of wl.accounts) {
      try {
        const { user, tweets } = await api.profile(acct.username, { count: 5 });
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

async function cmdPost() {
  const text = args.slice(1).join(" ");
  if (!text) {
    console.error("Usage: x-search post <text>");
    process.exit(1);
  }
  if (text.length > 280) {
    console.error(`Tweet too long: ${text.length}/280 chars`);
    process.exit(1);
  }
  const result = await api.postTweet(text);
  console.log(`Posted: https://x.com/i/status/${result.id}`);
  console.log(`Cost: ~$0.01`);
}

async function cmdReply() {
  const tweetId = args[1];
  const text = args.slice(2).join(" ");
  if (!tweetId || !text) {
    console.error("Usage: x-search reply <tweet_id> <text>");
    process.exit(1);
  }
  if (text.length > 280) {
    console.error(`Reply too long: ${text.length}/280 chars`);
    process.exit(1);
  }
  const result = await api.replyToTweet(text, tweetId);
  console.log(`Replied: https://x.com/i/status/${result.id}`);
  console.log(`Cost: ~$0.01`);
}

async function cmdDelete() {
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
    console.error("  --since 1d|7d|1h|3h|12h   Time window (default: 1d)");
    console.error("  --limit N                  Tweets per account (default: 4)");
    console.error("  --markdown                 Markdown output");
    console.error("  --save                     Save to smaug/knowledge/research/");
    console.error("  --json                     Raw JSON");
    console.error("  --bird                     Free bird CLI fallback");
    console.error("  --no-cache                 Skip cache");
    process.exit(1);
  }

  const since = getOpt("since") || "1d";
  const limit = parseInt(getOpt("limit") || "4");
  const asMarkdown = getFlag("markdown");
  const asJson = getFlag("json");
  const save = getFlag("save");
  const useBird = getFlag("bird");
  const noCache = getFlag("no-cache");

  const feedgroups = loadFeedGroups();
  const accounts = resolveFeedAccounts(feedgroups, target);

  if (accounts.length === 0) {
    console.error(`No accounts found for "${target}". Use: x-search feedgroup`);
    process.exit(1);
  }

  console.error(`Fetching feed: ${accounts.length} accounts, since ${since}...\n`);

  let groupedTweets: Map<string, { label?: string; tweets: api.Tweet[] }>;

  if (useBird) {
    groupedTweets = await fetchFeedBird(accounts, since, limit);
  } else {
    groupedTweets = await fetchFeedApi(accounts, since, limit, noCache);
  }

  const windowLabel =
    since === "1d" ? "today" : since === "7d" ? "last week" : `last ${since}`;
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
  thread <tweet_id>           Fetch full conversation thread
  profile <username>          Recent tweets from a user
  tweet <tweet_id>            Fetch a single tweet
  feed <group|users> [opts]   Daily feed from account groups
  feedgroup [subcommand]      Manage feed groups (list/show/create/add/remove/delete/alias)
  post <text>                 Post a tweet (requires OAuth 1.0a)
  reply <tweet_id> <text>     Reply to a tweet (requires OAuth 1.0a)
  watchlist                   Show watchlist
  watchlist add <user> [note] Add user to watchlist
  watchlist remove <user>     Remove user from watchlist
  watchlist check             Check recent from all watchlist accounts
  cache clear                 Clear search cache

Search options:
  --sort likes|impressions|retweets|recent   (default: likes)
  --since 1h|3h|12h|1d|7d   Time filter (default: last 7 days)
  --min-likes N              Filter minimum likes
  --min-impressions N        Filter minimum impressions
  --pages N                  Pages to fetch, 1-5 (default: 1)
  --limit N                  Results to display (default: 15)
  --quick                    Quick mode: 1 page, max 10, noise filter, 1hr cache
  --from <username>          Shorthand for from:username in query
  --quality                  Filter low-engagement tweets (min 10 likes)
  --no-replies               Exclude replies
  --save                     Save to ~/tools/smaug/knowledge/research/
  --json                     Raw JSON output
  --markdown                 Markdown research doc

Feed options:
  --since 1d|7d|1h|3h|12h   Time window (default: 1d)
  --limit N                  Tweets per account (default: 4)
  --bird                     Free bird CLI fallback (no API cost)
  --markdown                 Markdown output
  --save                     Save to ~/tools/smaug/knowledge/research/
  --json                     Raw JSON output
  --no-cache                 Skip cache

Cost: $0.005/post read, $0.01/user lookup, $0.01/post create (pay-per-use)`);
}

async function main() {
  switch (command) {
    case "search":
    case "s":
      await cmdSearch();
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
    default:
      usage();
  }
}

main().catch((e) => {
  console.error(`Error: ${e.message}`);
  process.exit(1);
});
