"""Payment HTTP endpoints.

Customer-facing: start a payment, list and read own payments. Provider-facing:
asynchronous webhook callbacks (unauthenticated at the HTTP layer — each
provider adapter verifies its own signature/credentials inside the service).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.core.dependencies import CurrentUser, DbSession, RedisClient
from src.core.enums import PaymentProvider
from src.core.pagination import Page, PaginationParams
from src.modules.payments.schemas import (
    PaymentInitRequest,
    PaymentInitResponse,
    PaymentResponse,
    PaymentWebhookResponse,
)
from src.modules.payments.service import PaymentService

router = APIRouter()


@router.post("/initiate", response_model=PaymentInitResponse)
async def initiate_payment(
    data: PaymentInitRequest,
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> PaymentInitResponse:
    payment = await PaymentService(db, redis_client).initiate(
        user.id, data  # type: ignore[attr-defined]
    )
    return PaymentInitResponse(
        payment_id=payment.id,
        provider=payment.provider,
        status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        checkout_url=getattr(payment, "checkout_url", None),
        params=getattr(payment, "checkout_params", {}) or {},
    )


@router.get("", response_model=Page[PaymentResponse])
async def list_my_payments(
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
    params: Annotated[PaginationParams, Depends()],
) -> Page[PaymentResponse]:
    page = await PaymentService(db, redis_client).list_for_user(
        user.id, params  # type: ignore[attr-defined]
    )
    return page.map(PaymentResponse.model_validate)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_my_payment(
    payment_id: uuid.UUID,
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> PaymentResponse:
    payment = await PaymentService(db, redis_client).get_for_user(
        payment_id, user.id  # type: ignore[attr-defined]
    )
    return PaymentResponse.model_validate(payment)


# --- Provider webhooks ------------------------------------------------------
@router.post("/webhook/{provider}", response_model=PaymentWebhookResponse)
async def payment_webhook(
    provider: PaymentProvider,
    request: Request,
    db: DbSession,
    redis_client: RedisClient,
) -> PaymentWebhookResponse:
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    await PaymentService(db, redis_client).handle_webhook(provider, headers, body)
    return PaymentWebhookResponse(received=True)
