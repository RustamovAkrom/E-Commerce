"""Click (UZ) payment provider.

Click uses a two-step server callback flow (``Prepare`` then ``Complete``) with
an MD5 signature over the request fields plus the merchant secret key. Here we
implement signature verification and status mapping; building the hosted
checkout link follows Click's documented URL scheme.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

from src.config import settings
from src.core.enums import PaymentProvider, PaymentStatus
from src.core.exceptions import PaymentError
from src.modules.payments.providers.base import (
    BasePaymentProvider,
    PaymentInitResult,
    WebhookResult,
)

_CHECKOUT_BASE = "https://my.click.uz/services/pay"

# Click action codes in the callback payload.
_ACTION_PREPARE = "0"
_ACTION_COMPLETE = "1"


class ClickProvider(BasePaymentProvider):
    name = PaymentProvider.CLICK

    def _sign(self, *parts: str) -> str:
        """MD5 of the concatenated parts plus the secret, per Click's spec."""
        raw = "".join(parts) + settings.CLICK_SECRET_KEY
        return hashlib.md5(raw.encode()).hexdigest()  # noqa: S324 - provider-mandated

    async def create_payment(
        self,
        *,
        payment_id: str,
        order_id: str,
        amount: Decimal,
        currency: str,
        return_url: str | None,
    ) -> PaymentInitResult:
        if not settings.CLICK_SERVICE_ID or not settings.CLICK_MERCHANT_ID:
            raise PaymentError("Click is not configured.")
        query: dict[str, Any] = {
            "service_id": settings.CLICK_SERVICE_ID,
            "merchant_id": settings.CLICK_MERCHANT_ID,
            "amount": str(amount),
            "transaction_param": order_id,
        }
        if return_url:
            query["return_url"] = return_url
        checkout_url = f"{_CHECKOUT_BASE}?{urlencode(query)}"
        return PaymentInitResult(checkout_url=checkout_url, params=query)

    async def parse_webhook(
        self, headers: dict[str, str], body: bytes
    ) -> WebhookResult:
        try:
            data: dict[str, Any] = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise PaymentError("Malformed Click callback.") from exc

        required = (
            "click_trans_id",
            "service_id",
            "merchant_trans_id",
            "amount",
            "action",
            "sign_time",
            "sign_string",
        )
        if any(field not in data for field in required):
            raise PaymentError("Incomplete Click callback.")

        merchant_prepare_id = str(data.get("merchant_prepare_id", ""))
        expected = self._sign(
            str(data["click_trans_id"]),
            str(data["service_id"]),
            merchant_prepare_id,
            str(data["merchant_trans_id"]),
            str(data["amount"]),
            str(data["action"]),
            str(data["sign_time"]),
        )
        if not _consteq(expected, str(data["sign_string"])):
            raise PaymentError("Invalid Click signature.")

        error_code = int(data.get("error", 0))
        action = str(data["action"])
        if error_code < 0:
            status = PaymentStatus.FAILED
        elif action == _ACTION_COMPLETE:
            status = PaymentStatus.PAID
        elif action == _ACTION_PREPARE:
            status = PaymentStatus.PROCESSING
        else:
            status = PaymentStatus.PENDING

        return WebhookResult(
            provider_payment_id=str(data["click_trans_id"]),
            status=status,
            order_id=str(data["merchant_trans_id"]),
            amount=Decimal(str(data["amount"])),
            raw=data,
        )


def _consteq(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a, b)
