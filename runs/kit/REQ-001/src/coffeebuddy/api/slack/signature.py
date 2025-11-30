from __future__ import annotations

import hmac
import logging
from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable, Mapping

from .errors import SlackVerificationError

LOGGER = logging.getLogger("coffeebuddy.api.slack.signature")


class SlackRequestVerifier:
    """Validates Slack signatures and prevents replayed requests."""

    def __init__(
        self,
        signing_secret: str,
        *,
        tolerance_seconds: int = 300,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._secret = signing_secret.encode("utf-8")
        self._tolerance = tolerance_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def verify(self, headers: Mapping[str, str], body: bytes) -> None:
        timestamp_header = headers.get("X-Slack-Request-Timestamp")
        signature_header = headers.get("X-Slack-Signature")

        if not timestamp_header or not signature_header:
            raise SlackVerificationError("Missing Slack signature headers.")

        try:
            timestamp = int(timestamp_header)
        except ValueError as exc:
            raise SlackVerificationError("Invalid Slack timestamp.") from exc

        now = int(self._clock().timestamp())
        if abs(now - timestamp) > self._tolerance:
            raise SlackVerificationError("Stale Slack request timestamp.")

        basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        digest = hmac.new(self._secret, basestring.encode("utf-8"), sha256).hexdigest()
        expected_signature = f"v0={digest}"

        if not hmac.compare_digest(expected_signature, signature_header):
            LOGGER.warning("Slack signature mismatch.")
            raise SlackVerificationError("Slack signature mismatch.")