# Changelog

All notable changes to this package are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

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
