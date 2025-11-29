from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


@dataclass(frozen=True, slots=True)
class CloseRunRequest:
    """DTO describing a close-run attempt from Slack or other interface."""

    run_id: str
    actor_user_id: str
    allow_immediate_repeat: bool = False


@dataclass(frozen=True, slots=True)
class ParticipantOrder:
    """Snapshot of a participant order at run close."""

    user_id: str
    display_name: str
    order_text: str
    provenance: str


@dataclass(frozen=True, slots=True)
class RunSummary:
    """Aggregated view of the run suitable for Slack channel + DM payloads."""

    run_id: str
    channel_id: str
    channel_name: str
    runner_user_id: str
    runner_display_name: str
    pickup_time: datetime | None
    pickup_note: str | None
    participants: Tuple[ParticipantOrder, ...]
    total_orders: int
    reminder_offset_minutes: int | None
    reminders_enabled: bool | None
    last_call_enabled: bool | None
    closed_at: datetime


@dataclass(frozen=True, slots=True)
class CloseRunResult:
    """Outcome returned by the close-run orchestrator."""

    run_id: str
    channel_id: str
    runner_user_id: str
    closed_at: datetime
    summary: RunSummary
    fairness_note: str