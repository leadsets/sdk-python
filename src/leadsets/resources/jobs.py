from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING
from urllib.parse import quote

import httpx

from ..types import AsyncJob

if TYPE_CHECKING:
    from .._client import AsyncLeadsets, Leadsets


def _path(job_id: str) -> str:
    if not job_id:
        raise ValueError("jobs.get: job_id is required")
    return f"/jobs/{quote(job_id, safe='')}"


class Jobs:
    def __init__(self, client: Leadsets) -> None:
        self._client = client

    def get(
        self,
        job_id: str,
        *,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> AsyncJob:
        """GET /v1/jobs/{id}: status of an async job."""
        return self._client.request(
            "GET", _path(job_id), AsyncJob, timeout=timeout, max_retries=max_retries, extra_headers=extra_headers
        )


class AsyncJobs:
    def __init__(self, client: AsyncLeadsets) -> None:
        self._client = client

    async def get(
        self,
        job_id: str,
        *,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> AsyncJob:
        """GET /v1/jobs/{id}: status of an async job."""
        return await self._client.request(
            "GET", _path(job_id), AsyncJob, timeout=timeout, max_retries=max_retries, extra_headers=extra_headers
        )
