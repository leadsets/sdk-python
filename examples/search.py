"""Ten revenue leaders at US SaaS companies with 20-200 people.

Run: LEADSETS_API_KEY=ls_live_… python examples/search.py
"""

import os

from leadsets import Leadsets

ls = Leadsets(os.environ.get("LEADSETS_KEY"))

res = ls.people.search(
    function=["revenue"],
    seniority=["vp", "head"],
    employees="20-200",
    country="US",
    industry="saas",
    limit=10,
)

for p in res.items:
    company = p.company.name if p.company else "?"
    email = f"{p.email.address} ({p.email.status})" if p.email else "no email"
    print(f"{p.full_name} · {p.title} @ {company} · {email}")
    print("  matched on:", ", ".join(p.match_reasons or []))

print("usage:", res.usage)
if res.last_response:
    print("records left in this 5-hour window:", res.last_response.rate_limit.records_remaining)
