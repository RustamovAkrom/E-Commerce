"""SMS channel via the Eskiz.uz gateway.

Eskiz uses a token-based REST API: authenticate with email/password to obtain a
bearer token, then POST the message. The token is cached on the instance for
the process lifetime and refreshed on a 401. Missing credentials degrade to a
soft failure rather than raising.
"""

from __future__ import annotations

import httpx

from src.config import settings
from src.modules.notifications.channels.base import BaseChannel, DeliveryResult


class SMSChannel(BaseChannel):
    name = "sms"

    def __init__(self) -> None:
        self._token: str | None = None

    async def _authenticate(self, client: httpx.AsyncClient) -> str | None:
        resp = await client.post(
            f"{settings.ESKIZ_BASE_URL}/auth/login",
            data={
                "email": settings.ESKIZ_EMAIL,
                "password": settings.ESKIZ_PASSWORD,
            },
        )
        if resp.status_code != httpx.codes.OK:
            return None
        return resp.json().get("data", {}).get("token")

    async def send(
        self,
        *,
        destination: str,
        subject: str | None,
        body: str,
    ) -> DeliveryResult:
        if not (settings.ESKIZ_EMAIL and settings.ESKIZ_PASSWORD):
            return DeliveryResult(
                success=False, detail="SMS gateway is not configured."
            )
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if self._token is None:
                    self._token = await self._authenticate(client)
                if self._token is None:
                    return DeliveryResult(
                        success=False, detail="SMS authentication failed."
                    )
                resp = await client.post(
                    f"{settings.ESKIZ_BASE_URL}/message/sms/send",
                    headers={"Authorization": f"Bearer {self._token}"},
                    data={
                        "mobile_phone": destination.lstrip("+"),
                        "message": body,
                        "from": "4546",
                    },
                )
                if resp.status_code == httpx.codes.UNAUTHORIZED:
                    # Token expired — refresh once and retry.
                    self._token = await self._authenticate(client)
                    if self._token is None:
                        return DeliveryResult(
                            success=False, detail="SMS re-authentication failed."
                        )
                    resp = await client.post(
                        f"{settings.ESKIZ_BASE_URL}/message/sms/send",
                        headers={"Authorization": f"Bearer {self._token}"},
                        data={
                            "mobile_phone": destination.lstrip("+"),
                            "message": body,
                            "from": "4546",
                        },
                    )
                if resp.status_code not in (httpx.codes.OK, httpx.codes.CREATED):
                    return DeliveryResult(
                        success=False,
                        detail=f"SMS gateway returned {resp.status_code}.",
                    )
        except Exception as exc:  # noqa: BLE001 - report, never propagate
            return DeliveryResult(success=False, detail=str(exc))
        return DeliveryResult(success=True)
