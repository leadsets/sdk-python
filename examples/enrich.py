"""Enrich a person (LinkedIn URL, work email, or name plus company domain) and a company.

Run: LEADSETS_API_KEY=ls_live_… python examples/enrich.py
"""

from leadsets import Leadsets, NotFoundError

ls = Leadsets()

try:
    res = ls.people.enrich(full_name="Jane Doe", company_domain="example.com")
    p = res.person
    print(f"matched by {res.matched_by}:", p.full_name, p.title, p.email.address if p.email else None)
    # Every field says where it came from and when it was last seen.
    print("title freshness:", p.sources.get("title"))
except NotFoundError:
    # A miss costs nothing.
    print("No match; nothing was counted.")

company = ls.companies.enrich(domain="example.com").company
print(company.name, company.industry, company.employees, company.technologies)
