"""Stripe payment provider.

Stripe is integrated over its REST API with ``httpx`` (the official SDK is not a
dependency). We create a Checkout Session and verify webhook authenticity using
the ``Stripe-Signature`` header HMAC scheme.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal
from typing import Any

import httpx

from src.config import settings
from src.core.enums import PaymentProvider, PaymentStatus
from src.core.exceptions import PaymentError
from src.modules.payments.providers.base import (
    BasePaymentProvider,
    PaymentInitResult,
    WebhookResult,
)

_API_BASE = "https://api.stripe.com/v1"
# Reject webhook timestamps older than this to defend against replay.
_SIGNATURE_TOLERANCE_SECONDS = 300

# Stripe Checkout event -> our status.
_EVENT_STATUS = {
    "checkout.session.completed": PaymentStatus.PAID,
    "checkout.session.async_payment_succeeded": PaymentStatus.PAID,
    "checkout.session.async_payment_failed": PaymentStatus.FAILED,
    "checkout.session.expired": PaymentStatus.FAILED,
    "charge.refunded": PaymentStatus.REFUNDED,
}


class StripeProvider(BasePaymentProvider):
    name = PaymentProvider.STRIPE

    async def create_payment(
        self,
        *,
        payment_id: str,
        order_id: str,
        amount: Decimal,
        currency: str,
        return_url: str | None,
    ) -> PaymentInitResult:
        if not settings.STRIPE_SECRET_KEY:
            raise PaymentError("Stripe is not configured.")
        # Stripe expects the smallest currency unit (e.g. cents).
        unit_amount = int((amount * 100).to_integral_value())
        success_url = return_url or f"{settings.BACKEND_API_URL}/payments/success"
        form: dict[str, str] = {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": success_url,
            "client_reference_id": order_id,
            "metadata[order_id]": order_id,
            "metadata[payment_id]": payment_id,
            "line_items[0][quantity]": "1",
            "line_items[0][price_data][currency]": currency.lower(),
            "line_items[0][price_data][unit_amount]": str(unit_amount),
            "line_items[0][price_data][product_data][name]": f"Order {order_id}",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{_API_BASE}/checkout/sessions",
                    data=form,
                    auth=(settings.STRIPE_SECRET_KEY, ""),
                )
        except httpx.HTTPError as exc:
            raise PaymentError("Could not reach Stripe.") from exc
        if resp.status_code >= 400:
            raise PaymentError(
                "Stripe rejected the checkout session.",
                details={"status": resp.status_code},
            )
        payload: dict[str, Any] = resp.json()
        return PaymentInitResult(
            provider_payment_id=payload.get("id"),
            checkout_url=payload.get("url"),
            raw=payload,
        )

    def _verify_signature(self, headers: dict[str, str], body: bytes) -> None:
        secret = settings.STRIPE_WEBHOOK_SECRET
        if not secret:
            raise PaymentError("Stripe webhook secret is not configured.")
        sig_header = headers.get("stripe-signature") or headers.get(
            "Stripe-Signature", ""
        )
        parts = dict(
            item.split("=", 1) for item in sig_header.split(",") if "=" in item
        )
        timestamp = parts.get("t")
        signature = parts.get("v1")
        if not timestamp or not signature:
            raise PaymentError("Malformed Stripe signature header.")
        if abs(time.time() - int(timestamp)) > _SIGNATURE_TOLERANCE_SECONDS:
            raise PaymentError("Stripe webhook timestamp outside tolerance.")
        signed_payload = f"{timestamp}.".encode() + body
        expected = hmac.new(
            secret.encode(), signed_payload, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise PaymentError("Invalid Stripe signature.")

    async def parse_webhook(
        self, headers: dict[str, str], body: bytes
    ) -> WebhookResult:
        self._verify_signature(headers, body)
        try:
            event: dict[str, Any] = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise PaymentError("Malformed Stripe event.") from exc

        event_type = event.get("type", "")
        obj = event.get("data", {}).get("object", {}) or {}
        status = _EVENT_STATUS.get(event_type, PaymentStatus.PROCESSING)
        order_id = (obj.get("metadata", {}) or {}).get("order_id") or obj.get(
            "client_reference_id"
        )
        amount_total = obj.get("amount_total")
        return WebhookResult(
            provider_payment_id=str(obj.get("id", event.get("id", ""))),
            status=status,
            order_id=order_id,
            amount=Decimal(amount_total) / 100 if amount_total is not None else None,
            raw=event,
        )
