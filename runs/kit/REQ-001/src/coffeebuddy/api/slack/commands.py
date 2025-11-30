from __future__ import annotations

import shlex
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from .errors import SlackCommandValidationError

DEFAULT_USAGE = (
    "Usage: /coffee [pickup=HH:MM (24h)] [note=\"Free text up to 120 chars\"]"
)


@dataclass(frozen=True)
class SlashCommandOptions:
    pickup_time: str | None
    pickup_note: str | None


@dataclass(frozen=True)
class SlashCommandRequest:
    token: str
    team_id: str
    team_domain: str
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    command: str
    text: str
    trigger_id: str
    response_url: str

    @classmethod
    def from_form(cls, form: Mapping[str, Sequence[str]]) -> "SlashCommandRequest":
        def _get(field: str, default: str | None = None) -> str:
            values = form.get(field)
            if not values:
                if default is not None:
                    return default
                raise SlackCommandValidationError(f"Missing field: {field}")
            return values[0]

        return cls(
            token=_get("token"),
            team_id=_get("team_id"),
            team_domain=_get("team_domain"),
            channel_id=_get("channel_id"),
            channel_name=_get("channel_name"),
            user_id=_get("user_id"),
            user_name=_get("user_name"),
            command=_get("command"),
            text=_get("text", ""),
            trigger_id=_get("trigger_id"),
            response_url=_get("response_url"),
        )


class SlashCommandHandler:
    """Parses `/coffee` commands and returns Slack response payloads."""

    def __init__(self, *, usage_message: str = DEFAULT_USAGE, clock: callable | None = None) -> None:
        self._usage_message = usage_message
        self._clock = clock or datetime.utcnow

    def handle(self, request: SlashCommandRequest, *, correlation_id: str) -> dict:
        if request.command != "/coffee":
            raise SlackCommandValidationError("Unsupported command.")

        options = self._parse_options(request.text)
        return {
            "response_type": "in_channel",
            "text": "Coffee run initiated",
            "blocks": self._build_blocks(request, options, correlation_id),
        }

    def handle_invalid(self, *, correlation_id: str, error: str) -> dict:
        return {
            "response_type": "ephemeral",
            "text": f"{self._usage_message}\nTracking ID: {correlation_id}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":warning: *{error}*\n{self._usage_message}",
                    },
                },
                _tracking_block(correlation_id),
            ],
        }

    def _parse_options(self, raw_text: str) -> SlashCommandOptions:
        if not raw_text.strip():
            return SlashCommandOptions(pickup_time=None, pickup_note=None)

        tokens = shlex.split(raw_text)
        pickup_time: str | None = None
        pickup_note: str | None = None

        for token in tokens:
            if "=" not in token:
                raise SlackCommandValidationError(
                    f"Invalid token '{token}'. Expected key=value pairs."
                )
            key, value = token.split("=", 1)
            key = key.lower()
            if key == "pickup":
                pickup_time = self._validate_pickup(value)
            elif key == "note":
                pickup_note = self._validate_note(value)
            else:
                raise SlackCommandValidationError(
                    f"Unsupported option '{key}'. Only pickup/note are allowed."
                )

        return SlashCommandOptions(pickup_time=pickup_time, pickup_note=pickup_note)

    def _validate_pickup(self, pickup_value: str) -> str:
        if len(pickup_value) != 5 or pickup_value[2] != ":":
            raise SlackCommandValidationError("pickup must follow HH:MM 24h format.")
        hour = pickup_value[:2]
        minute = pickup_value[3:]
        try:
            hour_int = int(hour)
            minute_int = int(minute)
        except ValueError as exc:
            raise SlackCommandValidationError("pickup time must be numeric.") from exc
        if not (0 <= hour_int <= 23 and 0 <= minute_int <= 59):
            raise SlackCommandValidationError("pickup time is outside 00:00-23:59.")
        return pickup_value

    def _validate_note(self, note_value: str) -> str:
        if not note_value:
            raise SlackCommandValidationError("note cannot be empty.")
        if len(note_value) > 120:
            raise SlackCommandValidationError("note must be 120 characters or fewer.")
        return note_value

    def _build_blocks(
        self,
        request: SlashCommandRequest,
        options: SlashCommandOptions,
        correlation_id: str,
    ) -> list[dict]:
        pickup_text = options.pickup_time or "Not specified"
        note_text = options.pickup_note or "No note provided"
        initiated_ts = self._clock().strftime("%H:%M UTC")

        blocks: list[dict] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "☕ Coffee run started", "emoji": True},
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Channel:* <#{request.channel_id}> • *Initiated by:* <@{request.user_id}>",
                    }
                ],
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Pickup time*\n{pickup_text}"},
                    {"type": "mrkdwn", "text": f"*Note*\n{note_text}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Use the buttons below to place or reuse your order.",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Place new order"},
                        "style": "primary",
                        "action_id": "order:new",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Use last order"},
                        "action_id": "order:reuse",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Close run"},
                        "style": "danger",
                        "action_id": "run:close",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Started at {initiated_ts}. Remember: responses are needed within {self._usage_message}.",
                    }
                ],
            },
            _tracking_block(correlation_id),
        ]
        return blocks


def _tracking_block(correlation_id: str) -> dict:
    return {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": f"*Tracking ID:* `{correlation_id}`"},
        ],
    }