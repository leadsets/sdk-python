# Leadsets Python SDK

[![PyPI](https://img.shields.io/pypi/v/leadsets?label=pypi)](https://pypi.org/project/leadsets/)
[![Python](https://img.shields.io/pypi/pyversions/leadsets?label=python)](https://pypi.org/project/leadsets/)
[![CI](https://github.com/leadsets/sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/leadsets/sdk-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

The official Python client for the [Leadsets](https://www.leadsets.ai/?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=intro) API.

Leadsets is B2B data for AI agents and the developers who build them. Search people and companies, enrich a person or a company, verify emails and scrape company websites and careers pages, over a REST API or an MCP server. Every record says why it matched, every field carries when it was last checked and a confidence score, and emails are only labelled verified when they are.

- Sync (`Leadsets`) and async (`AsyncLeadsets`) clients on [httpx](https://www.python-httpx.org/)
- Typed responses (dataclasses) and typed keyword arguments, with a `py.typed` marker
- Automatic retries with backoff on 429 (honouring `Retry-After`), 5xx and network errors
- An Idempotency-Key on every paid call, so a retry never counts records twice
- Cursor pagination with generators and async generators
- Python 3.10+

## Contents

- [Install](#install)
- [Quickstart](#quickstart)
- [Authentication](#authentication)
- [Resources](#resources)
- [Pagination](#pagination)
- [Errors and retries](#errors-and-retries)
- [Limits and usage](#limits-and-usage)
- [Idempotency](#idempotency)
- [Async usage](#async-usage)
- [Configuration](#configuration)
- [Typing](#typing)
- [MCP](#mcp)
- [Support](#support)
- [License](#license)

## Install

```bash
pip install leadsets
# or
uv add leadsets
poetry add leadsets
```

## Quickstart

[Create a free account](https://www.leadsets.ai/signup?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=quickstart) and copy your API key. Keys start with `ls_live_`.

```bash
export LEADSETS_API_KEY="ls_live_…"
```

Ten revenue leaders at US SaaS companies with 20–200 people:

```python
import os
from leadsets import Leadsets

ls = Leadsets(os.environ["LEADSETS_API_KEY"])

res = ls.people.search(
    function=["revenue"],
    seniority=["vp", "head"],
    employees="20-200",
    country="US",
    industry="saas",
    limit=10,
)

print(res.items[0].match_reasons, res.usage)
```

Every response carries what the call counted and what is left (`usage`), plus a `request_id`. The [quickstart guide](https://www.leadsets.ai/docs/quickstart?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=quickstart) walks through the same call with cURL.

## Authentication

The API uses bearer keys. Pass the key to the constructor, or leave it out and the SDK reads the `LEADSETS_API_KEY` environment variable (or `LEADSETS_KEY`).

```python
ls = Leadsets("ls_live_…")   # explicit
ls = Leadsets()              # from LEADSETS_API_KEY / LEADSETS_KEY
```

Keep the key out of source control. A free key is available at [leadsets.ai/signup](https://www.leadsets.ai/signup?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=authentication).

## Resources

| Method | Endpoint | Uses |
| --- | --- | --- |
| `ls.people.search(**params)` | `POST /v1/people/search` | 1 search record per record returned |
| `ls.people.enrich(**params)` | `POST /v1/people/enrich` | 1 enrichment record when found (+1 for a personal email) |
| `ls.companies.search(**params)` | `POST /v1/companies/search` | 1 search record per record returned |
| `ls.companies.enrich(**params)` | `POST /v1/companies/enrich` | 1 enrichment record when found |
| `ls.emails.verify(email_or_emails)` | `POST /v1/emails/verify` | 1 enrichment record per email checked |
| `ls.scrape.company(**params)` | `POST /v1/scrape/company` | 1 scrape unit per page read |
| `ls.scrape.jobs(**params)` | `POST /v1/scrape/jobs` | 1 scrape unit per page read |
| `ls.jobs.get(job_id)` | `GET /v1/jobs/{id}` | nothing |
| `ls.usage.get()` | `GET /v1/usage` | nothing |

Every method also takes [request options](#per-request-options) as keyword arguments.

Responses are dataclasses: `res.items[0].email.status`. `obj.to_dict()` returns the raw JSON, and `obj["field"]` reads any field, including ones newer than your SDK version.

### People search

Filters: `title`, `seniority` (`c_level`, `vp`, `head`, `director`, `manager`, `ic`), `function` (`revenue`, `marketing`, `engineering`, `product`, `ops`, `finance`, `hr`), `company_domain`, `employees` (`"50-200"`, `"1000+"`, `"<50"`), `industry` (slugs such as `"saas"`), `country` (ISO 3166-1 alpha-2), `has_verified_email`, `max_age_days`, `exclude_stale`, `limit` (1–100, default 25) and `cursor`. A string or a list works wherever a list is accepted.

```python
res = ls.people.search(
    title=["VP Sales", "Head of Sales"],  # fuzzy: "VP Sales" also finds "Vice President, Sales"
    country=["US", "CA"],
    employees="50-200",
    has_verified_email=True,
    limit=25,
)

for p in res.items:
    print(p.full_name, p.title, p.company.domain if p.company else None)
    if p.email:
        print(p.email.address, p.email.status, p.email.confidence, p.email.checked_at)
    print(p.match_reasons)     # ["title", "size", "country", "verified_email"]
    print(p.sources["title"])  # FieldSource(seen_at=…, confidence=…)
```

Each `Person` has `person_id`, names, `title`, `seniority` and `function` (with finer `seniority_detail` and `function_detail`), `linkedin_url`, `location`, `company`, `email`, `refreshed_at`, `stale` and `sources`.

### People enrich

Look a person up by LinkedIn URL, by work email, or by name plus company domain.

```python
res = ls.people.enrich(linkedin_url="https://www.linkedin.com/in/example")
ls.people.enrich(email="jane@example.com")
ls.people.enrich(full_name="Jane Doe", company_domain="example.com")
ls.people.enrich(first_name="Jane", last_name="Doe", company_domain="example.com", include_personal_email=True)

print(res.person.title, res.matched_by)
```

No match raises `NotFoundError` and costs nothing.

### Companies search

```python
res = ls.companies.search(
    industry="saas",
    employees="50-200",
    country="US",
    technology=["hubspot", "salesforce"],  # matches any
    limit=50,
)
print([(c.name, c.domain, c.employees) for c in res.items])
```

### Companies enrich

```python
company = ls.companies.enrich(domain="example.com").company  # a URL works too
ls.companies.enrich(linkedin_url="https://www.linkedin.com/company/example")

print(company.industry, company.naics, company.employee_range, company.revenue_range, company.technologies)
```

### Email verification

One email or up to 100 per call. Each result has a `status` (`verified`, `catch_all`, `unknown`, `invalid`), a `confidence` and `checked_at`.

```python
one = ls.emails.verify("jane@example.com")
many = ls.emails.verify(["jane@example.com", "sam@example.org"])
# or: ls.emails.verify(emails=[...])

print(many.summary)  # verified, catch_all, unknown, invalid, not_checked
for r in many.results:
    if r.status is None:
        print(r.email, r.reason)  # not checked, not counted
```

### Scrape a company website

A website as structured data: name, description, headings, key links (pricing, customers, careers, docs and more), social profiles and page text. `max_pages` (1–10, default 1) adds the about, pricing, customers, product and careers pages. Scraping is available on paid plans with scrape units.

```python
site = ls.scrape.company(domain="example.com", max_pages=3)
print(site.name, site.key_links.get("pricing"), site.social.get("linkedin"))
print([p.url for p in site.pages], site.usage.scrape_units_left)
```

### Scrape open roles

Open roles from a company's careers page or job board: title, link, team, location and posted date when shown. `max_pages` defaults to 3.

```python
res = ls.scrape.jobs(domain="example.com")
print(res.count, res.careers_url)
for job in res.jobs:
    print(job.title, job.team, job.location, job.url)
```

### Async jobs

```python
job = ls.jobs.get("job_123")
```

Async jobs are not generally available yet. Until they are, `jobs.get` raises `NotFoundError`. Split large runs across windows instead.

### Usage

What's left in every meter and when each window resets. Free to call, so call it before a big run.

```python
from leadsets.types import WindowMeters

u = ls.usage.get()
print(u.plan)
if isinstance(u.search, WindowMeters):
    used, limit = u.search.records_5h
    print(f"{limit - used} search records left; resets at {u.search.resets_at}")
print(u.concurrent_searches, u.scrape_units)
```

On the Free plan, `u.free` holds the one-time balances instead.

## Pagination

Searches return `next_cursor`. `search_all` follows it for you and yields one record at a time:

```python
for person in ls.people.search_all(title=["VP Sales"], country="US", limit=100):
    print(person.full_name)
```

Each record returned counts, so cap a run with `max_items`. The last page asks only for what's left, so you never pay for more than you take. `max_pages` caps the number of calls.

```python
for company in ls.companies.search_all(industry="saas", max_items=250):
    ...
```

To read `usage` as you go, iterate pages instead:

```python
for page in ls.people.search_pages(country="US", limit=100, max_pages=5):
    print(len(page.items), page.usage.search_records_left_5h)
```

Breaking out of a loop stops fetching. To page by hand, pass `cursor=res.next_cursor` to the next `search` call.

## Errors and retries

Every API error has a status, a machine-readable `type`, a message and a `request_id`. The SDK raises a typed exception for each:

| Exception | Status | `type` |
| --- | --- | --- |
| `InvalidRequestError` | 400 | `invalid_request` (`param` names the field) |
| `AuthenticationError` | 401 | `unauthorized` |
| `FreeRecordsExhaustedError` | 402 | `free_records_exhausted` |
| `ScrapeUnitsExhaustedError` | 402 | `scrape_units_exhausted` |
| `PermissionDeniedError` | 403 | `forbidden` (`upgrade_url` when an upgrade would allow the call) |
| `NotFoundError` | 404 | `not_found` |
| `IdempotencyConflictError` | 409 | `idempotency_conflict` |
| `RateLimitError` | 429 | `window_full`, `weekly_limit`, `too_many_concurrent` |
| `InternalServerError` | 5xx | `internal_error` |
| `ServiceUnavailableError` | 503 | `unavailable` |
| `APIConnectionError` | none | the request got no answer |
| `APITimeoutError` | none | the request timed out |

`FreeRecordsExhaustedError` and `ScrapeUnitsExhaustedError` subclass `PaymentRequiredError`. Every HTTP error subclasses `APIError`, and everything subclasses `LeadsetsError`. `leadsets.ConnectionError` and `leadsets.TimeoutError` are aliases of the last two.

```python
from leadsets import APIError, NotFoundError, RateLimitError

try:
    ls.people.enrich(email="jane@example.com")
except NotFoundError:
    pass  # nothing to enrich; nothing was counted
except RateLimitError as e:
    print(e.type, e.meter, e.resets_at, e.retry_after)
except APIError as e:
    print(e.status_code, e.type, e.message, e.request_id)
```

**Retries.** The SDK retries 429, 5xx, timeouts and network errors up to `max_retries` times (default 2). It waits for `Retry-After` when the API sends one, and otherwise backs off exponentially with jitter (about 0.5 s, 1 s, 2 s, up to 8 s). A `Retry-After` longer than `max_retry_delay` (default 60 s), such as a weekly limit, is raised at once so a run doesn't hang. 400, 401, 402, 403, 404 and 409 are never retried.

## Limits and usage

- **Records count only when data comes back.** Empty results, misses and errors use no records. Every call counts one request toward its window, hits and misses alike.
- **Paid plans have rolling five-hour windows** for records and for requests, plus a **weekly** records window, kept separately for search and for enrichment. Scraping uses scrape units.
- **Free** has 1,000 enrichment records and 100 search records, one time, with no card needed. Paid plans start at $29/month. See [pricing](https://www.leadsets.ai/pricing?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=limits).

Every response has a `usage` object with what the call counted and what's left, and the SDK parses the rate-limit headers into `res.last_response.rate_limit`:

```python
res = ls.people.search(country="US")
res.usage                         # search_records_counted, search_records_left_5h, …
res.last_response.rate_limit      # records_remaining, requests_remaining, weekly_remaining, free_remaining, retry_after
res.last_response.request_id      # also res.request_id
res.last_response.headers         # the raw httpx.Headers
```

Read more in the [docs](https://www.leadsets.ai/docs?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=limits).

## Idempotency

The SDK sends an `Idempotency-Key` with every paid call (all POSTs) and reuses it across its own retries, so a retry never counts records twice. Pass your own key to make a call safe to repeat across processes, for example one key per CRM row:

```python
ls.people.enrich(email=row["email"], idempotency_key=f"crm-{row['id']}")
```

A repeat with the same key and body returns the first result (`res.last_response.idempotent_replayed` is `True`) and counts nothing. The same key with a different body raises `IdempotencyConflictError`. Keys last 24 hours. With `search_all`/`search_pages`, a key you pass is suffixed per page (`key`, `key-p2`, `key-p3` …).

## Async usage

`AsyncLeadsets` has the same resources and methods, awaited:

```python
import asyncio
from leadsets import AsyncLeadsets

async def main() -> None:
    async with AsyncLeadsets() as ls:
        sales, marketing = await asyncio.gather(
            ls.people.search(function="revenue", seniority="vp", country="US", limit=10),
            ls.people.search(function="marketing", seniority="head", country="US", limit=10),
        )
        async for company in ls.companies.search_all(industry="saas", max_items=50):
            print(company.name)

asyncio.run(main())
```

Use the clients as context managers (or call `close()` / `await aclose()`) to release connections. One client can be shared across threads or tasks.

## Configuration

```python
ls = Leadsets(
    "ls_live_…",                         # default: LEADSETS_API_KEY or LEADSETS_KEY
    base_url="https://api.leadsets.ai",  # default; LEADSETS_BASE_URL also works
    max_retries=2,                       # retries on 429, 5xx, timeouts and network errors
    timeout=120.0,                       # seconds per attempt (float or httpx.Timeout)
    max_retry_delay=60.0,                # longest Retry-After to wait for, in seconds
    default_headers={"X-My-App": "crm-sync"},
    http_client=httpx.Client(proxy="http://proxy:8080"),  # your own httpx client
)
```

### Per-request options

```python
ls.people.search(
    country="US",
    idempotency_key="run-42",
    max_retries=5,
    timeout=30.0,
    extra_headers={"X-Trace-Id": "abc"},
)
```

## Typing

The package ships a `py.typed` marker. Search and enrich parameters are `TypedDict`s (`PeopleSearchParams`, `CompaniesSearchParams`, …) used as keyword arguments, so mypy and Pyright check filter names and values such as `seniority="vp"`. Responses are dataclasses in `leadsets.types`: `Person`, `Company`, `Email`, `EmailVerification`, `ScrapeCompanyResponse`, `Job`, `UsageResponse`, `Usage` and more. Fields the API may leave empty are `Optional`.

```python
from leadsets.types import PeopleSearchParams, Person

query: PeopleSearchParams = {"seniority": ["vp"], "function": ["marketing"]}
people: list[Person] = ls.people.search(**query).items
```

## MCP

Using an AI agent? Leadsets also runs a hosted MCP server at `https://mcp.leadsets.ai` with the same tools, so Claude, Cursor, ChatGPT and other MCP clients can call it with no code. See [Connect via MCP](https://www.leadsets.ai/docs/mcp?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=mcp).

## Support

- [Docs](https://www.leadsets.ai/docs?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=support) and the [quickstart](https://www.leadsets.ai/docs/quickstart?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=support)
- [Support](https://www.leadsets.ai/support?utm_source=github&utm_medium=readme&utm_campaign=sdk-python&utm_content=support): include the `request_id` from the response or error and we can see exactly what happened
- Bugs and feature requests: [GitHub issues](https://github.com/leadsets/sdk-python/issues)
- Security: see [SECURITY.md](SECURITY.md)

Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
