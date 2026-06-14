"""Payment Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field

from src.core.enums import PaymentProvider, PaymentStatus
from src.core.schemas import ORMSchema, StrictSchema


class PaymentInitRequest(StrictSchema):
    """Start a payment for an existing order via a chosen provider."""

    order_id: uuid.UUID
    provider: PaymentProvider
    # Where the provider should send the customer back to after checkout.
    return_url: str | None = Field(default=None, max_length=2048)


class PaymentInitResponse(ORMSchema):
    payment_id: uuid.UUID
    provider: PaymentProvider
    status: PaymentStatus
    amount: Decimal
    currency: str
    # Hosted checkout URL the client should redirect the customer to.
    checkout_url: str | None = None
    # Extra provider-specific params (e.g. form fields) the client may need.
    params: dict[str, Any] = Field(default_factory=dict)


class PaymentResponse(ORMSchema):
    id: uuid.UUID
    order_id: uuid.UUID
    user_id: uuid.UUID
    provider: PaymentProvider
    status: PaymentStatus
    amount: Decimal
    currency: str
    provider_payment_id: str | None
    created_at: datetime


class PaymentWebhookResponse(StrictSchema):
    """Response returned to the payment provider's webhook call.

    Providers expect different ack shapes; this generic body is adequate for
    Stripe-style ``{"received": true}`` acknowledgements. Click/Payme handlers
    return their own provider-mandated JSON directly from the router.
    """

    received: bool = True
