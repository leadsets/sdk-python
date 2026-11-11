"""Shared request logic for the sync and async clients."""

from __future__ import annotations

import os
import platform
import random
import uuid
from collections.abc import Mapping
from typing import Any, TypeVar

import httpx

from ._exceptions import APIError, LeadsetsError, make_api_error, parse_retry_after
from ._models import Model
from ._version import __version__
from .types import RateLimitInfo, ResponseMeta

DEFAULT_BASE_URL = "https://api.leadsets.ai"
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_MAX_RETRY_DELAY = 60.0

USER_AGENT = f"leadsets-sdk-python/{__version__} (Python {platform.python_version()}; httpx {httpx.__version__})"

M = TypeVar("M", bound=Model)


def _env(name: str) -> str | None:
    v = os.environ.get(name)
    return v.strip() if v and v.strip() else None


def resolve_api_key(api_key: str | None) -> str:
    key = api_key or _env("LEADSETS_API_KEY") or _env("LEADSETS_KEY")
    if not key:
        raise LeadsetsError(
            "No API key. Pass one to Leadsets(api_key) or set the LEADSETS_API_KEY environment variable. "
            "Get a free key at https://www.leadsets.ai/signup."
        )
    return key


def resolve_base_url(base_url: str | None) -> str:
    return (base_url or _env("LEADSETS_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def new_idempotency_key() -> str:
    return str(uuid.uuid4())


def backoff(attempt: int) -> float:
    """Exponential backoff with jitter: ~0.5 s, 1 s, 2 s … capped at 8 s."""
    base: float = min(8.0, 0.5 * 2**attempt)
    return base * (0.75 + random.random() * 0.25)


def clean(params: Mapping[str, Any]) -> dict[str, Any]:
    """Drop unset (None) parameters; turn tuples and other sequences into lists."""
    out: dict[str, Any] = {}
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, (tuple, set, frozenset)):
            v = list(v)
        out[k] = v
    return out


class BaseClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        base_url: str | None,
        max_retries: int,
        timeout: float | httpx.Timeout | None,
        max_retry_delay: float,
        default_headers: Mapping[str, str] | None,
    ) -> None:
        self.api_key = resolve_api_key(api_key)
        self.base_url = resolve_base_url(base_url)
        self.max_retries = max(0, int(max_retries))
        self.timeout = timeout
        self.max_retry_delay = max(0.0, float(max_retry_delay))
        self._default_headers = dict(default_headers or {})

    def _headers(
        self, *, has_body: bool, idempotency_key: str | None, extra: Mapping[str, str] | None
    ) -> dict[str, str]:
        h = {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            **self._default_headers,
            **(extra or {}),
            "Authorization": f"Bearer {self.api_key}",
        }
        if has_body:
            h["Content-Type"] = "application/json"
        if idempotency_key:
            h["Idempotency-Key"] = idempotency_key
        return h

    def _url(self, path: str) -> str:
        return f"{self.base_url}/v1{path}"

    def _retry_delay(self, err: APIError | None, attempt: int) -> float | None:
        """Seconds to wait before retrying, or None to not retry. ``err`` is None for network errors."""
        if err is None:
            return backoff(attempt)
        if not (err.status_code in (408, 429) or err.status_code >= 500):
            return None
        if err.retry_after is not None:
            if err.retry_after > self.max_retry_delay:
                return None
            return err.retry_after + random.random() * 0.25
        return backoff(attempt)

    @staticmethod
    def _parse(cls: type[M], response: httpx.Response, idempotency_key: str | None, attempts: int) -> M:
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        obj = cls.from_dict(data)
        if hasattr(obj, "last_response"):
            object.__setattr__(obj, "last_response", response_meta(response, data, idempotency_key, attempts))
        return obj

    @staticmethod
    def _error(response: httpx.Response) -> APIError:
        return make_api_error(response)


def _int(v: str | None) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        try:
            return int(float(v))
        except ValueError:
            return None


def rate_limit_info(h: httpx.Headers) -> RateLimitInfo:
    return RateLimitInfo(
        records_remaining=_int(h.get("x-leadsets-records-remaining")),
        requests_remaining=_int(h.get("x-leadsets-requests-remaining")),
        weekly_remaining=_int(h.get("x-leadsets-weekly-remaining")),
        free_remaining=_int(h.get("x-leadsets-free-remaining")),
        retry_after=parse_retry_after(h.get("retry-after")),
    )


def response_meta(
    response: httpx.Response, data: dict[str, Any], idempotency_key: str | None, attempts: int
) -> ResponseMeta:
    rid = data.get("request_id")
    return ResponseMeta(
        status_code=response.status_code,
        headers=response.headers,
        request_id=rid if isinstance(rid, str) else None,
        idempotency_key=idempotency_key,
        idempotent_replayed=response.headers.get("idempotent-replayed") == "true",
        rate_limit=rate_limit_info(response.headers),
        attempts=attempts,
    )
