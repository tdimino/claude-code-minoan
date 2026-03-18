#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Wikimedia Commons image source — millions of freely-licensed media files."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, normalize_license, warn
from sources.base import ImageSource


class WikimediaSource(ImageSource):
    name = "wikimedia"
    display_name = "Wikimedia Commons"
    tier = 1
    requires_key = False
    rate_limit_seconds = 0.3
    base_url = "https://commons.wikimedia.org/w/api.php"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": "6",
            "gsrlimit": str(min(limit, 50)),
            "prop": "imageinfo",
            "iiprop": "url|mime|extmetadata|size",
            "iiurlwidth": "800",
            "format": "json",
        }

        try:
            async with session.get(
                self.base_url, params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"wikimedia: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"wikimedia: {e}")
            return []

        pages = data.get("query", {}).get("pages", {})
        results: list[ImageResult] = []

        for _page_id, page in pages.items():
            info_list = page.get("imageinfo", [])
            if not info_list:
                continue
            info = info_list[0]
            mime = info.get("mime", "")
            if not mime.startswith("image/"):
                continue

            extmeta = info.get("extmetadata", {})
            license_raw = extmeta.get("LicenseShortName", {}).get("value", "")
            title = page.get("title", "").replace("File:", "")
            attribution = extmeta.get("Artist", {}).get("value", "")

            results.append(ImageResult(
                source="wikimedia",
                title=title,
                url=info.get("url", ""),
                thumbnail_url=info.get("thumburl", "") or info.get("url", ""),
                license=normalize_license(license_raw),
                attribution=attribution,
                width=info.get("width", 0) or 0,
                height=info.get("height", 0) or 0,
                tags=[],
                source_url=info.get("descriptionurl", "") or f"https://commons.wikimedia.org/wiki/{page.get('title', '')}",
            ))
            if len(results) >= limit:
                break

        return results
