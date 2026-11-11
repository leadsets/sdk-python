from __future__ import annotations

import json

import httpx
import pytest
import respx

from leadsets import APIConnectionError, AsyncLeadsets, NotFoundError, RateLimitError
from leadsets.types import PeopleSearchResponse

from .conftest import KEY, error_body, person, search_page
from .test_pagination import pages


async def test_every_endpoint(als: AsyncLeadsets, mock: respx.MockRouter) -> None:
    mock.post("/v1/people/search").respond(json=search_page([person()]))
    mock.post("/v1/people/enrich").respond(json={"person": person(), "matched_by": "email", "request_id": "r"})
    mock.post("/v1/companies/search").respond(
        json={"items": [{"company_id": "c"}], "next_cursor": None, "request_id": "r"}
    )
    mock.post("/v1/companies/enrich").respond(json={"company": {"company_id": "c", "name": "N"}, "request_id": "r"})
    mock.post("/v1/emails/verify").respond(
        json={"results": [{"email": "a@b.co", "status": "invalid"}], "request_id": "r"}
    )
    mock.post("/v1/scrape/company").respond(json={"domain": "a.co", "url": "u", "name": "A", "request_id": "r"})
    mock.post("/v1/scrape/jobs").respond(json={"domain": "a.co", "careers_url": "u", "count": 0, "request_id": "r"})
    mock.get("/v1/jobs/j1").respond(json={"id": "j1", "status": "running", "request_id": "r"})
    mock.get("/v1/usage").respond(json={"plan": "solo", "request_id": "r"})

    res = await als.people.search(function=["revenue"], country="US", limit=10)
    assert isinstance(res, PeopleSearchResponse)
    assert res.items[0].match_reasons
    assert (await als.people.enrich(email="maya@northwind.io")).matched_by == "email"
    assert (await als.companies.search(industry="saas")).items[0].company_id == "c"
    assert (await als.companies.enrich(domain="a.co")).company.name == "N"
    assert (await als.emails.verify(["a@b.co"])).results[0].status == "invalid"
    assert (await als.scrape.company(domain="a.co")).name == "A"
    assert (await als.scrape.jobs(domain="a.co")).count == 0
    assert (await als.jobs.get("j1")).status == "running"
    assert (await als.usage.get()).plan == "solo"
    posts = [c.request for c in mock.calls if c.request.method == "POST"]
    assert all(len(r.headers["idempotency-key"]) == 36 for r in posts)
    assert json.loads(mock.calls[0].request.content) == {"function": ["revenue"], "country": "US", "limit": 10}


async def test_async_retry(als: AsyncLeadsets, mock: respx.MockRouter, sleeps: list[float]) -> None:
    route = mock.post("/v1/people/search").mock(
        side_effect=[
            httpx.Response(429, json=error_body("window_full"), headers={"Retry-After": "3"}),
            httpx.ConnectError("reset"),
            httpx.Response(200, json=search_page([])),
        ]
    )
    res = await als.people.search()
    assert route.call_count == 3
    assert 3 <= sleeps[0] < 3.3
    keys = {c.request.headers["idempotency-key"] for c in route.calls}
    assert len(keys) == 1
    assert res.last_response is not None
    assert res.last_response.attempts == 3


async def test_async_errors(als: AsyncLeadsets, mock: respx.MockRouter) -> None:
    mock.post("/v1/people/enrich").respond(404, json=error_body("not_found"))
    with pytest.raises(NotFoundError) as info:
        await als.people.enrich(email="x@y.co")
    assert info.value.request_id == "req_err01"
    mock.post("/v1/people/search").respond(429, json=error_body("weekly_limit"), headers={"Retry-After": "99999"})
    with pytest.raises(RateLimitError):
        await als.people.search()
    mock.get("/v1/usage").mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(APIConnectionError):
        await als.usage.get(max_retries=0)


async def test_async_pagination(als: AsyncLeadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").mock(side_effect=pages(3, 2))
    ids = [p.person_id async for p in als.people.search_all(limit=2, max_items=5)]
    assert ids == ["p1-0", "p1-1", "p2-0", "p2-1", "p3-0"]
    assert [json.loads(c.request.content)["limit"] for c in route.calls] == [2, 2, 1]
    mock.post("/v1/companies/search").respond(
        json={"items": [{"company_id": "c"}], "next_cursor": "c_2", "request_id": "r"}
    )
    n = 0
    async for page in als.companies.search_pages(max_pages=1):
        n += 1
        assert page.request_id
    assert n == 1


async def test_async_env_key(mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEADSETS_KEY", KEY)
    route = mock.get("/v1/usage").respond(json={"plan": "pro", "request_id": "r"})
    async with AsyncLeadsets() as c:
        await c.usage.get()
    assert route.calls[0].request.headers["authorization"] == f"Bearer {KEY}"
