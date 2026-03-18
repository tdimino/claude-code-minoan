#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Iconify image source — 275K+ icons from 100+ icon sets (SVG vector)."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource


class IconifySource(ImageSource):
    name = "iconify"
    display_name = "Iconify Icons"
    tier = 3
    requires_key = False
    rate_limit_seconds = 0.1
    base_url = "https://api.iconify.design"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        params = {
            "query": query,
            "limit": str(min(limit, 64)),
        }

        try:
            async with session.get(
                f"{self.base_url}/search", params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    warn(f"iconify: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"iconify: {e}")
            return []

        results: list[ImageResult] = []
        icons = data.get("icons", [])

        for icon_name in icons:
            # Icon names are "prefix:name" format
            # SVG URL: https://api.iconify.design/{prefix}/{name}.svg
            parts = icon_name.split(":", 1)
            if len(parts) != 2:
                continue
            prefix, name = parts
            svg_url = f"{self.base_url}/{prefix}/{name}.svg"

            results.append(ImageResult(
                source="iconify",
                title=f"{name} ({prefix})",
                url=svg_url,
                thumbnail_url=svg_url,
                license="Various",
                attribution=f"Icon set: {prefix}",
                width=24,
                height=24,
                tags=[name.replace("-", " ")],
                source_url=f"https://icon-sets.iconify.design/{prefix}/{name}/",
            ))
            if len(results) >= limit:
                break

        return results
