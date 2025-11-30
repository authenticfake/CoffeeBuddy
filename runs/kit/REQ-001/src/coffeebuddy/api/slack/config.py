from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlackConfig:
    """
    Configuration for Slack HTTP handlers.

    Attributes:
        signing_secret: Slack app signing secret used to validate
            slash command and interaction requests.
        command_timeout_seconds: Target response window for slash command
            acknowledgements.
        request_tolerance_seconds: Maximum acceptable age (seconds) for
            Slack requests before rejecting them to avoid replay attacks.
    """

    signing_secret: str
    command_timeout_seconds: int = 2
    request_tolerance_seconds: int = 300