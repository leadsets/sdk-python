"""Open roles from a company's careers page, job board and LinkedIn: a hiring signal.

Needs a paid plan with scrape units.

Run: LEADSETS_API_KEY=ls_live_… python examples/scrape_jobs.py
"""

from leadsets import Leadsets, PermissionDeniedError, ScrapeUnitsExhaustedError

ls = Leadsets()

try:
    res = ls.scrape.jobs(domain="example.com", max_pages=3)
    print(f"{res.count} open roles at {res.company} (careers page: {res.careers_url or 'none found'})")
    for job in res.jobs:
        print(f"- [{job.source}] {job.title} ({job.location or 'no location'})")
    print("scrape units left:", res.usage.scrape_units_left)
except PermissionDeniedError as e:
    print("Scraping needs a paid plan:", e.upgrade_url)
except ScrapeUnitsExhaustedError:
    print("No scrape units left. Add a pack in Billing.")
