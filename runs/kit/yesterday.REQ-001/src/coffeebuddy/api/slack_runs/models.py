from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SlackCommandPayload:
    token: str
    team_id: str
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    text: str
    trigger_id: str
    response_url: str


@dataclass(slots=True)
class RunCommandOptions:
    pickup_time: datetime | None = None
    pickup_note: str | None = None
    errors: list[str] | None = None

    def has_errors(self) -> bool:
        return bool(self.errors)


@dataclass(slots=True, frozen=True)
class SlackResponseEnvelope:
    response_type: str
    blocks: list[dict[str, Any]]
    text: str