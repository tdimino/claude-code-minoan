#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Openverse image source — 800M+ CC-licensed items from Flickr, Wikimedia, Europeana, museums."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, normalize_license, warn
from sources.base import ImageSource


class OpenverseSource(ImageSource):
    name = "openverse"
    display_name = "Openverse"
    tier = 1
    requires_key = False
    rate_limit_seconds = 0.5
    base_url = "https://api.openverse.org/v1"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        params: dict[str, str | int] = {
            "q": query,
            "page_size": min(limit, 50),
        }

        # Map license filter to Openverse's license_type param
        if license_filter and license_filter != "any":
            lf = license_filter.lower().replace("-", "_")
            if lf in ("cc0", "pd"):
                params["license"] = "cc0,pdm"
            elif lf == "cc_by":
                params["license"] = "by"
            elif lf == "cc_by_sa":
                params["license"] = "by-sa,by,cc0,pdm"
            else:
                params["license_type"] = "all-cc"

        url = f"{self.base_url}/images/"
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    warn(f"openverse: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"openverse: {e}")
            return []

        results: list[ImageResult] = []
        for item in data.get("results", []):
            results.append(ImageResult(
                source="openverse",
                title=item.get("title", "Untitled") or "Untitled",
                url=item.get("url", ""),
                thumbnail_url=item.get("thumbnail", "") or item.get("url", ""),
                license=normalize_license(
                    f"{item.get('license', '')} {item.get('license_version', '')}".strip()
                ),
                attribution=item.get("attribution", "") or "",
                width=item.get("width", 0) or 0,
                height=item.get("height", 0) or 0,
                tags=[t.get("name", "") for t in item.get("tags", []) if t.get("name")],
                source_url=item.get("foreign_landing_url", "") or item.get("url", ""),
                score=1.0 - (len(results) / max(len(data.get("results", [])), 1)),
            ))
            if len(results) >= limit:
                break

        return results
