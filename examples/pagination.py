"""Walk every page of a search. max_items caps what you pay for: the last page asks only for what's left.

Run: LEADSETS_API_KEY=ls_live_… python examples/pagination.py
"""

from leadsets import Leadsets

ls = Leadsets()

for n, person in enumerate(ls.people.search_all(title=["VP Sales"], country="US", limit=100, max_items=250), 1):
    print(n, person.full_name, person.company.domain if person.company else None)

# Or page by page, to read usage as you go.
for page in ls.companies.search_pages(industry="saas", employees="50-200", max_pages=3):
    print(f"{len(page.items)} companies; records left this window: {page.usage.search_records_left_5h}")
