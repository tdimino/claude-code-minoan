#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""Abstract base class for image sources."""

import sys
from abc import ABC, abstractmethod

import aiohttp

# Add parent dir to path for _well_utils import
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from _well_utils import ImageResult, RateLimiter, get_api_key, warn


class ImageSource(ABC):
    """Base class for all image sources."""

    name: str = ""
    display_name: str = ""
    tier: int = 1
    requires_key: bool = False
    key_env_var: str | None = None
    rate_limit_seconds: float = 0.3
    base_url: str = ""

    def __init__(self) -> None:
        self._limiter = RateLimiter(self.rate_limit_seconds)
        self._api_key: str | None = None
        if self.requires_key and self.key_env_var:
            self._api_key = get_api_key(self.key_env_var)

    def is_available(self) -> bool:
        """Check if this source can be used (key present if required)."""
        if not self.requires_key:
            return True
        return self._api_key is not None

    def status_line(self) -> str:
        """Human-readable status for the `sources` command."""
        if not self.requires_key:
            status = "ready (no key needed)"
        elif self._api_key:
            status = "ready (key set)"
        else:
            status = f"unavailable ({self.key_env_var} not set)"
        return f"  T{self.tier}  {self.display_name:<20s}  {status}"

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int,
        license_filter: str | None,
        session: aiohttp.ClientSession,
    ) -> list[ImageResult]:
        """Search for images. Returns results or empty list on error."""
        ...

    async def _rate_wait(self) -> None:
        await self._limiter.wait()
