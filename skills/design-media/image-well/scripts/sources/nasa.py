#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""NASA Image and Video Library — 140k+ public domain assets."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource


class NasaSource(ImageSource):
    name = "nasa"
    display_name = "NASA Images"
    tier = 1
    requires_key = False
    rate_limit_seconds = 0.2
    base_url = "https://images-api.nasa.gov"

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
            "media_type": "image",
            "page_size": min(limit, 100),
        }

        try:
            async with session.get(
                f"{self.base_url}/search", params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"nasa: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"nasa: {e}")
            return []

        items = data.get("collection", {}).get("items", [])
        results: list[ImageResult] = []

        for item in items:
            item_data = item.get("data", [{}])[0] if item.get("data") else {}
            links = item.get("links", [])

            # Find the thumbnail link
            thumb_url = ""
            for link in links:
                if link.get("rel") == "preview" or link.get("render") == "image":
                    thumb_url = link.get("href", "")
                    break

            if not thumb_url:
                continue

            # The full-res image is at the asset manifest endpoint, but
            # the thumbnail is often good enough and avoids an extra request.
            # Use the larger version by replacing ~thumb with ~orig if available.
            full_url = thumb_url.replace("~thumb", "~orig").replace("~medium", "~orig")

            title = item_data.get("title", "Untitled") or "Untitled"
            nasa_id = item_data.get("nasa_id", "")
            description = item_data.get("description", "")
            keywords = item_data.get("keywords", []) or []

            results.append(ImageResult(
                source="nasa",
                title=title,
                url=full_url,
                thumbnail_url=thumb_url,
                license="PD",
                attribution=f"NASA" + (f" / {item_data.get('center', '')}" if item_data.get('center') else ""),
                width=0,
                height=0,
                tags=keywords[:10],
                source_url=f"https://images.nasa.gov/details/{nasa_id}" if nasa_id else "",
            ))
            if len(results) >= limit:
                break

        return results
