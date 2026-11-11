from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from leadsets import APIConnectionError, APITimeoutError, InvalidRequestError, Leadsets, RateLimitError
from leadsets._base import backoff

from .conftest import KEY, error_body, search_page

OK = httpx.Response(200, json=search_page([]))


def test_429_honours_retry_after_and_keeps_the_key(ls: Leadsets, mock: respx.MockRouter, sleeps: list[float]) -> None:
    route = mock.post("/v1/people/search").mock(
        side_effect=[httpx.Response(429, json=error_body("too_many_concurrent"), headers={"Retry-After": "2"}), OK]
    )
    res = ls.people.search(limit=5)
    assert route.call_count == 2
    assert len(sleeps) == 1
    assert 2 <= sleeps[0] < 2.3
    keys = [c.request.headers["idempotency-key"] for c in route.calls]
    assert len(keys[0]) == 36
    assert keys[0] == keys[1]
    assert res.last_response is not None
    assert res.last_response.attempts == 2


def test_5xx_backoff(ls: Leadsets, mock: respx.MockRouter, sleeps: list[float]) -> None:
    route = mock.post("/v1/people/search").mock(
        side_effect=[
            httpx.Response(500, json=error_body("internal_error")),
            httpx.Response(503, json=error_body("unavailable")),
            OK,
        ]
    )
    ls.people.search()
    assert route.call_count == 3
    assert 0.375 <= sleeps[0] <= 0.5
    assert 0.75 <= sleeps[1] <= 1.0


def test_network_error_retried(ls: Leadsets, mock: respx.MockRouter, sleeps: list[float]) -> None:
    route = mock.post("/v1/companies/search").mock(side_effect=[httpx.ConnectError("reset"), OK])
    ls.companies.search()
    assert route.call_count == 2
    assert len(sleeps) == 1


def test_network_error_exhausted(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/enrich").mock(side_effect=httpx.ConnectError("reset"))
    with pytest.raises(APIConnectionError):
        ls.people.enrich(email="a@b.co")
    assert route.call_count == 3


def test_timeout(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(APITimeoutError):
        ls.people.search(max_retries=1)
    assert route.call_count == 2


def test_api_error_exhausted(mock: respx.MockRouter, sleeps: list[float]) -> None:
    route = mock.post("/v1/people/search").respond(
        429, json=error_body("window_full", meter="search_records_5h"), headers={"Retry-After": "1"}
    )
    with pytest.raises(RateLimitError):
        Leadsets(KEY, max_retries=1).people.search()
    assert route.call_count == 2


def test_long_retry_after_is_raised_at_once(ls: Leadsets, mock: respx.MockRouter, sleeps: list[float]) -> None:
    route = mock.post("/v1/people/search").mock(
        side_effect=[httpx.Response(429, json=error_body("weekly_limit"), headers={"Retry-After": "86400"}), OK]
    )
    with pytest.raises(RateLimitError) as info:
        ls.people.search()
    assert info.value.retry_after == 86400
    assert route.call_count == 1
    assert sleeps == []


def test_max_retry_delay_configurable(mock: respx.MockRouter, sleeps: list[float]) -> None:
    mock.post("/v1/people/search").mock(
        side_effect=[httpx.Response(429, json=error_body("window_full"), headers={"Retry-After": "90"}), OK]
    )
    Leadsets(KEY, max_retry_delay=120).people.search()
    assert 90 <= sleeps[0] < 90.3


def test_4xx_not_retried(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").respond(400, json=error_body("invalid_request"))
    with pytest.raises(InvalidRequestError):
        ls.people.search()
    assert route.call_count == 1


def test_max_retries_zero(mock: respx.MockRouter, sleeps: list[float]) -> None:
    route = mock.get("/v1/usage").respond(503, json=error_body("unavailable"))
    with pytest.raises(Exception, match="unavailable"):
        Leadsets(KEY, max_retries=0).usage.get()
    assert route.call_count == 1
    with pytest.raises(Exception, match="unavailable"):
        Leadsets(KEY).usage.get(max_retries=0)
    assert route.call_count == 2


def test_backoff() -> None:
    assert 0.375 <= backoff(0) <= 0.5
    assert 3.0 <= backoff(3) <= 4.0
    assert backoff(20) <= 8.0


class TestIdempotency:
    def test_fresh_key_on_every_paid_post(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        any_ok: dict[str, Any] = {"items": [], "next_cursor": None, "request_id": "r", "usage": {}}
        mock.post("/v1/people/search").respond(json=any_ok)
        mock.post("/v1/people/enrich").respond(json={"person": {"person_id": "p"}, "request_id": "r"})
        mock.post("/v1/companies/search").respond(json=any_ok)
        mock.post("/v1/companies/enrich").respond(json={"company": {"company_id": "c"}, "request_id": "r"})
        mock.post("/v1/emails/verify").respond(json={"results": [], "request_id": "r"})
        mock.post("/v1/scrape/company").respond(json={"domain": "a.co", "url": "u", "request_id": "r"})
        mock.post("/v1/scrape/jobs").respond(json={"domain": "a.co", "careers_url": "u", "request_id": "r"})
        ls.people.search()
        ls.people.search()
        ls.people.enrich(email="a@b.co")
        ls.companies.search()
        ls.companies.enrich(domain="a.co")
        ls.emails.verify("a@b.co")
        ls.scrape.company(domain="a.co")
        ls.scrape.jobs(domain="a.co")
        keys = [c.request.headers.get("idempotency-key") for c in mock.calls]
        assert len(keys) == 8
        assert all(k and len(k) == 36 for k in keys)
        assert len(set(keys)) == 8

    def test_caller_key(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/people/search").respond(json=search_page([]))
        res = ls.people.search(idempotency_key="crm-row-42")
        assert route.calls[0].request.headers["idempotency-key"] == "crm-row-42"
        assert res.last_response is not None
        assert res.last_response.idempotency_key == "crm-row-42"

    def test_get_has_no_key(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.get("/v1/usage").respond(json={"plan": "pro", "request_id": "r"})
        ls.usage.get()
        assert "idempotency-key" not in route.calls[0].request.headers
