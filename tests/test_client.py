from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

import leadsets
from leadsets import DEFAULT_BASE_URL, Leadsets, LeadsetsError, NotFoundError
from leadsets.types import (
    CompaniesSearchResponse,
    Email,
    EmailVerifyResponse,
    PeopleSearchResponse,
    Person,
    Unavailable,
    WindowMeters,
)

from .conftest import BASE, KEY, USAGE, person, search_page


def body(route: respx.Route, i: int = -1) -> object:
    return json.loads(route.calls[i].request.content)


class TestConfiguration:
    def test_version_matches_pyproject(self) -> None:
        root = Path(__file__).resolve().parents[1]
        version_file = (root / "src/leadsets/_version.py").read_text()
        assert f'"{leadsets.__version__}"' in version_file

    def test_key_as_first_argument(self, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/people/search").respond(json=search_page([]))
        Leadsets(KEY).people.search()
        assert route.calls[0].request.headers["authorization"] == f"Bearer {KEY}"

    def test_reads_leadsets_api_key(self, mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LEADSETS_API_KEY", "ls_live_fromenv000000000000")
        monkeypatch.setenv("LEADSETS_KEY", "ls_live_other00000000000000")
        route = mock.get("/v1/usage").respond(json={"plan": "pro", "request_id": "r"})
        Leadsets().usage.get()
        assert route.calls[0].request.headers["authorization"] == "Bearer ls_live_fromenv000000000000"

    def test_falls_back_to_leadsets_key(self, mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LEADSETS_KEY", "ls_live_other00000000000000")
        route = mock.get("/v1/usage").respond(json={"plan": "pro", "request_id": "r"})
        Leadsets().usage.get()
        assert route.calls[0].request.headers["authorization"] == "Bearer ls_live_other00000000000000"

    def test_explicit_key_wins(self, mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LEADSETS_API_KEY", "ls_live_fromenv000000000000")
        route = mock.get("/v1/usage").respond(json={"plan": "pro", "request_id": "r"})
        Leadsets(KEY).usage.get()
        assert route.calls[0].request.headers["authorization"] == f"Bearer {KEY}"

    def test_missing_key_raises(self) -> None:
        with pytest.raises(LeadsetsError, match="LEADSETS_API_KEY"):
            Leadsets()
        with pytest.raises(LeadsetsError):
            leadsets.AsyncLeadsets()

    def test_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert DEFAULT_BASE_URL == "https://api.leadsets.ai"
        assert Leadsets(KEY).base_url == "https://api.leadsets.ai"
        assert Leadsets(KEY, base_url="http://localhost:8080/").base_url == "http://localhost:8080"
        monkeypatch.setenv("LEADSETS_BASE_URL", "https://staging.example.com")
        assert Leadsets(KEY).base_url == "https://staging.example.com"

    def test_custom_base_url_is_used(self) -> None:
        with respx.mock(base_url="http://localhost:8080") as m:
            route = m.get("/v1/usage").respond(json={"plan": "pro", "request_id": "r"})
            Leadsets(KEY, base_url="http://localhost:8080").usage.get()
            assert route.called

    def test_headers(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/people/search").respond(json=search_page([]))
        c = Leadsets(KEY, default_headers={"X-Trace": "abc"})
        c.people.search(limit=1, extra_headers={"X-Extra": "1"})
        h = route.calls[0].request.headers
        assert h["user-agent"].startswith(f"leadsets-sdk-python/{leadsets.__version__}")
        assert h["content-type"] == "application/json"
        assert h["accept"] == "application/json"
        assert h["x-trace"] == "abc"
        assert h["x-extra"] == "1"

    def test_custom_http_client(self, mock: respx.MockRouter) -> None:
        route = mock.get("/v1/usage").respond(json={"plan": "pro", "request_id": "r"})
        with httpx.Client() as http:
            c = Leadsets(KEY, http_client=http)
            c.usage.get()
            c.close()  # doesn't close a client it didn't create
            assert not http.is_closed
        assert route.called


class TestEndpoints:
    def test_people_search(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/people/search").respond(
            json=search_page([person()], cursor="c_abc", rid="req_3f9a1c0b2d4e"),
            headers={
                "X-Leadsets-Records-Remaining": "499",
                "X-Leadsets-Requests-Remaining": "2499",
                "X-Leadsets-Weekly-Remaining": "2499",
            },
        )
        res = ls.people.search(
            function=["revenue"], seniority=["vp", "head"], employees="20-200", country="US", industry="saas", limit=10
        )
        assert body(route) == {
            "function": ["revenue"],
            "seniority": ["vp", "head"],
            "employees": "20-200",
            "country": "US",
            "industry": "saas",
            "limit": 10,
        }
        assert isinstance(res, PeopleSearchResponse)
        p = res.items[0]
        assert isinstance(p, Person)
        assert p.match_reasons is not None
        assert "function" in p.match_reasons
        assert isinstance(p.email, Email)
        assert p.email.status == "verified"
        assert p.sources["title"].confidence == 0.9
        assert p.location.city == "San Francisco"
        assert p.company is not None
        assert p.company.employees == 120
        # Unknown fields are kept.
        assert p["something_new"] == {"x": 1}
        assert p.to_dict()["person_id"] == p.person_id
        assert res.usage.search_records_counted == 1
        assert res.next_cursor == "c_abc"
        assert res.request_id == "req_3f9a1c0b2d4e"
        assert res.last_response is not None
        assert res.last_response.status_code == 200
        assert res.last_response.request_id == "req_3f9a1c0b2d4e"
        assert res.last_response.attempts == 1
        rl = res.last_response.rate_limit
        assert (rl.records_remaining, rl.requests_remaining, rl.weekly_remaining, rl.free_remaining) == (
            499,
            2499,
            2499,
            None,
        )

    def test_none_params_are_left_out_and_tuples_become_lists(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/people/search").respond(json=search_page([]))
        ls.people.search(title=("VP Sales",), country=None, limit=5)  # type: ignore[arg-type]
        assert body(route) == {"title": ["VP Sales"], "limit": 5}

    def test_companies_search(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/companies/search").respond(
            json={
                "items": [{"company_id": "c1", "name": "Example", "technologies": ["hubspot"]}],
                "next_cursor": None,
                "usage": {"search_records_counted": 1},
                "request_id": "r",
            }
        )
        res = ls.companies.search(industry="saas", technology=["hubspot"], employees="50-200")
        assert body(route) == {"industry": "saas", "technology": ["hubspot"], "employees": "50-200"}
        assert isinstance(res, CompaniesSearchResponse)
        assert res.items[0].technologies == ["hubspot"]

    def test_people_enrich(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/people/enrich").respond(
            json={
                "person": person(),
                "matched_by": "linkedin_url",
                "usage": {"enrich_records_counted": 1},
                "request_id": "r",
            },
            headers={"X-Leadsets-Free-Remaining": "999"},
        )
        res = ls.people.enrich(linkedin_url="https://www.linkedin.com/in/example")
        assert body(route) == {"linkedin_url": "https://www.linkedin.com/in/example"}
        assert res.person.full_name == "Jane Doe"
        assert res.matched_by == "linkedin_url"
        assert res.usage.enrich_records_counted == 1
        assert res.last_response is not None
        assert res.last_response.rate_limit.free_remaining == 999

    def test_companies_enrich(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/companies/enrich").respond(
            json={
                "company": {"company_id": "c1", "name": "Example", "location": {"country": "US"}},
                "usage": {},
                "request_id": "r",
            }
        )
        res = ls.companies.enrich(domain="example.com")
        assert body(route) == {"domain": "example.com"}
        assert res.company.name == "Example"
        assert res.company.location.country == "US"

    def test_emails_verify_forms(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.post("/v1/emails/verify").respond(
            json={
                "results": [
                    {
                        "email": "a@b.co",
                        "status": "verified",
                        "confidence": 0.95,
                        "checked_at": "x",
                        "source": "s",
                        "mx_provider": None,
                    },
                    {
                        "email": "c@d.co",
                        "status": None,
                        "confidence": None,
                        "checked_at": None,
                        "source": None,
                        "mx_provider": None,
                        "reason": "not_checked: limit reached",
                    },
                ],
                "summary": {"verified": 1, "catch_all": 0, "unknown": 0, "invalid": 0, "not_checked": 1},
                "usage": {"enrich_records_counted": 1},
                "request_id": "r",
            }
        )
        res = ls.emails.verify(emails=["a@b.co", "c@d.co"])
        ls.emails.verify("a@b.co")
        ls.emails.verify(["a@b.co"])
        assert [body(route, i) for i in range(3)] == [
            {"emails": ["a@b.co", "c@d.co"]},
            {"email": "a@b.co"},
            {"emails": ["a@b.co"]},
        ]
        assert isinstance(res, EmailVerifyResponse)
        assert res.summary.verified == 1
        assert res.results[1].status is None
        assert res.results[1].reason == "not_checked: limit reached"
        with pytest.raises(TypeError):
            ls.emails.verify()

    def test_scrape(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        company = mock.post("/v1/scrape/company").respond(
            json={
                "domain": "example.com",
                "url": "https://example.com/",
                "name": "Example",
                "description": None,
                "headings": ["Analytics"],
                "key_links": {"pricing": "https://example.com/pricing"},
                "social": {},
                "pages": [{"url": "https://example.com/", "title": "Example", "description": None, "text": "hi"}],
                "units_used": 1,
                "scraped_at": "x",
                "usage": {"scrape_units_counted": 1, "scrape_units_left": 99},
                "request_id": "r",
            }
        )
        jobs = mock.post("/v1/scrape/jobs").respond(
            json={
                "domain": "example.com",
                "careers_url": "https://example.com/careers",
                "jobs": [
                    {
                        "title": "AE",
                        "url": "u",
                        "location": "Remote",
                        "team": "Sales",
                        "posted": None,
                        "source": "site",
                        "found_on": "u",
                    }
                ],
                "count": 1,
                "units_used": 2,
                "scraped_at": "x",
                "usage": {"scrape_units_counted": 2, "scrape_units_left": 97},
                "request_id": "r",
            }
        )
        c = ls.scrape.company(domain="example.com", max_pages=3)
        j = ls.scrape.jobs(domain="example.com")
        assert body(company) == {"domain": "example.com", "max_pages": 3}
        assert body(jobs) == {"domain": "example.com"}
        assert c.key_links["pricing"] == "https://example.com/pricing"
        assert c.pages[0].text == "hi"
        assert c.usage.scrape_units_left == 99
        assert j.jobs[0].title == "AE"
        assert j.count == 1

    def test_jobs_get(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.get("/v1/jobs/job%201").respond(
            json={"id": "job 1", "status": "done", "rows": 3, "request_id": "r"}
        )
        job = ls.jobs.get("job 1")
        req = route.calls[0].request
        assert req.method == "GET"
        assert req.content == b""
        assert "idempotency-key" not in req.headers
        assert job.status == "done"
        assert job["rows"] == 3
        with pytest.raises(ValueError, match="job_id"):
            ls.jobs.get("")

    def test_jobs_get_not_available(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        mock.get("/v1/jobs/j1").respond(
            404,
            json={
                "error": {"type": "not_found", "message": "Async jobs are not available yet.", "charged": 0},
                "request_id": None,
            },
        )
        with pytest.raises(NotFoundError):
            ls.jobs.get("j1")

    def test_usage_get(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        route = mock.get("/v1/usage").respond(
            json={
                "plan": "pro",
                "enrich": {
                    "records_5h": [9150, 15000],
                    "requests_5h": [30400, 75000],
                    "records_week": [45800, 75000],
                    "resets_at": "2026-11-11T14:15:00Z",
                    "week_resets_at": None,
                },
                "search": {"unavailable": True},
                "concurrent_searches": [2, 5],
                "scrape_units": 320,
                "scraping": True,
                "usage": {},
                "request_id": "req_u",
            }
        )
        u = ls.usage.get()
        req = route.calls[0].request
        assert req.method == "GET"
        assert "idempotency-key" not in req.headers
        assert "content-type" not in req.headers
        assert u.plan == "pro"
        assert isinstance(u.enrich, WindowMeters)
        assert u.enrich.records_5h == (9150, 15000)
        assert isinstance(u.search, Unavailable)
        assert u.concurrent_searches == (2, 5)
        assert u.scrape_units == 320

    def test_free_usage(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        mock.get("/v1/usage").respond(
            json={
                "plan": "free",
                "free": {
                    "search_records": [10, 100],
                    "enrich_records": [5, 1000],
                    "data_calls": [7, 1000],
                    "search_per_call": 10,
                    "note": "n",
                },
                "concurrent_searches": [None, 3],
                "scrape_units": 0,
                "scraping": False,
                "usage": {},
                "request_id": "r",
            }
        )
        u = ls.usage.get()
        assert u.free is not None
        assert u.free.enrich_records == (5, 1000)
        assert u.concurrent_searches == (None, 3)

    def test_replayed(self, ls: Leadsets, mock: respx.MockRouter) -> None:
        mock.post("/v1/people/search").respond(json=search_page([]), headers={"Idempotent-Replayed": "true"})
        res = ls.people.search(idempotency_key="row-1")
        assert res.last_response is not None
        assert res.last_response.idempotent_replayed is True
        assert res.last_response.idempotency_key == "row-1"


def test_usage_constant_shape() -> None:
    assert USAGE["search_records_counted"] == 1
    assert BASE == DEFAULT_BASE_URL
