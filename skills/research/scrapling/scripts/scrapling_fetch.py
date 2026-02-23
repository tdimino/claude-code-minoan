#!/usr/bin/env python3
"""
scrapling_fetch.py -- Stdout wrapper for Scrapling extraction.

Uses the Scrapling Python API directly (faster than CLI, avoids curl_cffi
cert issues). Outputs text or HTML to stdout for piping into
filter_web_results.py.

Usage:
    scrapling_fetch.py URL [options]
    scrapling_fetch.py URL --stealth --css ".product"
    scrapling_fetch.py URL --dynamic --solve-cloudflare
    scrapling_fetch.py URL --format html
    scrapling_fetch.py URL | filter_web_results.py --sections "API"
"""

import argparse
import sys


def fetch_http(url, impersonate="chrome", css=None, timeout=30, html=False):
    """Fetch via curl_cffi HTTP (fastest, TLS impersonation).
    timeout: seconds (curl_cffi native unit)."""
    from scrapling.fetchers import Fetcher

    # verify=False avoids curl_cffi bundled CA cert staleness on macOS/pyenv
    page = Fetcher.get(url, impersonate=impersonate, timeout=timeout, verify=False)
    if css:
        elements = page.css(css)
        if html:
            return "\n".join(str(el) for el in elements)
        return "\n".join(el.get_all_text() for el in elements)
    if html:
        return page.text
    return page.get_all_text()


def fetch_dynamic(url, css=None, headless=True, timeout=30, html=False):
    """Fetch via Playwright/Chromium (JS rendering).
    timeout: seconds (converted to ms for Playwright)."""
    from scrapling.fetchers import DynamicFetcher

    # DynamicFetcher expects milliseconds
    page = DynamicFetcher.fetch(url, headless=headless, timeout=timeout * 1000)
    if css:
        elements = page.css(css)
        if html:
            return "\n".join(str(el) for el in elements)
        return "\n".join(el.get_all_text() for el in elements)
    if html:
        return page.text
    return page.get_all_text()


def fetch_stealth(url, css=None, headless=True, solve_cloudflare=False, timeout=30, html=False):
    """Fetch via Patchright/Chrome (maximum stealth, anti-bot bypass).
    timeout: seconds (converted to ms for Patchright)."""
    from scrapling.fetchers import StealthyFetcher

    # StealthyFetcher expects milliseconds
    page = StealthyFetcher.fetch(
        url,
        headless=headless,
        solve_cloudflare=solve_cloudflare,
        timeout=timeout * 1000,
    )
    if css:
        elements = page.css(css)
        if html:
            return "\n".join(str(el) for el in elements)
        return "\n".join(el.get_all_text() for el in elements)
    if html:
        return page.text
    return page.get_all_text()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch a URL with Scrapling and output to stdout"
    )
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument(
        "--stealth", action="store_true",
        help="Use StealthyFetcher (Patchright, anti-bot bypass)"
    )
    parser.add_argument(
        "--dynamic", action="store_true",
        help="Use DynamicFetcher (Playwright, JS rendering)"
    )
    parser.add_argument(
        "--css", metavar="SELECTOR",
        help="CSS selector for targeted extraction"
    )
    parser.add_argument(
        "--solve-cloudflare", action="store_true",
        help="Enable Cloudflare Turnstile solver (stealth only)"
    )
    parser.add_argument(
        "--impersonate", metavar="BROWSER", default="chrome",
        help="Browser to impersonate for TLS fingerprint (HTTP only, default: chrome)"
    )
    parser.add_argument(
        "--format", choices=["text", "html"], default="text",
        help="Output format: text (extracted text, default) or html (raw HTML)"
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="Show browser window (debugging)"
    )
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="Request timeout in seconds (default: 30)"
    )

    args = parser.parse_args()
    headless = not args.no_headless
    html = args.format == "html"

    # Warn about incompatible flag combinations
    if args.solve_cloudflare and args.dynamic and not args.stealth:
        print("Warning: --solve-cloudflare has no effect without --stealth", file=sys.stderr)

    try:
        if args.stealth:
            content = fetch_stealth(
                args.url,
                css=args.css,
                headless=headless,
                solve_cloudflare=args.solve_cloudflare,
                timeout=args.timeout,
                html=html,
            )
        elif args.dynamic:
            content = fetch_dynamic(
                args.url,
                css=args.css,
                headless=headless,
                timeout=args.timeout,
                html=html,
            )
        else:
            content = fetch_http(
                args.url,
                impersonate=args.impersonate,
                css=args.css,
                timeout=args.timeout,
                html=html,
            )

        if content:
            sys.stdout.write(content)
            if not content.endswith("\n"):
                sys.stdout.write("\n")
        else:
            print("Warning: scrapling produced empty output", file=sys.stderr)
            sys.exit(1)

    except ImportError as e:
        print(
            f"Error: Missing dependency: {e}\n"
            "Run: ~/.claude/skills/scrapling/scripts/scrapling_install.sh",
            file=sys.stderr,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
