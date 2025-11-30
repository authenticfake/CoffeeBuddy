import io
import json
import logging

from coffeebuddy.observability.correlation import push_request_context, reset_request_context
from coffeebuddy.observability.logging import configure_json_logging


def test_configure_json_logging_emits_contextual_json() -> None:
    stream = io.StringIO()
    logger = configure_json_logging(level=logging.INFO, stream=stream)

    token = push_request_context(correlation_id="corr-xyz", channel_id="C123", run_id="run-1")
    logger.info("hello world", extra={"event": "demo"})
    reset_request_context(token)

    payload = json.loads(stream.getvalue())
    assert payload["correlation_id"] == "corr-xyz"
    assert payload["channel_id"] == "C123"
    assert payload["run_id"] == "run-1"
    assert payload["message"] == "hello world"
    assert payload["extra"]["event"] == "demo"