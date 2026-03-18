#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Rijksmuseum image source — 700k+ CC0 objects with IIIF deep zoom."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource


class RijksmuseumSource(ImageSource):
    name = "rijksmuseum"
    display_name = "Rijksmuseum"
    tier = 2
    requires_key = True
    key_env_var = "RIJKSMUSEUM_API_KEY"
    rate_limit_seconds = 0.3
    base_url = "https://www.rijksmuseum.nl/api/en/collection"

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
            "imgonly": "True",
            "ps": str(min(limit, 100)),
            "format": "json",
        }

        try:
            async with session.get(
                self.base_url, params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"rijksmuseum: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"rijksmuseum: {e}")
            return []

        results: list[ImageResult] = []
        for obj in data.get("artObjects", []):
            web_image = obj.get("webImage") or {}
            img_url = web_image.get("url", "")
            if not img_url:
                continue

            header_image = obj.get("headerImage") or {}
            thumb_url = header_image.get("url", "") or img_url

            title = obj.get("title", "Untitled") or "Untitled"
            artist = obj.get("principalOrFirstMaker", "")

            results.append(ImageResult(
                source="rijksmuseum",
                title=title,
                url=img_url,
                thumbnail_url=thumb_url,
                license="CC0",
                attribution=artist,
                width=web_image.get("width", 0) or 0,
                height=web_image.get("height", 0) or 0,
                tags=[],
                source_url=obj.get("links", {}).get("web", "") or f"https://www.rijksmuseum.nl/en/collection/{obj.get('objectNumber', '')}",
            ))
            if len(results) >= limit:
                break

        return results
