"""Verify a list of emails in batches of 100 and keep only the deliverable ones.

Run: LEADSETS_API_KEY=ls_live_… python examples/verify_list.py
"""

from leadsets import Leadsets

ls = Leadsets()

emails = ["maya@northwind.io", "sam@stackfold.com", "not-an-email", "jo@parcelry.co"]

keep: list[str] = []
for i in range(0, len(emails), 100):
    res = ls.emails.verify(emails[i : i + 100])
    for r in res.results:
        if r.status == "verified":
            keep.append(r.email)
        elif r.status is None:
            print(f"{r.email}: {r.reason}")  # not checked, not counted
    print("summary:", res.summary)

print("deliverable:", keep)
