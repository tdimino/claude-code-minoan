#!/usr/bin/env python3
"""Check design-system URLs from references/index.json for liveness."""

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

INDEX_PATH = Path(__file__).parent.parent / "references" / "index.json"
TIMEOUT = 8
MAX_WORKERS = 8
USER_AGENT = "component-gallery-linkcheck/1.0 (skill link audit)"

MAJOR_SITES_403 = {
    "github.com", "gitlab.com", "medium.com", "linkedin.com",
    "twitter.com", "x.com", "facebook.com", "instagram.com",
    "pinterest.com", "amazon.com",
}


def classify(url: str) -> dict:
    """HEAD then GET a URL, return classification dict."""
    result = {"url": url, "status": None, "code": None, "detail": "", "category": "unknown"}
    headers = {"User-Agent": USER_AGENT}

    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx)
            code = resp.getcode()
            final_url = resp.geturl()
            result["code"] = code
            if final_url != url:
                result["category"] = "redirected"
                result["detail"] = final_url
            else:
                result["category"] = "ok"
            return result
        except urllib.error.HTTPError as e:
            result["code"] = e.code
            if e.code == 403:
                from urllib.parse import urlparse
                host = urlparse(url).hostname or ""
                if any(host.endswith(s) for s in MAJOR_SITES_403):
                    result["category"] = "bot-blocked"
                    result["detail"] = f"403 from {host} (likely bot protection)"
                    return result
                result["category"] = "bot-blocked"
                result["detail"] = f"403 Forbidden"
                if method == "HEAD":
                    continue
                return result
            elif 400 <= e.code < 500:
                result["category"] = "client-error"
                result["detail"] = f"HTTP {e.code}"
                return result
            elif 500 <= e.code < 600:
                result["category"] = "server-error"
                result["detail"] = f"HTTP {e.code}"
                if method == "HEAD":
                    continue
                return result
        except ssl.SSLError as e:
            result["category"] = "unreachable"
            result["detail"] = f"TLS error: {str(e)[:100]}"
            return result
        except urllib.error.URLError as e:
            reason = str(e.reason) if hasattr(e, "reason") else str(e)
            result["category"] = "unreachable"
            result["detail"] = reason[:120]
            return result
        except OSError as e:
            result["category"] = "unreachable"
            result["detail"] = str(e)[:120]
            return result

    return result


def load_urls() -> list[dict]:
    """Load all design-system URLs from index.json."""
    with open(INDEX_PATH) as f:
        data = json.load(f)

    urls = []
    for ds in data.get("design_systems", []):
        if ds.get("url"):
            urls.append({"name": ds["name"], "url": ds["url"]})
    return urls


CATEGORY_ORDER = {
    "unreachable": 0,
    "server-error": 1,
    "client-error": 2,
    "bot-blocked": 3,
    "redirected": 4,
    "ok": 5,
    "unknown": 6,
}


def main():
    parser = argparse.ArgumentParser(
        description="Validate design-system URLs from index.json"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    entries = load_urls()
    print(f"Checking {len(entries)} design-system URLs...", file=sys.stderr)

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {
            pool.submit(classify, e["url"]): e for e in entries
        }
        for future in as_completed(future_map):
            entry = future_map[future]
            try:
                res = future.result()
            except Exception as exc:
                res = {
                    "url": entry["url"],
                    "code": None,
                    "category": "unreachable",
                    "detail": str(exc)[:120],
                }
            res["name"] = entry["name"]
            results.append(res)
            cat = res["category"]
            if cat != "ok":
                print(f"  {cat}: {entry['name']}", file=sys.stderr)

    results.sort(key=lambda r: (CATEGORY_ORDER.get(r["category"], 99), r["name"]))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        cats = {}
        for r in results:
            cats.setdefault(r["category"], []).append(r)

        print(f"\n{'Name':<45} {'Status':<15} {'Code':<6} {'Detail'}")
        print("-" * 110)
        for r in results:
            code_str = str(r["code"]) if r["code"] else "-"
            detail = r.get("detail", "")[:50]
            print(f"{r['name']:<45} {r['category']:<15} {code_str:<6} {detail}")

        print(f"\n--- Summary ---")
        for cat in sorted(cats.keys(), key=lambda c: CATEGORY_ORDER.get(c, 99)):
            print(f"  {cat}: {len(cats[cat])}")
        print(f"  total: {len(results)}")


if __name__ == "__main__":
    main()
