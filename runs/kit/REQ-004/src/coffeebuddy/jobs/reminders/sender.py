from __future__ import annotations

import logging
from typing import Any, Protocol

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from coffeebuddy.infra.kafka.models import ReminderPayload
from coffeebuddy.infra.kafka.reminder_worker import ReminderSender

from .messages import ReminderMessageBuilder

LOGGER = logging.getLogger(__name__)


class SlackDMClient(Protocol):
    async def send_dm(self, *, user_id: str, text: str, blocks: list[dict[str, Any]] | None = None) -> None: ...


class SlackChannelMessenger(Protocol):
    async def post_message(self, *, channel_id: str, text: str, blocks: list[dict[str, Any]] | None = None) -> None: ...


class SlackAsyncDMClient(SlackDMClient):
    """Production Slack DM implementation using AsyncWebClient."""

    def __init__(self, client: AsyncWebClient) -> None:
        self._client = client

    async def send_dm(self, *, user_id: str, text: str, blocks: list[dict[str, Any]] | None = None) -> None:
        try:
            opened = await self._client.conversations_open(users=user_id)
            channel_id = opened["channel"]["id"]
            await self._client.chat_postMessage(channel=channel_id, text=text, blocks=blocks)
        except SlackApiError as exc:  # pragma: no cover - network errors exercised in integration tests
            LOGGER.exception("Failed to send Slack DM", extra={"user_id": user_id})
            raise exc


class SlackAsyncChannelMessenger(SlackChannelMessenger):
    """Posts messages into a Slack channel via AsyncWebClient."""

    def __init__(self, client: AsyncWebClient) -> None:
        self._client = client

    async def post_message(self, *, channel_id: str, text: str, blocks: list[dict[str, Any]] | None = None) -> None:
        try:
            await self._client.chat_postMessage(channel=channel_id, text=text, blocks=blocks)
        except SlackApiError as exc:  # pragma: no cover - network errors exercised in integration tests
            LOGGER.exception("Failed to post Slack channel message", extra={"channel_id": channel_id})
            raise exc


class SlackReminderSender(ReminderSender):
    """ReminderSender implementation that talks to Slack."""

    def __init__(
        self,
        *,
        dm_client: SlackDMClient,
        channel_messenger: SlackChannelMessenger,
        message_builder: ReminderMessageBuilder | None = None,
    ) -> None:
        self._dm_client = dm_client
        self._channel_messenger = channel_messenger
        self._messages = message_builder or ReminderMessageBuilder()

    async def send_runner_reminder(self, payload: ReminderPayload) -> None:
        if not payload.runner_user_id:
            raise ValueError("runner_user_id is required for runner reminders")
        message = self._messages.build_runner_message(payload)
        await self._dm_client.send_dm(user_id=payload.runner_user_id, text=message.text, blocks=message.blocks)

    async def send_last_call_reminder(self, payload: ReminderPayload) -> None:
        message = self._messages.build_last_call_message(payload)
        await self._channel_messenger.post_message(
            channel_id=payload.channel_id,
            text=message.text,
            blocks=message.blocks,
        )


def build_default_slack_sender(client: AsyncWebClient) -> SlackReminderSender:
    """Factory that wires Slack AsyncWebClient into the reminder sender."""
    return SlackReminderSender(
        dm_client=SlackAsyncDMClient(client),
        channel_messenger=SlackAsyncChannelMessenger(client),
    )


__all__ = [
    "SlackReminderSender",
    "SlackDMClient",
    "SlackChannelMessenger",
    "SlackAsyncDMClient",
    "SlackAsyncChannelMessenger",
    "build_default_slack_sender",
]