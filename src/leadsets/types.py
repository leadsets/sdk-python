"""Request and response types for the Leadsets API v1.

Request parameters are ``TypedDict``s (they type-check the keyword arguments of each method).
Responses are dataclasses built from the JSON. Every response object also has
``to_dict()`` for the raw JSON and ``last_response`` with HTTP details.
"""

from __future__ import annotations

import dataclasses
import sys
from collections.abc import Sequence
from typing import Literal, TypedDict

if sys.version_info >= (3, 11):
    from typing import Required
else:  # pragma: no cover
    from typing_extensions import Required

import httpx

from ._models import Model

__all__ = [
    "APIResponse",
    "AsyncJob",
    "CompaniesSearchParams",
    "CompaniesSearchResponse",
    "Company",
    "CompanyEnrichParams",
    "CompanyEnrichResponse",
    "Email",
    "EmailStatus",
    "EmailVerification",
    "EmailVerifyResponse",
    "EmailVerifySummary",
    "FieldSource",
    "FreeMeters",
    "Job",
    "JobSources",
    "Location",
    "PeopleSearchParams",
    "PeopleSearchResponse",
    "Person",
    "PersonCompany",
    "PersonEnrichParams",
    "PersonEnrichResponse",
    "PersonFunction",
    "Plan",
    "RateLimitInfo",
    "ResponseMeta",
    "ScrapeCompanyResponse",
    "ScrapeJobsParams",
    "ScrapeJobsResponse",
    "ScrapeParams",
    "ScrapedPage",
    "Seniority",
    "Unavailable",
    "Usage",
    "UsageResponse",
    "VerificationStatus",
    "WindowMeters",
]

Seniority = Literal["c_level", "vp", "head", "director", "manager", "ic"]
PersonFunction = Literal["revenue", "marketing", "engineering", "product", "ops", "finance", "hr"]
Plan = Literal["free", "solo", "pro", "team", "max"]
#: Status of an email attached to a person. Invalid emails are never returned.
EmailStatus = Literal["verified", "catch_all", "unknown"]
#: Status from ``emails.verify``.
VerificationStatus = Literal["verified", "catch_all", "unknown", "invalid"]

_StrList = str | Sequence[str]


# ---- Request parameters ----------------------------------------------------------------------


class PeoplePriority(TypedDict, total=False):
    """One group of titles for ``PeopleSearchParams.priorities``, best first. ``title`` is required."""

    #: Titles for this priority, fuzzy-matched like ``title``.
    title: _StrList
    #: Titles that rule a person out of this priority, e.g. ["assistant", "intern"].
    exclude_title: _StrList
    #: Replaces the top-level ``seniority`` for this priority.
    seniority: Seniority | Sequence[Seniority]
    #: Replaces the top-level ``function`` for this priority.
    function: PersonFunction | Sequence[PersonFunction]
    #: Replaces the top-level ``country`` for this priority.
    country: _StrList
    #: Also match these titles against the LinkedIn headline.
    match_headline: bool


class PeopleSearchParams(TypedDict, total=False):
    #: Job titles. Fuzzy-matched: "VP Sales" also finds "Vice President, Sales".
    title: _StrList
    #: Also match title words against the LinkedIn headline.
    match_headline: bool
    seniority: Seniority | Sequence[Seniority]
    function: PersonFunction | Sequence[PersonFunction]
    #: Only people at these companies (domains).
    company_domain: _StrList
    #: With ``priorities``: the company by its LinkedIn page, instead of ``company_domain``.
    company_linkedin_url: str
    #: What their company does, e.g. ["clay", "gtm engineering"]: whole words in its name,
    #: description and specialties.
    company_keywords: _StrList
    #: Leave out people whose company mentions any of these.
    exclude_company_keywords: _StrList
    #: Best contacts at ONE company (one ``company_domain`` or ``company_linkedin_url``): 1–10
    #: groups of titles, best first. Results never repeat a person and carry ``priority``.
    #: ``limit`` 1–25 (default 5); no cursor, no top-level ``title``.
    priorities: Sequence[PeoplePriority]
    #: Company headcount range, e.g. "50-200", "1000+" or "<50".
    employees: str
    #: Leadsets industry slugs, e.g. "saas".
    industry: _StrList
    #: ISO 3166-1 alpha-2 country codes, e.g. "US".
    country: _StrList
    has_verified_email: bool
    #: Company details on each person (default True): one more search record per person.
    include_company: bool
    #: The work email on each person when one is found (default False, on with
    #: ``has_verified_email``): 1 enrichment record each.
    include_emails: bool
    max_age_days: int
    exclude_stale: bool
    #: 1–100. Default 25. Free plan: at most 10.
    limit: int
    cursor: str
    #: Optional: the request in plain language, kept with your request log.
    prompt: str


