from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RunCreatedEvent:
    run_id: str
    channel_id: str
    initiator_user_id: str
    pickup_time: str | None
    pickup_note: str | None
    correlation_id: str
    created_at: str

    def to_payload(self) -> dict:
        return asdict(self)


class RunEventPublisher(Protocol):
    def publish_run_created(self, event: RunCreatedEvent) -> None:
        ...