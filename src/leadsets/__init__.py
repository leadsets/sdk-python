"""Official Python SDK for the Leadsets B2B data API.

>>> import os
>>> from leadsets import Leadsets
>>> ls = Leadsets(os.environ["LEADSETS_KEY"])
>>> res = ls.people.search(function=["revenue"], seniority=["vp", "head"], employees="20-200",
...                        country="US", industry="saas", limit=10)
>>> res.items[0].match_reasons, res.usage
"""

from . import types
from ._base import DEFAULT_BASE_URL
from ._client import AsyncLeadsets, Leadsets
from ._exceptions import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    FreeRecordsExhaustedError,
    IdempotencyConflictError,
    InternalServerError,
    InvalidRequestError,
    LeadsetsError,
    NotFoundError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
    ScrapeUnitsExhaustedError,
    ServiceUnavailableError,
)
from ._exceptions import APIConnectionError as ConnectionError
from ._exceptions import APITimeoutError as TimeoutError
from ._version import __version__

__all__ = [
    "DEFAULT_BASE_URL",
    "APIConnectionError",
    "APIError",
    "APITimeoutError",
    "AsyncLeadsets",
    "AuthenticationError",
    "ConnectionError",
    "FreeRecordsExhaustedError",
    "IdempotencyConflictError",
    "InternalServerError",
    "InvalidRequestError",
    "Leadsets",
    "LeadsetsError",
    "NotFoundError",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "RateLimitError",
    "ScrapeUnitsExhaustedError",
    "ServiceUnavailableError",
    "TimeoutError",
    "__version__",
    "types",
]