class PersonEnrichParams(TypedDict, total=False):
    linkedin_url: str
    email: str
    full_name: str
    first_name: str
    last_name: str
    company_domain: str
    include_personal_email: bool
    prompt: str


class CompaniesSearchParams(TypedDict, total=False):
    #: What the company does, e.g. ["lead generation", "appointment setting"]: whole words in its
    #: name, description and specialties; any keyword matches.
    keywords: _StrList
    #: Leave out companies that mention any of these, e.g. ["pottery"].
    exclude_keywords: _StrList
    industry: _StrList
    employees: str
    country: _StrList
    #: Technologies the company uses, e.g. "hubspot". Matches any.
    technology: _StrList
    domain: _StrList
    max_age_days: int
    exclude_stale: bool
    limit: int
    cursor: str
    prompt: str


class CompanyEnrichParams(TypedDict, total=False):
    #: Company domain or website URL, e.g. "example.com".
    domain: str
    linkedin_url: str
    prompt: str


class ScrapeParams(TypedDict, total=False):
    domain: str
    #: A specific page to start from (overrides domain).
    url: str
    #: Pages to read, 1–10. 1 scrape unit per page read.
    max_pages: int


class ScrapeJobsParams(TypedDict, total=False):
    #: Required. The company website, e.g. "example.com" or "https://example.com".
    domain: Required[str]
    #: Open roles to return at most, 1–500. Default 25. 1 scrape unit per role returned; once this
    #: many are found, no more pages are read.
    limit: int
    #: Pages to read across every source (careers page, job board, LinkedIn), 1–10. Default 3. Not charged.
    max_pages: int


# ---- HTTP details ----------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class RateLimitInfo:
    """Rate-limit headers of a response, parsed. ``None`` when the header was absent."""

    #: ``X-Leadsets-Records-Remaining``: records left in this kind's five-hour window.
    records_remaining: int | None
    #: ``X-Leadsets-Requests-Remaining``: requests left in this kind's five-hour window.
    requests_remaining: int | None
    #: ``X-Leadsets-Weekly-Remaining``: records left in this kind's weekly window.
    weekly_remaining: int | None
    #: ``X-Leadsets-Free-Remaining``: Free plan only, free records left.
    free_remaining: int | None
    #: ``Retry-After`` in seconds.
    retry_after: float | None


@dataclasses.dataclass(frozen=True)
class ResponseMeta:
    """HTTP details of a response, as ``last_response`` on every result."""

    status_code: int
    headers: httpx.Headers
    request_id: str | None
    #: The Idempotency-Key that was sent, if any.
    idempotency_key: str | None
    #: True when the API replayed a stored result for this key (nothing was counted again).
    idempotent_replayed: bool
    rate_limit: RateLimitInfo
    #: How many HTTP attempts the call took (1 = no retries).
    attempts: int


# ---- Shared response parts -------------------------------------------------------------------


@dataclasses.dataclass(kw_only=True)
class FieldSource(Model):
    """When a field was last seen and how confident we are in it."""

    seen_at: str | None = None
    confidence: float | None = None


@dataclasses.dataclass(kw_only=True)
class Location(Model):
    country: str | None = None
    region: str | None = None
    city: str | None = None


@dataclasses.dataclass(kw_only=True)
class Usage(Model):
    """What this call counted and what is left. Which fields are set depends on the endpoint and plan."""

    search_records_counted: int | None = None
    search_records_left_5h: int | None = None
    search_requests_left_5h: int | None = None
    search_records_left_week: int | None = None
    free_search_records_left: int | None = None
    enrich_records_counted: int | None = None
    enrich_records_left_5h: int | None = None
    enrich_requests_left_5h: int | None = None
    enrich_records_left_week: int | None = None
    free_enrich_records_left: int | None = None
    free_calls_left: int | None = None
    scrape_units_counted: int | None = None
    scrape_units_left: int | None = None
    #: True when limits could not be checked for this call.
    degraded: bool | None = None
    #: Paid plans: the limits behind the ``*_left_*`` numbers, e.g. ``search_records_5h``.
    limits: dict[str, int] | None = None
    #: Paid plans: when the oldest usage leaves each window (ISO 8601), e.g. ``search_5h``.
    resets_at: dict[str, str | None] | None = None


@dataclasses.dataclass(kw_only=True)
class APIResponse(Model):
    #: Quote it to support: we can see exactly what happened.
    request_id: str
    usage: Usage = dataclasses.field(default_factory=Usage)
    #: HTTP status, headers and rate-limit info.
    last_response: ResponseMeta | None = dataclasses.field(default=None, repr=False, compare=False)


