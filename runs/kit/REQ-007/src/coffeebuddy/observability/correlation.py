from __future__ import annotations

import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass, replace
from typing import Mapping, Optional

__all__ = [
    "RequestContext",
    "new_correlation_id",
    "correlation_id_from_headers",
    "push_request_context",
    "reset_request_context",
    "get_request_context",
    "update_request_context",
]

_DEFAULT_CONTEXT: ContextVar[Optional["RequestContext"]] = ContextVar(
    "coffeebuddy_request_context", default=None
)


@dataclass(frozen=True)
class RequestContext:
    """
    Captures per-request observability identifiers.

    Attributes:
        correlation_id: Traces a logical request through logs/metrics.
        channel_id: Optional Slack channel identifier for contextual logs.
        run_id: Optional Coffee run identifier when known.
    """

    correlation_id: str
    channel_id: Optional[str] = None
    run_id: Optional[str] = None


def new_correlation_id() -> str:
    """Return a random correlation identifier."""
    return uuid.uuid4().hex


def correlation_id_from_headers(
    headers: Mapping[str, str], fallback: Optional[str] = None
) -> str:
    """
    Resolve a correlation ID from canonical Slack/Kong headers.

    Precedence:
        1. X-Correlation-ID
        2. X-Slack-Request-Id
        3. X-Request-Id
        4. Generated UUID (or provided fallback)
    """
    lowered = {k.lower(): v for k, v in headers.items()}
    for key in ("x-correlation-id", "x-slack-request-id", "x-request-id"):
        value = lowered.get(key)
        if value:
            return value
    return fallback or new_correlation_id()


def push_request_context(
    *, correlation_id: Optional[str] = None, channel_id: Optional[str] = None, run_id: Optional[str] = None
) -> Token:
    """
    Bind a RequestContext to the running task.

    Returns:
        ContextVar token so callers can reset after the request completes.
    """
    ctx = RequestContext(correlation_id or new_correlation_id(), channel_id=channel_id, run_id=run_id)
    return _DEFAULT_CONTEXT.set(ctx)


def reset_request_context(token: Token) -> None:
    """Reset the context to the previous value using the provided token."""
    _DEFAULT_CONTEXT.reset(token)


def get_request_context() -> Optional[RequestContext]:
    """Fetch the currently bound context, if any."""
    return _DEFAULT_CONTEXT.get()


def update_request_context(**kwargs: Optional[str]) -> None:
    """
    Replace fields on the bound context.

    Raises:
        RuntimeError: when no context is currently bound.
    """
    ctx = _DEFAULT_CONTEXT.get()
    if ctx is None:
        raise RuntimeError("No request context bound to update.")
    _DEFAULT_CONTEXT.set(replace(ctx, **kwargs))