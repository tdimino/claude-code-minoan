#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Pixabay image source — free stock photos, no attribution required."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource


class PixabaySource(ImageSource):
    name = "pixabay"
    display_name = "Pixabay"
    tier = 2
    requires_key = True
    key_env_var = "PIXABAY_API_KEY"
    rate_limit_seconds = 0.3
    base_url = "https://pixabay.com/api/"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        params = {
            "key": self._api_key,
            "q": query,
            "per_page": min(limit, 200),
            "image_type": "photo",
            "safesearch": "true",
        }

        try:
            async with session.get(
                self.base_url, params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"pixabay: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"pixabay: {e}")
            return []

        results: list[ImageResult] = []
        for hit in data.get("hits", []):
            tags = [t.strip() for t in hit.get("tags", "").split(",") if t.strip()]
            results.append(ImageResult(
                source="pixabay",
                title=tags[0].title() if tags else f"Pixabay #{hit.get('id', '')}",
                url=hit.get("largeImageURL", "") or hit.get("webformatURL", ""),
                thumbnail_url=hit.get("previewURL", "") or hit.get("webformatURL", ""),
                license="Pixabay",
                attribution=hit.get("user", ""),
                width=hit.get("imageWidth", 0) or 0,
                height=hit.get("imageHeight", 0) or 0,
                tags=tags[:10],
                source_url=hit.get("pageURL", ""),
            ))
            if len(results) >= limit:
                break

        return results
