"""Open roles from a company's careers page: a hiring signal. Needs a paid plan with scrape units.

Run: LEADSETS_API_KEY=ls_live_… python examples/scrape_jobs.py
"""

from leadsets import Leadsets, PermissionDeniedError, ScrapeUnitsExhaustedError

ls = Leadsets()

try:
    res = ls.scrape.jobs(domain="northwind.io", max_pages=3)
    print(f"{res.count} open roles at {res.careers_url}")
    for job in res.jobs:
        print(f"- {job.title} ({job.team or 'no team'}, {job.location or 'no location'})")
    print("scrape units left:", res.usage.scrape_units_left)
except PermissionDeniedError as e:
    print("Scraping needs a paid plan:", e.upgrade_url)
except ScrapeUnitsExhaustedError:
    print("No scrape units left. Add a pack in Billing.")
