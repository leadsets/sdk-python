from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

import httpx

from ..types import EmailVerifyResponse

if TYPE_CHECKING:
    from .._client import AsyncLeadsets, Leadsets


def _body(email: str | Sequence[str] | None, emails: Sequence[str] | None) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if isinstance(email, str):
        body["email"] = email
    elif email is not None:
        body["emails"] = list(email)
    if emails is not None:
        body["emails"] = [*body.get("emails", []), *emails]
    if not body:
        raise TypeError("emails.verify: pass an email, a list of emails, or emails=[...]")
    return body


class Emails:
    def __init__(self, client: Leadsets) -> None:
        self._client = client

    def verify(
        self,
        email: str | Sequence[str] | None = None,
        *,
        emails: Sequence[str] | None = None,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> EmailVerifyResponse:
        """POST /v1/emails/verify. One email, or up to 100. 1 enrichment record per email checked.

        ``verify("a@b.co")``, ``verify(["a@b.co", "c@d.co"])`` or ``verify(emails=[...])``.
        """
        return self._client.request(
            "POST",
            "/emails/verify",
            EmailVerifyResponse,
            body=_body(email, emails),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )


class AsyncEmails:
    def __init__(self, client: AsyncLeadsets) -> None:
        self._client = client

    async def verify(
        self,
        email: str | Sequence[str] | None = None,
        *,
        emails: Sequence[str] | None = None,
        idempotency_key: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        max_retries: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> EmailVerifyResponse:
        """POST /v1/emails/verify. One email, or up to 100. 1 enrichment record per email checked."""
        return await self._client.request(
            "POST",
            "/emails/verify",
            EmailVerifyResponse,
            body=_body(email, emails),
            idempotent=True,
            idempotency_key=idempotency_key,
            timeout=timeout,
            max_retries=max_retries,
            extra_headers=extra_headers,
        )
