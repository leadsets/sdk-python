"""The async client: run several searches at once.

Run: LEADSETS_API_KEY=ls_live_… python examples/async_search.py
"""

import asyncio

from leadsets import AsyncLeadsets


async def main() -> None:
    async with AsyncLeadsets() as ls:
        sales, marketing = await asyncio.gather(
            ls.people.search(function="revenue", seniority="vp", country="US", limit=10),
            ls.people.search(function="marketing", seniority="head", country="US", limit=10),
        )
        print(len(sales.items), "sales leaders;", len(marketing.items), "marketing leaders")

        async for company in ls.companies.search_all(industry="saas", employees="50-200", max_items=50):
            print(company.name, company.domain)


asyncio.run(main())
