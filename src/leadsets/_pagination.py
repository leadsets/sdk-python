from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator, Mapping
from typing import Any, Protocol, TypeVar


class _Page(Protocol):
    @property
    def items(self) -> list[Any]: ...
    @property
    def next_cursor(self) -> str | None: ...


P = TypeVar("P", bound=_Page)


def _page_args(
    params: Mapping[str, Any],
    page: int,
    seen: int,
    cursor: str | None,
    max_items: int | None,
    max_pages: int | None,
    idempotency_key: str | None,
) -> tuple[dict[str, Any], str | None] | None:
    if max_pages is not None and page > max_pages:
        return None
    body = dict(params)
    if max_items is not None:
        left = max_items - seen
        if left <= 0:
            return None
        body["limit"] = min(int(body.get("limit") or 25), left)
    if cursor:
        body["cursor"] = cursor
    # Each page has a different body, so a caller's key is derived per page.
    key = f"{idempotency_key}-p{page}" if idempotency_key and page > 1 else idempotency_key
    return body, key


def iter_pages(
    fetch: Callable[[dict[str, Any], str | None], P],
    params: Mapping[str, Any],
    *,
    max_items: int | None,
    max_pages: int | None,
    idempotency_key: str | None,
) -> Iterator[P]:
    cursor = params.get("cursor")
    seen = 0
    page = 1
    while True:
        args = _page_args(params, page, seen, cursor, max_items, max_pages, idempotency_key)
        if args is None:
            return
        res = fetch(*args)
        seen += len(res.items)
        yield res
        if not res.next_cursor or not res.items:
            return
        cursor = res.next_cursor
        page += 1


async def aiter_pages(
    fetch: Callable[[dict[str, Any], str | None], Awaitable[P]],
    params: Mapping[str, Any],
    *,
    max_items: int | None,
    max_pages: int | None,
    idempotency_key: str | None,
) -> AsyncIterator[P]:
    cursor = params.get("cursor")
    seen = 0
    page = 1
    while True:
        args = _page_args(params, page, seen, cursor, max_items, max_pages, idempotency_key)
        if args is None:
            return
        res = await fetch(*args)
        seen += len(res.items)
        yield res
        if not res.next_cursor or not res.items:
            return
        cursor = res.next_cursor
        page += 1
