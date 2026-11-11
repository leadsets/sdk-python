from __future__ import annotations

import json
from typing import Any

import httpx
import respx

from leadsets import Leadsets

from .conftest import person, search_page


def pages(n: int, per_page: int) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        cursor = body.get("cursor")
        page = int(cursor[2:]) if cursor else 1
        count = min(per_page, body.get("limit", 25))
        items = [person(f"p{page}-{i}") for i in range(count)]
        return httpx.Response(200, json=search_page(items, f"c_{page + 1}" if page < n else None, f"req_{page}"))

    return handler


def bodies(route: respx.Route) -> list[dict[str, Any]]:
    return [json.loads(c.request.content) for c in route.calls]


def test_search_all_follows_cursor(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").mock(side_effect=pages(3, 2))
    ids = [p.person_id for p in ls.people.search_all(country="US", limit=2)]
    assert ids == ["p1-0", "p1-1", "p2-0", "p2-1", "p3-0", "p3-1"]
    assert [b.get("cursor") for b in bodies(route)] == [None, "c_2", "c_3"]
    assert all(b["country"] == "US" for b in bodies(route))


def test_max_items_trims_the_last_page(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").mock(side_effect=pages(10, 25))
    out = list(ls.people.search_all(limit=25, max_items=30))
    assert len(out) == 30
    assert [b["limit"] for b in bodies(route)] == [25, 5]


def test_max_pages(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").mock(side_effect=pages(10, 2))
    assert len(list(ls.people.search_all(limit=2, max_pages=2))) == 4
    assert route.call_count == 2


def test_break_stops_fetching(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").mock(side_effect=pages(10, 2))
    for _ in ls.people.search_all(limit=2):
        break
    assert route.call_count == 1


def test_search_pages_and_derived_keys(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").mock(side_effect=pages(3, 1))
    seen = []
    for page in ls.people.search_pages(limit=1, idempotency_key="run-7"):
        seen.append(page.request_id)
        assert page.usage.search_records_counted == 1
        assert page.last_response is not None
    assert seen == ["req_1", "req_2", "req_3"]
    assert [c.request.headers["idempotency-key"] for c in route.calls] == ["run-7", "run-7-p2", "run-7-p3"]


def test_companies_search_all(ls: Leadsets, mock: respx.MockRouter) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        cursor = json.loads(request.content).get("cursor")
        return httpx.Response(
            200,
            json={
                "items": [{"company_id": cursor or "first"}],
                "next_cursor": None if cursor else "c_next",
                "request_id": "r",
            },
        )

    mock.post("/v1/companies/search").mock(side_effect=handler)
    assert [c.company_id for c in ls.companies.search_all(industry="saas")] == ["first", "c_next"]
    assert len(list(ls.companies.search_pages())) == 2


def test_empty_page_stops(ls: Leadsets, mock: respx.MockRouter) -> None:
    route = mock.post("/v1/people/search").respond(json=search_page([], cursor="c_x"))
    assert list(ls.people.search_all()) == []
    assert route.call_count == 1
