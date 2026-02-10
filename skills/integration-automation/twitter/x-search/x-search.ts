#!/usr/bin/env bun
/**
 * x-search — CLI for X/Twitter research via official API v2.
 *
 * Commands:
 *   search <query> [options]    Search recent tweets (last 7 days)
 *   thread <tweet_id>           Fetch full conversation thread
 *   profile <username>          Recent tweets from a user
 *   tweet <tweet_id>            Fetch a single tweet
 *   watchlist                   Show watchlist
 *   watchlist add <user> [note] Add user to watchlist
 *   watchlist remove <user>     Remove user from watchlist
 *   watchlist check             Check recent tweets from all watchlist accounts
 *   cache clear                 Clear search cache
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

function usage() {
  console.log(`x-search — X/Twitter research CLI (official API v2)

Commands:
  search <query> [options]    Search recent tweets (last 7 days)
  thread <tweet_id>           Fetch full conversation thread
  profile <username>          Recent tweets from a user
  tweet <tweet_id>            Fetch a single tweet
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

Cost: $0.005/post read, $0.01/user lookup (pay-per-use)`);
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
    case "watchlist":
    case "wl":
      await cmdWatchlist();
      break;
    case "cache":
      await cmdCache();
      break;
    default:
      usage();
  }
}

main().catch((e) => {
  console.error(`Error: ${e.message}`);
  process.exit(1);
});
