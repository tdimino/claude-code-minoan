#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Unsplash image source — high-quality free photos, attribution required."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource


class UnsplashSource(ImageSource):
    name = "unsplash"
    display_name = "Unsplash"
    tier = 2
    requires_key = True
    key_env_var = "UNSPLASH_ACCESS_KEY"
    rate_limit_seconds = 1.0
    base_url = "https://api.unsplash.com"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        headers = {
            "Authorization": f"Client-ID {self._api_key}",
            "Accept-Version": "v1",
        }
        params = {
            "query": query,
            "per_page": min(limit, 30),
        }

        try:
            async with session.get(
                f"{self.base_url}/search/photos", params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"unsplash: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"unsplash: {e}")
            return []

        results: list[ImageResult] = []
        for photo in data.get("results", []):
            urls = photo.get("urls", {})
            user = photo.get("user", {})
            photographer = user.get("name", "")

            tags = []
            for tag in photo.get("tags", []):
                if isinstance(tag, dict) and tag.get("title"):
                    tags.append(tag["title"])

            results.append(ImageResult(
                source="unsplash",
                title=photo.get("description", "") or photo.get("alt_description", "") or f"Unsplash #{photo.get('id', '')}",
                url=urls.get("full", "") or urls.get("regular", ""),
                thumbnail_url=urls.get("small", "") or urls.get("thumb", ""),
                license="Unsplash",
                attribution=f"Photo by {photographer} on Unsplash" if photographer else "Unsplash",
                width=photo.get("width", 0) or 0,
                height=photo.get("height", 0) or 0,
                tags=tags[:10],
                source_url=photo.get("links", {}).get("html", ""),
            ))
            if len(results) >= limit:
                break

        return results
