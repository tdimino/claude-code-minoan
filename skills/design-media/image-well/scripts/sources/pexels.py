#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Pexels image source — high-quality stock photos, no attribution required."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource


class PexelsSource(ImageSource):
    name = "pexels"
    display_name = "Pexels"
    tier = 2
    requires_key = True
    key_env_var = "PEXELS_API_KEY"
    rate_limit_seconds = 0.5
    base_url = "https://api.pexels.com/v1"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        headers = {"Authorization": self._api_key}
        params = {
            "query": query,
            "per_page": min(limit, 80),
        }

        try:
            async with session.get(
                f"{self.base_url}/search", params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"pexels: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"pexels: {e}")
            return []

        results: list[ImageResult] = []
        for photo in data.get("photos", []):
            src = photo.get("src", {})
            results.append(ImageResult(
                source="pexels",
                title=photo.get("alt", "") or f"Pexels #{photo.get('id', '')}",
                url=src.get("original", "") or src.get("large2x", ""),
                thumbnail_url=src.get("medium", "") or src.get("small", ""),
                license="Pexels",
                attribution=photo.get("photographer", ""),
                width=photo.get("width", 0) or 0,
                height=photo.get("height", 0) or 0,
                tags=[],
                source_url=photo.get("url", ""),
            ))
            if len(results) >= limit:
                break

        return results
