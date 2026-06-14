"""Payme (UZ) payment provider.

Payme uses a JSON-RPC Merchant API authenticated with HTTP Basic where the
password is the merchant key. Customers are sent to a hosted checkout whose
parameters are base64-encoded. We verify the Basic credentials on callbacks and
map the JSON-RPC method onto a payment status.
"""

from __future__ import annotations

import base64
import json
from decimal import Decimal
from typing import Any

from src.config import settings
from src.core.enums import PaymentProvider, PaymentStatus
from src.core.exceptions import PaymentError
from src.modules.payments.providers.base import (
    BasePaymentProvider,
    PaymentInitResult,
    WebhookResult,
)

_CHECKOUT_BASE = "https://checkout.paycom.uz"

# JSON-RPC methods Payme calls on the merchant.
_METHOD_PERFORM = "PerformTransaction"
_METHOD_CANCEL = "CancelTransaction"
_METHOD_CREATE = "CreateTransaction"


class PaymeProvider(BasePaymentProvider):
    name = PaymentProvider.PAYME

    async def create_payment(
        self,
        *,
        payment_id: str,
        order_id: str,
        amount: Decimal,
        currency: str,
        return_url: str | None,
    ) -> PaymentInitResult:
        if not settings.PAYME_ID or not settings.PAYME_KEY:
            raise PaymentError("Payme is not configured.")
        # Payme amounts are in tiyin (1/100 of the som).
        amount_tiyin = int((amount * 100).to_integral_value())
        parts = [
            f"m={settings.PAYME_ID}",
            f"ac.order_id={order_id}",
            f"a={amount_tiyin}",
        ]
        if return_url:
            parts.append(f"c={return_url}")
        encoded = base64.b64encode(";".join(parts).encode()).decode()
        checkout_url = f"{_CHECKOUT_BASE}/{encoded}"
        return PaymentInitResult(
            checkout_url=checkout_url, params={"amount_tiyin": amount_tiyin}
        )

    def _check_auth(self, headers: dict[str, str]) -> None:
        header = headers.get("authorization") or headers.get("Authorization", "")
        if not header.startswith("Basic "):
            raise PaymentError("Missing Payme authorization.")
        try:
            decoded = base64.b64decode(header[6:]).decode()
            _, _, password = decoded.partition(":")
        except (ValueError, UnicodeDecodeError) as exc:
            raise PaymentError("Malformed Payme authorization.") from exc
        import hmac

        if not hmac.compare_digest(password, settings.PAYME_KEY):
            raise PaymentError("Invalid Payme credentials.")

    async def parse_webhook(
        self, headers: dict[str, str], body: bytes
    ) -> WebhookResult:
        self._check_auth(headers)
        try:
            data: dict[str, Any] = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise PaymentError("Malformed Payme callback.") from exc

        method = data.get("method", "")
        params = data.get("params", {}) or {}
        account = params.get("account", {}) or {}
        txn_id = str(params.get("id", ""))
        if not txn_id:
            raise PaymentError("Payme callback missing transaction id.")

        if method == _METHOD_PERFORM:
            status = PaymentStatus.PAID
        elif method == _METHOD_CANCEL:
            status = PaymentStatus.REFUNDED
        elif method == _METHOD_CREATE:
            status = PaymentStatus.PROCESSING
        else:
            status = PaymentStatus.PENDING

        amount = params.get("amount")
        return WebhookResult(
            provider_payment_id=txn_id,
            status=status,
            order_id=account.get("order_id"),
            amount=Decimal(amount) / 100 if amount is not None else None,
            raw=data,
        )