# ---- People ----------------------------------------------------------------------------------


@dataclasses.dataclass(kw_only=True)
class Email(Model):
    address: str
    status: EmailStatus
    type: str = "business"
    confidence: float | None = None
    checked_at: str | None = None
    mx_provider: str | None = None


@dataclasses.dataclass(kw_only=True)
class PersonCompany(Model):
    company_id: str | None = None
    name: str | None = None
    domain: str | None = None
    #: The domain the company's work emails use, when known.
    email_domain: str | None = None
    industry: str | None = None
    employees: int | None = None
    employee_range: str | None = None


@dataclasses.dataclass(kw_only=True)
class Person(Model):
    person_id: str
    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    #: LinkedIn headline, when known.
    headline: str | None = None
    seniority: Seniority | None = None
    #: Finer-grained seniority, e.g. "founder" or "senior".
    seniority_detail: str | None = None
    function: PersonFunction | None = None
    #: Finer-grained function, e.g. "sales" or "revops".
    function_detail: str | None = None
    linkedin_url: str | None = None
    location: Location = dataclasses.field(default_factory=Location)
    #: None when left out with ``include_company=False``.
    company: PersonCompany | None = None
    #: On ``people.search``, set only with ``include_emails`` or ``has_verified_email``.
    email: Email | None = None
    #: Present on ``people.enrich`` with ``include_personal_email``.
    personal_email: Email | None = None
    #: Which filters this record matched (search results only).
    match_reasons: list[str] | None = None
    #: With ``priorities``: which priority found this person (1 for the first group).
    priority: int | None = None
    refreshed_at: str | None = None
    confirmed_at: str | None = None
    stale_after_at: str | None = None
    stale: bool = False
    #: Source, last-seen date and confidence for every field that has a value.
    sources: dict[str, FieldSource] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(kw_only=True)
class MatchedCompany(Model):
    """With ``priorities``: the company the search was scoped to."""

    company_id: str | None = None
    name: str | None = None
    domain: str | None = None
    email_domain: str | None = None
    linkedin_url: str | None = None


@dataclasses.dataclass(kw_only=True)
class PeopleSearchResponse(APIResponse):
    items: list[Person] = dataclasses.field(default_factory=list)
    next_cursor: str | None = None
    #: With ``priorities``: the company that was matched, or ``None`` when none is on file.
    company: MatchedCompany | None = None
    #: With ``priorities``, when no company is on file for the LinkedIn page.
    note: str | None = None


@dataclasses.dataclass(kw_only=True)
class CountResponse(APIResponse):
    """``people.count`` / ``companies.count``: how many records match. Uses no records."""

    count: int = 0
    #: True when counting stopped at 10,000: there are at least ``count`` matches.
    count_capped: bool = False


@dataclasses.dataclass(kw_only=True)
class PersonEnrichResponse(APIResponse):
    person: Person
    #: "linkedin_url", "email" or "name_and_domain".
    matched_by: str | None = None
    #: Why a requested personal email was left out.
    personal_email_note: str | None = None


# ---- Companies -------------------------------------------------------------------------------


@dataclasses.dataclass(kw_only=True)
class Company(Model):
    company_id: str
    name: str | None = None
    domain: str | None = None
    #: The domain its work emails use, when known (may differ from ``domain``).
    email_domain: str | None = None
    linkedin_url: str | None = None
    industry: str | None = None
    naics: str | None = None
    employees: int | None = None
    employee_range: str | None = None
    revenue_range: str | None = None
    location: Location = dataclasses.field(default_factory=Location)
    founded_year: int | None = None
    description: str | None = None
    technologies: list[str] = dataclasses.field(default_factory=list)
    #: What the company says it does (LinkedIn specialties).
    specialties: list[str] = dataclasses.field(default_factory=list)
    match_reasons: list[str] | None = None
    refreshed_at: str | None = None
    confirmed_at: str | None = None
    stale_after_at: str | None = None
    stale: bool = False
    sources: dict[str, FieldSource] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(kw_only=True)
class CompaniesSearchResponse(APIResponse):
    items: list[Company] = dataclasses.field(default_factory=list)
    next_cursor: str | None = None


@dataclasses.dataclass(kw_only=True)
class CompanyEnrichResponse(APIResponse):
    company: Company


# ---- Emails ----------------------------------------------------------------------------------


@dataclasses.dataclass(kw_only=True)
class EmailVerification(Model):
    email: str
    #: ``None`` when the email was not checked (see ``reason``); nothing was counted for it.
    status: VerificationStatus | None = None
    confidence: float | None = None
    checked_at: str | None = None
    mx_provider: str | None = None
    #: Why the email was not checked, e.g. "not_checked: limit reached".
    reason: str | None = None


@dataclasses.dataclass(kw_only=True)
class EmailVerifySummary(Model):
    verified: int = 0
    catch_all: int = 0
    unknown: int = 0
    invalid: int = 0
    not_checked: int = 0


@dataclasses.dataclass(kw_only=True)
class EmailVerifyResponse(APIResponse):
    results: list[EmailVerification] = dataclasses.field(default_factory=list)
    summary: EmailVerifySummary = dataclasses.field(default_factory=EmailVerifySummary)


# ---- Scrape ----------------------------------------------------------------------------------


@dataclasses.dataclass(kw_only=True)
class ScrapedPage(Model):
    url: str
    title: str | None = None
    description: str | None = None
    #: Page text as Markdown, truncated.
    text: str = ""


@dataclasses.dataclass(kw_only=True)
class ScrapeCompanyResponse(APIResponse):
    domain: str
    url: str
    name: str | None = None
    description: str | None = None
    headings: list[str] = dataclasses.field(default_factory=list)
    #: e.g. pricing, about, customers, careers, contact, blog, docs, product, login, signup.
    key_links: dict[str, str] = dataclasses.field(default_factory=dict)
    #: e.g. linkedin, x, github, youtube, facebook, instagram.
    social: dict[str, str] = dataclasses.field(default_factory=dict)
    pages: list[ScrapedPage] = dataclasses.field(default_factory=list)
    units_used: int = 0
    scraped_at: str | None = None


@dataclasses.dataclass(kw_only=True)
class Job(Model):
    title: str
    url: str
    location: str | None = None
    team: str | None = None
    posted: str | None = None
    #: Where the role is listed: "greenhouse", "lever", "ashby", "workable", "recruitee",
    #: "smartrecruiters", "bamboohr", "site" or "linkedin".
    source: str | None = None
    found_on: str | None = None


@dataclasses.dataclass(kw_only=True)
class JobSources(Model):
    careers_page: bool = False
    job_board: bool = False
    linkedin: bool = False


@dataclasses.dataclass(kw_only=True)
class ScrapeJobsResponse(APIResponse):
    domain: str
    #: The company name searched on LinkedIn.
    company: str | None = None
    #: None when no careers page could be read (roles may still come from LinkedIn).
    careers_url: str | None = None
    #: Which sources were read.
    sources: JobSources = dataclasses.field(default_factory=JobSources)
    jobs: list[Job] = dataclasses.field(default_factory=list)
    count: int = 0
    #: True when ``limit`` cut the list short: more roles were found, or pages were left unread.
    limited: bool = False
    #: Scrape units counted: the roles returned.
    units_used: int = 0
    #: Pages read to find them (not charged).
    pages_read: int = 0
    scraped_at: str | None = None


# ---- Async jobs ------------------------------------------------------------------------------


@dataclasses.dataclass(kw_only=True)
class AsyncJob(APIResponse):
    id: str
    status: str
    # Other fields are available with job["field"] or job.to_dict().


# ---- Usage -----------------------------------------------------------------------------------


@dataclasses.dataclass(kw_only=True)
class WindowMeters(Model):
    """Each meter is ``(used, limit)``."""

    records_5h: tuple[int, int]
    requests_5h: tuple[int, int]
    records_week: tuple[int, int]
    resets_at: str | None = None
    week_resets_at: str | None = None


@dataclasses.dataclass(kw_only=True)
class Unavailable(Model):
    """A meter that could not be read right now."""

    unavailable: bool = True


@dataclasses.dataclass(kw_only=True)
class FreeMeters(Model):
    """Free plan one-time balances, each ``(used, limit)``."""

    search_records: tuple[int, int]
    enrich_records: tuple[int, int]
    data_calls: tuple[int, int]
    search_per_call: int | None = None
    note: str | None = None


@dataclasses.dataclass(kw_only=True)
class UsageResponse(APIResponse):
    plan: str
    #: Free plan: one-time balances.
    free: FreeMeters | None = None
    #: Paid plans: enrichment windows.
    enrich: WindowMeters | Unavailable | None = None
    #: Paid plans: search windows.
    search: WindowMeters | Unavailable | None = None
    #: Plans with a weekly personal email cap: ``(used, limit)``.
    personal_emails_week: tuple[int, int] | Unavailable | None = None
    #: ``(running, limit)``. ``running`` is None when it could not be read.
    concurrent_searches: tuple[int | None, int] | None = None
    scrape_units: int = 0
    scraping: bool = False
