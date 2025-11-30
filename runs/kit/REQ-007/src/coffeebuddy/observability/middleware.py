from __future__ import annotations

import logging
from time import perf_counter
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .correlation import correlation_id_from_headers, push_request_context, reset_request_context
from .errors import CoffeeBuddyError
from .metrics import RequestMetricsRecorder

__all__ = ["CorrelationIdMiddleware", "ErrorHandlingMiddleware"]


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Ensures every HTTP request has a correlation identifier propagated to logs.
    """

    def __init__(self, app, header_name: str = "X-Correlation-ID") -> None:
        super().__init__(app)
        self._header_name = header_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = correlation_id_from_headers(request.headers)
        token = push_request_context(correlation_id=correlation_id)
        try:
            response = await call_next(request)
        finally:
            reset_request_context(token)
        response.headers[self._header_name] = correlation_id
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Converts domain exceptions into Slack-safe JSON bodies and records metrics.
    """

    def __init__(
        self,
        app,
        *,
        metrics: Optional[RequestMetricsRecorder] = None,
        request_type_resolver: Optional[Callable[[Request], str]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(app)
        self._metrics = metrics
        self._request_type_resolver = request_type_resolver or _default_request_type_resolver
        self._logger = logger or logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except CoffeeBuddyError as exc:
            status_code = exc.status_code
            self._logger.warning(
                exc.log_message or "CoffeeBuddy domain error",
                extra={"error_code": exc.error_code},
            )
            return JSONResponse(
                {"ok": False, "error": exc.user_message, "code": exc.error_code},
                status_code=status_code,
            )
        except Exception:
            status_code = 500
            self._logger.exception("Unhandled CoffeeBuddy error")
            return JSONResponse(
                {"ok": False, "error": "Unexpected error. Please retry or contact support."},
                status_code=status_code,
            )
        finally:
            duration = perf_counter() - started
            if self._metrics is not None:
                request_type = self._request_type_resolver(request)
                self._metrics.observe(request_type, status_code, duration)


def _default_request_type_resolver(request: Request) -> str:
    """
    Derives a request type label for metrics.

    Preference order:
        1. X-Slack-Request-Type header (slash, interaction, etc.)
        2. Request path (useful for internal endpoints)
    """
    return request.headers.get("X-Slack-Request-Type") or request.scope.get("path", "http")