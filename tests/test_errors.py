from __future__ import annotations

import httpx
import pytest
import respx

import leadsets
from leadsets import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    FreeRecordsExhaustedError,
    IdempotencyConflictError,
    InternalServerError,
    InvalidRequestError,
    Leadsets,
    LeadsetsError,
    NotFoundError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
    ScrapeUnitsExhaustedError,
    ServiceUnavailableError,
)
from leadsets._exceptions import parse_retry_after

from .conftest import KEY, error_body


def fail(
    mock: respx.MockRouter,
    status: int,
    json: object = None,
    text: str | None = None,
    headers: dict[str, str] | None = None,
) -> APIError:
    route = mock.post("/v1/people/search")
    if text is not None:
        route.respond(status, text=text, headers=headers)
    else:
        route.respond(status, json=json, headers=headers)
    with pytest.raises(APIError) as info:
        Leadsets(KEY, max_retries=0).people.search()
    return info.value


CASES = [
    (400, "invalid_request", InvalidRequestError),
    (401, "unauthorized", AuthenticationError),
    (402, "free_records_exhausted", FreeRecordsExhaustedError),
    (402, "scrape_units_exhausted", ScrapeUnitsExhaustedError),
    (403, "forbidden", PermissionDeniedError),
    (404, "not_found", NotFoundError),
    (409, "idempotency_conflict", IdempotencyConflictError),
    (429, "window_full", RateLimitError),
    (429, "weekly_limit", RateLimitError),
    (429, "too_many_concurrent", RateLimitError),
    (500, "internal_error", InternalServerError),
    (503, "unavailable", ServiceUnavailableError),
]


@pytest.mark.parametrize(("status", "etype", "cls"), CASES)
def test_mapping(mock: respx.MockRouter, status: int, etype: str, cls: type[APIError]) -> None:
    e = fail(mock, status, error_body(etype))
    assert type(e) is cls
    assert isinstance(e, LeadsetsError)
    assert e.status_code == status
    assert e.status == status
    assert e.type == etype
    assert e.message == f"{etype} happened"
    assert e.request_id == "req_err01"
    assert e.charged == 0
    assert "req_err01" in str(e)
    assert etype in repr(e)


def test_payment_and_server_families(mock: respx.MockRouter) -> None:
    assert isinstance(fail(mock, 402, error_body("scrape_units_exhausted")), PaymentRequiredError)
    assert isinstance(fail(mock, 402, error_body("free_records_exhausted")), PaymentRequiredError)
    assert isinstance(fail(mock, 503, error_body("unavailable")), InternalServerError)


def test_status_fallback(mock: respx.MockRouter) -> None:
    assert type(fail(mock, 404, error_body("something_new"))) is NotFoundError
    assert type(fail(mock, 418, error_body("teapot"))) is APIError
    assert type(fail(mock, 502, error_body("bad_gateway"))) is InternalServerError


def test_param(mock: respx.MockRouter) -> None:
    assert fail(mock, 400, error_body("invalid_request", param="employees")).param == "employees"


def test_upgrade_url(mock: respx.MockRouter) -> None:
    e = fail(mock, 403, error_body("forbidden", upgrade_url="https://www.leadsets.ai/pricing"))
    assert isinstance(e, PermissionDeniedError)
    assert e.upgrade_url == "https://www.leadsets.ai/pricing"


def test_rate_limit_fields(mock: respx.MockRouter) -> None:
    e = fail(
        mock,
        429,
        error_body("window_full", meter="search_records_5h", resets_at="2026-11-11T17:00:00Z"),
        headers={"Retry-After": "1200"},
    )
    assert isinstance(e, RateLimitError)
    assert e.retry_after == 1200
    assert e.meter == "search_records_5h"
    assert e.resets_at == "2026-11-11T17:00:00Z"
    assert e.headers["retry-after"] == "1200"


def test_scrape_units_meter(mock: respx.MockRouter) -> None:
    assert fail(mock, 402, error_body("scrape_units_exhausted", meter="scrape_units")).meter == "scrape_units"


def test_non_json_body(mock: respx.MockRouter) -> None:
    e = fail(mock, 502, text="<html>Bad gateway</html>")
    assert isinstance(e, InternalServerError)
    assert e.request_id is None
    assert "Bad gateway" in e.message
    empty = fail(mock, 500, text="")
    assert empty.message == "Request failed with status 500"


def test_connection_errors() -> None:
    assert issubclass(APITimeoutError, APIConnectionError)
    assert issubclass(APIConnectionError, LeadsetsError)
    assert not issubclass(APIConnectionError, APIError)
    assert APIConnectionError().request_id is None
    assert leadsets.ConnectionError is APIConnectionError
    assert leadsets.TimeoutError is APITimeoutError


def test_parse_retry_after() -> None:
    assert parse_retry_after("30") == 30
    assert parse_retry_after(None) is None
    assert parse_retry_after("soon") is None
    now = 1794391200.0  # 2026-11-11T10:00:00Z
    assert parse_retry_after("Wed, 11 Nov 2026 10:00:10 GMT", now=now) == 10


def test_transport_error_is_wrapped(mock: respx.MockRouter) -> None:
    mock.post("/v1/people/search").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(APIConnectionError) as info:
        Leadsets(KEY, max_retries=0).people.search()
    assert isinstance(info.value.__cause__, httpx.ConnectError)
