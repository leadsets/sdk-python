from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
import respx

import leadsets._client as client_module
from leadsets import AsyncLeadsets, Leadsets

KEY = "ls_live_test0000000000000000"
BASE = "https://api.leadsets.ai"
USAGE = {"search_records_counted": 1, "search_records_left_5h": 499, "search_requests_left_5h": 2499}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("LEADSETS_API_KEY", "LEADSETS_KEY", "LEADSETS_BASE_URL"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records retry sleeps instead of sleeping."""
    calls: list[float] = []

    def fake(seconds: float) -> None:
        calls.append(seconds)

    async def afake(seconds: float) -> None:
        calls.append(seconds)

    monkeypatch.setattr(client_module, "_sleep", fake)
    monkeypatch.setattr(client_module, "_async_sleep", afake)
    return calls


@pytest.fixture
def mock() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
def ls(sleeps: list[float]) -> Iterator[Leadsets]:
    with Leadsets(KEY) as c:
        yield c


@pytest.fixture
async def als(sleeps: list[float]) -> Any:
    async with AsyncLeadsets(KEY) as c:
        yield c


def person(pid: str = "6f1c0000-0000-4000-8000-000000000001") -> dict[str, Any]:
    return {
        "person_id": pid,
        "full_name": "Maya Chen",
        "first_name": "Maya",
        "last_name": "Chen",
        "title": "VP Sales",
        "seniority": "vp",
        "seniority_detail": "vp",
        "function": "revenue",
        "function_detail": "sales",
        "linkedin_url": "https://www.linkedin.com/in/mayachen",
        "location": {"country": "US", "region": "CA", "city": "San Francisco"},
        "company": {
            "company_id": "c1",
            "name": "Northwind Analytics",
            "domain": "northwind.io",
            "industry": "SaaS",
            "employees": 120,
            "employee_range": "51-200",
        },
        "email": {
            "address": "maya@northwind.io",
            "status": "verified",
            "type": "business",
            "confidence": 0.95,
            "checked_at": "2026-11-02T00:00:00Z",
            "verified_by": "leadsets",
            "mx_provider": "google",
        },
        "match_reasons": ["function", "seniority", "size", "industry", "country"],
        "refreshed_at": "2026-11-01T00:00:00Z",
        "confirmed_at": "2026-11-01T00:00:00Z",
        "stale_after_at": "2027-01-05T00:00:00Z",
        "stale": False,
        "sources": {"title": {"source": "licensed", "seen_at": "2026-11-01T00:00:00Z", "confidence": 0.9}},
        "something_new": {"x": 1},
    }


def error_body(etype: str, **extra: Any) -> dict[str, Any]:
    return {"error": {"type": etype, "message": f"{etype} happened", **extra, "charged": 0}, "request_id": "req_err01"}


def search_page(items: list[dict[str, Any]], cursor: str | None = None, rid: str = "req_1") -> dict[str, Any]:
    return {"items": items, "next_cursor": cursor, "usage": USAGE, "request_id": rid}
