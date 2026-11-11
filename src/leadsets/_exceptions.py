"""Error hierarchy.

::

    LeadsetsError
    ├── APIError                        the API answered with an error status
    │   ├── InvalidRequestError         400 invalid_request
    │   ├── AuthenticationError         401 unauthorized
    │   ├── PaymentRequiredError        402
    │   │   ├── FreeRecordsExhaustedError    free_records_exhausted
    │   │   └── ScrapeUnitsExhaustedError    scrape_units_exhausted
    │   ├── PermissionDeniedError       403 forbidden (upgrade_url)
    │   ├── NotFoundError               404 not_found
    │   ├── IdempotencyConflictError    409 idempotency_conflict
    │   ├── RateLimitError              429 window_full, weekly_limit, too_many_concurrent
    │   └── InternalServerError         5xx internal_error
    │       └── ServiceUnavailableError      503 unavailable
    └── APIConnectionError              the request never got an answer
        └── APITimeoutError             ...because it timed out
"""

from __future__ import annotations

import email.utils
import math
import time
from collections.abc import Mapping
from typing import Any

import httpx

__all__ = [
    "APIConnectionError",
    "APIError",
    "APITimeoutError",
    "AuthenticationError",
    "FreeRecordsExhaustedError",
    "IdempotencyConflictError",
    "InternalServerError",
    "InvalidRequestError",
    "LeadsetsError",
    "NotFoundError",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "RateLimitError",
    "ScrapeUnitsExhaustedError",
    "ServiceUnavailableError",
]


class LeadsetsError(Exception):
    """Base class for every error the SDK raises."""

    request_id: str | None

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.request_id = request_id


class APIError(LeadsetsError):
    """The API answered with an error status."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        error: Mapping[str, Any] | None,
        request_id: str | None,
        headers: httpx.Headers,
        body: Any,
    ) -> None:
        super().__init__(message, request_id=request_id)
        self.status_code = status_code
        #: The ``error`` object of the response.
        self.error: dict[str, Any] = dict(error or {})
        #: Machine-readable ``error.type``, e.g. ``"window_full"``.
        self.type: str | None = _str(self.error.get("type"))
        #: The field a 400 refers to.
        self.param: str | None = _str(self.error.get("param"))
        #: The meter that ran out, e.g. ``"search_records_5h"``.
        self.meter: str | None = _str(self.error.get("meter"))
        #: When the meter's window frees up (ISO 8601).
        self.resets_at: str | None = _str(self.error.get("resets_at"))
        #: Always 0: errors never count records.
        charged = self.error.get("charged")
        self.charged: int | None = charged if isinstance(charged, int) else None
        #: Seconds to wait, from the ``Retry-After`` header.
        self.retry_after: float | None = parse_retry_after(headers.get("retry-after"))
        self.headers = headers
        #: The full parsed response body.
        self.body = body

    @property
    def status(self) -> int:
        """Alias of :attr:`status_code`."""
        return self.status_code

    def __str__(self) -> str:
        parts = [f"{self.status_code}"]
        if self.type:
            parts.append(self.type)
        s = f"[{' '.join(parts)}] {self.message}"
        if self.request_id:
            s += f" (request_id: {self.request_id})"
        return s

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(status_code={self.status_code!r}, type={self.type!r}, "
            f"message={self.message!r}, request_id={self.request_id!r})"
        )


class InvalidRequestError(APIError):
    """400 ``invalid_request``: a value isn't valid. ``param`` names the field."""


class AuthenticationError(APIError):
    """401 ``unauthorized``: missing, invalid, revoked or expired key."""


class PaymentRequiredError(APIError):
    """402: a one-time balance is used up."""


class FreeRecordsExhaustedError(PaymentRequiredError):
    """402 ``free_records_exhausted``: the Free plan's records are used up."""


class ScrapeUnitsExhaustedError(PaymentRequiredError):
    """402 ``scrape_units_exhausted``: no scrape units left."""


class PermissionDeniedError(APIError):
    """403 ``forbidden``. ``upgrade_url`` is set when a plan change would allow the call."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.upgrade_url: str | None = _str(self.error.get("upgrade_url"))


class NotFoundError(APIError):
    """404 ``not_found``: nothing found for that input. Nothing was counted."""


class IdempotencyConflictError(APIError):
    """409 ``idempotency_conflict``: same Idempotency-Key with a different body, or still running."""


class RateLimitError(APIError):
    """429 ``window_full``, ``weekly_limit`` or ``too_many_concurrent``."""


class InternalServerError(APIError):
    """5xx ``internal_error``."""


class ServiceUnavailableError(InternalServerError):
    """503 ``unavailable``."""


class APIConnectionError(LeadsetsError):
    """The request got no answer (DNS, connection refused, reset…)."""

    def __init__(self, message: str = "Could not reach the Leadsets API.") -> None:
        super().__init__(message)


class APITimeoutError(APIConnectionError):
    """The request timed out."""

    def __init__(self, message: str = "The request to the Leadsets API timed out.") -> None:
        super().__init__(message)


_BY_TYPE: dict[str, type[APIError]] = {
    "invalid_request": InvalidRequestError,
    "unauthorized": AuthenticationError,
    "free_records_exhausted": FreeRecordsExhaustedError,
    "scrape_units_exhausted": ScrapeUnitsExhaustedError,
    "forbidden": PermissionDeniedError,
    "not_found": NotFoundError,
    "idempotency_conflict": IdempotencyConflictError,
    "window_full": RateLimitError,
    "weekly_limit": RateLimitError,
    "too_many_concurrent": RateLimitError,
    "internal_error": InternalServerError,
    "unavailable": ServiceUnavailableError,
}


def _by_status(status: int) -> type[APIError]:
    if status in (400, 413, 422):
        return InvalidRequestError
    if status == 401:
        return AuthenticationError
    if status == 402:
        return PaymentRequiredError
    if status == 403:
        return PermissionDeniedError
    if status == 404:
        return NotFoundError
    if status == 409:
        return IdempotencyConflictError
    if status == 429:
        return RateLimitError
    if status == 503:
        return ServiceUnavailableError
    if status >= 500:
        return InternalServerError
    return APIError


def make_api_error(response: httpx.Response) -> APIError:
    """The most specific error class for an error response."""
    text = response.text
    try:
        body: Any = response.json() if text else None
    except ValueError:
        body = None
    obj = body if isinstance(body, dict) else {}
    error = obj.get("error") if isinstance(obj.get("error"), dict) else None
    if error is None and text and body is None:
        error = {"message": text[:500]}
    request_id = obj.get("request_id") if isinstance(obj.get("request_id"), str) else None
    etype = error.get("type") if error else None
    cls = (_BY_TYPE.get(etype) if isinstance(etype, str) else None) or _by_status(response.status_code)
    message = (error or {}).get("message") or f"Request failed with status {response.status_code}"
    return cls(
        str(message),
        status_code=response.status_code,
        error=error,
        request_id=request_id,
        headers=response.headers,
        body=body if body is not None else text,
    )


def parse_retry_after(value: str | None, now: float | None = None) -> float | None:
    """``Retry-After`` as seconds: a number of seconds or an HTTP date."""
    if value is None or not value.strip():
        return None
    try:
        n = float(value)
        if math.isfinite(n):
            return max(0.0, n)
        return None
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    current = time.time() if now is None else now
    return float(max(0, math.ceil(dt.timestamp() - current)))


def _str(v: object) -> str | None:
    return v if isinstance(v, str) else None
