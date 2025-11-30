from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Protocol

from coffeebuddy.infra.kafka.models import ReminderPayload
from coffeebuddy.infra.kafka.reminder_worker import ReminderSender

try:  # pragma: no cover - import is only for runtime integration
    from coffeebuddy.api.slack_runs.messaging import SlackMessageDispatcher
except ImportError:  # pragma: no cover - tests inject their own messenger
    SlackMessageDispatcher = None  # type: ignore[misc]


@dataclass(frozen=True)
class RunnerContact:
    """Resolved runner contact information."""

    user_id: str
    slack_user_id: str
    display_name: str


@dataclass(frozen=True)
class ChannelContact:
    """Resolved channel contact information."""

    channel_id: str
    slack_channel_id: str
    name: str


class ReminderContextResolver(Protocol):
    """Resolves Slack-facing contact details from internal identifiers."""

    def get_runner_contact(self, user_id: str | None) -> RunnerContact | None: ...

    def get_channel_contact(self, channel_id: str) -> ChannelContact | None: ...


class SlackReminderMessenger(Protocol):
    """Subset of Slack helper exposed by ``coffeebuddy.api.slack_runs``."""

    async def send_dm(self, slack_user_id: str, *, text: str, blocks: List[dict[str, Any]]) -> None: ...

    async def post_channel_message(
        self, slack_channel_id: str, *, text: str, blocks: List[dict[str, Any]]
    ) -> None: ...


class ReminderDispatchError(RuntimeError):
    """Raised when reminder delivery cannot be fulfilled."""


class SlackReminderSender(ReminderSender):
    """ReminderSender that delegates to the Slack message dispatcher."""

    def __init__(
        self,
        messenger: SlackReminderMessenger,
        resolver: ReminderContextResolver,
    ) -> None:
        self._messenger = messenger
        self._resolver = resolver

    async def send_runner_reminder(self, payload: ReminderPayload) -> None:
        contact = self._resolver.get_runner_contact(payload.runner_user_id)
        if contact is None:
            raise ReminderDispatchError("Unable to resolve runner contact.")
        text = (
            f"CoffeeBuddy reminder: you're up for the run in channel "
            f"{payload.channel_id}. Pickup in ~{payload.reminder_offset_minutes} minutes."
        )
        blocks = self._build_runner_blocks(contact, payload)
        await self._messenger.send_dm(contact.slack_user_id, text=text, blocks=blocks)

    async def send_last_call_reminder(self, payload: ReminderPayload) -> None:
        channel = self._resolver.get_channel_contact(payload.channel_id)
        if channel is None:
            raise ReminderDispatchError("Unable to resolve channel contact.")
        text = (
            f"CoffeeBuddy last call: finalize orders in #{channel.name} before the runner leaves."
        )
        blocks = self._build_last_call_blocks(channel, payload)
        await self._messenger.post_channel_message(channel.slack_channel_id, text=text, blocks=blocks)

    def _build_runner_blocks(
        self,
        contact: RunnerContact,
        payload: ReminderPayload,
    ) -> List[dict[str, Any]]:
        return [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Hi {contact.display_name}!*"}},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"Coffee run `{payload.run_id}` is about to start. "
                        f"This reminder fired roughly {payload.reminder_offset_minutes} minutes "
                        "before the pickup time."
                    ),
                },
            },
        ]

    def _build_last_call_blocks(
        self,
        channel: ChannelContact,
        payload: ReminderPayload,
    ) -> List[dict[str, Any]]:
        eta_minutes = self._minutes_until(payload.scheduled_for)
        return [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"Last call for #{channel.name}!"}},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"Runner leaves in approximately {eta_minutes} minutes. "
                            "Submit or edit your order now."
                        ),
                    }
                ],
            },
        ]

    def _minutes_until(self, target: datetime) -> int:
        now = datetime.now(timezone.utc)
        delta = target - now
        minutes = max(delta.total_seconds() / 60, 0)
        return int(math.ceil(minutes))