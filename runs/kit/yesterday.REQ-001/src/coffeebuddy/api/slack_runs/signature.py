from __future__ import annotations

import hashlib
import hmac
import time


class SlackVerificationError(Exception):
    """Raised when Slack signature validation fails."""


class SlackSignatureVerifier:
    def __init__(self, *, signing_secret: str, tolerance_seconds: int = 300) -> None:
        self._secret = signing_secret.encode()
        self._tolerance = tolerance_seconds

    def verify(self, *, timestamp: str | None, signature: str | None, body: bytes) -> None:
        if not timestamp or not signature:
            raise SlackVerificationError("Missing Slack signature headers.")

        if abs(time.time() - int(timestamp)) > self._tolerance:
            raise SlackVerificationError("Stale Slack request timestamp.")

        expected_signature = self._compute_signature(timestamp, body)
        if not hmac.compare_digest(expected_signature, signature):
            raise SlackVerificationError("Slack signature mismatch.")

    def _compute_signature(self, timestamp: str, body: bytes) -> str:
        basestring = f"v0:{timestamp}:{body.decode()}".encode()
        digest = hmac.new(self._secret, basestring, hashlib.sha256).hexdigest()
        return f"v0={digest}"