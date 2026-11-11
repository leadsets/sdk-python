"""Handle every error type. The SDK already retries 429, 5xx and network errors (2 retries by default).

Run: LEADSETS_API_KEY=ls_live_… python examples/error_handling.py
"""

from leadsets import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    FreeRecordsExhaustedError,
    InvalidRequestError,
    Leadsets,
    NotFoundError,
    RateLimitError,
)

ls = Leadsets(max_retries=3)

try:
    res = ls.people.search(title=["Head of Growth"], country="GB", limit=25, idempotency_key="growth-gb-1")
    print(len(res.items), "people")
except RateLimitError as e:
    # window_full, weekly_limit or too_many_concurrent, after the SDK's own retries.
    print(f"{e.type} on {e.meter}; resets at {e.resets_at}; retry in {e.retry_after}s")
except FreeRecordsExhaustedError:
    print("Free records are used up. Pick a plan to keep going.")
except InvalidRequestError as e:
    print(f"Bad value for {e.param}: {e.message}")
except AuthenticationError:
    print("Check the API key.")
except NotFoundError:
    print("Nothing found; nothing counted.")
except APIError as e:
    print(f"API error {e.status_code} {e.type}: {e.message} (request_id {e.request_id})")
except APIConnectionError as e:
    print("Network problem:", e)
