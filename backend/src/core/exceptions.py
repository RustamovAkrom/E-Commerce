"""Application exception hierarchy.

Services raise these domain exceptions; a single exception handler in
``main.py`` maps them to HTTP responses. Keeping HTTP status codes here is a
pragmatic compromise so handlers stay trivial.
"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base class for all handled application errors."""

    status_code: int = 500
    error_code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = 404
    error_code = "not_found"
    message = "Resource not found."


class AlreadyExistsError(AppException):
    status_code = 409
    error_code = "already_exists"
    message = "Resource already exists."


class ValidationError(AppException):
    status_code = 422
    error_code = "validation_error"
    message = "Validation failed."


class AuthenticationError(AppException):
    status_code = 401
    error_code = "authentication_error"
    message = "Could not validate credentials."


class PermissionDeniedError(AppException):
    status_code = 403
    error_code = "permission_denied"
    message = "You do not have permission to perform this action."


class ConflictError(AppException):
    status_code = 409
    error_code = "conflict"
    message = "The request conflicts with the current state."


class PaymentError(AppException):
    status_code = 402
    error_code = "payment_error"
    message = "Payment could not be processed."


class RateLimitError(AppException):
    status_code = 429
    error_code = "rate_limited"
    message = "Too many requests."


class CacheError(AppException):
    status_code = 503
    error_code = "cache_error"
    message = "Cache service unavailable."
