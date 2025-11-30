"""
Observability utilities for CoffeeBuddy.

REQ-007 delivers the common instrumentation hooks that subsequent
application REQs will compose: correlation IDs, structured logging,
Prometheus metrics, and HTTP-safe error handling.
"""

from .correlation import (
    RequestContext,
    correlation_id_from_headers,
    get_request_context,
    push_request_context,
    reset_request_context,
    update_request_context,
)
from .errors import CoffeeBuddyError
from .logging import configure_json_logging
from .metrics import (
    MetricsSuite,
    RequestMetricsRecorder,
    RunMetricsRecorder,
    build_metrics_suite,
    render_registry,
)
from .middleware import CorrelationIdMiddleware, ErrorHandlingMiddleware

__all__ = [
    "RequestContext",
    "correlation_id_from_headers",
    "get_request_context",
    "push_request_context",
    "reset_request_context",
    "update_request_context",
    "CoffeeBuddyError",
    "configure_json_logging",
    "MetricsSuite",
    "RequestMetricsRecorder",
    "RunMetricsRecorder",
    "build_metrics_suite",
    "render_registry",
    "CorrelationIdMiddleware",
    "ErrorHandlingMiddleware",
]