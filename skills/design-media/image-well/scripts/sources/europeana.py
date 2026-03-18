#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Europeana image source — 50M+ items from European cultural institutions."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, normalize_license, warn
from sources.base import ImageSource


class EuropeanaSource(ImageSource):
    name = "europeana"
    display_name = "Europeana"
    tier = 3
    requires_key = True
    key_env_var = "EUROPEANA_API_KEY"
    rate_limit_seconds = 0.5
    base_url = "https://api.europeana.eu/record/v2"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        params: dict[str, str | int] = {
            "wskey": self._api_key or "",
            "query": query,
            "rows": min(limit, 100),
            "media": "true",
            "qf": "TYPE:IMAGE",
            "profile": "standard",
        }

        # Map license filter
        if license_filter and license_filter.lower() in ("cc0", "pd"):
            params["reusability"] = "open"

        try:
            async with session.get(
                f"{self.base_url}/search.json", params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"europeana: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"europeana: {e}")
            return []

        results: list[ImageResult] = []
        for item in data.get("items", []):
            # Get image URL from edmIsShownBy or edmPreview
            img_url = ""
            if item.get("edmIsShownBy"):
                img_url = item["edmIsShownBy"][0] if isinstance(item["edmIsShownBy"], list) else item["edmIsShownBy"]
            thumb_url = ""
            if item.get("edmPreview"):
                thumb_url = item["edmPreview"][0] if isinstance(item["edmPreview"], list) else item["edmPreview"]

            if not img_url and not thumb_url:
                continue

            title_list = item.get("title", ["Untitled"])
            title = title_list[0] if isinstance(title_list, list) and title_list else str(title_list)

            rights_list = item.get("rights", [""])
            rights = rights_list[0] if isinstance(rights_list, list) and rights_list else str(rights_list)

            provider_list = item.get("dataProvider", [""])
            provider = provider_list[0] if isinstance(provider_list, list) and provider_list else str(provider_list)

            results.append(ImageResult(
                source="europeana",
                title=title,
                url=img_url or thumb_url,
                thumbnail_url=thumb_url or img_url,
                license=normalize_license(rights),
                attribution=provider,
                width=0,
                height=0,
                tags=[],
                source_url=item.get("guid", "") or f"https://www.europeana.eu/item{item.get('id', '')}",
            ))
            if len(results) >= limit:
                break

        return results
