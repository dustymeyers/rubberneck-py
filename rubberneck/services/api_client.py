"""Asynchronous client for the versioned D&D 5e SRD API."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse

import aiohttp

SRD_API_ORIGIN = "https://www.dnd5eapi.co"
SRD_API_VERSION_PATH = "/api/2014"


class DnDAPIError(RuntimeError):
    """Raised when the SRD API cannot satisfy a request."""


class ResourceNotFound(DnDAPIError):
    """Raised when an SRD resource does not exist."""


@dataclass(frozen=True)
class ResourceReference:
    index: str
    name: str
    url: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ResourceReference":
        return cls(index=value["index"], name=value["name"], url=value["url"])


def canonical_srd_url(path: str | None) -> str | None:
    """Return a safe, versioned dnd5eapi.co resource URL."""
    if not path:
        return None

    parsed = urlparse(path)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme == "https" and parsed.netloc == "www.dnd5eapi.co":
            return path
        return None

    normalized = f"/{path.lstrip('/')}"
    if normalized.startswith(f"{SRD_API_VERSION_PATH}/"):
        return f"{SRD_API_ORIGIN}{normalized}"
    if normalized.startswith("/api/"):
        return None
    return f"{SRD_API_ORIGIN}{SRD_API_VERSION_PATH}{normalized}"


class DnDAPI:
    """Small generic API client with a process-local TTL cache.

    The client deliberately has no Redis dependency. A shared cache can be added
    behind the same interface later if deployment needs it.
    """

    def __init__(
        self,
        base_url: str = "https://www.dnd5eapi.co/api/2014",
        cache_ttl: float = 3600,
        timeout: float = 10,
        session_factory: Callable[..., Any] = aiohttp.ClientSession,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_ttl = cache_ttl
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session_factory = session_factory
        self._cache: dict[str, tuple[float, Any]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def list_resources(self, endpoint: str) -> list[ResourceReference]:
        payload = await self.get(endpoint)
        return [
            ResourceReference.from_dict(item) for item in payload.get("results", [])
        ]

    async def get_resource(self, endpoint: str, index: str) -> dict[str, Any]:
        return await self.get(f"{endpoint}/{self.normalise_index(index)}")

    async def get(self, path: str) -> Any:
        path = path.strip("/")
        cached = self._cache.get(path)
        now = time.monotonic()
        if cached and cached[0] > now:
            return cached[1]

        lock = self._locks.setdefault(path, asyncio.Lock())
        async with lock:
            cached = self._cache.get(path)
            now = time.monotonic()
            if cached and cached[0] > now:
                return cached[1]
            payload = await self._request(path)
            self._cache[path] = (now + self.cache_ttl, payload)
            return payload

    async def _request(self, path: str) -> Any:
        url = f"{self.base_url}/{path}"
        try:
            async with self._session_factory(timeout=self.timeout) as session:
                async with session.get(
                    url, headers={"Accept": "application/json"}
                ) as response:
                    if response.status == 404:
                        raise ResourceNotFound(f"No SRD resource found for '{path}'.")
                    if response.status >= 400:
                        detail = await response.text()
                        raise DnDAPIError(
                            f"SRD API returned {response.status}: {detail[:200]}"
                        )
                    return await response.json()
        except (ResourceNotFound, DnDAPIError):
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise DnDAPIError("The SRD API is temporarily unavailable.") from exc

    @staticmethod
    def normalise_index(value: str) -> str:
        return "-".join(value.strip().lower().replace("_", " ").split())
