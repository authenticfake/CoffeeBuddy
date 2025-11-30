from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import IO, Any, Dict, Optional, Set

from .correlation import get_request_context

__all__ = ["configure_json_logging", "JsonLogFormatter", "ContextFilter"]


class ContextFilter(logging.Filter):
    """Injects correlation/run/channel identifiers into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = get_request_context()
        record.correlation_id = getattr(record, "correlation_id", None) or (ctx.correlation_id if ctx else None)
        record.channel_id = getattr(record, "channel_id", None) or (ctx.channel_id if ctx else None)
        record.run_id = getattr(record, "run_id", None) or (ctx.run_id if ctx else None)
        return True


class JsonLogFormatter(logging.Formatter):
    """
    Structured JSON formatter that avoids leaking sensitive data.

    Only whitelisted metadata is preserved; arbitrary record attributes are
    merged under the `extra` key to prevent namespace collisions.
    """

    _RESERVED_FIELDS: Set[str] = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
            "channel_id": getattr(record, "channel_id", None),
            "run_id": getattr(record, "run_id", None),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        extras: Dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key not in self._RESERVED_FIELDS and key not in payload:
                extras[key] = value
        if extras:
            payload["extra"] = extras

        return json.dumps(payload, ensure_ascii=False)


def configure_json_logging(
    level: int = logging.INFO,
    *,
    stream: Optional[IO[str]] = None,
    logger_name: str = "coffeebuddy",
) -> logging.Logger:
    """
    Configure the CoffeeBuddy logger hierarchy for JSON output.

    Args:
        level: Minimum severity to emit.
        stream: Optional stream for handler (defaults to stderr).
        logger_name: The logger namespace to configure.

    Returns:
        The configured logger instance for convenience chaining.
    """
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(ContextFilter())

    logger = logging.getLogger(logger_name)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    return logger