from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import httpx

from ..types import UsageResponse

if TYPE_CHECKING:
    from .._client import AsyncLeadsets, Leadsets


class UsageResource:
    def __init__(self, client: Leadsets) -> None:
        self._client = client

    def get(
        self,
        *,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> UsageResponse:
        """GET /v1/usage: what's left in every meter and when each window resets. Free to call."""
        return self._client.request(
            "GET", "/usage", UsageResponse, timeout=timeout, max_retries=max_retries, extra_headers=extra_headers
        )


class AsyncUsageResource:
    def __init__(self, client: AsyncLeadsets) -> None:
        self._client = client

    async def get(
        self,
        *,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> UsageResponse:
        """GET /v1/usage: what's left in every meter and when each window resets. Free to call."""
        return await self._client.request(
            "GET", "/usage", UsageResponse, timeout=timeout, max_retries=max_retries, extra_headers=extra_headers
        )
