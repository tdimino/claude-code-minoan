#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Smithsonian Open Access — millions of objects across 19 museums, CC0 for PD works.

Uses the /category/art_design/search endpoint, which returns actual museum objects
with digitized images. The base /search endpoint returns library catalog entries
(books, bibliographies) that lack online_media fields.
"""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, get_api_key, warn
from sources.base import ImageSource


class SmithsonianSource(ImageSource):
    name = "smithsonian"
    display_name = "Smithsonian"
    tier = 3
    requires_key = False
    rate_limit_seconds = 0.3
    base_url = "https://api.si.edu/openaccess/api/v1.0"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        await self._rate_wait()

        # Use real key if available, fall back to DEMO_KEY (30/hr, 50/day)
        api_key = get_api_key("SMITHSONIAN_API_KEY") or "DEMO_KEY"

        # Over-fetch since not all results have images
        params = {
            "q": query,
            "rows": str(min(limit * 4, 100)),
            "api_key": api_key,
        }

        # Use category endpoint — returns museum objects with actual images
        try:
            async with session.get(
                f"{self.base_url}/category/art_design/search", params=params,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    warn(f"smithsonian: HTTP {resp.status}")
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            warn(f"smithsonian: {e}")
            return []

        rows = data.get("response", {}).get("rows", [])
        results: list[ImageResult] = []

        for row in rows:
            content = row.get("content", {})
            desc = content.get("descriptiveNonRepeating", {})
            freetext = content.get("freetext", {})
            indexed = content.get("indexedStructured", {})

            # Title can be a dict {"label": "Title", "content": "..."} or string
            raw_title = desc.get("title", {})
            if isinstance(raw_title, dict):
                title = raw_title.get("content", "") or "Untitled"
            elif isinstance(raw_title, list):
                title = next((t.get("content", "") for t in raw_title if isinstance(t, dict) and t.get("content")), "Untitled")
            else:
                title = str(raw_title) if raw_title else "Untitled"

            # Extract image URL from online_media
            media_list = desc.get("online_media", {}).get("media", [])
            img_url = ""
            thumb_url = ""
            width = 0
            height = 0

            for media in media_list:
                if media.get("type", "").startswith("Images"):
                    img_url = media.get("content", "")
                    thumb_url = media.get("thumbnail", "") or img_url

                    # Extract dimensions from resources array
                    for res in media.get("resources", []):
                        if res.get("label") == "High-resolution JPEG":
                            width = res.get("width", 0) or 0
                            height = res.get("height", 0) or 0
                            break
                        elif not width and res.get("width"):
                            width = res.get("width", 0) or 0
                            height = res.get("height", 0) or 0

                    # Better thumbnail from resources
                    for res in media.get("resources", []):
                        if res.get("label") == "Thumbnail Image" and res.get("url"):
                            thumb_url = res["url"]
                            break
                    break

            if not img_url:
                continue

            # Extract attribution from freetext
            attribution = ""
            for note in freetext.get("name", []):
                if isinstance(note, dict):
                    attribution = note.get("content", "")
                    break

            # Extract tags from indexedStructured
            tags: list[str] = []
            for field in ("topic", "culture", "object_type"):
                for val in indexed.get(field, []) or []:
                    if isinstance(val, str) and val not in tags:
                        tags.append(val)

            results.append(ImageResult(
                source="smithsonian",
                title=title,
                url=img_url,
                thumbnail_url=thumb_url,
                license="CC0",
                attribution=attribution,
                width=width,
                height=height,
                tags=tags[:10],
                source_url=desc.get("record_link", "") or desc.get("guid", ""),
            ))
            if len(results) >= limit:
                break

        return results
