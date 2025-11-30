from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from coffeebuddy.core.orders.models import Clock
from coffeebuddy.core.runs.exceptions import RunnerSelectionError
from coffeebuddy.infra.db.models import RunnerStat
from coffeebuddy.services.fairness.models import FairnessDecision


class FairnessService:
    """Encapsulates runner selection logic based on historical participation."""

    _EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

    def __init__(self, session: Session, *, clock: Clock | None = None) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def assign_runner(
        self,
        *,
        channel_id: str | UUID,
        participant_user_ids: Sequence[str | UUID],
        last_runner_id: str | None,
        allow_immediate_repeat: bool,
    ) -> FairnessDecision:
        participants = self._unique_ordered(participant_user_ids)
        if not participants:
            raise RunnerSelectionError("No eligible participants to evaluate for runner assignment.")

        channel_uuid = _as_uuid(channel_id)
        stats = self._load_stats(channel_uuid, participants)
        previous_counts = {uid: stat.runs_served_count for uid, stat in stats.items()}

        candidate_stats = list(stats.values())
        excluded_last_runner = False
        if (
            not allow_immediate_repeat
            and last_runner_id
            and last_runner_id in stats
            and len(candidate_stats) > 1
        ):
            candidate_stats = [
                stat for stat in candidate_stats if str(stat.user_id) != last_runner_id
            ]
            excluded_last_runner = True

        if not candidate_stats:
            candidate_stats = list(stats.values())

        chosen = min(candidate_stats, key=self._sort_key)
        now = self._clock()

        if getattr(chosen, "created_at", None) is None:
            chosen.created_at = now
        chosen.runs_served_count += 1
        chosen.last_run_at = now
        chosen.updated_at = now

        rationale = self._build_rationale(
            previous_count=previous_counts[str(chosen.user_id)],
            excluded_last_runner=excluded_last_runner,
        )

        return FairnessDecision(runner_user_id=str(chosen.user_id), rationale=rationale)

    def _load_stats(
        self, channel_id: UUID, participants: list[str]
    ) -> dict[str, RunnerStat]:
        stmt = (
            select(RunnerStat)
            .where(
                RunnerStat.channel_id == channel_id,
                RunnerStat.user_id.in_([_as_uuid(pid) for pid in participants]),
            )
        )
        rows = self._session.scalars(stmt).all()
        stats = {str(stat.user_id): stat for stat in rows}

        for participant in participants:
            if participant not in stats:
                participant_uuid = _as_uuid(participant)
                now = self._clock()
                stat = RunnerStat(
                    id=uuid4(),
                    channel_id=channel_id,
                    user_id=participant_uuid,
                    runs_served_count=0,
                    last_run_at=None,
                    created_at=now,
                    updated_at=now,
                )
                stats[participant] = stat
                self._session.add(stat)
        return stats

    def _sort_key(self, stat: RunnerStat) -> tuple[int, datetime, datetime, str]:
        last_run = stat.last_run_at or self._EPOCH
        created_at = getattr(stat, "created_at", self._EPOCH)
        return (stat.runs_served_count, last_run, created_at, str(stat.user_id))

    def _build_rationale(self, *, previous_count: int, excluded_last_runner: bool) -> str:
        base = (
            "Runner chosen by minimum recent runs served "
            f"(count before assignment: {previous_count}). "
            "Tie-breakers: earliest last_run_at then deterministic user id."
        )
        if excluded_last_runner:
            return base + " Previous runner excluded to avoid back-to-back assignments."
        return base

    def _unique_ordered(self, identifiers: Sequence[str | UUID]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for identifier in identifiers:
            normalized = str(identifier)
            if normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered


def _as_uuid(value: str | UUID) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(value)