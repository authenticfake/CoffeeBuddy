from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


@dataclass(frozen=True, slots=True)
class CloseRunRequest:
    """Command payload for closing a run."""

    run_id: str
    actor_user_id: str
    correlation_id: str
    allow_consecutive_runner: bool = False


@dataclass(frozen=True, slots=True)
class RunnerSnapshot:
    """Resolved runner identity."""

    user_id: str
    slack_user_id: str
    display_name: str


@dataclass(frozen=True, slots=True)
class OrderSnapshot:
    """Immutable snapshot of an order at run closure."""

    order_id: str
    user_id: str
    slack_user_id: str
    display_name: str
    order_text: str
    provenance: str
    submitted_at: datetime
    confirmed: bool


@dataclass(frozen=True, slots=True)
class RunSummary:
    """Structured summary shared with Slack channel & runner."""

    run_id: str
    channel_id: str
    channel_name: str
    pickup_time: datetime | None
    pickup_note: str | None
    runner: RunnerSnapshot
    participant_orders: tuple[OrderSnapshot, ...]
    participant_count: int
    reminder_offset_minutes: int
    fairness_explanation: str


@dataclass(frozen=True, slots=True)
class CloseRunResult:
    """Outcome of run closure."""

    run_id: str
    runner_user_id: str
    summary: RunSummary
    events_emitted: Sequence[str]