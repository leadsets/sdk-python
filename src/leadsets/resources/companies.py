from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping
from typing import TYPE_CHECKING, Any

import httpx

from .._base import clean
from .._pagination import aiter_pages, iter_pages
from ..types import CompaniesSearchParams, CompaniesSearchResponse, Company, CompanyEnrichParams, CompanyEnrichResponse
from ._compat import Unpack

if TYPE_CHECKING:
    from .._client import AsyncLeadsets, Leadsets


class Companies:
    def __init__(self, client: Leadsets) -> None:
        self._client = client

    def search(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CompaniesSearchParams],
    ) -> CompaniesSearchResponse:
        """POST /v1/companies/search. 1 search record per record returned; empty results use none."""
        return self._client.request(
            "POST",
            "/companies/search",
            CompaniesSearchResponse,
            body=clean(params),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )

    def search_pages(
        self,
        *,
        max_items: int | None = None,
        max_pages: int | None = None,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CompaniesSearchParams],
    ) -> Iterator[CompaniesSearchResponse]:
        """Every page of results, following ``next_cursor``."""

        def fetch(body: dict[str, Any], key: str | None) -> CompaniesSearchResponse:
            return self._client.request(
                "POST",
                "/companies/search",
                CompaniesSearchResponse,
                body=body,
                idempotent=True,
                idempotency_key=key,
                timeout=timeout,
                max_retries=max_retries,
                extra_headers=extra_headers,
            )

        return iter_pages(
            fetch, clean(params), max_items=max_items, max_pages=max_pages, idempotency_key=idempotency_key
        )

    def search_all(
        self,
        *,
        max_items: int | None = None,
        max_pages: int | None = None,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CompaniesSearchParams],
    ) -> Iterator[Company]:
        """Every matching company, page after page. ``max_items`` caps what you pay for."""
        for page in self.search_pages(
            max_items=max_items,
            max_pages=max_pages,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
            **params,
        ):
            yield from page.items

    def enrich(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CompanyEnrichParams],
    ) -> CompanyEnrichResponse:
        """POST /v1/companies/enrich. 1 enrichment record when found; 404 uses none."""
        return self._client.request(
            "POST",
            "/companies/enrich",
            CompanyEnrichResponse,
            body=clean(params),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )


class AsyncCompanies:
    def __init__(self, client: AsyncLeadsets) -> None:
        self._client = client

    async def search(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CompaniesSearchParams],
    ) -> CompaniesSearchResponse:
        """POST /v1/companies/search. 1 search record per record returned; empty results use none."""
        return await self._client.request(
            "POST",
            "/companies/search",
            CompaniesSearchResponse,
            body=clean(params),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )

    def search_pages(
        self,
        *,
        max_items: int | None = None,
        max_pages: int | None = None,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CompaniesSearchParams],
    ) -> AsyncIterator[CompaniesSearchResponse]:
        """Every page of results, following ``next_cursor``."""

        async def fetch(body: dict[str, Any], key: str | None) -> CompaniesSearchResponse:
            return await self._client.request(
                "POST",
                "/companies/search",
                CompaniesSearchResponse,
                body=body,
                idempotent=True,
                idempotency_key=key,
                timeout=timeout,
                max_retries=max_retries,
                extra_headers=extra_headers,
            )

        return aiter_pages(
            fetch, clean(params), max_items=max_items, max_pages=max_pages, idempotency_key=idempotency_key
        )

    async def search_all(
        self,
        *,
        max_items: int | None = None,
        max_pages: int | None = None,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CompaniesSearchParams],
    ) -> AsyncIterator[Company]:
        """Every matching company, page after page. ``max_items`` caps what you pay for."""
        async for page in self.search_pages(
            max_items=max_items,
            max_pages=max_pages,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
            **params,
        ):
            for item in page.items:
                yield item

    async def enrich(
        self,
        *,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        **params: Unpack[CompanyEnrichParams],
    ) -> CompanyEnrichResponse:
        """POST /v1/companies/enrich. 1 enrichment record when found; 404 uses none."""
        return await self._client.request(
            "POST",
            "/companies/enrich",
            CompanyEnrichResponse,
            body=clean(params),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )
