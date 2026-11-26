# Changelog

All notable changes to this package are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.5.0] - 2026-11-26

### Changed

- `scrape.jobs` counts 1 scrape unit per role returned, not per page read (the API's new rule). New `limit`
  (1–500, default 25) caps the roles returned and stops further reads; `max_pages` is no longer charged.
- `ScrapeJobsResponse`: new `limited` and `pages_read`; `units_used` is the roles returned.

## [0.4.0] - 2026-11-26

### Changed

- `scrape.jobs` takes the company website only: `{ domain }` is required and `url` is gone (the API no longer
  accepts it). Roles now also come from LinkedIn's public job listings; `Job.source` can be `"linkedin"`.
- `ScrapeJobsResponse`: new `company` and `sources`; `careers_url` can be null when only LinkedIn had roles.

## [0.3.0] - 2026-11-25

### Added

- `people.search`: `include_company` (default True) and `include_emails` (default False, on with `has_verified_email`).

### Changed

- The API counts each person as one search record and their company as another, and each work email
  as one enrichment record. Pass `include_company=False` for people only.
- Search results no longer carry work emails unless you ask for them with `include_emails=True`.

## [0.2.0] - 2026-11-19

### Added

- `companies.search`: `keywords` and `exclude_keywords`, matched as whole words in the company's
  name, description and specialties. `Company` has `specialties` and `email_domain`.
- `people.search`: `company_keywords` and `exclude_company_keywords` (what the person's company does),
  `match_headline` (title words also match the LinkedIn headline) and `priorities` with
  `company_linkedin_url`: the best contacts at one company, in your order of preference, each
  tagged with `priority`. `Person` has `headline`; the response has `company` with `priorities`.
- `people.count` and `companies.count` (sync and async): how many records match (`count`,
  `count_capped`), using no records.
- `Usage.limits` and `Usage.resets_at`: the limits behind the remaining counts, and when each window
  resets.

## [0.1.2] - 2026-11-11

### Changed

- README badges on PyPI read the published package.

## [0.1.1] - 2026-11-11

### Changed

- PyPI project links to the Leadsets homepage and docs carry campaign parameters.

## [0.1.0] - 2026-11-11

### Added

- First release of `leadsets`.
- Sync `Leadsets` and async `AsyncLeadsets` clients on httpx.
- `people.search`, `people.enrich`, `companies.search`, `companies.enrich`, `emails.verify`,
  `scrape.company`, `scrape.jobs`, `jobs.get` and `usage.get`.
- Pagination with `search_all` (records) and `search_pages` (pages), sync and async, with
  `max_items` and `max_pages`.
- Typed exceptions mapped from `error.type` and status, each with `request_id`.
- Automatic retries with exponential backoff and jitter on 429 (honouring `Retry-After`), 5xx,
  timeouts and network errors.
- An auto-generated `Idempotency-Key` on every paid call, reused across retries.
- Typed parameters (`TypedDict`) and responses (dataclasses), with a `py.typed` marker.
- Parsed rate-limit headers on `last_response.rate_limit`.

[0.1.0]: https://github.com/leadsets/sdk-python/releases/tag/v0.1.0
