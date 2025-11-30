from __future__ import annotations


class SlackVerificationError(Exception):
    """Raised when Slack request verification fails."""


class SlackCommandValidationError(Exception):
    """Raised when slash command payloads are invalid."""


class SlackInteractionValidationError(Exception):
    """Raised when Slack interaction payloads cannot be parsed."""