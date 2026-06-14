"""Payment business logic.

Orchestrates the provider adapters and persistence:

* ``initiate`` creates a :class:`Payment` row and asks the chosen provider for a
  checkout URL.
* ``handle_webhook`` authenticates a provider callback, updates the payment
  idempotently, and — on success — transitions the order to ``PAID``.

Webhook idempotency is anchored on ``(provider, provider_payment_id)``: a repeat
callback for an already-final payment is a no-op.
"""

from __future__ import annotations

import uuid

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import OrderStatus, PaymentProvider, PaymentStatus
from src.core.exceptions import NotFoundError, PaymentError, PermissionDeniedError
from src.core.pagination import Page, PaginationParams
from src.modules.orders.repository import OrderRepository
from src.modules.orders.service import OrderService
from src.modules.payments.models import Payment
from src.modules.payments.providers import WebhookResult, get_provider
from src.modules.payments.repository import PaymentRepository
from src.modules.payments.schemas import PaymentInitRequest

# Statuses from which a fresh payment attempt makes sense.
_PAYABLE_ORDER_STATUSES = {OrderStatus.PENDING, OrderStatus.CONFIRMED}
# Once a payment reaches one of these it will not change again.
_FINAL_PAYMENT_STATUSES = {
    PaymentStatus.PAID,
    PaymentStatus.FAILED,
    PaymentStatus.REFUNDED,
}


class PaymentService:
    def __init__(self, session: AsyncSession, redis_client: redis.Redis) -> None:
        self.session = session
        self.redis = redis_client
        self.repo = PaymentRepository(session)
        self.orders = OrderRepository(session)
        self.order_service = OrderService(session, redis_client)

    async def initiate(
        self, user_id: uuid.UUID, data: PaymentInitRequest
    ) -> Payment:
        order = await self.orders.get(data.order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        if order.user_id != user_id:
            raise PermissionDeniedError("This order does not belong to you.")
        if order.status == OrderStatus.PAID:
            raise PaymentError("Order is already paid.")
        if order.status not in _PAYABLE_ORDER_STATUSES:
            raise PaymentError(
                "Order cannot be paid in its current state.",
                details={"status": order.status.value},
            )

        payment = Payment(
            order_id=order.id,
            user_id=user_id,
            provider=data.provider,
            status=PaymentStatus.PENDING,
            amount=order.total_amount,
            currency=order.currency,
        )
        self.session.add(payment)
        await self.session.flush()  # assigns payment.id

        provider = get_provider(data.provider)
        result = await provider.create_payment(
            payment_id=str(payment.id),
            order_id=str(order.id),
            amount=order.total_amount,
            currency=order.currency,
            return_url=data.return_url,
        )
        if result.provider_payment_id:
            payment.provider_payment_id = result.provider_payment_id
        payment.raw_payload = result.raw or None
        payment.status = PaymentStatus.PROCESSING
        self.session.add(payment)
        await self.session.flush()

        # Stash the checkout details on the instance for the router (not
        # persisted columns — purely transport).
        payment.checkout_url = result.checkout_url  # type: ignore[attr-defined]
        payment.checkout_params = result.params  # type: ignore[attr-defined]
        return payment

    async def handle_webhook(
        self, provider_name: PaymentProvider, headers: dict[str, str], body: bytes
    ) -> Payment:
        provider = get_provider(provider_name)
        # Raises PaymentError on signature/credential failure.
        result = await provider.parse_webhook(headers, body)
        payment = await self._resolve_payment(provider_name, result)

        # Idempotent: ignore callbacks that don't move a final payment.
        if payment.status in _FINAL_PAYMENT_STATUSES:
            return payment

        payment.provider_payment_id = result.provider_payment_id
        payment.status = result.status
        payment.raw_payload = result.raw or payment.raw_payload
        self.session.add(payment)
        await self.session.flush()

        if result.status == PaymentStatus.PAID:
            await self.order_service.mark_paid(payment.order_id)

        return payment

    async def _resolve_payment(
        self, provider_name: PaymentProvider, result: WebhookResult
    ) -> Payment:
        """Find the Payment a callback refers to, by txn id or by order."""
        existing = await self.repo.get_by_provider_txn(
            provider_name, result.provider_payment_id
        )
        if existing is not None:
            return existing
        # Click/Payme assign the transaction id only at callback time; fall back
        # to the latest pending payment for the echoed order.
        if result.order_id:
            try:
                order_id = uuid.UUID(result.order_id)
            except ValueError as exc:
                raise PaymentError("Callback referenced an invalid order.") from exc
            payments = await self.repo.list_for_order(order_id)
            for payment in payments:
                if (
                    payment.provider == provider_name
                    and payment.status not in _FINAL_PAYMENT_STATUSES
                ):
                    return payment
        raise NotFoundError("No matching payment for this callback.")

    async def get_for_user(
        self, payment_id: uuid.UUID, user_id: uuid.UUID
    ) -> Payment:
        payment = await self.repo.get(payment_id)
        if payment is None:
            raise NotFoundError("Payment not found.")
        if payment.user_id != user_id:
            raise PermissionDeniedError("This payment does not belong to you.")
        return payment

    async def list_for_user(
        self, user_id: uuid.UUID, params: PaginationParams
    ) -> Page[Payment]:
        items, total = await self.repo.list_for_user(
            user_id, offset=params.offset, limit=params.limit
        )
        return Page.create(items, total, params)
