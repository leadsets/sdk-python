from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Literal

import httpx

from ._base import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RETRY_DELAY,
    DEFAULT_TIMEOUT,
    BaseClient,
    M,
    new_idempotency_key,
)
from ._exceptions import APIConnectionError, APIError, APITimeoutError
from .resources.companies import AsyncCompanies, Companies
from .resources.emails import AsyncEmails, Emails
from .resources.jobs import AsyncJobs, Jobs
from .resources.people import AsyncPeople, People
from .resources.scrape import AsyncScrape, Scrape
from .resources.usage import AsyncUsageResource, UsageResource

Method = Literal["GET", "POST"]


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


async def _async_sleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


class Leadsets(BaseClient):
    """The Leadsets API client.

    >>> ls = Leadsets(os.environ["LEADSETS_KEY"])
    >>> res = ls.people.search(function=["revenue"], country="US", limit=10)
    """

    people: People
    companies: Companies
    emails: Emails
    scrape: Scrape
    jobs: Jobs
    usage: UsageResource

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        max_retry_delay: float = DEFAULT_MAX_RETRY_DELAY,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """
        Args:
            api_key: Your API key (``ls_live_…``). Defaults to ``LEADSETS_API_KEY`` or ``LEADSETS_KEY``.
            base_url: Defaults to https://api.leadsets.ai (or ``LEADSETS_BASE_URL``).
            max_retries: Retries on 429, 5xx, timeouts and network errors. Default 2.
            timeout: Per-attempt timeout in seconds. Default 120.
            max_retry_delay: The longest ``Retry-After`` (seconds) to wait for before retrying.
                A 429 asking for longer (a weekly limit, say) is raised at once. Default 60.
            default_headers: Headers sent with every request.
            http_client: Your own ``httpx.Client`` (proxies, transports…).
        """
        super().__init__(
            api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            max_retry_delay=max_retry_delay,
            default_headers=default_headers,
        )
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)
        self.people = People(self)
        self.companies = Companies(self)
        self.emails = Emails(self)
        self.scrape = Scrape(self)
        self.jobs = Jobs(self)
        self.usage = UsageResource(self)

    def request(
        self,
        method: Method,
        path: str,
        cls: type[M],
        *,
        body: Mapping[str, Any] | None = None,
        idempotent: bool = False,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> M:
        key = idempotency_key or (new_idempotency_key() if idempotent else None)
        headers = self._headers(has_body=body is not None, idempotency_key=key, extra=extra_headers)
        retries = self.max_retries if max_retries is None else max(0, max_retries)
        t = self.timeout if timeout is None else timeout
        for attempt in range(retries + 1):
            try:
                res = self._client.request(method, self._url(path), json=body, headers=headers, timeout=t)
            except httpx.TimeoutException as e:
                if attempt < retries:
                    _sleep(self._retry_delay(None, attempt) or 0)
                    continue
                raise APITimeoutError() from e
            except httpx.TransportError as e:
                if attempt < retries:
                    _sleep(self._retry_delay(None, attempt) or 0)
                    continue
                raise APIConnectionError() from e
            if res.is_success:
                return self._parse(cls, res, key, attempt + 1)
            err: APIError = self._error(res)
            delay = self._retry_delay(err, attempt)
            if attempt < retries and delay is not None:
                _sleep(delay)
                continue
            raise err
        raise AssertionError("unreachable")  # pragma: no cover

    def close(self) -> None:
        """Close the underlying HTTP client (if the SDK created it)."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Leadsets:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        self.close()


class AsyncLeadsets(BaseClient):
    """The async Leadsets API client.

    >>> async with AsyncLeadsets() as ls:
    ...     res = await ls.people.search(function=["revenue"], country="US", limit=10)
    """

    people: AsyncPeople
    companies: AsyncCompanies
    emails: AsyncEmails
    scrape: AsyncScrape
    jobs: AsyncJobs
    usage: AsyncUsageResource

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        max_retry_delay: float = DEFAULT_MAX_RETRY_DELAY,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Same arguments as :class:`Leadsets`; ``http_client`` is an ``httpx.AsyncClient``."""
        super().__init__(
            api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            max_retry_delay=max_retry_delay,
            default_headers=default_headers,
        )
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=timeout)
        self.people = AsyncPeople(self)
        self.companies = AsyncCompanies(self)
        self.emails = AsyncEmails(self)
        self.scrape = AsyncScrape(self)
        self.jobs = AsyncJobs(self)
        self.usage = AsyncUsageResource(self)

    async def request(
        self,
        method: Method,
        path: str,
        cls: type[M],
        *,
        body: Mapping[str, Any] | None = None,
        idempotent: bool = False,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> M:
        key = idempotency_key or (new_idempotency_key() if idempotent else None)
        headers = self._headers(has_body=body is not None, idempotency_key=key, extra=extra_headers)
        retries = self.max_retries if max_retries is None else max(0, max_retries)
        t = self.timeout if timeout is None else timeout
        for attempt in range(retries + 1):
            try:
                res = await self._client.request(method, self._url(path), json=body, headers=headers, timeout=t)
            except httpx.TimeoutException as e:
                if attempt < retries:
                    await _async_sleep(self._retry_delay(None, attempt) or 0)
                    continue
                raise APITimeoutError() from e
            except httpx.TransportError as e:
                if attempt < retries:
                    await _async_sleep(self._retry_delay(None, attempt) or 0)
                    continue
                raise APIConnectionError() from e
            if res.is_success:
                return self._parse(cls, res, key, attempt + 1)
            err: APIError = self._error(res)
            delay = self._retry_delay(err, attempt)
            if attempt < retries and delay is not None:
                await _async_sleep(delay)
                continue
            raise err
        raise AssertionError("unreachable")  # pragma: no cover

    async def aclose(self) -> None:
        """Close the underlying HTTP client (if the SDK created it)."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncLeadsets:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.aclose()
