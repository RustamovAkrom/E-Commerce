"""FastAPI application factory.

Wires together configuration, middleware, exception handling, observability and
every module router. The platform is always a multi-vendor marketplace, so the
``vendors`` router is mounted unconditionally.

Run with: ``uvicorn src.main:app``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from src.core.database import async_session_maker
from sqladmin import Admin
from src.core.database import async_session_maker
from src.core.startup import create_superadmin

# Importing the registry guarantees every ORM model is registered on
# Base.metadata before the app (and Alembic) touch the database.
import src.models_registry  # noqa: F401
from src.admin.router import router as admin_router
from src.admin.sqladmin_setup import (
    CategoryAdmin,
    CourierAdmin,
    DeliveryAssignmentAdmin,
    OrderAdmin,
    OrderItemAdmin,
    ProductAdmin,
    ProductImageAdmin,
    StockMovementAdmin,
    UserAdmin,
    VendorAdmin,
)
from src.config import settings
from src.core.database import engine
from src.core.exceptions import AppException
from src.core.middleware import register_middleware
from src.core.rate_limit import limiter
from src.core.redis import close_redis
from src.modules.auth.router import router as auth_router
from src.modules.cart.router import router as cart_router
from src.modules.catalog.router import router as catalog_router
from src.modules.delivery.router import router as delivery_router
from src.modules.inventory.router import router as inventory_router
from src.modules.notifications.router import router as notifications_router
from src.modules.orders.router import router as orders_router
from src.modules.payments.router import router as payments_router
from src.modules.reviews.router import router as reviews_router
from src.modules.shipping.router import router as shipping_router
from src.modules.users.router import router as users_router
from src.modules.vendors.router import router as vendors_router

logger = structlog.get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown hooks."""
    logger.info(
        "startup",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
    )
    # Auto-provision the superadmin on first boot.


    async with async_session_maker() as session:
        await create_superadmin(session)
        await session.commit()
    yield
    await close_redis()
    logger.info("shutdown")


def _configure_sentry() -> None:
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment="debug" if settings.DEBUG else "production",
        )


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _handle_app_exception(
        request: Request, exc: AppException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(RateLimitExceeded)
    async def _handle_rate_limit(
        request: Request, exc: RateLimitExceeded
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "message": "Too many requests.",
                "details": {"limit": str(exc.limit.limit)},
            },
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all: log + capture to Sentry, never leak internals."""
        logger.exception("unhandled_exception", path=str(request.url.path))
        if settings.SENTRY_DSN:
            sentry_sdk.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "Something went wrong. Please try again.",
            },
        )


def _register_routers(app: FastAPI) -> None:
    api = settings.API_V1_PREFIX
    app.include_router(auth_router, prefix=f"{api}/auth", tags=["auth"])
    app.include_router(users_router, prefix=f"{api}/users", tags=["users"])
    app.include_router(
        catalog_router, prefix=f"{api}/catalog", tags=["catalog"]
    )
    app.include_router(
        inventory_router, prefix=f"{api}/inventory", tags=["inventory"]
    )
    app.include_router(cart_router, prefix=f"{api}/cart", tags=["cart"])
    app.include_router(orders_router, prefix=f"{api}/orders", tags=["orders"])
    app.include_router(
        payments_router, prefix=f"{api}/payments", tags=["payments"]
    )
    app.include_router(
        shipping_router, prefix=f"{api}/shipping", tags=["shipping"]
    )
    app.include_router(
        delivery_router, prefix=f"{api}/delivery", tags=["delivery"]
    )
    # Reviews paths are product- and review-scoped; mount at the API root.
    app.include_router(reviews_router, prefix=api, tags=["reviews"])
    app.include_router(
        notifications_router,
        prefix=f"{api}/notifications",
        tags=["notifications"],
    )
    app.include_router(admin_router, prefix=f"{api}/admin", tags=["admin"])

    # Multi-vendor marketplace — vendors are always active.
    app.include_router(
        vendors_router, prefix=f"{api}/vendors", tags=["vendors"]
    )

    # ─── SQLAdmin panel ──────────────────────────────────────────────────


    admin = Admin(
        app,
        session_maker=async_session_maker,
        base_url="/admin/panel",
        title="Platform Admin",
    )
    admin.add_view(ProductAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductImageAdmin)
    admin.add_view(StockMovementAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(OrderItemAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(VendorAdmin)
    admin.add_view(CourierAdmin)
    admin.add_view(DeliveryAssignmentAdmin)


def create_app() -> FastAPI:
    """Application factory — builds and returns the configured FastAPI app."""
    _configure_sentry()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Rate limiting (slowapi): bind the limiter and add its middleware.
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    register_middleware(app)
    _register_exception_handlers(app)
    _register_routers(app)

    # Prometheus metrics at /metrics.
    Instrumentator().instrument(app).expose(
        app, endpoint="/metrics", include_in_schema=False
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()
