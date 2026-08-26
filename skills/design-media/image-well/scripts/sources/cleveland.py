#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Cleveland Museum of Art image source — 37k+ CC0 open-access works. Single-step search."""

import sys

import aiohttp

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, warn
from sources.base import ImageSource


class ClevelandSource(ImageSource):
    name = "cleveland"
    display_name = "Cleveland Museum"
    tier = 1
    requires_key = False
    rate_limit_seconds = 0.3
    base_url = "https://openaccess-api.clevelandart.org/api/artworks/"

    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        results: list[ImageResult] = []
        skip = 0
        # Verified live: `cc0=` behaves identically to the documented bare `cc0`
        # flag, and has_image=1 rows all come back CC0 anyway — the per-row
        # share_license_status check below is the authoritative gate.
        while len(results) < limit and skip < limit * 3:
            await self._rate_wait()
            params = {
                "q": query,
                "has_image": "1",
                "cc0": "",
                "limit": str(min(limit, 100)),
                "skip": str(skip),
            }
            try:
                async with session.get(
                    self.base_url, params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        warn(f"cleveland: HTTP {resp.status}")
                        break
                    data = await resp.json()
            except (aiohttp.ClientError, TimeoutError) as e:
                warn(f"cleveland: {e}")
                break

            rows = data.get("data") or []
            if not rows:
                break
            skip += len(rows)

            for obj in rows:
                if obj.get("share_license_status") != "CC0":
                    continue
                images = obj.get("images") or {}
                web = images.get("web") or {}
                prnt = images.get("print") or {}
                # print (~3400px JPEG) for download, web (~900px) for preview;
                # skip the archival TIFF in `full` entirely.
                url = prnt.get("url") or web.get("url") or ""
                if not url:
                    continue
                chosen = prnt if prnt.get("url") else web

                title = obj.get("title", "Untitled") or "Untitled"
                date = obj.get("creation_date", "") or ""
                creators = obj.get("creators") or []
                attribution = "; ".join(
                    c.get("description", "") for c in creators if c.get("description")
                )

                tags: list[str] = []
                for t in (obj.get("culture") or []) + [obj.get("type"), obj.get("department"), obj.get("collection")]:
                    if t and t not in tags:
                        tags.append(t)

                accession = obj.get("accession_number", "")
                results.append(ImageResult(
                    source="cleveland",
                    title=f"{title}" + (f" ({date})" if date else ""),
                    url=url,
                    thumbnail_url=web.get("url", "") or url,
                    license="CC0",
                    attribution=attribution,
                    width=int(chosen.get("width") or 0),
                    height=int(chosen.get("height") or 0),
                    tags=tags[:10],
                    source_url=obj.get("url", "") or (f"https://www.clevelandart.org/art/{accession}" if accession else ""),
                ))
                if len(results) >= limit:
                    break

            if skip >= data.get("info", {}).get("total", 0):
                break

        return results[:limit]
