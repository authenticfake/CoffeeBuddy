from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class KafkaEvent(BaseModel):
    """Structured payload sent across Kafka topics."""

    event_type: str
    correlation_id: str
    payload: dict[str, Any]
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _ensure_correlation(self) -> "KafkaEvent":
        if not self.correlation_id:
            raise ValueError("correlation_id is required")
        return self

    def as_bytes(self) -> bytes:
        return self.model_dump_json().encode("utf-8")


ReminderType = Literal["runner", "last_call"]


class ReminderPayload(BaseModel):
    """Schema enforced for reminder events consumed by the worker harness."""

    reminder_id: str
    run_id: str
    channel_id: str
    runner_user_id: str | None
    reminder_type: ReminderType
    scheduled_for: datetime
    reminder_offset_minutes: int
    channel_reminders_enabled: bool = True
    last_call_enabled: bool = False
    correlation_id: str | None = None

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}