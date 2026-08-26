#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Getty Museum image source — Open Content program, per-image CC0 via IIIF.

Uses the collection website's JSON search API (www.getty.edu/art/collection/api/search)
— undocumented but the only keyword-search surface Getty exposes (the Linked Art
REST/SPARQL endpoints have no text search). Verified live 2026-08-26:
`open_content=true&images=true` filters server-side, and each row's
manifest.license carries the CC0 URI, which is the authoritative per-image gate.
Download URLs derive from the row's IIIF thumb by swapping the size segment.
"""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource

CC0_URI = "creativecommons.org/publicdomain/zero"


class GettySource(ImageSource):
    name = "getty"
    display_name = "Getty Museum"
    tier = 1
    requires_key = False
    rate_limit_seconds = 0.5
    base_url = "https://www.getty.edu/art/collection/api/search"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()
        params = {
            "q": query,
            "open_content": "true",
            "images": "true",
            "size": str(min(limit, 50)),
            "from": "0",
        }
        try:
            async with session.get(
                self.base_url, params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"getty: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"getty: {e}")
            return []

        results: list[ImageResult] = []
        for obj in data.get("data") or []:
            manifest = obj.get("manifest") or {}
            thumb = manifest.get("thumb") or ""
            # Per-image CC0 gate — open_content=true should guarantee this,
            # but the license URI on the row is the authoritative statement.
            if not thumb or CC0_URI not in (manifest.get("license") or ""):
                continue
            if "/full/" not in thumb:
                continue

            title = obj.get("primary_name", "Untitled") or "Untitled"
            date = obj.get("date_created", "") or ""
            producers = obj.get("producers") or []
            attribution = "; ".join(
                p.get("description", "") for p in producers if p.get("description")
            )

            tags: list[str] = []
            culture = obj.get("culture")
            if isinstance(culture, str) and culture:
                tags.append(culture)
            elif isinstance(culture, list):
                tags.extend(c for c in culture if isinstance(c, str))

            slug = obj.get("slug_with_path", "") or ""
            base = thumb.split("/full/")[0]
            results.append(ImageResult(
                source="getty",
                title=f"{title}" + (f" ({date})" if date else ""),
                url=f"{base}/full/1200,/0/default.jpg",
                thumbnail_url=thumb,
                license="CC0",
                attribution=attribution,
                width=0,
                height=0,
                tags=tags[:10],
                source_url=f"https://www.getty.edu/art/collection{slug}" if slug else "",
            ))
            if len(results) >= limit:
                break

        return results
