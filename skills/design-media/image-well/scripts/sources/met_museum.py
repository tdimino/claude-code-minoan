#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Met Museum image source — 375k+ open-access objects, CC0. Two-step search."""

import asyncio
import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource


class MetMuseumSource(ImageSource):
    name = "met"
    display_name = "Met Museum"
    tier = 1
    requires_key = False
    rate_limit_seconds = 0.3
    base_url = "https://collectionapi.metmuseum.org/public/collection/v1"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        # Step 1: Search for object IDs
        search_url = f"{self.base_url}/search"
        params = {
            "q": query,
            "hasImages": "true",
            "isPublicDomain": "true",
        }

        try:
            async with session.get(
                search_url, params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"met: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"met: {e}")
            return []

        object_ids = data.get("objectIDs") or []
        if not object_ids:
            return []

        # Step 2: Fetch object details (parallel, limited concurrency)
        object_ids = object_ids[:limit]
        sem = asyncio.Semaphore(5)
        results: list[ImageResult] = []

        async def fetch_object(obj_id: int) -> ImageResult | None:
            async with sem:
                await self._rate_wait()
                url = f"{self.base_url}/objects/{obj_id}"
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status != 200:
                            return None
                        obj = await resp.json()
                except (aiohttp.ClientError, TimeoutError):
                    return None

                img = obj.get("primaryImage", "")
                if not img:
                    return None

                title = obj.get("title", "Untitled") or "Untitled"
                artist = obj.get("artistDisplayName", "")
                date = obj.get("objectDate", "")
                dept = obj.get("department", "")

                attribution = ""
                if artist:
                    attribution = artist
                    if date:
                        attribution += f", {date}"

                tags = []
                for tag in obj.get("tags", []) or []:
                    if isinstance(tag, dict) and tag.get("term"):
                        tags.append(tag["term"])
                    elif isinstance(tag, str):
                        tags.append(tag)

                return ImageResult(
                    source="met",
                    title=f"{title}" + (f" ({date})" if date else ""),
                    url=img,
                    thumbnail_url=obj.get("primaryImageSmall", "") or img,
                    license="CC0",
                    attribution=attribution,
                    width=0,
                    height=0,
                    tags=tags[:10],
                    source_url=obj.get("objectURL", "") or f"https://www.metmuseum.org/art/collection/search/{obj_id}",
                )

        fetched = await asyncio.gather(*[fetch_object(oid) for oid in object_ids])
        results = [r for r in fetched if r is not None]

        return results[:limit]
