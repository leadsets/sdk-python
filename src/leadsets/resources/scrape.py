from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import httpx

from .._base import clean
from ..types import ScrapeCompanyResponse, ScrapeJobsParams, ScrapeJobsResponse, ScrapeParams
from ._compat import Unpack

if TYPE_CHECKING:
    from .._client import AsyncLeadsets, Leadsets


class Scrape:
    def __init__(self, client: Leadsets) -> None:
        self._client = client

    def company(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[ScrapeParams],
    ) -> ScrapeCompanyResponse:
        """POST /v1/scrape/company. 1 scrape unit per page read (default 1). Paid plans with scrape units."""
        return self._client.request(
            "POST",
            "/scrape/company",
            ScrapeCompanyResponse,
            body=clean(params),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )

    def jobs(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[ScrapeJobsParams],
    ) -> ScrapeJobsResponse:
        """POST /v1/scrape/jobs: open roles from the careers page, job board and LinkedIn, from the website only.
        1 scrape unit per role returned (``limit``, default 25). Paid plans with scrape units."""
        return self._client.request(
            "POST",
            "/scrape/jobs",
            ScrapeJobsResponse,
            body=clean(params),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )


class AsyncScrape:
    def __init__(self, client: AsyncLeadsets) -> None:
        self._client = client

    async def company(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[ScrapeParams],
    ) -> ScrapeCompanyResponse:
        """POST /v1/scrape/company. 1 scrape unit per page read (default 1). Paid plans with scrape units."""
        return await self._client.request(
            "POST",
            "/scrape/company",
            ScrapeCompanyResponse,
            body=clean(params),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )

    async def jobs(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[ScrapeJobsParams],
    ) -> ScrapeJobsResponse:
        """POST /v1/scrape/jobs: open roles from the careers page, job board and LinkedIn, from the website only.
        1 scrape unit per role returned (``limit``, default 25). Paid plans with scrape units."""
        return await self._client.request(
            "POST",
            "/scrape/jobs",
            ScrapeJobsResponse,
            body=clean(params),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )
