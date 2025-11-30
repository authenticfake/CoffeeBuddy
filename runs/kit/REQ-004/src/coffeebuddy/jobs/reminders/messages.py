from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List

from coffeebuddy.infra.kafka.models import ReminderPayload


@dataclass(frozen=True)
class ReminderMessage:
    """Normalized Slack message payload."""

    text: str
    blocks: List[dict[str, Any]] | None = None


class ReminderMessageBuilder:
    """Creates human-friendly Slack messages for reminder workflows."""

    def __init__(self, *, time_format: str = "%H:%M %Z") -> None:
        self._time_format = time_format

    def build_runner_message(self, payload: ReminderPayload) -> ReminderMessage:
        formatted_time = self._format_time(payload.scheduled_for)
        text = (
            f"Coffee run reminder for <#{payload.channel_id}>.\n"
            f"Pickup is at {formatted_time}; you're scheduled to head out "
            f"in about {payload.reminder_offset_minutes} minutes."
        )
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Run ID: `{payload.run_id}` • Reminder ID: `{payload.reminder_id}`",
                    }
                ],
            },
        ]
        return ReminderMessage(text=text, blocks=blocks)

    def build_last_call_message(self, payload: ReminderPayload) -> ReminderMessage:
        formatted_time = self._format_time(payload.scheduled_for)
        text = (
            ":bell: *Last call for coffee orders!* This run will close soon.\n"
            f"Pickup is scheduled for {formatted_time}. Submit or edit your order now."
        )
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Run ID: `{payload.run_id}` • Reminder ID: `{payload.reminder_id}`",
                    }
                ],
            },
        ]
        return ReminderMessage(text=text, blocks=blocks)

    def _format_time(self, timestamp: datetime) -> str:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=datetime.utcnow().astimezone().tzinfo)
        return timestamp.strftime(self._time_format)


__all__ = ["ReminderMessage", "ReminderMessageBuilder"]