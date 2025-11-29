from __future__ import annotations


class AdminError(Exception):
    """Base class for admin surfaced failures."""


class AdminAuthorizationError(AdminError):
    """Raised when the actor is not permitted to perform admin actions."""

    def __init__(self, slack_user_id: str, reason: str) -> None:
        self.slack_user_id = slack_user_id
        self.reason = reason
        super().__init__(f"User {slack_user_id} is not authorized: {reason}")


class ChannelNotFoundError(AdminError):
    """Raised when the Slack channel cannot be resolved to a configured channel."""

    def __init__(self, slack_channel_id: str) -> None:
        self.slack_channel_id = slack_channel_id
        super().__init__(f"Channel {slack_channel_id} is not recognized by CoffeeBuddy.")


class ChannelConfigValidationError(AdminError):
    """Raised when an attempted configuration change violates policy."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"Invalid value for {field}: {message}")