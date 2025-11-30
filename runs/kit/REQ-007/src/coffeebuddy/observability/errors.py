from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "CoffeeBuddyError",
    "SlackConfigError",
    "SlackAuthError",
]


@dataclass(frozen=True)
class CoffeeBuddyError(Exception):
    """
    Domain-safe error representation for user-facing Slack responses.

    Attributes:
        user_message: What to send back to Slack users/admins.
        status_code: HTTP status suitable for slash command response.
        error_code: Stable identifier for metrics/audit.
    """

    user_message: str
    status_code: int = 400
    error_code: str = "bad_request"
    log_message: str | None = None

    def __post_init__(self) -> None:
        super().__init__(self.log_message or self.user_message)


class SlackConfigError(CoffeeBuddyError):
    """Raised when Slack app configuration or scopes are invalid."""

    def __init__(self, message: str, *, log_message: str | None = None) -> None:
        super().__init__(
            user_message=message,
            status_code=400,
            error_code="slack_config_error",
            log_message=log_message,
        )


class SlackAuthError(CoffeeBuddyError):
    """Raised when Slack signature or auth validation fails."""

    def __init__(self, message: str = "Slack request could not be authorized.") -> None:
        super().__init__(
            user_message=message,
            status_code=401,
            error_code="slack_auth_error",
            log_message=message,
        )