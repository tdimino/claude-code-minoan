#!/usr/bin/env python3
"""
cf_browser.py -- Cloudflare Browser Rendering CLI wrapper.

Single-file CLI for Cloudflare's Browser Rendering REST API. Outputs to stdout
for piping into filter_web_results.py.

Auth: CLOUDFLARE_ACCOUNT_ID (required) + CLOUDFLARE_API_TOKEN (preferred)
      or CLOUDFLARE_GLOBAL_API_KEY + CLOUDFLARE_EMAIL (fallback).

Usage:
    cf_browser.py markdown https://example.com
    cf_browser.py markdown https://example.com --no-render
    cf_browser.py crawl https://docs.example.com --limit 50
    cf_browser.py crawl https://docs.example.com --async
    cf_browser.py status <job-id>
    cf_browser.py screenshot https://example.com -o page.png
    cf_browser.py links https://example.com
    cf_browser.py json https://example.com --prompt "Extract product names"
    cf_browser.py markdown URL | filter_web_results.py --sections "API"
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("Error: requests is required. Run: uv pip install requests", file=sys.stderr)
    sys.exit(1)


def _get_config():
    """Load Cloudflare credentials from environment."""
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not account_id:
        print(
            "Error: CLOUDFLARE_ACCOUNT_ID not set.\n"
            "Get it from: wrangler whoami\n"
            "Add to ~/.config/env/secrets.env: export CLOUDFLARE_ACCOUNT_ID=\"...\"",
            file=sys.stderr,
        )
        sys.exit(1)

    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    global_key = os.environ.get("CLOUDFLARE_GLOBAL_API_KEY")
    email = os.environ.get("CLOUDFLARE_EMAIL")

    if not api_token and not (global_key and email):
        print(
            "Error: Set CLOUDFLARE_API_TOKEN or both CLOUDFLARE_GLOBAL_API_KEY + CLOUDFLARE_EMAIL",
            file=sys.stderr,
        )
        sys.exit(1)

    return account_id, api_token, global_key, email


# Cache config to avoid re-reading env vars on every call
_cached_config = None


def _config():
    """Cached config loader."""
    global _cached_config
    if _cached_config is None:
        _cached_config = _get_config()
    return _cached_config


def _headers():
    """Return auth headers for the CF API."""
    _, api_token, global_key, email = _config()
    if api_token:
        return {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    return {
        "X-Auth-Key": global_key,
        "X-Auth-Email": email,
        "Content-Type": "application/json",
    }


def _base_url():
    """Return the base URL for Browser Rendering API."""
    account_id = _config()[0]
    return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering"


def _post(endpoint, payload, stream=False):
    """POST to a Browser Rendering endpoint. Returns response."""
    url = f"{_base_url()}/{endpoint}"
    resp = requests.post(url, headers=_headers(), json=payload, stream=stream, timeout=60)
    if resp.status_code != 200:
        try:
            err = resp.json()
            errors = err.get("errors", [])
            msg = errors[0].get("message", resp.text) if errors else resp.text
        except Exception:
            msg = resp.text
        print(f"Error ({resp.status_code}): {msg}", file=sys.stderr)
        sys.exit(1)
    return resp


def _get(endpoint, params=None):
    """GET from a Browser Rendering endpoint. Returns response JSON."""
    url = f"{_base_url()}/{endpoint}"
    resp = requests.get(url, headers=_headers(), params=params, timeout=60)
    if resp.status_code != 200:
        try:
            err = resp.json()
            errors = err.get("errors", [])
            msg = errors[0].get("message", resp.text) if errors else resp.text
        except Exception:
            msg = resp.text
        print(f"Error ({resp.status_code}): {msg}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def _delete(endpoint):
    """DELETE a Browser Rendering resource."""
    url = f"{_base_url()}/{endpoint}"
    resp = requests.delete(url, headers=_headers(), timeout=60)
    return resp


# --- Endpoint functions ---


def fetch_markdown(url):
    """Fetch a single page as markdown."""
    payload = {"url": url}
    resp = _post("markdown", payload)
    data = resp.json()
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return resp.text


def fetch_content(url):
    """Fetch a single page as rendered HTML."""
    payload = {"url": url}
    resp = _post("content", payload)
    data = resp.json()
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return resp.text


def fetch_screenshot(url):
    """Fetch a screenshot of a page. Returns PNG bytes."""
    payload = {"url": url}
    resp = _post("screenshot", payload, stream=True)
    return resp.content


def fetch_pdf(url):
    """Fetch a page as PDF. Returns PDF bytes."""
    payload = {"url": url}
    resp = _post("pdf", payload, stream=True)
    return resp.content


def fetch_links(url, exclude_external=False):
    """Extract all links from a page."""
    payload = {"url": url, "excludeExternalLinks": exclude_external}
    resp = _post("links", payload)
    data = resp.json()
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


def fetch_scrape(url, selectors):
    """Scrape specific elements via CSS selectors."""
    payload = {"url": url, "elements": selectors}
    resp = _post("scrape", payload)
    data = resp.json()
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


def fetch_json(url, prompt=None, schema=None):
    """AI-powered structured data extraction."""
    payload = {"url": url}
    json_options = {}
    if prompt:
        json_options["prompt"] = prompt
    if schema:
        json_options["response_format"] = json.loads(schema)
    if json_options:
        payload["jsonOptions"] = json_options
    resp = _post("json", payload)
    data = resp.json()
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


def start_crawl(url, limit=100, depth=None, source="all", formats=None,
                render=True, include_patterns=None, exclude_patterns=None,
                modified_since=None, max_age=None, include_subdomains=False,
                include_external=False, json_prompt=None):
    """Start an async crawl job. Returns job data."""
    payload = {"url": url, "limit": limit, "source": source, "render": render}
    if depth is not None:
        payload["depth"] = depth
    if formats:
        payload["formats"] = formats
    else:
        payload["formats"] = ["markdown"]
    if modified_since is not None:
        payload["modifiedSince"] = modified_since
    if max_age is not None:
        payload["maxAge"] = max_age
    if json_prompt:
        payload["jsonOptions"] = {"prompt": json_prompt}

    options = {}
    if include_patterns:
        options["includePatterns"] = include_patterns
    if exclude_patterns:
        options["excludePatterns"] = exclude_patterns
    if include_subdomains:
        options["includeSubdomains"] = True
    if include_external:
        options["includeExternalLinks"] = True
    if options:
        payload["options"] = options

    resp = _post("crawl", payload)
    return resp.json()


def get_crawl_status(job_id, cursor=None):
    """Get crawl job status and results."""
    params = {}
    if cursor:
        params["cursor"] = cursor
    return _get(f"crawl/{job_id}", params=params)


def cancel_crawl(job_id):
    """Cancel a running crawl job."""
    return _delete(f"crawl/{job_id}")


def poll_crawl(job_id, timeout=300, interval=2):
    """Poll a crawl job until completion. Exponential backoff."""
    start = time.time()
    current_interval = interval
    while time.time() - start < timeout:
        data = get_crawl_status(job_id)
        status = data.get("status", data.get("result", {}).get("status", "unknown"))
        if status == "completed":
            return data
        if status in ("errored", "cancelled_by_user", "cancelled_due_to_timeout", "cancelled_due_to_limits"):
            print(f"Crawl {status}: {json.dumps(data, indent=2)}", file=sys.stderr)
            sys.exit(1)
        # Progress indicator
        pages = data.get("result", {}).get("pages_crawled", "?")
        print(f"  Crawling... status={status} pages={pages} (poll in {current_interval}s)", file=sys.stderr)
        time.sleep(current_interval)
        current_interval = min(current_interval * 1.5, 15)

    print(f"Error: Crawl timed out after {timeout}s. Job ID: {job_id}", file=sys.stderr)
    print(f"Check later: cf_browser.py status {job_id}", file=sys.stderr)
    sys.exit(1)


def format_crawl_results(data):
    """Format crawl results as readable output."""
    results = data.get("result", data)
    pages = results.get("data", results.get("pages", []))
    if not pages:
        return json.dumps(data, indent=2)

    output = []
    for page in pages:
        url = page.get("url", "unknown")
        output.append(f"# {url}\n")
        if "markdown" in page:
            output.append(page["markdown"])
        elif "html" in page:
            output.append(page["html"])
        elif "json" in page:
            output.append(json.dumps(page["json"], indent=2))
        output.append("\n---\n")
    return "\n".join(output)


# --- CLI ---


def main():
    parser = argparse.ArgumentParser(
        description="Cloudflare Browser Rendering CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Pipe into filter_web_results.py for token-efficient filtering.\n"
               "Docs: https://developers.cloudflare.com/browser-rendering/rest-api/",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- markdown --
    p_md = sub.add_parser("markdown", help="Fetch single page as markdown")
    p_md.add_argument("url", help="URL to fetch")
    p_md.add_argument("--no-render", action="store_true", help="Static HTML only (free during beta)")

    # -- content --
    p_ct = sub.add_parser("content", help="Fetch single page as rendered HTML")
    p_ct.add_argument("url", help="URL to fetch")
    p_ct.add_argument("--no-render", action="store_true", help="Static HTML only")

    # -- crawl --
    p_cr = sub.add_parser("crawl", help="Crawl entire website (async)")
    p_cr.add_argument("url", help="Starting URL")
    p_cr.add_argument("--limit", type=int, default=100, help="Max pages (default: 100, max: 100000)")
    p_cr.add_argument("--depth", type=int, help="Max link depth")
    p_cr.add_argument("--source", choices=["all", "sitemaps", "links"], default="all", help="URL discovery method")
    p_cr.add_argument("--format", dest="formats", action="append", choices=["html", "markdown", "json"],
                       help="Output format(s), repeatable (default: markdown)")
    p_cr.add_argument("--no-render", action="store_true", help="Static HTML only (free during beta)")
    p_cr.add_argument("--include-pattern", action="append", dest="include_patterns", help="Wildcard URL include filter")
    p_cr.add_argument("--exclude-pattern", action="append", dest="exclude_patterns", help="Wildcard URL exclude filter")
    p_cr.add_argument("--modified-since", type=int, help="Unix timestamp for incremental crawl")
    p_cr.add_argument("--max-age", type=int, help="Cache TTL in seconds (default: 86400)")
    p_cr.add_argument("--include-subdomains", action="store_true", help="Follow subdomain links")
    p_cr.add_argument("--include-external", action="store_true", help="Follow external links")
    p_cr.add_argument("--json-prompt", help="AI extraction prompt (adds json to formats)")
    p_cr.add_argument("--async", dest="async_mode", action="store_true", help="Return job ID immediately")
    p_cr.add_argument("--timeout", type=int, default=300, help="Poll timeout in seconds (default: 300)")

    # -- status --
    p_st = sub.add_parser("status", help="Check crawl job status")
    p_st.add_argument("job_id", help="Crawl job ID")
    p_st.add_argument("--cursor", help="Pagination cursor for large results")

    # -- cancel --
    p_ca = sub.add_parser("cancel", help="Cancel a running crawl job")
    p_ca.add_argument("job_id", help="Crawl job ID")

    # -- screenshot --
    p_ss = sub.add_parser("screenshot", help="Capture page screenshot (PNG)")
    p_ss.add_argument("url", help="URL to capture")
    p_ss.add_argument("-o", "--output", default="-", help="Output file (default: stdout)")
    p_ss.add_argument("--no-render", action="store_true", help="Static HTML only")

    # -- pdf --
    p_pdf = sub.add_parser("pdf", help="Render page as PDF")
    p_pdf.add_argument("url", help="URL to render")
    p_pdf.add_argument("-o", "--output", default="-", help="Output file (default: stdout)")
    p_pdf.add_argument("--no-render", action="store_true", help="Static HTML only")

    # -- links --
    p_ln = sub.add_parser("links", help="Extract all links from a page")
    p_ln.add_argument("url", help="URL to extract links from")
    p_ln.add_argument("--no-render", action="store_true", help="Static HTML only")
    p_ln.add_argument("--exclude-external", action="store_true", help="Exclude external links")

    # -- scrape --
    p_sc = sub.add_parser("scrape", help="Scrape HTML elements via CSS selectors")
    p_sc.add_argument("url", help="URL to scrape")
    p_sc.add_argument("--selector", "-s", action="append", required=True, help="CSS selector(s)")
    p_sc.add_argument("--no-render", action="store_true", help="Static HTML only")

    # -- json --
    p_js = sub.add_parser("json", help="AI-powered structured data extraction")
    p_js.add_argument("url", help="URL to extract from")
    p_js.add_argument("--prompt", "-p", help="Extraction prompt for the AI model")
    p_js.add_argument("--schema", help="JSON schema string for response structure")
    p_js.add_argument("--no-render", action="store_true", help="Static HTML only")

    args = parser.parse_args()

    try:
        if args.command == "markdown":
            result = fetch_markdown(args.url)
            sys.stdout.write(result)
            if result and not result.endswith("\n"):
                sys.stdout.write("\n")

        elif args.command == "content":
            result = fetch_content(args.url)
            sys.stdout.write(result)
            if result and not result.endswith("\n"):
                sys.stdout.write("\n")

        elif args.command == "crawl":
            formats = args.formats
            if args.json_prompt and (not formats or "json" not in formats):
                formats = (formats or []) + ["json"]
            data = start_crawl(
                args.url, limit=args.limit, depth=args.depth, source=args.source,
                formats=formats, render=not args.no_render,
                include_patterns=args.include_patterns,
                exclude_patterns=args.exclude_patterns,
                modified_since=args.modified_since, max_age=args.max_age,
                include_subdomains=args.include_subdomains,
                include_external=args.include_external,
                json_prompt=args.json_prompt,
            )
            job_id = data.get("id", data.get("result", {}).get("id"))
            if not job_id:
                print(f"Error: No job ID returned: {json.dumps(data)}", file=sys.stderr)
                sys.exit(1)

            if args.async_mode:
                print(f"Job started: {job_id}")
                print(f"Check: cf_browser.py status {job_id}", file=sys.stderr)
            else:
                print(f"Crawl started (job: {job_id}), polling...", file=sys.stderr)
                result = poll_crawl(job_id, timeout=args.timeout)
                output = format_crawl_results(result)
                sys.stdout.write(output)
                if output and not output.endswith("\n"):
                    sys.stdout.write("\n")

        elif args.command == "status":
            data = get_crawl_status(args.job_id, cursor=args.cursor)
            status = data.get("status", data.get("result", {}).get("status", "unknown"))
            if status == "completed" and not args.cursor:
                output = format_crawl_results(data)
                sys.stdout.write(output)
            else:
                print(json.dumps(data, indent=2))

        elif args.command == "cancel":
            resp = cancel_crawl(args.job_id)
            if resp.status_code == 200:
                print(f"Crawl {args.job_id} cancelled.")
            else:
                print(f"Cancel failed ({resp.status_code}): {resp.text}", file=sys.stderr)
                sys.exit(1)

        elif args.command == "screenshot":
            data = fetch_screenshot(args.url)
            if args.output == "-":
                sys.stdout.buffer.write(data)
            else:
                with open(args.output, "wb") as f:
                    f.write(data)
                print(f"Screenshot saved: {args.output}", file=sys.stderr)

        elif args.command == "pdf":
            data = fetch_pdf(args.url)
            if args.output == "-":
                sys.stdout.buffer.write(data)
            else:
                with open(args.output, "wb") as f:
                    f.write(data)
                print(f"PDF saved: {args.output}", file=sys.stderr)

        elif args.command == "links":
            data = fetch_links(args.url, exclude_external=args.exclude_external)
            if isinstance(data, list):
                for link in data:
                    print(link)
            else:
                print(json.dumps(data, indent=2))

        elif args.command == "scrape":
            data = fetch_scrape(args.url, args.selector)
            print(json.dumps(data, indent=2))

        elif args.command == "json":
            data = fetch_json(args.url, prompt=args.prompt, schema=args.schema)
            print(json.dumps(data, indent=2))

    except KeyboardInterrupt:
        sys.exit(130)
    except requests.exceptions.Timeout:
        print("Error: Request timed out", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Connection failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
