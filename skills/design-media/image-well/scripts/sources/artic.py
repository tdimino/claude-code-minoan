#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Art Institute of Chicago image source — 60k+ public-domain works via IIIF.

AIC etiquette (api.artic.edu/docs): 60 req/min anonymous, identify with an
AIC-User-Agent header, pass `fields`, and download images serially — the
download path in well.py serializes artic downloads accordingly.
"""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource

AIC_USER_AGENT = "ImageWell/1.0 (github.com/tdimino)"


class ArticSource(ImageSource):
    name = "artic"
    display_name = "Art Inst. Chicago"
    tier = 1
    requires_key = False
    rate_limit_seconds = 1.0  # 60 requests/minute anonymous limit
    base_url = "https://api.artic.edu/api/v1"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        results: list[ImageResult] = []
        page = 1
        iiif_base = "https://www.artic.edu/iiif/2"
        # Some rows have image_id: null — page until we fill `limit` real ones.
        while len(results) < limit and page <= 3:
            await self._rate_wait()
            params = {
                "q": query,
                "query[term][is_public_domain]": "true",
                "fields": "id,title,image_id,artist_display,date_display,is_public_domain,classification_titles,thumbnail",
                "limit": str(min(limit, 100)),
                "page": str(page),
            }
            try:
                async with session.get(
                    f"{self.base_url}/artworks/search", params=params,
                    headers={"AIC-User-Agent": AIC_USER_AGENT},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        warn(f"artic: HTTP {resp.status}")
                        break
                    data = await resp.json()
            except (aiohttp.ClientError, TimeoutError) as e:
                warn(f"artic: {e}")
                break

            # API returns its IIIF base in every response — prefer it to the hardcode.
            iiif_base = data.get("config", {}).get("iiif_url") or iiif_base
            rows = data.get("data") or []
            if not rows:
                break

            for obj in rows:
                image_id = obj.get("image_id")
                if not image_id or obj.get("is_public_domain") is not True:
                    continue

                title = obj.get("title", "Untitled") or "Untitled"
                date = obj.get("date_display", "") or ""
                thumb_meta = obj.get("thumbnail") or {}

                results.append(ImageResult(
                    source="artic",
                    title=f"{title}" + (f" ({date})" if date else ""),
                    # 843px is AIC's documented preferred download/hotlink size.
                    url=f"{iiif_base}/{image_id}/full/843,/0/default.jpg",
                    thumbnail_url=f"{iiif_base}/{image_id}/full/400,/0/default.jpg",
                    license="PD",  # public domain, not formally CC0; passes --license cc0
                    attribution=obj.get("artist_display", "") or "",
                    width=int(thumb_meta.get("width") or 0),
                    height=int(thumb_meta.get("height") or 0),
                    tags=(obj.get("classification_titles") or [])[:10],
                    source_url=f"https://www.artic.edu/artworks/{obj['id']}",
                ))
                if len(results) >= limit:
                    break

            total_pages = data.get("pagination", {}).get("total_pages", 1)
            if page >= total_pages:
                break
            page += 1

        return results[:limit]
