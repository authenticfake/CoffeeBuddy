from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable


Clock = Callable[[], datetime]


class OrderProvenance(str, Enum):
    """Describes how an order submission was produced."""

    MANUAL = "manual"
    PREFERENCE = "preference"
    EDIT = "edit"


@dataclass(frozen=True, slots=True)
class OrderSubmissionRequest:
    run_id: str
    user_id: str
    order_text: str
    confirm: bool = True
    provenance: OrderProvenance = OrderProvenance.MANUAL


@dataclass(frozen=True, slots=True)
class OrderSubmissionResult:
    order_id: str
    participant_count: int
    order_text: str
    provenance: OrderProvenance
    preference_updated: bool


@dataclass(frozen=True, slots=True)
class OrderCancellationResult:
    order_id: str
    participant_count: int


@dataclass(frozen=True, slots=True)
class UseLastOrderResult:
    preference_id: str
    submission: OrderSubmissionResult